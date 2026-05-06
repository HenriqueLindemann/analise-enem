
import json
import sys
from pathlib import Path
from collections import defaultdict

# Adicionar src ao path para usar o mapeador
src_path = Path.cwd() / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from tri_enem import MapeadorProvas

def extrair_exemplos_completos():
    fixtures_path = Path('tests/fixtures/exemplos_microdados.json')
    output_path = Path('tests/suite_testes_completos.txt')
    
    if not fixtures_path.exists():
        print(f"Erro: Arquivo {fixtures_path} não encontrado.")
        return

    with open(fixtures_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapeador = MapeadorProvas()
    
    # Agrupar por (ano, id)
    estudantes = defaultdict(lambda: {
        'respostas': {}, 
        'cores': {}, 
        'notas': {}, 
        'linguas': {},
        'co_provas': {},
        'tipo_aplicacao': None
    })
    
    for item in data:
        ano = item['ano']
        est_id = item['id']
        area = item['area']
        
        key = (ano, est_id)
        est = estudantes[key]
        
        est['respostas'][area] = item['respostas']
        est['cores'][area] = item.get('cor_prova', 'desconhecida')
        est['notas'][area] = item['nota_oficial']
        est['co_provas'][area] = item['co_prova']
        
        # Identificar tipo_aplicacao e normalizar cor se possível
        info = mapeador.descobrir_prova_por_codigo(int(item['co_prova']))
        if info:
            est['tipo_aplicacao'] = info.tipo_aplicacao
            if info.cor:
                est['cores'][area] = info.cor
        
        if area == 'LC':
            tp = item.get('tp_lingua')
            if tp in (0, '0'):
                est['linguas'][area] = 'ingles'
            elif tp in (1, '1'):
                est['linguas'][area] = 'espanhol'
            else:
                est['linguas'][area] = 'ingles' # Default

    # Salvar no arquivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Suite de Testes Completos (Simulação Streamlit)\n")
        f.write("# Formato: ano|id|tipo_aplicacao|cores_json|linguas_json|respostas_json|notas_json\n\n")
        
        for (ano, est_id), est in sorted(estudantes.items()):
            # Se não identificou tipo_aplicacao, assume 1a_aplicacao
            tipo = est['tipo_aplicacao'] or '1a_aplicacao'
            
            # Sanitizar cores: se uma área não tem cor definida no mapeador, tenta usar o que veio no JSON
            # Mas CalculadorEnem precisa de cores válidas.
            
            line = f"{ano}|{est_id}|{tipo}|{json.dumps(est['cores'])}|{json.dumps(est['linguas'])}|{json.dumps(est['respostas'])}|{json.dumps(est['notas'])}\n"
            f.write(line)

    print(f"Sucesso: {len(estudantes)} casos de teste (estudantes) extraídos para {output_path}")

if __name__ == "__main__":
    extrair_exemplos_completos()
