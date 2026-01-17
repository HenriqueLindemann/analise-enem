"""
Calibração completa salvando resultados em JSON.

Execute a partir da raiz do projeto:
    python tools/calibrar_todos_anos.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import Calibrador
import json

print("=" * 80)
print("CALIBRAÇÃO COMPLETA - SALVANDO EM JSON")
print("Amostragem estratificada com 200 participantes por prova")
print("=" * 80)

# Recalibrar todos os anos, mas pulando 2017 (muito problemático)
cal = Calibrador("microdados_limpos")
anos = [a for a in range(2009, 2025) if a != 2017]

# Carregar dados existentes
coeficientes_data = {
    'por_prova': {},
    'por_area': {},
    'metadata': {}
}
if Path('tri_enem/coeficientes_data.json').exists():
    with open('tri_enem/coeficientes_data.json', 'r', encoding='utf-8') as f:
        coeficientes_data = json.load(f)

print(f"Carregados {len(coeficientes_data['por_prova'])} coeficientes existentes.")

provas_problematicas = []

for ano in anos:
    print(f"\n{'='*80}")
    print(f"ANO {ano}")
    print('='*80)
    
    try:
        # Calibrar ano completo
        resultados = cal.calibrar_ano_completo(ano, n_amostras_por_prova=200, verbose=True)
        
        # Processar resultados
        for area, lista_provas in resultados.items():
            if not isinstance(lista_provas, list):
                continue
            
            slopes_area = []
            intercepts_area = []
            
            for r in lista_provas:
                # Verificar se houve erro
                if 'erro' in r:
                    continue
                    
                # Verificar MAE alto (limiar 10.0) ou R² baixo
                if r['mae'] > 10.0 or r.get('r_squared', 0) < 0.90:
                    provas_problematicas.append({
                        'ano': ano,
                        'area': area,
                        'prova': r.get('prova'),
                        'mae': r['mae'],
                        'r_squared': r.get('r_squared'),
                        'slope': r.get('slope'),
                        'intercept': r.get('intercept')
                    })
                    print(f"  ⚠️ PROVA PROBLEMÁTICA: {area} {r.get('prova')} MAE={r['mae']:.2f}")
                    # Não salvar coeficientes ruins (exceto se for única opção, mas melhor não)
                    if r['mae'] > 20.0:  # Se muito ruim, descarta
                        continue

                # Salvar coeficientes aceitáveis (mesmo com MAE 10-20, pode ser útil)
                key = f"{r['ano']},{r['area']},{r['prova']}"
                coeficientes_data['por_prova'][key] = {
                    'slope': r['slope'],
                    'intercept': r['intercept'],
                    'r_squared': r['r_squared'],
                    'mae': r['mae'],
                    'n_amostras': r['n_amostras']
                }
                
                slopes_area.append(r['slope'])
                intercepts_area.append(r['intercept'])
            
            # Salvar média da área
            if slopes_area:
                import numpy as np
                key = f"{ano},{area}"
                coeficientes_data['por_area'][key] = {
                    'slope': float(np.mean(slopes_area)),
                    'intercept': float(np.mean(intercepts_area)),
                    'n_provas': len(slopes_area)
                }
        
        print(f"\n{cal.resumo_calibracao(resultados)}")
        
        # Salvar JSON parcial para não perder progresso
        with open('tri_enem/coeficientes_data.json', 'w', encoding='utf-8') as f:
            json.dump(coeficientes_data, f, indent=2, ensure_ascii=False)
        print(f"Dados salvos parcialmente.")
        
    except Exception as e:
        print(f"\n❌ Erro ao calibrar {ano}: {e}")

# Salvar lista de provas problemáticas
with open('tri_enem/provas_problematicas.json', 'w', encoding='utf-8') as f:
    json.dump(provas_problematicas, f, indent=2, ensure_ascii=False)
    
# Salvar JSON Final (Metadata será adicionado depois)
output_file = Path('tri_enem/coeficientes_data.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(coeficientes_data, f, indent=2, ensure_ascii=False)
print(f"\nSalvas {len(provas_problematicas)} provas problemáticas em tri_enem/provas_problematicas.json")

# Calcular padrões por área
import numpy as np
for area in ['MT', 'CN', 'CH', 'LC']:
    valores = [v for k, v in coeficientes_data['por_area'].items() if k.endswith(f',{area}')]
    if valores:
        slopes = [v['slope'] for v in valores]
        intercepts = [v['intercept'] for v in valores]
        coeficientes_data['metadata'][area] = {
            'slope_medio': float(np.mean(slopes)),
            'intercept_medio': float(np.mean(intercepts)),
            'n_anos': len(valores)
        }

# Salvar JSON
output_file = Path('tri_enem/coeficientes_data.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(coeficientes_data, f, indent=2, ensure_ascii=False)

print(f"\n{'='*80}")
print("CALIBRAÇÃO COMPLETA!")
print(f"{'='*80}")
print(f"Coeficientes salvos em: {output_file}")
print(f"  Por prova: {len(coeficientes_data['por_prova'])}")
print(f"  Por área: {len(coeficientes_data['por_area'])}")
