#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Recalibra todas as provas e publica um catálogo v4 validado.

O script faz uma passagem pelos microdados oficiais, retém deterministicamente
uma amostra estratificada por prova/faixa/idioma, ajusta a escala sem reutilizar
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
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tri_enem import CalculadorTRI, MapeadorProvas  # noqa: E402
from tri_enem.calibracao_modelos import (  # noqa: E402
    ROTULOS_FAIXAS,
    classificar_validacao,
    faixa_nota,
    ranking_erro_medio,
)
from tools.relatorio_validacao import gerar_relatorio  # noqa: E402,F401

AREAS = ("CN", "CH", "LC", "MT")
CAP_ESTRATO = 160
SCHEMA_VERSION = 4
ALGORITHM_VERSION = "stratified-v3.2"
MODELO = "escala-fixa-grade40-v1"
HASH_KEY = "enem-tri-v3"
IDENTITY_ALGORITHM = "pandas-null-object-v1"


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
    def texto_nullable(serie):
        s = serie.astype("string").astype(object)
        return s.where(s.notna(), None)

    frame = pd.DataFrame({
        "chave": HASH_KEY,
        "ano": ano,
        "area": area,
        "prova": texto_nullable(prova.astype("Int64")),
        "lingua": texto_nullable(lingua.astype("Int64")),
        "id": texto_nullable(identificador),
    })
    # Pandas 2 convertia NA em '<NA>'; Pandas 3 preserva ausência ao usar
    # astype(str). Uma representação explícita evita mudar a identidade dos
    # participantes entre ambientes, mantendo os hashes gerados no Pandas 3.
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
            respostas.str.len().eq(50).fillna(False).astype(bool)
            & respostas.str.slice(5, 10).eq("99999").fillna(False).astype(bool)
            & normal_ingles.str.fullmatch(r"[A-E.*]{45}", na=False)
        )
        valida_50_espanhol = (
            respostas.str.len().eq(50).fillna(False).astype(bool)
            & respostas.str.slice(0, 5).eq("99999").fillna(False).astype(bool)
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
    excluir_case_ids: set[str] | None = None,
) -> Tuple[AmostraEstratificada, Dict[str, Any], List[Path]]:
    amostra = AmostraEstratificada(cap)
    diagnostico: Dict[str, Any] = {
        "codigos_nao_mapeados": defaultdict(int),
        "participantes_mapeados": defaultdict(int),
    }
    fontes = []
    indice_excluidos = pd.Index(list(excluir_case_ids), dtype=object) if excluir_case_ids else None

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
                if indice_excluidos is not None:
                    # Reutiliza o índice de hashes entre chunks; isin(set)
                    # reconstruía uma tabela com mais de 500 mil entradas.
                    dados = dados[indice_excluidos.get_indexer(dados["case_id"].to_numpy(dtype=object)) < 0]

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
    excluir_case_ids: set[str] | None = None,
) -> Tuple[AmostraEstratificada, Dict[str, Any], List[Path]]:
    """Processa anos independentes em paralelo e funde amostras determinísticas."""
    if workers <= 1 or len(anos) <= 1:
        return amostrar_microdados(
            base, anos, provas, itens_disponiveis, chunk_size, cap, excluir_case_ids
        )
    tarefas = [
        (base, [ano], provas, itens_disponiveis, chunk_size, cap, excluir_case_ids)
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


def _publicos(casos: Sequence[Caso], split: str) -> List[Dict[str, Any]]:
    return [caso.publico(split) for caso in casos]


def _calculador_catalogo(calc: CalculadorTRI, catalogo: Dict[str, Any],
                         reconstrucoes: Dict[str, Any]) -> CalculadorTRI:
    novo = CalculadorTRI(itens_path=str(calc.base_path), reconstrucoes=reconstrucoes,
                         catalogo=catalogo)
    novo._cache_df_itens = calc._cache_df_itens
    return novo


def calibrar_catalogo(
    calc: CalculadorTRI,
    provas: Dict[tuple, Any],
    itens_problemas: Dict[str, str],
    amostra: AmostraEstratificada,
    splits: Dict[str, Dict[str, List[Caso]]],
    timestamp: str,
    candidatos_reconstrucao: Dict[str, List[Dict[str, Any]]] | None = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Escala por área no treino; reconstruções pela seleção; holdout só avalia.

    As notas de gabarito do catálogo empacotado são preservadas: vêm do censo
    (``levantar_notas_gabarito.py``), não da amostra.
    """
    from tri_enem.coeficientes import obter_catalogo
    from tools.avaliar_catalogo import (
        ajustar_escala, carregar_inconsistentes, metricas, metricas_ponderadas,
        notas_casos, pesos_estrato,
    )

    empacotado = obter_catalogo()
    inconsistentes = carregar_inconsistentes()
    treino = [c for partes in splits.values() for c in _publicos(partes["treino"], "treino")]
    escala = ajustar_escala(calc, treino, inconsistentes)
    catalogo: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "por_prova": {},
        "metadata": {
            "versao": "4.0",
            "modelo": MODELO,
            "quadratura": {"tipo": "grade", "pontos": calc.N_QUADRATURA,
                           "limite": calc.LIMITE_QUADRATURA},
            "escala": escala,
            "ultima_calibracao": timestamp,
        },
    }
    notas_gabarito = {
        chave: info["nota_gabarito"]
        for chave, info in empacotado.get("por_prova", {}).items()
        if "nota_gabarito" in info
    }
    contexto = {"metadata": catalogo["metadata"], "por_prova": {
        chave: {"nota_gabarito": valor} for chave, valor in notas_gabarito.items()}}
    faixas_por_prova: Dict[str, set[str]] = defaultdict(set)
    for (prova_key, _, faixa), n in amostra.contagens.items():
        if n:
            faixas_por_prova[prova_key].add(faixa)
    holdout_publico: List[Dict[str, Any]] = []
    for (ano, area, codigo), prova in sorted(provas.items()):
        key = f"{ano},{area},{codigo}"
        base: Dict[str, Any] = {
            "ano": ano, "area": area, "prova": codigo,
            "tipo_aplicacao": prova.tipo_aplicacao, "cor": prova.cor,
            "validacao": None,
            "qualidade": {"status": "nao_calibrado", "motivo": "sem_amostra",
                          "validado_em": timestamp},
        }
        if key in notas_gabarito:
            base["nota_gabarito"] = notas_gabarito[key]
        catalogo["por_prova"][key] = base
        if key in itens_problemas:
            base["qualidade"].update(status="sem_itens", motivo=itens_problemas[key])
            continue
        partes = splits.get(key)
        if not partes:
            base["qualidade"].update(status="sem_participantes", motivo="sem_participantes_validos")
            continue
        selecao = [c for c in _publicos(partes["selecao"], "selecao")
                   if c["case_id"] not in inconsistentes]
        alternativas = [calc.reconstrucoes.get(key)] + list((candidatos_reconstrucao or {}).get(key, []))
        escolhida, ranking = None, None
        for reconstrucao in alternativas:
            reconstrucoes = {**calc.reconstrucoes}
            reconstrucoes.pop(key, None)
            if reconstrucao:
                reconstrucoes[key] = reconstrucao
            candidato = _calculador_catalogo(calc, contexto, reconstrucoes)
            if not selecao:
                escolhida = reconstrucao
                break
            erros = notas_casos(candidato, selecao) - np.asarray([c["nota_oficial"] for c in selecao])
            m = metricas_ponderadas(erros, pesos_estrato(selecao, amostra.contagens))
            ordem = ranking_erro_medio(m)
            if ranking is None or ordem < ranking:
                escolhida, ranking = reconstrucao, ordem
        if escolhida:
            base["reconstrucao_itens"] = escolhida
        reconstrucoes = {**calc.reconstrucoes}
        reconstrucoes.pop(key, None)
        if escolhida:
            reconstrucoes[key] = escolhida
        holdout = _publicos(partes["holdout"], "holdout")
        holdout_publico.extend(holdout)
        avaliados = [c for c in holdout if c["case_id"] not in inconsistentes]
        if avaliados:
            calc_prova = _calculador_catalogo(calc, contexto, reconstrucoes)
            erros = notas_casos(calc_prova, avaliados) - np.asarray([c["nota_oficial"] for c in avaliados])
            base["validacao"] = {
                **metricas(erros, [c["faixa"] for c in avaliados]),
                "faixas_existentes": sorted(faixas_por_prova[key]),
            }
            base["teste"] = dict(base["validacao"])
        status, motivo = classificar_validacao(
            base.get("teste"), sorted(faixas_por_prova[key]), base.get("censo"))
        base["qualidade"].update(status=status, motivo=motivo)
        print(f"{key}: {status}; n={len(avaliados)}", flush=True)
    return catalogo, sorted(
        holdout_publico,
        key=lambda item: (item["ano"], item["area"], item["co_prova"], item["case_id"]),
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
            "identity_algorithm": IDENTITY_ALGORITHM,
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
            if (info.get("validacao_confirmacao") or {}).get("erro_maximo", 0) > 2.0 + 1e-12:
                raise RuntimeError(f"{key}: status ok com erro na confirmação acima de 2 pontos")
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
