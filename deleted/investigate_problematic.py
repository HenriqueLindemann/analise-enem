import pandas as pd
from tri_enem.calculador import CalculadorTRI
from tri_enem.calibrador import Calibrador
import numpy as np

def check_lc_2020():
    print("\n=== Investigating LC 2020 ===")
    try:
        df_itens = pd.read_csv('microdados_limpos/2020/ITENS_PROVA_2020.csv', sep=';')
        lc_itens = df_itens[df_itens['SG_AREA'] == 'LC']
        print(f"LC Items Count: {len(lc_itens)}")
        print(f"LC Items Positions: {lc_itens['CO_POSICAO'].unique()}")
        print(f"LC Items CO_ITEM sample: {lc_itens['CO_ITEM'].head().tolist()}")
        
        df_dados = pd.read_csv('microdados_limpos/2020/DADOS_ENEM_2020.csv', sep=';', usecols=['TX_RESPOSTAS_LC', 'TP_LINGUA', 'CO_PROVA_LC'], nrows=100)
        print(f"Response Length: {len(df_dados['TX_RESPOSTAS_LC'].iloc[0])}")
        print("Sample Responses (TP_LINGUA=0 English):")
        print(df_dados[df_dados['TP_LINGUA']==0][['TX_RESPOSTAS_LC']].head(3))
        print("Sample Responses (TP_LINGUA=1 Spanish):")
        print(df_dados[df_dados['TP_LINGUA']==1][['TX_RESPOSTAS_LC']].head(3))
        
        # Test calibration for one LC proof with debug
        print("\nRunning quick calibration for LC 2020 Prova 691 (10 samples)...")
        cal = Calibrador('microdados_limpos')
        cal.calibrar_area_todas_provas(2020, 'LC', 20, verbose=True)
        
    except Exception as e:
        print(f"Error checking LC 2020: {e}")

def test_quadrature_mt_2019():
    print("\n=== Testing Quadrature on MT 2019 (Prova 515) ===")
    
    # We need to monkeypatch or modify N_QUADRATURA
    # Since it's a class attribute, we can modify it on the class
    
    quadratures = [40, 80, 120]
    
    for q in quadratures:
        print(f"\n--- Testing N_QUADRATURA = {q} ---")
        CalculadorTRI.N_QUADRATURA = q
        
        # Prova 515 MT 2019
        cal = Calibrador('microdados_limpos')
        c = cal # Alias
        c.calibrar_prova(2019, 'MT', 515, n_amostras=200, verbose=True)

if __name__ == "__main__":
    check_lc_2020()
    test_quadrature_mt_2019()
