# Chatbot Secretaria Acadêmica - IFSC Câmpus Garopaba

Chatbot em Flask com PLN (classificador de intenção por similaridade de
texto) para entender mensagens livres, além do menu numérico tradicional,
e um painel para a secretaria gerenciar as demandas recebidas.

## Estrutura do projeto

```
ifsc_bot/
├── app.py             -> rotas Flask (/, /start, /chat, /admin/*)
├── bot.py             -> lógica/máquina de estados do chatbot
├── content.py         -> todos os textos e palavras-chave (edite aqui!)
├── db.py              -> banco SQLite: demandas do chatbot e login dos atendentes
├── criar_admin.py     -> cadastra o atendente do painel (senha forte, sem senha padrão)
├── testar_seguranca.py-> testes automáticos do login, do chat e do modo piloto
├── .gitignore         -> impede enviar painel.db, chave e CSVs ao GitHub
├── train_model.py     -> (opcional) confere os exemplos de treino do PLN
├── requirements.txt
├── painel.db                    -> criado automaticamente (não versionar)
├── nlu/
│   ├── training_data.py         -> frases de exemplo de cada intenção (edite aqui!)
│   └── classifier.py            -> PLN em Python puro (TF-IDF + cosseno)
└── templates/
    ├── index.html          -> janela de chat simples para testar no navegador
    ├── admin_login.html    -> tela de login do painel
    ├── admin_dashboard.html-> fila de demandas do painel
    └── admin_demanda.html  -> tela de status/parecer de uma demanda
```

## Como rodar localmente

```bash
cd ifsc_bot
pip install -r requirements.txt
python criar_admin.py      # cadastra o atendente do painel (senha forte, digitada sem aparecer)
python app.py
```

Depois abra **http://localhost:5000** no navegador — vai aparecer uma
janela de chat já conversando com o bot.

