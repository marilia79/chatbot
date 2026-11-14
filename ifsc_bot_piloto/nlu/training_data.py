# -*- coding: utf-8 -*-
"""
Dados de treino do classificador de intenções (PLN).

Cada chave é o "código" da intenção (o mesmo usado em content.py para
montar a resposta) e o valor é uma lista de frases de exemplo de como
uma pessoa real poderia escrever pedindo aquilo.

IMPORTANTE: quanto mais frases variadas você adicionar aqui (gírias,
erros de digitação comuns, formas informais), melhor o modelo fica.
Depois de editar este arquivo, rode `python train_model.py` na raiz do
projeto para o modelo aprender de novo com os exemplos atualizados.
"""

INTENT_EXAMPLES = {

    # ---- 1.1 Requerimento (matrícula, trancamento, diploma, etc.) ----
    "1.1": [
        "quero trancar minha matricula",
        "como faço para trancar a matricula",
        "preciso cancelar minha matricula",
        "quero cancelar uma disciplina",
        "como peço segunda chamada da prova",
        "perdi a prova e preciso de segunda chamada",
        "como faço adaptação curricular",
        "quero fazer ajuste de matricula",
        "como peço reingresso no curso",
        "quero voltar a estudar depois que tranquei",
        "como faço para pegar meu diploma",
        "quero emitir meu certificado",
        "preciso do meu certificado de conclusão",
        "como faço uma matricula isolada",
        "quero fazer só uma disciplina isolada",
        "como peço colação de grau",
        "quando é a colação de grau",
        "preciso validar uma disciplina que já cursei",
        "quero validar unidade curricular",
        "como faço um requerimento",
        "onde peço um requerimento online",
        "preciso de atividade domiciliar porque não consigo ir presencial",
        "estou com problema de locomoção e preciso estudar de casa",
        "quero cancelar minha vaga no curso",
    ],

    # ---- 1.2 Cursos ofertados ----
    "justificativa_ausencia": [
        "faltei ontem",
        "faltei hoje na aula",
        "faltei na aula",
        "faltei e quero justificar",
        "preciso justificar minha falta",
        "como justificar falta",
        "como justificar uma ausencia",
        "quero justificar a falta com atestado",
        "justificativa de falta",
        "justificar ausencia",
        "nao pude ir a aula e quero justificar",
        "perdi aula por motivo de saude",
        "tenho atestado medico o que eu faco",
        "faltei por problema de saude",
        "como justifico uma falta",
        "quero justificativa de ausencia",
        "preciso de um atestado para a falta",
        "faltei numa aula e quero justificar",
    ],

    "1.2": [
        "quais cursos vocês tem",
        "quais cursos são oferecidos no campus",
        "quero saber quais cursos existem",
        "quais sao os cursos disponiveis",
        "tem curso de informatica",
        "vocês tem curso técnico",
        "quais cursos técnicos tem no garopaba",
        "quero saber mais sobre os cursos do ifsc",
        "quais graduações vocês oferecem",
        "tem curso superior nesse campus",
        "lista de cursos do campus garopaba",
        "quero conhecer os cursos",
        "onde vejo os cursos ofertados",
    ],

    # ---- 1.3 Cursos com inscrições em aberto ----
    "1.3": [
        "quais cursos estão com inscrição aberta",
        "tem processo seletivo aberto agora",
        "quero saber se tem vaga aberta",
        "como faço pra ver os editais abertos",
        "onde vejo as inscrições abertas",
        "tem edital aberto para algum curso",
        "quero me inscrever em um curso",
        "como faço pra entrar num curso agora",
        "tem vestibular aberto",
        "quero saber sobre processo seletivo",
        "quais editais estão abertos no momento",
        "queria saber se ainda dá tempo de me inscrever",
    ],

    # ---- 2 CERE (estágio, emprego, eventos, imprensa) ----
    "2": [
        "como faço para conseguir um estagio",
        "quero saber sobre vagas de estagio",
        "tem vaga de emprego para estudante",
        "como funciona o processo de estagio",
        "quero informações sobre emprego",
        "preciso falar sobre um evento do campus",
        "quero saber sobre eventos que vão acontecer",
        "quero fazer uma matéria sobre o campus",
        "sou da imprensa e preciso de informações",
        "como entro em contato com a comunicação do campus",
        "quero saber sobre parcerias com empresas",
        "preciso de ajuda para achar emprego",
    ],

    # ---- 3 Coordenação/Assistência Estudantil ----
    "3": [
        "preciso sair mais cedo da aula",
        "posso sair antes do horário",
        "quero saber sobre auxilio financeiro",
        "preciso de ajuda psicologica",
        "quero falar com um psicologo",
        "estou passando por um problema emocional",
        "preciso de assistencia estudantil",
        "quero saber sobre bolsa auxilio",
        "tem algum auxilio para quem tem dificuldade financeira",
        "preciso de apoio psicologico na escola",
        "meu filho precisa sair mais cedo",
        "quero saber sobre a coordenadoria pedagogica",
    ],

    # ---- 4 Falar com atendente / humano ----
    "4": [
        "quero falar com uma pessoa",
        "quero falar com um atendente",
        "pode me transferir para um humano",
        "isso nao resolveu meu problema quero falar com alguem",
        "preciso de atendimento humano",
        "quero falar com a secretaria diretamente",
        "ninguem consegue me ajudar aqui",
        "quero conversar com um funcionario",
        "pode chamar um atendente",
        "gostaria de falar com uma pessoa de verdade",
    ],

    # ---- Saudação: bom dia ----
    "saudacao_bom_dia": [
        "bom dia",
        "bom dia, tudo bem?",
        "bom dia, gostaria de uma informação",
        "bom dia, preciso de ajuda",
        "bom diaa",
    ],

    # ---- Saudação: boa tarde ----
    "saudacao_boa_tarde": [
        "boa tarde",
        "boa tarde, tudo bem?",
        "boa tarde, gostaria de uma informação",
        "boa tarde, preciso de ajuda",
        "boa tardee",
    ],

    # ---- Saudação: boa noite ----
    "saudacao_boa_noite": [
        "boa noite",
        "boa noite, tudo bem?",
        "boa noite, gostaria de uma informação",
        "boa noite, preciso de ajuda",
    ],

    # ---- Saudação: oi/olá (sem período do dia definido) ----
    "saudacao_oi": [
        "oi",
        "ola",
        "oi tudo bem",
        "e ai",
        "opa",
        "oiê",
        "olá, preciso de ajuda",
        "oi, gostaria de uma informação",
    ],

    # ---- Agradecimento ----
    "agradecimento": [
        "obrigado",
        "obrigada",
        "valeu",
        "vlw",
        "muito obrigado pela ajuda",
        "brigadao",
        "agradeço a ajuda",
        "top, obrigado",
        "show, valeu mesmo",
    ],

    # ---- Despedida ----
    "despedida": [
        "tchau",
        "ate mais",
        "falou",
        "flw",
        "vlw flw",
        "ate logo",
        "vou indo, obrigado",
        "por hoje é só, tchau",
        "ate a proxima",
    ],
}
