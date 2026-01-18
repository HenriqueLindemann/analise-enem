# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Classes base para geração de relatórios.

Este módulo define a estrutura de dados e interface base para relatórios.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class QuestaoAnalise:
    """Dados de uma questão analisada."""
    posicao: int
    gabarito: str
    resposta_dada: str
    acertou: bool
    param_a: float  # Discriminação
    param_b: float  # Dificuldade
    param_c: float  # Acerto casual
    impacto: float  # Ganho se acertasse (erro) ou perda se errasse (acerto)
    co_item: Optional[int] = None


@dataclass
class AreaAnalise:
    """Análise completa de uma área."""
    sigla: str  # MT, CN, CH, LC
    nome: str
    ano: int
    co_prova: int
    nota: float
    theta: float
    acertos: int
    total_itens: int
    questoes: List[QuestaoAnalise] = field(default_factory=list)
    lingua: Optional[str] = None  # Para LC
    
    @property
    def erros(self) -> int:
        return self.total_itens - self.acertos
    
    @property
    def percentual_acertos(self) -> float:
        return (self.acertos / self.total_itens * 100) if self.total_itens > 0 else 0
    
    @property
    def questoes_acertadas(self) -> List[QuestaoAnalise]:
        return [q for q in self.questoes if q.acertou]
    
    @property
    def questoes_erradas(self) -> List[QuestaoAnalise]:
        return [q for q in self.questoes if not q.acertou]


@dataclass
class DadosRelatorio:
    """Dados completos para geração do relatório."""
    titulo: str = "Relatório de Simulado ENEM"
    subtitulo: str = ""
    data_geracao: datetime = field(default_factory=datetime.now)
    ano_prova: int = 2024
    areas: List[AreaAnalise] = field(default_factory=list)
    observacoes: str = ""
    
    @property
    def media_notas(self) -> float:
        if not self.areas:
            return 0
        return sum(a.nota for a in self.areas) / len(self.areas)
    
    @property
    def total_acertos(self) -> int:
        return sum(a.acertos for a in self.areas)
    
    @property
    def total_questoes(self) -> int:
        return sum(a.total_itens for a in self.areas)
    
    def get_area(self, sigla: str) -> Optional[AreaAnalise]:
        for area in self.areas:
            if area.sigla == sigla:
                return area
        return None


class RelatorioBase:
    """
    Classe base para geradores de relatório.
    
    Subclasses devem implementar o método gerar().
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: Configurações personalizadas do relatório
        """
        self.config = config or {}
    
    def gerar(self, dados: DadosRelatorio, caminho_saida: str) -> str:
        """
        Gera o relatório.
        
        Args:
            dados: Dados do relatório
            caminho_saida: Caminho do arquivo de saída
            
        Returns:
            Caminho do arquivo gerado
        """
        raise NotImplementedError("Subclasses devem implementar gerar()")
    
    def validar_dados(self, dados: DadosRelatorio) -> bool:
        """Valida se os dados estão completos para geração."""
        if not dados.areas:
            return False
        return True
