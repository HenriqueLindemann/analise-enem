#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Completo de Validação do Calculador TRI

Este script executa o fluxo completo de validação:
1. Gera exemplos de microdados (1 por CO_PROVA)
2. Valida as notas calculadas contra as oficiais
3. Gera relatório de provas problemáticas

Uso:
    python tests/run_full_validation.py

Requisitos:
    - Diretório microdados/ com arquivos originais
    - Diretório microdados_limpos/ com dados processados
    - Arquivo src/tri_enem/mapeamento_provas.yaml

Saídas:
    - tests/fixtures/exemplos_microdados.json
    - tests/fixtures/codigos_presentes.json (cache)
    - tests/provas_problematicas.md
    - Relatório no console com métricas de validação
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar tests/ ao path para imports
TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR))

import _utils

_utils.add_src_to_path()


def verificar_requisitos() -> bool:
    """Verifica se os diretórios necessários existem."""
    requisitos = [
        (_utils.ROOT / "microdados", "Diretório de microdados originais"),
        (_utils.ROOT / "microdados_limpos", "Diretório de microdados processados"),
        (_utils.MAPEAMENTO_PATH, "Mapeamento de provas"),
    ]
    
    ok = True
    for path, descricao in requisitos:
        if path.exists():
            print(f"  ✅ {descricao}: {path}")
        else:
            print(f"  ❌ {descricao} não encontrado: {path}")
            ok = False
    
    return ok


def run_step(name: str, script: str, args: list[str]) -> bool:
    """Executa um passo do pipeline."""
    print(f"\n{'='*70}")
    print(f"PASSO: {name}")
    print(f"{'='*70}")
    
    cmd = [sys.executable, str(TESTS_DIR / script)] + args
    print(f"Comando: {' '.join(cmd)}\n")
    
    start = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    elapsed = time.time() - start
    
    if result.returncode == 0:
        print(f"\n✅ {name} concluído em {elapsed:.1f}s")
        return True
    else:
        print(f"\n❌ {name} falhou (código {result.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo de validação do calculador TRI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--microdados-dir",
        default="microdados",
        help="Diretório com microdados originais (default: microdados)"
    )
    parser.add_argument(
        "--microdados-limpos",
        default="microdados_limpos", 
        help="Diretório com microdados processados (default: microdados_limpos)"
    )
    parser.add_argument(
        "--skip-gerar",
        action="store_true",
        help="Pular geração de exemplos (usar existentes)"
    )
    parser.add_argument(
        "--limite-dif",
        type=float,
        default=_utils.LIMITE_DIF_PADRAO,
        help=f"Limite de diferença para marcar como problemático (default: {_utils.LIMITE_DIF_PADRAO})"
    )
    args = parser.parse_args()
    
    print("="*70)
    print("PIPELINE DE VALIDAÇÃO COMPLETA")
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Verificar requisitos
    print("\n📋 Verificando requisitos...")
    if not verificar_requisitos():
        print("\n❌ Requisitos não atendidos. Abortando.")
        return 1
    
    # Criar diretório fixtures se necessário
    fixtures_dir = TESTS_DIR / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    exemplos_path = fixtures_dir / "exemplos_microdados.json"
    
    # Passo 1: Gerar exemplos
    if args.skip_gerar and exemplos_path.exists():
        print(f"\n⏭️  Pulando geração de exemplos (--skip-gerar)")
        print(f"   Usando: {exemplos_path}")
    else:
        ok = run_step(
            "Gerar Exemplos por CO_PROVA",
            "gerar_exemplos_microdados.py",
            [
                "--microdados-dir", args.microdados_dir,
                "--microdados-limpos", args.microdados_limpos,
                "--saida", str(exemplos_path),
            ]
        )
        if not ok:
            return 1
    
    # Verificar se exemplos foram gerados
    if not exemplos_path.exists():
        print(f"\n❌ Arquivo de exemplos não encontrado: {exemplos_path}")
        return 1
    
    # Passo 2: Validar exemplos
    ok = run_step(
        "Validar Exemplos contra Microdados",
        "validar_exemplos_microdados.py",
        [
            "--exemplos", str(exemplos_path),
            "--microdados-limpos", args.microdados_limpos,
        ]
    )
    if not ok:
        print("⚠️  Validação teve problemas, mas continuando...")
    
    # Passo 3: Gerar relatório de provas problemáticas
    relatorio_path = TESTS_DIR / "provas_problematicas.md"
    ok = run_step(
        "Gerar Relatório de Provas Problemáticas",
        "gerar_provas_problematicas.py",
        [
            "--exemplos", str(exemplos_path),
            "--microdados-limpos", args.microdados_limpos,
            "--saida", str(relatorio_path),
            "--limite-dif", str(args.limite_dif),
        ]
    )
    if not ok:
        print("⚠️  Geração de relatório teve problemas")
    
    # Resumo final
    print("\n" + "="*70)
    print("RESUMO FINAL")
    print("="*70)
    
    outputs = [
        (exemplos_path, "Exemplos gerados"),
        (fixtures_dir / "codigos_presentes.json", "Cache de códigos"),
        (relatorio_path, "Relatório de provas problemáticas"),
    ]
    
    for path, desc in outputs:
        if path.exists():
            size = path.stat().st_size
            size_str = f"{size:,} bytes" if size < 1024*1024 else f"{size/1024/1024:.1f} MB"
            print(f"  ✅ {desc}: {path.name} ({size_str})")
        else:
            print(f"  ❌ {desc}: não gerado")
    
    print(f"\nConcluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
