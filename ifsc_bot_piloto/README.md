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

## Como funciona a API (para plugar no site ou WhatsApp depois)

**Iniciar conversa**
```
POST /start
Body: { "user_id": "identificador-do-usuario" }
Resposta: { "reply": "mensagem de boas-vindas + menu" }
```

**Enviar mensagem**
```
POST /chat
Body: { "user_id": "identificador-do-usuario", "message": "1" }
Resposta: { "reply": "texto de resposta do bot" }
```

O `user_id` pode ser qualquer identificador único da conversa: um ID de
sessão gerado no navegador (já feito no `index.html`) ou, no futuro, o
número de telefone de quem manda mensagem no WhatsApp. É esse campo que
faz o bot lembrar em qual menu a pessoa está.

## Fluxo implementado

- Mensagem de boas-vindas + menu principal (opções 1 a 4)
- Opção 1 abre um submenu (1.1 Requerimento, 1.2 Cursos ofertados,
  1.3 Inscrições em aberto) — digitando 0 volta ao menu principal
- Opções 2 e 3 respondem direto com telefone/e-mail e voltam ao menu
- Opção 4 informa que vai transferir para atendente + horário de atendimento
- **Texto livre agora passa pelo PLN** (veja seção abaixo) antes de cair
  na busca por palavra-chave antiga, que continua como rede de segurança
- Se a pessoa pedir "atendente"/"humano" em texto livre, o bot reforça o
  menu e pede para digitar 4
- Se nada for reconhecido, o bot mostra o menu novamente
- Digitar "menu" a qualquer momento volta para o início

## PLN (Processamento de Linguagem Natural)

Quando a pessoa escreve algo fora do menu numérico, o bot agora tenta
entender a **intenção** por trás da frase, não só procurar uma palavra
exata. A abordagem usada é **TF-IDF + Similaridade de Cosseno**:

1. `nlu/training_data.py` tem várias frases de exemplo para cada
   intenção (ex: pedidos de trancamento, saudações, agradecimentos...)
2. O texto do usuário é comparado com todas essas frases de exemplo
3. A intenção da frase mais parecida "vence", com uma confiança de 0 a 1
4. Se a confiança for baixa (< 0.30), o bot não arrisca e cai na busca
   por palavra-chave antiga como reforço; se ainda assim nada bater,
   mostra o menu de novo

Essa abordagem foi escolhida (em vez de um classificador probabilístico
tradicional) porque funciona bem mesmo com poucas frases de exemplo por
intenção — ideal para essa fase inicial do projeto.

O PLN é feito em **Python puro**, sem scikit-learn/scipy/joblib. Isso
evita um problema comum no Windows: políticas de segurança (Controle de
Aplicativo / Smart App Control) que bloqueiam os arquivos compilados
dessas bibliotecas e impedem o bot de abrir. Além disso, não existe
arquivo de modelo salvo em disco: o índice é montado na memória quando o
servidor inicia, então nunca fica um "modelo antigo" em cache.

**Intenções reconhecidas hoje**: justificativa_ausencia (resposta curta com link e e-mail da
secretaria), 1.1 (Requerimento), 1.2 (Cursos
ofertados), 1.3 (Inscrições abertas), 2 (CERE), 3 (Assistência
Estudantil), 4 (falar com atendente), além de saudação, agradecimento
e despedida (que o menu por palavra-chave sozinho nunca soube tratar).

**Como melhorar o PLN**: edite `nlu/training_data.py` adicionando mais
frases de exemplo (principalmente gírias, erros de digitação comuns e
formas diferentes de perguntar a mesma coisa) e reinicie o servidor
(`python app.py`). Não precisa treinar nada.

Opcional: `python train_model.py` mostra quantas frases cada intenção
tem e avisa se a mesma frase foi colocada em duas intenções diferentes.

**Transparência no painel**: cada demanda registrada guarda qual
intenção o PLN detectou e com que confiança — dá pra ver isso na fila
e ao abrir uma demanda específica. Isso ajuda a identificar frases que
o modelo ainda não está entendendo bem, pra adicionar como exemplo.

## Feedback: "Isso resolveu sua dúvida?"

Depois de uma resposta informativa (opções 2 e 3 do menu, opções do
submenu da Secretaria, ou uma pergunta em texto livre que o bot entendeu),
o chat mostra os botões **Sim / Não**.

- **Sim**: registra que a dúvida foi resolvida.
- **Não**: registra e mostra o botão **Falar com atendente**, que leva a
  pessoa direto para o atendimento humano, em qualquer ponto do menu.

O bot **não** pergunta isso depois de saudação, agradecimento, despedida,
pedido de atendente ou simples navegação de menu — nesses casos não há
"dúvida resolvida" para avaliar, e isso distorceria a taxa de resolução.

No painel, a taxa de resolução aparece **geral e separada por modo
(PLN x Palavra-chave)**, e a resposta de cada pessoa também vai para o
CSV exportado. É a base para comparar as duas abordagens no TCC.

## Painel da Secretaria Acadêmica

Toda mensagem trocada com o chatbot vira uma "demanda" registrada em um
banco SQLite (`painel.db`, criado automaticamente). O painel é a área
onde o atendente vê essa fila e dá andamento a cada uma.

**Acesso**: http://localhost:5000/admin/login

**Login**: não existe mais usuário nem senha padrão. Crie o atendente com
`python criar_admin.py` (ou `python criar_admin.py maria`). A senha antiga do
protótipo (`admin123`) fica **bloqueada**, mesmo que ainda esteja gravada em
um `painel.db` antigo: rode o script para definir uma senha nova.

O que dá pra fazer no painel:
- Ver a fila de todas as mensagens recebidas pelo bot, com data/hora e usuário
- Filtrar por status: Pendente / Em análise / Resolvido
- Filtrar as mensagens **não entendidas** pelo bot (aparecem com a intenção
  `nao_entendida`): são as perguntas reais que viram novos exemplos de treino
- Abrir uma demanda, mudar o status e escrever um parecer/observação
- Exportar tudo em CSV (botão "Exportar CSV")

## Teste piloto e publicação

O código já vem preparado para um **teste piloto** com poucas pessoas e para
ficar na internet (por exemplo, no PythonAnywhere). Tudo se liga por variáveis
de ambiente; sem elas, o programa roda como sempre, só na sua máquina.

| Variável | Para quê |
|---|---|
| `MODO_PILOTO=1` | Mostra o aviso de teste na boas-vindas e **sorteia** o modo (PLN ou palavra-chave) de cada pessoa, de forma equilibrada. A pessoa não escolhe nem vê qual modo está usando |
| `APP_PUBLICO=1` | Use quando o app estiver na internet com HTTPS: o cookie de sessão fica "secure" e o IP é lido do proxy |
| `SECRET_KEY` | Chave que assina a sessão. Se não definir, uma chave aleatória é criada em `.secret_key` |
| `PAINEL_DB` | Caminho do arquivo do banco (útil para guardá-lo fora da pasta do código e fazer backup) |
| `APP_HOST`, `PORT`, `FLASK_DEBUG` | Só para `python app.py`. Padrão: `127.0.0.1`, `5000`, **debug desligado** |

**O que já está protegido**
- Sem senha padrão; senha forte (mínimo de 12 caracteres, com letras e números/símbolos); guardada só como hash
- Bloqueio temporário após várias tentativas erradas de login (8 por usuário ou 20 por IP, em 15 minutos)
- Formulários do painel com token CSRF; cookie de sessão HttpOnly, SameSite e (publicado) Secure; sessão expira em 8 horas
- Painel sem cache e sem poder ser embutido em outros sites
- Chat: tamanho máximo de mensagem (500 caracteres), `user_id` validado e limite de mensagens por minuto
- Feedback só aceito do próprio autor da mensagem (evita distorcer as métricas do piloto)
- CSV exportado neutraliza "injeção de fórmulas" do Excel

**Limites conhecidos (aceitáveis para um piloto)**
- Os limites de tentativas e o estado da conversa ficam **em memória**: funcionam com um único processo do servidor
  (o padrão do plano gratuito do PythonAnywhere) e zeram quando ele reinicia
- O painel usa o mesmo endereço público do chat (`/admin`); a proteção é o login
- Não há "esqueci a senha": para trocar, rode `python criar_admin.py` no servidor

**Passo a passo resumido (PythonAnywhere ou outro servidor)**
1. Envie o código (sem `painel.db`, sem `.secret_key` e sem `.csv`; o `.gitignore` já cuida disso se usar o GitHub)
2. `pip install -r requirements.txt`
3. Defina `MODO_PILOTO=1` e `APP_PUBLICO=1`
4. `python criar_admin.py` para cadastrar o atendente
5. Aponte o servidor web (arquivo WSGI) para o objeto `app` de `app.py`
6. Abra o link, converse, e entre em `/admin` para conferir o registro
7. Faça backup do `painel.db` (ou do CSV exportado) com frequência

**Testes automáticos**: `python testar_seguranca.py` confere cada proteção acima
com um banco temporário (não mexe no seu `painel.db`).

**Cuidados com os dados (LGPD)**: o painel guarda as mensagens dos participantes.
Oriente a não informar dados pessoais, acesse o painel só com a conta de atendente,
use os dados apenas para o trabalho e apague ou anonimize ao final.

## Próximos passos sugeridos

1. **Melhorar o PLN**: adicionar mais frases de exemplo em
   `nlu/training_data.py` conforme forem aparecendo perguntas reais que
   o modelo não entendeu (o painel mostra a intenção detectada e a
   confiança de cada demanda, o que ajuda a identificar esses casos).
   Mais pra frente, dá pra evoluir para spaCy, embeddings, ou até um LLM.
2. **Persistência**: hoje o estado da conversa fica em memória
   (dicionário Python) e se perde se o servidor reiniciar. Para
   produção, vale mover para Redis ou um banco simples (SQLite/Postgres).
3. **WhatsApp**: integrar via Twilio API for WhatsApp (ou WhatsApp
   Business API oficial) — cria-se uma rota `/whatsapp` que recebe o
   webhook, usa o número do remetente como `user_id` e chama
   `bot.process_message()` normalmente.
4. **Site**: incorporar o `index.html` (ou adaptar seu CSS) como um
   widget flutuante no canto da página do câmpus.
5. **Múltiplos atendentes**: já é possível cadastrar vários com
   `python criar_admin.py nome`; falta uma tela no painel para isso e para
   trocar a própria senha.
6. **Segurança básica**: quando for para produção, considerar rate
   limiting na rota `/chat` para evitar abuso, e usar HTTPS.
