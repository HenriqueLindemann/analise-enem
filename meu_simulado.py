#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEU SIMULADO ENEM - Calculador de Nota TRI

COMO USAR:
    1. Preencha suas respostas abaixo (45 letras: A, B, C, D, E ou .)
    2. Defina o ano, cor da prova e tipo de aplicação
    3. Execute: python meu_simulado.py
    4. Veja sua nota e gere um relatório PDF!

Desenvolvido por Henrique Lindemann - Eng. Computação UFRGS
"""

# ============================================================================
#                           CONFIGURAÇÕES
# ============================================================================

ANO = 2021

# TIPO DE APLICAÇÃO
# Opções: '1a_aplicacao', 'digital', 'reaplicacao', 'segunda_oportunidade'
TIPO_APLICACAO = '1a_aplicacao'

# LÍNGUA ESTRANGEIRA (para Linguagens e Códigos)
LINGUA = 'ingles'  # ou 'espanhol'

# ============================================================================
#                     DIA 1: LINGUAGENS E CIÊNCIAS HUMANAS
# ============================================================================

# COR DA PROVA (azul, amarela, rosa, cinza, branca, verde)
# Dica: A cor está na capa do caderno de questões

COR_LC = 'rosa'
RESPOSTAS_LC = 'ACABCDCEACABCACCBEABDCCDBEDDDBBBACCDCDCCEBBCB'

COR_CH = 'rosa'
RESPOSTAS_CH = 'EDAAAADBCAABBABEECBBAEEBBBADCBCBBCEDDEBBCAEAB'

# ============================================================================
#                     DIA 2: CIÊNCIAS DA NATUREZA E MATEMÁTICA
# ============================================================================

COR_CN = 'rosa'
RESPOSTAS_CN = 'DABCEDEBEECBEABEBDCBCBECBADCDBABBACCCDBDBEBAB'

COR_MT = 'rosa'
RESPOSTAS_MT = 'DCCAEBABDDCABEACCBCCEEADDCEACDEAADCABBDBDEDCE'

# OPÇÕES DE RELATÓRIO
GERAR_PDF = True
NOME_PDF = None  # None = nome automático
TITULO_RELATORIO = 'Simulador nota ENEM'

# ============================================================================
#                    NÃO MODIFIQUE ABAIXO DESTA LINHA
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


def calcular_e_analisar(calc, area, ano, respostas, lingua=None, co_prova=None, cor_prova=None, tipo_aplicacao='1a_aplicacao'):
    if respostas == "." * 45:
        return None
    try:
        # Resolver código se foi fornecida cor
        if co_prova is None and cor_prova:
            from tri_enem import MapeadorProvas
            mapeador = MapeadorProvas()
            co_prova = mapeador.obter_codigo(ano, area, tipo_aplicacao, cor_prova)
        
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
            'cor_prova': cor_prova,
            'aviso_precisao': aviso,
        }
    except Exception as e:
        print(f"Erro ao calcular {area}: {e}")
        return None


def gerar_relatorio_pdf(resultados, ano, titulo, nome_arquivo=None, tipo_aplicacao='', cor_prova=''):
    try:
        from tri_enem.relatorios import RelatorioPDF, DadosRelatorio
        from tri_enem.relatorios.base import AreaAnalise, QuestaoAnalise
    except ImportError:
        print("Instale reportlab: pip install reportlab")
        return None
    
    # Formatar tipo de aplicação para exibição
    tipos_extenso = {
        '1a_aplicacao': '1ª Aplicação',
        'digital': 'Digital',
        'reaplicacao': 'Reaplicação',
        'segunda_oportunidade': 'Segunda Oportunidade',
    }
    tipo_extenso = tipos_extenso.get(tipo_aplicacao, tipo_aplicacao)
    
    dados = DadosRelatorio(
        titulo=titulo, 
        ano_prova=ano,
        tipo_aplicacao=tipo_extenso,
        cor_prova=cor_prova.capitalize() if cor_prova else ''
    )
    
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
            cor_prova=r.get('cor_prova'),
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


def main():
    print()
    print("=" * 60)
    print(f"           CALCULADOR DE NOTA TRI - ENEM {ANO}")
    print("=" * 60)
    
    # Ordem: Dia 1 (LC, CH) -> Dia 2 (CN, MT)
    areas = [
        ('LC', 'Linguagens', RESPOSTAS_LC, COR_LC),
        ('CH', 'Ciências Humanas', RESPOSTAS_CH, COR_CH),
        ('CN', 'Ciências da Natureza', RESPOSTAS_CN, COR_CN),
        ('MT', 'Matemática', RESPOSTAS_MT, COR_MT),
    ]
    
    for sigla, nome, resp, cor in areas:
        if resp != "." * 45 and not validar_respostas(resp, nome):
            return
    
    print(f"\nAplicação: {TIPO_APLICACAO}")
    print("\nCarregando dados...")
    calc = CalculadorTRI()
    
    print("\n" + "-" * 60)
    print("RESULTADOS")
    print("-" * 60)
    
    resultados = []
    notas = {}
    avisos = []
    
    for sigla, nome, resp, cor in areas:
        if resp == "." * 45:
            print(f"{nome:.<35} NÃO PREENCHIDO")
            continue
        
        res = calcular_e_analisar(calc, sigla, ANO, resp,
                                  lingua=LINGUA if sigla == 'LC' else None,
                                  cor_prova=cor,
                                  tipo_aplicacao=TIPO_APLICACAO)
        if res:
            resultados.append(res)
            notas[sigla] = res['nota']
            print(f"{nome:.<35} {res['nota']:>6.1f} pts ({res['acertos']}/{res['total_itens']})")
            if res.get('aviso_precisao'):
                avisos.append(f"  {sigla}: {res['aviso_precisao']}")
    
    if notas:
        print("-" * 60)
        print(f"{'MÉDIA':.<35} {sum(notas.values())/len(notas):>6.1f} pts")
    
    # Mostrar avisos de precisão
    if avisos:
        print("\n" + "-" * 60)
        print("⚠️  AVISOS DE PRECISÃO:")
        print("-" * 60)
        for aviso in avisos:
            print(aviso)
        print("\nNota: Provas não calibradas ou com erro alto podem ter\n"
              "      diferença significativa em relação à nota oficial.")
    
    if GERAR_PDF and resultados:
        print("\n" + "-" * 60)
        print("Gerando relatorio PDF...")
        # Usar a primeira cor encontrada (normalmente todas são iguais)
        cor_predominante = COR_LC or COR_CH or COR_CN or COR_MT
        caminho = gerar_relatorio_pdf(
            resultados, ANO, TITULO_RELATORIO, NOME_PDF,
            tipo_aplicacao=TIPO_APLICACAO,
            cor_prova=cor_predominante
        )
        if caminho:
            print(f"Relatorio salvo: {caminho}")
    
    print("\n" + "=" * 60)
    print("Cálculo aproximado - erro típico < 1 ponto para provas calibradas")
    print("Contribua: github.com/HenriqueLindemann/analise-enem")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
