import pandas as pd
import numpy as np

def analyze_lc_2020():
    print("Loading LC 2020 Data...")
    try:
        # Load valid participants only (TP_PRESENCA_LC=1)
        df = pd.read_csv('microdados_limpos/2020/DADOS_ENEM_2020.csv', sep=';', 
                         usecols=['NU_INSCRICAO', 'TX_RESPOSTAS_LC', 'TP_LINGUA', 'CO_PROVA_LC', 'TP_PRESENCA_LC'],
                         nrows=5000) # Load enough to find both languages
        
        df = df[df['TP_PRESENCA_LC'] == 1].dropna(subset=['TX_RESPOSTAS_LC', 'TP_LINGUA'])
        print(f"Valid Candidates Loaded: {len(df)}")
        
        # Check Lengths
        df['len_resp'] = df['TX_RESPOSTAS_LC'].apply(len)
        print(f"Response Lengths: {df['len_resp'].unique()}")
        
        # Analyze English (0)
        eng = df[df['TP_LINGUA'] == 0].head(5)
        print("\n--- English (0) Samples ---")
        for idx, row in eng.iterrows():
            print(f"Resp: {row['TX_RESPOSTAS_LC']}")
            
        # Analyze Spanish (1)
        esp = df[df['TP_LINGUA'] == 1].head(5)
        print("\n--- Spanish (1) Samples ---")
        for idx, row in esp.iterrows():
            print(f"Resp: {row['TX_RESPOSTAS_LC']}")
            
        # Check if 99999 pattern exists
        print("\nChecking '99999' pattern:")
        
        # In English, if 2016 model holds: [0:5] is answers, [5:10] is 99999?
        eng_sample = eng.iloc[0]['TX_RESPOSTAS_LC']
        print(f"Eng Sample [0:5]: {eng_sample[0:5]}")
        print(f"Eng Sample [5:10]: {eng_sample[5:10]}")
        
        # In Spanish, if 2016 model holds: [0:5] is 99999, [5:10] is answers?
        if not esp.empty:
            esp_sample = esp.iloc[0]['TX_RESPOSTAS_LC']
            print(f"Esp Sample [0:5]: {esp_sample[0:5]}")
            print(f"Esp Sample [5:10]: {esp_sample[5:10]}")
        
        # Load Item Data to Cross Reference Gabarito
        print("\nLoading LC 2020 Items...")
        df_itens = pd.read_csv('microdados_limpos/2020/ITENS_PROVA_2020.csv', sep=';')
        lc_itens = df_itens[df_itens['SG_AREA'] == 'LC']
        
        # Check positions for a specific proof
        if not eng.empty:
            co_prova = int(eng.iloc[0]['CO_PROVA_LC'])
            print(f"\nAnalyzing Co_Prova {co_prova} (English User)")
            prova_itens = lc_itens[lc_itens['CO_PROVA'] == co_prova].sort_values('CO_POSICAO')
            print(f"Items Found: {len(prova_itens)}")
            print(f"Item Positions: {prova_itens['CO_POSICAO'].tolist()}")
            
            # Print Gabarito
            gabarito = "".join(prova_itens['TX_GABARITO'].tolist())
            print(f"Gabarito ({len(gabarito)}): {gabarito}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_lc_2020()
