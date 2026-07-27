#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do golden de regressão (tests/fixtures/golden_notas.json).

O golden fixa nota, theta e acertos de casos reais cobrindo todo ano x área.
Os casos saem de exemplos_microdados.json, e a nota oficial é copiada junto, de
modo que o diff de uma regeneração mostre se o motor se aproximou ou se afastou
da nota do INEP.

Regenerar é obrigatório após qualquer recalibração: o golden anterior fixa notas
produzidas com os coeficientes antigos.

Execute a partir da raiz do projeto:
    python tests/fixtures/gerar_golden_notas.py
    python tests/fixtures/gerar_golden_notas.py --reselecionar
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent
ROOT = FIXTURES.parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from tri_enem import CalculadorTRI  # noqa: E402

EXEMPLOS = FIXTURES / 'exemplos_microdados.json'
GOLDEN = FIXTURES / 'golden_notas.json'

# Dois casos por (ano, área) cobrem os extremos da escala; o volume de acurácia
# fica com tests/test_e2e_usuario.py.
CASOS_POR_PAR = 2


def carregar_exemplos() -> list:
    with open(EXEMPLOS, encoding='utf-8') as f:
        return json.load(f)


def selecionar_do_golden(exemplos: list) -> list:
    """Reaproveita a seleção atual, para o diff mostrar só a mudança de valor."""
    if not GOLDEN.exists():
        return []

    with open(GOLDEN, encoding='utf-8') as f:
        atual = json.load(f)

    indice = {(e['ano'], e['area'], int(e['co_prova']), e['respostas']): e
              for e in exemplos}
    selecionados = []
    for caso in atual:
        chave = (caso['ano'], caso['area'], caso['co_prova'], caso['respostas'])
        if chave in indice:
            selecionados.append(indice[chave])
        else:
            print(f"  caso sem exemplo correspondente, descartado: {chave[:3]}")

    return selecionados


def selecionar_por_extremos(exemplos: list) -> list:
    """
    Seleção do zero: por (ano, área), os exemplos de menor e maior nota oficial.

    Desempate por identificador, para não depender da ordem do arquivo.
    """
    por_par = defaultdict(list)
    for e in exemplos:
        por_par[(e['ano'], e['area'])].append(e)

    selecionados = []
    for par in sorted(por_par):
        ordenados = sorted(por_par[par],
                           key=lambda e: (float(e['nota_oficial']), str(e['id'])))
        escolhidos = [ordenados[0], ordenados[-1]][:CASOS_POR_PAR]
        selecionados.extend(escolhidos)

    return selecionados


def gerar_caso(calc: CalculadorTRI, exemplo: dict) -> dict:
    co_prova = int(exemplo['co_prova'])
    tp_lingua = exemplo['tp_lingua']
    if tp_lingua is not None:
        tp_lingua = int(tp_lingua)

    r = calc.calcular_nota(exemplo['ano'], exemplo['area'], co_prova,
                           exemplo['respostas'], tp_lingua)
    nota_oficial = float(exemplo['nota_oficial'])

    return {
        'ano': exemplo['ano'],
        'area': exemplo['area'],
        'co_prova': co_prova,
        'respostas': exemplo['respostas'],
        'tp_lingua': tp_lingua,
        'nota': r['nota'],
        'theta': r['theta'],
        'acertos': r['acertos'],
        'total_itens': r['total_itens'],
        'nota_oficial': nota_oficial,
        'erro': r['nota'] - nota_oficial,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reselecionar', action='store_true',
                        help='Escolhe os casos do zero em vez de reaproveitar '
                             'os do golden atual')
    args = parser.parse_args()

    exemplos = carregar_exemplos()

    selecionados = [] if args.reselecionar else selecionar_do_golden(exemplos)
    if not selecionados:
        selecionados = selecionar_por_extremos(exemplos)

    calc = CalculadorTRI()
    casos, falhas = [], []
    for exemplo in selecionados:
        try:
            casos.append(gerar_caso(calc, exemplo))
        except Exception as e:
            falhas.append((exemplo['ano'], exemplo['area'],
                           exemplo['co_prova'], str(e)))

    with open(GOLDEN, 'w', encoding='utf-8') as f:
        json.dump(casos, f, ensure_ascii=False, indent=2)
        f.write('\n')

    pares = len({(c['ano'], c['area']) for c in casos})
    erros = sorted(abs(c['erro']) for c in casos)
    print(f"{GOLDEN.relative_to(ROOT)}: {len(casos)} casos, {pares} pares ano x area")
    print(f"  erro contra a nota oficial: mediana {erros[len(erros) // 2]:.3f}, "
          f"maximo {erros[-1]:.3f}")
    for falha in falhas:
        print(f"  falhou: {falha}")

    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
