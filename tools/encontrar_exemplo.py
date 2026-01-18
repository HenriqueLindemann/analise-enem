"""Script para encontrar um participante exemplo para validação."""

import pandas as pd

# Usar dados limpos
dados = pd.read_csv('microdados_limpos/2024/DADOS_ENEM_2024.csv', sep=';', nrows=100000)

# Filtrar: notas altas em todas areas
mask = (
    (dados['NU_NOTA_MT'].notna()) & 
    (dados['NU_NOTA_CN'].notna()) & 
    (dados['NU_NOTA_CH'].notna()) & 
    (dados['NU_NOTA_LC'].notna()) &
    (dados['NU_NOTA_MT'] > 700) &
    (dados['NU_NOTA_CN'] > 600) &
    (dados['NU_NOTA_CH'] > 600) &
    (dados['NU_NOTA_LC'] > 600)
)
print(f'Encontrados com notas altas: {mask.sum()}')

amostra = dados[mask].head(1)
for _, row in amostra.iterrows():
    print()
    print('PARTICIPANTE ENCONTRADO:')
    print('=' * 60)
    print(f"MT: Prova={int(row['CO_PROVA_MT'])}, Nota={row['NU_NOTA_MT']:.1f}")
    print(f"    Respostas: {row['TX_RESPOSTAS_MT']}")
    print()
    print(f"CN: Prova={int(row['CO_PROVA_CN'])}, Nota={row['NU_NOTA_CN']:.1f}")
    print(f"    Respostas: {row['TX_RESPOSTAS_CN']}")
    print()
    print(f"CH: Prova={int(row['CO_PROVA_CH'])}, Nota={row['NU_NOTA_CH']:.1f}")
    print(f"    Respostas: {row['TX_RESPOSTAS_CH']}")
    print()
    print(f"LC: Prova={int(row['CO_PROVA_LC'])}, Nota={row['NU_NOTA_LC']:.1f}, TP_LINGUA={int(row['TP_LINGUA'])}")
    print(f"    Respostas: {row['TX_RESPOSTAS_LC']}")
    
    lingua = 'ingles' if row['TP_LINGUA'] == 0 else 'espanhol'
    
    print()
    print('CODIGO PYTHON PARA EXEMPLO:')
    print('=' * 60)
    print(f"""
PARTICIPANTE = {{
    'MT': {{
        'prova': {int(row['CO_PROVA_MT'])},
        'nota_oficial': {row['NU_NOTA_MT']:.1f},
        'respostas': '{row['TX_RESPOSTAS_MT']}',
    }},
    'CN': {{
        'prova': {int(row['CO_PROVA_CN'])},
        'nota_oficial': {row['NU_NOTA_CN']:.1f},
        'respostas': '{row['TX_RESPOSTAS_CN']}',
    }},
    'CH': {{
        'prova': {int(row['CO_PROVA_CH'])},
        'nota_oficial': {row['NU_NOTA_CH']:.1f},
        'respostas': '{row['TX_RESPOSTAS_CH']}',
    }},
    'LC': {{
        'prova': {int(row['CO_PROVA_LC'])},
        'nota_oficial': {row['NU_NOTA_LC']:.1f},
        'respostas': '{row['TX_RESPOSTAS_LC']}',
        'lingua': '{lingua}',  # TP_LINGUA = {int(row['TP_LINGUA'])}
    }},
}}
""")
