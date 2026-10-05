#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Recalcula offline a confirmação independente e verifica seus hashes."""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tri_enem import CalculadorTRI
from tri_enem.calibracao_modelos import aplicar_modelo


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    calc = CalculadorTRI(reconstrucoes={k: v["reconstrucao_itens"]
        for k, v in catalogo["por_prova"].items() if "reconstrucao_itens" in v})
    grupos, ids = defaultdict(list), set()
    for linha in gzip.open(fixture, "rt", encoding="utf-8"):
        r = json.loads(linha)
        if r["case_id"] in ids or r["split"] != "confirmacao":
            falhas.append("caso repetido ou split incorreto")
        ids.add(r["case_id"])
        grupos[(r["ano"], r["area"], r["co_prova"], r["tp_lingua"])].append(r)
    fingerprint = hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
    if fingerprint != manifesto["case_ids_sha256"] or fingerprint != manifesto["after"]["case_ids_sha256"]:
        falhas.append("hash dos casos avaliados diverge da confirmação")
    holdout_ids = {json.loads(l)["case_id"] for l in gzip.open(ROOT / "tests/fixtures/validation_holdout.jsonl.gz", "rt")}
    if ids & holdout_ids:
        falhas.append("confirmação sobrepõe o holdout de investigação")
    erros_por_prova = defaultdict(list)
    for (ano, area, code, lingua), casos in grupos.items():
        itens, u = calc.preparar_respostas_batch(ano, area, code, [r["respostas"] for r in casos], lingua)
        theta = calc.estimar_theta_eap_batch(u, itens)
        key = f"{ano},{area},{code}"
        modelo = catalogo["por_prova"][key]["transformacao"]
        erros = abs(aplicar_modelo(theta, modelo) - np.array([r["nota_oficial"] for r in casos]))
        erros_por_prova[key].extend(erros.tolist())
    todos = []
    for key, erros in erros_por_prova.items():
        erros = np.asarray(erros)
        todos.extend(erros.tolist())
        esperado = manifesto["after"]["por_prova"][key]
        publicada = catalogo["por_prova"][key].get("validacao_confirmacao") or {}
        metrics = {"n": len(erros), "mae": float(erros.mean()), "erro_p95": float(np.percentile(erros, 95)),
                   "erro_maximo": float(erros.max()), "acima_2": int((erros > 2+1e-12).sum())}
        for nome, valor in metrics.items():
            if not np.isclose(valor, esperado[nome], rtol=0, atol=1e-6):
                falhas.append(f"{key}: {nome} diverge: {valor} != {esperado[nome]}")
            if not np.isclose(valor, publicada.get(nome, np.nan), rtol=0, atol=1e-6):
                falhas.append(f"{key}: evidência de confirmação no catálogo diverge: {nome}")
    erros = np.asarray(todos)
    for nome, valor in {"n": len(erros), "mae": erros.mean(), "erro_maximo": erros.max(),
                        "erro_p95": np.percentile(erros, 95), "acima_2": (erros > 2+1e-12).sum()}.items():
        if not np.isclose(valor, manifesto["after"]["total"][nome], rtol=0, atol=1e-6):
            falhas.append(f"total: {nome} diverge")
    return falhas


if __name__ == "__main__":
    erros = validar()
    if erros:
        print("\n".join(erros))
        raise SystemExit(1)
    print("Confirmação independente: hashes, separação do holdout publicado e métricas conferidos.")
