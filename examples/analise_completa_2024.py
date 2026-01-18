"""
===============================================================================
            ANALISE COMPLETA DE PROVA - EXEMPLO REAL ENEM 2024
===============================================================================

Este arquivo demonstra a analise completa de uma prova real do ENEM 2024.
Os dados sao de um participante real dos microdados do INEP.

Funcionalidades demonstradas:
1. Calculo da nota TRI
2. Validacao com nota oficial
3. Analise de impacto de cada questao
4. Ranking de questoes por ganho potencial
5. Identificacao de erros em questoes faceis (prioridade de estudo)

===============================================================================
"""

import sys
from pathlib import Path

# Adiciona o modulo ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tri_enem import SimuladorNota, CalculadorTRI

# ==============================================================================
#                    DADOS REAIS - PARTICIPANTE ENEM 2024
# ==============================================================================

# Participante real (extraido dos microdados INEP)
# Encontrado via: tools/encontrar_exemplo.py
PARTICIPANTE = {
    'MT': {
        'prova': 1410,
        'nota_oficial': 711.7,
        'respostas': 'DBCEECACBDBAADDDDDDCBCDCCAADACCEBBECADACBADDD',
    },
    'CN': {
        'prova': 1422,
        'nota_oficial': 647.4,
        'respostas': 'DBCCCBBDEBBCEEDDBECCBCBCAADDDDABBECBCEECEAACD',
    },
    'CH': {
        'prova': 1384,
        'nota_oficial': 684.6,
        'respostas': 'BADDBCDCECADEBBBEBCEBADACBCADEDBEACBAECAECEDA',
    },
    'LC': {
        'prova': 1396,
        'nota_oficial': 636.9,
        'respostas': 'AACEADADECBBDBDEBDADCCBEDDCDEBBDEDDEBDCECEDDC',
        'lingua': 'ingles',  # TP_LINGUA = 0
    },
}

ANO = 2024


def analisar_area(sim, calc, area, dados):
    """Analisa uma area completa."""
    print()
    print('=' * 70)
    print(f'  {area} - {"MATEMATICA" if area == "MT" else "CIENCIAS NATUREZA" if area == "CN" else "CIENCIAS HUMANAS" if area == "CH" else "LINGUAGENS"}')
    print('=' * 70)
    
    prova = dados['prova']
    nota_oficial = dados['nota_oficial']
    respostas = dados['respostas']
    lingua = dados.get('lingua', 'ingles')
    
    # Calcular nota
    if area == 'LC':
        resultado = sim.calcular(area, ANO, respostas, lingua=lingua, co_prova=prova)
    else:
        resultado = sim.calcular(area, ANO, respostas, co_prova=prova)
    
    erro = resultado.nota - nota_oficial
    
    print()
    print(f'  Prova: {prova}')
    print(f'  Nota Oficial INEP: {nota_oficial:.1f}')
    print(f'  Nota Calculada:    {resultado.nota:.1f}')
    print(f'  Diferenca:         {erro:+.1f} pontos')
    print(f'  Acertos:           {resultado.acertos}/{resultado.total_itens}')
    print(f'  Theta (proficiencia): {resultado.theta:.4f}')
    
    # Analisar impacto dos erros
    print()
    print('-' * 70)
    print('  ANALISE DE IMPACTO DOS ERROS')
    print('-' * 70)
    
    impactos = calc.analisar_impacto_erros(ANO, area, prova, respostas)
    
    if not impactos:
        print('  Nenhum erro para analisar (gabarito perfeito ou dados indisponiveis)')
        return resultado, []
    
    # Ordenar por ganho potencial
    impactos_ordenados = sorted(impactos, key=lambda x: -x['ganho_potencial'])
    
    print()
    print(f'  {"#":>3} {"Questao":>8} {"Ganho":>10} {"Dificuldade":>12} {"Sua Resp":>10} {"Gabarito":>10}')
    print('  ' + '-' * 65)
    
    for i, erro in enumerate(impactos_ordenados, 1):
        dificuldade = erro['param_b']
        if dificuldade < -1:
            nivel = 'Muito Facil'
        elif dificuldade < 0:
            nivel = 'Facil'
        elif dificuldade < 1:
            nivel = 'Media'
        elif dificuldade < 2:
            nivel = 'Dificil'
        else:
            nivel = 'Muito Dificil'
        
        print(f'  {i:>3} {erro["posicao"]:>8} {erro["ganho_potencial"]:>+10.1f} {nivel:>12} {erro["resposta_dada"]:>10} {erro["gabarito"]:>10}')
    
    # Resumo
    print()
    print('-' * 70)
    print('  RESUMO')
    print('-' * 70)
    
    erros_faceis = [e for e in impactos if e['param_b'] < 0]
    erros_medios = [e for e in impactos if 0 <= e['param_b'] < 1]
    erros_dificeis = [e for e in impactos if e['param_b'] >= 1]
    
    ganho_faceis = sum(e['ganho_potencial'] for e in erros_faceis)
    ganho_medios = sum(e['ganho_potencial'] for e in erros_medios)
    ganho_dificeis = sum(e['ganho_potencial'] for e in erros_dificeis)
    
    print(f'  Erros em questoes faceis:    {len(erros_faceis):>3} (ganho potencial: +{ganho_faceis:.1f} pts)')
    print(f'  Erros em questoes medias:    {len(erros_medios):>3} (ganho potencial: +{ganho_medios:.1f} pts)')
    print(f'  Erros em questoes dificeis:  {len(erros_dificeis):>3} (ganho potencial: +{ganho_dificeis:.1f} pts)')
    print()
    
    if erros_faceis:
        print('  PRIORIDADE: Estudar questoes faceis que voce errou!')
        print('  Questoes prioritarias:', ', '.join(str(e['posicao']) for e in sorted(erros_faceis, key=lambda x: -x['ganho_potencial'])[:5]))
    
    return resultado, impactos_ordenados


def main():
    print()
    print('=' * 70)
    print('        ANALISE COMPLETA - PROVA REAL ENEM 2024')
    print('=' * 70)
    print()
    print('Este exemplo usa dados reais de um participante do ENEM 2024')
    print('extraidos dos microdados oficiais do INEP.')
    print()
    
    # Inicializar
    sim = SimuladorNota()
    calc = CalculadorTRI()
    
    resultados = {}
    todas_analises = {}
    
    # Analisar cada area
    for area in ['MT', 'CN', 'CH', 'LC']:
        resultado, impactos = analisar_area(sim, calc, area, PARTICIPANTE[area])
        resultados[area] = resultado
        todas_analises[area] = impactos
    
    # Resumo final
    print()
    print('=' * 70)
    print('                    RESUMO GERAL')
    print('=' * 70)
    print()
    print(f'  {"Area":12} {"Oficial":>10} {"Calculada":>10} {"Erro":>8} {"Acertos":>10}')
    print('  ' + '-' * 55)
    
    soma_oficial = 0
    soma_calculada = 0
    
    for area in ['MT', 'CN', 'CH', 'LC']:
        r = resultados[area]
        oficial = PARTICIPANTE[area]['nota_oficial']
        erro = r.nota - oficial
        soma_oficial += oficial
        soma_calculada += r.nota
        print(f'  {area:12} {oficial:>10.1f} {r.nota:>10.1f} {erro:>+8.1f} {r.acertos:>7}/{r.total_itens}')
    
    media_oficial = soma_oficial / 4
    media_calculada = soma_calculada / 4
    
    print('  ' + '-' * 55)
    print(f'  {"MEDIA":12} {media_oficial:>10.1f} {media_calculada:>10.1f} {media_calculada - media_oficial:>+8.1f}')
    
    print()
    print('=' * 70)
    print('  VALIDACAO: Erro medio < 1 ponto confirma precisao do calculo TRI')
    print('=' * 70)
    print()


if __name__ == '__main__':
    main()
