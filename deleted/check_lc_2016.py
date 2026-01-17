import pandas as pd
print("Checking LC 2016...")

# 1. Check Items
df = pd.read_csv('microdados_limpos/2016/ITENS_PROVA_2016.csv', sep=';', encoding='latin1')
lc = df[df['SG_AREA']=='LC']
p = lc['CO_PROVA'].iloc[0]
lc_p = lc[lc['CO_PROVA']==p].sort_values('CO_POSICAO')

print(f"Items: {len(lc_p)}")
print(f"Positions: {lc_p['CO_POSICAO'].min()}-{lc_p['CO_POSICAO'].max()}")
print(f"TP_LINGUA: {lc_p['TP_LINGUA'].value_counts(dropna=False).to_dict()}")

# Check duplicated positions
dups = lc_p[lc_p.duplicated('CO_POSICAO', keep=False)]
if not dups.empty:
    print(f"\nDuplicated Positions: {dups['CO_POSICAO'].unique()}")
    print("Example Pos 1:")
    print(lc_p[lc_p['CO_POSICAO']==1][['CO_POSICAO', 'TP_LINGUA', 'CO_ITEM']])

# 2. Check Responses
print("\nChecking Responses...")
df_dados = pd.read_csv('microdados_limpos/2016/DADOS_ENEM_2016.csv', sep=';', nrows=20)
cols = ['TP_LINGUA', 'TX_RESPOSTAS_LC', 'CO_PROVA_LC', 'NU_NOTA_LC']
df_dados = df_dados[cols].dropna()

for _, row in df_dados.head(5).iterrows():
    print(f"TP_LINGUA={row['TP_LINGUA']} | Len={len(row['TX_RESPOSTAS_LC'])} | Resp={row['TX_RESPOSTAS_LC']}")
