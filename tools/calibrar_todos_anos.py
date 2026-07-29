#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atalho compatível para a recalibração v4 de todos os anos.

O script antigo mantinha um segundo algoritmo, pulava 2017 e escrevia
resultados parciais no esquema v2. Este atalho agora delega ao único pipeline
reproduzível, que só publica catálogo, holdout, manifesto e relatório após
validar o conjunto completo.

Exemplo:
    python tools/calibrar_todos_anos.py \
      --microdados-dir /caminho/MICRODADOS_ENEM --workers 3
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microdados-dir", required=True, type=Path)
    parser.add_argument("--itens-path", type=Path)
    parser.add_argument("--chunk-size", type=int, default=250_000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--cap-por-estrato", type=int, default=160)
    parser.add_argument(
        "--nao-publicar",
        action="store_true",
        help="Executa o diagnóstico completo sem substituir artefatos.",
    )
    args = parser.parse_args()

    comando = [
        sys.executable,
        str(ROOT / "tools" / "recalibrar_validacao.py"),
        "--microdados-dir",
        str(args.microdados_dir),
        "--chunk-size",
        str(args.chunk_size),
        "--workers",
        str(args.workers),
        "--cap-por-estrato",
        str(args.cap_por_estrato),
    ]
    if args.itens_path:
        comando.extend(["--itens-path", str(args.itens_path)])
    if args.nao_publicar:
        comando.append("--nao-publicar")
    print("[aviso] Atalho legado: delegando ao pipeline de calibração v4.", flush=True)
    return subprocess.run(comando, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
