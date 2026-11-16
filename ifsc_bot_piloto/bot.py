# -*- coding: utf-8 -*-
"""
Núcleo do chatbot da Secretaria Acadêmica - IFSC Câmpus Garopaba.

Tem PLN: para texto livre (fora dos números do menu), o bot pode usar
um classificador de intenção (nlu/classifier.py) treinado com frases de
exemplo, em vez de só procurar palavras-chave exatas.

O parâmetro `usar_pln` (em process_message) liga/desliga essa camada -
isso permite comparar, na hora, o comportamento "com PLN" e "sem PLN"
(só busca por palavra-chave), útil para demonstração/comparação no TCC.

Ordem de prioridade ao interpretar uma mensagem:
1. Números do menu (1, 2, 3, 4, 0) -> navegação direta, sem PLN.
2. Se usar_pln=True: classificador de PLN -> tenta entender a frase
   mesmo com variações de escrita, gírias, etc.
3. Busca por palavra-chave (content.KEYWORDS) -> roda sempre, seja como
   única camada (usar_pln=False) ou como rede de segurança do PLN.
4. Se nada funcionar, mostra o menu de novo.

Cada resposta também indica se é uma "resposta final" (uma informação
de verdade, não só navegação de menu) - isso é usado pelo app.py/painel
para decidir quando vale perguntar "isso resolveu sua dúvida?".
"""

import unicodedata
import content
from nlu import classifier as nlu_classifier

STATE_MAIN = "MAIN"
STATE_SUBMENU_1 = "SUBMENU_1"

# Comando interno enviado pelo botão "Falar com atendente" do chat (que
# aparece quando a pessoa diz que a dúvida NÃO foi resolvida). Funciona em
# qualquer ponto do menu, ao contrário de digitar "4" dentro de um submenu.
COMANDO_ATENDENTE = "__atendente__"

# Só estas intenções são respostas informativas de verdade. Saudação,
# agradecimento, despedida e pedido de atendente não entram: perguntar
# "isso resolveu sua dúvida?" depois delas não faz sentido e distorceria
# a taxa de resolução.
# Registrada no painel quando o bot não entendeu a mensagem de texto livre.
INTENCAO_NAO_ENTENDIDA = "nao_entendida"

INTENCOES_INFORMATIVAS = ("1.1", "1.2", "1.3", "2", "3", "justificativa_ausencia")

_sessions = {}  # user_id -> estado atual


def _get_state(user_id: str) -> str:
    return _sessions.get(user_id, STATE_MAIN)


def _set_state(user_id: str, state: str) -> None:
    _sessions[user_id] = state


def _normalize(text: str) -> str:
    """Minúsculas e sem acento, para facilitar comparação/keyword matching."""
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def _find_keyword_match(text_normalized: str):
    """Procura alguma palavra-chave conhecida dentro do texto do usuário."""
    for keyword, option_code in content.KEYWORDS.items():
        if keyword in text_normalized:
            return option_code
    return None


def _response_for_option_code(option_code: str) -> str:
    mapping = {
        "1.1": content.OPTION_1_1,
        "justificativa_ausencia": content.OPTION_JUSTIFICATIVA_AUSENCIA,
        "1.2": content.OPTION_1_2,
        "1.3": content.OPTION_1_3,
        "2": content.OPTION_2,
        "3": content.OPTION_3,
    }
    return mapping.get(option_code)


def start_conversation(user_id: str) -> str:
    """Chamado quando um usuário novo inicia a conversa."""
    _set_state(user_id, STATE_MAIN)
    return content.WELCOME + "\n\n" + content.MAIN_MENU


def process_message(user_id: str, message: str, usar_pln: bool = True) -> dict:
    """
    Função principal: recebe o texto do usuário e devolve um dicionário
    {"reply": ..., "intent": ..., "confidence": ..., "modo": ..., "pedir_feedback": ...}.

    usar_pln: quando False, o bot ignora o classificador de PLN e usa
    só a busca por palavra-chave (comportamento da fase anterior).

    "pedir_feedback" vem True quando a resposta foi uma informação de
    verdade (não só abrir um menu) - é nesse caso que faz sentido
    perguntar depois se a dúvida foi resolvida.
    """
    raw = message.strip()
    normalized = _normalize(raw)
    state = _get_state(user_id)
    modo = "PLN" if usar_pln else "Palavra-chave"

    # Botão "Falar com atendente" do chat: funciona em qualquer estado.
    if raw == COMANDO_ATENDENTE:
        _set_state(user_id, STATE_MAIN)
        return {
            "reply": content.OPTION_4 + "\n\n" + content.VOLTAR_MENU,
            "intent": None, "confidence": None, "modo": modo, "pedir_feedback": False,
        }

    # Comando universal: digitar "menu" a qualquer momento volta ao início.
    if normalized in ("menu", "inicio", "voltar ao menu"):
        _set_state(user_id, STATE_MAIN)
        return {"reply": content.MAIN_MENU, "intent": None, "confidence": None, "modo": modo, "pedir_feedback": False}

    if state == STATE_SUBMENU_1:
        reply, intent, confidence, pedir_feedback = _handle_submenu_1(user_id, raw, normalized, usar_pln)
    else:
        reply, intent, confidence, pedir_feedback = _handle_main_menu(user_id, raw, normalized, usar_pln)

    return {"reply": reply, "intent": intent, "confidence": confidence, "modo": modo, "pedir_feedback": pedir_feedback}


def _resposta_por_intencao(intencao: str):
    """Dado o código de uma intenção, devolve a resposta pronta correspondente."""
    if intencao == "4":
        return content.FALLBACK_WANTS_ATTENDANT
    if intencao == "saudacao_bom_dia":
        return content.SAUDACAO_BOM_DIA_RESPOSTA
    if intencao == "saudacao_boa_tarde":
        return content.SAUDACAO_BOA_TARDE_RESPOSTA
    if intencao == "saudacao_boa_noite":
        return content.SAUDACAO_BOA_NOITE_RESPOSTA
    if intencao == "saudacao_oi":
        return content.SAUDACAO_OI_RESPOSTA
    if intencao == "agradecimento":
        return content.AGRADECIMENTO_RESPOSTA
    if intencao == "despedida":
        return content.DESPEDIDA_RESPOSTA

    resposta_menu = _response_for_option_code(intencao)
    if resposta_menu:
        return content.SUGGESTION_TEMPLATE.format(resposta=resposta_menu)

    return None


def _interpretar_texto_livre(normalized: str, raw: str, usar_pln: bool):
    """
    Tenta entender uma mensagem que não é um número do menu.
    Retorna (resposta, intent, confidence). resposta é None se nada
    foi entendido.
    """
    # 1) Camada de PLN (só roda se usar_pln estiver ligado).
    if usar_pln:
        intencao, confianca = nlu_classifier.prever_intencao(raw)
        if intencao:
            resposta = _resposta_por_intencao(intencao)
            if resposta:
                return resposta, intencao, confianca
    else:
        confianca = None

    # 2) Busca por palavra-chave: única camada quando usar_pln=False,
    #    ou rede de segurança quando o PLN não teve confiança suficiente.
    option_code = _find_keyword_match(normalized)
    if option_code == "4":
        return content.FALLBACK_WANTS_ATTENDANT, "4", None
    resposta = _response_for_option_code(option_code) if option_code else None
    if resposta:
        return content.SUGGESTION_TEMPLATE.format(resposta=resposta), option_code, None

    # 3) Nada entendido.
    return None, None, confianca


def _handle_main_menu(user_id: str, raw: str, normalized: str, usar_pln: bool):
    if raw == "0":
        return content.MAIN_MENU, None, None, False

    if raw == "1":
        _set_state(user_id, STATE_SUBMENU_1)
        return content.SUBMENU_1, None, None, False

    if raw == "2":
        return content.OPTION_2 + "\n\n" + content.VOLTAR_MENU, None, None, True

    if raw == "3":
        return content.OPTION_3 + "\n\n" + content.VOLTAR_MENU, None, None, True

    if raw == "4":
        return content.OPTION_4 + "\n\n" + content.VOLTAR_MENU, None, None, False

    resposta, intent, confidence = _interpretar_texto_livre(normalized, raw, usar_pln)
    if resposta:
        return resposta, intent, confidence, intent in INTENCOES_INFORMATIVAS

    return content.FALLBACK_ASK_MENU, INTENCAO_NAO_ENTENDIDA, confidence, False


def _handle_submenu_1(user_id: str, raw: str, normalized: str, usar_pln: bool):
    if raw == "0":
        _set_state(user_id, STATE_MAIN)
        return content.MAIN_MENU, None, None, False

    if raw == "1":
        return content.OPTION_1_1 + "\n\n" + content.VOLTAR_MENU, None, None, True

    if raw == "2":
        return content.OPTION_1_2 + "\n\n" + content.VOLTAR_MENU, None, None, True

    if raw == "3":
        return content.OPTION_1_3 + "\n\n" + content.VOLTAR_MENU, None, None, True

    resposta, intent, confidence = _interpretar_texto_livre(normalized, raw, usar_pln)
    if resposta:
        return resposta, intent, confidence, intent in INTENCOES_INFORMATIVAS

    return content.INVALID_OPTION + "\n\n" + content.SUBMENU_1, INTENCAO_NAO_ENTENDIDA, confidence, False
