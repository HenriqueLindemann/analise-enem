#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Levanta nos microdados a nota oficial de quem acerta todos os itens.

Para cada prova/idioma, compara a nota oficial dos participantes que acertaram
todos os itens com gabarito A-E (inclusive abandonados) com a nota do modelo.
Registra ``nota_gabarito`` quando a nota oficial, unânime, difere da do
modelo. Cadernos sem participantes nessa condição herdam o valor de um caderno
da mesma aplicação com os mesmos itens válidos.

    python tools/levantar_notas_gabarito.py --microdados-dir DIR --saida notas.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tri_enem import CalculadorTRI, MapeadorProvas  # noqa: E402
from tools.recalibrar_validacao import _linhas_validas, localizar_microdados  # noqa: E402

AREAS = ("CN", "CH", "LC", "MT")
TOLERANCIA = 0.05  # notas oficiais têm uma casa decimal


def _linguas(ano: int, area: str):
    return (0, 1) if area == "LC" and ano != 2009 else (None,)


def _chave_itens(itens) -> tuple:
    return tuple(
        (item.co_item, item.param_a, item.param_b, item.param_c)
        for item in itens if not item.abandonado
    )


def _contar_gabaritos(caminho: Path, ano: int, calc: CalculadorTRI, provas) -> dict:
    """{(área, prova, idioma): Counter(nota oficial)} de quem gabaritou."""
    cabecalho = pd.read_csv(caminho, sep=";", nrows=0, encoding="latin1").columns
    colunas = [c for c in cabecalho if c == "TP_LINGUA" or any(
        c == f"{p}_{a}" for a in AREAS
        for p in ("TP_PRESENCA", "CO_PROVA", "NU_NOTA", "TX_RESPOSTAS"))]
    gabaritos = {}
    for area, prova in provas:
        for lingua in _linguas(ano, area):
            try:
                itens = calc.carregar_itens(ano, area, prova, lingua)
            except (ValueError, FileNotFoundError):
                continue
            posicoes = [i for i, item in enumerate(itens) if item.gabarito.upper() in set("ABCDE")]
            gabaritos[(area, prova, lingua)] = (
                np.asarray(posicoes), np.frombuffer(
                    "".join(itens[i].gabarito.upper() for i in posicoes).encode(), dtype=np.uint8))
    contagens: dict = defaultdict(Counter)
    for bloco in pd.read_csv(caminho, sep=";", usecols=colunas, encoding="latin1",
                             dtype=str, chunksize=500_000):
        for area in AREAS:
            linhas = _linhas_validas(bloco, ano, area, None)
            for (prova, lingua), grupo in linhas.groupby(["prova", linhas["lingua"].fillna(-1)]):
                lingua = None if lingua == -1 or area != "LC" or ano == 2009 else int(lingua)
                chave = (area, int(prova), lingua)
                if chave not in gabaritos:
                    continue
                respostas = [
                    calc.normalizar_respostas(r, area, ano, lingua).upper()
                    for r in grupo["respostas"]
                ]
                matriz = np.frombuffer("".join(respostas).encode(), dtype=np.uint8).reshape(len(respostas), -1)
                posicoes, esperado = gabaritos[chave]
                acertou = (matriz[:, posicoes] == esperado).all(axis=1)
                contagens[chave].update(grupo["nota"].to_numpy(dtype=float)[acertou].round(1).tolist())
    return contagens


def levantar(microdados_dir: Path, anos) -> dict:
    calc = CalculadorTRI(catalogo=_catalogo_sem_gabarito())
    mapeador = MapeadorProvas()
    resultado = {}
    for ano in anos:
        provas = mapeador.listar_todas_provas(ano)
        contagens = _contar_gabaritos(
            localizar_microdados(microdados_dir, ano), ano, calc,
            [(p.area, p.codigo) for p in provas],
        )
        grupos = defaultdict(list)
        for prova in provas:
            for lingua in _linguas(ano, prova.area):
                try:
                    itens = calc.carregar_itens(ano, prova.area, prova.codigo, lingua)
                except (ValueError, FileNotFoundError):
                    continue
                natural = calc.transformar_escala(
                    calc.estimar_theta_eap([1] * len(itens), itens), ano, prova.area)
                observadas = contagens.get((prova.area, prova.codigo, lingua), Counter())
                grupos[(prova.area, prova.tipo_aplicacao, lingua, _chave_itens(itens))].append(
                    (prova.codigo, natural, observadas))
        for (area, _, lingua, _), membros in grupos.items():
            observados = {}
            for codigo, natural, contagem in membros:
                if not contagem:
                    continue
                nota, n = contagem.most_common(1)[0]
                if n != sum(contagem.values()):
                    # Notas divergentes para o mesmo padrão (ex.: anulações
                    # seletivas de 2011) não definem uma regra.
                    continue
                observados[codigo] = (nota, n, natural)
            valores = {nota for nota, _, _ in observados.values()}
            if len(valores) != 1:
                continue
            nota = valores.pop()
            if all(abs(nota - natural) <= TOLERANCIA for _, _, natural in observados.values()):
                continue
            referencia = min(observados)
            for codigo, natural, _ in membros:
                if abs(nota - natural) <= TOLERANCIA:
                    continue
                registro = {
                    "nota": nota,
                    "nota_modelo": round(natural, 4),
                    "n_observados": observados[codigo][1] if codigo in observados else 0,
                    "origem": "microdados" if codigo in observados else "caderno_equivalente",
                }
                if codigo not in observados:
                    registro["caderno_referencia"] = referencia
                chave = f"{ano},{area},{codigo}"
                if lingua is None:
                    resultado[chave] = registro
                else:
                    resultado.setdefault(chave, {"por_idioma": {}})["por_idioma"][str(lingua)] = registro
        print(f"{ano}: {sum(k.startswith(str(ano)) for k in resultado)} provas com nota de gabarito", flush=True)
    return resultado


def _catalogo_sem_gabarito() -> dict:
    from tri_enem.coeficientes import obter_catalogo

    catalogo = obter_catalogo()
    for info in catalogo.get("por_prova", {}).values():
        info.pop("nota_gabarito", None)
    return catalogo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--microdados-dir", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--anos", type=int, nargs="*", default=list(range(2009, 2026)))
    args = parser.parse_args()
    resultado = levantar(args.microdados_dir, args.anos)
    args.saida.write_text(json.dumps(resultado, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
