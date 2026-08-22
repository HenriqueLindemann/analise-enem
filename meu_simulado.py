#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora Nota TRI ENEM - Script de Simulação Local

COMO USAR:
    1. Preencha suas respostas abaixo (45 letras: A, B, C, D, E ou .)
    2. Defina o ano, cor da prova e tipo de aplicação
    3. Execute: python meu_simulado.py
    4. Veja sua nota e gere um relatório PDF!

Site: https://notatri.com
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
TITULO_RELATORIO = 'Desempenho no Simulado ENEM'

# ============================================================================
#                    NÃO MODIFIQUE ABAIXO DESTA LINHA
# ============================================================================

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from tri_enem import CalculadorTRI, MapeadorProvas
from tri_enem.config import NOMES_AREAS
from tri_enem.formatacao import formatar_numero
from tri_enem.posicoes import normalizar_posicoes_resultados


def validar_respostas(respostas, nome):
    if not respostas or respostas == "." * 45:
        return True
    if len(respostas) != 45:
        print(f"ERRO: {nome} deve ter 45 respostas, tem {len(respostas)}")
        return False
    invalidas = [c for c in respostas.upper() if c not in 'ABCDE.*']
    if invalidas:
        print(f"ERRO: {nome} tem caracteres invalidos: {set(invalidas)}")
        return False
    return True


def calcular_e_analisar(calc, area, ano, respostas, lingua=None, co_prova=None, cor_prova=None, tipo_aplicacao='1a_aplicacao'):
    if not respostas or respostas == "." * 45:
        return None
    try:
        # Resolver código se foi fornecida cor
        if co_prova is None and cor_prova:
            mapeador = MapeadorProvas()
            co_prova = mapeador.obter_codigo(ano, area, tipo_aplicacao, cor_prova)
        
        if area == "LC":
            lingua_norm = str(lingua or "").strip().lower()
            if lingua_norm in {"ingles", "inglês"}:
                tp_lingua = 0
            elif lingua_norm in {"espanhol", "español"}:
                tp_lingua = 1
            else:
                raise ValueError("Para LC, informe LINGUA='ingles' ou 'espanhol'")
        else:
            tp_lingua = None
        analise = calc.analisar_todas_questoes(ano, area, co_prova, respostas, tp_lingua)
        
        # Falhas inesperadas desta camada chegam ao tratamento externo, que
        # mostra a causa no CLI em vez de ocultá-la.
        from tri_enem import (
            formatar_resumo_validacao,
            verificar_precisao_prova,
        )
        precisao = verificar_precisao_prova(ano, area, co_prova)
        
        resultado = {
            'sigla': area,
            'nome': NOMES_AREAS.get(area, area),
            'ano': ano,
            'co_prova': co_prova,
            'nota': analise['nota'],
            'theta': analise['theta'],
            'acertos': analise['total_acertos'],
            'total_itens': analise['total_itens'],
            'total_anulados': analise.get('total_anulados', 0),
            'questoes_acertadas': analise['acertos'],
            'questoes_erradas': analise['erros'],
            'questoes_anuladas': analise.get('questoes_anuladas', []),
            'anuladas': analise.get('anuladas', []),
            'lingua': lingua if area == 'LC' else None,
            'cor_prova': cor_prova,
            'aviso_precisao': precisao.get("aviso"),
            'severidade_precisao': precisao.get("severidade"),
            'status_precisao': precisao.get("status"),
            'perfil_precisao': precisao.get("perfil"),
            'n_validacao': precisao.get("n_validacao"),
            'mae_validacao': precisao.get("mae"),
            'erro_p95': precisao.get("erro_p95"),
            'erro_maximo': precisao.get("erro_maximo"),
            'n_acima_2': precisao.get("n_acima_2"),
            'resumo_validacao': formatar_resumo_validacao(precisao),
        }
        return normalizar_posicoes_resultados(
            [resultado],
            MapeadorProvas().listar_ordem_provas(ano),
        )[0]
    except Exception as e:
        print(f"Erro ao calcular {area}: {e}")
        return None


def gerar_relatorio_pdf(resultados, ano, titulo, nome_arquivo=None, tipo_aplicacao='', cor_prova=''):
    try:
        from tri_enem.relatorios import (
            RelatorioPDF,
            adaptar_resultados_para_relatorio,
        )
    except ImportError:
        print("Instale reportlab: pip install reportlab")
        return None
    
    dados = adaptar_resultados_para_relatorio(
        resultados,
        ano,
        titulo=titulo,
        tipo_aplicacao=tipo_aplicacao,
        cor_prova=cor_prova,
        origem_geracao="github.com/HenriqueLindemann/analise-enem",
    )
    
    if not nome_arquivo:
        raiz = Path(__file__).parent
        nome_arquivo = str(raiz / "relatorios" / f"resultado_enem_{ano}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    try:
        relatorio = RelatorioPDF()
        return relatorio.gerar(dados, nome_arquivo)
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def formatar_contagem_resultado(resultado):
    """Formata acertos e anuladas para a saída do CLI."""
    total_anulados = resultado.get('total_anulados', 0)
    if not total_anulados:
        return f"{resultado['acertos']}/{resultado['total_itens']}"

    label_anuladas = 'anulada' if total_anulados == 1 else 'anuladas'
    return (
        f"{resultado['acertos']}/{resultado['total_itens']} válidas + "
        f"{total_anulados} {label_anuladas}"
    )


def main():
    print()
    print("=" * 60)
    print(f"       CALCULADORA NOTA TRI ENEM - PROVA {ANO}")
    print("=" * 60)
    
    # Ordem: Dia 1 (LC, CH) -> Dia 2 (CN, MT)
    areas = [
        ('LC', 'Linguagens', RESPOSTAS_LC, COR_LC),
        ('CH', 'Ciências Humanas', RESPOSTAS_CH, COR_CH),
        ('CN', 'Ciências da Natureza', RESPOSTAS_CN, COR_CN),
        ('MT', 'Matemática', RESPOSTAS_MT, COR_MT),
    ]
    
    for sigla, nome, resp, cor in areas:
        if not validar_respostas(resp, nome):
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
        if not resp or resp == "." * 45:
            print(f"{nome:.<35} NÃO PREENCHIDO")
            continue
        
        res = calcular_e_analisar(calc, sigla, ANO, resp,
                                  lingua=LINGUA if sigla == 'LC' else None,
                                  cor_prova=cor,
                                  tipo_aplicacao=TIPO_APLICACAO)
        if res:
            resultados.append(res)
            notas[sigla] = res['nota']
            nota_texto = formatar_numero(res['nota'])
            print(
                f"{nome:.<35} {nota_texto:>6} pts "
                f"({formatar_contagem_resultado(res)})"
            )
            if res.get("resumo_validacao"):
                print(f"  {sigla}: {res['resumo_validacao']}")
            if res.get('aviso_precisao'):
                avisos.append(f"  {sigla}: {res['aviso_precisao']}")
    
    if notas:
        print("-" * 60)
        media_texto = formatar_numero(sum(notas.values()) / len(notas))
        print(f"{'MÉDIA':.<35} {media_texto:>6} pts")
    
    # Mostrar mensagens de validação, inclusive a confirmação positiva das
    # provas com boa calibração.
    if avisos:
        print("\n" + "-" * 60)
        print("VALIDACAO DAS PROVAS:")
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
    print("Nota estimada com TRI e verificada contra microdados oficiais")
    print("Contribua: github.com/HenriqueLindemann/analise-enem")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
