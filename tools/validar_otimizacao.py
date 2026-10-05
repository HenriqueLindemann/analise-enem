#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Compara o motor atual com uma referência Git, sem recalibrar as fixtures.

O motor de referência usa os mesmos dados e módulos auxiliares, cuja ausência
de mudanças é conferida antes da comparação. O lote cobre todas as quatro
fixtures; a referência escalar cobre os extremos de cada prova/idioma do
holdout. Os relatórios contêm somente métricas agregadas e hashes.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import subprocess
import sys
import types
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tri_enem import CalculadorTRI, __version__  # noqa: E402
from tri_enem.calibracao_modelos import aplicar_modelo  # noqa: E402

FIXTURES = (
    "validation_holdout", "reconstruction_confirmation",
    "residual_confirmation", "mean_error_confirmation",
)


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validar(referencia: str) -> dict:
    commit = git("rev-parse", "--verify", f"{referencia}^{{commit}}").strip()
    # Os dois motores compartilham esses módulos e os artefatos publicados.
    compartilhados = [
        "src/tri_enem/coeficientes.py", "src/tri_enem/coeficientes_data.json",
        "src/tri_enem/calibracao_modelos.py", "src/tri_enem/tradutor.py",
        "src/tri_enem/posicoes.py", "src/tri_enem/ordem_provas.yaml",
        "src/tri_enem/mapeamento_provas.yaml", "src/tri_enem/data/itens",
        "tests/fixtures",
    ]
    if git("diff", commit, "--", *compartilhados).strip():
        raise ValueError("Dados ou módulos compartilhados divergem da referência")
    fonte = git("show", f"{commit}:src/tri_enem/calculador.py")
    modulo = types.ModuleType("tri_enem._referencia_otimizacao")
    sys.modules[modulo.__name__] = modulo
    exec(compile(fonte, f"{commit}/calculador.py", "exec"), modulo.__dict__)
    anterior, atual = modulo.CalculadorTRI(), CalculadorTRI()
    catalogo_path = ROOT / "src/tri_enem/coeficientes_data.json"
    catalogo = json.loads(catalogo_path.read_text(encoding="utf-8"))["por_prova"]
    avaliacoes = []
    ids = set()
    falhas = []
    escalares = {"n": 0, "delta_theta_max": 0.0, "delta_nota_max": 0.0}
    for nome in FIXTURES:
        path = ROOT / "tests/fixtures" / f"{nome}.jsonl.gz"
        grupos = defaultdict(list)
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for linha in stream:
                caso = json.loads(linha)
                ids.add(caso["case_id"])
                grupos[(caso["ano"], caso["area"], caso["co_prova"],
                        caso["tp_lingua"])].append(caso)
        metricas = {
            "fixture": nome, "sha256": sha256(path), "n": 0,
            "grupos_prova_idioma": len(grupos), "theta_identicos": 0,
            "notas_identicas": 0, "delta_theta_max": 0.0, "delta_nota_max": 0.0,
        }
        for chave, casos in grupos.items():
            ano, area, prova, lingua = chave
            respostas = [c["respostas"] for c in casos]
            itens_ref, u_ref = anterior.preparar_respostas_batch(
                ano, area, prova, respostas, lingua,
            )
            itens, u = atual.preparar_respostas_batch(ano, area, prova, respostas, lingua)
            # repr também permite comparar os NaN de TP_LINGUA nos itens comuns.
            if ([repr(asdict(i)) for i in itens_ref] != [repr(asdict(i)) for i in itens]
                    or not np.array_equal(u_ref, u)):
                falhas.append(f"{nome}/{chave}: itens ou respostas binárias divergentes")
            theta_ref = anterior.estimar_theta_eap_batch(u_ref, itens_ref)
            theta = atual.estimar_theta_eap_batch(u, itens)
            modelo = catalogo[f"{ano},{area},{prova}"]["transformacao"]
            notas_ref, notas = aplicar_modelo(theta_ref, modelo), aplicar_modelo(theta, modelo)
            dt, dn = np.abs(theta - theta_ref), np.abs(notas - notas_ref)
            metricas["n"] += len(casos)
            metricas["theta_identicos"] += int(np.count_nonzero(theta == theta_ref))
            metricas["notas_identicas"] += int(np.count_nonzero(notas == notas_ref))
            metricas["delta_theta_max"] = max(metricas["delta_theta_max"], float(dt.max()))
            metricas["delta_nota_max"] = max(metricas["delta_nota_max"], float(dn.max()))
            if (not np.all(np.isfinite(theta)) or not np.all(np.isfinite(notas))
                    or not np.allclose(theta, theta_ref, rtol=0, atol=2e-14)
                    or not np.allclose(notas, notas_ref, rtol=0, atol=1e-9)):
                falhas.append(f"{nome}/{chave}: resultado numérico divergente")
            if nome == "validation_holdout":
                ordenados = sorted(range(len(casos)), key=lambda i: casos[i]["nota_oficial"])
                for i in sorted({ordenados[0], ordenados[-1]}):
                    t_ref = anterior.estimar_theta_eap(u_ref[i], itens_ref)
                    t = atual.estimar_theta_eap(u[i], itens)
                    n_ref = anterior.transformar_escala(t_ref, ano, area, prova)
                    n = atual.transformar_escala(t, ano, area, prova)
                    escalares["n"] += 1
                    escalares["delta_theta_max"] = max(escalares["delta_theta_max"], abs(t - t_ref))
                    escalares["delta_nota_max"] = max(escalares["delta_nota_max"], abs(n - n_ref))
                    if not np.isclose(t, t_ref, rtol=0, atol=2e-14) or not np.isclose(n, n_ref, rtol=0, atol=1e-9):
                        falhas.append(f"{nome}/{chave}: referência escalar divergente")
        avaliacoes.append(metricas)
        print(f"{nome}: {metricas['n']} casos; delta nota máximo {metricas['delta_nota_max']:.3g}", flush=True)
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "versao": __version__, "referencia_git": commit,
        "motor_referencia_sha256": hashlib.sha256(fonte.encode()).hexdigest(),
        "motor_atual_sha256": sha256(ROOT / "src/tri_enem/calculador.py"),
        "catalogo_sha256": sha256(catalogo_path),
        "ambiente": {"python": platform.python_version(), "numpy": np.__version__},
        "tolerancias_absolutas": {"theta": 2e-14, "nota": 1e-9},
        "avaliacoes": avaliacoes, "casos_distintos": len(ids),
        "comparacao_escalar": escalares, "falhas": falhas,
    }


def gerar_markdown(relatorio: dict) -> str:
    linhas = [
        "# Equivalência numérica do motor otimizado", "",
        f"- Versão: `{relatorio['versao']}`",
        f"- Referência Git: `{relatorio['referencia_git']}`",
        f"- Execução (UTC): `{relatorio['gerado_em']}`",
        f"- Resultado: **{'APROVADO' if not relatorio['falhas'] else 'REPROVADO'}**", "",
        "Os motores usam as mesmas fixtures, parâmetros, reconstruções e transformações.",
        "A comparação verifica os itens carregados, as respostas binárias, theta e nota.", "",
        "| Fixture | Avaliações | Grupos prova/idioma | Notas idênticas | Maior diferença em pontos |",
        "|---|---:|---:|---:|---:|",
    ]
    for m in relatorio["avaliacoes"]:
        linhas.append(f"| {m['fixture']} | {m['n']} | {m['grupos_prova_idioma']} | {m['notas_identicas']} | {m['delta_nota_max']:.12g} |")
    escalar = relatorio["comparacao_escalar"]
    linhas += [
        "", f"Casos distintos: **{relatorio['casos_distintos']}**. A fixture de erro médio",
        "inclui casos exploratórios já presentes no holdout; as avaliações não são todas independentes.", "",
        f"A referência escalar foi comparada nos extremos de nota oficial de cada grupo do holdout: **{escalar['n']} casos**.",
        f"Diferença máxima: theta **{escalar['delta_theta_max']:.12g}**, nota **{escalar['delta_nota_max']:.12g} pontos**.", "",
        "Tolerâncias absolutas: theta `2e-14`; nota `1e-9` ponto. A validação das notas",
        "contra o INEP é feita pelos quatro validadores oficiais do projeto; este relatório mede",
        "a equivalência com o motor anterior, sem alterar modelos ou criar nova evidência de calibração.", "",
        "Reproduzir a comparação:", "", "```bash",
        f"OPENBLAS_NUM_THREADS=1 python tools/validar_otimizacao.py --referencia {relatorio['referencia_git']}",
        "```", "",
    ]
    if relatorio["falhas"]:
        linhas += ["Falhas:", "", *[f"- {f}" for f in relatorio["falhas"]], ""]
    return "\n".join(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--referencia", default="HEAD", help="Commit do motor anterior.")
    parser.add_argument("--saida", type=Path, default=ROOT / "resultados/investigacao/otimizacao_6_1_0")
    args = parser.parse_args()
    relatorio = validar(args.referencia)
    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "equivalencia.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.saida / "equivalencia.md").write_text(gerar_markdown(relatorio), encoding="utf-8")
    return int(bool(relatorio["falhas"]))


if __name__ == "__main__":
    raise SystemExit(main())
