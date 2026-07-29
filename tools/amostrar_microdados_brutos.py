#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amostragem dos microdados brutos do INEP para calibração.

Os arquivos brutos têm de 2 a 4 GB por ano e não cabem no disco do projeto.
Esta ferramenta cria amostras uniformes para investigações legadas. A
publicação v3 usa `tools/recalibrar_validacao.py`, que preserva separadamente
faixas de nota, extremos, seleção de modelo e holdout.

Reduz cada ano a microdados_limpos/<ano>/AMOSTRA_CALIBRACAO_<ano>.csv, que
tools/calibrar_com_mapeamento.py consome no lugar do arquivo bruto.

São duas passadas por ano: a primeira conta as linhas válidas de cada prova, a
segunda sorteia cada linha com probabilidade n_alvo/total. A amostragem precisa
ser uniforme sobre o arquivo inteiro porque os microdados vêm ordenados por
inscrição — pegar as primeiras N linhas enviesaria a faixa de notas.

`--brutos` aponta para o diretório com microdados_enem_<ano>/DADOS/, como vem do
portal do INEP:
https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

Execute a partir da raiz do projeto:
    python tools/amostrar_microdados_brutos.py --brutos ~/microdados_enem
    python tools/amostrar_microdados_brutos.py --brutos ~/microdados_enem --anos 2009 2015
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AREAS = ('CN', 'CH', 'LC', 'MT')

ANOS_PADRAO = list(range(2009, 2026))

CHUNK = 500_000

# TP_LINGUA não existe em 2009; resolvida contra o cabeçalho de cada arquivo.
COLUNAS = (
    [f'TP_PRESENCA_{a}' for a in AREAS]
    + [f'CO_PROVA_{a}' for a in AREAS]
    + [f'NU_NOTA_{a}' for a in AREAS]
    + [f'TX_RESPOSTAS_{a}' for a in AREAS]
    + ['TP_LINGUA']
)


def localizar_arquivo(brutos: Path, ano: int) -> Path:
    """Encontra o arquivo de resultados do ano no diretório de microdados brutos."""
    dados = brutos / f'microdados_enem_{ano}' / 'DADOS'
    for nome in (f'MICRODADOS_ENEM_{ano}.csv', f'RESULTADOS_{ano}.csv'):
        caminho = dados / nome
        if caminho.exists():
            return caminho
    raise FileNotFoundError(f'Microdados de {ano} não encontrados em {dados}')


def colunas_do_arquivo(caminho: Path) -> list:
    """Interseção entre as colunas essenciais e as existentes no arquivo."""
    cabecalho = pd.read_csv(caminho, encoding='latin1', sep=';', nrows=0)
    return [c for c in COLUNAS if c in cabecalho.columns]


def _linhas_validas(chunk: pd.DataFrame, area: str) -> pd.DataFrame:
    """
    Linhas aproveitáveis: presente, nota positiva e respostas registradas.

    Mesmo critério de Calibrador._carregar_dados, para que a contagem da
    primeira passada valha para a segunda.
    """
    pres, prova = f'TP_PRESENCA_{area}', f'CO_PROVA_{area}'
    nota, resp = f'NU_NOTA_{area}', f'TX_RESPOSTAS_{area}'
    if pres not in chunk.columns:
        return chunk.iloc[:0]

    valido = (chunk[pres] == 1) & (chunk[nota] > 0)
    return chunk[valido].dropna(subset=[nota, resp, prova])


def contar_por_prova(caminho: Path, usecols: list) -> dict:
    """Primeira passada: linhas válidas por (área, código de prova)."""
    contagens = {area: {} for area in AREAS}

    for chunk in pd.read_csv(caminho, encoding='latin1', sep=';',
                             usecols=usecols, chunksize=CHUNK, low_memory=False):
        for area in AREAS:
            validas = _linhas_validas(chunk, area)
            if validas.empty:
                continue
            for co_prova, n in validas[f'CO_PROVA_{area}'].value_counts().items():
                chave = int(co_prova)
                contagens[area][chave] = contagens[area].get(chave, 0) + int(n)

    return contagens


def amostrar(caminho: Path, usecols: list, contagens: dict,
             n_alvo: int, seed: int) -> pd.DataFrame:
    """
    Segunda passada: Bernoulli com probabilidade n_alvo/total por prova.

    Uma linha pode ser sorteada por mais de uma área; é mantida uma vez só, com
    todas as colunas, e o Calibrador filtra por área na leitura.
    """
    prob = {
        area: {p: min(1.0, n_alvo / n) for p, n in provas.items()}
        for area, provas in contagens.items()
    }
    rng = np.random.default_rng(seed)
    partes = []

    for chunk in pd.read_csv(caminho, encoding='latin1', sep=';',
                             usecols=usecols, chunksize=CHUNK, low_memory=False):
        selecionadas = pd.Index([])
        for area in AREAS:
            validas = _linhas_validas(chunk, area)
            if validas.empty:
                continue
            p = validas[f'CO_PROVA_{area}'].astype(int).map(prob[area]).fillna(0.0)
            sorteadas = validas.index[rng.random(len(validas)) < p.to_numpy()]
            selecionadas = selecionadas.union(sorteadas)

        if len(selecionadas):
            partes.append(chunk.loc[selecionadas])

    if not partes:
        return pd.DataFrame(columns=usecols)
    return pd.concat(partes, ignore_index=True)


def processar_ano(brutos: Path, saida: Path, ano: int, n_alvo: int,
                  seed: int) -> None:
    caminho = localizar_arquivo(brutos, ano)
    usecols = colunas_do_arquivo(caminho)
    tamanho_gb = caminho.stat().st_size / 1e9
    print(f'{ano}: {caminho.name} ({tamanho_gb:.1f} GB, {len(usecols)} colunas)')

    contagens = contar_por_prova(caminho, usecols)
    n_provas = sum(len(v) for v in contagens.values())
    n_linhas = sum(sum(v.values()) for v in contagens.values())
    print(f'  contagem: {n_provas} provas, {n_linhas} respostas válidas')

    df = amostrar(caminho, usecols, contagens, n_alvo, seed + ano)

    destino_dir = saida / str(ano)
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / f'AMOSTRA_CALIBRACAO_{ano}.csv'
    df.to_csv(destino, index=False, encoding='latin1', sep=';')
    print(f'  amostra: {len(df)} linhas -> {destino} '
          f'({destino.stat().st_size / 1e6:.1f} MB)')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--brutos', required=True,
                        help='Diretório com microdados_enem_<ano>/DADOS/, como '
                             'baixado do portal do INEP')
    parser.add_argument('--saida', default='microdados_limpos',
                        help='Diretório de saída das amostras')
    parser.add_argument('--anos', type=int, nargs='+', default=ANOS_PADRAO)
    parser.add_argument('--n-por-prova', type=int, default=1500,
                        help='Alvo de participantes amostrados por prova')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    brutos = Path(args.brutos).expanduser()
    if not brutos.exists():
        print(f'Diretório de microdados brutos não encontrado: {brutos}')
        return 1

    saida = Path(args.saida)
    for ano in args.anos:
        try:
            processar_ano(brutos, saida, ano, args.n_por_prova, args.seed)
        except FileNotFoundError as e:
            print(f'{ano}: {e}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
