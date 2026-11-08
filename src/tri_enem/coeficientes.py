# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Escala de notas do ENEM e notas de gabarito catalogadas.

A escala é afim e fixa por área, igual em todas as edições; as constantes
ficam em ``metadata.escala``. ``nota_gabarito`` registra, por prova, a nota
oficial de quem acerta todos os itens quando ela difere da nota do modelo.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping

_DATA_FILE = Path(__file__).parent / "coeficientes_data.json"

# Usada só se o catálogo estiver ausente ou corrompido.
_ESCALA_EMERGENCIA = {
    "CN": (113.102301, 501.143423),
    "CH": (112.310030, 501.489020),
    "LC": (108.085986, 499.977975),
    "MT": (129.646241, 500.019367),
}


def _carregar_catalogo() -> Dict[str, Any]:
    try:
        data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


_DATA = _carregar_catalogo()


def escala_catalogo(catalogo: Mapping[str, Any]) -> Dict[str, tuple[float, float]]:
    """(slope, intercept) por área; áreas inválidas usam a escala de emergência."""
    escala = dict(_ESCALA_EMERGENCIA)
    for area, valor in ((catalogo.get("metadata") or {}).get("escala") or {}).items():
        try:
            escala[area.upper()] = (float(valor["slope"]), float(valor["intercept"]))
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
    return escala


def notas_gabarito_catalogo(catalogo: Mapping[str, Any]) -> Dict[tuple, float]:
    """{(ano, área, prova, idioma): nota}; idioma é None fora de LC."""
    resultado: Dict[tuple, float] = {}
    for chave, info in (catalogo.get("por_prova") or {}).items():
        regra = info.get("nota_gabarito") if isinstance(info, dict) else None
        if not isinstance(regra, dict):
            continue
        ano, area, prova = chave.split(",")
        por_idioma = regra.get("por_idioma", {None: regra})
        for idioma, valor in por_idioma.items():
            lingua = None if idioma in (None, "None") else int(idioma)
            resultado[(int(ano), area, int(prova), lingua)] = float(valor["nota"])
    return resultado


def reconstrucoes_catalogo(catalogo: Mapping[str, Any]) -> Dict[str, Any]:
    """Associações empíricas publicadas junto do modelo e de sua validação."""
    return {
        chave: deepcopy(info["reconstrucao_itens"])
        for chave, info in (catalogo.get("por_prova") or {}).items()
        if isinstance(info.get("reconstrucao_itens"), dict)
    }


_ESCALA = escala_catalogo(_DATA)


def obter_transformacao(
    ano: int | None = None, area: str = "MT", co_prova: int | None = None
) -> Dict[str, Any]:
    """Transformação θ → nota da área. ``ano`` e ``co_prova`` não a alteram."""
    del ano, co_prova
    slope, intercept = _ESCALA[area.upper()]
    return {"tipo": "linear", "slope": slope, "intercept": intercept}


def aplicar_transformacao(theta: float, transformacao: Mapping[str, Any]) -> float:
    return float(transformacao["slope"]) * float(theta) + float(transformacao["intercept"])


def obter_catalogo() -> Dict[str, Any]:
    """Retorna uma cópia defensiva do catálogo carregado."""
    return deepcopy(_DATA)


def obter_reconstrucoes_itens() -> Dict[str, Any]:
    return reconstrucoes_catalogo(_DATA)
