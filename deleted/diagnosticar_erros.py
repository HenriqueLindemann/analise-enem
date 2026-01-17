"""Investigar problemas específicos de LC e CN."""
import pandas as pd
import numpy as np
from pathlib import Path

def investigar_lc(ano):
    """Investiga por que LC não tem dados suficientes."""
    print(f"\n{'='*80}")
    print(f"INVESTIGANDO LC {ano}")
    print('='*80)
    
    base_path = Path("microdados_limpos")
    dados_file = base_path / str(ano) / f"DADOS_ENEM_{ano}.csv"
    
    # Carregar primeiros 1000 registros
    df = pd.read_csv(dados_file, sep=';', nrows=1000)
    
    print(f"Total registros lidos: {len(df)}")
    
    # Verificar colunas LC
    cols_lc = [c for c in df.columns if 'LC' in c]
    print(f"Colunas LC: {cols_lc}")
    
    # Checar presença
    if 'TP_PRESENCA_LC' in df.columns:
        presentes = (df['TP_PRESENCA_LC'] == 1).sum()
        print(f"Presentes LC: {presentes}/{len(df)}")
    
    # Checar notas
    if 'NU_NOTA_LC' in df.columns:
        com_nota = (df['NU_NOTA_LC'] > 0).sum()
        print(f"Com nota LC: {com_nota}/{len(df)}")
        
        # Distribuição de notas
        notas = df[df['NU_NOTA_LC'] > 0]['NU_NOTA_LC']
        if len(notas) > 0:
            print(f"Nota min: {notas.min():.0f}, max: {notas.max():.0f}, média: {notas.mean():.0f}")
    
    # Checar respostas
    if 'TX_RESPOSTAS_LC' in df.columns:
        com_resp = df['TX_RESPOSTAS_LC'].notna().sum()
        print(f"Com respostas LC: {com_resp}/{len(df)}")
        
        # Tamanho das respostas
        if com_resp > 0:
            resp_sample = df['TX_RESPOSTAS_LC'].dropna().iloc[0]
            print(f"Tamanho resposta exemplo: {len(resp_sample)} chars")
    
    # Checar TP_LINGUA
    if 'TP_LINGUA' in df.columns:
        tp_dist = df['TP_LINGUA'].value_counts(dropna=False)
        print(f"TP_LINGUA distribuição: {tp_dist.to_dict()}")
    else:
        print("TP_LINGUA: NÃO EXISTE")
    
    # Filtrar válidos
    if all(c in df.columns for c in ['TP_PRESENCA_LC', 'NU_NOTA_LC', 'TX_RESPOSTAS_LC', 'CO_PROVA_LC']):
        validos = df[
            (df['TP_PRESENCA_LC'] == 1) & 
            (df['NU_NOTA_LC'] > 0) &
            df['TX_RESPOSTAS_LC'].notna() &
            df['CO_PROVA_LC'].notna()
        ]
        print(f"\n✅ Registros VÁLIDOS para análise: {len(validos)}/{len(df)}")
        
        if len(validos) > 0:
            # Distribuição por faixa
            bins = [0, 500, 600, 700, 800, 1000]
            validos['faixa'] = pd.cut(validos['NU_NOTA_LC'], bins=bins)
            print("\nDistribuição por faixa:")
            print(validos['faixa'].value_counts().sort_index())
    else:
        print("\n❌ Colunas essenciais faltando")


def investigar_cn_2018():
    """Investiga erro alto em CN 2018."""
    print(f"\n{'='*80}")
    print("INVESTIGANDO CN 2018 (MAE Alto)")
    print('='*80)
    
    base_path = Path("microdados_limpos")
    dados_file = base_path / str(2018) / "DADOS_ENEM_2018.csv"
    itens_file = base_path / str(2018) / "ITENS_PROVA_2018.csv"
    
    # Checar itens
    df_itens = pd.read_csv(itens_file, sep=';')
    cn_itens = df_itens[df_itens['SG_AREA'] == 'CN']
    
    print(f"Itens CN total: {len(cn_itens)}")
    print(f"Provas únicas: {cn_itens['CO_PROVA'].nunique()}")
    
    # Primeira prova
    prova = cn_itens['CO_PROVA'].iloc[0]
    cn_prova = cn_itens[cn_itens['CO_PROVA'] == prova]
    print(f"\nProva exemplo {prova}:")
    print(f"  Itens: {len(cn_prova)}")
    print(f"  Posições: {cn_prova['CO_POSICAO'].min()}-{cn_prova['CO_POSICAO'].max()}")
    
    # Checar parâmetros
    params_validos = cn_prova[
        cn_prova['NU_PARAM_A'].notna() &
        cn_prova['NU_PARAM_B'].notna() &
        cn_prova['NU_PARAM_C'].notna()
    ]
    print(f"  Itens com parâmetros válidos: {len(params_validos)}/{len(cn_prova)}")
    
    # Checar itens abandonados
    if 'IN_ITEM_ABAN' in cn_prova.columns:
        abandonados = (cn_prova['IN_ITEM_ABAN'] == 1).sum()
        print(f"  Itens abandonados: {abandonados}")
    
    # Verificar coeficientes calibrados
    import json
    coef_file = Path("tri_enem/coeficientes_data.json")
    if coef_file.exists():
        with open(coef_file, 'r') as f:
            data = json.load(f)
        
        # Procurar CN 2018
        cn_2018_keys = [k for k in data.get('por_area', {}).keys() if k.startswith('2018,CN')]
        print(f"\nCoeficientes CN 2018 em por_area: {len(cn_2018_keys)}")
        if cn_2018_keys:
            key = cn_2018_keys[0]
            coef = data['por_area'][key]
            print(f"  {key}: slope={coef['slope']:.2f}, intercept={coef['intercept']:.2f}")
        
        cn_2018_provas = [k for k in data.get('por_prova', {}).keys() if k.startswith('2018,CN,')]
        print(f"Coeficientes CN 2018 em por_prova: {len(cn_2018_provas)}")
        if cn_2018_provas:
            for key in cn_2018_provas[:3]:
                coef = data['por_prova'][key]
                print(f"  {key}: slope={coef['slope']:.2f}, intercept={coef['intercept']:.2f}, R²={coef.get('r_squared', 'N/A')}")


# Executar investigações
print("="*80)
print("DIAGNÓSTICO COMPLETO")
print("="*80)

# LC anos problemáticos
for ano in [2015, 2018, 2020]:
    investigar_lc(ano)

# CN 2018
investigar_cn_2018()

print("\n" + "="*80)
print("DIAGNÓSTICO CONCLUÍDO")
print("="*80)
