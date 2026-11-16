# -*- coding: utf-8 -*-
"""
Classificador de intenções (PLN) do chatbot da Secretaria Acadêmica.

Abordagem: TF-IDF + Similaridade de Cosseno, implementada em Python puro
(só biblioteca padrão) - sem scikit-learn, scipy ou joblib.

Por que sem bibliotecas externas? Elas trazem arquivos compilados que
alguns computadores (principalmente com políticas de segurança do
Windows) bloqueiam, e o bot deixa de abrir. Como o nosso conjunto de
frases de exemplo é pequeno, a versão em Python puro é instantânea e dá
exatamente o mesmo resultado.

Como funciona:
1. `nlu/training_data.py` tem frases de exemplo para cada intenção.
2. Ao iniciar, este módulo transforma cada frase em um vetor TF-IDF
   (palavras e pares de palavras, com peso maior para termos raros).
3. `prever_intencao(texto)` transforma a mensagem do usuário da mesma
   forma, compara com todas as frases de exemplo e devolve a intenção
   da mais parecida + o quão parecida ela é (de 0.0 a 1.0).

Não existe arquivo de modelo salvo em disco: o índice é montado na
memória em milissegundos, então editar `training_data.py` e reiniciar o
servidor já basta (não há "modelo antigo" para apagar).
"""

import math
import re
import unicodedata
from collections import Counter

from . import training_data

# Abaixo desse valor de similaridade, o bot prefere dizer "não entendi" a
# arriscar uma resposta errada. Pode ajustar conforme for testando.
CONFIDENCE_THRESHOLD = 0.30

# Palavras com 2 ou mais letras/números (mesmo critério usado antes).
_PADRAO_PALAVRA = re.compile(r"\b\w\w+\b")


def _normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem pontuação - deixa o texto 'cru' para o modelo."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _termos(texto_normalizado: str):
    """Palavras isoladas + pares de palavras vizinhas (ex: 'trancar matricula')."""
    palavras = _PADRAO_PALAVRA.findall(texto_normalizado)
    pares = [f"{a} {b}" for a, b in zip(palavras, palavras[1:])]
    return palavras + pares


def _normalizar_vetor(vetor: dict) -> dict:
    """Deixa o vetor com comprimento 1, para o produto escalar virar cosseno."""
    tamanho = math.sqrt(sum(v * v for v in vetor.values()))
    if tamanho == 0:
        return {}
    return {termo: v / tamanho for termo, v in vetor.items()}


def _peso_tf(contagem: int) -> float:
    """TF sublinear: repetir uma palavra muitas vezes não domina o resultado."""
    return 1.0 + math.log(contagem)


class _Indice:
    """Guarda as frases de exemplo já convertidas em vetores TF-IDF."""

    def __init__(self):
        frases, self.rotulos = [], []
        for intencao, exemplos in training_data.INTENT_EXAMPLES.items():
            for frase in exemplos:
                frases.append(_termos(_normalizar(frase)))
                self.rotulos.append(intencao)

        # IDF: termos que aparecem em poucas frases valem mais.
        total = len(frases)
        frequencia_doc = Counter()
        for termos in frases:
            frequencia_doc.update(set(termos))
        self.idf = {
            termo: math.log((1 + total) / (1 + df)) + 1
            for termo, df in frequencia_doc.items()
        }

        self.vetores = [self._vetorizar_termos(termos) for termos in frases]

    def _vetorizar_termos(self, termos) -> dict:
        contagem = Counter(t for t in termos if t in self.idf)
        vetor = {t: _peso_tf(c) * self.idf[t] for t, c in contagem.items()}
        return _normalizar_vetor(vetor)

    def vetorizar(self, texto_normalizado: str) -> dict:
        return self._vetorizar_termos(_termos(texto_normalizado))


_indice_em_memoria = None  # montado uma vez e reaproveitado


def _carregar_indice() -> _Indice:
    global _indice_em_memoria
    if _indice_em_memoria is None:
        _indice_em_memoria = _Indice()
    return _indice_em_memoria


def treinar_modelo() -> int:
    """
    Remonta o índice a partir de training_data.py (útil para testes ou
    depois de editar os exemplos sem reiniciar). Devolve quantas frases
    de exemplo foram carregadas.
    """
    global _indice_em_memoria
    _indice_em_memoria = _Indice()
    return len(_indice_em_memoria.rotulos)


def prever_intencao(texto: str):
    """
    Recebe o texto livre do usuário e devolve (intencao, confianca).
    confianca é a similaridade (0.0 a 1.0) com a frase de exemplo mais
    parecida. Se ficar abaixo de CONFIDENCE_THRESHOLD, devolve
    (None, confianca) para o chamador tratar como "não entendi".
    """
    indice = _carregar_indice()
    texto_normalizado = _normalizar(texto)

    if not texto_normalizado:
        return None, 0.0

    vetor_mensagem = indice.vetorizar(texto_normalizado)
    if not vetor_mensagem:
        return None, 0.0

    melhor_similaridade = 0.0
    melhor_rotulo = None
    for rotulo, vetor_exemplo in zip(indice.rotulos, indice.vetores):
        # Produto escalar de vetores de comprimento 1 = similaridade de cosseno.
        similaridade = sum(
            peso * vetor_exemplo.get(termo, 0.0) for termo, peso in vetor_mensagem.items()
        )
        if similaridade > melhor_similaridade:
            melhor_similaridade = similaridade
            melhor_rotulo = rotulo

    if melhor_rotulo is None or melhor_similaridade < CONFIDENCE_THRESHOLD:
        return None, melhor_similaridade

    return melhor_rotulo, melhor_similaridade
