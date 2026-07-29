#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Gera os dados de itens empacotados a partir dos CSVs oficiais do INEP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DESTINO_PADRAO = ROOT / "src" / "tri_enem" / "data" / "itens"
ANOS = tuple(range(2009, 2026))
COLUNAS_OBRIGATORIAS = {
    "CO_POSICAO",
    "SG_AREA",
    "TX_GABARITO",
    "NU_PARAM_A",
    "NU_PARAM_B",
    "NU_PARAM_C",
    "CO_PROVA",
}


def sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def localizar_item_oficial(base: Path, ano: int) -> Path:
    candidatos = (
        base / f"microdados_enem_{ano}" / "DADOS" / f"ITENS_PROVA_{ano}.csv",
        base / f"microdados_enem_{ano}" / "DADOS" / f"itens_prova_{ano}.csv",
        base / str(ano) / f"ITENS_PROVA_{ano}.csv",
        base / f"ITENS_PROVA_{ano}.csv",
    )
    for caminho in candidatos:
        if caminho.is_file():
            return caminho
    raise FileNotFoundError(
        f"ITENS_PROVA de {ano} não encontrado sob {base}; caminhos testados: "
        + ", ".join(str(path) for path in candidatos)
    )


def validar_frame(df: pd.DataFrame, ano: int, origem: Path) -> dict[str, Any]:
    faltantes = sorted(COLUNAS_OBRIGATORIAS - set(df.columns))
    if faltantes:
        raise ValueError(f"{origem}: colunas obrigatórias ausentes: {faltantes}")
    areas = sorted(str(area) for area in df["SG_AREA"].dropna().unique())
    if set(areas) != {"CH", "CN", "LC", "MT"}:
        raise ValueError(f"{origem}: áreas inesperadas: {areas}")
    provas = pd.to_numeric(df["CO_PROVA"], errors="coerce")
    if provas.isna().any():
        raise ValueError(f"{origem}: CO_PROVA ausente ou inválido")
    if len(df) == 0:
        raise ValueError(f"{origem}: arquivo sem itens")
    return {
        "ano": ano,
        "linhas": int(len(df)),
        "provas": int(provas.nunique()),
        "areas": areas,
    }


def gerar_dados_itens(
    microdados_dir: Path,
    destino: Path = DESTINO_PADRAO,
) -> dict[str, Any]:
    """Normaliza os 17 CSVs e os substitui somente após validar o conjunto."""
    microdados_dir = microdados_dir.resolve()
    destino = destino.resolve()
    entradas = []
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent) as temp_nome:
        temp = Path(temp_nome)
        for ano in ANOS:
            origem = localizar_item_oficial(microdados_dir, ano)
            df = pd.read_csv(origem, encoding="latin1", sep=";", low_memory=False)
            metadados = validar_frame(df, ano, origem)
            saida = temp / str(ano) / f"ITENS_PROVA_{ano}.csv"
            saida.parent.mkdir(parents=True, exist_ok=True)
            # A normalização é intencional: UTF-8, ';', LF, mesma ordem oficial.
            df.to_csv(saida, index=False, encoding="utf-8", sep=";", lineterminator="\n")
            entradas.append({
                **metadados,
                "arquivo": f"{ano}/ITENS_PROVA_{ano}.csv",
                "fonte": str(origem.relative_to(microdados_dir)),
                "sha256_fonte": sha256(origem),
                "sha256_normalizado": sha256(saida),
                "bytes_normalizado": saida.stat().st_size,
            })

        manifesto = {
            "schema_version": 1,
            "generator": "tools/gerar_dados_itens.py",
            "normalization": "pandas-read-latin1-write-utf8-semicolon-lf",
            "years": [entrada["ano"] for entrada in entradas],
            "files": entradas,
        }
        (temp / "manifest.json").write_text(
            json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        destino.mkdir(parents=True, exist_ok=True)
        for entrada in entradas:
            relativo = Path(entrada["arquivo"])
            alvo = destino / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temp / relativo, alvo)
        os.replace(temp / "manifest.json", destino / "manifest.json")
    return manifesto


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microdados-dir", required=True, type=Path)
    parser.add_argument("--destino", type=Path, default=DESTINO_PADRAO)
    args = parser.parse_args()
    manifesto = gerar_dados_itens(args.microdados_dir, args.destino)
    total = sum(item["bytes_normalizado"] for item in manifesto["files"])
    print(
        f"{len(manifesto['files'])} arquivos de itens gerados e validados "
        f"({total / 1024 / 1024:.2f} MiB)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
