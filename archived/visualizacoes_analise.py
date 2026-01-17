#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualizações Gráficas da Análise do Participante ENEM 2021
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from matplotlib.patches import Rectangle
import warnings
from config import NOTAS_PARTICIPANTE

warnings.filterwarnings('ignore')

# Configurações de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

print("=" * 80)
print("GERAÇÃO DE VISUALIZAÇÕES GRÁFICAS - ENEM 2021")
print("=" * 80)

# Carregar dados
base_path = Path(__file__).parent
dados_path = base_path / "DADOS" / "MICRODADOS_ENEM_2021.csv"
output_dir = base_path / "graficos"
output_dir.mkdir(exist_ok=True)

print(f"\n[1/7] Carregando dados...")

colunas = [
    'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO',
    'TP_PRESENCA_CN', 'TP_PRESENCA_CH', 'TP_PRESENCA_LC', 'TP_PRESENCA_MT'
]

df = pd.read_csv(dados_path, sep=';', encoding='latin-1', usecols=colunas, low_memory=False)

# Filtrar presentes
df_presentes = df[
    (df['TP_PRESENCA_CN'] == 1) &
    (df['TP_PRESENCA_CH'] == 1) &
    (df['TP_PRESENCA_LC'] == 1) &
    (df['TP_PRESENCA_MT'] == 1)
].copy()

print(f"✓ Dados carregados: {len(df_presentes):,} participantes")

# Mapeamento de áreas
# Chave curta -> (Nome Display, Nome Coluna no CSV/Config)
areas_map = {
    'LC': ('Linguagens e Códigos', 'NU_NOTA_LC'),
    'CH': ('Ciências Humanas', 'NU_NOTA_CH'),
    'CN': ('Ciências da Natureza', 'NU_NOTA_CN'),
    'MT': ('Matemática', 'NU_NOTA_MT'),
    'REDACAO': ('Redação', 'NU_NOTA_REDACAO')
}

# Helper para pegar nota do config usando a chave curta
def get_nota(sigla):
    coluna = areas_map[sigla][1]
    return NOTAS_PARTICIPANTE[coluna]

# ============================================================================
# GRÁFICO 1: HISTOGRAMAS DE DISTRIBUIÇÃO COM POSIÇÃO DO PARTICIPANTE
# ============================================================================
print("\n[2/7] Gerando histogramas de distribuição...")

fig, axes = plt.subplots(3, 2, figsize=(16, 14))
fig.suptitle('Distribuição de Notas ENEM 2021 - Posição do Participante',
             fontsize=16, fontweight='bold', y=0.995)

axes = axes.flatten()

for idx, (sigla, (nome, coluna)) in enumerate(areas_map.items()):
    ax = axes[idx]

    # Dados
    dados = df_presentes[coluna].dropna()
    nota_part = get_nota(sigla)

    # Histograma
    n, bins, patches = ax.hist(dados, bins=100, alpha=0.7, color='steelblue',
                                edgecolor='black', linewidth=0.5)

    # Linha vertical na nota do participante
    ax.axvline(nota_part, color='red', linestyle='--', linewidth=2.5,
               label=f'Participante: {nota_part:.1f}')

    # Linha da média
    media = dados.mean()
    ax.axvline(media, color='orange', linestyle='--', linewidth=2,
               label=f'Média: {media:.1f}')

    # Percentil
    percentil = (dados < nota_part).sum() / len(dados) * 100

    # Sombrear área abaixo da nota do participante
    for i, patch in enumerate(patches):
        if bins[i] < nota_part:
            patch.set_facecolor('lightgreen')
            patch.set_alpha(0.6)

    ax.set_xlabel('Nota', fontweight='bold')
    ax.set_ylabel('Frequência', fontweight='bold')
    ax.set_title(f'{nome}\nPercentil: {percentil:.2f}%', fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

# Remover último subplot (são 5 áreas)
fig.delaxes(axes[5])

plt.tight_layout()
plt.savefig(output_dir / '01_histogramas_distribuicao.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/01_histogramas_distribuicao.png")
plt.close()

# ============================================================================
# GRÁFICO 2: BOX PLOTS COMPARATIVOS
# ============================================================================
print("\n[3/7] Gerando box plots comparativos...")

fig, ax = plt.subplots(figsize=(16, 8))

# Preparar dados para box plot
dados_box = []
labels_box = []
posicoes_participante = []

for sigla, (nome, coluna) in areas_map.items():
    dados_box.append(df_presentes[coluna].dropna())
    labels_box.append(nome.replace(' e suas Tecnologias', ''))
    posicoes_participante.append(get_nota(sigla))

# Box plot
bp = ax.boxplot(dados_box, labels=labels_box, patch_artist=True,
                showmeans=True, meanline=True,
                boxprops=dict(facecolor='lightblue', alpha=0.7),
                medianprops=dict(color='red', linewidth=2),
                meanprops=dict(color='orange', linewidth=2, linestyle='--'))

# Plotar notas do participante
for i, nota in enumerate(posicoes_participante, 1):
    ax.plot(i, nota, 'D', color='red', markersize=12,
            label='Participante' if i == 1 else '', zorder=5)

ax.set_ylabel('Nota', fontweight='bold', fontsize=12)
ax.set_title('Distribuição de Notas por Área - Box Plot\n(Diamante vermelho = Participante)',
             fontweight='bold', fontsize=14)
ax.legend(loc='lower right', fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / '02_boxplots_comparativos.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/02_boxplots_comparativos.png")
plt.close()

# ============================================================================
# GRÁFICO 3: COMPARAÇÃO COM PERCENTIS
# ============================================================================
print("\n[4/7] Gerando gráfico de comparação com percentis...")

fig, ax = plt.subplots(figsize=(16, 8))

# Calcular percentis
percentis = [25, 50, 75, 90, 95, 99]
cores_percentis = ['#d73027', '#fc8d59', '#fee090', '#e0f3f8', '#91bfdb', '#4575b4']

x = np.arange(len(areas_map))
width = 0.12

for idx, p in enumerate(percentis):
    valores = [df_presentes[areas_map[sigla][1]].dropna().quantile(p/100)
               for sigla in areas_map.keys()]
    offset = width * (idx - len(percentis)/2 + 0.5)
    ax.bar(x + offset, valores, width, label=f'P{p}', alpha=0.8)

# Linha das notas do participante
notas_part = [get_nota(sigla) for sigla in areas_map.keys()]
ax.plot(x, notas_part, 'ro-', linewidth=3, markersize=10,
        label='Participante', zorder=10)

ax.set_xlabel('Área de Conhecimento', fontweight='bold', fontsize=12)
ax.set_ylabel('Nota', fontweight='bold', fontsize=12)
ax.set_title('Comparação com Percentis da População ENEM 2021',
             fontweight='bold', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels([areas_map[s][0].replace(' e suas Tecnologias', '')
                     for s in areas_map.keys()], rotation=15, ha='right')
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / '03_comparacao_percentis.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/03_comparacao_percentis.png")
plt.close()

# ============================================================================
# GRÁFICO 4: MATRIZ DE CORRELAÇÃO ENTRE ÁREAS
# ============================================================================
print("\n[5/7] Gerando matriz de correlação...")

fig, ax = plt.subplots(figsize=(10, 8))

# Preparar DataFrame para correlação
df_notas = df_presentes[['NU_NOTA_LC', 'NU_NOTA_CH', 'NU_NOTA_CN',
                          'NU_NOTA_MT', 'NU_NOTA_REDACAO']].dropna()
df_notas.columns = ['LC', 'CH', 'CN', 'MT', 'Redação']

# Calcular correlação
corr = df_notas.corr()

# Heatmap
sns.heatmap(corr, annot=True, fmt='.3f', cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            vmin=0, vmax=1, ax=ax)

ax.set_title('Matriz de Correlação entre Áreas de Conhecimento\nENEM 2021',
             fontweight='bold', fontsize=14, pad=20)

plt.tight_layout()
plt.savefig(output_dir / '04_matriz_correlacao.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/04_matriz_correlacao.png")
plt.close()

# ============================================================================
# GRÁFICO 5: SCATTER PLOTS DE CORRELAÇÃO
# ============================================================================
print("\n[6/7] Gerando scatter plots de correlação...")

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Correlações entre Áreas - Posição do Participante',
             fontsize=16, fontweight='bold')

axes = axes.flatten()

# Pares de áreas para comparar
pares = [
    ('NU_NOTA_MT', 'NU_NOTA_CN', 'Matemática', 'Ciências da Natureza', 'MT', 'CN'),
    ('NU_NOTA_CH', 'NU_NOTA_LC', 'Ciências Humanas', 'Linguagens', 'CH', 'LC'),
    ('NU_NOTA_MT', 'NU_NOTA_LC', 'Matemática', 'Linguagens', 'MT', 'LC'),
    ('NU_NOTA_CN', 'NU_NOTA_CH', 'Ciências da Natureza', 'Ciências Humanas', 'CN', 'CH'),
    ('NU_NOTA_REDACAO', 'NU_NOTA_LC', 'Redação', 'Linguagens', 'REDACAO', 'LC'),
    ('NU_NOTA_MT', 'NU_NOTA_REDACAO', 'Matemática', 'Redação', 'MT', 'REDACAO')
]

for idx, (col_x, col_y, nome_x, nome_y, sigla_x, sigla_y) in enumerate(pares):
    ax = axes[idx]

    # Sample para não sobrecarregar o gráfico
    sample = df_presentes[[col_x, col_y]].dropna().sample(n=min(10000, len(df_presentes)),
                                                            random_state=42)

    # Scatter plot
    ax.scatter(sample[col_x], sample[col_y], alpha=0.3, s=1, color='steelblue')

    # Ponto do participante
    ax.scatter(get_nota(sigla_x), get_nota(sigla_y),
               color='red', s=200, marker='*', edgecolors='black', linewidth=1.5,
               label='Participante', zorder=5)

    # Linha de tendência
    z = np.polyfit(df_presentes[col_x].dropna(), df_presentes[col_y].dropna(), 1)
    p = np.poly1d(z)
    x_line = np.linspace(df_presentes[col_x].min(), df_presentes[col_x].max(), 100)
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Tendência')

    # Correlação
    corr_val = df_presentes[[col_x, col_y]].corr().iloc[0, 1]

    ax.set_xlabel(nome_x, fontweight='bold')
    ax.set_ylabel(nome_y, fontweight='bold')
    ax.set_title(f'{nome_x} × {nome_y}\nCorrelação: {corr_val:.3f}', fontweight='bold')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '05_scatter_correlacoes.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/05_scatter_correlacoes.png")
plt.close()

# ============================================================================
# GRÁFICO 6: RADAR CHART (SPIDER PLOT)
# ============================================================================
print("\n[7/7] Gerando radar chart...")

fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

# Categorias
categorias = ['Linguagens', 'C. Humanas', 'C. Natureza', 'Matemática', 'Redação']
num_vars = len(categorias)

# Ângulos para cada eixo
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]  # Fechar o círculo

# Normalizar notas para 0-1 baseado no range de cada área
def normalizar(valores, coluna):
    dados = df_presentes[coluna].dropna()
    min_val = dados.min()
    max_val = dados.max()
    return [(v - min_val) / (max_val - min_val) for v in valores]

# Dados do participante (normalizados)
notas_part_norm = []
for sigla in ['LC', 'CH', 'CN', 'MT', 'REDACAO']:
    coluna = areas_map[sigla][1]
    nota = get_nota(sigla)
    norm = (nota - df_presentes[coluna].min()) / (df_presentes[coluna].max() - df_presentes[coluna].min())
    notas_part_norm.append(norm)
notas_part_norm += notas_part_norm[:1]

# Dados dos percentis
percentis_radar = [50, 75, 90, 95, 99]
cores_radar = ['#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']

for p, cor in zip(percentis_radar, cores_radar):
    valores = []
    for sigla in ['LC', 'CH', 'CN', 'MT', 'REDACAO']:
        coluna = areas_map[sigla][1]
        val = df_presentes[coluna].dropna().quantile(p/100)
        norm = (val - df_presentes[coluna].min()) / (df_presentes[coluna].max() - df_presentes[coluna].min())
        valores.append(norm)
    valores += valores[:1]
    ax.plot(angles, valores, 'o-', linewidth=1.5, label=f'P{p}', color=cor, alpha=0.6)
    ax.fill(angles, valores, alpha=0.15, color=cor)

# Participante
ax.plot(angles, notas_part_norm, 'o-', linewidth=3, label='Participante',
        color='blue', markersize=8)
ax.fill(angles, notas_part_norm, alpha=0.25, color='blue')

# Configurar eixos
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categorias, fontsize=11, fontweight='bold')
ax.set_ylim(0, 1)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=9)
ax.grid(True, alpha=0.3)

ax.set_title('Comparação Multidimensional - Radar Chart\n(Normalizado por área)',
             fontweight='bold', fontsize=14, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / '06_radar_chart.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/06_radar_chart.png")
plt.close()

# ============================================================================
# GRÁFICO 7: CURVAS CUMULATIVAS
# ============================================================================
print("\n[EXTRA] Gerando curvas cumulativas...")

fig, axes = plt.subplots(3, 2, figsize=(16, 14))
fig.suptitle('Distribuição Cumulativa - ENEM 2021', fontsize=16, fontweight='bold')

axes = axes.flatten()

for idx, (sigla, (nome, coluna)) in enumerate(areas_map.items()):
    ax = axes[idx]

    dados = df_presentes[coluna].dropna().sort_values()
    nota_part = get_nota(sigla)

    # Calcular percentis cumulativos
    percentis = np.arange(len(dados)) / len(dados) * 100

    # Curva cumulativa
    ax.plot(dados, percentis, linewidth=2, color='steelblue')

    # Linha horizontal e vertical do participante
    percentil = (dados < nota_part).sum() / len(dados) * 100
    ax.axvline(nota_part, color='red', linestyle='--', linewidth=2.5,
               label=f'Participante: {nota_part:.1f}')
    ax.axhline(percentil, color='red', linestyle=':', linewidth=2, alpha=0.6)

    # Sombrear área abaixo
    ax.fill_between(dados[dados <= nota_part], 0,
                     percentis[dados <= nota_part],
                     alpha=0.3, color='green', label='Notas menores')

    ax.set_xlabel('Nota', fontweight='bold')
    ax.set_ylabel('Percentil Cumulativo (%)', fontweight='bold')
    ax.set_title(f'{nome}\nPercentil: {percentil:.2f}%', fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)

fig.delaxes(axes[5])

plt.tight_layout()
plt.savefig(output_dir / '07_curvas_cumulativas.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/07_curvas_cumulativas.png")
plt.close()

# ============================================================================
# GRÁFICO 8: COMPARAÇÃO DE PERFORMANCE GERAL
# ============================================================================
print("\n[EXTRA] Gerando gráfico de performance geral...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
fig.suptitle('Performance Geral do Participante', fontsize=16, fontweight='bold')

# Gráfico 1: Barras comparativas
areas_nomes = [areas_map[s][0].replace(' e suas Tecnologias', '') for s in areas_map.keys()]
notas_part = [get_nota(s) for s in areas_map.keys()]
medias = [df_presentes[areas_map[s][1]].dropna().mean() for s in areas_map.keys()]
p95 = [df_presentes[areas_map[s][1]].dropna().quantile(0.95) for s in areas_map.keys()]

x = np.arange(len(areas_nomes))
width = 0.25

bars1 = ax1.bar(x - width, medias, width, label='Média Geral', alpha=0.8, color='gray')
bars2 = ax1.bar(x, p95, width, label='Percentil 95', alpha=0.8, color='orange')
bars3 = ax1.bar(x + width, notas_part, width, label='Participante', alpha=0.8, color='green')

ax1.set_xlabel('Área', fontweight='bold')
ax1.set_ylabel('Nota', fontweight='bold')
ax1.set_title('Comparação: Participante vs População', fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(areas_nomes, rotation=15, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3, axis='y')

# Adicionar valores nas barras
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}', ha='center', va='bottom', fontsize=8)

# Gráfico 2: Percentis por área
percentis_por_area = []
for sigla in areas_map.keys():
    coluna = areas_map[sigla][1]
    nota = get_nota(sigla)
    dados = df_presentes[coluna].dropna()
    percentil = (dados < nota).sum() / len(dados) * 100
    percentis_por_area.append(percentil)

colors = ['red' if p >= 99 else 'orange' if p >= 95 else 'yellow'
          for p in percentis_por_area]
bars = ax2.barh(areas_nomes, percentis_por_area, color=colors, alpha=0.7, edgecolor='black')

ax2.set_xlabel('Percentil (%)', fontweight='bold')
ax2.set_title('Percentil do Participante por Área', fontweight='bold')
ax2.set_xlim(0, 100)
ax2.axvline(95, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='P95')
ax2.axvline(99, color='darkred', linestyle='--', linewidth=1.5, alpha=0.5, label='P99')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='x')

# Adicionar valores
for i, (bar, val) in enumerate(zip(bars, percentis_por_area)):
    ax2.text(val + 1, i, f'{val:.2f}%', va='center', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '08_performance_geral.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: graficos/08_performance_geral.png")
plt.close()

print("\n" + "=" * 80)
print("VISUALIZAÇÕES CONCLUÍDAS!")
print("=" * 80)
print(f"\nTodos os gráficos foram salvos em: {output_dir}/")
print("\nArquivos gerados:")
print("  1. 01_histogramas_distribuicao.png - Distribuições com posição do participante")
print("  2. 02_boxplots_comparativos.png - Box plots por área")
print("  3. 03_comparacao_percentis.png - Comparação com percentis da população")
print("  4. 04_matriz_correlacao.png - Correlação entre áreas")
print("  5. 05_scatter_correlacoes.png - Scatter plots de correlação")
print("  6. 06_radar_chart.png - Radar chart multidimensional")
print("  7. 07_curvas_cumulativas.png - Curvas de distribuição cumulativa")
print("  8. 08_performance_geral.png - Performance geral comparativa")
print("\n" + "=" * 80)
