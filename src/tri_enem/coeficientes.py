# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Transformações da escala latente para a escala de notas do ENEM.

O catálogo v3 aceita uma transformação afim ou uma transformação monotônica
linear por partes. ``obter_coeficiente`` continua disponível para clientes
antigos, mas o motor usa ``obter_transformacao`` e ``aplicar_transformacao``.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

_DATA_FILE = Path(__file__).parent / "coeficientes_data.json"

_PADRAO_EMERGENCIA = {
    "MT": (129.63, 500.0),
    "CN": (113.13, 501.16),
    "CH": (112.32, 501.47),
    "LC": (108.08, 500.0),
}


def _carregar_catalogo() -> Dict[str, Any]:
    try:
        data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


_DATA = _carregar_catalogo()


def _linear(slope: float, intercept: float, origem: str) -> Dict[str, Any]:
    return {
        "tipo": "linear",
        "slope": float(slope),
        "intercept": float(intercept),
        "origem": origem,
    }


def _normalizar_transformacao(info: Dict[str, Any], origem: str) -> Dict[str, Any]:
    """Converte entradas v2/v3 para o contrato único usado pelo motor."""
    slope = float(info.get("slope", 100.0))
    intercept = float(info.get("intercept", 500.0))
    transformacao = info.get("transformacao")
    if not isinstance(transformacao, dict):
        return _linear(slope, intercept, origem)

    tipo = transformacao.get("tipo", "linear")
    if tipo == "linear":
        return _linear(
            transformacao.get("slope", slope),
            transformacao.get("intercept", intercept),
            origem,
        )

    if tipo != "monotonica_linear":
        return _linear(slope, intercept, origem)

    try:
        theta = np.asarray(transformacao["theta_knots"], dtype=float)
        notas = np.asarray(transformacao["score_knots"], dtype=float)
    except (KeyError, TypeError, ValueError):
        return _linear(slope, intercept, origem)

    valida = (
        theta.ndim == notas.ndim == 1
        and theta.size == notas.size
        and theta.size >= 2
        and np.all(np.isfinite(theta))
        and np.all(np.isfinite(notas))
        and np.all(np.diff(theta) > 0)
        and np.all(np.diff(notas) >= 0)
    )
    if not valida:
        return _linear(slope, intercept, origem)

    return {
        "tipo": "monotonica_linear",
        "slope": slope,
        "intercept": intercept,
        "theta_knots": theta.tolist(),
        "score_knots": notas.tolist(),
        "origem": origem,
    }


def _coeficientes_area() -> Dict[Tuple[int, str], Tuple[float, float]]:
    resultado: Dict[Tuple[int, str], Tuple[float, float]] = {}
    for key, value in _DATA.get("por_area", {}).items():
        try:
            ano, area = key.split(",")
            resultado[(int(ano), area.upper())] = (
                float(value["slope"]),
                float(value["intercept"]),
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
    return resultado


def _coeficientes_padrao() -> Dict[str, Tuple[float, float]]:
    resultado = dict(_PADRAO_EMERGENCIA)
    for area, meta in _DATA.get("metadata", {}).items():
        if not isinstance(meta, dict):
            continue
        try:
            resultado[area.upper()] = (
                float(meta["slope_medio"]),
                float(meta["intercept_medio"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
    return resultado


COEF_POR_AREA = _coeficientes_area()
COEF_PADRAO = _coeficientes_padrao()
COEF_POR_PROVA: Dict[Tuple[int, str, int], Tuple[float, float]] = {}
for _key, _value in _DATA.get("por_prova", {}).items():
    try:
        _ano, _area, _prova = _key.split(",")
        if _value.get("slope") is not None and _value.get("intercept") is not None:
            COEF_POR_PROVA[(int(_ano), _area.upper(), int(_prova))] = (
                float(_value["slope"]),
                float(_value["intercept"]),
            )
    except (AttributeError, KeyError, TypeError, ValueError):
        continue


def obter_transformacao(
    ano: int, area: str, co_prova: int | None = None
) -> Dict[str, Any]:
    """Obtém a melhor transformação disponível, com origem explícita."""
    ano = int(ano)
    area = area.upper()

    if co_prova is not None:
        key = f"{ano},{area},{int(co_prova)}"
        info = _DATA.get("por_prova", {}).get(key)
        if isinstance(info, dict) and info.get("slope") is not None:
            return _normalizar_transformacao(info, "prova")

    coef_area = COEF_POR_AREA.get((ano, area))
    if coef_area is not None:
        return _linear(*coef_area, origem="area_ano")

    return _linear(*COEF_PADRAO.get(area, (100.0, 500.0)), origem="area_padrao")


def aplicar_transformacao(theta: float, transformacao: Dict[str, Any]) -> float:
    """Aplica transformação linear ou monotônica, incluindo extrapolação."""
    theta = float(theta)
    if transformacao.get("tipo") != "monotonica_linear":
        return (
            float(transformacao["slope"]) * theta
            + float(transformacao["intercept"])
        )

    xs = np.asarray(transformacao["theta_knots"], dtype=float)
    ys = np.asarray(transformacao["score_knots"], dtype=float)
    nota = float(np.interp(theta, xs, ys))

    if theta < xs[0]:
        slope = max(0.0, float((ys[1] - ys[0]) / (xs[1] - xs[0])))
        nota = float(ys[0] + slope * (theta - xs[0]))
    elif theta > xs[-1]:
        slope = max(0.0, float((ys[-1] - ys[-2]) / (xs[-1] - xs[-2])))
        nota = float(ys[-1] + slope * (theta - xs[-1]))
    return nota


def obter_coeficiente(
    ano: int, area: str, co_prova: int | None = None
) -> Tuple[float, float]:
    """Retorna o baseline afim para compatibilidade com a API v3."""
    transformacao = obter_transformacao(ano, area, co_prova)
    return float(transformacao["slope"]), float(transformacao["intercept"])


def obter_catalogo() -> Dict[str, Any]:
    """Retorna uma cópia defensiva do catálogo carregado."""
    return deepcopy(_DATA)
