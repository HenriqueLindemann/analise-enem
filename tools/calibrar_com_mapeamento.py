#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibilidade para diagnósticos de calibração por ano/prova.

Desde a versão 4, toda calibração usa o mesmo amostrador estratificado, os
mesmos modelos e os mesmos critérios de validação do pipeline oficial. Este
atalho nunca publica artefatos: ele delega a ``recalibrar_validacao.py`` com
``--nao-publicar``.

Exemplo:
    python tools/calibrar_com_mapeamento.py \
      --microdados-dir /caminho/MICRODADOS_ENEM --anos 2023
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
    parser.add_argument("--anos", nargs="+", type=int, default=list(range(2009, 2026)))
    parser.add_argument("--chunk-size", type=int, default=250_000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--cap-por-estrato", type=int, default=160)
    args = parser.parse_args()

    comando = [
        sys.executable,
        str(ROOT / "tools" / "recalibrar_validacao.py"),
        "--microdados-dir",
        str(args.microdados_dir),
        "--anos",
        *(str(ano) for ano in args.anos),
        "--chunk-size",
        str(args.chunk_size),
        "--workers",
        str(args.workers),
        "--cap-por-estrato",
        str(args.cap_por_estrato),
        "--sem-hash-fontes",
        "--nao-publicar",
    ]
    if args.itens_path:
        comando.extend(["--itens-path", str(args.itens_path)])
    print(
        "[aviso] Atalho legado: executando o calibrador v4 sem publicar.",
        flush=True,
    )
    return subprocess.run(comando, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
