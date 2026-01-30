#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera exemplos por CO_PROVA a partir dos microdados (modo rapido).

Objetivo: 1 exemplo por codigo de prova, parando assim que cobrir todos os codigos
presentes no mapeamento e nos microdados.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

import _utils

_utils.add_src_to_path()

from tri_enem import MapeadorProvas


def _is_valid(value: Optional[str]) -> bool:
    if value is None:
        return False
    value = value.strip()
    if not value:
        return False
    if value.lower() in {"na", "nan", "null"}:
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


def _arquivo_por_ano(ano_dir: Path) -> Optional[Path]:
    ano = ano_dir.name
    resultados = ano_dir / f"RESULTADOS_{ano}.csv"
    microdados = ano_dir / f"MICRODADOS_ENEM_{ano}.csv"
    if resultados.exists():
        return resultados
    if microdados.exists():
        return microdados
    return None


def _carregar_codigos_presentes(microdados_limpos_dir: Path) -> Set[str]:
    if _utils.CACHE_CODIGOS_PATH.exists():
        try:
            codigos = _utils.carregar_codigos_presentes(_utils.CACHE_CODIGOS_PATH, "codigo")
            if codigos:
                print(f"Cache de codigos carregado: {len(codigos)}", flush=True)
                return codigos
        except Exception as exc:
            print(f"Aviso: cache invalido ({exc}). Recriando...", flush=True)

    codigos = set()
    progress_interval = 100000
    print("Construindo cache de codigos presentes (microdados_limpos)...", flush=True)

    for ano_dir in sorted([p for p in microdados_limpos_dir.iterdir() if p.is_dir() and p.name.isdigit()],
                          key=lambda p: p.name):
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
            colunas = [f"CO_PROVA_{area}" for area in ["CN", "CH", "LC", "MT"]]
            if not all(col in idx for col in colunas):
                continue

            linhas = 0
            for row in reader:
                linhas += 1
                if len(row) < len(header):
                    continue

                for area in ["CN", "CH", "LC", "MT"]:
                    co_prova = row[idx[f"CO_PROVA_{area}"]].strip()
                    if _is_valid(co_prova):
                        # Normalizar para int (alguns vêm como '1003.0')
                        try:
                            co_prova_norm = str(int(float(co_prova)))
                            codigos.add(co_prova_norm)
                        except ValueError:
                            pass

                if linhas % progress_interval == 0:
                    print(f"  {ano_dir.name}: {linhas} linhas lidas", flush=True)

        print(f"  {ano_dir.name}: codigos acumulados={len(codigos)}", flush=True)

    _utils.CACHE_CODIGOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Converter para int (alguns vêm como '1003.0')
    codigos_int = sorted(int(float(x)) for x in codigos)
    payload = {"agrupar_por": "codigo", "codigos": codigos_int}
    _utils.CACHE_CODIGOS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
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
) -> None:
    mapeador = MapeadorProvas()
    resultados = []
    contagens: Dict[str, int] = {}
    total_registros = 0
    total_codigos = set()
    progress_interval = 50000
    completos = set()
    alvos = _carregar_alvos(microdados_limpos_dir)
    total_alvos = len(alvos)
    parar = False

    print(f"Alvos considerados: {total_alvos}", flush=True)
    if total_alvos == 0:
        print("Nada a fazer. Verifique microdados_limpos e mapeamento.", flush=True)
        return

    for ano_dir in sorted([p for p in microdados_dir.iterdir() if p.is_dir() and p.name.isdigit()],
                          key=lambda p: p.name):
        arquivo = _arquivo_por_ano(ano_dir)
        if not arquivo:
            continue

        print(f"\nAno {ano_dir.name}: usando {arquivo.name}", flush=True)
        with open(arquivo, "r", encoding="latin-1", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            try:
                header = next(reader)
            except StopIteration:
                continue

            idx = _col_idx(header)
            id_col = "NU_SEQUENCIAL" if "NU_SEQUENCIAL" in idx else ("NU_INSCRICAO" if "NU_INSCRICAO" in idx else None)
            if not id_col:
                continue

            needed = [
                id_col,
                "CO_PROVA_CN", "CO_PROVA_CH", "CO_PROVA_LC", "CO_PROVA_MT",
                "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
                "TX_RESPOSTAS_CN", "TX_RESPOSTAS_CH", "TX_RESPOSTAS_LC", "TX_RESPOSTAS_MT",
            ]
            if not all(c in idx for c in needed):
                continue

            linhas_lidas = 0
            registros_ano = 0
            codigos_ano = set()
            for row in reader:
                linhas_lidas += 1

                if len(row) < len(header):
                    continue

                for area in ["CN", "CH", "LC", "MT"]:
                    co_prova = row[idx[f"CO_PROVA_{area}"]].strip()
                    if not _is_valid(co_prova) or co_prova not in alvos:
                        continue

                    if contagens.get(co_prova, 0) >= 1:
                        continue

                    if f"TP_PRESENCA_{area}" in idx:
                        if row[idx[f"TP_PRESENCA_{area}"]].strip() != "1":
                            continue

                    nota = row[idx[f"NU_NOTA_{area}"]]
                    respostas = row[idx[f"TX_RESPOSTAS_{area}"]]
                    if not _is_valid(nota) or not _is_valid(respostas):
                        continue

                    registro = {
                        "ano": int(ano_dir.name),
                        "id_col": id_col,
                        "id": row[idx[id_col]],
                        "area": area,
                        "tp_lingua": row[idx["TP_LINGUA"]] if "TP_LINGUA" in idx else None,
                        "co_prova": co_prova,
                        "cor_prova": _cor_por_codigo(mapeador, co_prova),
                        "nota_oficial": nota,
                        "respostas": respostas,
                        "len_respostas": len(respostas),
                        "arquivo": arquivo.name,
                    }
                    resultados.append(registro)
                    contagens[co_prova] = 1
                    registros_ano += 1
                    total_registros += 1
                    try:
                        cod = int(co_prova)
                        codigos_ano.add(cod)
                        total_codigos.add(cod)
                    except ValueError:
                        pass

                    completos.add(co_prova)
                    if len(completos) == total_alvos:
                        print("Alvos completos. Encerrando leitura.", flush=True)
                        parar = True
                        break

                if linhas_lidas % progress_interval == 0:
                    print(f"  Linhas lidas: {linhas_lidas} | registros: {registros_ano}", flush=True)

                if parar:
                    break

            print(
                f"  Concluido ano {ano_dir.name}: linhas={linhas_lidas}, registros={registros_ano}, "
                f"CO_PROVA unicos={len(codigos_ano)}",
                flush=True,
            )

            if parar:
                break

        if parar:
            break

    print(
        f"\nResumo: registros={total_registros}, CO_PROVA unicos={len(total_codigos)}",
        flush=True,
    )
    faltantes = set(alvos) - set(completos)
    if faltantes:
        faltantes_str = ", ".join(sorted(faltantes)[:20])
        print(f"Codigos faltantes (primeiros): {faltantes_str}", flush=True)

    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerar exemplos rapidos por CO_PROVA.")
    parser.add_argument("--microdados-dir", default="microdados", help="Diretorio com microdados por ano")
    parser.add_argument("--microdados-limpos", default="microdados_limpos", help="Diretorio microdados_limpos")
    parser.add_argument("--saida", default=str(_utils.EXEMPLOS_PATH), help="Arquivo de saida (JSON)")
    args = parser.parse_args()

    microdados_dir = Path(args.microdados_dir)
    microdados_limpos = Path(args.microdados_limpos)
    saida = Path(args.saida)

    if not microdados_dir.exists():
        raise SystemExit(f"Diretorio nao encontrado: {microdados_dir}")
    if not microdados_limpos.exists():
        raise SystemExit(f"Diretorio nao encontrado: {microdados_limpos}")
    if not _utils.MAPEAMENTO_PATH.exists():
        raise SystemExit(f"Arquivo nao encontrado: {_utils.MAPEAMENTO_PATH}")

    gerar_exemplos(
        microdados_dir,
        microdados_limpos,
        saida,
    )
    print(f"Arquivo gerado: {saida}")


if __name__ == "__main__":
    main()
