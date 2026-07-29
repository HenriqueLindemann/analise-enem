# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Ajuste e avaliação reproduzíveis das transformações de nota."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence

import numpy as np

LIMITES_FAIXAS = np.asarray(
    [-np.inf, 400, 500, 600, 700, 800, 900, 1000, np.inf],
    dtype=float,
)
ROTULOS_FAIXAS = (
    "ate_400",
    "400_500",
    "500_600",
    "600_700",
    "700_800",
    "800_900",
    "900_1000",
    "acima_1000",
)
NOS_CANDIDATOS = (5, 9, 17, 33)


def faixa_nota(nota: float) -> str:
    """Classifica nota positiva, incluindo explicitamente valores >1000."""
    indice = int(np.searchsorted(LIMITES_FAIXAS[1:], float(nota), side="left"))
    return ROTULOS_FAIXAS[min(max(indice, 0), len(ROTULOS_FAIXAS) - 1)]


def ajustar_linear(theta: Sequence[float], nota: Sequence[float]) -> Dict[str, Any]:
    x = np.asarray(theta, dtype=float)
    y = np.asarray(nota, dtype=float)
    if x.size < 2 or np.ptp(x) <= 1e-12:
        raise ValueError("Variação insuficiente de theta para ajustar a transformação")
    slope, intercept = np.polyfit(x, y, 1)
    if slope < 0:
        slope = 0.0
        intercept = float(np.mean(y))
    return {
        "tipo": "linear",
        "slope": float(slope),
        "intercept": float(intercept),
        "complexidade": 2,
    }


def _isotonica_ponderada(valores: np.ndarray, pesos: np.ndarray) -> np.ndarray:
    """Pool Adjacent Violators Algorithm para sequência não decrescente."""
    blocos = [
        {"inicio": i, "fim": i, "peso": float(p), "media": float(v)}
        for i, (v, p) in enumerate(zip(valores, pesos))
    ]
    indice = 0
    while indice < len(blocos) - 1:
        if blocos[indice]["media"] <= blocos[indice + 1]["media"]:
            indice += 1
            continue
        a, b = blocos[indice], blocos[indice + 1]
        peso = a["peso"] + b["peso"]
        combinado = {
            "inicio": a["inicio"],
            "fim": b["fim"],
            "peso": peso,
            "media": (a["media"] * a["peso"] + b["media"] * b["peso"]) / peso,
        }
        blocos[indice:indice + 2] = [combinado]
        indice = max(0, indice - 1)

    resultado = np.empty(len(valores), dtype=float)
    for bloco in blocos:
        resultado[bloco["inicio"]:bloco["fim"] + 1] = bloco["media"]
    return resultado


def ajustar_monotonica(
    theta: Sequence[float],
    nota: Sequence[float],
    n_nos: int,
    limites_theta: tuple[float, float] | None = None,
) -> Dict[str, Any]:
    """Ajusta transformação linear por partes em quantis de theta.

    ``limites_theta`` permite que o reajuste final mantenha os dois nós de
    extremidade definidos exclusivamente pelo conjunto de calibração.
    """
    x = np.asarray(theta, dtype=float)
    y = np.asarray(nota, dtype=float)
    if x.size < max(10, n_nos):
        raise ValueError(f"Amostra insuficiente para {n_nos} nós")

    ordem = np.argsort(x, kind="stable")
    xs, ys = x[ordem], y[ordem]
    if limites_theta is not None:
        limite_inferior, limite_superior = map(float, limites_theta)
        if (
            not np.isfinite(limite_inferior)
            or not np.isfinite(limite_superior)
            or limite_inferior >= limite_superior
        ):
            raise ValueError("Limites de theta inválidos")
        xs = np.clip(xs, limite_inferior, limite_superior)
    grupos = np.array_split(np.arange(xs.size), max(1, n_nos - 2))

    nos_x = [float(xs[0])]
    nos_y = [float(np.median(ys[np.isclose(xs, xs[0], atol=1e-12)]))]
    pesos = [int(np.isclose(xs, xs[0], atol=1e-12).sum())]
    for grupo in grupos:
        nos_x.append(float(np.median(xs[grupo])))
        nos_y.append(float(np.median(ys[grupo])))
        pesos.append(int(grupo.size))
    nos_x.append(float(xs[-1]))
    nos_y.append(float(np.median(ys[np.isclose(xs, xs[-1], atol=1e-12)])))
    pesos.append(int(np.isclose(xs, xs[-1], atol=1e-12).sum()))

    # Consolida thetas repetidos antes da regressão isotônica.
    consolidados: list[tuple[float, float, int]] = []
    for valor_x, valor_y, peso in sorted(zip(nos_x, nos_y, pesos)):
        if consolidados and abs(valor_x - consolidados[-1][0]) <= 1e-12:
            anterior_x, anterior_y, anterior_peso = consolidados[-1]
            peso_total = anterior_peso + peso
            media = (anterior_y * anterior_peso + valor_y * peso) / peso_total
            consolidados[-1] = (anterior_x, media, peso_total)
        else:
            consolidados.append((valor_x, valor_y, peso))

    if len(consolidados) < 2:
        raise ValueError("Nós de theta insuficientes após consolidação")
    knot_x = np.asarray([item[0] for item in consolidados])
    knot_y = np.asarray([item[1] for item in consolidados])
    weights = np.asarray([item[2] for item in consolidados], dtype=float)
    knot_y = _isotonica_ponderada(knot_y, weights)

    baseline = ajustar_linear(x, y)
    return {
        "tipo": "monotonica_linear",
        "slope": baseline["slope"],
        "intercept": baseline["intercept"],
        "theta_knots": knot_x.tolist(),
        "score_knots": knot_y.tolist(),
        "complexidade": len(knot_x),
        "n_nos_solicitados": int(n_nos),
    }


def aplicar_modelo(theta: Sequence[float], modelo: Dict[str, Any]) -> np.ndarray:
    x = np.asarray(theta, dtype=float)
    if modelo["tipo"] == "linear":
        return float(modelo["slope"]) * x + float(modelo["intercept"])

    knots_x = np.asarray(modelo["theta_knots"], dtype=float)
    knots_y = np.asarray(modelo["score_knots"], dtype=float)
    pred = np.interp(x, knots_x, knots_y)
    slope_left = max(
        0.0, float((knots_y[1] - knots_y[0]) / (knots_x[1] - knots_x[0]))
    )
    slope_right = max(
        0.0,
        float((knots_y[-1] - knots_y[-2]) / (knots_x[-1] - knots_x[-2])),
    )
    pred = np.where(
        x < knots_x[0], knots_y[0] + slope_left * (x - knots_x[0]), pred
    )
    pred = np.where(
        x > knots_x[-1], knots_y[-1] + slope_right * (x - knots_x[-1]), pred
    )
    return pred


def metricas_modelo(
    theta: Sequence[float],
    nota: Sequence[float],
    modelo: Dict[str, Any],
    faixas: Iterable[str] = (),
) -> Dict[str, Any]:
    x = np.asarray(theta, dtype=float)
    y = np.asarray(nota, dtype=float)
    pred = aplicar_modelo(x, modelo)
    erros = np.abs(pred - y)
    if erros.size == 0:
        raise ValueError("Não há casos para avaliar")
    ss_res = float(np.sum((pred - y) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {
        "n": int(erros.size),
        "mae": float(erros.mean()),
        "erro_p95": float(np.percentile(erros, 95)),
        "erro_maximo": float(erros.max()),
        "acima_2": int(np.sum(erros > 2.0 + 1e-12)),
        "r_squared": float(1 - ss_res / ss_tot) if ss_tot > 0 else None,
        "faixas_cobertas": sorted(set(faixas)),
    }


def selecionar_modelo(
    theta_treino: Sequence[float],
    nota_treino: Sequence[float],
    theta_selecao: Sequence[float],
    nota_selecao: Sequence[float],
) -> Dict[str, Any]:
    """Seleciona por violações de 2 pontos, máximo, MAE e complexidade."""
    candidatos = [ajustar_linear(theta_treino, nota_treino)]
    for n_nos in NOS_CANDIDATOS:
        try:
            candidatos.append(ajustar_monotonica(theta_treino, nota_treino, n_nos))
        except ValueError:
            continue

    avaliados = []
    for modelo in candidatos:
        metricas = metricas_modelo(theta_selecao, nota_selecao, modelo)
        chave = (
            metricas["acima_2"],
            metricas["erro_maximo"],
            metricas["mae"],
            modelo["complexidade"],
        )
        avaliados.append((chave, modelo, metricas))
    _, modelo, metricas = min(avaliados, key=lambda item: item[0])
    return {"modelo": modelo, "metricas_selecao": metricas}


def reajustar_modelo(
    modelo_selecionado: Dict[str, Any],
    theta: Sequence[float],
    nota: Sequence[float],
) -> Dict[str, Any]:
    if modelo_selecionado["tipo"] == "linear":
        return ajustar_linear(theta, nota)
    return ajustar_monotonica(
        theta,
        nota,
        int(modelo_selecionado["n_nos_solicitados"]),
        limites_theta=(
            float(modelo_selecionado["theta_knots"][0]),
            float(modelo_selecionado["theta_knots"][-1]),
        ),
    )


def classificar_validacao(
    metricas: Dict[str, Any] | None,
    faixas_existentes: Sequence[str],
) -> tuple[str, str]:
    if not metricas or metricas.get("n", 0) < 30:
        return "nao_calibrado", "holdout_insuficiente"
    cobertas = set(metricas.get("faixas_cobertas", []))
    existentes = set(faixas_existentes)
    if len(existentes) < 2 or not existentes.issubset(cobertas):
        return "nao_calibrado", "faixas_incompletas"

    erro = float(metricas["erro_maximo"])
    if erro <= 2.0 + 1e-12:
        return "ok", "erro_maximo_ate_2"
    if erro <= 5.0 + 1e-12:
        return "aviso_leve", "erro_maximo_ate_5"
    if erro <= 15.0 + 1e-12:
        return "aviso_forte", "erro_maximo_ate_15"
    return "erro_alto", "erro_maximo_acima_15"
