
import json
import os
from pathlib import Path

def extrair_exemplos():
    """Extrai exemplos do JSON de fixtures e salva em um arquivo TXT estruturado."""
    fixtures_path = Path('tests/fixtures/exemplos_microdados.json')
    output_path = Path('tests/suite_testes_tri.txt')
    
    if not fixtures_path.exists():
        print(f"Erro: Arquivo {fixtures_path} não encontrado.")
        return

    with open(fixtures_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Agrupar para pegar apenas um exemplo por (ano, area, lingua)
    exemplos_unicos = {}
    
    for item in data:
        ano = item['ano']
        area = item['area']
        tp_lingua = item.get('tp_lingua')
        
        # Normalizar lingua
        lingua_str = "N/A"
        if area == 'LC':
            if tp_lingua in (0, '0'):
                lingua_str = "ingles"
            elif tp_lingua in (1, '1'):
                lingua_str = "espanhol"
        
        key = (ano, area, lingua_str, item.get('co_prova'))
        if key not in exemplos_unicos:
            exemplos_unicos[key] = item

    # Ordenar
    sorted_keys = sorted(exemplos_unicos.keys(), key=lambda k: (k[0], k[1], k[2], str(k[3])))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("# Suite de Testes TRI ENEM\n")
        f.write("# Formato: ano|area|lingua|co_prova|respostas|nota_oficial\n\n")
        
        for key in sorted_keys:
            ex = exemplos_unicos[key]
            lingua = key[2]
            line = f"{ex['ano']}|{ex['area']}|{lingua}|{ex['co_prova']}|{ex['respostas']}|{ex['nota_oficial']}\n"
            f.write(line)
            
    print(f"Sucesso: {len(sorted_keys)} exemplos extraídos para {output_path}")

if __name__ == "__main__":
    extrair_exemplos()
