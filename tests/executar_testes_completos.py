
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Mock Streamlit antes de importar o calculador
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st
# Mock decorators
def mock_decorator(*args, **kwargs):
    return lambda f: f
mock_st.cache_resource = mock_decorator
mock_st.cache_data = mock_decorator

# Adicionar caminhos ao sys.path
root_path = Path.cwd()
src_path = root_path / 'src'
app_path = root_path / 'streamlit_app'

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(app_path) not in sys.path:
    sys.path.insert(0, str(app_path))

from calculador import CalculadorEnem
from tri_enem import verificar_precisao_prova

def executar_testes_completos():
    input_path = Path('tests/suite_testes_completos.txt')
    if not input_path.exists():
        print(f"Erro: Arquivo {input_path} não encontrado. Execute extrair_exemplos_completos.py primeiro.")
        return

    calc_app = CalculadorEnem()
    
    print(f"\n{'ANO':<5} | {'ID':<15} | {'AREA':<4} | {'NOTA REAL':<10} | {'NOTA CALC':<10} | {'DIFF':<7} | {'POS (1ª)':<8} | {'ORDEM OK?':<10}")
    print("-" * 100)

    total_casos = 0
    erros_totais = []
    falhas_ordem = 0

    todas_linhas = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('#') and line.strip():
                todas_linhas.append(line.strip())

    # Amostrar 15 de antes de 2017 e 15 de 2017 em diante
    linhas_pre = [l for l in todas_linhas if int(l.split('|')[0]) < 2017]
    linhas_pos = [l for l in todas_linhas if int(l.split('|')[0]) >= 2017]
    
    import random
    random.seed(42)
    amostra = random.sample(linhas_pre, min(len(linhas_pre), 20)) + \
              random.sample(linhas_pos, min(len(linhas_pos), 20))
    
    # Ordenar por ano para o relatório ficar bonito
    amostra.sort(key=lambda l: int(l.split('|')[0]))

    for line in amostra:
        try:
            parts = line.split('|')
            ano = int(parts[0])
            est_id = parts[1]
            tipo = parts[2]
            cores = json.loads(parts[3])
            linguas = json.loads(parts[4])
            respostas = json.loads(parts[5])
            notas_reais = json.loads(parts[6])
            
            # Simular Streamlit: pegar a primeira língua do dicionário para a chamada (geralmente só tem uma de qq forma)
            lingua_principal = next(iter(linguas.values())) if linguas else 'ingles'
            
            # EXECUTAR CÁLCULO (Simulando o App)
            resultados, erros_app = calc_app.calcular_todas_areas(
                ano=ano,
                respostas=respostas,
                cores=cores,
                tipo_aplicacao=tipo,
                lingua=lingua_principal
            )
            
            for res in resultados:
                sigla = res['sigla']
                nota_real = float(notas_reais.get(sigla, 0))
                nota_calc = res['nota']
                diff = abs(nota_real - nota_calc)
                erros_totais.append(diff)
                
                # Coletar todas as questões para validação de ordem
                todas_q = sorted(res.get('questoes_acertadas', []) + res.get('questoes_erradas', []), key=lambda x: x['posicao'])
                if not todas_q: continue
                
                primeira_pos = todas_q[0]['posicao']
                # Validação da regra de ordem (considerando possíveis questões anuladas no início)
                offset_base = {
                    'CH': 0 if ano <= 2016 else 45,
                    'CN': 45 if ano <= 2016 else 90,
                    'LC': 90 if ano <= 2016 else 0,
                    'MT': 135
                }.get(sigla, -1)
                
                # A posição esperada deve ser offset_base + idx_area_da_primeira_questao + 1
                # Se idx_area > 0, significa que as primeiras questões foram puladas (ex: anuladas)
                idx_primeira = todas_q[0]['idx_area'] if todas_q else 0
                esperado_real = offset_base + idx_primeira + 1
                
                ordem_ok = "✅" if primeira_pos == esperado_real else f"❌ (Exp {esperado_real})"
                if primeira_pos != esperado_real:
                    falhas_ordem += 1
                
                prefixo = ">>> " if primeira_pos != esperado_real else ""
                print(f"{prefixo}{ano:<5} | {est_id:<15} | {sigla:<4} | {nota_real:10.1f} | {nota_calc:10.1f} | {diff:7.2f} | {primeira_pos:<8} | {ordem_ok:<10}")
            
            total_casos += 1
                
        except Exception as e:
            print(f"Erro no caso {line[:50]}...: {e}")

    print("-" * 100)
    print(f"Total de estudantes testados: {total_casos}")
    print(f"Falhas de ordem detectadas: {falhas_ordem}")
    if erros_totais:
        print(f"Média do Erro (MAE): {sum(erros_totais)/len(erros_totais):.2f}")

if __name__ == "__main__":
    executar_testes_completos()
