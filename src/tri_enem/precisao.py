# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Verificação de precisão de provas.

Módulo leve para verificar se uma prova tem calibração confiável.
Fonte única de verdade: coeficientes_data.json (gerado por tools/calibrar_com_mapeamento.py).
"""

import json
from pathlib import Path
from typing import Dict


# Limiares (mesmos usados em tools/calibrar_com_mapeamento.py)
MAE_OK         = 2.0
MAE_AVISO_LEVE = 5.0
MAE_AVISO_FORTE = 15.0


def verificar_precisao_prova(ano: int, area: str, co_prova: int) -> Dict:
    """
    Verifica a precisão estimada de uma prova a partir do coeficientes_data.json.

    Args:
        ano: Ano da prova (2009-2025)
        area: Área (LC, CH, CN, MT)
        co_prova: Código da prova

    Returns:
        dict com:
            - 'mae': Mean Absolute Error (pontos) ou None
            - 'r_squared': R² ou None
            - 'confiavel': True se a prova é confiável
            - 'aviso': Mensagem de aviso para o usuário (ou None)
            - 'status': 'ok' | 'aviso_leve' | 'aviso_forte' | 'erro_alto' |
                        'falhou' | 'nao_calibrado' | 'desconhecido'
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

    # --- Status qualitativo (status_provas) ---
    status_info = data.get('status_provas', {}).get(key)
    if status_info:
        status = status_info.get('status', 'desconhecido')
        resultado['status'] = status

        mensagem_raw = status_info.get('mensagem')
        if mensagem_raw and 'Poucos participantes' in mensagem_raw:
            resultado['aviso'] = (
                "⚠️ Esta prova não possui participantes suficientes nos microdados públicos do INEP. "
                "Estamos usando calibração genérica da área, o que pode resultar em nota menos precisa."
            )
        else:
            resultado['aviso'] = mensagem_raw

        resultado['confiavel'] = status in ('ok', 'aviso_leve', 'aviso_forte')

    elif resultado['mae'] is not None:
        # Status não registrado: classificar pelo MAE medido
        mae = resultado['mae']
        if mae <= MAE_OK:
            resultado['status']    = 'ok'
        elif mae <= MAE_AVISO_LEVE:
            resultado['status']    = 'aviso_leve'
            resultado['aviso']     = (
                f"ℹ️ Esta prova tem boa calibração, mas pode haver diferença de até "
                f"{mae:.1f} pontos em relação à nota oficial."
            )
        elif mae <= MAE_AVISO_FORTE:
            resultado['status']    = 'aviso_forte'
            resultado['confiavel'] = True
            resultado['aviso']     = (
                f"⚠️ Atenção: calibração parcial. Erro médio de {mae:.1f} pontos. "
                "Use como estimativa."
            )
        else:
            resultado['status']    = 'erro_alto'
            resultado['confiavel'] = False
            resultado['aviso']     = (
                f"⚠️ ATENÇÃO: Esta prova não está calibrada corretamente. "
                f"Erro médio de {mae:.1f} pontos — a nota pode variar bastante da oficial."
            )
    else:
        # Prova completamente desconhecida
        resultado['status']    = 'nao_calibrado'
        resultado['confiavel'] = False
        resultado['aviso']     = (
            "⚠️ Esta prova não possui calibração específica. "
            "Estamos usando parâmetros genéricos da área — use como estimativa."
        )

    return resultado
