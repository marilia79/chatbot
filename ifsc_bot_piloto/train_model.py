# -*- coding: utf-8 -*-
"""
Confere os exemplos de treino do PLN (nlu/training_data.py).

Não é mais obrigatório rodar isto: o PLN não usa arquivo de modelo, ele
monta tudo na memória quando o servidor inicia. Basta editar
`nlu/training_data.py` e reiniciar o `python app.py`.

Este script serve só para conferir se está tudo certo depois de editar:
mostra quantas frases cada intenção tem e avisa se a mesma frase foi
colocada em duas intenções diferentes (isso confunde o bot).

Uso:
    python train_model.py
"""

from nlu import classifier, training_data

if __name__ == "__main__":
    total = classifier.treinar_modelo()
    print(f"{total} frases de exemplo carregadas.\n")

    print("Frases por intenção:")
    for intencao, exemplos in training_data.INTENT_EXAMPLES.items():
        print(f"  {intencao:22s} {len(exemplos)}")

    vistas = {}
    conflitos = []
    for intencao, exemplos in training_data.INTENT_EXAMPLES.items():
        for frase in exemplos:
            chave = classifier._normalizar(frase)
            if chave in vistas and vistas[chave] != intencao:
                conflitos.append((frase, vistas[chave], intencao))
            vistas[chave] = intencao

    if conflitos:
        print("\nATENÇÃO: mesma frase em intenções diferentes:")
        for frase, a, b in conflitos:
            print(f"  '{frase}' está em '{a}' e em '{b}'")
    else:
        print("\nNenhum conflito encontrado. Pode reiniciar o servidor (python app.py).")
