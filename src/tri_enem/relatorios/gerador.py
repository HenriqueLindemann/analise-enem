"""
Gerador Principal de Relatórios PDF.

Combina estilos, gráficos e tabelas para gerar o relatório completo.
"""

from pathlib import Path
from datetime import datetime
from typing import List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Line
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

from .base import DadosRelatorio, AreaAnalise
from .estilos import criar_estilos, Cores
from .graficos import grafico_barras_notas, grafico_impacto_erros, grade_questoes, legenda_grafico_impacto
from .tabelas import tabela_erros_completa, tabela_resumo_areas
from .utils import verificar_precisao_prova


class RelatorioPDF:
    """
    Gerador de relatórios em PDF.
    
    Layout compacto com visualizações úteis para estudantes:
    - Barras de progresso por área
    - Grade visual das 45 questões
    - Gráfico de impacto dos erros
    - Tabela completa de erros
    """
    
    def __init__(self):
        if not REPORTLAB_DISPONIVEL:
            raise ImportError(
                "reportlab não está instalado. "
                "Execute: pip install reportlab"
            )
        
        self.styles = criar_estilos()
    
    def gerar(self, dados: DadosRelatorio, caminho_saida: str) -> str:
        """Gera o relatório PDF."""
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        
        # Documento com margens reduzidas
        doc = SimpleDocTemplate(
            str(caminho),
            pagesize=A4,
            leftMargin=1.2*cm,
            rightMargin=1.2*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        elementos = []
        
        # Cabeçalho
        elementos.extend(self._cabecalho(dados))
        
        # Resumo visual (barras)
        elementos.extend(self._resumo_visual(dados))
        
        # Seções por área
        for area in dados.areas:
            elementos.extend(self._secao_area(area))
        
        # Rodapé com disclaimer
        elementos.extend(self._rodape(dados))
        
        doc.build(elementos)
        return str(caminho.absolute())
    
    def _cabecalho(self, dados: DadosRelatorio) -> List:
        """Cabeçalho compacto."""
        return [
            Paragraph(dados.titulo, self.styles['TituloPrincipal']),
            Paragraph(f"ENEM {dados.ano_prova}", self.styles['Subtitulo']),
        ]
    
    def _resumo_visual(self, dados: DadosRelatorio) -> List:
        """Resumo com barras de progresso."""
        elementos = []
        
        # Gráfico de barras
        grafico = grafico_barras_notas(dados.areas)
        elementos.append(grafico)
        
        # Média em destaque
        if dados.areas:
            media = sum(a.nota for a in dados.areas) / len(dados.areas)
            elementos.append(Paragraph(
                f"Média: {media:.1f}",
                self.styles['NotaDestaque']
            ))
        
        elementos.append(Spacer(1, 5))
        return elementos
    
    def _secao_area(self, area: AreaAnalise) -> List:
        """Seção de uma área com grade, gráfico e tabela de erros."""
        elementos = []
        
        # Título
        titulo = f"{area.sigla} - {area.nome}"
        if area.lingua:
            titulo += f" ({area.lingua})"
        titulo += f" — {area.nota:.1f} pts"
        elementos.append(Paragraph(titulo, self.styles['TituloArea']))
        
        # Grade das 45 questões
        grade = grade_questoes(area.questoes)
        elementos.append(grade)
        elementos.append(Paragraph(
            f"✓ {area.acertos} acertos | ✗ {area.total_itens - area.acertos} erros",
            self.styles['Legenda']
        ))
        
        # Separar erros
        erros = [q for q in area.questoes if not q.acertou]
        
        if erros:
            elementos.append(Spacer(1, 5))
            
            # Gráfico de impacto
            elementos.append(Paragraph("Impacto dos Erros na Nota:", self.styles['TextoNormal']))
            grafico = grafico_impacto_erros(erros)
            elementos.append(grafico)
            elementos.append(Paragraph(legenda_grafico_impacto(), self.styles['Legenda']))
            
            elementos.append(Spacer(1, 3))
            
            # Tabela de erros (todos)
            elementos.append(Paragraph("Detalhes dos Erros:", self.styles['TextoNormal']))
            tabela = tabela_erros_completa(erros)
            if tabela:
                elementos.append(tabela)
        
        elementos.append(Spacer(1, 8))
        return elementos
    
    def _rodape(self, dados: DadosRelatorio) -> List:
        """Rodapé com disclaimer e assinatura."""
        elementos = []
        
        # Linha separadora
        d = Drawing(450, 1)
        linha = Line(0, 0, 450, 0)
        linha.strokeColor = Cores.CINZA_CLARO
        d.add(linha)
        elementos.append(d)
        
        # Disclaimer
        elementos.append(Paragraph(
            "<b>AVISO:</b> Cálculo aproximado por engenharia reversa dos microdados INEP. "
            "Precisão varia por prova. Algumas provas (LC antigos, reaplicações) podem ter erro maior. "
            "Use como referência, não como valor oficial.",
            self.styles['Disclaimer']
        ))
        
        elementos.append(Paragraph(
            "<b>USO COMERCIAL PROIBIDO</b> sem autorização prévia do autor.",
            self.styles['Disclaimer']
        ))
        
        elementos.append(Spacer(1, 3))
        
        # Assinatura
        elementos.append(Paragraph(
            f"Gerado em {dados.data_geracao.strftime('%d/%m/%Y %H:%M')} | "
            f"<b>Calculador de Nota TRI</b> — Software Livre | "
            f"github.com/HenriqueLindemann/analise-enem",
            self.styles['Disclaimer']
        ))
        
        return elementos
