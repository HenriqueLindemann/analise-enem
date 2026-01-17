import pandas as pd
print("Checking MT 2019...")
df = pd.read_csv('microdados_limpos/2019/ITENS_PROVA_2019.csv', sep=';', encoding='latin1')
mt = df[df['SG_AREA']=='MT']
print(f'MT 2019 total items: {len(mt)}')
print(f'Provas: {mt["CO_PROVA"].unique()}')
for p in mt['CO_PROVA'].unique():
    i = mt[mt['CO_PROVA']==p]
    print(f'Prova {p}: {len(i)} items, pos {i["CO_POSICAO"].min()}-{i["CO_POSICAO"].max()}')
