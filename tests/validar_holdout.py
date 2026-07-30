#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Valida o holdout real contra o catálogo v3 e retorna erro em divergências."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tri_enem import (  # noqa: E402
    CalculadorTRI,
    MapeadorProvas,
    aplicar_transformacao,
)
from tri_enem.calibracao_modelos import classificar_validacao  # noqa: E402

ITEM_MANIFEST = ROOT / "src" / "tri_enem" / "data" / "itens" / "manifest.json"
HOLDOUT_FIELDS = {
    "case_id",
    "ano",
    "area",
    "co_prova",
    "tp_lingua",
    "nota_oficial",
    "respostas",
    "faixa",
    "split",
}


def _sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_holdout(caminho: Path) -> list[dict]:
    casos = []
    with gzip.open(caminho, "rt", encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue
            try:
                caso = json.loads(linha)
            except ValueError as exc:
                raise ValueError(f"Linha {numero} inválida: {exc}") from exc
            casos.append(caso)
    return casos


def validar_relatorio_derivado(
    catalogo: dict,
    manifesto_path: Path | None,
    relatorio_path: Path,
) -> str | None:
    """Compara o relatório inteiro com a geração determinística esperada."""
    try:
        relatorio = relatorio_path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"relatório ausente: {exc}"
    if manifesto_path is None or not manifesto_path.exists():
        return "manifesto necessário para validar o relatório derivado"
    try:
        manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        return f"manifesto inválido para o relatório derivado: {exc}"

    from tools.recalibrar_validacao import gerar_relatorio

    if relatorio != gerar_relatorio(catalogo, manifesto):
        return "relatório derivado desatualizado"
    return None


def validar(
    catalogo_path: Path,
    holdout_path: Path,
    manifesto_path: Path | None = None,
    relatorio_path: Path | None = None,
) -> list[str]:
    catalogo = json.loads(catalogo_path.read_text(encoding="utf-8"))
    if catalogo.get("schema_version") != 3:
        return ["coeficientes_data.json não usa schema_version=3"]
    casos = carregar_holdout(holdout_path)
    falhas = []
    mapeador = MapeadorProvas()
    esperadas = {
        f"{prova.ano},{prova.area},{prova.codigo}"
        for ano in mapeador.listar_anos_disponiveis()
        for prova in mapeador.listar_todas_provas(ano)
    }
    encontradas = set(catalogo.get("por_prova", {}))
    if esperadas != encontradas:
        falhas.append(
            "cobertura do catálogo diverge do mapeamento: "
            f"faltam={sorted(esperadas - encontradas)[:5]}, "
            f"sobram={sorted(encontradas - esperadas)[:5]}"
        )
    status_validos = {
        "ok", "aviso_leve", "aviso_forte", "erro_alto",
        "nao_calibrado", "sem_participantes", "sem_itens",
    }
    for chave, info in catalogo.get("por_prova", {}).items():
        qualidade = info.get("qualidade") or {}
        status = qualidade.get("status")
        validacao = info.get("validacao") or {}
        if status not in status_validos:
            falhas.append(f"{chave}: status inválido {status!r}")
        if not qualidade.get("motivo"):
            falhas.append(f"{chave}: prova sem motivo catalogado")
        if status != "sem_itens" and not info.get("transformacao"):
            falhas.append(f"{chave}: prova calculável sem transformação")
        if status == "ok" and float(
            validacao.get("erro_maximo", math.inf)
        ) > 2.0 + 1e-12:
            falhas.append(f"{chave}: ok com erro máximo >2")

    ids = set()
    grupos = defaultdict(list)
    for caso in casos:
        campos_inesperados = set(caso) - HOLDOUT_FIELDS
        campos_ausentes = HOLDOUT_FIELDS - set(caso)
        if campos_inesperados or campos_ausentes:
            falhas.append(
                f"{caso.get('case_id')}: campos ausentes={sorted(campos_ausentes)}, "
                f"inesperados={sorted(campos_inesperados)}"
            )
        campos_privados = {
            campo for campo in caso
            if any(
                termo in campo.lower()
                for termo in ("inscricao", "identificador", "sequencial", "id_col")
            )
        }
        if campos_privados:
            falhas.append(f"{caso.get('case_id')}: identificador pessoal presente")
        case_id = caso.get("case_id")
        if (
            not isinstance(case_id, str)
            or len(case_id) != 24
            or any(c not in "0123456789abcdef" for c in case_id)
            or case_id in ids
        ):
            falhas.append(f"case_id ausente ou duplicado: {case_id!r}")
        ids.add(case_id)
        if caso.get("split") != "holdout":
            falhas.append(f"{case_id}: split diferente de holdout")
        try:
            nota = float(caso["nota_oficial"])
        except (KeyError, TypeError, ValueError):
            nota = math.nan
        if not math.isfinite(nota) or nota <= 0:
            falhas.append(f"{case_id}: nota oficial inválida {nota!r}")
        chave = (
            int(caso["ano"]),
            str(caso["area"]).upper(),
            int(caso["co_prova"]),
            caso.get("tp_lingua"),
        )
        grupos[chave].append(caso)

    calc = CalculadorTRI()
    erros_por_prova = defaultdict(list)
    faixas_por_prova = defaultdict(list)
    for (ano, area, prova, lingua), grupo in sorted(grupos.items()):
        try:
            itens, respostas = calc.preparar_respostas_batch(
                ano,
                area,
                prova,
                [caso["respostas"] for caso in grupo],
                lingua,
            )
            thetas = calc.estimar_theta_eap_batch(respostas, itens)
            info = catalogo["por_prova"].get(f"{ano},{area},{prova}") or {}
            transformacao = info.get("transformacao")
            if not transformacao:
                transformacao = {
                    "tipo": "linear",
                    **catalogo["por_area"][f"{ano},{area}"],
                }
            notas = np.asarray([
                aplicar_transformacao(theta, transformacao) for theta in thetas
            ])
        except Exception as exc:
            falhas.append(f"{ano}/{area}/{prova}/{lingua}: cálculo falhou: {exc}")
            continue
        oficiais = np.asarray([float(caso["nota_oficial"]) for caso in grupo])
        chave_prova = f"{ano},{area},{prova}"
        erros_por_prova[chave_prova].extend(np.abs(notas - oficiais).tolist())
        faixas_por_prova[chave_prova].extend(caso["faixa"] for caso in grupo)

    for chave, info in catalogo["por_prova"].items():
        validacao = info.get("validacao")
        qualidade = info.get("qualidade") or {}
        status = qualidade.get("status")
        if not validacao:
            if chave in erros_por_prova:
                falhas.append(f"{chave}: possui casos, mas não possui métricas")
            continue
        erros = np.asarray(erros_por_prova.get(chave, []), dtype=float)
        if len(erros) != int(validacao["n"]):
            falhas.append(
                f"{chave}: n recalculado={len(erros)} != catálogo={validacao['n']}"
            )
            continue
        calculadas = {
            "mae": float(erros.mean()),
            "erro_p95": float(np.percentile(erros, 95)),
            "erro_maximo": float(erros.max()),
        }
        for metrica, valor in calculadas.items():
            if not math.isclose(
                valor, float(validacao[metrica]), rel_tol=0, abs_tol=1e-8
            ):
                falhas.append(
                    f"{chave}: {metrica} recalculado={valor:.12f} "
                    f"!= catálogo={validacao[metrica]:.12f}"
                )
        metricas_status = {
            **validacao,
            "faixas_cobertas": sorted(set(faixas_por_prova[chave])),
        }
        esperado, _ = classificar_validacao(
            metricas_status, validacao.get("faixas_existentes", [])
        )
        if esperado != status:
            falhas.append(f"{chave}: status={status}, esperado={esperado}")
        if status == "ok" and calculadas["erro_maximo"] > 2.0 + 1e-12:
            falhas.append(f"{chave}: ok com erro máximo >2")

    if manifesto_path is not None:
        try:
            manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            falhas.append(f"manifesto ausente ou corrompido: {exc}")
        else:
            cobertura = manifesto.get("coverage") or {}
            if cobertura.get("mapped_proofs") != len(encontradas):
                falhas.append("manifesto com contagem de provas desatualizada")
            if cobertura.get("holdout_cases") != len(casos):
                falhas.append("manifesto com contagem de holdout desatualizada")
            status_manifesto = cobertura.get("status") or {}
            status_catalogo = defaultdict(int)
            for info in catalogo.get("por_prova", {}).values():
                status_catalogo[(info.get("qualidade") or {}).get("status")] += 1
            if status_manifesto != dict(sorted(status_catalogo.items())):
                falhas.append("manifesto com contagens de status desatualizadas")
            if manifesto.get("generated_at") != (
                catalogo.get("metadata") or {}
            ).get("ultima_calibracao"):
                falhas.append("manifesto e catálogo têm datas divergentes")
            fontes = manifesto.get("sources") or []
            if (
                len(fontes) != 17
                or len({fonte.get("file") for fonte in fontes}) != 17
                or any(not fonte.get("sha256") for fonte in fontes)
            ):
                falhas.append("manifesto sem hashes das 17 fontes oficiais")
            if (
                not ITEM_MANIFEST.exists()
                or manifesto.get("item_data_manifest_sha256")
                != _sha256(ITEM_MANIFEST)
            ):
                falhas.append("manifesto de validação não corresponde aos dados de itens")
            estratos = manifesto.get("strata_counts") or []
            if cobertura.get("strata") != len(estratos):
                falhas.append("manifesto com contagem de estratos desatualizada")
            holdout_manifesto = defaultdict(int)
            for estrato in estratos:
                chave = (
                    estrato.get("prova"),
                    estrato.get("tp_lingua"),
                    estrato.get("faixa"),
                )
                holdout_manifesto[chave] += int(estrato.get("holdout", 0))
            holdout_real = defaultdict(int)
            for caso in casos:
                holdout_real[(
                    f"{caso['ano']},{str(caso['area']).upper()},{caso['co_prova']}",
                    caso.get("tp_lingua"),
                    caso.get("faixa"),
                )] += 1
            if not estratos or dict(holdout_manifesto) != dict(holdout_real):
                falhas.append("contagens por estrato/split ausentes ou divergentes")

    if relatorio_path is not None:
        falha_relatorio = validar_relatorio_derivado(
            catalogo, manifesto_path, relatorio_path
        )
        if falha_relatorio:
            falhas.append(falha_relatorio)
    return falhas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalogo",
        type=Path,
        default=ROOT / "src" / "tri_enem" / "coeficientes_data.json",
    )
    parser.add_argument(
        "--holdout",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "validation_holdout.jsonl.gz",
    )
    parser.add_argument(
        "--manifesto",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "validation_manifest.json",
    )
    parser.add_argument(
        "--relatorio",
        type=Path,
        default=ROOT / "docs" / "VALIDATION_REPORT.md",
    )
    args = parser.parse_args()
    if not args.catalogo.exists() or not args.holdout.exists():
        print("[falha] Catálogo ou holdout não encontrado")
        return 1
    falhas = validar(
        args.catalogo, args.holdout, args.manifesto, args.relatorio
    )
    if falhas:
        print(f"[falha] {len(falhas)} divergência(s)")
        for falha in falhas[:50]:
            print(f"  {falha}")
        return 1
    print("[ok] Holdout real reproduz o catálogo e todas as invariantes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
