# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Gera ``docs/VALIDATION_REPORT.md`` a partir do catálogo e do manifesto primário.

Os números por prova vêm do censo (todos os participantes); o teste por amostra
aparece como confirmação independente.
"""

from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tri_enem.precisao import (  # noqa: E402
    PERFIL_BOA_COM_EXCECOES, PERFIL_CALIBRACAO_VERIFICADA, PERFIL_ESTIMATIVA,
    PERFIL_SEM_VALIDACAO, classificar_perfil_validacao, formatar_percentual,
    formatar_proporcao_censo, metricas_prova, metricas_teste,
)

AREAS = {
    "CH": "Ciências Humanas",
    "CN": "Ciências da Natureza",
    "LC": "Linguagens",
    "MT": "Matemática",
}
APLICACOES = {
    "1a_aplicacao": "1ª aplicação",
    "digital": "Prova digital",
    "reaplicacao": "Reaplicação",
    "reaplicacao_2": "2ª reaplicação",
    "segunda_oportunidade": "Segunda oportunidade",
}
PERFIS = {
    PERFIL_CALIBRACAO_VERIFICADA: "Boa calibração verificada",
    PERFIL_BOA_COM_EXCECOES: "Precisa para quase todos",
    PERFIL_ESTIMATIVA: "Estimativa com variação relevante",
    PERFIL_SEM_VALIDACAO: "Sem validação suficiente",
}
SIGNIFICADO_PERFIS = {
    PERFIL_CALIBRACAO_VERIFICADA: "Praticamente todas as notas ficaram a até 2 pontos da oficial.",
    PERFIL_BOA_COM_EXCECOES: "Quase todas batem; um pequeno grupo passou de 2 pontos.",
    PERFIL_ESTIMATIVA: "As diferenças não se limitam a poucos casos. Use com cautela.",
    PERFIL_SEM_VALIDACAO: "A nota é calculada, mas faltam notas oficiais para conferi-la.",
}
MOTIVOS_SEM_VALIDACAO = {
    "sem_participantes": "sem participantes nos microdados do INEP",
    "sem_itens": "sem parâmetros de itens publicados (nota indisponível)",
    "nao_calibrado": "participantes de menos para conferir",
}
STATUS = (
    ("ok", "menos de 5 participantes acima de 2 pontos"),
    ("erro_raro", "5 ou mais participantes acima de 2 pontos"),
    ("aviso_leve", "sem censo; maior erro do teste > 2 e ≤ 5 pontos"),
    ("aviso_forte", "sem censo; maior erro do teste > 5 e ≤ 15 pontos"),
    ("erro_alto", "sem censo; maior erro do teste > 15 pontos"),
    ("nao_calibrado", "menos de 30 participantes"),
    ("sem_participantes", "nenhum participante válido nos microdados"),
    ("sem_itens", "parâmetros dos itens indisponíveis"),
)


def _numero(valor: float, casas: int = 3) -> str:
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _inteiro(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def _ordem(chave: str) -> Tuple[int, str, int]:
    ano, area, prova = chave.split(",")
    return int(ano), area, int(prova)


def _rotulo(chave: str, info: Mapping[str, Any], com_ano: bool = True) -> str:
    ano, area, codigo = chave.split(",")
    partes = [f"ENEM {ano}"] if com_ano else []
    partes.append(AREAS.get(area, area))
    aplicacao = str(info.get("tipo_aplicacao") or "").strip()
    if aplicacao:
        partes.append(APLICACOES.get(aplicacao, aplicacao.replace("_", " ").capitalize()))
    cor = str(info.get("cor") or "").strip()
    if cor:
        partes.append(cor.replace("_", " ").capitalize())
    return " · ".join(partes) + f" (prova `{codigo}`)"


def _perfil(info: Mapping[str, Any]) -> str:
    m = metricas_prova(info)
    return classificar_perfil_validacao(
        info["qualidade"]["status"], m.get("erro_p95"), m.get("acima_2"), m.get("n"))


def _percentual(n: int, acima_2: int) -> str:
    return formatar_percentual(math.floor(10000 * (n - acima_2) / n) / 100)


def _agregado(metricas: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Soma das métricas de um grupo de provas."""
    metricas = [m for m in metricas if m and m.get("n")]
    n = sum(int(m["n"]) for m in metricas)
    if not n:
        return {"n": 0}
    acima_2 = sum(int(m["acima_2"]) for m in metricas)
    return {
        "n": n,
        "mae": sum(float(m["mae"]) * int(m["n"]) for m in metricas) / n,
        "acima_2": acima_2,
        "ate_2": _percentual(n, acima_2),
    }


def _lista_por_ano(chaves: List[str], por_prova: Mapping[str, Any]) -> List[str]:
    por_ano: Dict[str, List[str]] = defaultdict(list)
    for chave in sorted(chaves, key=_ordem):
        por_ano[chave.split(",")[0]].append(_rotulo(chave, por_prova[chave], com_ano=False))
    return [f"- **{ano}:** " + "; ".join(provas) for ano, provas in sorted(por_ano.items())]


def gerar_relatorio(catalogo: Dict[str, Any], manifesto: Dict[str, Any]) -> str:
    por_prova = catalogo["por_prova"]
    perfis = {chave: _perfil(info) for chave, info in por_prova.items()}
    contagem = Counter(perfis.values())
    metricas = {chave: metricas_prova(info) for chave, info in por_prova.items()}
    total = _agregado(metricas.values())
    teste = _agregado(metricas_teste(info) for info in por_prova.values())
    anos = sorted({int(chave.split(",")[0]) for chave in por_prova})
    treino = sum(int(e.get("n_treino", 0))
                 for e in ((catalogo.get("metadata") or {}).get("escala") or {}).values())
    com_falhas = contagem[PERFIL_BOA_COM_EXCECOES] + contagem[PERFIL_ESTIMATIVA]

    linhas = [
        "# Validação das notas TRI",
        "",
        "Quão perto a calculadora chega da nota oficial do INEP? As "
        f"**{_inteiro(total['n'])} notas** de todos os participantes do ENEM "
        f"{anos[0]}–{anos[-1]} nos microdados públicos foram comparadas com as calculadas.",
        "",
        "## Resumo",
        "",
        f"- **{_numero(total['mae'])} ponto** de diferença média.",
        f"- **{total['ate_2']}** das notas a até 2 pontos da oficial.",
        f"- **{contagem[PERFIL_CALIBRACAO_VERIFICADA]} de {_inteiro(len(por_prova))} provas** "
        f"verificadas, {com_falhas} com falhas conhecidas e "
        f"{contagem[PERFIL_SEM_VALIDACAO]} sem dados para conferir. Cada área, cor e "
        "aplicação conta como uma prova.",
        "",
        "## Sua prova",
        "",
        "Ao lado da nota, a calculadora indica uma destas situações:",
        "",
        "| Situação | O que significa | Provas |",
        "|---|---|---:|",
    ]
    for perfil in (PERFIL_CALIBRACAO_VERIFICADA, PERFIL_BOA_COM_EXCECOES,
                   PERFIL_ESTIMATIVA, PERFIL_SEM_VALIDACAO):
        if contagem[perfil] or perfil != PERFIL_ESTIMATIVA:
            linhas.append(f"| {PERFIS[perfil]} | {SIGNIFICADO_PERFIS[perfil]} | {contagem[perfil]} |")
    linhas.extend([
        "",
        "Por edição:",
        "",
        "| Ano | Provas | Verificadas | Com falhas | Sem validação | "
        "Notas | Diferença média | Até 2 pontos |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for ano in anos:
        chaves = [c for c in por_prova if int(c.split(",")[0]) == ano]
        p = Counter(perfis[c] for c in chaves)
        h = _agregado(metricas[c] for c in chaves)
        linhas.append(
            f"| {ano} | {len(chaves)} | {p[PERFIL_CALIBRACAO_VERIFICADA]} | "
            f"{p[PERFIL_BOA_COM_EXCECOES] + p[PERFIL_ESTIMATIVA]} | "
            f"{p[PERFIL_SEM_VALIDACAO]} | {_inteiro(h['n'])} | "
            + (f"{_numero(h['mae'])} | {h['ate_2']} |" if h["n"] else "— | — |")
        )
    linhas.extend([
        "",
        "Cada prova, por ano e cor, está no [detalhamento](#detalhamento-por-prova).",
        "",
        "## Provas com falhas conhecidas",
        "",
        "Nestas provas, um pequeno grupo de participantes ficou a mais de 2 pontos "
        "da nota oficial. Em 2011, o INEP anulou itens só para parte dos "
        "participantes, e a calculadora não tem como saber a qual grupo cada um pertence.",
        "",
        "| Prova | Participantes | Acima de 2 pontos | Proporção | Maior diferença |",
        "|---|---:|---:|---|---:|",
    ])
    falhas = sorted((c for c, p in perfis.items()
                     if p in (PERFIL_BOA_COM_EXCECOES, PERFIL_ESTIMATIVA)), key=_ordem)
    for chave in falhas:
        m = metricas[chave]
        proporcao = formatar_proporcao_censo(
            {"status": "erro_raro", "n_validacao": m["n"], "n_acima_2": m["acima_2"]}) or ""
        proporcao = proporcao.removeprefix("Cerca de ").split(" participantes")[0] or "—"
        maior = m.get("maior_diferenca", m.get("erro_maximo"))
        linhas.append(
            f"| {_rotulo(chave, por_prova[chave])} | {_inteiro(int(m['n']))} | "
            f"{_inteiro(int(m['acima_2']))} | {proporcao} | "
            f"{_numero(float(maior), 1) if maior is not None else '—'} |"
        )
    if not falhas:
        linhas.append("| Nenhuma | | | | |")

    sem_validacao: Dict[str, List[str]] = defaultdict(list)
    for chave, perfil in perfis.items():
        if perfil == PERFIL_SEM_VALIDACAO:
            sem_validacao[por_prova[chave]["qualidade"]["status"]].append(chave)
    linhas.extend([
        "",
        "## Provas sem validação",
        "",
        "A nota é calculada, mas não há notas oficiais para conferi-la.",
        "",
    ])
    for status, motivo in MOTIVOS_SEM_VALIDACAO.items():
        chaves = sem_validacao.get(status, [])
        if not chaves:
            continue
        linhas.extend([
            "<details>",
            f"<summary><strong>{len(chaves)}</strong> provas: {motivo}</summary>",
            "",
            *_lista_por_ano(chaves, por_prova),
            "",
            "</details>",
            "",
        ])

    contagem_status = Counter(info["qualidade"]["status"] for info in por_prova.values())
    linhas.extend([
        "## Como a validação é feita",
        "",
        "Para cada participante válido dos microdados, a nota calculada é comparada "
        "com a oficial. Cada prova recebe um status pelo número de participantes a "
        "mais de 2 pontos; 1 ou 2 casos isolados, com erro de dezenas de pontos, são "
        "registros corrompidos e não rebaixam a prova.",
        "",
        "| Status | Critério | Provas |",
        "|---|---|---:|",
        *(f"| `{s}` | {criterio} | {contagem_status[s]} |"
          for s, criterio in STATUS if contagem_status[s] or s in ("ok", "erro_raro")),
        "",
        f"A escala de cada área é ajustada com {_inteiro(treino)} participantes sorteados. "
        f"Outros {_inteiro(teste['n'])}, fora de todo ajuste, confirmam o resultado: "
        f"diferença média de {_numero(teste['mae'])} ponto e {teste['ate_2']} a até 2 pontos.",
        "",
        "Registros do INEP com respostas de outra prova (por exemplo, CN e CH "
        "trocadas) ficam fora das contas; estão em "
        "`tests/fixtures/registros_inconsistentes.json`.",
        "",
        "Por área:",
        "",
        "| Área | Provas | Notas | Diferença média | Até 2 pontos |",
        "|---|---:|---:|---:|---:|",
    ])
    for area, nome in sorted(AREAS.items(), key=lambda item: item[1]):
        chaves = [c for c in por_prova if c.split(",")[1] == area]
        h = _agregado(metricas[c] for c in chaves)
        linhas.append(
            f"| {nome} | {len(chaves)} | {_inteiro(h['n'])} | {_numero(h['mae'])} | {h['ate_2']} |"
        )
    linhas.extend([
        "",
        f"Modelo `{(catalogo.get('metadata') or {}).get('modelo', '—')}` · "
        f"gerado em `{manifesto['generated_at']}`.",
        "",
        "## Detalhamento por prova",
        "",
        "| Prova | Situação | Status | Participantes | Diferença média | Até 2 pontos | Acima de 2 |",
        "|---|---|---|---:|---:|---:|---:|",
    ])
    for chave in sorted(por_prova, key=_ordem):
        info, m = por_prova[chave], metricas[chave]
        if m.get("n"):
            numeros = (f"{_inteiro(int(m['n']))} | {_numero(float(m['mae']))} | "
                       f"{_percentual(int(m['n']), int(m['acima_2']))} | {_inteiro(int(m['acima_2']))}")
        else:
            numeros = "— | — | — | —"
        linhas.append(
            f"| {_rotulo(chave, info)} | {PERFIS[perfis[chave]]} | "
            f"`{info['qualidade']['status']}` | {numeros} |"
        )
    return "\n".join(linhas) + "\n"
