import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem.mapeador_provas import MapeadorProvas

def validar_2024():
    mapeador = MapeadorProvas()
    print("Iniciando validação de códigos 2024...\n")

    # Estrutura esperada baseada no que foi inserido
    esperado = {
        'CN': {
            '1a_aplicacao': {'azul': 1419, 'amarela': 1420, 'verde': 1421, 'cinza': 1422},
            'reaplicacao': {'azul': 1373, 'amarela': 1374, 'cinza': 1375, 'verde': 1376},
            'especiais': {
                'verde_ampliada': 1423, 'verde_superampliada': 1424, 
                'laranja_adaptada_ledor': 1426, 'roxa_videoprova_libras': 1427
            }
        },
        'CH': {
            '1a_aplicacao': {'azul': 1383, 'amarela': 1384, 'branca': 1385, 'verde': 1386},
            'reaplicacao': {'azul': 1343, 'amarela': 1344, 'branca': 1345, 'verde': 1346},
             'especiais': {
                'verde_ampliada': 1387, 'verde_superampliada': 1388,
                'roxa_videoprova_libras': 1391
            }
        },
        'LC': {
            '1a_aplicacao': {'azul': 1395, 'amarela': 1396, 'verde': 1397, 'branca': 1398},
            'reaplicacao': {'azul': 1353, 'amarela': 1354, 'verde': 1355, 'branca': 1356},
             'especiais': {
                'verde_ampliada': 1399, 'roxa_videoprova_libras': 1403
            }
        },
        'MT': {
            '1a_aplicacao': {'azul': 1407, 'amarela': 1408, 'verde': 1409, 'cinza': 1410},
            'reaplicacao': {'azul': 1363, 'amarela': 1364, 'verde': 1365, 'cinza': 1366},
             'especiais': {
                'verde_ampliada': 1411, 'roxa_videoprova_libras': 1415
            }
        }
    }

    erros = 0
    testes = 0

    for area, tipos in esperado.items():
        print(f"Verificando Área {area}...")
        for tipo, cores in tipos.items():
            for cor, codigo_esperado in cores.items():
                if tipo == 'especiais':
                    # Para especiais, o nome da cor é a chave completa no mapeamento
                    # Mas no MapeadorProvas.obter_codigo não acessamos 'especiais' diretamente como tipo
                    # A implementação atual do mapeador não expõe 'especiais' via obter_codigo de forma direta
                    # Precisamos verificar se ele está no YAML carregado
                    
                    # Vamos verificar direto na estrutura de dados do mapeador para especiais
                    codigo_real = mapeador.dados[2024][area]['especiais'].get(cor)
                    
                else:
                    codigo_real = mapeador.obter_codigo(2024, area, tipo, cor, permitir_fallback=False)
                
                testes += 1
                if codigo_real != codigo_esperado:
                    print(f"❌ ERRO: {area} {tipo} {cor} -> Esperado {codigo_esperado}, obtido {codigo_real}")
                    erros += 1
                else:
                    # print(f"✅ OK: {area} {tipo} {cor} -> {codigo_real}")
                    pass
    
    print(f"\nResumo: {testes} testes realizados.")
    if erros == 0:
        print("✅ SUCESSO! Todos os códigos 2024 verificados conferem.")
    else:
        print(f"❌ FRACASSO! Encontrados {erros} erros.")
        exit(1)

if __name__ == "__main__":
    validar_2024()
