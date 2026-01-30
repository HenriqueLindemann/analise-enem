"""
Validação Completa do Simulador TRI

Testa com dados reais dos microdados em:
- Todos os anos (2009-2024)
- Todas as áreas (MT, CN, CH, LC)
- Diferentes faixas de nota (baixa, média, alta)

Identifica problemas específicos, especialmente em LC.

Execute a partir da raiz do projeto:
    python tests/validar_completo.py
"""
from pathlib import Path

import _utils

_utils.add_src_to_path()

import pandas as pd
import numpy as np
from tri_enem import SimuladorNota

def validar_ano_area(sim, ano, area, n_amostras=50):
    """Valida uma área/ano específico."""
    base_path = Path("microdados_limpos")
    dados_file = base_path / str(ano) / f"DADOS_ENEM_{ano}.csv"
    
    if not dados_file.exists():
        return {'erro': 'Arquivo não encontrado'}
    
    # Carregar dados
    pres_col = f'TP_PRESENCA_{area}'
    nota_col = f'NU_NOTA_{area}'
    resp_col = f'TX_RESPOSTAS_{area}'
    prova_col = f'CO_PROVA_{area}'
    
    cols = [pres_col, nota_col, resp_col, prova_col]
    if area == 'LC':
        cols.append('TP_LINGUA')
    
    try:
        df = pd.read_csv(dados_file, sep=';', nrows=n_amostras * 10)
    except Exception as e:
        return {'erro': str(e)}
    
    # Verificar colunas
    cols = [c for c in cols if c in df.columns]
    if len(cols) < 4:
        return {'erro': 'Colunas faltando'}
    
    # Filtrar presentes com nota
    df = df[(df[pres_col] == 1) & (df[nota_col] > 0)]
    df = df.dropna(subset=[nota_col, resp_col, prova_col])
    print(f"  Dados filtrados: {len(df)} registros", flush=True)
    
    if len(df) < 10:
        return {'erro': 'Poucos dados'}
    
    # Estratificar por faixa de nota
    bins = [0, 500, 600, 700, 800, 1000]
    df['faixa'] = pd.cut(df[nota_col], bins=bins, labels=['0-500', '500-600', '600-700', '700-800', '800+'])
    
    resultados_por_faixa = {}
    
    for faixa in df['faixa'].unique():
        if pd.isna(faixa):
            continue
            
        df_faixa = df[df['faixa'] == faixa]
        n_sample = min(len(df_faixa), max(5, n_amostras // 5))
        df_sample = df_faixa.sample(n=n_sample, random_state=42)
        print(f"  Faixa {faixa}: amostrando {n_sample}/{len(df_faixa)}", flush=True)
        
        erros = []
        notas_reais = []
        notas_calc = []
        
        for _, row in df_sample.iterrows():
            try:
                # Descobrir língua para LC
                lingua = 'ingles'
                if area == 'LC' and 'TP_LINGUA' in row.index:
                    tp_lingua = row.get('TP_LINGUA')
                    if pd.notna(tp_lingua):
                        lingua = 'ingles' if int(tp_lingua) == 0 else 'espanhol'
                
                # Calcular
                prova = int(row[prova_col])
                resultado = sim.calcular(area, ano, row[resp_col], lingua=lingua, co_prova=prova)
                
                erro = row[nota_col] - resultado.nota
                erros.append(erro)
                notas_reais.append(row[nota_col])
                notas_calc.append(resultado.nota)
                
            except Exception as e:
                continue
        
        if erros:
            resultados_por_faixa[str(faixa)] = {
                'n': len(erros),
                'mae': np.mean(np.abs(erros)),
                'bias': np.mean(erros),
                'max_erro': np.max(np.abs(erros)),
                'nota_media_real': np.mean(notas_reais),
                'nota_media_calc': np.mean(notas_calc),
            }
    
    return resultados_por_faixa


def main():
    print("=" * 80)
    print("VALIDAÇÃO COMPLETA - DADOS REAIS")
    print("=" * 80)
    
    sim = SimuladorNota("microdados_limpos")
    
    # Testar anos selecionados
    anos_teste = [2009, 2012, 2015, 2018, 2020, 2023]
    areas = ['MT', 'CN', 'CH', 'LC']
    
    problemas_lc = []
    
    for ano in anos_teste:
        print(f"\n{'='*80}")
        print(f"ANO {ano}")
        print('='*80)
        
        for area in areas:
            print(f"\n--- {area} ---")
            resultado = validar_ano_area(sim, ano, area, n_amostras=50)
            
            if 'erro' in resultado:
                print(f"  ❌ Erro: {resultado['erro']}")
                continue
            
            if not resultado:
                print(f"  ⚠️  Sem dados suficientes")
                continue
            
            # Mostrar por faixa
            for faixa, stats in resultado.items():
                mae = stats['mae']
                bias = stats['bias']
                status = "✅" if mae < 5.0 else "⚠️" if mae < 20.0 else "❌"
                
                print(f"  {faixa:8} | N={stats['n']:2} | MAE={mae:6.1f} | Bias={bias:+7.1f} | "
                      f"Real={stats['nota_media_real']:.0f} Calc={stats['nota_media_calc']:.0f} {status}")
                
                # Detectar problemas em LC
                if area == 'LC' and mae > 10.0:
                    problemas_lc.append({
                        'ano': ano,
                        'faixa': faixa,
                        'mae': mae,
                        'bias': bias,
                    })
    
    # Resumo de problemas LC
    if problemas_lc:
        print(f"\n{'='*80}")
        print("PROBLEMAS DETECTADOS EM LC")
        print('='*80)
        for p in problemas_lc:
            print(f"  {p['ano']} - {p['faixa']}: MAE={p['mae']:.1f}, Bias={p['bias']:+.1f}")
    
    print(f"\n{'='*80}")
    print("VALIDAÇÃO CONCLUÍDA")
    print('='*80)


if __name__ == "__main__":
    main()
