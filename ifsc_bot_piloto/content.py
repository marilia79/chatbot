# -*- coding: utf-8 -*-
"""
Todos os textos/conteúdos do chatbot ficam centralizados aqui.
Assim, para atualizar uma informação (telefone, link, texto de boas-vindas),
não é preciso mexer na lógica do bot (bot.py) - só editar este arquivo.
"""

WELCOME = (
    "Olá! Seja muito bem-vindo(a) ao IFSC Câmpus Garopaba!\n"
    "Sou o assistente virtual da Secretaria Acadêmica e estou aqui para te "
    "ajudar com informações sobre nossos cursos, processos seletivos e "
    "serviços acadêmicos.\n"
    "Nosso horário de atendimento humano é das 8h às 20h, de segunda a "
    "sexta-feira.\n"
    "Nosso endereço é na R. Maria Aparecida Barbosa, 153 - Campo Duna, "
    "Garopaba - SC, 88495-000.\n\n"
    "Aviso de privacidade: suas mensagens ficam registradas no painel da "
    "Secretaria para melhoria do atendimento; por favor, não informe dados "
    "pessoais (como CPF, matrícula ou telefone).\n"
)

MAIN_MENU = (
    "Escolha uma das opções abaixo digitando o número correspondente:\n\n"
    "1 - Secretaria Acadêmica/Registro Acadêmico\n"
    "2 - CERE - Coordenadoria de Relações Externas\n"
    "3 - Coordenação/Assistência Estudantil\n"
    "4 - Falar com a atendente\n\n"
    "Se nenhuma das opções acima resolver, você também pode escrever sua "
    "pergunta diretamente.\n"
    "Por exemplo: em vez de perguntar \"Como faço minha matrícula?\", "
    "você pode escrever somente \"matrícula\"."
)

SUBMENU_1 = (
    "Secretaria Acadêmica/Registro Acadêmico - escolha uma opção:\n\n"
    "1 - Requerimento\n"
    "2 - Cursos ofertados\n"
    "3 - Cursos com inscrições em aberto\n\n"
    "Digite 0 para voltar ao menu principal."
)

VOLTAR_MENU = "Digite 0 para voltar ao menu principal."

OPTION_1_1 = (
    "Requerimento\n\n"
    "Para tratar de assuntos como:\n"
    "- Adaptação curricular\n"
    "- Ajuste de matrícula\n"
    "- Cancelamento de matrícula\n"
    "- Cancelamento de matrícula em unidade curricular\n"
    "- Justificativa de ausência\n"
    "- Matrícula isolada\n"
    "- Reingresso\n"
    "- Segunda chamada avaliativa\n"
    "- Trancamento de matrícula\n"
    "- Validação de unidade curricular\n"
    "- Colação de Grau\n"
    "- Emissão de Certificados e Diplomas\n"
    "- Atividade domiciliar (problema de locomoção de aluno)\n\n"
    "Devem ser solicitados via requerimento eletrônico pelo link:\n"
    "https://www.ifsc.edu.br/en/web/campus-garopaba/registro-academico-secretaria"
)

# Resposta curta e direta para o serviço mais perguntado: justificar falta.
# (Os demais serviços de requerimento continuam na lista geral OPTION_1_1.)
OPTION_JUSTIFICATIVA_AUSENCIA = (
    "Justificativa de ausência\n\n"
    "Para justificar uma falta, solicite a \"Justificativa de ausência\" pelo "
    "Requerimento Online, anexando o documento comprobatório (por exemplo, "
    "atestado médico):\n"
    "https://www.ifsc.edu.br/en/web/campus-garopaba/registro-academico-secretaria\n\n"
    "Se preferir, baixe o modelo de requerimento na mesma página, preencha e "
    "envie por e-mail para secretaria.gpb@ifsc.edu.br com o documento anexado."
)

OPTION_1_2 = (
    "Cursos ofertados\n\n"
    "Através do link do site do IFSC, você consegue verificar todos os "
    "cursos disponibilizados no Câmpus IFSC Garopaba:\n"
    "https://www.ifsc.edu.br/en/web/campus-garopaba/cursos\n\n"
    "Você também pode nos acompanhar pelo nosso Instagram: @ifsc.garopaba"
)

OPTION_1_3 = (
    "Cursos com inscrições em aberto\n\n"
    "Conheça nossos cursos que estão com inscrições em aberto, clique no link:\n"
    "https://sistemadeingresso.ifsc.edu.br/inscricao/escolher_curso.php"
)

OPTION_2 = (
    "CERE - Coordenadoria de Relações Externas\n\n"
    "Assuntos relacionados a comunicações, imprensa, eventos e o suporte a "
    "estágios e empregos para os estudantes, entre em contato através do "
    "telefone (48) 3254-7336 ou e-mail cere.garopaba@ifsc.edu.br"
)

OPTION_3 = (
    "Coordenação/Assistência Estudantil\n\n"
    "Assuntos relacionados com aluno em sala de aula, como: saída de aluno "
    "antes do horário de aula, auxílio psicológico e assistência financeira "
    "estudantil, devem ser tratados com a Coordenadoria Pedagógica pelo "
    "telefone (48) 3254-7329 ou (48) 9940-0198, ou e-mail "
    "assistenciaestudantil.gpb@ifsc.edu.br"
)

OPTION_4 = (
    "Certo, vou te transferir para um atendente humano.\n"
    "Nosso horário de atendimento é das 8h às 20h, de segunda a "
    "sexta-feira. Por favor, aguarde só um instante."
)

INVALID_OPTION = (
    "Não entendi essa opção. Por favor, digite um número válido do menu."
)

FALLBACK_ASK_MENU = (
    "Não consegui entender sua mensagem. Aqui está o menu novamente:\n\n"
    + MAIN_MENU
)

FALLBACK_WANTS_ATTENDANT = (
    "Entendi que você quer falar com um atendente. Para isso, digite a "
    "opção 4 no menu abaixo:\n\n" + MAIN_MENU
)

# Mostrado no início da conversa quando o servidor roda em modo piloto.
AVISO_PILOTO = (
    "VERSÃO DE TESTE (PILOTO): este atendimento faz parte de uma pesquisa "
    "acadêmica. Suas mensagens ficam registradas para melhorar o chatbot; "
    "por favor, não informe dados pessoais (como CPF, matrícula ou telefone)."
)

SUGGESTION_TEMPLATE = (
    "Talvez isso ajude com o que você perguntou:\n\n{resposta}\n\n"
    "Se não era isso, digite 'menu' para ver todas as opções."
)

SAUDACAO_BOM_DIA_RESPOSTA = (
    "Bom dia! Em que posso te ajudar?\n\n" + MAIN_MENU
)

SAUDACAO_BOA_TARDE_RESPOSTA = (
    "Boa tarde! Em que posso te ajudar?\n\n" + MAIN_MENU
)

SAUDACAO_BOA_NOITE_RESPOSTA = (
    "Boa noite! Em que posso te ajudar?\n\n" + MAIN_MENU
)

SAUDACAO_OI_RESPOSTA = (
    "Oi! Em que posso te ajudar?\n\n" + MAIN_MENU
)

AGRADECIMENTO_RESPOSTA = (
    "Por nada! Se precisar de mais alguma coisa, é só chamar. "
    "Digite 'menu' para ver as opções novamente."
)

DESPEDIDA_RESPOSTA = (
    "Até mais! Se precisar, é só voltar a qualquer momento. Bons estudos!"
)

# --------------------------------------------------------------------------
# Reconhecimento simples por palavra-chave (fase pré-PLN).
# Cada palavra-chave (sem acento, minúscula) aponta para um "código" de opção.
# O bot.py usa esse mapa para sugerir uma resposta quando o usuário escreve
# um texto livre em vez de escolher um número do menu.
# --------------------------------------------------------------------------
KEYWORDS = {
    # -> Justificativa de ausência (resposta própria; vem antes de 1.1 para
    #    "ganhar" de palavras mais genéricas na mesma frase)
    "justificativa": "justificativa_ausencia",
    "justificar": "justificativa_ausencia",
    "falta": "justificativa_ausencia",
    "faltei": "justificativa_ausencia",
    "ausencia": "justificativa_ausencia",
    "atestado": "justificativa_ausencia",

    # -> 1.1 Requerimento
    "matricula": "1.1",
    "adaptacao curricular": "1.1",
    "cancelamento": "1.1",
    "trancamento": "1.1",
    "reingresso": "1.1",
    "segunda chamada": "1.1",
    "validacao": "1.1",
    "colacao de grau": "1.1",
    "diploma": "1.1",
    "certificado": "1.1",
    "requerimento": "1.1",
    "atividade domiciliar": "1.1",

    # -> 1.2 Cursos ofertados
    "curso": "1.2",
    "cursos": "1.2",
    "quais cursos": "1.2",

    # -> 1.3 Inscrições
    "inscricao": "1.3",
    "inscricoes": "1.3",
    "processo seletivo": "1.3",
    "vaga": "1.3",
    "vagas": "1.3",
    "edital": "1.3",

    # -> 2 CERE
    "estagio": "2",
    "emprego": "2",
    "evento": "2",
    "imprensa": "2",
    "comunicacao": "2",
    "cere": "2",

    # -> 3 Assistência estudantil
    "psicologico": "3",
    "psicologo": "3",
    "assistencia estudantil": "3",
    "auxilio financeiro": "3",
    "bolsa": "3",
    "sair mais cedo": "3",

    # -> 4 Atendente (tratado à parte via FALLBACK_WANTS_ATTENDANT)
    "atendente": "4",
    "humano": "4",
    "pessoa": "4",
    "falar com alguem": "4",
}
