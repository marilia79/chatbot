# -*- coding: utf-8 -*-
"""
API Flask do chatbot da Secretaria Acadêmica - IFSC Câmpus Garopaba.

Rotas do chat:
- GET  /          -> página de conversa
- POST /start     -> {"user_id"}            devolve boas-vindas + menu
- POST /chat      -> {"user_id","message"}  devolve a resposta do bot
- POST /feedback  -> {"user_id","demanda_id","resolvido"}

Rotas do painel (exigem login): /admin/login, /admin, /admin/demanda/<id>,
/admin/export, /admin/logout.

Como rodar na sua máquina (teste):
    pip install -r requirements.txt
    python criar_admin.py           # cadastra o atendente com uma senha forte
    python app.py                   # abre em http://localhost:5000

Configuração por variáveis de ambiente (todas opcionais):
    SECRET_KEY    chave que assina a sessão do painel. Se não existir, uma chave
                  aleatória é criada e guardada no arquivo .secret_key.
    APP_PUBLICO   "1" quando o app estiver na internet com HTTPS: o cookie de
                  sessão passa a ser "secure" e o IP é lido do proxy.
    MODO_PILOTO   "1" liga o teste piloto: aviso de teste na boas-vindas e
                  sorteio equilibrado do modo (PLN x palavra-chave) por pessoa.
    PAINEL_DB     caminho do arquivo do banco (padrão: painel.db ao lado do código).
    APP_HOST, PORT, FLASK_DEBUG  usados só ao rodar com "python app.py".
                  O padrão é 127.0.0.1, 5000 e debug DESLIGADO.

Quando for integrar com WhatsApp (ex: Twilio), basta criar uma nova rota
tipo /whatsapp que recebe o webhook, extrai o número do remetente como
user_id e o texto da mensagem, chama bot.process_message(user_id, texto)
e devolve a resposta no formato que a Twilio espera (TwiML). A lógica
do bot (bot.py) não muda nada.
"""

import csv
import hmac
import io
import os
import re
import secrets
import sys
import time
from collections import defaultdict, deque
from datetime import timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, Response, abort, jsonify, redirect, render_template, request, session, url_for

import bot
import content
import db

BASE_DIR = Path(__file__).parent


def _ligado(nome_variavel: str) -> bool:
    return os.environ.get(nome_variavel, "").strip().lower() in ("1", "true", "sim", "yes")


MODO_PILOTO = _ligado("MODO_PILOTO")
APP_PUBLICO = _ligado("APP_PUBLICO")

# Limites (proteção básica de um app público)
MAX_CARACTERES_MENSAGEM = 500
MAX_CARACTERES_PARECER = 2000
LIMITE_MENSAGENS_POR_MINUTO_USUARIO = 25
LIMITE_MENSAGENS_POR_MINUTO_IP = 200      # alto: no campus muita gente divide o mesmo IP
LIMITE_FALHAS_LOGIN_USUARIO = 8
LIMITE_FALHAS_LOGIN_IP = 20
JANELA_LOGIN_SEGUNDOS = 15 * 60
USER_ID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{4,64}$")


def _carregar_chave_secreta() -> str:
    """Chave da sessão: variável SECRET_KEY, ou arquivo .secret_key (criado na 1ª execução)."""
    chave = os.environ.get("SECRET_KEY", "").strip()
    if chave:
        return chave
    arquivo = BASE_DIR / ".secret_key"
    try:
        if arquivo.exists():
            chave = arquivo.read_text(encoding="utf-8").strip()
            if chave:
                return chave
        chave = secrets.token_hex(32)
        arquivo.write_text(chave, encoding="utf-8")
        try:
            arquivo.chmod(0o600)
        except OSError:
            pass
        return chave
    except OSError:
        print("AVISO: não foi possível gravar o arquivo .secret_key; usando uma chave temporária "
              "(quem estiver logado no painel precisará entrar de novo quando o servidor reiniciar).",
              file=sys.stderr)
        return secrets.token_hex(32)


app = Flask(__name__)
app.secret_key = _carregar_chave_secreta()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=APP_PUBLICO,          # só trafega por HTTPS quando estiver publicado
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=16 * 1024,               # recusa requisições gigantes
)

db.init_db()


def _avisos_de_seguranca() -> None:
    if db.total_usuarios() == 0:
        print("AVISO: nenhum atendente cadastrado, então ninguém consegue entrar no painel. "
              "Rode:  python criar_admin.py", file=sys.stderr)
    for usuario in db.usuarios_com_senha_padrao():
        print(f"AVISO: o usuário '{usuario}' ainda tem a senha padrão antiga, que está BLOQUEADA. "
              f"Defina uma nova com:  python criar_admin.py {usuario}", file=sys.stderr)


_avisos_de_seguranca()


# --------------------------------------------------------------------------
# Utilitários de segurança
# --------------------------------------------------------------------------

_eventos = defaultdict(deque)   # chave -> instantes (limite de frequência, em memória)


def _contar(chave: str, janela: int) -> int:
    agora = time.time()
    fila = _eventos[chave]
    while fila and agora - fila[0] > janela:
        fila.popleft()
    return len(fila)


def _registrar(chave: str) -> None:
    _eventos[chave].append(time.time())
    if len(_eventos) > 5000:     # evita crescer sem limite
        agora = time.time()
        for k in [k for k, f in _eventos.items() if not f or agora - f[-1] > 3600]:
            del _eventos[k]


def _excedeu(chave: str, limite: int, janela: int) -> bool:
    """Conta a tentativa e diz se passou do limite."""
    if _contar(chave, janela) >= limite:
        return True
    _registrar(chave)
    return False


def _ip_cliente() -> str:
    """IP de quem chamou. Atrás de proxy (hospedagem) usa o último valor de X-Forwarded-For,
    que é o que o proxy confiável acrescentou (o primeiro poderia ser forjado)."""
    if APP_PUBLICO:
        encaminhado = request.headers.get("X-Forwarded-For", "")
        if encaminhado:
            return encaminhado.split(",")[-1].strip()[:64]
    return request.remote_addr or "?"


def csrf_token() -> str:
    token = session.get("_csrf")
    if not token:
        token = secrets.token_hex(16)
        session["_csrf"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


def _checar_csrf() -> None:
    enviado = request.form.get("csrf_token", "")
    esperado = session.get("_csrf", "")
    if not esperado or not hmac.compare_digest(enviado, esperado):
        abort(400, "Token de segurança ausente ou expirado. Volte à página anterior, recarregue e tente de novo.")


def _csv_seguro(valor):
    """Evita 'injeção de fórmulas': no Excel, células que começam com = + - @ viram fórmulas."""
    if isinstance(valor, str) and valor[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + valor
    return valor


@app.after_request
def _cabecalhos_de_seguranca(resposta):
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["Referrer-Policy"] = "same-origin"
    if request.path.startswith("/admin"):
        resposta.headers["X-Frame-Options"] = "DENY"       # painel não pode ser embutido em outro site
        resposta.headers["Cache-Control"] = "no-store"
    if APP_PUBLICO:
        resposta.headers["Strict-Transport-Security"] = "max-age=31536000"
    return resposta


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapper


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------

def _user_id_valido(user_id) -> bool:
    return isinstance(user_id, str) and USER_ID_VALIDO.match(user_id) is not None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not _user_id_valido(user_id):
        return jsonify({"error": "user_id inválido"}), 400

    reply = bot.start_conversation(user_id)
    if MODO_PILOTO:
        db.atribuir_modo(user_id)     # sorteia já na chegada
        reply = content.AVISO_PILOTO + "\n\n" + reply
    return jsonify({"reply": reply, "piloto": MODO_PILOTO})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    message = data.get("message", "")

    if not _user_id_valido(user_id):
        return jsonify({"error": "user_id inválido"}), 400
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "message não pode ser vazio"}), 400
    if len(message) > MAX_CARACTERES_MENSAGEM:
        return jsonify({"error": f"Mensagem muito longa (máximo de {MAX_CARACTERES_MENSAGEM} caracteres)."}), 400
    if (_excedeu(f"chat-usuario:{user_id}", LIMITE_MENSAGENS_POR_MINUTO_USUARIO, 60)
            or _excedeu(f"chat-ip:{_ip_cliente()}", LIMITE_MENSAGENS_POR_MINUTO_IP, 60)):
        return jsonify({"error": "Muitas mensagens em pouco tempo. Aguarde um instante e tente novamente."}), 429

    # No piloto, o modo vem do sorteio do servidor (a pessoa não escolhe nem sabe qual é).
    if MODO_PILOTO:
        usar_pln = db.atribuir_modo(user_id) == "PLN"
    else:
        usar_pln = bool(data.get("usar_pln", True))

    resultado = bot.process_message(user_id, message, usar_pln=usar_pln)
    reply = resultado["reply"]
    intent = resultado.get("intent")
    confidence = resultado.get("confidence")
    modo = resultado.get("modo")
    pedir_feedback = resultado.get("pedir_feedback", False)

    # No painel, o comando interno do botão aparece com um texto legível.
    mensagem_para_log = "[Botão] Falar com atendente" if message.strip() == bot.COMANDO_ATENDENTE else message
    demanda_id = db.log_demanda(user_id, mensagem_para_log, reply, intent, confidence, modo)
    return jsonify({
        "reply": reply,
        "intent": intent,
        "confidence": confidence,
        "modo": modo,
        "demanda_id": demanda_id,
        "pedir_feedback": pedir_feedback,
    })


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    demanda_id = data.get("demanda_id")
    resolvido = data.get("resolvido")

    if (not _user_id_valido(user_id) or isinstance(demanda_id, bool) or not isinstance(demanda_id, int)
            or not isinstance(resolvido, bool)):
        return jsonify({"error": "user_id, demanda_id e resolvido são obrigatórios"}), 400
    # Só quem gerou a demanda pode avaliá-la (senão qualquer um distorceria as métricas).
    if not db.demanda_pertence_a(demanda_id, user_id):
        return jsonify({"error": "demanda não encontrada para este usuário"}), 403

    db.registrar_feedback(demanda_id, resolvido)
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# Painel da Secretaria Acadêmica (área do atendente)
# --------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    erro = None
    if request.method == "POST":
        _checar_csrf()
        username = request.form.get("username", "").strip()[:64]
        password = request.form.get("password", "")[:256]
        chave_usuario = f"login-usuario:{username.lower()}"
        chave_ip = f"login-ip:{_ip_cliente()}"

        if (_contar(chave_usuario, JANELA_LOGIN_SEGUNDOS) >= LIMITE_FALHAS_LOGIN_USUARIO
                or _contar(chave_ip, JANELA_LOGIN_SEGUNDOS) >= LIMITE_FALHAS_LOGIN_IP):
            erro = "Muitas tentativas de entrada. Aguarde alguns minutos e tente de novo."
            return render_template("admin_login.html", erro=erro), 429

        if db.verificar_login(username, password):
            session.clear()                    # nova sessão após o login (evita fixação de sessão)
            session["logged_in"] = True
            session["username"] = username
            session.permanent = True
            _eventos.pop(chave_usuario, None)
            return redirect(url_for("admin_dashboard"))

        _registrar(chave_usuario)
        _registrar(chave_ip)
        erro = "Usuário ou senha inválidos."
    return render_template("admin_login.html", erro=erro)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    status_filtro = request.args.get("status")
    somente_nao_entendidas = request.args.get("filtro") == "nao_entendidas"
    demandas = db.list_demandas(status_filtro, nao_entendidas=somente_nao_entendidas)
    contagem = db.contar_por_status()
    resolucao = db.estatisticas_resolucao()
    return render_template(
        "admin_dashboard.html",
        demandas=demandas,
        contagem=contagem,
        status_opcoes=db.STATUS_OPCOES,
        status_filtro=status_filtro,
        somente_nao_entendidas=somente_nao_entendidas,
        total_nao_entendidas=db.contar_nao_entendidas(),
        username=session.get("username"),
        resolucao=resolucao,
    )


@app.route("/admin/demanda/<int:demanda_id>", methods=["GET", "POST"])
@login_required
def admin_demanda(demanda_id):
    demanda = db.get_demanda(demanda_id)
    if demanda is None:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        _checar_csrf()
        status = request.form.get("status", db.STATUS_PENDENTE)
        if status not in db.STATUS_OPCOES:
            status = db.STATUS_PENDENTE
        parecer = request.form.get("parecer", "")[:MAX_CARACTERES_PARECER]
        db.update_demanda(demanda_id, status, parecer, session.get("username", ""))
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_demanda.html", demanda=demanda, status_opcoes=db.STATUS_OPCOES
    )


@app.route("/admin/export")
@login_required
def admin_export():
    demandas = db.list_demandas()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Protocolo", "Data/Hora", "Usuário", "Mensagem", "Resposta do bot", "Modo", "Intenção detectada (PLN)", "Confiança", "Resolveu a dúvida?", "Status", "Parecer", "Atendente"]
    )
    for d in demandas:
        linha = [d["id"], d["data_hora"], d["user_id"], d["mensagem"], d["resposta_bot"], d["modo"] or "", d["intent_detectado"] or "", d["confianca"] or "", d["resolvido_pelo_usuario"] or "", d["status"], d["parecer"], d["atendente"]]
        writer.writerow([_csv_seguro(c) for c in linha])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=demandas_secretaria.csv"},
    )


if __name__ == "__main__":
    app.run(
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=_ligado("FLASK_DEBUG"),
    )
