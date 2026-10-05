# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Mapeador dos seletores de prova da interface."""

from typing import Dict, List, Tuple
import streamlit as st

from tri_enem import CalculadorTRI, MapeadorProvas
from streamlit_app.calculador import _criar_calculador, _criar_mapeador


class MapeadorInterface:
    """Mapeador que oferece só cadernos com itens, incluindo os especiais.

    O mapeamento registra alguns cadernos especiais sem itens nos microdados
    (2009 e os ampliados de 2020); eles ficam fora dos seletores.
    """

    def __init__(self, mapeador: MapeadorProvas, calculador: CalculadorTRI):
        self._mapeador = mapeador
        self._calculador = calculador
        self._calculaveis: Dict[Tuple[int, str, str], List[str]] = {}

    def __getattr__(self, nome):
        return getattr(self._mapeador, nome)

    def listar_tipos_disponiveis(self, ano: int, area: str) -> List[str]:
        tipos = self._mapeador.listar_tipos_disponiveis(ano, area)
        if self.listar_cores_disponiveis(ano, area, "especiais"):
            tipos.append("especiais")
        return tipos

    def listar_cores_disponiveis(self, ano: int, area: str, tipo_aplicacao: str) -> List[str]:
        chave = (int(ano), area, tipo_aplicacao)
        if chave not in self._calculaveis:
            self._calculaveis[chave] = [
                cor for cor in self._mapeador.listar_cores_disponiveis(ano, area, tipo_aplicacao)
                if self._tem_itens(ano, area, self._mapeador.obter_codigo(ano, area, tipo_aplicacao, cor))
            ]
        return list(self._calculaveis[chave])

    def _tem_itens(self, ano: int, area: str, co_prova: int) -> bool:
        for lingua in ((0, 1) if area.upper() == "LC" else (None,)):
            try:
                if self._calculador.carregar_itens(ano, area, co_prova, lingua):
                    return True
            except ValueError:
                pass
        return False


@st.cache_resource(show_spinner=False)
def get_mapeador_interface() -> MapeadorInterface:
    """Mapeador da interface, com o calculador e o mapeador em cache."""
    return MapeadorInterface(_criar_mapeador(), _criar_calculador())
