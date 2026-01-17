#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise TRI FINAL - Corrigida para Língua Estrangeira
Visualizações de padrão de acertos/erros por dificuldade TRI
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
from config import NOTAS_PARTICIPANTE as NOTAS_ALVO

warnings.filterwarnings('ignore')

# Configurações
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 80)
print("ANÁLISE TRI FINAL - CORRIGIDA PARA LÍNGUA ESTRANGEIRA")
print("=" * 80)

# Caminhos
base_path = Path(__file__).parent
dados_path = base_path / "DADOS" / "MICRODADOS_ENEM_2021.csv"
itens_path = base_path / "DADOS" / "ITENS_PROVA_2021.csv"
output_dir = base_path / "graficos_tri"
output_dir.mkdir(exist_ok=True)

print("\n[1/6] Carregando microdados...")

# Colunas necessárias (adicionar TP_LINGUA)
colunas = [
    'NU_INSCRICAO',
    'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO',
    'TX_RESPOSTAS_CN', 'TX_RESPOSTAS_CH', 'TX_RESPOSTAS_LC', 'TX_RESPOSTAS_MT',
    'TX_GABARITO_CN', 'TX_GABARITO_CH', 'TX_GABARITO_LC', 'TX_GABARITO_MT',
    'CO_PROVA_CN', 'CO_PROVA_CH', 'CO_PROVA_LC', 'CO_PROVA_MT',
    'TP_PRESENCA_CN', 'TP_PRESENCA_CH', 'TP_PRESENCA_LC', 'TP_PRESENCA_MT',
    'TP_LINGUA'
]

df = pd.read_csv(dados_path, sep=';', encoding='latin-1', usecols=colunas, low_memory=False)
print(f"✓ {len(df):,} participantes carregados")

print("\n[2/6] Buscando participante pelas notas exatas...")

# Buscar participante com notas exatas
tolerancia = 0.1
mask = (
    (df['NU_NOTA_LC'].between(NOTAS_ALVO['NU_NOTA_LC'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_LC'] + tolerancia)) &
    (df['NU_NOTA_CH'].between(NOTAS_ALVO['NU_NOTA_CH'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_CH'] + tolerancia)) &
    (df['NU_NOTA_CN'].between(NOTAS_ALVO['NU_NOTA_CN'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_CN'] + tolerancia)) &
    (df['NU_NOTA_MT'].between(NOTAS_ALVO['NU_NOTA_MT'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_MT'] + tolerancia)) &
    (df['NU_NOTA_REDACAO'].between(NOTAS_ALVO['NU_NOTA_REDACAO'] - tolerancia,
                                    NOTAS_ALVO['NU_NOTA_REDACAO'] + tolerancia))
)

candidatos = df[mask]

if len(candidatos) == 0:
    print("✗ Participante não encontrado!")
    exit(1)

participante = candidatos.iloc[0]

print(f"✓ Participante encontrado: {participante['NU_INSCRICAO']}")
print(f"  Língua estrangeira: {'Inglês' if participante['TP_LINGUA'] == 0 else 'Espanhol'}")

print("\n[3/6] Carregando parâmetros TRI das questões...")

df_itens = pd.read_csv(itens_path, sep=';', encoding='latin-1')
print(f"✓ {len(df_itens):,} itens carregados")

print("\n[4/6] Analisando respostas do participante...")

# Áreas
areas = {
    'LC': {'nome': 'Linguagens e Códigos', 'col_resp': 'TX_RESPOSTAS_LC',
           'col_gab': 'TX_GABARITO_LC', 'col_prova': 'CO_PROVA_LC', 'sg': 'LC'},
    'CH': {'nome': 'Ciências Humanas', 'col_resp': 'TX_RESPOSTAS_CH',
           'col_gab': 'TX_GABARITO_CH', 'col_prova': 'CO_PROVA_CH', 'sg': 'CH'},
    'CN': {'nome': 'Ciências da Natureza', 'col_resp': 'TX_RESPOSTAS_CN',
           'col_gab': 'TX_GABARITO_CN', 'col_prova': 'CO_PROVA_CN', 'sg': 'CN'},
    'MT': {'nome': 'Matemática', 'col_resp': 'TX_RESPOSTAS_MT',
           'col_gab': 'TX_GABARITO_MT', 'col_prova': 'CO_PROVA_MT', 'sg': 'MT'}
}

resultados_por_area = {}

for area, info in areas.items():
    print(f"\n{info['nome']}:")

    respostas = str(participante[info['col_resp']])
    gabarito = str(participante[info['col_gab']])
    codigo_prova = participante[info['col_prova']]

    if pd.isna(respostas) or pd.isna(gabarito):
        print(f"  ⚠ Dados ausentes")
        continue

    # Buscar parâmetros TRI das questões desta prova
    itens_prova = df_itens[
        (df_itens['SG_AREA'] == info['sg']) &
        (df_itens['CO_PROVA'] == codigo_prova)
    ].copy()

    if len(itens_prova) == 0:
        print(f"  ⚠ Parâmetros TRI não encontrados")
        continue

    # Ordenar por posição
    itens_prova = itens_prova.sort_values('CO_POSICAO').reset_index(drop=True)

    # Determinar questões válidas (especial para LC)
    if area == 'LC':
        # Linguagens tem língua estrangeira
        if participante['TP_LINGUA'] == 0:  # Inglês
            questoes_validas = list(range(0, 5)) + list(range(10, len(respostas)))
            lingua_msg = "Inglês (Q1-5 + Q11-50)"
        else:  # Espanhol
            questoes_validas = list(range(5, len(respostas)))
            lingua_msg = "Espanhol (Q6-50)"

        print(f"  Língua: {lingua_msg}")
        print(f"  Questões válidas: {len(questoes_validas)}")
    else:
        # Outras áreas: todas as questões
        questoes_validas = list(range(len(respostas)))

    # Criar análise questão por questão
    questoes = []
    for idx in questoes_validas:
        if idx >= len(respostas) or idx >= len(itens_prova):
            continue

        resp = respostas[idx]
        gab = gabarito[idx]
        item = itens_prova.iloc[idx]

        acertou = (resp == gab and resp != '.' and resp != '9')
        param_b = item['NU_PARAM_B']

        questoes.append({
            'posicao': idx + 1,
            'resposta': resp,
            'gabarito': gab,
            'acertou': acertou,
            'param_a': item['NU_PARAM_A'],
            'param_b': param_b if not pd.isna(param_b) else 999,
            'param_c': item['NU_PARAM_C'],
            'dificuldade': param_b if not pd.isna(param_b) else 999
        })

    df_questoes = pd.DataFrame(questoes)
    resultados_por_area[area] = df_questoes

    # Estatísticas
    total_validas = len(questoes_validas)
    acertos = df_questoes['acertou'].sum()
    perc_acertos = (acertos / total_validas) * 100

    print(f"  Acertos: {acertos}/{total_validas} ({perc_acertos:.1f}%)")

    # Dividir em quartis de dificuldade (excluindo NaN)
    df_questoes_validos = df_questoes[df_questoes['dificuldade'] != 999].copy()

    if len(df_questoes_validos) > 0:
        df_questoes_validos['quartil_dif'] = pd.qcut(
            df_questoes_validos['dificuldade'],
            q=4, labels=['Fácil', 'Médio', 'Difícil', 'Muito Difícil'],
            duplicates='drop'
        )

        # Propagar de volta para o df principal
        df_questoes.loc[df_questoes_validos.index, 'quartil_dif'] = df_questoes_validos['quartil_dif']

        print(f"  Desempenho por nível de dificuldade:")
        for nivel in ['Fácil', 'Médio', 'Difícil', 'Muito Difícil']:
            subset = df_questoes[df_questoes['quartil_dif'] == nivel]
            if len(subset) > 0:
                acertos_nivel = subset['acertou'].sum()
                total_nivel = len(subset)
                perc_nivel = (acertos_nivel / total_nivel * 100) if total_nivel > 0 else 0
                print(f"    {nivel}: {acertos_nivel}/{total_nivel} ({perc_nivel:.1f}%)")

print("\n[5/6] Gerando visualizações atualizadas...")

# ============================================================================
# GRÁFICO 1: Acertos por Dificuldade (TRI)
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(18, 14))
fig.suptitle('Análise TRI: Padrão de Acertos vs Dificuldade das Questões\n(Parâmetro B da TRI - CORRIGIDO para Língua Estrangeira)',
             fontsize=16, fontweight='bold')

axes = axes.flatten()

for idx, (area, df_q) in enumerate(resultados_por_area.items()):
    ax = axes[idx]

    # Filtrar questões com param_b válido
    df_q_plot = df_q[df_q['dificuldade'] != 999].copy()

    # Separar acertos e erros
    acertos_df = df_q_plot[df_q_plot['acertou'] == True]
    erros_df = df_q_plot[df_q_plot['acertou'] == False]

    # Scatter plot
    if len(acertos_df) > 0:
        ax.scatter(acertos_df['posicao'], acertos_df['dificuldade'],
                  color='green', s=100, alpha=0.6, marker='o',
                  label=f'Acertos ({len(acertos_df)})', edgecolors='black', linewidth=0.5)

    if len(erros_df) > 0:
        ax.scatter(erros_df['posicao'], erros_df['dificuldade'],
                  color='red', s=100, alpha=0.6, marker='x',
                  label=f'Erros ({len(erros_df)})', linewidth=2)

    # Linha de tendência da dificuldade
    if len(df_q_plot) > 0:
        ax.plot(df_q_plot['posicao'], df_q_plot['dificuldade'],
               color='gray', alpha=0.3, linewidth=1, linestyle='--', label='Dificuldade')

        # Média de dificuldade
        media_dif = df_q_plot['dificuldade'].mean()
        ax.axhline(media_dif, color='orange', linestyle=':', linewidth=2,
                  alpha=0.7, label=f'Dif. Média: {media_dif:.2f}')

    # Título com estatística corrigida
    total_questoes = len(df_q)
    acertos_total = df_q['acertou'].sum()

    titulo_extra = ""
    if area == 'LC':
        titulo_extra = f"\n(45 questões válidas: {'Inglês' if participante['TP_LINGUA'] == 0 else 'Espanhol'} + Comuns)"

    ax.set_xlabel('Posição da Questão na Prova', fontweight='bold')
    ax.set_ylabel('Dificuldade (Parâmetro B)', fontweight='bold')
    ax.set_title(f'{areas[area]["nome"]}\n{acertos_total} acertos / {total_questoes} questões ({acertos_total/total_questoes*100:.1f}%){titulo_extra}',
                fontweight='bold', fontsize=10)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '01_acertos_vs_dificuldade_corrigido.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: {output_dir}/01_acertos_vs_dificuldade_corrigido.png")
plt.close()

# ============================================================================
# GRÁFICO 2: Taxa de Acerto por Quartil de Dificuldade
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(18, 14))
fig.suptitle('Taxa de Acerto por Nível de Dificuldade (CORRIGIDO)',
             fontsize=16, fontweight='bold')

axes = axes.flatten()

for idx, (area, df_q) in enumerate(resultados_por_area.items()):
    ax = axes[idx]

    # Taxa de acerto por quartil
    if 'quartil_dif' in df_q.columns:
        taxa_por_quartil = df_q.groupby('quartil_dif')['acertou'].agg(['sum', 'count'])
        taxa_por_quartil['taxa'] = (taxa_por_quartil['sum'] / taxa_por_quartil['count']) * 100

        # Reordenar
        ordem = ['Fácil', 'Médio', 'Difícil', 'Muito Difícil']
        taxa_por_quartil = taxa_por_quartil.reindex([o for o in ordem if o in taxa_por_quartil.index])

        if len(taxa_por_quartil) > 0:
            # Gráfico de barras
            colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
            colors = colors[:len(taxa_por_quartil)]

            bars = ax.bar(range(len(taxa_por_quartil)), taxa_por_quartil['taxa'],
                          color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

            # Adicionar valores
            for i, (bar, (nivel, row)) in enumerate(zip(bars, taxa_por_quartil.iterrows())):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%\n({int(row["sum"])}/{int(row["count"])})',
                        ha='center', va='bottom', fontweight='bold', fontsize=10)

            ax.set_xticks(range(len(taxa_por_quartil)))
            ax.set_xticklabels(taxa_por_quartil.index, fontweight='bold')
            ax.set_ylabel('Taxa de Acerto (%)', fontweight='bold')

            titulo_extra = ""
            if area == 'LC':
                titulo_extra = f"\n(Corrigido: 45 questões válidas)"

            ax.set_title(f'{areas[area]["nome"]}{titulo_extra}', fontweight='bold')
            ax.set_ylim(0, 110)
            ax.grid(True, alpha=0.3, axis='y')
            ax.axhline(50, color='red', linestyle='--', alpha=0.5, linewidth=1)

plt.tight_layout()
plt.savefig(output_dir / '03_taxa_acerto_por_dificuldade_corrigido.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: {output_dir}/03_taxa_acerto_por_dificuldade_corrigido.png")
plt.close()

# ============================================================================
# GRÁFICO 3: Histograma de Dificuldade
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(18, 14))
fig.suptitle('Distribuição de Dificuldade: Questões Acertadas vs Erradas (CORRIGIDO)',
             fontsize=16, fontweight='bold')

axes = axes.flatten()

for idx, (area, df_q) in enumerate(resultados_por_area.items()):
    ax = axes[idx]

    # Filtrar param_b válidos
    df_q_plot = df_q[df_q['dificuldade'] != 999].copy()

    acertos = df_q_plot[df_q_plot['acertou'] == True]['dificuldade']
    erros = df_q_plot[df_q_plot['acertou'] == False]['dificuldade']

    # Histogramas sobrepostos
    if len(acertos) > 0:
        ax.hist(acertos, bins=15, alpha=0.6, color='green',
               label=f'Acertos ({len(acertos)})', edgecolor='black')
    if len(erros) > 0:
        ax.hist(erros, bins=15, alpha=0.6, color='red',
               label=f'Erros ({len(erros)})', edgecolor='black')

    ax.set_xlabel('Dificuldade (Parâmetro B)', fontweight='bold')
    ax.set_ylabel('Frequência', fontweight='bold')

    titulo_extra = ""
    if area == 'LC':
        titulo_extra = f"\n(45 questões válidas)"

    ax.set_title(f'{areas[area]["nome"]}{titulo_extra}', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / '02_histograma_dificuldade_corrigido.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: {output_dir}/02_histograma_dificuldade_corrigido.png")
plt.close()

# ============================================================================
# GRÁFICO 4: Resumo Comparativo
# ============================================================================

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
fig.suptitle('Resumo da Performance TRI (CORRIGIDO)', fontsize=16, fontweight='bold')

# Preparar dados do resumo
areas_nomes = []
acertos_list = []
total_list = []
notas_list = []

for area in ['LC', 'CH', 'CN', 'MT']:
    if area in resultados_por_area:
        df_q = resultados_por_area[area]
        areas_nomes.append(areas[area]['nome'].replace(' e suas Tecnologias', ''))
        acertos_list.append(df_q['acertou'].sum())
        total_list.append(len(df_q))
        notas_list.append(participante[f'NU_NOTA_{area}'])

# Gráfico 1: Barras de acertos
x = np.arange(len(areas_nomes))
perc_acertos = [(a/t)*100 for a, t in zip(acertos_list, total_list)]

bars = ax1.bar(x, perc_acertos, color=['#f39c12', '#e74c3c', '#9b59b6', '#3498db'],
               alpha=0.7, edgecolor='black', linewidth=1.5)

# Adicionar valores
for i, (bar, acerto, total) in enumerate(zip(bars, acertos_list, total_list)):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}%\n({acerto}/{total})',
            ha='center', va='bottom', fontweight='bold', fontsize=10)

ax1.set_xticks(x)
ax1.set_xticklabels(areas_nomes, rotation=0)
ax1.set_ylabel('Taxa de Acerto (%)', fontweight='bold', fontsize=12)
ax1.set_title('Taxa de Acerto por Área\n(Linguagens corrigida: 45 questões)', fontweight='bold')
ax1.set_ylim(0, 110)
ax1.grid(True, alpha=0.3, axis='y')
ax1.axhline(75, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='75%')
ax1.legend()

# Gráfico 2: Notas
bars2 = ax2.bar(x, notas_list, color=['#f39c12', '#e74c3c', '#9b59b6', '#3498db'],
                alpha=0.7, edgecolor='black', linewidth=1.5)

for i, (bar, nota) in enumerate(zip(bars2, notas_list)):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{nota:.1f}',
            ha='center', va='bottom', fontweight='bold', fontsize=10)

ax2.set_xticks(x)
ax2.set_xticklabels(areas_nomes, rotation=0)
ax2.set_ylabel('Nota TRI', fontweight='bold', fontsize=12)
ax2.set_title('Notas TRI por Área', fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / '04_resumo_comparativo_corrigido.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: {output_dir}/04_resumo_comparativo_corrigido.png")
plt.close()

# ============================================================================
# GRÁFICO 5: Curva de Acerto ao Longo da Prova
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(18, 14))
fig.suptitle('Padrão de Acerto ao Longo da Prova (CORRIGIDO)',
             fontsize=16, fontweight='bold')

axes = axes.flatten()

for idx, (area, df_q) in enumerate(resultados_por_area.items()):
    ax = axes[idx]

    # Filtrar questões válidas e ordenar por posição
    df_q_sorted = df_q.sort_values('posicao').copy()

    # Acertos acumulados
    acertos_acum = df_q_sorted['acertou'].cumsum()
    posicoes = df_q_sorted['posicao'].values
    total_acum = np.arange(1, len(df_q_sorted) + 1)
    taxa_acum = (acertos_acum / total_acum) * 100

    # Plotar curva acumulada
    ax.plot(posicoes, taxa_acum, 'b-', linewidth=2.5, label='Taxa Acumulada')

    # Taxa final
    ax.axhline(taxa_acum.iloc[-1], color='green', linestyle='--', linewidth=2,
              alpha=0.7, label=f'Taxa Final: {taxa_acum.iloc[-1]:.1f}%')

    # Marcar questões individuais (acerto/erro)
    for pos, acertou in zip(posicoes, df_q_sorted['acertou']):
        color = 'green' if acertou else 'red'
        ax.scatter(pos, 100 if acertou else 0, c=color, s=50, alpha=0.4,
                  edgecolors='black', linewidth=0.5)

    # Destacar gap em Linguagens (posições 6-10 para Inglês)
    if area == 'LC' and participante['TP_LINGUA'] == 0:
        ax.axvspan(5.5, 10.5, alpha=0.2, color='gray',
                  label='Espanhol (não aplicável)')

    ax.set_xlabel('Posição da Questão', fontweight='bold')
    ax.set_ylabel('Taxa de Acerto Acumulada (%)', fontweight='bold')

    titulo_extra = ""
    if area == 'LC':
        titulo_extra = f"\n(45 questões válidas)"

    ax.set_title(f'{areas[area]["nome"]}{titulo_extra}', fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-5, 105)

plt.tight_layout()
plt.savefig(output_dir / '05_curva_acerto_corrigida.png', dpi=300, bbox_inches='tight')
print(f"✓ Salvo: {output_dir}/05_curva_acerto_corrigida.png")
plt.close()

print("\n[6/6] Resumo final...")

print(f"\n{'='*80}")
print("RESUMO CORRIGIDO - TODAS AS ÁREAS")
print(f"{'='*80}")
print(f"{'Área':<20} {'Acertos':<15} {'Taxa':<10} {'Nota TRI':<10}")
print(f"{'-'*80}")

for area, nome in zip(['LC', 'CH', 'CN', 'MT'], areas_nomes):
    if area in resultados_por_area:
        df_q = resultados_por_area[area]
        acertos = df_q['acertou'].sum()
        total = len(df_q)
        taxa = (acertos/total)*100
        nota = participante[f'NU_NOTA_{area}']
        print(f"{nome:<20} {acertos}/{total:<12} {taxa:<9.1f}% {nota:<10.1f}")

print(f"\n{'='*80}")
print("VISUALIZAÇÕES ATUALIZADAS GERADAS COM SUCESSO!")
print(f"{'='*80}")
print(f"\nArquivos salvos em: {output_dir}/")
print("  1. 01_acertos_vs_dificuldade_corrigido.png")
print("  2. 02_histograma_dificuldade_corrigido.png")
print("  3. 03_taxa_acerto_por_dificuldade_corrigido.png")
print("  4. 04_resumo_comparativo_corrigido.png")
print("  5. 05_curva_acerto_corrigida.png")
print("\n" + "=" * 80)
