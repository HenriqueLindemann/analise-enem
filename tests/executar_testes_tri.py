
import sys
import argparse
from pathlib import Path
import numpy as np

# Adicionar src ao path para importar tri_enem
src_path = Path.cwd() / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tri_enem import SimuladorNota, verificar_precisao_prova

def executar_testes(apenas_erros=False):
    input_path = Path('tests/suite_testes_tri.txt')
    if not input_path.exists():
        print(f"Erro: Arquivo {input_path} não encontrado. Execute extrair_exemplos.py primeiro.")
        return

    sim = SimuladorNota("microdados_limpos")
    
    print(f"\n{'ANO':<5} | {'PROVA':<5} | {'AREA':<4} | {'LING':<8} | {'REAL':<7} | {'CALC':<7} | {'DIFF':<7} | {'RESULTADO':<15} | {'PRECISAO_DB':<12} | {'MAE_DB':<5}")
    print("-" * 115)

    erros = []
    inesperados_count = 0
    
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
                status_calc = "✅ Exato"
                is_error = False
                
                if diff > 10:
                    if status_str != 'ok':
                        status_calc = "⚠️ (Esperado)"
                        is_error = True
                    else:
                        status_calc = "❌ (Inesperado!)"
                        inesperados_count += 1
                        is_error = True
                elif diff > 5:
                    status_calc = "🟡 Parcial"
                    is_error = True
                
                if apenas_erros and not is_error:
                    continue
                    
                print(f"{ano:<5} | {co_prova:<5} | {area:<4} | {lingua:<8} | {nota_real:7.1f} | {resultado.nota:7.1f} | {diff:7.2f} | {status_calc:<15} | {status_str:<12} | {mae_str:<5}")
                
            except Exception as e:
                print(f"Erro no exemplo {line.strip()}: {e}")

    if erros:
        avg_err = np.mean(erros)
        print("-" * 115)
        print(f"Resumo da Simulação TRI:")
        print(f"  Média do Erro (MAE) Global : {avg_err:.2f}")
        print(f"  Margem de Erro Máxima      : {np.max(erros):.2f}")
        print(f"  Total de testes efetuados  : {len(erros)}")
        print(f"  Total de erros inesperados : {inesperados_count}")
        
        if inesperados_count == 0 and avg_err < 10:
            print("\n✅ SUCESSO: Todos os cálculos estão dentro da margem esperada.")
        else:
            print("\n⚠️ AVISO: Existem erros maiores do que 10 em testes não listados nas provas não calibradas.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Testa os cálculos de TRI baseados nas provas geradas.")
    parser.add_argument('--apenas-erros', action='store_true', help="Mostra apenas os testes que tiveram um desvio maior do que o ideal.")
    args = parser.parse_args()
    
    executar_testes(args.apenas_erros)
