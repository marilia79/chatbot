# -*- coding: utf-8 -*-
"""
Camada de acesso a dados (SQLite) do painel da Secretaria Acadêmica.

Duas tabelas:
- demandas: cada mensagem trocada com o chatbot vira uma linha aqui
- usuarios: login dos atendentes que acessam o painel

Uso de SQLite puro (sem ORM) para manter a fase básica simples.
Quando o volume crescer, dá pra trocar por Postgres/MySQL sem mudar
muito a interface destas funções.
"""

import os
import random
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# O banco fica ao lado do código, a menos que a variável de ambiente
# PAINEL_DB aponte para outro lugar (útil para backups e para os testes).
DB_PATH = Path(os.environ.get("PAINEL_DB", Path(__file__).parent / "painel.db"))

# Senha que existia no protótipo antigo. Fica BLOQUEADA: ninguém entra com ela.
SENHA_PADRAO_ANTIGA = "admin123"
TAMANHO_MIN_SENHA = 12
MODOS_PILOTO = ("PLN", "Palavra-chave")

STATUS_PENDENTE = "Pendente"
STATUS_EM_ANALISE = "Em análise"
STATUS_RESOLVIDO = "Resolvido"
STATUS_OPCOES = [STATUS_PENDENTE, STATUS_EM_ANALISE, STATUS_RESOLVIDO]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria as tabelas se não existirem. Não cria nenhum usuário padrão."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS demandas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            resposta_bot TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            parecer TEXT NOT NULL DEFAULT '',
            atendente TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS atribuicoes (
            user_id TEXT PRIMARY KEY,
            modo TEXT NOT NULL,
            data_hora TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # Migração leve: adiciona as colunas de PLN em bancos criados antes
    # dessa funcionalidade existir. Se a coluna já existir, ignora o erro.
    colunas_novas = {
        "intent_detectado": "TEXT",
        "confianca": "REAL",
        "modo": "TEXT",
        "resolvido_pelo_usuario": "TEXT",
    }
    colunas_existentes = {row["name"] for row in conn.execute("PRAGMA table_info(demandas)").fetchall()}
    for nome_coluna, tipo in colunas_novas.items():
        if nome_coluna not in colunas_existentes:
            conn.execute(f"ALTER TABLE demandas ADD COLUMN {nome_coluna} {tipo}")
    conn.commit()

    # Nenhum usuário padrão é criado: o atendente é cadastrado com uma senha
    # forte pelo script criar_admin.py (veja o README).
    conn.close()


def log_demanda(user_id: str, mensagem: str, resposta_bot: str, intent_detectado: str = None, confianca: float = None, modo: str = None) -> int:
    """Registra uma nova demanda (toda mensagem enviada ao bot) e devolve o id gerado."""
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO demandas (user_id, mensagem, resposta_bot, data_hora, status, parecer, atendente, intent_detectado, confianca, modo)
        VALUES (?, ?, ?, ?, ?, '', '', ?, ?, ?)
        """,
        (user_id, mensagem, resposta_bot, datetime.now().isoformat(timespec="seconds"), STATUS_PENDENTE, intent_detectado, confianca, modo),
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return novo_id


def registrar_feedback(demanda_id: int, resolvido: bool) -> None:
    """Salva a resposta da pessoa para 'isso resolveu sua dúvida?'."""
    conn = get_connection()
    conn.execute(
        "UPDATE demandas SET resolvido_pelo_usuario = ? WHERE id = ?",
        ("Sim" if resolvido else "Não", demanda_id),
    )
    conn.commit()
    conn.close()


def list_demandas(status_filtro: str = None, nao_entendidas: bool = False):
    conn = get_connection()
    condicoes, params = [], []
    if status_filtro and status_filtro in STATUS_OPCOES:
        condicoes.append("status = ?"); params.append(status_filtro)
    if nao_entendidas:
        condicoes.append("intent_detectado = 'nao_entendida'")
    where = (" WHERE " + " AND ".join(condicoes)) if condicoes else ""
    rows = conn.execute(f"SELECT * FROM demandas{where} ORDER BY id DESC", params).fetchall()
    conn.close()
    return rows


def get_demanda(demanda_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM demandas WHERE id = ?", (demanda_id,)).fetchone()
    conn.close()
    return row


def update_demanda(demanda_id: int, status: str, parecer: str, atendente: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE demandas SET status = ?, parecer = ?, atendente = ? WHERE id = ?",
        (status, parecer, atendente, demanda_id),
    )
    conn.commit()
    conn.close()


def contar_por_status():
    conn = get_connection()
    rows = conn.execute("SELECT status, COUNT(*) AS total FROM demandas GROUP BY status").fetchall()
    conn.close()
    contagem = {status: 0 for status in STATUS_OPCOES}
    for row in rows:
        contagem[row["status"]] = row["total"]
    contagem["Total"] = sum(contagem.values())
    return contagem


def estatisticas_resolucao():
    """
    Taxa de resolução com base no feedback dado pelas pessoas
    ('isso resolveu sua dúvida?'), no total e separado por modo
    (PLN vs Palavra-chave) - útil para comparar as duas abordagens.
    """
    conn = get_connection()

    def _calcular(modo_filtro=None):
        if modo_filtro:
            rows = conn.execute(
                "SELECT resolvido_pelo_usuario, COUNT(*) AS total FROM demandas "
                "WHERE modo = ? AND resolvido_pelo_usuario IS NOT NULL "
                "GROUP BY resolvido_pelo_usuario",
                (modo_filtro,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT resolvido_pelo_usuario, COUNT(*) AS total FROM demandas "
                "WHERE resolvido_pelo_usuario IS NOT NULL "
                "GROUP BY resolvido_pelo_usuario"
            ).fetchall()
        sim = next((r["total"] for r in rows if r["resolvido_pelo_usuario"] == "Sim"), 0)
        nao = next((r["total"] for r in rows if r["resolvido_pelo_usuario"] == "Não"), 0)
        total = sim + nao
        percentual = round((sim / total) * 100, 1) if total > 0 else None
        return {"sim": sim, "nao": nao, "total": total, "percentual": percentual}

    resultado = {
        "geral": _calcular(),
        "PLN": _calcular("PLN"),
        "Palavra-chave": _calcular("Palavra-chave"),
    }
    conn.close()
    return resultado


# Hash de uma senha qualquer, usado só para gastar o mesmo tempo quando o
# usuário não existe (assim não dá para descobrir usuários pelo tempo de resposta).
_HASH_FALSO = generate_password_hash("senha-falsa-para-igualar-o-tempo")


def verificar_login(username: str, password: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
    conn.close()
    hash_guardado = row["password_hash"] if row else _HASH_FALSO
    senha_correta = check_password_hash(hash_guardado, password)
    if not row or not senha_correta:
        return False
    # A senha do protótipo antigo nunca é aceita, mesmo que ainda esteja no banco.
    return password != SENHA_PADRAO_ANTIGA


def validar_senha(username: str, password: str):
    """Devolve uma mensagem de erro, ou None se a senha for aceitável."""
    if len(password) < TAMANHO_MIN_SENHA:
        return f"A senha precisa ter pelo menos {TAMANHO_MIN_SENHA} caracteres."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[^A-Za-z]", password):
        return "Use letras e também números ou símbolos."
    baixa = password.lower()
    if username and username.lower() in baixa:
        return "A senha não pode conter o nome de usuário."
    for fraca in ("admin123", "senha", "password", "123456", "qwerty"):
        if fraca in baixa:
            return "Essa senha é fácil de adivinhar. Escolha outra."
    return None


def criar_ou_atualizar_usuario(username: str, password: str) -> str:
    """Cria o atendente ou troca a senha dele. Devolve 'criado' ou 'atualizado'."""
    erro = validar_senha(username, password)
    if erro:
        raise ValueError(erro)
    conn = get_connection()
    existe = conn.execute("SELECT 1 FROM usuarios WHERE username = ?", (username,)).fetchone()
    novo_hash = generate_password_hash(password)
    if existe:
        conn.execute("UPDATE usuarios SET password_hash = ? WHERE username = ?", (novo_hash, username))
        resultado = "atualizado"
    else:
        conn.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)", (username, novo_hash))
        resultado = "criado"
    conn.commit()
    conn.close()
    return resultado


def total_usuarios() -> int:
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"]
    conn.close()
    return n


def usuarios_com_senha_padrao() -> list:
    """Usuários cujo hash ainda corresponde à senha antiga (para avisar no início)."""
    conn = get_connection()
    rows = conn.execute("SELECT username, password_hash FROM usuarios").fetchall()
    conn.close()
    return [r["username"] for r in rows if check_password_hash(r["password_hash"], SENHA_PADRAO_ANTIGA)]


# --------------------------------------------------------------------------
# Piloto: sorteio equilibrado do modo e conferência do feedback
# --------------------------------------------------------------------------

def atribuir_modo(user_id: str) -> str:
    """
    Sorteio equilibrado (PLN x Palavra-chave) para o teste piloto: quem já foi
    sorteado mantém o modo; um novo participante vai para o grupo que tem menos
    gente (empate: sorteia). Assim, com poucas pessoas, os grupos não ficam
    desbalanceados por acaso.
    """
    conn = get_connection()
    row = conn.execute("SELECT modo FROM atribuicoes WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        conn.close()
        return row["modo"]
    contagem = {m: 0 for m in MODOS_PILOTO}
    for r in conn.execute("SELECT modo, COUNT(*) AS n FROM atribuicoes GROUP BY modo").fetchall():
        if r["modo"] in contagem:
            contagem[r["modo"]] = r["n"]
    menor = min(contagem.values())
    modo = random.choice([m for m, n in contagem.items() if n == menor])
    conn.execute(
        "INSERT INTO atribuicoes (user_id, modo, data_hora) VALUES (?, ?, ?)",
        (user_id, modo, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    return modo


def demanda_pertence_a(demanda_id: int, user_id: str) -> bool:
    """Confere se a demanda foi gerada por este user_id (evita feedback de terceiros)."""
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM demandas WHERE id = ? AND user_id = ?", (demanda_id, user_id)).fetchone()
    conn.close()
    return row is not None


def contar_nao_entendidas() -> int:
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) AS n FROM demandas WHERE intent_detectado = 'nao_entendida'").fetchone()["n"]
    conn.close()
    return n

