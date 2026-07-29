#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Executa geração de itens, recalibração real e todas as validações v4."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def executar(nome: str, comando: list[str]) -> None:
    print(f"\n{'=' * 72}\n{nome}\n{'=' * 72}", flush=True)
    inicio = time.monotonic()
    resultado = subprocess.run(comando, cwd=ROOT)
    if resultado.returncode:
        raise RuntimeError(
            f"{nome} falhou com código {resultado.returncode}: "
            + " ".join(comando)
        )
    print(f"[ok] {nome}: {time.monotonic() - inicio:.1f}s", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microdados-dir", required=True, type=Path)
    parser.add_argument("--chunk-size", type=int, default=250_000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--itens-path", type=Path)
    parser.add_argument(
        "--sem-gerar-itens",
        action="store_true",
        help="Usa os itens já empacotados sem regenerá-los.",
    )
    parser.add_argument(
        "--somente-validar",
        action="store_true",
        help="Não recalibra; valida os artefatos já publicados e roda pytest.",
    )
    args = parser.parse_args()

    if not args.microdados_dir.is_dir():
        parser.error(f"diretório inexistente: {args.microdados_dir}")
    if not args.somente_validar and not args.sem_gerar_itens:
        executar(
            "Gerar e validar os dados de itens",
            [
                sys.executable,
                str(ROOT / "tools" / "gerar_dados_itens.py"),
                "--microdados-dir",
                str(args.microdados_dir),
            ],
        )

    if not args.somente_validar:
        recalibrar = [
            sys.executable,
            str(ROOT / "tools" / "recalibrar_validacao.py"),
            "--microdados-dir",
            str(args.microdados_dir),
            "--chunk-size",
            str(args.chunk_size),
            "--workers",
            str(args.workers),
        ]
        if args.itens_path:
            recalibrar.extend(["--itens-path", str(args.itens_path)])
        executar("Recalibrar catálogo e publicar holdout", recalibrar)
    executar(
        "Recalcular o holdout publicado",
        [sys.executable, str(ROOT / "tests" / "validar_holdout.py")],
    )
    executar(
        "Regenerar golden tests determinísticos",
        [sys.executable, str(ROOT / "tests" / "fixtures" / "gerar_golden_notas.py")],
    )
    executar(
        "Executar a suíte pytest",
        [sys.executable, "-m", "pytest", "-q"],
    )
    print("\n[ok] Pipeline v4 concluído sem publicação parcial.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\n[falha] {exc}", file=sys.stderr)
        raise SystemExit(1)
