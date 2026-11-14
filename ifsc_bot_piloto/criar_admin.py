# -*- coding: utf-8 -*-
"""
Cadastra (ou troca a senha de) um atendente que pode entrar no painel.

Uso:
    python criar_admin.py              -> cria/atualiza o usuário "admin"
    python criar_admin.py maria        -> cria/atualiza o usuário "maria"

A senha é digitada sem aparecer na tela e nunca fica gravada em texto puro
(só o hash). Regras: mínimo de 12 caracteres, com letras e também números ou
símbolos, sem o nome do usuário e sem senhas fáceis. A senha antiga do
protótipo (admin123) está bloqueada.

Para uso automático (sem digitar), defina a variável ADMIN_PASSWORD antes.
"""
import getpass
import os
import sys

import db

db.init_db()
usuario = (sys.argv[1] if len(sys.argv) > 1 else "admin").strip()
if not usuario:
    sys.exit("Informe um nome de usuário.")

senha = os.environ.get("ADMIN_PASSWORD")
if senha is None:
    senha = getpass.getpass(f"Nova senha para '{usuario}' (mín. {db.TAMANHO_MIN_SENHA} caracteres): ")
    if senha != getpass.getpass("Repita a senha: "):
        sys.exit("As senhas não são iguais. Nada foi alterado.")

try:
    resultado = db.criar_ou_atualizar_usuario(usuario, senha)
except ValueError as erro:
    sys.exit(f"Senha recusada: {erro}")

print(f"Pronto: usuário '{usuario}' {resultado}. Reinicie o servidor se ele já estiver rodando.")
