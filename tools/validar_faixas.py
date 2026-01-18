"""Validação do cálculo TRI em diferentes faixas de nota."""

import pandas as pd
import sys
sys.path.insert(0, 'src')
from tri_enem import CalculadorTRI

calc = CalculadorTRI()

# Carregar dados
dados = pd.read_csv('microdados_limpos/2024/DADOS_ENEM_2024.csv', sep=';', nrows=200000)

# Filtrar por faixas de nota em MT
faixas = [
    ('Muito Baixa', 300, 400),
    ('Baixa', 400, 500),
    ('Media', 500, 600),
    ('Alta', 600, 700),
    ('Muito Alta', 700, 800),
    ('Excelente', 800, 1000),
]

print('Validacao em diferentes faixas de nota (MT):')
print('=' * 70)
print(f'{"Faixa":<15} {"Oficial":>10} {"Calculada":>10} {"Erro":>10} {"Acertos":>10}')
print('-' * 70)

for nome, min_nota, max_nota in faixas:
    mask = (
        (dados['NU_NOTA_MT'].notna()) & 
        (dados['NU_NOTA_MT'] >= min_nota) & 
        (dados['NU_NOTA_MT'] < max_nota) &
        (dados['CO_PROVA_MT'].isin([1407, 1408, 1409, 1410]))
    )
    
    if mask.sum() == 0:
        continue
    
    amostra = dados[mask].head(1)
    
    for _, row in amostra.iterrows():
        prova = int(row['CO_PROVA_MT'])
        respostas = row['TX_RESPOSTAS_MT']
        oficial = row['NU_NOTA_MT']
        
        resultado = calc.calcular_nota(2024, 'MT', prova, respostas)
        calculada = resultado['nota']
        erro = calculada - oficial
        
        print(f'{nome:<15} {oficial:>10.1f} {calculada:>10.1f} {erro:>+10.1f} {resultado["acertos"]:>7}/{resultado["total_itens"]}')

print('-' * 70)
print('Validacao OK se todos os erros sao < 2 pontos')
