"""Check 2017 and 2013 responses."""
import pandas as pd

def check_year(ano):
    print(f"\n{'='*40}")
    print(f"CHECKING {ano}")
    print('='*40)
    
    df = pd.read_csv(f'microdados_limpos/{ano}/DADOS_ENEM_{ano}.csv', sep=';', nrows=10)
    
    for area in ['MT', 'CN', 'CH', 'LC']:
        col = f'TX_RESPOSTAS_{area}'
        if col in df.columns:
            resp = df[col].dropna().iloc[0]
            print(f"{area}: len={len(resp)}")
        
        # Check items for a specific prova
        p_col = f'CO_PROVA_{area}'
        if p_col in df.columns:
            prova = df[p_col].iloc[0]
            print(f"  Prova: {prova}")

check_year(2017)
check_year(2013)
