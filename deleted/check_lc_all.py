import pandas as pd
from pathlib import Path

print("Checking LC positions...")
for ano in range(2010, 2025):
    try:
        f = f'microdados_limpos/{ano}/ITENS_PROVA_{ano}.csv'
        if not Path(f).exists():
            continue
            
        df = pd.read_csv(f, sep=';', encoding='latin1')
        lc = df[df['SG_AREA']=='LC']
        if len(lc) > 0:
            p = lc['CO_PROVA'].iloc[0]
            lc_p = lc[lc['CO_PROVA']==p]
            min_pos = lc_p['CO_POSICAO'].min()
            max_pos = lc_p['CO_POSICAO'].max()
            print(f'{ano}: pos {min_pos}-{max_pos} (items: {len(lc_p)})')
            
            # Check if 91-135 or 1-45/50
            if min_pos == 1:
                print(f"  -> USA POSIÇÃO 1-{max_pos}")
            else:
                print(f"  -> USA POSIÇÃO {min_pos}-{max_pos}")
                
    except Exception as e:
        print(f'{ano}: error {e}')
