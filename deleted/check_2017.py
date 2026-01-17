import pandas as pd
df = pd.read_csv('microdados_limpos/2017/ITENS_PROVA_2017.csv', sep=';')
lc = df[df['SG_AREA']=='LC']
prova = lc['CO_PROVA'].iloc[0]
lc_p = lc[lc['CO_PROVA']==prova].sort_values('CO_POSICAO')
print(f'2017 LC items: {len(lc_p)}')
print(f'Positions: {lc_p["CO_POSICAO"].min()}-{lc_p["CO_POSICAO"].max()}')
print(f'TP_LINGUA distribution: {lc_p["TP_LINGUA"].value_counts(dropna=False).to_dict()}')

# Check responses
df_dados = pd.read_csv('microdados_limpos/2017/DADOS_ENEM_2017.csv', sep=';', nrows=10)
resp = df_dados['TX_RESPOSTAS_LC'].dropna().iloc[0]
print(f'TX_RESPOSTAS length: {len(resp)}')
