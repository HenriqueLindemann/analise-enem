"""Check item positions for all areas."""
import pandas as pd
from pathlib import Path

print("Checking item positions for ALL areas...")

for ano in range(2009, 2025):
    try:
        f = f'microdados_limpos/{ano}/ITENS_PROVA_{ano}.csv'
        if not Path(f).exists():
            continue
            
        df = pd.read_csv(f, sep=';', encoding='latin1')
        
        print(f"\nANO {ano}")
        for area in ['MT', 'CN', 'CH', 'LC']:
            itens_area = df[df['SG_AREA'] == area]
            if len(itens_area) == 0:
                print(f"  {area}: SEM ITENS")
                continue
                
            # Pegar primeira prova como exemplo
            prova = itens_area['CO_PROVA'].iloc[0]
            itens_prova = itens_area[itens_area['CO_PROVA'] == prova]
            
            min_pos = itens_prova['CO_POSICAO'].min()
            max_pos = itens_prova['CO_POSICAO'].max()
            n_itens = len(itens_prova)
            
            print(f"  {area}: {n_itens} itens, pos {min_pos}-{max_pos}")
            
    except Exception as e:
        print(f'{ano}: error {e}')
