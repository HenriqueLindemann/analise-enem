#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Recalibra todas as provas e publica um catálogo v3 validado.

O script faz uma passagem pelos microdados oficiais, retém deterministicamente
uma amostra estratificada por prova/faixa/idioma, ajusta modelos sem reutilizar
o holdout e só substitui os artefatos versionados após validar as invariantes.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import heapq
import json
import math
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Sequence, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tri_enem import CalculadorTRI, MapeadorProvas  # noqa: E402
from tri_enem.calibracao_modelos import (  # noqa: E402
    ROTULOS_FAIXAS,
    ajustar_linear,
    classificar_validacao,
    faixa_nota,
    metricas_modelo,
    reajustar_modelo,
    selecionar_modelo,
)
from tri_enem.precisao import classificar_perfil_validacao  # noqa: E402

AREAS = ("CN", "CH", "LC", "MT")
CAP_ESTRATO = 160
SCHEMA_VERSION = 3
ALGORITHM_VERSION = "stratified-v3.1"
HASH_KEY = "enem-tri-v3"
FALLBACK_AREA = {
    "MT": (129.63, 500.0),
    "CN": (113.13, 501.16),
    "CH": (112.32, 501.47),
    "LC": (108.08, 500.0),
}


@dataclass(frozen=True)
class Caso:
    ano: int
    area: str
    co_prova: int
    tp_lingua: int | None
    nota_oficial: float
    respostas: str
    faixa: str
    case_id: str
    rank: int

    @property
    def prova_key(self) -> str:
        return f"{self.ano},{self.area},{self.co_prova}"

    @property
    def estrato(self) -> Tuple[str, int | None, str]:
        return self.prova_key, self.tp_lingua, self.faixa

    def publico(self, split: str) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "ano": self.ano,
            "area": self.area,
            "co_prova": self.co_prova,
            "tp_lingua": self.tp_lingua,
            "nota_oficial": self.nota_oficial,
            "respostas": self.respostas,
            "faixa": self.faixa,
            "split": split,
        }


class AmostraEstratificada:
    """Mantém os menores hashes por estrato e extremos por prova/idioma."""

    def __init__(self, cap: int = CAP_ESTRATO):
        self.cap = cap
        self.heaps: Dict[Tuple[str, int | None, str], list] = defaultdict(list)
        self.contagens: Dict[Tuple[str, int | None, str], int] = defaultdict(int)
        self.extremos: Dict[Tuple[str, int | None], Dict[str, Any]] = {}

    def registrar_contagem(
        self, estrato: Tuple[str, int | None, str], quantidade: int
    ) -> None:
        self.contagens[estrato] += int(quantidade)

    def adicionar(self, caso: Caso) -> None:
        estrato = caso.estrato
        heap = self.heaps[estrato]
        item = (-caso.rank, caso.case_id, caso)
        if len(heap) < self.cap:
            heapq.heappush(heap, item)
        elif caso.rank < -heap[0][0]:
            heapq.heapreplace(heap, item)

        chave = (caso.prova_key, caso.tp_lingua)
        estado = self.extremos.setdefault(
            chave,
            {"min": math.inf, "max": -math.inf, "min_casos": [], "max_casos": []},
        )
        self._atualizar_extremo(estado, "min", caso, menor=True)
        self._atualizar_extremo(estado, "max", caso, menor=False)

    @staticmethod
    def _atualizar_extremo(
        estado: Dict[str, Any], nome: str, caso: Caso, menor: bool
    ) -> None:
        valor = caso.nota_oficial
        atual = estado[nome]
        melhora = valor < atual if menor else valor > atual
        if melhora:
            estado[nome] = valor
            estado[f"{nome}_casos"] = [caso]
        elif valor == atual:
            casos = estado[f"{nome}_casos"]
            casos.append(caso)
            casos.sort(key=lambda item: item.rank)
            del casos[2:]

    def casos(self) -> Dict[Tuple[str, int | None, str], List[Caso]]:
        resultado = {
            chave: sorted((item[2] for item in heap), key=lambda c: c.rank)
            for chave, heap in self.heaps.items()
        }
        # Extremos são acrescentados mesmo quando não ficaram entre os menores
        # hashes do respectivo estrato.
        for (prova_key, lingua), estado in self.extremos.items():
            for nome in ("min_casos", "max_casos"):
                for caso in estado[nome]:
                    chave = (prova_key, lingua, caso.faixa)
                    existentes = {item.case_id for item in resultado.setdefault(chave, [])}
                    if caso.case_id not in existentes:
                        resultado[chave].append(caso)
                        resultado[chave].sort(key=lambda item: item.rank)
        # Os extremos substituem casos de hash maior; nunca aumentam o limite
        # de retenção do estrato.
        extremos_ids = {
            caso.case_id
            for estado in self.extremos.values()
            for nome in ("min_casos", "max_casos")
            for caso in estado[nome]
        }
        for chave, casos in resultado.items():
            unicos = {caso.case_id: caso for caso in casos}
            forcados = sorted(
                (caso for caso in unicos.values() if caso.case_id in extremos_ids),
                key=lambda caso: caso.rank,
            )
            restantes = sorted(
                (caso for caso in unicos.values() if caso.case_id not in extremos_ids),
                key=lambda caso: caso.rank,
            )
            resultado[chave] = sorted(
                forcados + restantes[:max(0, self.cap - len(forcados))],
                key=lambda caso: caso.rank,
            )
        return resultado


def localizar_microdados(base: Path, ano: int) -> Path:
    candidatos = (
        base / f"microdados_enem_{ano}" / "DADOS" / f"RESULTADOS_{ano}.csv",
        base / f"microdados_enem_{ano}" / "DADOS" / f"MICRODADOS_ENEM_{ano}.csv",
        base / str(ano) / f"RESULTADOS_{ano}.csv",
        base / str(ano) / f"MICRODADOS_ENEM_{ano}.csv",
    )
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    raise FileNotFoundError(f"Microdados oficiais de {ano} não encontrados em {base}")


def _id_coluna(colunas: Iterable[str]) -> str | None:
    existentes = set(colunas)
    for candidato in (
        "NU_INSCRICAO",
        "NU_SEQUENCIAL",
        "CO_INSCRICAO",
        "IN_INSCRICAO",
    ):
        if candidato in existentes:
            return candidato
    return None


def _hashes_estaveis(
    ano: int,
    area: str,
    prova: pd.Series,
    lingua: pd.Series,
    identificador: pd.Series,
) -> np.ndarray:
    frame = pd.DataFrame({
        "chave": HASH_KEY,
        "ano": ano,
        "area": area,
        "prova": prova.astype("Int64").astype(str),
        "lingua": lingua.astype("Int64").astype(str),
        "id": identificador.astype(str),
    })
    return pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype=np.uint64)


def _case_id(rank: int, ano: int, area: str, prova: int) -> str:
    bruto = f"{HASH_KEY}|{ano}|{area}|{prova}|{int(rank)}".encode()
    return hashlib.sha256(bruto).hexdigest()[:24]


def _provas_mapeadas(mapeador: MapeadorProvas, anos: Sequence[int]) -> Dict[tuple, Any]:
    resultado = {}
    for ano in anos:
        for prova in mapeador.listar_todas_provas(ano):
            resultado[(prova.ano, prova.area, prova.codigo)] = prova
    return resultado


def _disponibilidade_itens(
    calc: CalculadorTRI, provas: Dict[tuple, Any]
) -> Tuple[set[tuple], Dict[str, str]]:
    disponiveis: set[tuple] = set()
    problemas: Dict[str, str] = {}
    for (ano, area, codigo), _ in provas.items():
        linguas = (0, 1) if area == "LC" and ano != 2009 else (None,)
        erros = []
        for lingua in linguas:
            try:
                itens = calc.carregar_itens(ano, area, codigo, lingua)
                if len(itens) != 45:
                    raise ValueError(f"{len(itens)} itens em vez de 45")
                disponiveis.add((ano, area, codigo, lingua))
            except (FileNotFoundError, KeyError, ValueError) as exc:
                erros.append(str(exc))
        if not any(item[:3] == (ano, area, codigo) for item in disponiveis):
            problemas[f"{ano},{area},{codigo}"] = "; ".join(erros) or "sem itens"
    return disponiveis, problemas


def _linhas_validas(
    chunk: pd.DataFrame,
    ano: int,
    area: str,
    id_col: str | None,
) -> pd.DataFrame:
    pres = f"TP_PRESENCA_{area}"
    prova = f"CO_PROVA_{area}"
    nota = f"NU_NOTA_{area}"
    resp = f"TX_RESPOSTAS_{area}"
    obrigatorias = (pres, prova, nota, resp)
    if not all(col in chunk.columns for col in obrigatorias):
        return pd.DataFrame()

    trabalho = pd.DataFrame({
        "presenca": pd.to_numeric(chunk[pres], errors="coerce"),
        "prova": pd.to_numeric(chunk[prova], errors="coerce"),
        "nota": pd.to_numeric(chunk[nota], errors="coerce"),
        "respostas": chunk[resp],
    })
    if area == "LC" and ano != 2009 and "TP_LINGUA" in chunk.columns:
        trabalho["lingua"] = pd.to_numeric(chunk["TP_LINGUA"], errors="coerce")
    else:
        trabalho["lingua"] = pd.Series(pd.NA, index=chunk.index, dtype="Int64")
    trabalho["identificador"] = (
        chunk[id_col].astype(str) if id_col else chunk.index.astype(str)
    )
    valido = (
        trabalho["presenca"].eq(1)
        & trabalho["prova"].notna()
        & trabalho["nota"].notna()
        & np.isfinite(trabalho["nota"])
        & trabalho["nota"].gt(0)
        & trabalho["respostas"].notna()
    )
    if area == "LC" and ano != 2009:
        valido &= trabalho["lingua"].isin([0, 1])
    respostas = trabalho["respostas"].astype("string").str.upper()
    valida_45 = respostas.str.fullmatch(r"[A-E.*]{45}", na=False)
    if area == "LC" and ano != 2009:
        normal_ingles = respostas.str.slice(0, 5) + respostas.str.slice(10)
        normal_espanhol = respostas.str.slice(5, 50)
        valida_50_ingles = (
            respostas.str.len().eq(50)
            & respostas.str.slice(5, 10).eq("99999")
            & normal_ingles.str.fullmatch(r"[A-E.*]{45}", na=False)
        )
        valida_50_espanhol = (
            respostas.str.len().eq(50)
            & respostas.str.slice(0, 5).eq("99999")
            & normal_espanhol.str.fullmatch(r"[A-E.*]{45}", na=False)
        )
        valido &= (
            valida_45
            | (trabalho["lingua"].eq(0) & valida_50_ingles)
            | (trabalho["lingua"].eq(1) & valida_50_espanhol)
        )
    else:
        valido &= valida_45
    return trabalho[valido].copy()


def amostrar_microdados(
    base: Path,
    anos: Sequence[int],
    provas: Dict[tuple, Any],
    itens_disponiveis: set[tuple],
    chunk_size: int,
    cap: int,
) -> Tuple[AmostraEstratificada, Dict[str, Any], List[Path]]:
    amostra = AmostraEstratificada(cap)
    diagnostico: Dict[str, Any] = {
        "codigos_nao_mapeados": defaultdict(int),
        "participantes_mapeados": defaultdict(int),
    }
    fontes = []

    for ano in anos:
        caminho = localizar_microdados(base, ano)
        fontes.append(caminho)
        header = pd.read_csv(caminho, encoding="latin1", sep=";", nrows=0)
        id_col = _id_coluna(header.columns)
        usecols = []
        for area in AREAS:
            usecols.extend([
                f"TP_PRESENCA_{area}",
                f"CO_PROVA_{area}",
                f"NU_NOTA_{area}",
                f"TX_RESPOSTAS_{area}",
            ])
        usecols.extend(["TP_LINGUA", id_col])
        usecols = list(dict.fromkeys(col for col in usecols if col in header.columns))

        print(f"{ano}: amostrando {caminho.name}", flush=True)
        offset = 0
        for numero_chunk, chunk in enumerate(pd.read_csv(
            caminho,
            encoding="latin1",
            sep=";",
            usecols=usecols,
            chunksize=chunk_size,
            low_memory=False,
        ), start=1):
            chunk.index = np.arange(offset, offset + len(chunk))
            offset += len(chunk)
            for area in AREAS:
                dados = _linhas_validas(chunk, ano, area, id_col)
                if dados.empty:
                    continue
                dados["prova"] = dados["prova"].astype(int)
                dados["lingua_int"] = (
                    dados["lingua"].astype("Int64")
                    if area == "LC" and ano != 2009
                    else pd.Series(pd.NA, index=dados.index, dtype="Int64")
                )
                mapeada = dados["prova"].map(
                    lambda codigo: (ano, area, int(codigo)) in provas
                )
                for codigo, n in dados.loc[~mapeada, "prova"].value_counts().items():
                    diagnostico["codigos_nao_mapeados"][f"{ano},{area},{int(codigo)}"] += int(n)
                dados = dados[mapeada]
                if dados.empty:
                    continue

                if area == "LC" and ano != 2009:
                    mascara_itens = np.zeros(len(dados), dtype=bool)
                    for lingua in (0, 1):
                        codigos = {
                            codigo
                            for a, ar, codigo, li in itens_disponiveis
                            if a == ano and ar == area and li == lingua
                        }
                        mascara_itens |= (
                            dados["lingua_int"].eq(lingua)
                            & dados["prova"].isin(codigos)
                        ).to_numpy()
                else:
                    codigos = {
                        codigo
                        for a, ar, codigo, li in itens_disponiveis
                        if a == ano and ar == area and li is None
                    }
                    mascara_itens = dados["prova"].isin(codigos).to_numpy()
                dados = dados[mascara_itens]
                if dados.empty:
                    continue
                ranks = _hashes_estaveis(
                    ano,
                    area,
                    dados["prova"],
                    dados["lingua_int"],
                    dados["identificador"],
                )
                dados["rank"] = ranks
                dados["faixa"] = dados["nota"].map(faixa_nota)
                dados["case_id"] = [
                    _case_id(rank, ano, area, int(prova))
                    for rank, prova in zip(ranks, dados["prova"])
                ]

                # Reduz cada chunk antes de criar objetos Python.
                grupos = ["prova", "lingua_int", "faixa"]
                for _, grupo in dados.groupby(grupos, dropna=False, observed=True):
                    lingua_grupo = (
                        int(grupo["lingua_int"].iloc[0])
                        if pd.notna(grupo["lingua_int"].iloc[0])
                        else None
                    )
                    prova_grupo = int(grupo["prova"].iloc[0])
                    faixa_grupo = str(grupo["faixa"].iloc[0])
                    prova_key = f"{ano},{area},{prova_grupo}"
                    amostra.registrar_contagem(
                        (prova_key, lingua_grupo, faixa_grupo), len(grupo)
                    )
                    diagnostico["participantes_mapeados"][prova_key] += len(grupo)
                    candidatos = pd.concat([
                        grupo.nsmallest(cap, "rank"),
                        grupo.nsmallest(2, "nota"),
                        grupo.nlargest(2, "nota"),
                    ]).drop_duplicates("case_id")
                    for row in candidatos.itertuples():
                        lingua = (
                            int(row.lingua_int)
                            if pd.notna(row.lingua_int)
                            else None
                        )
                        caso = Caso(
                            ano=ano,
                            area=area,
                            co_prova=int(row.prova),
                            tp_lingua=lingua,
                            nota_oficial=float(row.nota),
                            respostas=str(row.respostas),
                            faixa=str(row.faixa),
                            case_id=str(row.case_id),
                            rank=int(row.rank),
                        )
                        amostra.adicionar(caso)
            if numero_chunk % 5 == 0:
                print(
                    f"  {numero_chunk * chunk_size:,} linhas; "
                    f"{len(amostra.heaps):,} estratos",
                    flush=True,
                )

    diagnostico["codigos_nao_mapeados"] = dict(
        sorted(diagnostico["codigos_nao_mapeados"].items())
    )
    diagnostico["participantes_mapeados"] = dict(
        sorted(diagnostico["participantes_mapeados"].items())
    )
    return amostra, diagnostico, fontes


def _amostrar_ano_tarefa(argumentos):
    return amostrar_microdados(*argumentos)


def amostrar_microdados_paralelo(
    base: Path,
    anos: Sequence[int],
    provas: Dict[tuple, Any],
    itens_disponiveis: set[tuple],
    chunk_size: int,
    cap: int,
    workers: int,
) -> Tuple[AmostraEstratificada, Dict[str, Any], List[Path]]:
    """Processa anos independentes em paralelo e funde amostras determinísticas."""
    if workers <= 1 or len(anos) <= 1:
        return amostrar_microdados(
            base, anos, provas, itens_disponiveis, chunk_size, cap
        )
    tarefas = [
        (base, [ano], provas, itens_disponiveis, chunk_size, cap)
        for ano in anos
    ]
    resultado = AmostraEstratificada(cap)
    diagnostico: Dict[str, Dict[str, int]] = {
        "codigos_nao_mapeados": defaultdict(int),
        "participantes_mapeados": defaultdict(int),
    }
    fontes: List[Path] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for parcial, diag_parcial, fontes_parciais in executor.map(
            _amostrar_ano_tarefa, tarefas
        ):
            for estrato, quantidade in parcial.contagens.items():
                resultado.registrar_contagem(estrato, quantidade)
            for casos in parcial.casos().values():
                for caso in casos:
                    resultado.adicionar(caso)
            for nome in diagnostico:
                for chave, quantidade in diag_parcial[nome].items():
                    diagnostico[nome][chave] += int(quantidade)
            fontes.extend(fontes_parciais)
    return resultado, {
        nome: dict(sorted(valores.items()))
        for nome, valores in diagnostico.items()
    }, sorted(fontes)


def _tamanhos_split(n: int) -> Tuple[int, int, int]:
    if n >= CAP_ESTRATO:
        return 100, 30, 30
    if n == 1:
        return 0, 0, 1
    if n == 2:
        return 1, 0, 1
    treino = max(1, int(math.floor(n * 0.60)))
    selecao = max(1, int(math.floor(n * 0.20)))
    holdout = n - treino - selecao
    if holdout < 1:
        treino -= 1
        holdout = 1
    return treino, selecao, holdout


def dividir_amostra(
    amostra: AmostraEstratificada,
) -> Dict[str, Dict[str, List[Caso]]]:
    por_prova: Dict[str, Dict[str, List[Caso]]] = defaultdict(
        lambda: {"treino": [], "selecao": [], "holdout": []}
    )
    extremos_roles: Dict[str, str] = {}
    for estado in amostra.extremos.values():
        for nome in ("min_casos", "max_casos"):
            casos = estado[nome]
            if not casos:
                continue
            extremos_roles[casos[0].case_id] = "holdout"
            if len(casos) > 1:
                extremos_roles[casos[1].case_id] = "treino"

    for _, casos in sorted(amostra.casos().items(), key=lambda item: str(item[0])):
        unicos = {caso.case_id: caso for caso in casos}
        casos = sorted(unicos.values(), key=lambda item: item.rank)
        n_treino, n_selecao, _ = _tamanhos_split(min(len(casos), CAP_ESTRATO))
        forcas = {"treino": [], "selecao": [], "holdout": []}
        restantes = []
        for caso in casos:
            papel = extremos_roles.get(caso.case_id)
            if papel:
                forcas[papel].append(caso)
            else:
                restantes.append(caso)
        metas = {"treino": n_treino, "selecao": n_selecao}
        for papel in ("treino", "selecao"):
            faltam = max(0, metas[papel] - len(forcas[papel]))
            forcas[papel].extend(restantes[:faltam])
            del restantes[:faltam]
        forcas["holdout"].extend(restantes)
        for papel, lista in forcas.items():
            por_prova[casos[0].prova_key][papel].extend(lista)
    return por_prova


def _calcular_thetas(
    calc: CalculadorTRI, casos: Sequence[Caso]
) -> Tuple[np.ndarray, np.ndarray, List[str], List[Caso]]:
    thetas: List[float] = []
    notas: List[float] = []
    faixas: List[str] = []
    validos: List[Caso] = []
    grupos: Dict[Tuple[int, str, int, int | None], List[Caso]] = defaultdict(list)
    for caso in casos:
        grupos[(caso.ano, caso.area, caso.co_prova, caso.tp_lingua)].append(caso)

    for (ano, area, prova, lingua), grupo in grupos.items():
        respostas_validas = []
        casos_validos = []
        itens = None
        for caso in grupo:
            try:
                itens, binaria, _ = calc._preparar_calculo(
                    ano, area, prova, caso.respostas, lingua
                )
            except (TypeError, ValueError, FileNotFoundError):
                continue
            respostas_validas.append(binaria)
            casos_validos.append(caso)
        if not casos_validos or itens is None:
            continue
        theta_grupo = calc.estimar_theta_eap_batch(respostas_validas, itens)
        thetas.extend(theta_grupo.tolist())
        notas.extend(caso.nota_oficial for caso in casos_validos)
        faixas.extend(caso.faixa for caso in casos_validos)
        validos.extend(casos_validos)
    return np.asarray(thetas), np.asarray(notas), faixas, validos


def _transformacao_publica(modelo: Dict[str, Any]) -> Dict[str, Any]:
    permitidas = {
        "tipo", "slope", "intercept", "theta_knots", "score_knots",
        "n_nos_solicitados",
    }
    return {key: value for key, value in modelo.items() if key in permitidas}


def calibrar_catalogo(
    calc: CalculadorTRI,
    provas: Dict[tuple, Any],
    itens_problemas: Dict[str, str],
    amostra: AmostraEstratificada,
    splits: Dict[str, Dict[str, List[Caso]]],
    timestamp: str,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    entradas: Dict[str, Any] = {}
    holdout_publico: List[Dict[str, Any]] = []
    faixas_por_prova: Dict[str, set[str]] = defaultdict(set)
    for (prova_key, _, faixa), n in amostra.contagens.items():
        if n:
            faixas_por_prova[prova_key].add(faixa)

    modelos_para_area: Dict[Tuple[int, str], List[Tuple[float, float]]] = defaultdict(list)
    pendentes_fallback: List[str] = []
    dados_fallback: Dict[
        str, Tuple[np.ndarray, np.ndarray, List[str], List[Caso]]
    ] = {}

    for (ano, area, codigo), prova in sorted(provas.items()):
        key = f"{ano},{area},{codigo}"
        base = {
            "ano": ano,
            "area": area,
            "prova": codigo,
            "tipo_aplicacao": prova.tipo_aplicacao,
            "cor": prova.cor,
            "slope": None,
            "intercept": None,
            "transformacao": None,
            "calibracao": {"n_treino": 0, "n_selecao": 0},
            "validacao": None,
            "qualidade": {
                "status": "nao_calibrado",
                "motivo": "sem_amostra",
                "validado_em": timestamp,
            },
        }
        if key in itens_problemas:
            base["qualidade"] = {
                "status": "sem_itens",
                "motivo": itens_problemas[key],
                "validado_em": timestamp,
            }
            entradas[key] = base
            continue

        prova_splits = splits.get(key)
        if not prova_splits:
            base["qualidade"] = {
                "status": "sem_participantes",
                "motivo": "sem_participantes_validos",
                "validado_em": timestamp,
            }
            entradas[key] = base
            pendentes_fallback.append(key)
            dados_fallback[key] = (
                np.asarray([]),
                np.asarray([]),
                [],
                [],
            )
            continue

        x_train, y_train, _, casos_train = _calcular_thetas(
            calc, prova_splits["treino"]
        )
        x_sel, y_sel, _, casos_sel = _calcular_thetas(
            calc, prova_splits["selecao"]
        )
        x_test, y_test, faixas_test, casos_test = _calcular_thetas(
            calc, prova_splits["holdout"]
        )
        base["calibracao"] = {
            "n_treino": len(casos_train),
            "n_selecao": len(casos_sel),
        }
        if len(x_train) < 10 or len(x_sel) < 1:
            base["qualidade"] = {
                "status": "nao_calibrado",
                "motivo": "amostra_calibracao_insuficiente",
                "validado_em": timestamp,
            }
            entradas[key] = base
            pendentes_fallback.append(key)
            dados_fallback[key] = (x_test, y_test, faixas_test, casos_test)
            continue

        selecionado = selecionar_modelo(x_train, y_train, x_sel, y_sel)
        modelo = reajustar_modelo(
            selecionado["modelo"],
            np.concatenate([x_train, x_sel]),
            np.concatenate([y_train, y_sel]),
        )
        transformacao = _transformacao_publica(modelo)
        base["slope"] = float(modelo["slope"])
        base["intercept"] = float(modelo["intercept"])
        base["transformacao"] = transformacao
        base["calibracao"]["modelo_selecionado"] = transformacao["tipo"]
        base["calibracao"]["metricas_selecao"] = selecionado["metricas_selecao"]
        modelos_para_area[(ano, area)].append(
            (float(modelo["slope"]), float(modelo["intercept"]))
        )

        metricas = None
        if len(x_test):
            metricas = metricas_modelo(x_test, y_test, modelo, faixas_test)
            metricas["faixas_existentes"] = sorted(faixas_por_prova[key])
            for caso in casos_test:
                holdout_publico.append(caso.publico("holdout"))
        status, motivo = classificar_validacao(
            metricas, sorted(faixas_por_prova[key])
        )
        base["validacao"] = metricas
        base["qualidade"] = {
            "status": status,
            "motivo": motivo,
            "validado_em": timestamp,
        }
        entradas[key] = base
        print(
            f"{key}: {status}; modelo={transformacao['tipo']}; "
            f"n={metricas['n'] if metricas else 0}; "
            f"max={metricas['erro_maximo'] if metricas else float('nan'):.3f}",
            flush=True,
        )

    por_area = {}
    for (ano, area), valores in sorted(modelos_para_area.items()):
        por_area[f"{ano},{area}"] = {
            "slope": float(np.median([v[0] for v in valores])),
            "intercept": float(np.median([v[1] for v in valores])),
            "n_provas": len(valores),
        }

    # Materializa o fallback na entrada da prova. Assim toda prova calculável
    # declara o modelo efetivamente usado, sem depender de uma fonte de status
    # paralela.
    for key in pendentes_fallback:
        ano, area, _ = key.split(",")
        modelo_area = por_area.get(f"{ano},{area}")
        if modelo_area is None:
            slope, intercept = FALLBACK_AREA[area]
            modelo_area = {"slope": slope, "intercept": intercept}
            origem = "area_padrao"
        else:
            origem = "area_ano"
        modelo = {
            "tipo": "linear",
            "slope": float(modelo_area["slope"]),
            "intercept": float(modelo_area["intercept"]),
        }
        entradas[key]["slope"] = modelo["slope"]
        entradas[key]["intercept"] = modelo["intercept"]
        entradas[key]["transformacao"] = {**modelo, "origem": origem}
        entradas[key]["qualidade"]["fallback"] = origem
        x_test, y_test, faixas_test, casos_test = dados_fallback[key]
        if len(x_test):
            metricas = metricas_modelo(
                x_test, y_test, {**modelo, "complexidade": 2}, faixas_test
            )
            metricas["faixas_existentes"] = sorted(faixas_por_prova[key])
            entradas[key]["validacao"] = metricas
            for caso in casos_test:
                holdout_publico.append(caso.publico("holdout"))
            status, motivo = classificar_validacao(
                metricas, sorted(faixas_por_prova[key])
            )
            entradas[key]["qualidade"].update({
                "status": status,
                "motivo": motivo,
            })

    metadata: Dict[str, Any] = {
        "versao": "3.0",
        "ultima_calibracao": timestamp,
    }
    for area in AREAS:
        valores = [
            item for key, item in por_area.items() if key.endswith(f",{area}")
        ]
        if valores:
            metadata[area] = {
                "slope_medio": float(np.median([v["slope"] for v in valores])),
                "intercept_medio": float(
                    np.median([v["intercept"] for v in valores])
                ),
                "n_anos": len(valores),
            }
    return {
        "schema_version": SCHEMA_VERSION,
        "por_prova": entradas,
        "por_area": por_area,
        "metadata": metadata,
    }, sorted(
        holdout_publico,
        key=lambda item: (
            item["ano"], item["area"], item["co_prova"], item["case_id"]
        ),
    )


def _hash_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(8 * 1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def criar_manifesto(
    catalogo: Dict[str, Any],
    holdout: Sequence[Dict[str, Any]],
    fontes: Sequence[Path],
    amostra: AmostraEstratificada,
    splits: Dict[str, Dict[str, List[Caso]]],
    diagnostico: Dict[str, Any],
    timestamp: str,
    hash_sources: bool,
) -> Dict[str, Any]:
    status = defaultdict(int)
    for info in catalogo["por_prova"].values():
        status[info["qualidade"]["status"]] += 1
    contagens_split: Dict[Tuple[str, int | None, str], Dict[str, int]] = (
        defaultdict(lambda: {"treino": 0, "selecao": 0, "holdout": 0})
    )
    for prova_key, por_split in splits.items():
        for split, casos in por_split.items():
            for caso in casos:
                contagens_split[(prova_key, caso.tp_lingua, caso.faixa)][split] += 1
    estratos = []
    for (prova_key, lingua, faixa), disponiveis in sorted(
        amostra.contagens.items(), key=lambda item: str(item[0])
    ):
        quantidades = contagens_split[(prova_key, lingua, faixa)]
        estratos.append({
            "prova": prova_key,
            "tp_lingua": lingua,
            "faixa": faixa,
            "disponiveis": int(disponiveis),
            **quantidades,
        })
    manifesto_itens = (
        ROOT / "src" / "tri_enem" / "data" / "itens" / "manifest.json"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "generated_at": timestamp,
        "git_commit": _git_commit(),
        "hash_key": HASH_KEY,
        "seed": HASH_KEY,
        "score_bands": list(ROTULOS_FAIXAS),
        "item_data_manifest_sha256": (
            _hash_arquivo(manifesto_itens) if manifesto_itens.exists() else None
        ),
        "sampling": {
            "cap_per_proof_language_band": amostra.cap,
            "target_split": {"treino": 100, "selecao": 30, "holdout": 30},
        },
        "sources": [
            {
                "file": path.name,
                "size": path.stat().st_size,
                "sha256": _hash_arquivo(path) if hash_sources else None,
            }
            for path in fontes
        ],
        "coverage": {
            "mapped_proofs": len(catalogo["por_prova"]),
            "holdout_cases": len(holdout),
            "status": dict(sorted(status.items())),
            "strata": len(amostra.contagens),
        },
        "strata_counts": estratos,
        "diagnostics": diagnostico,
    }


def validar_artefatos(
    catalogo: Dict[str, Any],
    holdout: Sequence[Dict[str, Any]],
    provas: Dict[tuple, Any],
) -> None:
    def validar_finitude(valor: Any, caminho: str) -> None:
        if isinstance(valor, float) and not math.isfinite(valor):
            raise RuntimeError(f"Valor não finito em {caminho}: {valor!r}")
        if isinstance(valor, dict):
            for chave, item in valor.items():
                validar_finitude(item, f"{caminho}.{chave}")
        elif isinstance(valor, (list, tuple)):
            for indice, item in enumerate(valor):
                validar_finitude(item, f"{caminho}[{indice}]")

    validar_finitude(catalogo, "catalogo")
    esperadas = {f"{ano},{area},{codigo}" for ano, area, codigo in provas}
    encontradas = set(catalogo.get("por_prova", {}))
    if esperadas != encontradas:
        raise RuntimeError(
            f"Cobertura de catálogo divergente: faltam={sorted(esperadas-encontradas)[:10]}, "
            f"sobram={sorted(encontradas-esperadas)[:10]}"
        )
    if len(encontradas) != len(catalogo["por_prova"]):
        raise RuntimeError("Provas duplicadas no catálogo")
    for key, info in catalogo["por_prova"].items():
        qualidade = info.get("qualidade") or {}
        validacao = info.get("validacao") or {}
        if qualidade.get("status") == "ok":
            if validacao.get("erro_maximo", math.inf) > 2.0 + 1e-12:
                raise RuntimeError(f"{key}: status ok com erro acima de 2 pontos")
            if validacao.get("n", 0) < 30:
                raise RuntimeError(f"{key}: status ok com holdout insuficiente")
    ids = set()
    for caso in holdout:
        if not math.isfinite(float(caso["nota_oficial"])) or float(
            caso["nota_oficial"]
        ) <= 0:
            raise RuntimeError(f"Nota oficial inválida no holdout: {caso}")
        if caso["case_id"] in ids:
            raise RuntimeError(f"Caso duplicado no holdout: {caso['case_id']}")
        ids.add(caso["case_id"])


def gerar_relatorio(catalogo: Dict[str, Any], manifesto: Dict[str, Any]) -> str:
    nomes_areas = {
        "CH": "Ciências Humanas",
        "CN": "Ciências da Natureza",
        "LC": "Linguagens",
        "MT": "Matemática",
    }
    nomes_aplicacoes = {
        "1a_aplicacao": "1ª aplicação",
        "digital": "Prova digital",
        "reaplicacao": "Reaplicação",
        "reaplicacao_2": "2ª reaplicação",
        "segunda_oportunidade": "Segunda oportunidade",
    }
    nomes_perfis = {
        "calibracao_verificada": "Boa calibração verificada",
        "boa_na_maioria_com_excecoes": (
            "Estimativa confiável na maioria dos casos, com exceções"
        ),
        "estimativa": "Estimativa com variação relevante",
        "sem_validacao": "Sem validação suficiente",
    }

    def rotulo_prova(
        chave: str, info: Dict[str, Any], incluir_ano: bool = True
    ) -> str:
        ano, area, codigo = chave.split(",")
        partes = []
        if incluir_ano:
            partes.append(f"ENEM {ano}")
        partes.append(nomes_areas.get(area, area))
        aplicacao = str(info.get("tipo_aplicacao") or "").strip()
        if aplicacao:
            partes.append(
                nomes_aplicacoes.get(
                    aplicacao, aplicacao.replace("_", " ").capitalize()
                )
            )
        cor = str(info.get("cor") or "").strip()
        if cor:
            partes.append(cor.replace("_", " ").capitalize())
        return " · ".join(partes) + f" (prova `{codigo}`)"

    def linhas_lista_provas(chaves: Sequence[str]) -> List[str]:
        por_ano: Dict[str, List[str]] = defaultdict(list)
        for chave in chaves:
            ano = chave.split(",")[0]
            por_ano[ano].append(
                rotulo_prova(
                    chave, catalogo["por_prova"][chave], incluir_ano=False
                )
            )
        return [
            f"- **ENEM {ano}:** " + "; ".join(provas_ano)
            for ano, provas_ano in sorted(por_ano.items())
        ] or ["Nenhuma."]

    status_ordenados = (
        "ok", "aviso_leve", "aviso_forte", "erro_alto",
        "nao_calibrado", "sem_participantes", "sem_itens",
    )
    contagem = defaultdict(int)
    contagem_perfis = defaultdict(int)
    metricas = []
    grupos_ano: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    grupos_area: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    provas_por_status: Dict[str, List[str]] = defaultdict(list)
    provas_por_perfil: Dict[str, List[str]] = defaultdict(list)
    for info in catalogo["por_prova"].values():
        status = info["qualidade"]["status"]
        validacao = info.get("validacao") or {}
        contagem[status] += 1
        perfil = classificar_perfil_validacao(
            status,
            validacao.get("erro_p95"),
            validacao.get("acima_2"),
            validacao.get("n"),
        )
        contagem_perfis[perfil] += 1
        if validacao:
            metricas.append(validacao)
    for chave, info in catalogo["por_prova"].items():
        ano, area, _ = chave.split(",")
        status = info["qualidade"]["status"]
        validacao = info.get("validacao") or {}
        perfil = classificar_perfil_validacao(
            status,
            validacao.get("erro_p95"),
            validacao.get("acima_2"),
            validacao.get("n"),
        )
        grupos_ano[ano].append((chave, info))
        grupos_area[area].append((chave, info))
        provas_por_status[status].append(chave)
        provas_por_perfil[perfil].append(chave)
    linhas = [
        "# Validação das notas TRI",
        "",
        "Relatório gerado automaticamente a partir do holdout estratificado de "
        "participantes reais dos microdados públicos do INEP.",
        "",
        f"- Provas catalogadas: **{len(catalogo['por_prova'])}**",
        f"- Casos no holdout: **{manifesto['coverage']['holdout_cases']}**",
        f"- Geração: `{manifesto['generated_at']}`",
        "",
        "## Como interpretar este relatório",
        "",
        "- **Boa calibração verificada:** a prova foi conferida com casos reais "
        "e atendeu integralmente ao critério estrito do projeto.",
        "- **Estimativa confiável na maioria dos casos, com exceções:** o erro "
        "típico foi baixo, mas casos atípicos impedem a garantia estrita.",
        "- **Estimativa com variação relevante:** as diferenças não ficaram "
        "limitadas a poucas exceções; a nota exige mais cautela.",
        "- **Sem validação suficiente:** faltam participantes, faixas ou "
        "parâmetros públicos para uma avaliação completa.",
        "",
        "As mensagens da interface usam esses perfis em linguagem simples. As "
        "seções seguintes preservam códigos, métricas e limites para auditoria.",
        "",
        "## Status",
        "",
        "| Status | Provas |",
        "|---|---:|",
    ]
    for status, n in sorted(contagem.items()):
        linhas.append(f"| `{status}` | {n} |")

    def estatisticas_grupo(
        itens: Sequence[Tuple[str, Dict[str, Any]]]
    ) -> Tuple[Counter, int, int, float | None]:
        status_grupo = Counter(
            (info.get("qualidade") or {}).get("status")
            for _, info in itens
        )
        validacoes = [
            info["validacao"] for _, info in itens if info.get("validacao")
        ]
        n_casos = sum(int(m["n"]) for m in validacoes)
        n_ate_2 = n_casos - sum(int(m["acima_2"]) for m in validacoes)
        mae_mediano = (
            float(np.median([m["mae"] for m in validacoes]))
            if validacoes
            else None
        )
        return status_grupo, n_casos, n_ate_2, mae_mediano

    linhas.extend([
        "",
        "## Estatísticas por ano",
        "",
        "| Ano | Provas | ok | leve | forte | alto | não calibrado | sem participantes | sem itens | Casos | Até 2 pts | MAE mediano |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for ano, itens in sorted(grupos_ano.items()):
        s, n_casos, n_ate_2, mae_mediano = estatisticas_grupo(itens)
        percentual = (
            f"{100 * n_ate_2 / n_casos:.2f}%" if n_casos else "—"
        )
        mae_texto = f"{mae_mediano:.3f}" if mae_mediano is not None else "—"
        linhas.append(
            f"| {ano} | {len(itens)} | {s['ok']} | {s['aviso_leve']} | "
            f"{s['aviso_forte']} | {s['erro_alto']} | {s['nao_calibrado']} | "
            f"{s['sem_participantes']} | {s['sem_itens']} | {n_casos} | "
            f"{percentual} | {mae_texto} |"
        )

    linhas.extend([
        "",
        "## Estatísticas por área",
        "",
        "| Área | Provas | ok | leve | forte | alto | não calibrado | sem participantes | sem itens | Casos | Até 2 pts | MAE mediano |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for area, itens in sorted(grupos_area.items()):
        s, n_casos, n_ate_2, mae_mediano = estatisticas_grupo(itens)
        percentual = (
            f"{100 * n_ate_2 / n_casos:.2f}%" if n_casos else "—"
        )
        mae_texto = f"{mae_mediano:.3f}" if mae_mediano is not None else "—"
        linhas.append(
            f"| {area} | {len(itens)} | {s['ok']} | {s['aviso_leve']} | "
            f"{s['aviso_forte']} | {s['erro_alto']} | {s['nao_calibrado']} | "
            f"{s['sem_participantes']} | {s['sem_itens']} | {n_casos} | "
            f"{percentual} | {mae_texto} |"
        )

    if metricas:
        total_casos = sum(int(m["n"]) for m in metricas)
        total_acima_2 = sum(int(m["acima_2"]) for m in metricas)
        dentro_2 = total_casos - total_acima_2
        linhas.extend([
            "",
            "## Métricas agregadas",
            "",
            f"- MAE mediano por prova: **{np.median([m['mae'] for m in metricas]):.2f} pontos**",
            f"- Maior erro observado: **{max(m['erro_maximo'] for m in metricas):.2f} pontos**",
            f"- Casos com erro absoluto de até 2 pontos: "
            f"**{dentro_2}/{total_casos} ({100 * dentro_2 / total_casos:.2f}%)**",
            "",
            "Uma prova só recebe `ok` quando todos os casos do holdout ficam em "
            "até 2 pontos da nota oficial e a cobertura mínima é satisfeita.",
        ])
    linhas.extend([
        "",
        "## Perfis usados na apresentação",
        "",
        "O status permanece estrito e auditável. O perfil serve apenas para "
        "evitar que poucas exceções ocultem o desempenho típico da calibração.",
        "",
        "| Perfil | Provas |",
        "|---|---:|",
    ])
    for perfil, n in sorted(contagem_perfis.items()):
        linhas.append(
            f"| {nomes_perfis.get(perfil, perfil)} (`{perfil}`) | {n} |"
        )

    linhas.extend(["", "## Listas de provas por status"])
    for status in status_ordenados:
        provas_status = sorted(
            provas_por_status.get(status, []),
            key=lambda chave: (
                int(chave.split(",")[0]),
                chave.split(",")[1],
                int(chave.split(",")[2]),
            ),
        )
        linhas.extend([
            "",
            f"### `{status}` ({len(provas_status)})",
            "",
            *linhas_lista_provas(provas_status),
        ])

    linhas.extend(["", "## Listas de provas por perfil de apresentação"])
    for perfil, provas_perfil in sorted(provas_por_perfil.items()):
        provas_perfil = sorted(
            provas_perfil,
            key=lambda chave: (
                int(chave.split(",")[0]),
                chave.split(",")[1],
                int(chave.split(",")[2]),
            ),
        )
        linhas.extend([
            "",
            f"### {nomes_perfis.get(perfil, perfil)} "
            f"(`{perfil}`, {len(provas_perfil)})",
            "",
            *linhas_lista_provas(provas_perfil),
        ])

    linhas.extend([
        "",
        "## Detalhamento por prova",
        "",
        "| Prova | Status | Perfil | Motivo | Modelo | n | MAE | p95 | Máximo | >2 | Faixas |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ])

    def numero(valor: Any, casas: int = 3) -> str:
        return "—" if valor is None else f"{float(valor):.{casas}f}"

    def ordem_prova(item: tuple[str, Any]) -> tuple[int, str, int]:
        ano, area, prova = item[0].split(",")
        return int(ano), area, int(prova)

    for chave, info in sorted(
        catalogo["por_prova"].items(), key=ordem_prova
    ):
        qualidade = info.get("qualidade") or {}
        status = qualidade.get("status", "desconhecido")
        validacao = info.get("validacao") or {}
        transformacao = info.get("transformacao") or {}
        perfil = classificar_perfil_validacao(
            status,
            validacao.get("erro_p95"),
            validacao.get("acima_2"),
            validacao.get("n"),
        )
        faixas_cobertas = set(validacao.get("faixas_cobertas", []))
        faixas_existentes = set(validacao.get("faixas_existentes", []))
        cobertura = (
            f"{len(faixas_cobertas)}/{len(faixas_existentes)}"
            if faixas_existentes
            else "—"
        )
        motivo = str(qualidade.get("motivo") or "—").replace("|", "/")
        linhas.append(
            f"| {rotulo_prova(chave, info)} | `{status}` | "
            f"{nomes_perfis.get(perfil, perfil)} | `{motivo}` | "
            f"`{transformacao.get('tipo') or '—'}` | "
            f"{validacao.get('n', '—')} | {numero(validacao.get('mae'))} | "
            f"{numero(validacao.get('erro_p95'))} | "
            f"{numero(validacao.get('erro_maximo'))} | "
            f"{validacao.get('acima_2', '—')} | {cobertura} |"
        )
    return "\n".join(linhas) + "\n"


def publicar_atomico(
    catalogo: Dict[str, Any],
    holdout: Sequence[Dict[str, Any]],
    manifesto: Dict[str, Any],
) -> None:
    destinos = {
        "catalogo": ROOT / "src" / "tri_enem" / "coeficientes_data.json",
        "holdout": ROOT / "tests" / "fixtures" / "validation_holdout.jsonl.gz",
        "manifesto": ROOT / "tests" / "fixtures" / "validation_manifest.json",
        "relatorio": ROOT / "docs" / "VALIDATION_REPORT.md",
    }
    with tempfile.TemporaryDirectory(dir=ROOT) as temporario:
        temp = Path(temporario)
        arquivos = {
            "catalogo": temp / "coeficientes_data.json",
            "holdout": temp / "validation_holdout.jsonl.gz",
            "manifesto": temp / "validation_manifest.json",
            "relatorio": temp / "VALIDATION_REPORT.md",
        }
        arquivos["catalogo"].write_text(
            json.dumps(
                catalogo, ensure_ascii=False, indent=2, allow_nan=False
            ) + "\n",
            encoding="utf-8",
        )
        with gzip.open(arquivos["holdout"], "wt", encoding="utf-8") as saida:
            for caso in holdout:
                saida.write(
                    json.dumps(caso, ensure_ascii=False, allow_nan=False) + "\n"
                )
        arquivos["manifesto"].write_text(
            json.dumps(
                manifesto, ensure_ascii=False, indent=2, allow_nan=False
            ) + "\n",
            encoding="utf-8",
        )
        arquivos["relatorio"].write_text(
            gerar_relatorio(catalogo, manifesto), encoding="utf-8"
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tests" / "validar_holdout.py"),
                "--catalogo",
                str(arquivos["catalogo"]),
                "--holdout",
                str(arquivos["holdout"]),
                "--manifesto",
                str(arquivos["manifesto"]),
                "--relatorio",
                str(arquivos["relatorio"]),
            ],
            cwd=ROOT,
            check=True,
        )
        for nome, destino in destinos.items():
            destino.parent.mkdir(parents=True, exist_ok=True)
            os.replace(arquivos[nome], destino)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--microdados-dir", required=True, type=Path)
    parser.add_argument("--itens-path", type=Path)
    parser.add_argument("--anos", nargs="+", type=int, default=list(range(2009, 2026)))
    parser.add_argument("--chunk-size", type=int, default=250_000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--cap-por-estrato", type=int, default=CAP_ESTRATO)
    parser.add_argument("--sem-hash-fontes", action="store_true")
    parser.add_argument("--nao-publicar", action="store_true")
    args = parser.parse_args()
    if args.sem_hash_fontes and not args.nao_publicar:
        parser.error("--sem-hash-fontes só pode ser usado com --nao-publicar")
    if args.workers < 1:
        parser.error("--workers deve ser pelo menos 1")
    if not args.nao_publicar and set(args.anos) != set(range(2009, 2026)):
        parser.error("publicação parcial é proibida; use --nao-publicar com --anos")

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    calc = CalculadorTRI(str(args.itens_path) if args.itens_path else None)
    mapeador = MapeadorProvas()
    provas = _provas_mapeadas(mapeador, args.anos)
    itens_disponiveis, itens_problemas = _disponibilidade_itens(calc, provas)
    print(
        f"{len(provas)} provas mapeadas; "
        f"{len(itens_problemas)} sem parâmetros utilizáveis",
        flush=True,
    )
    amostra, diagnostico, fontes = amostrar_microdados_paralelo(
        args.microdados_dir,
        args.anos,
        provas,
        itens_disponiveis,
        args.chunk_size,
        args.cap_por_estrato,
        args.workers,
    )
    splits = dividir_amostra(amostra)
    catalogo, holdout = calibrar_catalogo(
        calc, provas, itens_problemas, amostra, splits, timestamp
    )
    validar_artefatos(catalogo, holdout, provas)
    manifesto = criar_manifesto(
        catalogo,
        holdout,
        fontes,
        amostra,
        splits,
        diagnostico,
        timestamp,
        not args.sem_hash_fontes,
    )
    if not args.nao_publicar:
        publicar_atomico(catalogo, holdout, manifesto)
    print(
        f"Concluído: {len(catalogo['por_prova'])} provas, "
        f"{len(holdout)} casos de holdout",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
