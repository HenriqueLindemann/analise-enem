"""
Teste final do módulo atualizado

Execute a partir da raiz do projeto:
    python tests/teste_final.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import CalculadorTRI
import pandas as pd
import numpy as np

calc = CalculadorTRI('microdados_limpos')

# Testar nota alta
df = pd.read_csv('microdados_limpos/2023/DADOS_ENEM_2023.csv', encoding='latin1', sep=';', nrows=30000)
df_high = df[(df['TP_PRESENCA_MT'] == 1) & (df['NU_NOTA_MT'] >= 850)].head(10)

print("TESTE: Notas 850+ com 80 pontos de quadratura")
print("=" * 55)
print(f"{'Nota Real':>10} | {'Nota Calc':>10} | {'Erro':>7} | {'Acertos':>7}")
print("-" * 55)

erros = []
for _, row in df_high.iterrows():
    prova = int(row['CO_PROVA_MT'])
    resultado = calc.calcular_nota(2023, 'MT', prova, row['TX_RESPOSTAS_MT'])
    erro = row['NU_NOTA_MT'] - resultado['nota']
    erros.append(erro)
    print(f"{row['NU_NOTA_MT']:>10.1f} | {resultado['nota']:>10.1f} | {erro:>+7.1f} | {int(resultado['acertos']):>7}")

print("-" * 55)
print(f"MAE: {np.mean(np.abs(erros)):.2f}")
print(f"Max erro: {np.max(np.abs(erros)):.2f}")
