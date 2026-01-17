"""
Test LC 50-char filtering.

Execute a partir da raiz do projeto:
    python tests/test_lc_50char.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import SimuladorNota
import pandas as pd

sim = SimuladorNota('microdados_limpos')

# Test 2018 LC
df = pd.read_csv('microdados_limpos/2018/DADOS_ENEM_2018.csv', sep=';', nrows=20)
row = df[(df['TP_PRESENCA_LC'] == 1) & (df['NU_NOTA_LC'] > 0)].iloc[0]

print('='*60)
print('TEST LC 2018')
print('='*60)
print(f'TX_RESPOSTAS_LC length: {len(row["TX_RESPOSTAS_LC"])}')
print(f'TP_LINGUA: {row["TP_LINGUA"]}')
print(f'Nota real: {row["NU_NOTA_LC"]}')

# Test calculation
try:
    lang = 'ingles' if int(row['TP_LINGUA']) == 0 else 'espanhol'
    resultado = sim.calcular('LC', 2018, row['TX_RESPOSTAS_LC'], lingua=lang, co_prova=int(row['CO_PROVA_LC']))
    erro = abs(row['NU_NOTA_LC'] - resultado.nota)
    print(f'Nota calculada: {resultado.nota:.1f}')
    print(f'Erro: {erro:.2f}')
    status = '✅ SUCCESS' if erro < 5.0 else '⚠️ WARNING'
    print(status)
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
