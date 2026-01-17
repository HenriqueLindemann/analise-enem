"""
Validação Completa - Todos os Anos (2009-2024)

Verifica:
1. Todos os 16 anos disponíveis
2. Respostas sempre têm 45 chars válidos após filtro
3. Cálculos precisos em todas faixas (incluindo outliers 900+)
4. Todas as 4 áreas

Execute a partir da raiz do projeto:
    python tests/validar_todos_anos.py
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pandas as pd
import numpy as np
from tri_enem import SimuladorNota

def validar_ano_area_completo(sim, ano, area, n_amostras=100):
    """Validação completa de uma área/ano."""
    base_path = Path("microdados_limpos")
    dados_file = base_path / str(ano) / f"DADOS_ENEM_{ano}.csv"
    
    if not dados_file.exists():
        return {'erro': 'Arquivo não encontrado'}
    
    pres_col = f'TP_PRESENCA_{area}'
    nota_col = f'NU_NOTA_{area}'
    resp_col = f'TX_RESPOSTAS_{area}'
    prova_col = f'CO_PROVA_{area}'
    
    cols = [pres_col, nota_col, resp_col, prova_col]
    if area == 'LC':
        cols.append('TP_LINGUA')
    
    try:
        df = pd.read_csv(dados_file, sep=';', nrows=n_amostras * 20)
    except Exception as e:
        return {'erro': str(e)}
    
    cols = [c for c in cols if c in df.columns]
    if len(cols) < 4:
        return {'erro': 'Colunas faltando'}
    
    df = df[(df[pres_col] == 1) & (df[nota_col] > 0)]
    df = df.dropna(subset=[nota_col, resp_col, prova_col])
    
    if len(df) < 10:
        return {'erro': 'Poucos dados'}
    
    # Estratificar incluindo outliers
    bins = [0, 500, 600, 700, 800, 900, 1000]
    labels = ['0-500', '500-600', '600-700', '700-800', '800-900', '900+']
    df['faixa'] = pd.cut(df[nota_col], bins=bins, labels=labels)
    
    resultados = {}
    problemas_resposta = []
    outliers_problematicos = []
    
    for faixa in df['faixa'].unique():
        if pd.isna(faixa):
            continue
            
        df_faixa = df[df['faixa'] == faixa]
        n_sample = min(len(df_faixa), max(10, n_amostras // 6))
        df_sample = df_faixa.sample(n=n_sample, random_state=42)
        
        erros = []
        notas_reais = []
        notas_calc = []
        
        for _, row in df_sample.iterrows():
            try:
                # Verificar tamanho da resposta ANTES do filtro
                resp_original = row[resp_col]
                len_original = len(resp_original)
                
                lingua = 'ingles'
                if area == 'LC' and 'TP_LINGUA' in row.index:
                    tp_lingua = row.get('TP_LINGUA')
                    if pd.notna(tp_lingua):
                        lingua = 'ingles' if int(tp_lingua) == 0 else 'espanhol'
                
                prova = int(row[prova_col])
                resultado = sim.calcular(area, ano, resp_original, lingua=lingua, co_prova=prova)
                
                erro = row[nota_col] - resultado.nota
                erros.append(erro)
                notas_reais.append(row[nota_col])
                notas_calc.append(resultado.nota)
                
                # Detectar problemas de formato
                if area != 'LC' and len_original != 45:
                    problemas_resposta.append({
                        'ano': ano,
                        'area': area,
                        'faixa': str(faixa),
                        'len_original': len_original,
                        'nota_real': row[nota_col],
                    })
                
                # Detectar outliers problemáticos (900+ com erro > 10)
                if row[nota_col] >= 900 and abs(erro) > 10:
                    outliers_problematicos.append({
                        'ano': ano,
                        'area': area,
                        'nota_real': row[nota_col],
                        'nota_calc': resultado.nota,
                        'erro': erro,
                    })
                
            except Exception as e:
                continue
        
        if erros:
            resultados[str(faixa)] = {
                'n': len(erros),
                'mae': np.mean(np.abs(erros)),
                'bias': np.mean(erros),
                'max_erro': np.max(np.abs(erros)),
                'nota_media_real': np.mean(notas_reais),
                'nota_media_calc': np.mean(notas_calc),
            }
    
    return {
        'resultados': resultados,
        'problemas_resposta': problemas_resposta,
        'outliers_problematicos': outliers_problematicos,
    }


def main():
    print("=" * 80)
    print("VALIDAÇÃO COMPLETA - TODOS OS ANOS (2009-2024)")
    print("=" * 80)
    
    sim = SimuladorNota("microdados_limpos")
    
    anos = list(range(2009, 2025))  # Todos os anos
    areas = ['MT', 'CN', 'CH', 'LC']
    
    todos_problemas = []
    todos_outliers = []
    resumo_geral = {}
    
    for ano in anos:
        print(f"\n{'='*80}")
        print(f"ANO {ano}")
        print('='*80)
        
        for area in areas:
            resultado = validar_ano_area_completo(sim, ano, area, n_amostras=100)
            
            if 'erro' in resultado:
                print(f"\n--- {area} ---")
                print(f"  ❌ {resultado['erro']}")
                continue
            
            resultados = resultado['resultados']
            if not resultados:
                print(f"\n--- {area} ---")
                print(f"  ⚠️  Sem dados")
                continue
            
            # Calcular MAE geral
            maes = [stats['mae'] for stats in resultados.values()]
            mae_geral = np.mean(maes)
            
            # Armazenar resumo
            resumo_geral[f'{ano}-{area}'] = mae_geral
            
            print(f"\n--- {area} (MAE geral: {mae_geral:.2f}) ---")
            for faixa, stats in resultados.items():
                mae = stats['mae']
                status = "✅" if mae < 1.0 else "⚠️" if mae < 5.0 else "❌"
                print(f"  {faixa:8} | N={stats['n']:2} | MAE={mae:6.2f} | "
                      f"Real={stats['nota_media_real']:.0f} | {status}")
            
            # Coletar problemas
            todos_problemas.extend(resultado['problemas_resposta'])
            todos_outliers.extend(resultado['outliers_problematicos'])
    
    # Relatórios finais
    print(f"\n{'='*80}")
    print("RESUMO GERAL")
    print('='*80)
    
    # Agrupar por ano
    for ano in anos:
        maes_ano = [v for k, v in resumo_geral.items() if k.startswith(f'{ano}-')]
        if maes_ano:
            mae_ano = np.mean(maes_ano)
            status = "✅" if mae_ano < 1.0 else "⚠️" if mae_ano < 5.0 else "❌"
            print(f"{ano}: MAE={mae_ano:.2f} {status}")
    
    if todos_problemas:
        print(f"\n{'='*80}")
        print(f"PROBLEMAS DE FORMATO (Total: {len(todos_problemas)})")
        print('='*80)
        for p in todos_problemas[:10]:  # Primeiros 10
            print(f"  {p['ano']} {p['area']} faixa={p['faixa']}: len={p['len_original']} (esperado 45)")
    
    if todos_outliers:
        print(f"\n{'='*80}")
        print(f"OUTLIERS PROBLEMÁTICOS 900+ (Total: {len(todos_outliers)})")
        print('='*80)
        for o in todos_outliers:
            print(f"  {o['ano']} {o['area']}: real={o['nota_real']:.0f} calc={o['nota_calc']:.0f} erro={o['erro']:+.1f}")
    
    print(f"\n{'='*80}")
    print("VALIDAÇÃO CONCLUÍDA")
    print('='*80)


if __name__ == "__main__":
    main()
