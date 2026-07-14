#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera exemplos por CO_PROVA a partir dos microdados brutos do INEP.

Objetivo: até N_MAX exemplos por código de prova, cobrindo todos os códigos
presentes tanto no mapeamento quanto nos microdados_limpos.

Suporta duas estruturas de diretório:
  - Padrão do projeto  : <dir>/YYYY/MICRODADOS_ENEM_YYYY.csv
  - Padrão de download do INEP : <dir>/microdados_enem_YYYY/DADOS/RESULTADOS_YYYY.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

import _utils

_utils.add_src_to_path()

from tri_enem import MapeadorProvas

# Número máximo de exemplos por CO_PROVA (aumentar dá MAE mais estável)
N_MAX_POR_PROVA = 10


def _is_valid(value: Optional[str]) -> bool:
    if value is None:
        return False
    value = value.strip()
    if not value or value.lower() in {"na", "nan", "null"}:
        return False
    return True


def _col_idx(header: List[str]) -> Dict[str, int]:
    return {name: i for i, name in enumerate(header)}


def _cor_por_codigo(mapeador: MapeadorProvas, codigo: str) -> Optional[str]:
    if not codigo:
        return None
    try:
        info = mapeador.descobrir_prova_por_codigo(int(codigo))
        return info.cor if info else None
    except Exception:
        return None


def _extrair_ano_do_nome(nome: str) -> Optional[int]:
    """Extrai o ano de nomes como '2024', 'microdados_enem_2024', etc."""
    if nome.isdigit():
        return int(nome)
    m = re.search(r'(\d{4})$', nome)
    return int(m.group(1)) if m else None


def _arquivo_por_ano(ano_dir: Path, ano: int) -> Optional[Path]:
    """
    Localiza o arquivo de microdados em diferentes estruturas de diretório.

    Prioridade:
      1. DADOS/RESULTADOS_YYYY.csv       (INEP: download recente)
      2. DADOS/MICRODADOS_ENEM_YYYY.csv  (INEP: download antigo)
      3. RESULTADOS_YYYY.csv             (projeto: microdados/YYYY/)
      4. MICRODADOS_ENEM_YYYY.csv        (projeto: microdados/YYYY/)
    """
    candidatos = [
        ano_dir / "DADOS" / f"RESULTADOS_{ano}.csv",
        ano_dir / "DADOS" / f"MICRODADOS_ENEM_{ano}.csv",
        ano_dir / f"RESULTADOS_{ano}.csv",
        ano_dir / f"MICRODADOS_ENEM_{ano}.csv",
    ]
    for c in candidatos:
        if c.exists():
            return c
    return None


def _listar_anos_disponiveis(microdados_dir: Path) -> List[tuple[int, Path]]:
    """Retorna lista ordenada de (ano, diretório) encontrados em microdados_dir."""
    anos = []
    for p in microdados_dir.iterdir():
        if not p.is_dir():
            continue
        ano = _extrair_ano_do_nome(p.name)
        if ano and 2009 <= ano <= 2030:
            anos.append((ano, p))
    return sorted(anos)


def _carregar_codigos_presentes(microdados_limpos_dir: Path) -> Set[str]:
    if _utils.CACHE_CODIGOS_PATH.exists():
        try:
            codigos = _utils.carregar_codigos_presentes(_utils.CACHE_CODIGOS_PATH, "codigo")
            if codigos:
                print(f"Cache de codigos carregado: {len(codigos)}", flush=True)
                return codigos
        except Exception as exc:
            print(f"Aviso: cache invalido ({exc}). Recriando...", flush=True)

    codigos: Set[str] = set()
    progress_interval = 100_000
    print("Construindo cache de codigos presentes (microdados_limpos)...", flush=True)

    for ano_dir in sorted(
        [p for p in microdados_limpos_dir.iterdir() if p.is_dir() and p.name.isdigit()],
        key=lambda p: p.name,
    ):
        arquivo = ano_dir / f"DADOS_ENEM_{ano_dir.name}.csv"
        if not arquivo.exists():
            continue

        with open(arquivo, "r", encoding="latin-1", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            try:
                header = next(reader)
            except StopIteration:
                continue

            idx = _col_idx(header)
            colunas = [f"CO_PROVA_{a}" for a in ["CN", "CH", "LC", "MT"]]
            if not all(col in idx for col in colunas):
                continue

            linhas = 0
            for row in reader:
                linhas += 1
                if len(row) < len(header):
                    continue
                for area in ["CN", "CH", "LC", "MT"]:
                    co = row[idx[f"CO_PROVA_{area}"]].strip()
                    if _is_valid(co):
                        try:
                            codigos.add(str(int(float(co))))
                        except ValueError:
                            pass
                if linhas % progress_interval == 0:
                    print(f"  {ano_dir.name}: {linhas} linhas lidas", flush=True)

        print(f"  {ano_dir.name}: codigos acumulados={len(codigos)}", flush=True)

    _utils.CACHE_CODIGOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    codigos_int = sorted(int(float(x)) for x in codigos)
    payload = {"agrupar_por": "codigo", "codigos": codigos_int}
    _utils.CACHE_CODIGOS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Cache salvo em {_utils.CACHE_CODIGOS_PATH} ({len(codigos)} codigos)", flush=True)
    return codigos


def _carregar_alvos(microdados_limpos_dir: Path) -> Set[str]:
    alvos_mapeamento = _utils.listar_chaves_mapeamento(_utils.MAPEAMENTO_PATH, "codigo")
    if not alvos_mapeamento:
        print("Aviso: mapeamento vazio. Usando codigos presentes.", flush=True)
        return _carregar_codigos_presentes(microdados_limpos_dir)

    presentes = _carregar_codigos_presentes(microdados_limpos_dir)
    if presentes:
        alvos = alvos_mapeamento.intersection(presentes)
        faltantes = alvos_mapeamento.difference(presentes)
        print(
            f"Mapeamento: {len(alvos_mapeamento)} | presentes: {len(presentes)} | "
            f"alvos: {len(alvos)} | faltantes: {len(faltantes)}",
            flush=True,
        )
        return alvos
    return alvos_mapeamento


def gerar_exemplos(
    microdados_dir: Path,
    microdados_limpos_dir: Path,
    saida: Path,
    n_max: int = N_MAX_POR_PROVA,
) -> None:
    mapeador = MapeadorProvas()
    resultados: List[dict] = []
    contagens: Dict[str, int] = {}   # co_prova -> número de exemplos já coletados
    total_registros = 0
    total_codigos: Set[int] = set()
    completos: Set[str] = set()
    alvos = _carregar_alvos(microdados_limpos_dir)
    total_alvos = len(alvos)
    parar = False

    print(f"Alvos considerados: {total_alvos} (max {n_max} exemplos por prova)", flush=True)
    if total_alvos == 0:
        print("Nada a fazer. Verifique microdados_limpos e mapeamento.", flush=True)
        return

    for ano, ano_dir in _listar_anos_disponiveis(microdados_dir):
        arquivo = _arquivo_por_ano(ano_dir, ano)
        if not arquivo:
            print(f"Ano {ano}: nenhum arquivo encontrado em {ano_dir}", flush=True)
            continue

        print(f"\nAno {ano}: usando {arquivo.relative_to(microdados_dir)}", flush=True)

        with open(arquivo, "r", encoding="latin-1", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            try:
                header = next(reader)
            except StopIteration:
                continue

            idx = _col_idx(header)
            id_col = next(
                (c for c in ("NU_SEQUENCIAL", "NU_INSCRICAO") if c in idx), None
            )
            if not id_col:
                print(f"  Sem coluna de ID, pulando.", flush=True)
                continue

            needed = [
                id_col,
                "CO_PROVA_CN", "CO_PROVA_CH", "CO_PROVA_LC", "CO_PROVA_MT",
                "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
                "TX_RESPOSTAS_CN", "TX_RESPOSTAS_CH", "TX_RESPOSTAS_LC", "TX_RESPOSTAS_MT",
            ]
            if not all(c in idx for c in needed):
                print(f"  Colunas insuficientes ({[c for c in needed if c not in idx]}), pulando.", flush=True)
                continue

            linhas_lidas = 0
            registros_ano = 0
            codigos_ano: Set[int] = set()

            for row in reader:
                linhas_lidas += 1
                if len(row) < len(header):
                    continue

                for area in ["CN", "CH", "LC", "MT"]:
                    co_prova = row[idx[f"CO_PROVA_{area}"]].strip()
                    if not _is_valid(co_prova) or co_prova not in alvos:
                        continue

                    # Já atingiu o limite para esta prova?
                    if contagens.get(co_prova, 0) >= n_max:
                        continue

                    if f"TP_PRESENCA_{area}" in idx:
                        if row[idx[f"TP_PRESENCA_{area}"]].strip() != "1":
                            continue

                    nota     = row[idx[f"NU_NOTA_{area}"]]
                    respostas = row[idx[f"TX_RESPOSTAS_{area}"]]
                    if not _is_valid(nota) or not _is_valid(respostas):
                        continue

                    registro = {
                        "ano":          ano,
                        "id_col":       id_col,
                        "id":           row[idx[id_col]],
                        "area":         area,
                        "tp_lingua":    row[idx["TP_LINGUA"]] if "TP_LINGUA" in idx else None,
                        "co_prova":     co_prova,
                        "cor_prova":    _cor_por_codigo(mapeador, co_prova),
                        "nota_oficial": nota,
                        "respostas":    respostas,
                        "len_respostas": len(respostas),
                        "arquivo":      arquivo.name,
                    }
                    resultados.append(registro)
                    # FIX: incrementar contador em vez de resetar para 1
                    contagens[co_prova] = contagens.get(co_prova, 0) + 1
                    registros_ano += 1
                    total_registros += 1
                    try:
                        codigos_ano.add(int(co_prova))
                        total_codigos.add(int(co_prova))
                    except ValueError:
                        pass

                    if contagens[co_prova] >= n_max:
                        completos.add(co_prova)

                if len(completos) == total_alvos:
                    print("Todos os alvos cobertos. Encerrando leitura.", flush=True)
                    parar = True
                    break

                if linhas_lidas % 50_000 == 0:
                    print(
                        f"  {linhas_lidas} linhas | {registros_ano} registros | "
                        f"{len(completos)}/{total_alvos} provas completas",
                        flush=True,
                    )

            print(
                f"  Ano {ano}: linhas={linhas_lidas}, registros={registros_ano}, "
                f"CO_PROVA unicos={len(codigos_ano)}",
                flush=True,
            )

        if parar:
            break

    faltantes = set(alvos) - completos
    print(
        f"\nResumo: {total_registros} registros | {len(total_codigos)} CO_PROVAs únicos | "
        f"{len(faltantes)} provas sem exemplos",
        flush=True,
    )
    if faltantes:
        print(
            "  Faltantes (primeiros 20): "
            + ", ".join(sorted(faltantes)[:20]),
            flush=True,
        )

    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"Arquivo gerado: {saida}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerar exemplos por CO_PROVA a partir dos microdados.")
    parser.add_argument(
        "--microdados-dir", default="microdados",
        help="Diretório com microdados por ano (padrão do projeto ou download do INEP)",
    )
    parser.add_argument(
        "--microdados-limpos", default="microdados_limpos",
        help="Diretório microdados_limpos",
    )
    parser.add_argument(
        "--saida", default=str(_utils.EXEMPLOS_PATH),
        help="Arquivo de saída (JSON)",
    )
    parser.add_argument(
        "--n-max", type=int, default=N_MAX_POR_PROVA,
        help=f"Máximo de exemplos por CO_PROVA (padrão: {N_MAX_POR_PROVA})",
    )
    args = parser.parse_args()

    microdados_dir   = Path(args.microdados_dir)
    microdados_limpos = Path(args.microdados_limpos)
    saida            = Path(args.saida)

    if not microdados_dir.exists():
        raise SystemExit(f"Diretório não encontrado: {microdados_dir}")
    if not microdados_limpos.exists():
        raise SystemExit(f"Diretório não encontrado: {microdados_limpos}")
    if not _utils.MAPEAMENTO_PATH.exists():
        raise SystemExit(f"Arquivo não encontrado: {_utils.MAPEAMENTO_PATH}")

    gerar_exemplos(microdados_dir, microdados_limpos, saida, args.n_max)


if __name__ == "__main__":
    main()
