#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera um relatorio de provas problematicas (dif > limite ou nao encontradas).

Usa o mapeamento em src/tri_enem/mapeamento_provas.yaml para exibir tipo/cor.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import _utils

_utils.add_src_to_path()

from tri_enem.simulador import SimuladorNota


def gerar_relatorio(
    exemplos_path: Path,
    microdados_limpos: Path,
    mapeamento_path: Path,
    saida: Path,
    limite_dif: float,
) -> None:
    exemplos = json.loads(exemplos_path.read_text(encoding="utf-8"))
    sim = SimuladorNota(microdados_path=str(microdados_limpos))

    mapeamento, duplicados = _utils.carregar_mapeamento(mapeamento_path)

    dif_maior = []
    nao_encontradas = []
    inconsistencias = []

    total = 0
    avaliados = 0
    progress_interval = 100

    print(f"Total de exemplos: {len(exemplos)}", flush=True)
    for i, item in enumerate(exemplos, start=1):
        total += 1
        ano = int(item["ano"])
        area = item["area"]
        co_prova = int(item["co_prova"])

        info_map = _utils.info_mapeamento(mapeamento, co_prova)
        if info_map["mapeado_ano"] is not None:
            if info_map["mapeado_ano"] != ano or info_map["mapeado_area"] != area:
                inconsistencias.append({
                    "ano_exemplo": ano,
                    "area_exemplo": area,
                    "co_prova": co_prova,
                    "ano_mapeado": info_map["mapeado_ano"],
                    "area_mapeada": info_map["mapeado_area"],
                    "tipo_aplicacao": info_map["tipo_aplicacao"],
                    "cor": info_map["cor"],
                    "eh_especial": info_map["eh_especial"],
                })

        nota_oficial = _utils.to_float(item["nota_oficial"])
        respostas = item["respostas"]
        tp_lingua = item.get("tp_lingua")
        lingua = _utils.lingua_por_tp(tp_lingua)

        try:
            resultado = sim.calcular(
                area=area,
                ano=ano,
                respostas=respostas,
                lingua=lingua if area == "LC" else "ingles",
                co_prova=co_prova,
            )
        except KeyError as exc:
            nao_encontradas.append({
                "ano": ano,
                "area": area,
                "co_prova": co_prova,
                "tipo_aplicacao": info_map["tipo_aplicacao"],
                "cor": info_map["cor"],
                "eh_especial": info_map["eh_especial"],
                "erro": f"KeyError: {exc}",
            })
            continue
        except (ValueError, TypeError) as exc:
            nao_encontradas.append({
                "ano": ano,
                "area": area,
                "co_prova": co_prova,
                "tipo_aplicacao": info_map["tipo_aplicacao"],
                "cor": info_map["cor"],
                "eh_especial": info_map["eh_especial"],
                "erro": f"{type(exc).__name__}: {exc}",
            })
            continue

        avaliados += 1
        nota_calc = resultado.nota
        dif = nota_calc - nota_oficial

        if abs(dif) > limite_dif:
            dif_maior.append({
                "ano": ano,
                "area": area,
                "co_prova": co_prova,
                "tipo_aplicacao": info_map["tipo_aplicacao"],
                "cor": info_map["cor"],
                "eh_especial": info_map["eh_especial"],
                "nota_oficial": nota_oficial,
                "nota_calc": nota_calc,
                "dif": dif,
                "abs_dif": abs(dif),
            })

        if i % progress_interval == 0 or i == len(exemplos):
            print(
                f"Progresso: {i}/{len(exemplos)} | avaliados={avaliados} | "
                f"dif>limite={len(dif_maior)} | nao_encontradas={len(nao_encontradas)}",
                flush=True,
            )

    dif_maior.sort(key=lambda item: item["abs_dif"], reverse=True)
    nao_encontradas.sort(key=lambda item: (item["ano"], item["area"], item["co_prova"]))
    inconsistencias.sort(key=lambda item: (item["ano_exemplo"], item["area_exemplo"], item["co_prova"]))

    linhas = []
    linhas.append("# Provas problematicas")
    linhas.append("")
    linhas.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    linhas.append(f"Exemplos: {exemplos_path.as_posix()}")
    linhas.append(f"Microdados limpos: {microdados_limpos.as_posix()}")
    linhas.append(f"Mapeamento: {mapeamento_path.as_posix()}")
    linhas.append("")
    linhas.append("Resumo")
    linhas.append(f"- total_exemplos: {total}")
    linhas.append(f"- avaliados: {avaliados}")
    linhas.append(f"- dif_maior_limite: {len(dif_maior)}")
    linhas.append(f"- nao_encontradas: {len(nao_encontradas)}")
    linhas.append(f"- mapeamento_inconsistente: {len(inconsistencias)}")
    linhas.append(f"- codigos_duplicados_no_mapeamento: {len(duplicados)}")
    linhas.append("")

    linhas.append("## Dif maior que limite")
    if dif_maior:
        linhas.append("| ano | area | co_prova | tipo | cor | especial | nota_oficial | nota_calc | dif |")
        linhas.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for item in dif_maior:
            linhas.append(
                f"| {item['ano']} | {item['area']} | {item['co_prova']} | "
                f"{item['tipo_aplicacao']} | {item['cor']} | "
                f"{'sim' if item['eh_especial'] else 'nao'} | "
                f"{item['nota_oficial']:.1f} | {item['nota_calc']:.1f} | {item['dif']:.1f} |"
            )
    else:
        linhas.append("Nenhum caso acima do limite.")
    linhas.append("")

    linhas.append("## Provas nao encontradas no microdados_limpos")
    if nao_encontradas:
        linhas.append("| ano | area | co_prova | tipo | cor | especial | erro |")
        linhas.append("| --- | --- | --- | --- | --- | --- | --- |")
        for item in nao_encontradas:
            erro = item["erro"].replace("\n", " ")[:160]
            linhas.append(
                f"| {item['ano']} | {item['area']} | {item['co_prova']} | "
                f"{item['tipo_aplicacao']} | {item['cor']} | "
                f"{'sim' if item['eh_especial'] else 'nao'} | {erro} |"
            )
    else:
        linhas.append("Nenhum caso.")
    linhas.append("")

    if inconsistencias:
        linhas.append("## Inconsistencias com o mapeamento")
        linhas.append("| ano_exemplo | area_exemplo | co_prova | ano_mapeado | area_mapeada | tipo | cor | especial |")
        linhas.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for item in inconsistencias:
            linhas.append(
                f"| {item['ano_exemplo']} | {item['area_exemplo']} | {item['co_prova']} | "
                f"{item['ano_mapeado']} | {item['area_mapeada']} | "
                f"{item['tipo_aplicacao']} | {item['cor']} | "
                f"{'sim' if item['eh_especial'] else 'nao'} |"
            )
        linhas.append("")

    if duplicados:
        linhas.append("## Codigos duplicados no mapeamento")
        for codigo, infos in sorted(duplicados.items()):
            linhas.append(f"- {codigo}: {infos}")
        linhas.append("")

    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerar relatorio de provas problematicas.")
    parser.add_argument("--exemplos", default="tests/fixtures/exemplos_microdados.json", help="JSON de exemplos")
    parser.add_argument("--microdados-limpos", default="microdados_limpos", help="Diretorio microdados_limpos")
    parser.add_argument(
        "--mapeamento",
        default="src/tri_enem/mapeamento_provas.yaml",
        help="Arquivo de mapeamento de provas",
    )
    parser.add_argument("--saida", default="tests/provas_problematicas.md", help="Arquivo de saida")
    parser.add_argument("--limite-dif", type=float, default=_utils.LIMITE_DIF_PADRAO, 
                        help=f"Limite de diferenca absoluta (default: {_utils.LIMITE_DIF_PADRAO})")
    args = parser.parse_args()

    exemplos_path = Path(args.exemplos)
    microdados_limpos = Path(args.microdados_limpos)
    mapeamento_path = Path(args.mapeamento)
    saida = Path(args.saida)

    if not exemplos_path.exists():
        raise SystemExit(f"Arquivo nao encontrado: {exemplos_path}")
    if not microdados_limpos.exists():
        raise SystemExit(f"Diretorio nao encontrado: {microdados_limpos}")
    if not mapeamento_path.exists():
        raise SystemExit(f"Arquivo nao encontrado: {mapeamento_path}")

    gerar_relatorio(
        exemplos_path,
        microdados_limpos,
        mapeamento_path,
        saida,
        limite_dif=args.limite_dif,
    )
    print(f"Relatorio gerado: {saida}")


if __name__ == "__main__":
    main()
