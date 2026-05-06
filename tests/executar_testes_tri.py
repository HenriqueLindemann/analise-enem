
import sys
from pathlib import Path
import numpy as np

# Adicionar src ao path para importar tri_enem
src_path = Path.cwd() / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tri_enem import SimuladorNota, verificar_precisao_prova

def executar_testes():
    input_path = Path('tests/suite_testes_tri.txt')
    if not input_path.exists():
        print(f"Erro: Arquivo {input_path} não encontrado. Execute extrair_exemplos.py primeiro.")
        return

    sim = SimuladorNota("microdados_limpos")
    
    print(f"\n{'ANO':<5} | {'AREA':<4} | {'LING':<8} | {'REAL':<7} | {'CALC':<7} | {'DIFF':<7} | {'RESULTADO':<15} | {'PRECISAO':<12} | {'MAE':<5}")
    print("-" * 105)

    erros = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            
            try:
                parts = line.strip().split('|')
                if len(parts) < 6:
                    continue
                    
                ano = int(parts[0])
                area = parts[1]
                lingua = parts[2]
                co_prova = int(parts[3])
                respostas = parts[4]
                nota_real = float(parts[5])
                
                # Executar cálculo
                resultado = sim.calcular(
                    area, 
                    ano, 
                    respostas, 
                    lingua=lingua if area == 'LC' else 'ingles', 
                    co_prova=co_prova
                )
                
                # Verificar precisão esperada
                precisao = verificar_precisao_prova(ano, area, co_prova)
                
                diff = abs(nota_real - resultado.nota)
                erros.append(diff)
                
                status_str = precisao.get('status', 'ok')
                mae_str = f"{precisao.get('mae', 0):.1f}" if precisao.get('mae') else "-"
                
                # Marcar se o erro foi alto e se já era esperado
                status_calc = "✅"
                if diff > 10:
                    if status_str != 'ok':
                        status_calc = "⚠️ (Esperado)"
                    else:
                        status_calc = "❌ (Inesperado!)"
                elif diff > 5:
                    status_calc = "🟡"
                
                print(f"{ano:<5} | {area:<4} | {lingua:<8} | {nota_real:7.1f} | {resultado.nota:7.1f} | {diff:7.2f} | {status_calc:<15} | {status_str:<12} | {mae_str:<5}")
                
            except Exception as e:
                print(f"Erro no exemplo {line.strip()}: {e}")

    if erros:
        avg_err = np.mean(erros)
        print("-" * 105)
        print(f"Média do Erro (MAE): {avg_err:.2f}")
        print(f"Erro Máximo: {np.max(erros):.2f}")
        print(f"Total de testes: {len(erros)}")
        
        if avg_err < 10:
            print("\nSUCESSO: A maioria dos cálculos está dentro da margem esperada.")
        else:
            print("\nAVISO: Erro médio elevado. Verifique os casos marcados com ❌.")

if __name__ == "__main__":
    executar_testes()
