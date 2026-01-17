"""Check 2018 LC structure."""
import pandas as pd

df_itens = pd.read_csv('microdados_limpos/2018/ITENS_PROVA_2018.csv', sep=';')
lc = df_itens[df_itens['SG_AREA'] == 'LC']
prova = lc['CO_PROVA'].iloc[0]
lc_p = lc[lc['CO_PROVA'] == prova].sort_values('CO_POSICAO')

print(f'Prova {prova}: {len(lc_p)} items')
print(f'TP_LINGUA distribution:')
print(lc_p['TP_LINGUA'].value_counts(dropna=False))
print(f'Positions: {lc_p["CO_POSICAO"].min()}-{lc_p["CO_POSICAO"].max()}')

# Positions by TP_LINGUA
for tp in [0.0, 1.0]:
    pos = lc_p[lc_p['TP_LINGUA'] == tp]['CO_POSICAO'].tolist()
    print(f'TP_LINGUA={tp}: {len(pos)} items, positions {pos[:5]}...{pos[-3:]}')

comum = lc_p[lc_p['TP_LINGUA'].isna()]['CO_POSICAO'].tolist()
print(f'Common (NaN): {len(comum)} items')

# Now check a real participant response
df_dados = pd.read_csv('microdados_limpos/2018/DADOS_ENEM_2018.csv', sep=';', nrows=10)
resp = df_dados['TX_RESPOSTAS_LC'].dropna().iloc[0]
tp_lingua = df_dados['TP_LINGUA'].dropna().iloc[0]
print(f'\nParticipant example:')
print(f'  TX_RESPOSTAS_LC length: {len(resp)}')
print(f'  TP_LINGUA: {tp_lingua}')
print(f'  First 10 chars: {resp[:10]}')
