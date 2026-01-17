"""Investigar por que certos anos têm erros altos."""
import json
import pandas as pd
from pathlib import Path

# Carregar coeficientes
coef_file = Path('tri_enem/coeficientes_data.json')
with open(coef_file, 'r') as f:
    coef_data = json.load(f)

print("="*80)
print("ANÁLISE DE COEFICIENTES CALIBRADOS")
print("="*80)

# Organizar por ano
anos_com_coef = {}
for key in coef_data['por_area'].keys():
    ano, area = key.split(',')
    if ano not in anos_com_coef:
        anos_com_coef[ano] = []
    anos_com_coef[ano].append(area)

print("\nAnos com coeficientes:")
for ano in sorted(anos_com_coef.keys()):
    areas = sorted(anos_com_coef[ano])
    print(f"  {ano}: {', '.join(areas)}")

# Anos problemáticos vs calibrados
anos_problematicos = [2011, 2013, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
anos_bons = [2009, 2010, 2012, 2022, 2023, 2024]

print(f"\n{'='*80}")
print("COMPARAÇÃO: Anos Bons vs Problemáticos")
print('='*80)

for ano in anos_problematicos:
    ano_str = str(ano)
    if ano_str in anos_com_coef:
        areas = anos_com_coef[ano_str]
        print(f"❌ {ano} PROBLEMÁTICO mas TEM coef: {areas}")
    else:
        print(f"❌ {ano} PROBLEMÁTICO e SEM coef")

print()
for ano in anos_bons:
    ano_str = str(ano)
    if ano_str in anos_com_coef:
        areas = anos_com_coef[ano_str]
        print(f"✅ {ano} BOM e TEM coef: {areas}")
    else:
        print(f"✅ {ano} BOM mas SEM coef")

# Investigar um ano problemático em detalhe
print(f"\n{'='*80}")
print("INVESTIGAÇÃO DETALHADA: 2015 CN (deveria ser bom)")
print('='*80)

ano_teste = 2015
for area in ['CN', 'LC']:
    key = f"{ano_teste},{area}"
    if key in coef_data['por_area']:
        coef = coef_data['por_area'][key]
        print(f"\n{area} {ano_teste}:")
        print(f"  Slope: {coef['slope']:.2f}")
        print(f"  Intercept: {coef['intercept']:.2f}")
        print(f"  N provas calibradas: {coef.get('n_provas', '?')}")
    else:
        print(f"\n{area} {ano_teste}: SEM COEFICIENTES")

# Testar cálculo manual
print(f"\n{'='*80}")
print("TESTE MANUAL: Carregando coeficiente via obter_coeficiente()")
print('='*80)

from tri_enem import obter_coeficiente

for ano in [2015, 2018, 2023]:
    for area in ['MT', 'CN', 'LC']:
        slope, intercept = obter_coeficiente(ano, area, None)
        print(f"{ano} {area}: slope={slope:.2f}, intercept={intercept:.2f}")
