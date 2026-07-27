# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Confiabilidade da nota calculada, por prova.

Fonte única de verdade: coeficientes_data.json (gerado por
tools/calibrar_com_mapeamento.py e atualizado por
tests/validar_exemplos_microdados.py --atualizar-status).

Causas de imprecisão por prova
------------------------------
A nota depende de dois insumos. Os parâmetros TRI dos itens (a, b, c) vêm do
ITENS_PROVA_<ano>.csv. Os coeficientes de equalização (slope, intercept) não
são publicados pelo INEP: são estimados por regressão entre o theta calculado
e a nota oficial de participantes reais da prova.

Três causas distintas de imprecisão, em ordem de frequência:

1. Ausência de participantes. A prova não possui participantes nos microdados
   públicos (comum em PPL e reaplicações), o que impede estimar slope e
   intercept específicos; aplica-se a média da área.

2. Ambiguidade estrutural do arquivo do ano. Provas adaptadas
   (IN_ITEM_ADAPTADO = 1) trazem mais de um item para a mesma CO_POSICAO, com
   gabarito e parâmetros distintos, e o arquivo não registra qual deles foi
   apresentado ao participante. Em 2013-CH-187, 2013-CN-188, 2013-MT-190 e
   2013-LC-189 a correlação entre theta e nota oficial fica próxima de zero, e
   nenhuma escolha de duplicata as recupera.

3. Divergência não explicada. Ver abaixo.

Os limiares abaixo separam esses regimes pelo MAE (erro médio absoluto, em
pontos da escala 0-1000) medido contra notas oficiais.

Provas que não reproduzem a nota (2017 e 2019)
----------------------------------------------
1as aplicações de 2017 em CN, CH e MT, e MT de 2019. Investigado em 2026-07,
causa desconhecida; ficam sinalizadas como erro_alto.

Verificados e corretos: o pareamento resposta/item, o gabarito e o modelo —
em 2018 e 2023 a nota oficial é reproduzida com resíduo mediano zero. Por
eliminação restam os parâmetros publicados, mas isso não está provado.

Duas medições foram tentadas e não servem: o refit dos parâmetros item a item
reprova no controle (2018-MT-459 dá MAE 19,66 onde o correto é 0,10), e o
ajuste da curva empírica depende do coeficiente canônico da área, que é
justamente o que não vale nessas provas.

LC 2009 já constou aqui como irrecuperável. Estava errado: um item anulado sem
CO_ITEM era descartado, deslocando as respostas seguintes. Corrigido, a
correlação com a nota oficial é 1,000000.
"""

import json
from pathlib import Path
from typing import Dict


# Limiares de MAE em pontos (mesmos usados em tools/calibrar_com_mapeamento.py)
MAE_OK          = 2.0   # indistinguível da nota oficial na prática
MAE_AVISO_LEVE  = 5.0   # diferença perceptível, mas pequena
MAE_AVISO_FORTE = 15.0  # estimativa; acima disso a nota não é confiável

# Severidade sugerida para a interface (info < atencao < alerta), utilizada
# para selecionar entre st.info, st.warning e st.error. Anteriormente todo
# aviso era exibido como erro, inclusive os meramente informativos.
SEVERIDADE_POR_STATUS = {
    'ok':            None,
    'aviso_leve':    'info',
    'aviso_forte':   'atencao',
    'erro_alto':     'alerta',
    'falhou':        'atencao',
    'nao_calibrado': 'atencao',
    'desconhecido':  None,
}


def _msg_sem_participantes() -> str:
    return (
        "Prova sem participantes nos microdados públicos do INEP. Não há dados para "
        "ajustar esta prova individualmente; foi aplicado o ajuste médio da área. "
        "O resultado deve ser interpretado como estimativa."
    )


def _msg_por_mae(mae: float) -> str:
    """Mensagem ao usuário final, expressa em pontos de diferença para a nota oficial."""
    if mae <= MAE_AVISO_LEVE:
        unidade = "ponto" if mae < 2 else "pontos"
        return (
            f"Diferença média de {mae:.0f} {unidade} em relação à nota oficial "
            "desta prova."
        )
    if mae <= MAE_AVISO_FORTE:
        return (
            f"Precisão reduzida nesta prova: diferença média de {mae:.0f} pontos em "
            "relação à nota oficial. O resultado deve ser interpretado como estimativa."
        )
    return (
        f"Esta prova não reproduz a nota oficial com precisão: diferença média de "
        f"{mae:.0f} pontos. A contagem de acertos e a análise por questão permanecem "
        "válidas; a nota deve ser considerada apenas como referência aproximada."
    )


def _msg_nao_calibrada() -> str:
    return (
        "Prova não conferida contra notas oficiais. Foi aplicado o ajuste médio da "
        "área; o resultado deve ser interpretado como estimativa."
    )


def _msg_nao_reproduz() -> str:
    """
    Prova conferida que reprovou, e por isso ficou sem coeficiente próprio.

    Sem essa mensagem cairia em _msg_nao_calibrada, que diz o contrário do que
    aconteceu.
    """
    return (
        "Esta prova foi conferida contra notas oficiais e não as reproduz. A "
        "contagem de acertos e a análise por questão permanecem válidas; a nota "
        "deve ser considerada apenas como referência aproximada."
    )


def verificar_precisao_prova(ano: int, area: str, co_prova: int) -> Dict:
    """
    Avalia a confiabilidade da nota calculada para uma prova.

    Args:
        ano: Ano da prova (2009-2025)
        area: Área (LC, CH, CN, MT)
        co_prova: Código da prova

    Returns:
        dict com:
            - 'mae': erro médio absoluto em pontos, ou None se desconhecido
            - 'r_squared': R² do ajuste, ou None
            - 'confiavel': False quando a nota não deve ser tomada como exata
            - 'aviso': mensagem destinada ao usuário final, ou None quando a
                       precisão da prova dispensa sinalização
            - 'severidade': None | 'info' | 'atencao' | 'alerta'
            - 'status': 'ok' | 'aviso_leve' | 'aviso_forte' | 'erro_alto' |
                        'falhou' | 'nao_calibrado' | 'desconhecido'

    Invariante: quando 'confiavel' é False, 'aviso' nunca é None. Prova cuja
    nota não é confiável jamais é repassada à interface sem sinalização.
    """
    try:
        ano      = int(ano)
        co_prova = int(co_prova)
    except (ValueError, TypeError):
        pass

    resultado = {
        'mae':        None,
        'r_squared':  None,
        'confiavel':  True,
        'aviso':      None,
        'severidade': None,
        'status':     'desconhecido',
    }

    data_file = Path(__file__).parent / 'coeficientes_data.json'
    if not data_file.exists():
        return resultado

    try:
        data = json.loads(data_file.read_text(encoding='utf-8'))
    except Exception:
        return resultado

    key = f"{ano},{area},{co_prova}"

    # --- Métricas numéricas (por_prova) ---
    info = data.get('por_prova', {}).get(key)
    if info:
        resultado['mae']       = info.get('mae')
        resultado['r_squared'] = info.get('r_squared')

    status_info = data.get('status_provas', {}).get(key)
    mae = resultado['mae']

    if status_info:
        status = status_info.get('status', 'desconhecido')
        resultado['status'] = status
        resultado['confiavel'] = status in ('ok', 'aviso_leve', 'aviso_forte')

        mensagem_raw = status_info.get('mensagem') or ''

        if 'Poucos participantes' in mensagem_raw or status == 'falhou':
            resultado['aviso'] = _msg_sem_participantes()
        elif status == 'ok':
            resultado['aviso'] = None
        elif mae is not None:
            # A mensagem é sempre derivada do MAE, e não lida do JSON: os textos
            # gravados vieram de versões distintas do calibrador, com redações
            # divergentes, e em 16 provas com erro_alto estavam ausentes, caso em
            # que a interface não exibia aviso algum.
            resultado['aviso'] = _msg_por_mae(mae)
        elif status == 'erro_alto':
            resultado['aviso'] = _msg_nao_reproduz()
        else:
            resultado['aviso'] = _msg_nao_calibrada()

    elif mae is not None:
        # Sem status registrado: classificar pelo MAE medido
        if mae <= MAE_OK:
            resultado['status'] = 'ok'
        elif mae <= MAE_AVISO_LEVE:
            resultado['status'] = 'aviso_leve'
            resultado['aviso']  = _msg_por_mae(mae)
        elif mae <= MAE_AVISO_FORTE:
            resultado['status'] = 'aviso_forte'
            resultado['aviso']  = _msg_por_mae(mae)
        else:
            resultado['status']    = 'erro_alto'
            resultado['confiavel'] = False
            resultado['aviso']     = _msg_por_mae(mae)

    else:
        # Prova completamente desconhecida
        resultado['status']    = 'nao_calibrado'
        resultado['confiavel'] = False
        resultado['aviso']     = _msg_nao_calibrada()

    resultado['severidade'] = SEVERIDADE_POR_STATUS.get(resultado['status'])

    # Garantia final do invariante: prova não confiável sempre acompanha
    # mensagem e severidade.
    if not resultado['confiavel']:
        if not resultado['aviso']:
            resultado['aviso'] = (_msg_nao_reproduz()
                                  if resultado['status'] == 'erro_alto'
                                  else _msg_nao_calibrada())
        if not resultado['severidade']:
            resultado['severidade'] = 'alerta'

    return resultado
