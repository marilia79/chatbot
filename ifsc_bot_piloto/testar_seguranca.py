# -*- coding: utf-8 -*-
"""
Testes automáticos das proteções do login e do modo piloto.

Uso:   python testar_seguranca.py

Usa um banco temporário (não mexe no seu painel.db) e liga o modo piloto só
dentro do teste. Cada linha mostra OK ou FALHOU; no fim, o total.
"""
import os
import re
import sys
import tempfile

# --- ambiente de teste (precisa ser definido ANTES de importar o app) ---
_pasta = tempfile.mkdtemp()
os.environ["PAINEL_DB"] = os.path.join(_pasta, "teste.db")
os.environ["SECRET_KEY"] = "chave-so-para-testes"
os.environ["MODO_PILOTO"] = "1"
os.environ.pop("APP_PUBLICO", None)

import app as A   # noqa: E402
import db         # noqa: E402
from werkzeug.security import generate_password_hash   # noqa: E402

resultados = []


def verificar(descricao, condicao):
    resultados.append(bool(condicao))
    print(("  OK      " if condicao else "  FALHOU  ") + descricao)


def token_csrf(cliente, caminho="/admin/login"):
    html = cliente.get(caminho).get_data(as_text=True)
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else ""


def entrar(cliente, usuario, senha, com_token=True):
    dados = {"username": usuario, "password": senha}
    if com_token:
        dados["csrf_token"] = token_csrf(cliente)
    return cliente.post("/admin/login", data=dados)


SENHA_BOA = "Garopaba#Teste2026"

print("\n[1] Cadastro e regras de senha")
verificar("sem usuários, o painel não abre (redireciona ao login)", A.app.test_client().get("/admin").status_code == 302)
for ruim, motivo in [("curta1!", "curta"), ("admin123", "senha antiga"), ("somenteletrasaqui", "sem número/símbolo"), ("atendente#12345678", "contém o usuário")]:
    try:
        db.criar_ou_atualizar_usuario("atendente", ruim); aceita = True
    except ValueError:
        aceita = False
    verificar(f"recusa senha fraca ({motivo})", not aceita)
verificar("aceita senha forte", db.criar_ou_atualizar_usuario("atendente", SENHA_BOA) == "criado")
verificar("troca de senha funciona", db.criar_ou_atualizar_usuario("atendente", SENHA_BOA) == "atualizado")

print("\n[2] Login")
c = A.app.test_client()
verificar("login sem token CSRF é recusado (400)", entrar(c, "atendente", SENHA_BOA, com_token=False).status_code == 400)
verificar("senha errada não entra", entrar(c, "atendente", "senha errada 123!").status_code == 200 and c.get("/admin").status_code == 302)
# usuário legado com a senha antiga no banco
conn = db.get_connection()
conn.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)", ("legado", generate_password_hash("admin123")))
conn.commit(); conn.close()
verificar("a senha antiga 'admin123' continua BLOQUEADA, mesmo estando no banco", entrar(c, "legado", "admin123").status_code == 200 and c.get("/admin").status_code == 302)
verificar("o script detecta usuário com senha antiga", "legado" in db.usuarios_com_senha_padrao())
r = entrar(c, "atendente", SENHA_BOA)
verificar("login correto entra no painel", r.status_code == 302 and c.get("/admin").status_code == 200)
cabecalhos = c.get("/admin").headers
verificar("painel não pode ser embutido em outro site (X-Frame-Options)", cabecalhos.get("X-Frame-Options") == "DENY")
verificar("painel não fica em cache (no-store)", "no-store" in cabecalhos.get("Cache-Control", ""))
verificar("X-Content-Type-Options presente", cabecalhos.get("X-Content-Type-Options") == "nosniff")
cookie = A.app.test_client().get("/admin/login").headers.get("Set-Cookie", "")
verificar("cookie de sessão é HttpOnly e SameSite", "HttpOnly" in cookie and "SameSite=Lax" in cookie)
c.get("/admin/logout")
verificar("após sair, o painel volta a pedir login", c.get("/admin").status_code == 302)

print("\n[3] Força bruta")
db.criar_ou_atualizar_usuario("vitima", "Outra#Chave2026x")
alvo = A.app.test_client()
for _ in range(8):
    entrar(alvo, "vitima", "tentativa errada 1!")
r = entrar(alvo, "vitima", "Outra#Chave2026x")
verificar("após 8 erros, até a senha certa do alvo é barrada (429)", r.status_code == 429)
verificar("o bloqueio de um usuário não atrapalha os outros", entrar(A.app.test_client(), "atendente", SENHA_BOA).status_code == 302)

print("\n[4] Chat: validação e limites")
cl = A.app.test_client()
def chat(user_id, message, **extra):
    return cl.post("/chat", json={"user_id": user_id, "message": message, **extra})
verificar("user_id inválido é recusado", chat("a b!", "oi").status_code == 400)
verificar("mensagem vazia é recusada", chat("aluno-0001", "   ").status_code == 400)
verificar("mensagem gigante é recusada", chat("aluno-0001", "x" * 501).status_code == 400)
verificar("mensagem normal funciona", chat("aluno-0001", "matrícula").status_code == 200)
codigos = [chat("limite-01", "matrícula").status_code for _ in range(30)]
verificar("excesso de mensagens por minuto leva a 429", 429 in codigos and codigos[0] == 200)

print("\n[5] Piloto: aviso e sorteio do modo")
r = cl.post("/start", json={"user_id": "aluno-0002"}).get_json()
verificar("boas-vindas traz o aviso de teste e piloto=True", "VERSÃO DE TESTE" in r["reply"] and r["piloto"] is True)
modos = {}
for i in range(20):
    uid = f"part-{i:03d}"
    cl.post("/start", json={"user_id": uid})
    modos[uid] = db.atribuir_modo(uid)
_c = db.get_connection()
_tot = {r["modo"]: r["n"] for r in _c.execute("SELECT modo, COUNT(*) AS n FROM atribuicoes GROUP BY modo")}
_c.close()
n_pln, n_kw = _tot.get("PLN", 0), _tot.get("Palavra-chave", 0)
verificar(f"sorteio equilibrado no total ({n_pln} PLN x {n_kw} palavra-chave)", abs(n_pln - n_kw) <= 1)
verificar("a mesma pessoa mantém o mesmo modo", all(db.atribuir_modo(u) == m for u, m in modos.items()))
u_kw = next(u for u, m in modos.items() if m == "Palavra-chave")
verificar("o servidor ignora o 'usar_pln' enviado pelo navegador", chat(u_kw, "matrícula", usar_pln=True).get_json()["modo"] == "Palavra-chave")

print("\n[6] Mensagens não entendidas")
r = chat("aluno-0003", "xyzzy qwerty plugh").get_json()
verificar("registra intenção 'nao_entendida'", r["intent"] == "nao_entendida" and r["pedir_feedback"] is False)
verificar("contador do painel encontra a mensagem", db.contar_nao_entendidas() >= 1)
adm = A.app.test_client(); entrar(adm, "atendente", SENHA_BOA)
html = adm.get("/admin?filtro=nao_entendidas").get_data(as_text=True)
verificar("filtro do painel mostra a mensagem não entendida", "xyzzy qwerty plugh" in html)

print("\n[7] Feedback")
d = chat("aluno-0004", "matrícula").get_json()["demanda_id"]
verificar("feedback de outra pessoa é recusado (403)", cl.post("/feedback", json={"user_id": "aluno-9999", "demanda_id": d, "resolvido": True}).status_code == 403)
verificar("feedback do dono é aceito", cl.post("/feedback", json={"user_id": "aluno-0004", "demanda_id": d, "resolvido": True}).status_code == 200)
verificar("feedback com tipos errados é recusado", cl.post("/feedback", json={"user_id": "aluno-0004", "demanda_id": "1", "resolvido": "sim"}).status_code == 400)

print("\n[8] Painel: edição e exportação")
d2 = chat("aluno-0005", "=1+1").get_json()["demanda_id"]
csv_texto = adm.get("/admin/export").get_data(as_text=True)
verificar("CSV neutraliza fórmulas (= vira '=)", "'=1+1" in csv_texto and ",=1+1," not in csv_texto)
verificar("editar demanda sem token CSRF é recusado", adm.post(f"/admin/demanda/{d2}", data={"status": "Resolvido", "parecer": "x"}).status_code == 400)
tok = token_csrf(adm, f"/admin/demanda/{d2}")
verificar("editar demanda com token funciona", adm.post(f"/admin/demanda/{d2}", data={"status": "Resolvido", "parecer": "ok", "csrf_token": tok}).status_code == 302
          and db.get_demanda(d2)["status"] == "Resolvido")
adm.post(f"/admin/demanda/{d2}", data={"status": "QUALQUER COISA", "parecer": "ok", "csrf_token": token_csrf(adm, f"/admin/demanda/{d2}")})
verificar("status inventado é trocado por 'Pendente'", db.get_demanda(d2)["status"] == "Pendente")

total, ok = len(resultados), sum(resultados)
print(f"\nResultado: {ok}/{total} verificações passaram.")
sys.exit(0 if ok == total else 1)
