#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Valida exemplos de microdados: compara nota calculada vs nota oficial.

Quando há múltiplos exemplos por CO_PROVA (--n-max > 1 em gerar_exemplos_microdados.py)
o MAE por prova é muito mais representativo.

Com --atualizar-status, provas com validação divergente do status atual são
atualizadas em coeficientes_data.json (status e mensagem de aviso).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import _utils

_utils.add_src_to_path()

from tri_enem.simulador import SimuladorNota

# Thresholds de classificação (alinhados com calibrar_com_mapeamento.py)
MAE_OK          = 2.0
MAE_AVISO_LEVE  = 5.0
MAE_AVISO_FORTE = 15.0


def _classificar_mae(mae: float) -> str:
    if mae <= MAE_OK:
        return "ok"
    if mae <= MAE_AVISO_LEVE:
        return "aviso_leve"
    if mae <= MAE_AVISO_FORTE:
        return "aviso_forte"
    return "erro_alto"


def _mensagem_para_status(status: str, mae: float) -> str | None:
    if status == "ok":
        return None
    if status == "aviso_leve":
        return (
            f"ℹ️ Esta prova tem boa calibração, mas pode haver diferença de até "
            f"{mae:.1f} pontos em relação à nota oficial."
        )
    if status == "aviso_forte":
        return (
            f"⚠️ Atenção: calibração parcial. Erro médio de {mae:.1f} pontos. "
            "Use como estimativa."
        )
    return (
        f"⚠️ ATENÇÃO: Esta prova não está calibrada corretamente. "
        f"Erro médio de {mae:.1f} pontos — a nota pode variar bastante da oficial."
    )


def validar(
    exemplos_path: Path,
    microdados_limpos: Path,
    atualizar_status: bool = False,
) -> None:
    exemplos: List[dict] = json.loads(exemplos_path.read_text(encoding="utf-8"))
    sim = SimuladorNota(microdados_path=str(microdados_limpos))

    total = len(exemplos)
    print(f"Total de exemplos: {total}", flush=True)

    # Acumular erros por prova e globalmente
    diffs_global: List[float] = []
    por_prova: Dict[tuple, List[float]] = defaultdict(list)  # (ano,area,co_prova) -> [|dif|]
    provas_nao_encontradas: Dict[tuple, int] = {}

    for i, item in enumerate(exemplos, start=1):
        ano      = int(item["ano"])
        area     = item["area"]
        co_prova = int(item["co_prova"])
        tp_lingua = item.get("tp_lingua")
        lingua    = _utils.lingua_por_tp(tp_lingua)
        nota_oficial = _utils.to_float(item["nota_oficial"])
        respostas    = item["respostas"]

        try:
            resultado = sim.calcular(
                area=area,
                ano=ano,
                respostas=respostas,
                lingua=lingua if area == "LC" else "ingles",
                co_prova=co_prova,
            )
        except (KeyError, ValueError) as e:
            chave = (ano, area, co_prova)
            provas_nao_encontradas[chave] = provas_nao_encontradas.get(chave, 0) + 1
            continue

        dif = abs(resultado.nota - nota_oficial)
        diffs_global.append(dif)
        por_prova[(ano, area, co_prova)].append(dif)

        if i % 200 == 0 or i == total:
            print(f"Progresso: {i}/{total}", flush=True)

    # Relatório global
    print("\n" + "=" * 72)
    if diffs_global:
        mae_global = sum(diffs_global) / len(diffs_global)
        max_dif    = max(diffs_global)
        print(f"MAE global          : {mae_global:.2f} pontos")
        print(f"Erro máximo         : {max_dif:.2f} pontos")
        print(f"Exemplos validados  : {len(diffs_global)}")
    print(f"Provas sem dados    : {len(provas_nao_encontradas)}")

    # Relatório por prova
    provas_com_aviso: List[tuple] = []
    print("\n--- MAE por CO_PROVA ---")
    print(f"{'ANO':<5} {'AREA':<4} {'PROVA':<6} {'N':>3} {'MAE':>6} STATUS")
    print("-" * 40)

    for (ano, area, co_prova), erros in sorted(por_prova.items()):
        mae    = sum(erros) / len(erros)
        status = _classificar_mae(mae)
        flag   = "" if status == "ok" else ("⚠" if "aviso" in status else "❌")
        print(f"{ano:<5} {area:<4} {co_prova:<6} {len(erros):>3} {mae:>6.2f} {flag} {status}")
        if status != "ok":
            provas_com_aviso.append((ano, area, co_prova, mae, status))

    if provas_nao_encontradas:
        print("\n--- Provas não encontradas ---")
        for (ano, area, co_prova), count in sorted(provas_nao_encontradas.items()):
            print(f"  {ano} {area} CO_PROVA {co_prova}: {count} caso(s)")

    # Atualizar status em coeficientes_data.json se solicitado
    if atualizar_status and por_prova:
        _atualizar_coeficientes(provas_com_aviso, por_prova)


def _atualizar_coeficientes(
    provas_com_aviso: List[tuple],
    por_prova: Dict[tuple, List[float]],
) -> None:
    """Atualiza status_provas em coeficientes_data.json com base na validação."""
    data_path = Path(__file__).resolve().parents[1] / "src" / "tri_enem" / "coeficientes_data.json"
    if not data_path.exists():
        print("\n⚠️  coeficientes_data.json não encontrado — status não atualizado.")
        return

    data = json.loads(data_path.read_text(encoding="utf-8"))
    status_provas = data.setdefault("status_provas", {})
    por_prova_coef = data.setdefault("por_prova", {})

    atualizados = 0
    for (ano, area, co_prova), erros in por_prova.items():
        # Só atualiza se temos amostras suficientes para ter confiança
        if len(erros) < 3:
            continue

        key       = f"{ano},{area},{co_prova}"
        mae       = sum(erros) / len(erros)
        novo_status = _classificar_mae(mae)
        atual     = status_provas.get(key, {}).get("status", "desconhecido")

        # Só atualiza quando a validação revela problema não registrado
        # ou quando melhora um status pessimista anterior
        mudou = novo_status != atual and atual not in ("falhou", "nao_calibrado")
        if mudou:
            status_provas[key] = {
                **status_provas.get(key, {}),
                "status":   novo_status,
                "mensagem": _mensagem_para_status(novo_status, mae),
            }
            # Atualiza MAE em por_prova apenas se a entrada já existe (preserva slope/intercept)
            coef_atual = por_prova_coef.get(key)
            if coef_atual is not None and len(erros) >= (coef_atual.get("n_amostras") or 0):
                por_prova_coef[key] = {**coef_atual, "mae": mae}
            atualizados += 1
            print(f"  Atualizado {key}: {atual} → {novo_status} (MAE={mae:.2f})")

    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ {atualizados} status atualizados em {data_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Comparar notas calculadas vs microdados e (opcionalmente) atualizar status."
    )
    parser.add_argument(
        "--exemplos",
        default=str(_utils.EXEMPLOS_PATH),
        help="Arquivo JSON de exemplos gerado por gerar_exemplos_microdados.py",
    )
    parser.add_argument(
        "--microdados-limpos", default="microdados_limpos",
        help="Diretório microdados_limpos",
    )
    parser.add_argument(
        "--atualizar-status", action="store_true",
        help=(
            "Atualiza status_provas em coeficientes_data.json quando a validação "
            "diverge da calibração (requer ≥3 exemplos por prova)"
        ),
    )
    args = parser.parse_args()

    exemplos_path    = Path(args.exemplos)
    microdados_limpos = Path(args.microdados_limpos)

    if not exemplos_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {exemplos_path}")
    if not microdados_limpos.exists():
        raise SystemExit(f"Diretório não encontrado: {microdados_limpos}")

    validar(exemplos_path, microdados_limpos, args.atualizar_status)


if __name__ == "__main__":
    main()
