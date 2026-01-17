#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise de Performance de Participante do ENEM 2021
Análise comparativa baseada em notas fornecidas
"""

import pandas as pd
import numpy as np
from pathlib import Path
from config import NOTAS_PARTICIPANTE

# Caminhos
base_path = Path(__file__).parent
dados_path = base_path / "DADOS" / "MICRODADOS_ENEM_2021.csv"

print("=" * 80)
print("ANÁLISE DE PERFORMANCE - ENEM 2021")
print("=" * 80)
print("\nNOTA: Análise baseada nas notas fornecidas (número de inscrição anonimizado)")
print("\n[1/3] Carregando microdados do ENEM 2021...")
print("(Este processo pode levar alguns minutos devido ao tamanho do arquivo - 1.5 GB)")

# Colunas necessárias para a análise
colunas = [
    'NU_NOTA_CN',  # Ciências da Natureza
    'NU_NOTA_CH',  # Ciências Humanas
    'NU_NOTA_LC',  # Linguagens e Códigos
    'NU_NOTA_MT',  # Matemática
    'NU_NOTA_REDACAO',  # Redação
    'NU_NOTA_COMP1',  # Competência 1 da redação
    'NU_NOTA_COMP2',  # Competência 2 da redação
    'NU_NOTA_COMP3',  # Competência 3 da redação
    'NU_NOTA_COMP4',  # Competência 4 da redação
    'NU_NOTA_COMP5',  # Competência 5 da redação
    'TP_PRESENCA_CN',
    'TP_PRESENCA_CH',
    'TP_PRESENCA_LC',
    'TP_PRESENCA_MT',
]

# Carregar apenas as colunas necessárias
df = pd.read_csv(
    dados_path,
    sep=';',
    encoding='latin-1',
    usecols=colunas,
    low_memory=False
)

print(f"✓ Dados carregados: {len(df):,} participantes")

print("\n[2/3] Preparando dados do participante...")
print(f"✓ Notas carregadas!")

# Criar objeto similar ao participante usando as notas fornecidas
class Participante:
    def __init__(self, notas):
        for key, value in notas.items():
            setattr(self, key, value)
        # Estimativa das competências da redação (vou calcular depois com base na média)
        self.NU_NOTA_COMP1 = None
        self.NU_NOTA_COMP2 = None
        self.NU_NOTA_COMP3 = None
        self.NU_NOTA_COMP4 = None
        self.NU_NOTA_COMP5 = None

participante = Participante(NOTAS_PARTICIPANTE)

# Filtrar apenas participantes que fizeram todas as provas
df_presentes = df[
    (df['TP_PRESENCA_CN'] == 1) &
    (df['TP_PRESENCA_CH'] == 1) &
    (df['TP_PRESENCA_LC'] == 1) &
    (df['TP_PRESENCA_MT'] == 1)
].copy()

print(f"✓ Base de comparação: {len(df_presentes):,} participantes presentes em todas as provas")

print("\n[3/3] Calculando estatísticas gerais e percentis...")

# Função para calcular percentil
def calcular_percentil(valor, serie):
    """Calcula o percentil de um valor em uma série"""
    serie_limpa = serie.dropna()
    if pd.isna(valor):
        return np.nan
    percentil = (serie_limpa < valor).sum() / len(serie_limpa) * 100
    return percentil

# Áreas e suas colunas
areas = {
    'Linguagens, Códigos e suas Tecnologias': 'NU_NOTA_LC',
    'Ciências Humanas e suas Tecnologias': 'NU_NOTA_CH',
    'Ciências da Natureza e suas Tecnologias': 'NU_NOTA_CN',
    'Matemática e suas Tecnologias': 'NU_NOTA_MT',
    'Redação': 'NU_NOTA_REDACAO'
}

resultados = []

for area, coluna in areas.items():
    nota_participante = getattr(participante, coluna)

    # Estatísticas gerais
    serie = df_presentes[coluna].dropna()
    media = serie.mean()
    mediana = serie.median()
    desvio = serie.std()
    minimo = serie.min()
    maximo = serie.max()

    # Percentil do participante
    percentil = calcular_percentil(nota_participante, serie)

    # Classificação
    if percentil >= 99:
        classificacao = "EXCEPCIONAL (Top 1%)"
    elif percentil >= 95:
        classificacao = "EXCELENTE (Top 5%)"
    elif percentil >= 90:
        classificacao = "MUITO BOM (Top 10%)"
    elif percentil >= 75:
        classificacao = "BOM (Top 25%)"
    elif percentil >= 50:
        classificacao = "ACIMA DA MÉDIA"
    elif percentil >= 25:
        classificacao = "MÉDIA"
    else:
        classificacao = "ABAIXO DA MÉDIA"

    # Diferença da média
    diferenca_media = nota_participante - media

    resultados.append({
        'Área': area,
        'Nota': nota_participante,
        'Média Geral': media,
        'Mediana': mediana,
        'Desvio Padrão': desvio,
        'Mínimo': minimo,
        'Máximo': maximo,
        'Percentil': percentil,
        'Diferença da Média': diferenca_media,
        'Classificação': classificacao
    })

print("✓ Cálculos concluídos!")

print("\n" + "=" * 80)
print("RESULTADOS DA ANÁLISE")
print("=" * 80)

# Criar DataFrame de resultados
df_resultados = pd.DataFrame(resultados)

# Exibir resultados por área
print("\n┌─ DESEMPENHO POR ÁREA DE CONHECIMENTO ─────────────────────────────────────┐\n")

for idx, row in df_resultados.iterrows():
    print(f"📚 {row['Área']}")
    print(f"   Nota do Participante: {row['Nota']:.1f}")
    print(f"   Média Geral: {row['Média Geral']:.1f}")
    print(f"   Percentil: {row['Percentil']:.1f}% (melhor que {row['Percentil']:.1f}% dos participantes)")
    print(f"   Classificação: {row['Classificação']}")

    if row['Diferença da Média'] > 0:
        print(f"   ✓ {row['Diferença da Média']:.1f} pontos ACIMA da média")
    else:
        print(f"   ✗ {abs(row['Diferença da Média']):.1f} pontos ABAIXO da média")
    print()

print("└───────────────────────────────────────────────────────────────────────────┘")

# Análise geral
print("\n┌─ RESUMO EXECUTIVO ────────────────────────────────────────────────────────┐\n")

nota_media_participante = df_resultados['Nota'].mean()
nota_media_geral = df_resultados['Média Geral'].mean()

print(f"📊 Média do Participante: {nota_media_participante:.1f}")
print(f"📊 Média Geral (ENEM 2021): {nota_media_geral:.1f}")
print(f"📊 Diferença: {(nota_media_participante - nota_media_geral):.1f} pontos\n")

# Melhor e pior área
melhor_area = df_resultados.loc[df_resultados['Percentil'].idxmax()]
pior_area = df_resultados.loc[df_resultados['Percentil'].idxmin()]

print(f"🏆 MELHOR DESEMPENHO:")
print(f"   {melhor_area['Área']}")
print(f"   Nota: {melhor_area['Nota']:.1f} (Percentil {melhor_area['Percentil']:.1f}%)\n")

print(f"⚠️  DESEMPENHO MAIS BAIXO (relativo):")
print(f"   {pior_area['Área']}")
print(f"   Nota: {pior_area['Nota']:.1f} (Percentil {pior_area['Percentil']:.1f}%)\n")

# Classificação geral
percentil_medio = df_resultados['Percentil'].mean()
if percentil_medio >= 95:
    classificacao_geral = "EXCEPCIONAL - Desempenho extraordinário!"
elif percentil_medio >= 90:
    classificacao_geral = "EXCELENTE - Desempenho superior!"
elif percentil_medio >= 75:
    classificacao_geral = "MUITO BOM - Acima da maioria!"
elif percentil_medio >= 50:
    classificacao_geral = "BOM - Acima da média!"
else:
    classificacao_geral = "REGULAR - Dentro da média."

print(f"🎯 CLASSIFICAÇÃO GERAL: {classificacao_geral}")
print(f"   (Percentil médio: {percentil_medio:.1f}%)")

print("\n└───────────────────────────────────────────────────────────────────────────┘")

print("\n" + "=" * 80)
print("ANÁLISE CONCLUÍDA")
print("=" * 80)
