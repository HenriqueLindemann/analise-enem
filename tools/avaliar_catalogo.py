# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Avaliação de um catálogo contra notas oficiais, compartilhada por ferramentas e validadores.

As notas vêm sempre de ``CalculadorTRI(catalogo=...)``, com as mesmas regras
da API. Registros listados em ``registros_inconsistentes.json`` ficam fora das
métricas, e a evidência de cada um é reconferida com o motor.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
REGISTROS_INCONSISTENTES = FIXTURES / "registros_inconsistentes.json"
LIMITE_INCONSISTENCIA = 2.0  # erro mínimo no código declarado
TOLERANCIA_ARREDONDAMENTO = 0.05
FIXTURES_TESTE = ("validation_holdout", "reconstruction_confirmation",
                  "residual_confirmation", "mean_error_confirmation")


def sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def assinatura(ids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def ler_fixture(caminho: Path) -> List[Dict[str, Any]]:
    with gzip.open(caminho, "rt", encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo if linha.strip()]


def casos_teste(fixtures_dir: Path = FIXTURES) -> List[Dict[str, Any]]:
    """Holdout e confirmações sem repetição: os casos que não entraram no ajuste."""
    vistos, casos = set(), []
    for nome in FIXTURES_TESTE:
        for caso in ler_fixture(fixtures_dir / f"{nome}.jsonl.gz"):
            if caso["case_id"] not in vistos:
                vistos.add(caso["case_id"])
                casos.append(caso)
    return casos


def chave_registro(registro: Mapping[str, Any]) -> tuple:
    """Identifica um registro dos microdados: prova, nota oficial e respostas."""
    return (int(registro["ano"]), registro["area"], int(registro["co_prova"]),
            float(registro["nota_oficial"]), str(registro["respostas"]).upper())


def carregar_inconsistentes(caminho: Path = REGISTROS_INCONSISTENTES) -> Dict[str, Dict[str, Any]]:
    """Registros por ``case_id``; os achados só no censo recebem uma chave própria."""
    registros = json.loads(caminho.read_text(encoding="utf-8"))
    return {r["case_id"] or "censo:" + ",".join(map(str, chave_registro(r)[:4])): r
            for r in registros}


def reconstrucao_efetiva(reconstrucao):
    """Reconstrução sem a quadratura, que passou a ser única; None se não altera o cálculo."""
    if not isinstance(reconstrucao, dict):
        return None
    reconstrucao = {k: v for k, v in reconstrucao.items() if k != "quadratura"}
    if "por_idioma" in reconstrucao:
        idiomas = {k: reconstrucao_efetiva(v) for k, v in reconstrucao["por_idioma"].items()}
        if not any(idiomas.values()):
            return None
        reconstrucao["por_idioma"] = {k: v for k, v in idiomas.items() if v}
        return reconstrucao
    return reconstrucao if {"itens", "codigo_base"} & set(reconstrucao) else None


def calculador(catalogo: Mapping[str, Any]):
    from tri_enem import CalculadorTRI

    return CalculadorTRI(catalogo=dict(catalogo))


def notas_casos(calc, casos: Sequence[Mapping[str, Any]]) -> np.ndarray:
    """Nota do motor para cada caso, na ordem recebida."""
    notas = np.full(len(casos), np.nan)
    grupos: Dict[tuple, List[int]] = defaultdict(list)
    for i, caso in enumerate(casos):
        grupos[(caso["ano"], caso["area"], caso["co_prova"], caso["tp_lingua"])].append(i)
    for (ano, area, prova, lingua), indices in grupos.items():
        notas[indices] = calc.calcular_notas_batch(
            ano, area, prova, [casos[i]["respostas"] for i in indices], lingua
        )
    return notas


def metricas(erros: Sequence[float], faixas: Iterable[str] = ()) -> Dict[str, Any]:
    erros = np.abs(np.asarray(erros, dtype=float))
    if not erros.size or not np.isfinite(erros).all():
        raise ValueError("avaliação vazia ou não finita")
    return {
        "n": int(erros.size),
        "mae": float(erros.mean()),
        "erro_p95": float(np.percentile(erros, 95)),
        "erro_maximo": float(erros.max()),
        "acima_2": int((erros > 2.0 + 1e-12).sum()),
        "faixas_cobertas": sorted(set(faixas)),
    }


def metricas_ponderadas(erros: Sequence[float], pesos: Sequence[float]) -> Dict[str, Any]:
    """Pesos = contagem real do estrato / casos amostrados nele."""
    e, w = np.abs(np.asarray(erros, dtype=float)), np.asarray(pesos, dtype=float)
    ordem = np.argsort(e, kind="stable")
    quantil = min(int(np.searchsorted(np.cumsum(w[ordem]), 0.95 * w.sum())), len(w) - 1)
    return {
        "n": int(e.size),
        "mae": float(np.average(e, weights=w)),
        "erro_p95": float(e[ordem[quantil]]),
        "erro_maximo": float(e.max()),
        "acima_2": int((e > 2.0 + 1e-12).sum()),
        "fracao_acima_2": float(np.average(e > 2.0 + 1e-12, weights=w)),
    }


def avaliar(
    catalogo: Mapping[str, Any],
    casos: Sequence[Mapping[str, Any]],
    inconsistentes: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Métricas por prova e totais, sem os registros inconsistentes."""
    inconsistentes = inconsistentes or {}
    usados = [c for c in casos if c["case_id"] not in inconsistentes]
    notas = notas_casos(calculador(catalogo), usados)
    erros: Dict[str, List[float]] = defaultdict(list)
    faixas: Dict[str, List[str]] = defaultdict(list)
    for caso, nota in zip(usados, notas):
        chave = f"{caso['ano']},{caso['area']},{caso['co_prova']}"
        erros[chave].append(abs(nota - caso["nota_oficial"]))
        faixas[chave].append(caso["faixa"])
    todos = [e for chave in erros for e in erros[chave]]
    return {
        "por_prova": {k: metricas(erros[k], faixas[k]) for k in sorted(erros)},
        "total": {k: v for k, v in metricas(todos).items() if k != "faixas_cobertas"},
        "case_ids_sha256": assinatura(c["case_id"] for c in casos),
        "excluidos": sorted(c["case_id"] for c in casos if c["case_id"] in inconsistentes),
    }


def pesos_estrato(casos: Sequence[Mapping[str, Any]], contagens: Mapping[tuple, int]) -> List[float]:
    amostrados = Counter(
        (f"{c['ano']},{c['area']},{c['co_prova']}", c["tp_lingua"], c["faixa"]) for c in casos
    )
    return [
        contagens[(f"{c['ano']},{c['area']},{c['co_prova']}", c["tp_lingua"], c["faixa"])]
        / amostrados[(f"{c['ano']},{c['area']},{c['co_prova']}", c["tp_lingua"], c["faixa"])]
        for c in casos
    ]


def verificar_inconsistentes(
    catalogo: Mapping[str, Any],
    casos: Sequence[Mapping[str, Any]],
    inconsistentes: Mapping[str, Mapping[str, Any]],
) -> List[str]:
    """Cada registro erra no código declarado e reproduz a nota no alternativo.

    Os que vêm das fixtures também precisam coincidir com o caso de mesmo ``case_id``.
    """
    calc = calculador(catalogo)
    falhas = []
    for chave, registro in inconsistentes.items():
        declarado = calc.calcular_nota(
            registro["ano"], registro["area"], registro["co_prova"],
            registro["respostas"], registro["tp_lingua"],
        )["nota"]
        alvo = registro["reproduz"]
        lingua = alvo.get("tp_lingua", registro["tp_lingua"]) if alvo["area"] == "LC" else None
        alternativo = calc.calcular_nota(
            registro["ano"], alvo["area"], alvo["co_prova"], registro["respostas"], lingua,
        )["nota"]
        if (abs(declarado - registro["nota_oficial"]) <= LIMITE_INCONSISTENCIA
                or abs(alternativo - alvo["nota_oficial"]) > TOLERANCIA_ARREDONDAMENTO):
            falhas.append(f"{chave}: exclusão por inconsistência não se sustenta")
    for caso in casos:
        registro = inconsistentes.get(caso["case_id"])
        if registro is not None and chave_registro(registro) != chave_registro(caso):
            falhas.append(f"{caso['case_id']}: registro inconsistente diverge da fixture")
    return falhas


def ajustar_escala(calc, treino, inconsistentes) -> Dict[str, Dict[str, float]]:
    """Por área, minimiza a soma das violações do arredondamento (±0,05).

    Usa só padrões com ao menos um acerto e um erro: a nota de gabarito e a
    de zero acerto não dependem da escala.
    """
    from scipy.optimize import linprog
    from scipy.sparse import csr_matrix, eye, hstack, vstack

    por_area: Dict[str, List] = defaultdict(list)
    grupos = defaultdict(list)
    for caso in treino:
        if caso["case_id"] not in inconsistentes:
            grupos[(caso["ano"], caso["area"], caso["co_prova"], caso["tp_lingua"])].append(caso)
    for (ano, area, prova, lingua), casos in grupos.items():
        itens, u = calc.preparar_respostas_batch(ano, area, prova, [c["respostas"] for c in casos], lingua)
        ativos = np.asarray([not item.abandonado for item in itens])
        acertos = u[:, ativos].sum(axis=1)
        theta = calc.estimar_theta_eap_batch(u, itens)
        interno = (acertos > 0) & (acertos < ativos.sum())
        por_area[area].extend(zip(theta[interno], np.asarray([c["nota_oficial"] for c in casos])[interno]))
    escala = {}
    for area, pares in sorted(por_area.items()):
        x, y = map(np.asarray, zip(*pares))
        n = len(x)
        X, identidade = csr_matrix(np.c_[x, np.ones(n)]), eye(n)
        r = linprog(
            np.r_[0, 0, np.ones(n)],
            A_ub=vstack([hstack([X, -identidade]), hstack([-X, -identidade])]),
            b_ub=np.r_[y + 0.05, -y + 0.05],
            bounds=[(None, None)] * 2 + [(0, None)] * n, method="highs",
        )
        if not r.success:
            raise RuntimeError(f"{area}: ajuste da escala falhou: {r.message}")
        escala[area] = {"slope": float(r.x[0]), "intercept": float(r.x[1]), "n_treino": n}
    return escala
