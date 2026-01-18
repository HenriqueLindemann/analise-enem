#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEU SIMULADO ENEM - Calculador de Nota TRI

COMO USAR:
    1. Preencha suas respostas abaixo (45 letras: A, B, C, D, E ou .)
    2. Defina o ano e codigo da prova
    3. Execute: python meu_simulado.py
    4. Veja sua nota e gere um relatorio PDF!

Desenvolvido por Henrique Lindemann - Eng. Computacao UFRGS
"""

# ============================================================================
#                           CONFIGURACOES
# ============================================================================

ANO = 2024

# Codigos de prova (consulte docs/GUIA_PROVAS.md)
CO_PROVA_MT = 1410
CO_PROVA_CN = 1422
CO_PROVA_CH = 1384
CO_PROVA_LC = 1396

LINGUA = 'ingles'  # ou 'espanhol'

# Suas respostas (45 caracteres cada)
RESPOSTAS_MT = 'DBCEECACBDBAADDDDDDCBCDCCAADACCEBBECADACBADDD'
RESPOSTAS_CN = 'DBCCCBBDEBBCEEDDBECCBCBCAADDDDABBECBCEECEAACD'
RESPOSTAS_CH = 'BADDBCDCECADEBBBEBCEBADACBCADEDBEACBAECAECEDA'
RESPOSTAS_LC = 'AACEADADECBBDBDEBDADCCBEDDCDEBBDEDDEBDCECEDDC'

# Opcoes de relatorio
GERAR_PDF = True
NOME_PDF = None  # None = nome automatico
TITULO_RELATORIO = 'Meu Simulado ENEM'

# ============================================================================
#                    NAO MODIFIQUE ABAIXO DESTA LINHA
# ============================================================================

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from tri_enem import CalculadorTRI
from tri_enem.config import NOMES_AREAS


def validar_respostas(respostas, nome):
    if len(respostas) != 45:
        print(f"ERRO: {nome} deve ter 45 respostas, tem {len(respostas)}")
        return False
    invalidas = [c for c in respostas.upper() if c not in 'ABCDE.']
    if invalidas:
        print(f"ERRO: {nome} tem caracteres invalidos: {set(invalidas)}")
        return False
    return True


def calcular_e_analisar(calc, area, ano, respostas, lingua=None, co_prova=None):
    if respostas == "." * 45:
        return None
    try:
        tp_lingua = 0 if lingua == 'ingles' else 1 if area == 'LC' else None
        analise = calc.analisar_todas_questoes(ano, area, co_prova, respostas, tp_lingua)
        
        # Verificar precisão da prova
        aviso = None
        try:
            from tri_enem.relatorios import verificar_precisao_prova
            precisao = verificar_precisao_prova(ano, area, co_prova)
            if precisao.get('aviso'):
                aviso = precisao['aviso']
        except:
            pass
        
        return {
            'sigla': area,
            'nome': NOMES_AREAS.get(area, area),
            'ano': ano,
            'co_prova': co_prova,
            'nota': analise['nota'],
            'theta': analise['theta'],
            'acertos': analise['total_acertos'],
            'total_itens': analise['total_itens'],
            'questoes_acertadas': analise['acertos'],
            'questoes_erradas': analise['erros'],
            'lingua': lingua if area == 'LC' else None,
            'aviso_precisao': aviso,
        }
    except Exception as e:
        print(f"Erro ao calcular {area}: {e}")
        return None


def gerar_relatorio_pdf(resultados, ano, titulo, nome_arquivo=None):
    try:
        from tri_enem.relatorios import RelatorioPDF, DadosRelatorio
        from tri_enem.relatorios.base import AreaAnalise, QuestaoAnalise
    except ImportError:
        print("Instale reportlab: pip install reportlab")
        return None
    
    dados = DadosRelatorio(titulo=titulo, ano_prova=ano)
    
    for r in resultados:
        questoes = []
        for q in r['questoes_acertadas']:
            questoes.append(QuestaoAnalise(
                posicao=q['posicao'], gabarito=q['gabarito'],
                resposta_dada=q['resposta_dada'], acertou=True,
                param_a=q['param_a'], param_b=q['param_b'], param_c=q['param_c'],
                impacto=q['perda_se_errasse'], co_item=q.get('co_item'),
            ))
        for q in r['questoes_erradas']:
            questoes.append(QuestaoAnalise(
                posicao=q['posicao'], gabarito=q['gabarito'],
                resposta_dada=q['resposta_dada'], acertou=False,
                param_a=q['param_a'], param_b=q['param_b'], param_c=q['param_c'],
                impacto=q['ganho_se_acertasse'], co_item=q.get('co_item'),
            ))
        
        area = AreaAnalise(
            sigla=r['sigla'], nome=r['nome'], ano=r['ano'], co_prova=r['co_prova'],
            nota=r['nota'], theta=r['theta'], acertos=r['acertos'],
            total_itens=r['total_itens'], questoes=questoes, lingua=r.get('lingua'),
        )
        dados.areas.append(area)
    
    if not nome_arquivo:
        nome_arquivo = f"relatorios/resultado_enem_{ano}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    try:
        relatorio = RelatorioPDF()
        return relatorio.gerar(dados, nome_arquivo)
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


CODIGOS = {'MT': CO_PROVA_MT, 'CN': CO_PROVA_CN, 'CH': CO_PROVA_CH, 'LC': CO_PROVA_LC}


def main():
    print()
    print("=" * 60)
    print(f"           CALCULADOR DE NOTA TRI - ENEM {ANO}")
    print("=" * 60)
    
    areas = {
        'MT': ('Matematica', RESPOSTAS_MT),
        'CN': ('Ciencias da Natureza', RESPOSTAS_CN),
        'CH': ('Ciencias Humanas', RESPOSTAS_CH),
        'LC': ('Linguagens', RESPOSTAS_LC),
    }
    
    for sigla, (nome, resp) in areas.items():
        if resp != "." * 45 and not validar_respostas(resp, nome):
            return
    
    print("\nCarregando dados...")
    calc = CalculadorTRI()
    
    print("\n" + "-" * 60)
    print("RESULTADOS")
    print("-" * 60)
    
    resultados = []
    notas = {}
    avisos = []
    
    for sigla, (nome, resp) in areas.items():
        if resp == "." * 45:
            print(f"{nome:.<35} NAO PREENCHIDO")
            continue
        
        res = calcular_e_analisar(calc, sigla, ANO, resp,
                                  lingua=LINGUA if sigla == 'LC' else None,
                                  co_prova=CODIGOS.get(sigla))
        if res:
            resultados.append(res)
            notas[sigla] = res['nota']
            print(f"{nome:.<35} {res['nota']:>6.1f} pts ({res['acertos']}/{res['total_itens']})")
            if res.get('aviso_precisao'):
                avisos.append(f"  {sigla}: {res['aviso_precisao']}")
    
    if notas:
        print("-" * 60)
        print(f"{'MEDIA':.<35} {sum(notas.values())/len(notas):>6.1f} pts")
    
    # Mostrar avisos de precisão
    if avisos:
        print("\n" + "-" * 60)
        print("AVISOS DE PRECISAO:")
        for aviso in avisos:
            print(aviso)
    
    if GERAR_PDF and resultados:
        print("\n" + "-" * 60)
        print("Gerando relatorio PDF...")
        caminho = gerar_relatorio_pdf(resultados, ANO, TITULO_RELATORIO, NOME_PDF)
        if caminho:
            print(f"Relatorio salvo: {caminho}")
    
    print("\n" + "=" * 60)
    print("Calculo aproximado - erro tipico < 1 ponto para provas calibradas")
    print("Contribua: github.com/HenriqueLindemann/analise-enem")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
