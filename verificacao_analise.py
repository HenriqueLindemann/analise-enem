#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação detalhada da análise do participante
"""

import pandas as pd
import numpy as np
from pathlib import Path

# NOTAS DO PARTICIPANTE
NOTAS_PARTICIPANTE = {
    'LC': 677.5,
    'CH': 749.9,
    'CN': 752.8,
    'MT': 916.4,
    'REDACAO': 940.0
}

print("=" * 80)
print("VERIFICAÇÃO DETALHADA DA ANÁLISE")
print("=" * 80)

# Carregar dados
base_path = Path(__file__).parent
dados_path = base_path / "DADOS" / "MICRODADOS_ENEM_2021.csv"

print("\n[1/4] Carregando dados...")

colunas = [
    'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO',
    'TP_PRESENCA_CN', 'TP_PRESENCA_CH', 'TP_PRESENCA_LC', 'TP_PRESENCA_MT'
]

df = pd.read_csv(dados_path, sep=';', encoding='latin-1', usecols=colunas, low_memory=False)

print(f"✓ Total de registros: {len(df):,}")

# Filtrar presentes
df_presentes = df[
    (df['TP_PRESENCA_CN'] == 1) &
    (df['TP_PRESENCA_CH'] == 1) &
    (df['TP_PRESENCA_LC'] == 1) &
    (df['TP_PRESENCA_MT'] == 1)
].copy()

print(f"✓ Participantes presentes em todas as provas: {len(df_presentes):,}")

print("\n[2/4] Verificando estatísticas por área...")
print("\n" + "=" * 80)

areas_map = {
    'LC': ('Linguagens e Códigos', 'NU_NOTA_LC'),
    'CH': ('Ciências Humanas', 'NU_NOTA_CH'),
    'CN': ('Ciências da Natureza', 'NU_NOTA_CN'),
    'MT': ('Matemática', 'NU_NOTA_MT'),
    'REDACAO': ('Redação', 'NU_NOTA_REDACAO')
}

for sigla, (nome, coluna) in areas_map.items():
    nota_participante = NOTAS_PARTICIPANTE[sigla]

    print(f"\n{nome.upper()}")
    print("-" * 80)

    # Remover NaN
    serie = df_presentes[coluna].dropna()

    # Estatísticas básicas
    print(f"Nota do participante: {nota_participante:.1f}")
    print(f"\nEstatísticas da população:")
    print(f"  Média: {serie.mean():.2f}")
    print(f"  Mediana: {serie.median():.2f}")
    print(f"  Desvio padrão: {serie.std():.2f}")
    print(f"  Mínimo: {serie.min():.2f}")
    print(f"  Máximo: {serie.max():.2f}")
    print(f"  Total de notas válidas: {len(serie):,}")

    # Cálculo de percentil detalhado
    abaixo = (serie < nota_participante).sum()
    igual = (serie == nota_participante).sum()
    acima = (serie > nota_participante).sum()

    percentil = (abaixo / len(serie)) * 100

    print(f"\nDistribuição:")
    print(f"  Participantes com nota < {nota_participante:.1f}: {abaixo:,} ({(abaixo/len(serie)*100):.2f}%)")
    print(f"  Participantes com nota = {nota_participante:.1f}: {igual:,} ({(igual/len(serie)*100):.4f}%)")
    print(f"  Participantes com nota > {nota_participante:.1f}: {acima:,} ({(acima/len(serie)*100):.2f}%)")
    print(f"\n  >>> PERCENTIL: {percentil:.2f}% (melhor que {percentil:.2f}% dos participantes)")

    # Quantis para contexto
    print(f"\nQuantis de referência:")
    print(f"  Q25 (25%): {serie.quantile(0.25):.1f}")
    print(f"  Q50 (50%): {serie.quantile(0.50):.1f}")
    print(f"  Q75 (75%): {serie.quantile(0.75):.1f}")
    print(f"  Q90 (90%): {serie.quantile(0.90):.1f}")
    print(f"  Q95 (95%): {serie.quantile(0.95):.1f}")
    print(f"  Q99 (99%): {serie.quantile(0.99):.1f}")
    print(f"  Q99.5 (99.5%): {serie.quantile(0.995):.1f}")
    print(f"  Q99.9 (99.9%): {serie.quantile(0.999):.1f}")

print("\n" + "=" * 80)
print("\n[3/4] Buscando participantes com desempenho similar...")

# Buscar participantes com notas próximas em todas as áreas
tolerancia = 10  # +/- 10 pontos

filtro = (
    (df_presentes['NU_NOTA_LC'].between(NOTAS_PARTICIPANTE['LC'] - tolerancia,
                                         NOTAS_PARTICIPANTE['LC'] + tolerancia)) &
    (df_presentes['NU_NOTA_CH'].between(NOTAS_PARTICIPANTE['CH'] - tolerancia,
                                         NOTAS_PARTICIPANTE['CH'] + tolerancia)) &
    (df_presentes['NU_NOTA_CN'].between(NOTAS_PARTICIPANTE['CN'] - tolerancia,
                                         NOTAS_PARTICIPANTE['CN'] + tolerancia)) &
    (df_presentes['NU_NOTA_MT'].between(NOTAS_PARTICIPANTE['MT'] - tolerancia,
                                         NOTAS_PARTICIPANTE['MT'] + tolerancia))
)

similares = df_presentes[filtro]

print(f"\nParticipantes com todas as notas no intervalo ±{tolerancia} pontos:")
print(f"  Total: {len(similares):,} participantes ({len(similares)/len(df_presentes)*100:.4f}%)")

if len(similares) > 0:
    print(f"\nPrimeiros 5 exemplos de notas similares:")
    print(similares[['NU_NOTA_LC', 'NU_NOTA_CH', 'NU_NOTA_CN', 'NU_NOTA_MT', 'NU_NOTA_REDACAO']].head())

print("\n[4/4] Calculando posição absoluta...")

# Calcular média geral de cada participante
df_presentes['MEDIA'] = df_presentes[['NU_NOTA_LC', 'NU_NOTA_CH',
                                       'NU_NOTA_CN', 'NU_NOTA_MT',
                                       'NU_NOTA_REDACAO']].mean(axis=1)

media_participante = np.mean(list(NOTAS_PARTICIPANTE.values()))
posicao = (df_presentes['MEDIA'] > media_participante).sum() + 1

print(f"\nMédia das 5 notas do participante: {media_participante:.2f}")
print(f"Posição aproximada no ranking geral: {posicao:,}º de {len(df_presentes):,}")
print(f"Percentil geral: {((len(df_presentes) - posicao)/len(df_presentes)*100):.2f}%")

print("\n" + "=" * 80)
print("TOP 10 MÉDIAS GERAIS NO ENEM 2021")
print("=" * 80)

top10 = df_presentes.nlargest(10, 'MEDIA')[['NU_NOTA_LC', 'NU_NOTA_CH',
                                              'NU_NOTA_CN', 'NU_NOTA_MT',
                                              'NU_NOTA_REDACAO', 'MEDIA']]

for idx, (i, row) in enumerate(top10.iterrows(), 1):
    print(f"\n{idx}º lugar - Média: {row['MEDIA']:.2f}")
    print(f"   LC: {row['NU_NOTA_LC']:.1f} | CH: {row['NU_NOTA_CH']:.1f} | "
          f"CN: {row['NU_NOTA_CN']:.1f} | MT: {row['NU_NOTA_MT']:.1f} | "
          f"RED: {row['NU_NOTA_REDACAO']:.1f}")

print("\n" + "=" * 80)
print("VERIFICAÇÃO CONCLUÍDA")
print("=" * 80)
