# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Wrapper para integração com o módulo tri_enem.

Facilita o uso do calculador TRI no contexto do Streamlit.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import streamlit as st

# Adicionar path do src
_src_path = Path(__file__).parent.parent / 'src'
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from tri_enem import CalculadorTRI, MapeadorProvas
from tri_enem.config import NOMES_AREAS


@st.cache_resource(show_spinner=False)
def _criar_calculador():
    """Cria instância do CalculadorTRI com cache."""
    return CalculadorTRI()


@st.cache_resource(show_spinner=False)
def _criar_mapeador():
    """Cria instância do MapeadorProvas com cache."""
    return MapeadorProvas()


class CalculadorEnem:
    """
    Wrapper simplificado para cálculo de notas TRI.
    
    Encapsula a lógica de mapeamento de provas e cálculo TRI
    para uso fácil no Streamlit.
    """
    
    def __init__(self):
        """Inicializa o calculador e mapeador com cache."""
        self._calculador = _criar_calculador()
        self._mapeador = _criar_mapeador()
    
    @property
    def mapeador(self) -> MapeadorProvas:
        """Retorna o mapeador de provas."""
        return self._mapeador
    
    def listar_anos(self) -> List[int]:
        """Lista todos os anos disponíveis."""
        return self._mapeador.listar_anos_disponiveis()
    
    def listar_tipos(self, ano: int, area: str) -> List[str]:
        """Lista tipos de aplicação disponíveis."""
        return self._mapeador.listar_tipos_disponiveis(ano, area)
    
    def listar_cores(self, ano: int, area: str, tipo: str) -> List[str]:
        """Lista cores disponíveis."""
        return self._mapeador.listar_cores_disponiveis(ano, area, tipo)
    
    def calcular_area(
        self,
        ano: int,
        area: str,
        respostas: str,
        cor: str,
        tipo_aplicacao: str = '1a_aplicacao',
        lingua: str = 'ingles'
    ) -> Optional[Dict]:
        """
        Calcula nota TRI para uma área específica.
        
        Args:
            ano: Ano do ENEM
            area: Área (LC, CH, CN, MT)
            respostas: String de 45 respostas
            cor: Cor da prova
            tipo_aplicacao: Tipo de aplicação
            lingua: Língua estrangeira (para LC)
            
        Returns:
            Dict com resultado ou None se não calculável
        """
        if not respostas or respostas == "." * 45 or len(respostas) != 45:
            return None
        
        try:
            # Obter código da prova
            co_prova = self._mapeador.obter_codigo(ano, area, tipo_aplicacao, cor)
            
            # Definir língua para LC
            tp_lingua = None
            if area.upper() == 'LC':
                tp_lingua = 0 if lingua == 'ingles' else 1
            
            # Calcular análise completa
            try:
                analise = self._calculador.analisar_todas_questoes(
                    ano, area, co_prova, respostas, tp_lingua
                )
            except Exception as calc_err:
                return {
                    'sigla': area.upper(),
                    'nome': NOMES_AREAS.get(area.upper(), area),
                    'erro': f"Erro no cálculo TRI: {calc_err}",
                }
            
            # Verificar precisão
            aviso = None
            try:
                from tri_enem.relatorios import verificar_precisao_prova
                precisao = verificar_precisao_prova(ano, area, co_prova)
                if precisao.get('aviso'):
                    aviso = precisao['aviso']
            except Exception:
                # Silenciar erros - continua sem aviso
                aviso = None
            
            return {
                'sigla': area.upper(),
                'nome': NOMES_AREAS.get(area.upper(), area),
                'ano': ano,
                'co_prova': co_prova,
                'nota': analise['nota'],
                'theta': analise['theta'],
                'acertos': analise['total_acertos'],
                'total_itens': analise['total_itens'],
                'questoes_acertadas': analise['acertos'],
                'questoes_erradas': analise['erros'],
                'lingua': lingua if area.upper() == 'LC' else None,
                'cor_prova': cor,
                'aviso_precisao': aviso,
            }
            
        except Exception as e:
            return {
                'sigla': area.upper(),
                'nome': NOMES_AREAS.get(area.upper(), area),
                'erro': str(e),
            }
    
    def calcular_todas_areas(
        self,
        ano: int,
        respostas: Dict[str, str],
        cores: Dict[str, str],
        tipo_aplicacao: str = '1a_aplicacao',
        lingua: str = 'ingles'
    ) -> Tuple[List[Dict], List[str]]:
        """
        Calcula notas para todas as áreas.
        
        Args:
            ano: Ano do ENEM
            respostas: Dict {area: string_respostas}
            cores: Dict {area: cor}
            tipo_aplicacao: Tipo de aplicação
            lingua: Língua estrangeira
            
        Returns:
            Tupla (lista_resultados, lista_erros)
        """
        resultados = []
        erros = []
        
        # Ordem: LC, CH, CN, MT
        for area in ['LC', 'CH', 'CN', 'MT']:
            resp = respostas.get(area, '')
            cor = cores.get(area)
            
            if not resp or resp == "." * 45:
                continue
            
            if not cor:
                erros.append(f"{area}: Cor da prova não disponível")
                continue
            
            resultado = self.calcular_area(
                ano=ano,
                area=area,
                respostas=resp,
                cor=cor,
                tipo_aplicacao=tipo_aplicacao,
                lingua=lingua
            )
            
            if resultado:
                if 'erro' in resultado:
                    erros.append(f"{area}: {resultado['erro']}")
                else:
                    resultados.append(resultado)
        
        return resultados, erros


# Instância singleton para reutilização (com cache do Streamlit)
@st.cache_resource(show_spinner=False)
def get_calculador() -> CalculadorEnem:
    """Retorna instância singleton do calculador (cached)."""
    return CalculadorEnem()
