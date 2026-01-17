"""
Exploração sistemática de TODAS as áreas (CN, CH, LC, MT) ao longo dos anos (2020-2023).
Objetivo: Verificar estabilidade dos coeficientes de equalização.
"""
import pandas as pd
import numpy as np
from scipy import stats
import os
import sys
sys.path.insert(0, '.')
from tri_enem import CalculadorTRI

def calibrar_amostra(ano, area, n_amostras=300):
    path = f'microdados/{ano}/MICRODADOS_ENEM_{ano}.csv'
    if not os.path.exists(path):
        return None
    
    # Colunas
    cols = [
        f'TP_PRESENCA_{area}', 
        f'CO_PROVA_{area}', 
        f'NU_NOTA_{area}', 
        f'TX_RESPOSTAS_{area}'
    ]
    if area == 'LC':
        cols.append('TP_LINGUA')
        
    try:
        df = pd.read_csv(path, encoding='latin1', sep=';', nrows=15000, usecols=cols)
    except:
        return None
        
    # Filtrar
    df = df[(df[f'TP_PRESENCA_{area}'] == 1) & (df[f'NU_NOTA_{area}'] > 0)].dropna()
    
    if df.empty:
        return None
        
    # Pegar a prova mais comum
    prova = int(df[f'CO_PROVA_{area}'].mode()[0])
    df_prova = df[df[f'CO_PROVA_{area}'] == prova].head(n_amostras)
    
    # Calcular
    calc = CalculadorTRI('microdados')
    try:
        itens = calc.carregar_itens(ano, area, prova)
    except:
        return {'erro': 'Itens não encontrados'}
        
    # Para LC, a questão da língua estrangeira
    # O calculador ignora a lingua e tenta calcular com o que tem.
    # Vamos ver como se comporta.
    
    dados = []
    for _, row in df_prova.iterrows():
        # Converter respostas
        # Nota: converter_respostas assume ordem dos itens carregados
        respostas_bin = calc.converter_respostas(row[f'TX_RESPOSTAS_{area}'], itens)
        theta = calc.estimar_theta_eap(respostas_bin, itens)
        dados.append({'theta': theta, 'nota': row[f'NU_NOTA_{area}']})
        
    if not dados:
        return {'erro': 'Sem dados calculados'}
        
    df_cal = pd.DataFrame(dados)
    
    # Regressão
    slope, intercept, r, _, _ = stats.linregress(df_cal['theta'], df_cal['nota'])
    
    # Validar MAE
    pred = slope * df_cal['theta'] + intercept
    mae = (df_cal['nota'] - pred).abs().mean()
    
    return {
        'ano': ano,
        'area': area,
        'prova': prova,
        'slope': slope,
        'intercept': intercept,
        'r2': r**2,
        'mae': mae,
        'n': len(df_cal)
    }

print("="*80)
print(f"{'EXPLORAÇÃO DE COEFICIENTES POR ÁREA E ANO':^80}")
print("="*80)
print(f"{'Area':^4} | {'Ano':^4} | {'Prova':^6} | {'Slope':^10} | {'Intercept':^10} | {'R²':^8} | {'MAE':^6}")
print("-" * 80)

resultados = {}

for area in ['CN', 'CH', 'LC', 'MT']:
    resultados[area] = []
    for ano in [2020, 2021, 2022, 2023]:
        res = calibrar_amostra(ano, area)
        if res and 'erro' not in res:
            resultados[area].append(res)
            print(f"{area:^4} | {ano:^4} | {res['prova']:^6} | {res['slope']:^10.4f} | {res['intercept']:^10.2f} | {res['r2']:^8.4f} | {res['mae']:^6.2f}")
        elif res:
             print(f"{area:^4} | {ano:^4} | {'ERRO':^6} | {res['erro']}")
        else:
             print(f"{area:^4} | {ano:^4} | {'---':^6} | (Arquivo não encontrado)")

print("\n" + "="*80)
print("RESUMO DA ESTABILIDADE")
print("="*80)

for area, lista in resultados.items():
    if not lista:
        continue
    slopes = [r['slope'] for r in lista]
    intercepts = [r['intercept'] for r in lista]
    
    print(f"\nÁREA: {area}")
    print(f"  Slope Médio:      {np.mean(slopes):.4f} +/- {np.std(slopes):.4f}")
    print(f"  Intercept Médio:  {np.mean(intercepts):.2f} +/- {np.std(intercepts):.2f}")
    
    # Verificar se é estável (cv < 1%)
    cv = np.std(slopes) / np.mean(slopes)
    status = "ESTÁVEL" if cv < 0.01 else "VARIÁVEL"
    print(f"  Status: {status} (CV={cv*100:.2f}%)")
