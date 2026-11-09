#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Recalcula offline a confirmação independente e verifica seus hashes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.avaliar_catalogo import (  # noqa: E402
    assinatura, avaliar, carregar_inconsistentes, ler_fixture, sha256,
    verificar_inconsistentes,
)

CAMPOS = ("n", "mae", "erro_p95", "erro_maximo", "acima_2")


def validar():
    fixture = ROOT / "tests/fixtures/reconstruction_confirmation.jsonl.gz"
    manifesto = json.loads((ROOT / "tests/fixtures/reconstruction_confirmation_manifest.json").read_text())
    catalogo_path = ROOT / "src/tri_enem/coeficientes_data.json"
    catalogo = json.loads(catalogo_path.read_text())
    falhas = []
    if sha256(catalogo_path) != manifesto["catalogo_sha256"]:
        falhas.append("hash do catálogo diverge da confirmação")
    if sha256(fixture) != manifesto["fixture_sha256"]:
        falhas.append("hash da fixture diverge da confirmação")
    if sha256(ROOT / "tests/fixtures/validation_manifest.json") != manifesto["source_manifest_sha256"]:
        falhas.append("manifesto das fontes diverge da confirmação")
    if manifesto["overlapping_cases"] != 0:
        falhas.append("confirmação sobrepõe a investigação")
    casos = ler_fixture(fixture)
    ids = [r["case_id"] for r in casos]
    if len(ids) != len(set(ids)) or any(r["split"] != "confirmacao" for r in casos):
        falhas.append("caso repetido ou split incorreto")
    fingerprint = assinatura(ids)
    if fingerprint != manifesto["case_ids_sha256"] or fingerprint != manifesto["after"]["case_ids_sha256"]:
        falhas.append("hash dos casos avaliados diverge da confirmação")
    holdout_ids = {r["case_id"] for r in ler_fixture(ROOT / "tests/fixtures/validation_holdout.jsonl.gz")}
    if set(ids) & holdout_ids:
        falhas.append("confirmação sobrepõe o holdout de investigação")
    inconsistentes = carregar_inconsistentes()
    falhas.extend(verificar_inconsistentes(catalogo, casos, inconsistentes))
    resultado = avaliar(catalogo, casos, inconsistentes)
    if resultado["excluidos"] != manifesto["after"].get("excluded_inconsistent"):
        falhas.append("registros excluídos divergem do manifesto")
    for key, metricas in resultado["por_prova"].items():
        esperado = manifesto["after"]["por_prova"].get(key, {})
        publicada = catalogo["por_prova"][key].get("validacao_confirmacao") or {}
        for nome in CAMPOS:
            if not np.isclose(metricas[nome], esperado.get(nome, np.nan), rtol=0, atol=1e-6):
                falhas.append(f"{key}: {nome} diverge: {metricas[nome]} != {esperado.get(nome)}")
            if not np.isclose(metricas[nome], publicada.get(nome, np.nan), rtol=0, atol=1e-6):
                falhas.append(f"{key}: evidência de confirmação no catálogo diverge: {nome}")
    for nome in CAMPOS:
        if not np.isclose(resultado["total"][nome], manifesto["after"]["total"][nome], rtol=0, atol=1e-6):
            falhas.append(f"total: {nome} diverge")
    return falhas


if __name__ == "__main__":
    erros = validar()
    if erros:
        print("\n".join(erros))
        raise SystemExit(1)
    print("Confirmação independente: hashes, separação do holdout publicado e métricas conferidos.")
