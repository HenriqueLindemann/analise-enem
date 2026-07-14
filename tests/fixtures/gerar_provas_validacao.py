#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera tests/fixtures/provas_validacao.md a partir das fixtures e metadados atuais.

Lê:
  - tests/fixtures/exemplos_microdados.json   (quais CO_PROVAs foram testados)
  - src/tri_enem/mapeamento_provas.yaml        (nomes legíveis)
  - src/tri_enem/coeficientes_data.json        (status e MAE por prova)

Saída:
  - tests/fixtures/provas_validacao.md

Uso:
    python tests/fixtures/gerar_provas_validacao.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

DATA_COEF = ROOT / "src" / "tri_enem" / "coeficientes_data.json"
MAPEAMENTO = ROOT / "src" / "tri_enem" / "mapeamento_provas.yaml"
EXEMPLOS   = ROOT / "tests" / "fixtures" / "exemplos_microdados.json"
SAIDA      = ROOT / "tests" / "fixtures" / "provas_validacao.md"

TIPO_LEGIVEL = {
    "1a_aplicacao":       "1ª Aplicação",
    "digital":            "Digital",
    "reaplicacao":        "Reaplicação",
    "segunda_oportunidade": "2ª Oportunidade",
    "especiais":          "Especial",
    "ppl":                "PPL",
}

STATUS_EMOJI = {
    "ok":           "✅",
    "aviso_leve":   "ℹ️",
    "aviso_forte":  "⚠️",
    "erro_alto":    "❌",
    "falhou":       "❌",
    "nao_calibrado":"❓",
    "desconhecido": "❓",
}

STATUS_ORDER = ["ok", "aviso_leve", "aviso_forte", "erro_alto", "falhou", "nao_calibrado", "desconhecido"]


def _build_lookup(mapeamento_raw: dict) -> dict[int, dict]:
    lookup: dict[int, dict] = {}
    for ano_key, dados_ano in mapeamento_raw.items():
        if str(ano_key).startswith("_"):
            continue
        try:
            ano = int(ano_key)
        except ValueError:
            continue
        for area, dados_area in dados_ano.items():
            if area not in ("MT", "CN", "CH", "LC") or not isinstance(dados_area, dict):
                continue
            for tipo, cores in dados_area.items():
                if not isinstance(cores, dict):
                    continue
                for cor, codigo in cores.items():
                    try:
                        lookup[int(codigo)] = {"ano": ano, "area": area, "tipo": tipo, "cor": cor}
                    except (TypeError, ValueError):
                        pass
    return lookup


def gerar(saida: Path = SAIDA) -> None:
    data_coef  = json.loads(DATA_COEF.read_text(encoding="utf-8"))
    exemplos   = json.loads(EXEMPLOS.read_text(encoding="utf-8"))
    mapeamento = yaml.safe_load(MAPEAMENTO.read_text(encoding="utf-8"))

    lookup = _build_lookup(mapeamento)
    exemplos_por_prova: dict[int, int] = Counter(int(x["co_prova"]) for x in exemplos)

    linhas_por_ano: dict[int, list] = defaultdict(list)
    for co_prova_int in sorted(exemplos_por_prova):
        info = lookup.get(co_prova_int, {})
        ano  = info.get("ano", "?")
        area = info.get("area", "?")
        tipo = info.get("tipo", "desconhecido")
        cor  = info.get("cor", "desconhecida")
        n    = exemplos_por_prova[co_prova_int]

        key = f"{ano},{area},{co_prova_int}"
        status_info = data_coef.get("status_provas", {}).get(key, {})
        coef_info   = data_coef.get("por_prova", {}).get(key, {})
        status  = status_info.get("status", "desconhecido")
        mae     = coef_info.get("mae")
        mae_str = f"{mae:.2f}" if mae is not None else "-"

        linhas_por_ano[ano].append((co_prova_int, area, tipo, cor, n, status, mae_str))

    total_provas  = len(exemplos_por_prova)
    total_exemplos = sum(exemplos_por_prova.values())
    n_por_prova   = total_exemplos // total_provas if total_provas else 0

    status_todos: list[str] = []
    for co in exemplos_por_prova:
        info = lookup.get(co, {})
        ano, area = info.get("ano", "?"), info.get("area", "?")
        key = f"{ano},{area},{co}"
        status_todos.append(data_coef.get("status_provas", {}).get(key, {}).get("status", "desconhecido"))
    cnt_status = Counter(status_todos)

    md: list[str] = []

    md += [
        "# Mapeamento das Provas na Suite de Validação",
        "",
        "Este arquivo lista todas as provas cobertas pela suite de validação, com nomes",
        "legíveis extraídos do `mapeamento_provas.yaml` em vez dos códigos brutos (`CO_PROVA`).",
        "",
        "**Fontes de dados:**",
        "- `tests/fixtures/exemplos_microdados.json` — exemplos extraídos dos microdados reais (10 por prova)",
        "- `src/tri_enem/mapeamento_provas.yaml` — mapeamento CO_PROVA → ano/área/tipo/cor",
        "- `src/tri_enem/coeficientes_data.json` — status de calibração e MAE por prova",
        "",
        "**Para regenerar este arquivo** (após um novo ciclo de validação):",
        "",
        "```bash",
        "python tests/fixtures/gerar_provas_validacao.py",
        "```",
        "",
        "Ou, para rodar o pipeline completo do zero:",
        "",
        "```bash",
        "python tests/run_full_validation.py \\",
        "  --microdados-dir /caminho/para/microdados_inep \\",
        "  --n-max 10 --atualizar-status",
        "```",
        "",
        "---",
        "",
        "## Legenda",
        "",
        "### Tipos de Aplicação",
        "",
        "| Código YAML | Nome |",
        "|-------------|------|",
        "| `1a_aplicacao` | 1ª Aplicação (aplicação regular) |",
        "| `reaplicacao` | Reaplicação (segunda chance) |",
        "| `digital` | Aplicação Digital (2020+) |",
        "| `segunda_oportunidade` | 2ª Oportunidade |",
        "| `especiais` | Provas especiais (adaptadas, Libras, etc.) |",
        "| `ppl` | Pessoas Privadas de Liberdade |",
        "",
        "### Status de Calibração",
        "",
        "O status é derivado do MAE (Erro Absoluto Médio) entre nota calculada e nota oficial,",
        "medido sobre os 10 exemplos reais de cada prova.",
        "",
        "| Emoji | Status | Critério | Interpretação |",
        "|-------|--------|----------|---------------|",
        "| ✅ | `ok` | MAE ≤ 2 pts | Calibração confiável |",
        "| ℹ️ | `aviso_leve` | 2 < MAE ≤ 5 pts | Boa estimativa, pequena diferença possível |",
        "| ⚠️ | `aviso_forte` | 5 < MAE ≤ 15 pts | Estimativa com margem maior |",
        "| ❌ | `erro_alto` | MAE > 15 pts | Calibração ruim — use com cautela |",
        "| ❌ | `falhou` | Erro na calibração | Coeficientes inválidos ou ausentes |",
        "| ❓ | `desconhecido` | Sem dados suficientes | Não há exemplos válidos para estimar MAE |",
        "",
        "> **MAE `-`**: prova com status definido pela calibração (`calibrar_com_mapeamento.py`),",
        "> sem coeficientes lineares em `por_prova` (comum em provas de reaplicação e especiais).",
        "",
        "---",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Anos cobertos | {min(linhas_por_ano)} – {max(linhas_por_ano)} |",
        f"| Provas únicas | {total_provas} |",
        f"| Exemplos totais | {total_exemplos} ({n_por_prova} por prova) |",
        "",
        "### Status de Calibração",
        "",
        "| Status | Provas |",
        "|--------|--------|",
    ]
    for s in STATUS_ORDER:
        if cnt_status.get(s, 0):
            md.append(f"| {s} | {cnt_status[s]} |")

    md += ["", "---", "", "## Provas por Ano", ""]
    md.append("Colunas: **CO_PROVA** · **Área** · **Tipo de Aplicação** · **Cor** · **N exemplos** · **Status** · **MAE (pts)**")
    md.append("")

    for ano in sorted(linhas_por_ano):
        rows = linhas_por_ano[ano]
        md += [
            f"### {ano}",
            "",
            "| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |",
            "|----------|------|-----------|-----|---|--------|-----|",
        ]
        for (co_prova, area, tipo, cor, n, status, mae_str) in rows:
            tipo_leg = TIPO_LEGIVEL.get(tipo, tipo)
            emoji    = STATUS_EMOJI.get(status, "❓")
            md.append(f"| {co_prova} | {area} | {tipo_leg} | {cor} | {n} | {emoji} {status} | {mae_str} |")
        md.append("")

    saida.write_text("\n".join(md), encoding="utf-8")
    print(f"✅ {saida.relative_to(ROOT)} — {total_provas} provas, {total_exemplos} exemplos")


if __name__ == "__main__":
    gerar()
