import json
from pathlib import Path

def inspect():
    path = Path('tri_enem/coeficientes_data.json')
    if not path.exists():
        print("Arquivo JSON não encontrado.")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return

    print(f"Total coeficientes por area: {len(data['por_area'])}")
    
    anos_lc = []
    
    print("\nResumo LC (2015-2021):")
    for ano in range(2015, 2022):
        if ano == 2017: continue
        
        key = f"{ano},LC"
        if key in data['por_area']:
            # Média dos coeficientes
            provas = [k for k in data['por_prova'].keys() if k.startswith(f"{ano},LC")]
            maes = [data['por_prova'][k]['mae'] for k in provas]
            
            if maes:
                avg_mae = sum(maes) / len(maes)
                status = "✅" if avg_mae < 1.0 else "❌"
                print(f"  {ano}: {len(provas)} provas. MAE médio = {avg_mae:.2f} {status}")
            else:
                 print(f"  {ano}: Área existe, mas sem provas individuais?")
        else:
            print(f"  {ano}: Ainda não calibrado")

    print("\nResumo CN Problemas (2011, 2013, 2018):")
    for ano in [2011, 2013, 2018]:
        key = f"{ano},CN"
        if key in data['por_area']:
             coef = data['por_area'][key]
             print(f"  {ano}: Slope={coef['slope']:.2f}, Intercept={coef['intercept']:.2f}")
        else:
             print(f"  {ano}: Sem dados")

inspect()
