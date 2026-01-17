"""
===============================================================================
                    MEU SIMULADO ENEM - Calculador de Nota TRI
===============================================================================

Este arquivo permite calcular sua nota do ENEM usando a Teoria de Resposta ao
Item (TRI), o mesmo metodo usado pelo INEP.

COMO USAR:
    1. Preencha suas respostas abaixo (45 letras por area: A, B, C, D ou E)
    2. Escolha o ano e CODIGO DA PROVA (ver tabela abaixo ou docs/GUIA_PROVAS.md)
    3. Execute este arquivo: python meu_simulado.py
    4. Veja sua nota estimada!

IMPORTANTE:
    - Use "." para questoes em branco ou que nao quer considerar
    - Cada area deve ter exatamente 45 respostas
    - Para Linguagens (LC), informe tambem a lingua estrangeira
    - O CODIGO DA PROVA é EXTREMAMENTE importante para precisao!

CODIGOS DE PROVA - 1a APLICACAO (mais comuns):
    Consulte docs/GUIA_PROVAS.md para lista completa.
    
    Exemplo 2023 MT: AZUL=1211, AMARELA=1212, ROSA=1213, CINZA=1214
    Exemplo 2024 MT: AZUL=1407, AMARELA=1408, VERDE=1409, CINZA=1410

AVISO: O mapeamento de cores foi inferido por numero de participantes.
       Consulte docs/GUIA_PROVAS.md para detalhes e limitacoes.

Desenvolvido por Henrique Lindemann - Eng. Computacao UFRGS
https://www.linkedin.com/in/henriquelindemann/
===============================================================================
"""

# ==============================================================================
#                           CONFIGURE AQUI SEU SIMULADO
# ==============================================================================

# Ano da prova (2009 a 2024)
ANO = 2023

# Codigo da prova (consulte docs/GUIA_PROVAS.md)
# Deixe None para usar a primeira prova disponivel (pode nao ser a sua!)
# Exemplos 2023: MT Azul=1211, CN Azul=1221, CH Azul=1191, LC Azul=1201
CO_PROVA_MT = None  # Ex: 1211 para Azul 2023
CO_PROVA_CN = None  # Ex: 1221 para Azul 2023
CO_PROVA_CH = None  # Ex: 1191 para Azul 2023
CO_PROVA_LC = None  # Ex: 1201 para Azul 2023

# Lingua estrangeira para Linguagens (LC): 'ingles' ou 'espanhol'
LINGUA = 'ingles'

# ------------------------------------------------------------------------------
# SUAS RESPOSTAS - Preencha com 45 letras (A, B, C, D, E) ou "." para em branco
# ------------------------------------------------------------------------------

# Matematica e suas Tecnologias (MT) - 45 questoes
RESPOSTAS_MT = "............................................."
# Exemplo:   "CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE"

# Ciencias da Natureza e suas Tecnologias (CN) - 45 questoes
RESPOSTAS_CN = "............................................."
# Exemplo:   "ABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDE"

# Ciencias Humanas e suas Tecnologias (CH) - 45 questoes
RESPOSTAS_CH = "............................................."
# Exemplo:   "ABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDE"

# Linguagens, Codigos e suas Tecnologias (LC) - 45 questoes
RESPOSTAS_LC = "............................................."
# Exemplo:   "ABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDEABCDE"


# ==============================================================================
#                    NAO PRECISA MODIFICAR ABAIXO DESTA LINHA
# ==============================================================================

import sys
from pathlib import Path

# Adiciona o modulo ao path (funciona em Windows, Linux e Mac)
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tri_enem import SimuladorNota


def validar_respostas(respostas, area):
    """Valida se as respostas estao no formato correto."""
    if len(respostas) != 45:
        print(f"ERRO: {area} deve ter 45 respostas, voce colocou {len(respostas)}")
        return False
    
    invalidas = [c for c in respostas.upper() if c not in 'ABCDE.']
    if invalidas:
        print(f"ERRO: {area} tem caracteres invalidos: {set(invalidas)}")
        print("      Use apenas A, B, C, D, E ou . (ponto para em branco)")
        return False
    
    return True


def calcular_nota(sim, area, ano, respostas, lingua=None, co_prova=None):
    """Calcula a nota de uma area."""
    # Verifica se todas as respostas sao pontos (nao respondeu)
    if respostas == "." * 45:
        return None
    
    try:
        if area == 'LC':
            resultado = sim.calcular(area, ano, respostas, lingua=lingua, co_prova=co_prova)
        else:
            resultado = sim.calcular(area, ano, respostas, co_prova=co_prova)
        return resultado
    except Exception as e:
        print(f"Erro ao calcular {area}: {e}")
        return None


# Mapa de codigos de prova por area
CODIGOS_PROVA = {
    'MT': CO_PROVA_MT,
    'CN': CO_PROVA_CN,
    'CH': CO_PROVA_CH,
    'LC': CO_PROVA_LC
}


def main():
    print()
    print("=" * 60)
    print("           CALCULADOR DE NOTA TRI - ENEM", ANO)
    print("=" * 60)
    print()
    
    # Mostrar aviso sobre codigos
    if all(v is None for v in CODIGOS_PROVA.values()):
        print("AVISO: Nenhum codigo de prova especificado.")
        print("       O sistema usara a primeira prova disponivel.")
        print("       Para maior precisao, consulte docs/GUIA_PROVAS.md")
        print()
    
    # Validar todas as respostas
    areas = {
        'MT': ('Matematica', RESPOSTAS_MT),
        'CN': ('Ciencias da Natureza', RESPOSTAS_CN),
        'CH': ('Ciencias Humanas', RESPOSTAS_CH),
        'LC': ('Linguagens', RESPOSTAS_LC),
    }
    
    todas_validas = True
    for sigla, (nome, respostas) in areas.items():
        if respostas != "." * 45:  # So valida se preencheu algo
            if not validar_respostas(respostas, nome):
                todas_validas = False
    
    if not todas_validas:
        print("\nCorrija os erros acima e execute novamente.")
        return
    
    # Inicializar simulador
    print("Carregando dados...")
    sim = SimuladorNota()
    
    # Calcular notas
    print()
    print("-" * 60)
    print("RESULTADOS")
    print("-" * 60)
    
    notas = {}
    for sigla, (nome, respostas) in areas.items():
        if respostas == "." * 45:
            print(f"{nome:.<30} NAO PREENCHIDO")
            continue
        
        co_prova = CODIGOS_PROVA.get(sigla)
        resultado = calcular_nota(sim, sigla, ANO, respostas, 
                                  lingua=LINGUA if sigla == 'LC' else None,
                                  co_prova=co_prova)
        
        if resultado:
            notas[sigla] = resultado.nota
            prova_info = f"prova {resultado.co_prova}" if resultado.co_prova else ""
            print(f"{nome:.<30} {resultado.nota:>6.1f} pontos ({resultado.acertos}/{resultado.total_itens} acertos) {prova_info}")
        else:
            print(f"{nome:.<30} ERRO NO CALCULO")
    
    # Media (se calculou mais de uma area)
    if len(notas) > 0:
        media = sum(notas.values()) / len(notas)
        print("-" * 60)
        print(f"{'MEDIA (sem redacao)':.<30} {media:>6.1f} pontos")
    
    print()
    print("=" * 60)
    print("ATENCAO: Esta e uma estimativa. A nota oficial pode variar.")
    print("         Nem todas as provas foram totalmente calibradas.")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
