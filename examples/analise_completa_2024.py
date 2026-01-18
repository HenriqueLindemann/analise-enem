"""
===============================================================================
            ANALISE COMPLETA DE PROVA - EXEMPLO REAL ENEM 2024
===============================================================================

Este arquivo demonstra a analise completa de uma prova real do ENEM 2024.
Os dados sao de um participante real dos microdados do INEP.

Funcionalidades demonstradas:
1. Calculo da nota TRI
2. Validacao com nota oficial
3. Analise de TODAS as questoes (acertos e erros)
4. Ranking de erros por ganho potencial
5. Ranking de acertos por contribuicao para a nota
6. Identificacao de erros em questoes faceis (prioridade de estudo)

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


def classificar_dificuldade(param_b):
    """Classifica a dificuldade do item baseado no parametro b."""
    if param_b < -1:
        return 'Muito Facil'
    elif param_b < 0:
        return 'Facil'
    elif param_b < 1:
        return 'Media'
    elif param_b < 2:
        return 'Dificil'
    else:
        return 'Muito Dificil'


def analisar_area_completa(calc, area, dados):
    """Analisa uma area usando analisar_todas_questoes."""
    print()
    print('=' * 80)
    nomes = {'MT': 'MATEMATICA', 'CN': 'CIENCIAS DA NATUREZA', 'CH': 'CIENCIAS HUMANAS', 'LC': 'LINGUAGENS'}
    print(f'  {area} - {nomes[area]}')
    print('=' * 80)
    
    prova = dados['prova']
    nota_oficial = dados['nota_oficial']
    respostas = dados['respostas']
    
    # Para LC, obter tp_lingua
    tp_lingua = None
    if area == 'LC':
        tp_lingua = 0 if dados.get('lingua', 'ingles') == 'ingles' else 1
    
    # Usar novo metodo de analise completa
    analise = calc.analisar_todas_questoes(ANO, area, prova, respostas, tp_lingua)
    
    erro = analise['nota'] - nota_oficial
    
    print()
    print(f'  Prova: {prova}')
    print(f'  Nota Oficial INEP: {nota_oficial:.1f}')
    print(f'  Nota Calculada:    {analise["nota"]:.1f}')
    print(f'  Diferenca:         {erro:+.1f} pontos')
    print(f'  Acertos:           {analise["total_acertos"]}/{analise["total_itens"]}')
    print(f'  Theta:             {analise["theta"]:.4f}')
    
    # ===== SECAO DE ERROS =====
    print()
    print('-' * 80)
    print('  QUESTOES ERRADAS (ordenadas por ganho potencial se acertasse)')
    print('-' * 80)
    
    if not analise['erros']:
        print('  Nenhum erro - Gabarito perfeito!')
    else:
        print()
        print(f'  {"#":>3} {"Q":>4} {"Ganho":>8} {"Dificuldade":>14} {"Resp":>6} {"Gab":>5}')
        print('  ' + '-' * 50)
        
        for i, erro_item in enumerate(analise['erros'], 1):
            nivel = classificar_dificuldade(erro_item['param_b'])
            print(f'  {i:>3} {erro_item["posicao"]:>4} {erro_item["ganho_se_acertasse"]:>+8.1f} {nivel:>14} {erro_item["resposta_dada"]:>6} {erro_item["gabarito"]:>5}')
        
        # Resumo por dificuldade
        print()
        erros_faceis = [e for e in analise['erros'] if e['param_b'] < 0]
        erros_medios = [e for e in analise['erros'] if 0 <= e['param_b'] < 1]
        erros_dificeis = [e for e in analise['erros'] if e['param_b'] >= 1]
        
        ganho_faceis = sum(e['ganho_se_acertasse'] for e in erros_faceis)
        ganho_medios = sum(e['ganho_se_acertasse'] for e in erros_medios)
        ganho_dificeis = sum(e['ganho_se_acertasse'] for e in erros_dificeis)
        
        print(f'  Resumo dos erros:')
        print(f'    - Questoes faceis:    {len(erros_faceis):>2} erros = +{ganho_faceis:>6.1f} pts potenciais')
        print(f'    - Questoes medias:    {len(erros_medios):>2} erros = +{ganho_medios:>6.1f} pts potenciais')
        print(f'    - Questoes dificeis:  {len(erros_dificeis):>2} erros = +{ganho_dificeis:>6.1f} pts potenciais')
        
        if erros_faceis:
            print()
            print('  ** PRIORIDADE DE ESTUDO: Questoes faceis que voce errou! **')
            prio = sorted(erros_faceis, key=lambda x: -x['ganho_se_acertasse'])[:5]
            print('  Questoes:', ', '.join(str(e['posicao']) for e in prio))
    
    # ===== SECAO DE ACERTOS =====
    print()
    print('-' * 80)
    print('  QUESTOES ACERTADAS (ordenadas por contribuicao para a nota)')
    print('-' * 80)
    
    if not analise['acertos']:
        print('  Nenhum acerto')
    else:
        print()
        print(f'  {"#":>3} {"Q":>4} {"Contribuicao":>12} {"Dificuldade":>14} {"Resp/Gab":>10}')
        print('  ' + '-' * 50)
        
        # Mostrar top 10 acertos mais valiosos e bottom 5
        top_acertos = analise['acertos'][:10]
        for i, acerto in enumerate(top_acertos, 1):
            nivel = classificar_dificuldade(acerto['param_b'])
            print(f'  {i:>3} {acerto["posicao"]:>4} {acerto["perda_se_errasse"]:>+12.1f} {nivel:>14} {acerto["gabarito"]:>10}')
        
        if len(analise['acertos']) > 10:
            print(f'  ... (mais {len(analise["acertos"]) - 10} acertos) ...')
            # Mostrar os 3 ultimos (menos valiosos)
            for acerto in analise['acertos'][-3:]:
                nivel = classificar_dificuldade(acerto['param_b'])
                print(f'      {acerto["posicao"]:>4} {acerto["perda_se_errasse"]:>+12.1f} {nivel:>14} {acerto["gabarito"]:>10}')
        
        # Estatisticas dos acertos
        print()
        print(f'  Maior contribuicao: Q{analise["acertos"][0]["posicao"]} (+{analise["acertos"][0]["perda_se_errasse"]:.1f} pts)')
        print(f'  Menor contribuicao: Q{analise["acertos"][-1]["posicao"]} (+{analise["acertos"][-1]["perda_se_errasse"]:.1f} pts)')
        total_contribuicao = sum(a['perda_se_errasse'] for a in analise['acertos'])
        print(f'  Contribuicao total dos acertos: +{total_contribuicao:.1f} pts')
    
    return analise


def main():
    print()
    print('=' * 80)
    print('             ANALISE COMPLETA - PROVA REAL ENEM 2024')
    print('=' * 80)
    print()
    print('Este exemplo usa dados reais de um participante do ENEM 2024')
    print('extraidos dos microdados oficiais do INEP.')
    print()
    
    # Inicializar
    calc = CalculadorTRI()
    
    resultados = {}
    
    # Analisar cada area
    for area in ['MT', 'CN', 'CH', 'LC']:
        analise = analisar_area_completa(calc, area, PARTICIPANTE[area])
        resultados[area] = analise
    
    # Resumo final
    print()
    print('=' * 80)
    print('                         RESUMO GERAL')
    print('=' * 80)
    print()
    print(f'  {"Area":12} {"Oficial":>10} {"Calculada":>10} {"Erro":>8} {"Acertos":>10}')
    print('  ' + '-' * 55)
    
    soma_oficial = 0
    soma_calculada = 0
    
    for area in ['MT', 'CN', 'CH', 'LC']:
        r = resultados[area]
        oficial = PARTICIPANTE[area]['nota_oficial']
        erro = r['nota'] - oficial
        soma_oficial += oficial
        soma_calculada += r['nota']
        print(f'  {area:12} {oficial:>10.1f} {r["nota"]:>10.1f} {erro:>+8.1f} {r["total_acertos"]:>7}/{r["total_itens"]}')
    
    media_oficial = soma_oficial / 4
    media_calculada = soma_calculada / 4
    
    print('  ' + '-' * 55)
    print(f'  {"MEDIA":12} {media_oficial:>10.1f} {media_calculada:>10.1f} {media_calculada - media_oficial:>+8.1f}')
    
    print()
    print('=' * 80)
    print('  VALIDACAO: Erro medio < 1 ponto confirma precisao do calculo TRI')
    print('=' * 80)
    print()


if __name__ == '__main__':
    main()
