#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICAÇÃO RIGOROSA DA ANÁLISE TRI
Validando correspondência entre respostas, gabaritos e parâmetros TRI
"""

import pandas as pd
import numpy as np
from pathlib import Path

# NOTAS DO PARTICIPANTE
NOTAS_ALVO = {
    'NU_NOTA_LC': 677.5,
    'NU_NOTA_CH': 749.9,
    'NU_NOTA_CN': 752.8,
    'NU_NOTA_MT': 916.4,
    'NU_NOTA_REDACAO': 940.0
}

print("=" * 100)
print("VERIFICAÇÃO RIGOROSA DA ANÁLISE TRI")
print("=" * 100)

# Caminhos
base_path = Path(__file__).parent
dados_path = base_path / "DADOS" / "MICRODADOS_ENEM_2021.csv"
itens_path = base_path / "DADOS" / "ITENS_PROVA_2021.csv"

print("\n[1/5] Carregando dados...")

colunas = [
    'NU_INSCRICAO',
    'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT',
    'TX_RESPOSTAS_CN', 'TX_RESPOSTAS_CH', 'TX_RESPOSTAS_LC', 'TX_RESPOSTAS_MT',
    'TX_GABARITO_CN', 'TX_GABARITO_CH', 'TX_GABARITO_LC', 'TX_GABARITO_MT',
    'CO_PROVA_CN', 'CO_PROVA_CH', 'CO_PROVA_LC', 'CO_PROVA_MT',
]

df = pd.read_csv(dados_path, sep=';', encoding='latin-1', usecols=colunas, low_memory=False)

# Buscar participante
tolerancia = 0.1
mask = (
    (df['NU_NOTA_LC'].between(NOTAS_ALVO['NU_NOTA_LC'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_LC'] + tolerancia)) &
    (df['NU_NOTA_CH'].between(NOTAS_ALVO['NU_NOTA_CH'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_CH'] + tolerancia)) &
    (df['NU_NOTA_CN'].between(NOTAS_ALVO['NU_NOTA_CN'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_CN'] + tolerancia)) &
    (df['NU_NOTA_MT'].between(NOTAS_ALVO['NU_NOTA_MT'] - tolerancia,
                               NOTAS_ALVO['NU_NOTA_MT'] + tolerancia))
)

participante = df[mask].iloc[0]
print(f"✓ Participante encontrado: {participante['NU_INSCRICAO']}")

# Carregar itens
df_itens = pd.read_csv(itens_path, sep=';', encoding='latin-1')
print(f"✓ Itens TRI carregados: {len(df_itens):,}")

print("\n[2/5] Verificando estrutura dos dados de ITENS...")

print("\nEstrutura do arquivo ITENS_PROVA_2021.csv:")
print(df_itens.head(10))

print("\nColunas disponíveis:")
print(df_itens.columns.tolist())

print("\nÁreas disponíveis:")
print(df_itens['SG_AREA'].unique())

print("\nCódigos de prova únicos por área:")
for area in ['LC', 'CH', 'CN', 'MT']:
    codigos = df_itens[df_itens['SG_AREA'] == area]['CO_PROVA'].unique()
    print(f"  {area}: {sorted(codigos)}")

print("\n[3/5] Verificando correspondência DETALHADA para MATEMÁTICA...")

area = 'MT'
codigo_prova = participante['CO_PROVA_MT']
respostas = str(participante['TX_RESPOSTAS_MT'])
gabarito = str(participante['TX_GABARITO_MT'])

print(f"\nCódigo da prova do participante: {codigo_prova}")
print(f"Quantidade de caracteres nas respostas: {len(respostas)}")
print(f"Quantidade de caracteres no gabarito: {len(gabarito)}")

# Buscar itens desta prova
itens_prova = df_itens[
    (df_itens['SG_AREA'] == area) &
    (df_itens['CO_PROVA'] == codigo_prova)
].copy()

print(f"\nItens TRI encontrados para esta prova: {len(itens_prova)}")

if len(itens_prova) == 0:
    print("⚠️ ERRO: Nenhum item TRI encontrado para esta prova!")
else:
    # Ordenar por posição
    itens_prova = itens_prova.sort_values('CO_POSICAO').reset_index(drop=True)

    print(f"\n{'='*100}")
    print("VERIFICAÇÃO DETALHADA - PRIMEIRAS 10 QUESTÕES DE MATEMÁTICA")
    print(f"{'='*100}")
    print(f"{'Pos':<5} {'Resp':<6} {'Gab':<6} {'OK?':<6} {'Item':<10} {'Gab_TRI':<10} "
          f"{'Match?':<8} {'Param_A':<10} {'Param_B':<10} {'Param_C':<10}")
    print(f"{'-'*100}")

    erros_encontrados = []

    for i in range(min(10, len(respostas), len(itens_prova))):
        resp_participante = respostas[i]
        gab_participante = gabarito[i]

        item = itens_prova.iloc[i]
        gab_tri = item['TX_GABARITO']

        acertou = (resp_participante == gab_participante and resp_participante != '.')
        match_gabarito = (gab_participante == gab_tri)

        # Detectar problemas
        problema = ""
        if not match_gabarito:
            problema = "⚠️ GABARITO NÃO CORRESPONDE!"
            erros_encontrados.append(f"Questão {i+1}: Gabarito participante ({gab_participante}) != Gabarito TRI ({gab_tri})")

        print(f"{i+1:<5} {resp_participante:<6} {gab_participante:<6} "
              f"{'✓' if acertou else '✗':<6} {item['CO_ITEM']:<10} {gab_tri:<10} "
              f"{'✓' if match_gabarito else '✗':<8} "
              f"{item['NU_PARAM_A']:<10.3f} {item['NU_PARAM_B']:<10.3f} {item['NU_PARAM_C']:<10.3f} "
              f"{problema}")

    if erros_encontrados:
        print(f"\n⚠️ PROBLEMAS DETECTADOS:")
        for erro in erros_encontrados:
            print(f"  - {erro}")
    else:
        print(f"\n✓ Primeiras 10 questões: correspondência CORRETA entre gabaritos!")

print("\n[4/5] Verificando interpretação dos parâmetros TRI...")

print("\nParâmetros da TRI (Modelo de 3 Parâmetros - ML3):")
print("  - Parâmetro A: Discriminação (poder de discriminar habilidades)")
print("  - Parâmetro B: Dificuldade (quanto MAIOR, mais DIFÍCIL)")
print("  - Parâmetro C: Acerto ao acaso (probabilidade de acertar chutando)")

print("\nVerificando range dos parâmetros B por área:")
for area in ['LC', 'CH', 'CN', 'MT']:
    params_b = df_itens[df_itens['SG_AREA'] == area]['NU_PARAM_B']
    print(f"  {area}: min={params_b.min():.3f}, max={params_b.max():.3f}, "
          f"média={params_b.mean():.3f}, mediana={params_b.median():.3f}")

print("\n[5/5] Análise de TODAS as áreas do participante...")

areas = {
    'MT': {'col_resp': 'TX_RESPOSTAS_MT', 'col_gab': 'TX_GABARITO_MT',
           'col_prova': 'CO_PROVA_MT', 'nota': 'NU_NOTA_MT'},
    'CN': {'col_resp': 'TX_RESPOSTAS_CN', 'col_gab': 'TX_GABARITO_CN',
           'col_prova': 'CO_PROVA_CN', 'nota': 'NU_NOTA_CN'},
    'CH': {'col_resp': 'TX_RESPOSTAS_CH', 'col_gab': 'TX_GABARITO_CH',
           'col_prova': 'CO_PROVA_CH', 'nota': 'NU_NOTA_CH'},
    'LC': {'col_resp': 'TX_RESPOSTAS_LC', 'col_gab': 'TX_GABARITO_LC',
           'col_prova': 'CO_PROVA_LC', 'nota': 'NU_NOTA_LC'},
}

resumo_geral = []

for area, info in areas.items():
    codigo_prova = participante[info['col_prova']]
    respostas = str(participante[info['col_resp']])
    gabarito = str(participante[info['col_gab']])
    nota = participante[info['nota']]

    # Buscar itens
    itens_prova = df_itens[
        (df_itens['SG_AREA'] == area) &
        (df_itens['CO_PROVA'] == codigo_prova)
    ].copy().sort_values('CO_POSICAO').reset_index(drop=True)

    if len(itens_prova) == 0:
        continue

    # Análise completa
    total_questoes = len(respostas)
    acertos = 0
    erros_faceis = 0  # Param B < média
    acertos_dificeis = 0  # Param B > percentil 75

    param_b_medio = itens_prova['NU_PARAM_B'].mean()
    param_b_p75 = itens_prova['NU_PARAM_B'].quantile(0.75)

    for i in range(min(len(respostas), len(itens_prova))):
        resp = respostas[i]
        gab = gabarito[i]

        if i < len(itens_prova):
            param_b = itens_prova.iloc[i]['NU_PARAM_B']

            acertou = (resp == gab and resp != '.')
            if acertou:
                acertos += 1
                if param_b > param_b_p75:
                    acertos_dificeis += 1
            else:
                if param_b < param_b_medio:
                    erros_faceis += 1

    perc_acertos = (acertos / total_questoes) * 100

    resumo_geral.append({
        'Área': area,
        'Nota': nota,
        'Acertos': acertos,
        'Total': total_questoes,
        'Perc': perc_acertos,
        'Erros_Fáceis': erros_faceis,
        'Acertos_Difíceis': acertos_dificeis,
        'Param_B_Médio': param_b_medio
    })

print(f"\n{'='*100}")
print("RESUMO GERAL - VALIDAÇÃO DA ANÁLISE")
print(f"{'='*100}")
print(f"{'Área':<6} {'Nota':<8} {'Acertos':<10} {'Taxa':<8} {'Erros_Fáceis':<15} "
      f"{'Acertos_Difíceis':<18} {'Param_B_Médio':<15}")
print(f"{'-'*100}")

for row in resumo_geral:
    print(f"{row['Área']:<6} {row['Nota']:<8.1f} {row['Acertos']}/{row['Total']:<6} "
          f"{row['Perc']:<7.1f}% {row['Erros_Fáceis']:<15} "
          f"{row['Acertos_Difíceis']:<18} {row['Param_B_Médio']:<15.3f}")

print(f"\n{'='*100}")
print("INTERPRETAÇÃO:")
print(f"{'='*100}")

print("\n✓ VERIFICAÇÕES REALIZADAS:")
print("  1. Correspondência entre respostas do participante e gabarito TRI")
print("  2. Ordem das questões (CO_POSICAO) vs ordem nas strings de resposta")
print("  3. Interpretação dos parâmetros TRI (A, B, C)")
print("  4. Análise de padrão de acertos por dificuldade")

print("\n⚠️ PONTOS DE ATENÇÃO:")
print("  - A string TX_RESPOSTAS tem 45-50 caracteres (uma resposta por questão)")
print("  - TX_GABARITO do participante DEVE corresponder ao TX_GABARITO dos itens TRI")
print("  - CO_POSICAO indica a posição da questão na prova")
print("  - Parâmetro B: valores MAIORES = questões MAIS DIFÍCEIS")

print("\n📊 ANÁLISE DO PADRÃO:")
for row in resumo_geral:
    area = row['Área']
    nota = row['Nota']

    # Análise qualitativa
    if row['Erros_Fáceis'] == 0 and row['Acertos_Difíceis'] > 5:
        padrao = "EXCELENTE - Sem erros fáceis + muitos acertos difíceis"
    elif row['Erros_Fáceis'] <= 2 and row['Acertos_Difíceis'] > 3:
        padrao = "MUITO BOM - Poucos erros fáceis + bons acertos difíceis"
    elif row['Erros_Fáceis'] > 5:
        padrao = "⚠️ ATENÇÃO - Muitos erros em questões fáceis (pode indicar problema)"
    else:
        padrao = "BOM - Padrão coerente"

    print(f"  {area} (Nota {nota:.1f}): {padrao}")

print(f"\n{'='*100}")
print("CONCLUSÃO DA VERIFICAÇÃO")
print(f"{'='*100}")

# Calcular correlação entre acertos e nota
notas_list = [r['Nota'] for r in resumo_geral]
acertos_list = [r['Perc'] for r in resumo_geral]

corr = np.corrcoef(notas_list, acertos_list)[0, 1]

print(f"\nCorrelação entre % acertos e nota TRI: {corr:.3f}")
print("\nInterpretação:")
if corr > 0.9:
    print("  ✓ Correlação ALTA - Mas nota TRI NÃO é simples % de acertos!")
    print("  ✓ TRI considera QUAL questão foi acertada, não só QUANTAS")
else:
    print("  ⚠️ Correlação não tão alta - Esperado, pois TRI é mais complexo")

print("\n✅ VALIDAÇÃO CONCLUÍDA!")
print("=" * 100)
