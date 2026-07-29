# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Testes dos utilitários que materializam dados derivados."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "limpar_microdados", ROOT / "tools" / "limpar_microdados.py"
)
assert SPEC and SPEC.loader
limpar_microdados = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(limpar_microdados)


def test_extrato_participantes_reconhece_layout_oficial_e_publica_utf8(tmp_path):
    origem = (
        tmp_path
        / "oficiais"
        / "microdados_enem_2024"
        / "DADOS"
        / "RESULTADOS_2024.csv"
    )
    origem.parent.mkdir(parents=True)
    dados = {"NU_SEQUENCIAL": [1, 2], "TP_LINGUA": [0, 1]}
    for area in ("CN", "CH", "LC", "MT"):
        dados[f"TP_PRESENCA_{area}"] = [1, 1]
        dados[f"CO_PROVA_{area}"] = [100, 100]
        dados[f"NU_NOTA_{area}"] = [500.0, 600.0]
        dados[f"TX_RESPOSTAS_{area}"] = ["A" * 45, "B" * 45]
    pd.DataFrame(dados).to_csv(
        origem, sep=";", index=False, encoding="latin1"
    )

    destino = tmp_path / "reduzidos"
    original, reduzido = limpar_microdados.limpar_arquivo_chunked(
        2024, tmp_path / "oficiais", destino, chunk_size=1
    )

    saida = destino / "2024" / "DADOS_ENEM_2024.csv"
    frame = pd.read_csv(saida, sep=";", encoding="utf-8")
    assert original > 0
    assert reduzido > 0
    assert len(frame) == 2
    assert set(dados).issubset(frame.columns)
