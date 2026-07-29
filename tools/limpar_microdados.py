#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera extratos locais de participantes e os dados empacotados de itens.

Os extratos são opcionais e servem apenas a investigações legadas. O catálogo
v3 e o holdout são sempre gerados diretamente dos microdados brutos por
``recalibrar_validacao.py``.

Exemplo:
    python tools/limpar_microdados.py \
      --microdados-dir /caminho/MICRODADOS_ENEM
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import pandas as pd

try:
    from gerar_dados_itens import gerar_dados_itens
except ImportError:  # Importado como módulo a partir da raiz do projeto.
    from tools.gerar_dados_itens import gerar_dados_itens

ANOS = tuple(range(2009, 2026))
CHUNK_SIZE = 100_000
COLUNAS_ESSENCIAIS = [
    "NU_INSCRICAO",
    "NU_SEQUENCIAL",
    "CO_INSCRICAO",
    "IN_INSCRICAO",
    *[f"TP_PRESENCA_{area}" for area in ("CN", "CH", "LC", "MT")],
    *[f"CO_PROVA_{area}" for area in ("CN", "CH", "LC", "MT")],
    *[f"NU_NOTA_{area}" for area in ("CN", "CH", "LC", "MT")],
    *[f"TX_RESPOSTAS_{area}" for area in ("CN", "CH", "LC", "MT")],
    "TP_LINGUA",
    "TP_STATUS_REDACAO",
    *[f"NU_NOTA_COMP{i}" for i in range(1, 6)],
    "NU_NOTA_REDACAO",
]


def localizar_participantes(base: Path, ano: int) -> Path:
    candidatos = (
        base / f"microdados_enem_{ano}" / "DADOS" / f"RESULTADOS_{ano}.csv",
        base / f"microdados_enem_{ano}" / "DADOS" / f"MICRODADOS_ENEM_{ano}.csv",
        base / str(ano) / f"RESULTADOS_{ano}.csv",
        base / str(ano) / f"MICRODADOS_ENEM_{ano}.csv",
    )
    for caminho in candidatos:
        if caminho.is_file():
            return caminho
    raise FileNotFoundError(
        f"Microdados de participantes de {ano} não encontrados sob {base}"
    )


def limpar_arquivo_chunked(
    ano: int,
    microdados_dir: Path,
    destino_base: Path,
    chunk_size: int = CHUNK_SIZE,
) -> tuple[float, float]:
    """Publica atomicamente o extrato de participantes de um ano."""
    origem = localizar_participantes(microdados_dir, ano)
    destino = destino_base / str(ano) / f"DADOS_ENEM_{ano}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    header = pd.read_csv(origem, encoding="latin1", sep=";", nrows=0)
    colunas = [coluna for coluna in COLUNAS_ESSENCIAIS if coluna in header.columns]
    obrigatorias = {
        f"{prefixo}_{area}"
        for prefixo in ("TP_PRESENCA", "CO_PROVA", "NU_NOTA", "TX_RESPOSTAS")
        for area in ("CN", "CH", "LC", "MT")
    }
    faltantes = sorted(obrigatorias - set(colunas))
    if faltantes:
        raise ValueError(f"{origem}: colunas essenciais ausentes: {faltantes}")

    tamanho_original = origem.stat().st_size / (1024 * 1024)
    total_linhas = 0
    with tempfile.TemporaryDirectory(dir=destino.parent) as temp_nome:
        temporario = Path(temp_nome) / destino.name
        primeiro = True
        for chunk in pd.read_csv(
            origem,
            encoding="latin1",
            sep=";",
            usecols=colunas,
            chunksize=chunk_size,
            low_memory=False,
        ):
            total_linhas += len(chunk)
            chunk.to_csv(
                temporario,
                index=False,
                encoding="utf-8",
                sep=";",
                mode="w" if primeiro else "a",
                header=primeiro,
                lineterminator="\n",
            )
            primeiro = False
            print(f"  {ano}: {total_linhas:,} linhas", end="\r", flush=True)
        if primeiro:
            raise ValueError(f"{origem}: arquivo sem participantes")
        os.replace(temporario, destino)

    tamanho_limpo = destino.stat().st_size / (1024 * 1024)
    print(
        f"  {ano}: {total_linhas:,} linhas, {len(colunas)} colunas, "
        f"{tamanho_limpo:.2f} MiB"
    )
    return tamanho_original, tamanho_limpo


def copiar_itens_prova(microdados_dir: Path) -> float:
    """Delega os 17 anos ao gerador único, validado e atômico de itens."""
    manifesto = gerar_dados_itens(microdados_dir)
    total = sum(item["bytes_normalizado"] for item in manifesto["files"])
    print(
        f"  {len(manifesto['files'])} arquivos de itens empacotados "
        f"({total / 1024 / 1024:.2f} MiB)"
    )
    return total / (1024 * 1024)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microdados-dir", required=True, type=Path)
    parser.add_argument(
        "--destino-participantes",
        type=Path,
        default=Path("microdados_limpos"),
    )
    parser.add_argument("--anos", nargs="+", type=int, default=list(ANOS))
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument(
        "--sem-itens",
        action="store_true",
        help="Não regenera os 17 CSVs de itens empacotados.",
    )
    args = parser.parse_args()
    if args.chunk_size <= 0:
        parser.error("--chunk-size deve ser positivo")
    anos = sorted(set(args.anos))
    invalidos = sorted(set(anos) - set(ANOS))
    if invalidos:
        parser.error(f"anos fora do intervalo 2009-2025: {invalidos}")

    total_original = 0.0
    total_limpo = 0.0
    for ano in anos:
        original, limpo = limpar_arquivo_chunked(
            ano,
            args.microdados_dir,
            args.destino_participantes,
            args.chunk_size,
        )
        total_original += original
        total_limpo += limpo
    if not args.sem_itens:
        copiar_itens_prova(args.microdados_dir)

    print(
        f"[ok] {len(anos)} extratos publicados: {total_limpo:.2f} MiB "
        f"de {total_original:.2f} MiB."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
