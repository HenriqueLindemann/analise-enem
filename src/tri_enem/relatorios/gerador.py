# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""
Gerador Principal de Relatórios PDF.

Combina estilos, gráficos e tabelas para gerar o relatório completo.
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Line
    from reportlab.lib.colors import Color
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

from .base import DadosRelatorio, AreaAnalise
from .estilos import criar_estilos, Cores
from .graficos import grafico_barras_notas, grafico_impacto_questoes, grade_questoes, legenda_grafico_impacto
from .tabelas import tabela_erros_completa, tabela_resumo_areas
from .utils import verificar_precisao_prova
from ..mapeador_provas import MapeadorProvas

TZ_BRASILIA = timezone(timedelta(hours=-3))


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
        self._mapeador = None  # Lazy loading
    
    def gerar(self, dados: DadosRelatorio, caminho_saida: str) -> str:
        """Gera o relatório PDF."""
        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        
        # Salvar dados para uso no rodapé de página
        self._dados = dados
        
        # Documento com margens reduzidas
        doc = SimpleDocTemplate(
            str(caminho),
            pagesize=A4,
            leftMargin=1.2*cm,
            rightMargin=1.2*cm,
            topMargin=1*cm,
            bottomMargin=1.5*cm
        )
        
        elementos = []
        
        # Cabeçalho
        elementos.extend(self._cabecalho(dados))
        
        areas_ordenadas = self._ordenar_areas_por_prova(dados.areas, dados.ano_prova)

        # Resumo visual (barras)
        elementos.extend(self._resumo_visual(dados, areas_ordenadas))
        
        # Seções por área
        for area in areas_ordenadas:
            elementos.extend(self._secao_area(area))
        
        # Rodapé com disclaimer
        elementos.extend(self._rodape(dados))
        
        # Build com função de página para números e metadados
        doc.build(elementos, onFirstPage=self._primeira_pagina, onLaterPages=self._rodape_pagina)
        return str(caminho.absolute())
    
    def _primeira_pagina(self, canvas, doc):
        """Configura metadados e rodapé da primeira página."""
        # Definir metadados do PDF
        canvas.setTitle(f"Resultado ENEM {self._dados.ano_prova}")
        canvas.setAuthor("Henrique Lindemann - Calculadora Nota TRI ENEM")
        canvas.setSubject(f"Relatório de Simulado ENEM {self._dados.ano_prova}")
        canvas.setCreator("Calculadora Nota TRI ENEM - https://notatri.com")
        
        # Adicionar número de página
        self._rodape_pagina(canvas, doc)
    
    def _rodape_pagina(self, canvas, doc):
        """Adiciona número de página no rodapé de cada página."""
        canvas.saveState()
        pagina = f"Página {doc.page}"
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(Cores.CINZA)
        canvas.drawRightString(doc.pagesize[0] - 1.2*cm, 0.8*cm, pagina)
        canvas.restoreState()

    def _formatar_data_brasilia(self, data: datetime, com_as: bool = False) -> str:
        """Converte para horário de Brasília (UTC-3) e formata para exibição."""
        data_brasilia = data.astimezone(TZ_BRASILIA)
        formato = '%d/%m/%Y às %H:%M' if com_as else '%d/%m/%Y %H:%M'
        return data_brasilia.strftime(formato)

    
    def _cabecalho(self, dados: DadosRelatorio) -> List:
        """Cabeçalho elegante e minimalista."""
        elementos = []
        
        # Título principal
        elementos.append(Paragraph(dados.titulo, self.styles['TituloPrincipal']))
        
        # Subtítulo com tipo de aplicação e cor
        subtitulo_partes = [f"ENEM {dados.ano_prova}"]
        if dados.tipo_aplicacao:
            subtitulo_partes.append(dados.tipo_aplicacao)
        if dados.cor_prova:
            subtitulo_partes.append(dados.cor_prova.capitalize())
        
        elementos.append(Paragraph(" · ".join(subtitulo_partes), self.styles['Subtitulo']))
        
        # Texto de geração com branding (horário de Brasília UTC-3)
        data_geracao = self._formatar_data_brasilia(dados.data_geracao, com_as=True)
        elementos.append(Paragraph(
            f"<i>Gerado em <b>notatri.com</b> em {data_geracao}</i>",
            self.styles['Disclaimer']
        ))
        
        elementos.append(Spacer(1, 12))
        return elementos
    
    def _resumo_visual(self, dados: DadosRelatorio, areas_ordenadas: List[AreaAnalise]) -> List:
        """Resumo visual limpo com média em destaque."""
        elementos = []
        
        # Gráfico de barras primeiro - ordenar por prova (ano)
        grafico = grafico_barras_notas(areas_ordenadas)
        elementos.append(grafico)
        
        elementos.append(Spacer(1, 10))
        
        # Média grande e impactante depois do gráfico
        if dados.areas:
            media = sum(a.nota for a in dados.areas) / len(dados.areas)
            elementos.append(Paragraph("MÉDIA GERAL", self.styles['NotaLabel']))
            elementos.append(Paragraph(f"{media:.0f}", self.styles['NotaDestaque']))
        
        elementos.append(Spacer(1, 18))
        return elementos

    def _ordenar_areas_por_prova(self, areas: List[AreaAnalise], ano: int) -> List[AreaAnalise]:
        """Ordena áreas conforme a ordem das provas do ano."""
        try:
            if self._mapeador is None:
                self._mapeador = MapeadorProvas()
            ordem = self._mapeador.listar_ordem_provas(ano)
        except Exception:
            ordem = ['LC', 'CH', 'CN', 'MT']

        index_map = {sigla: idx for idx, sigla in enumerate(ordem)}
        return sorted(areas, key=lambda a: index_map.get(a.sigla, 99))
    
    def _secao_area(self, area: AreaAnalise) -> List:
        """Seção de uma área - design limpo e organizado."""
        elementos = []
        
        # Título da área com nota
        titulo = f"{area.sigla} — {area.nome}"
        if area.lingua:
            titulo += f" ({area.lingua})"
        elementos.append(Paragraph(titulo, self.styles['TituloArea']))
        
        # Código da prova, cor e nota
        info_prova = f"Prova {area.co_prova}"
        if area.cor_prova:
            info_prova += f" ({area.cor_prova.capitalize()})"
        info_prova += f"  ·  <b>{area.nota:.0f}</b> pontos  ·  {area.acertos}/{area.total_itens} acertos"
        elementos.append(Paragraph(info_prova, self.styles['TextoNormal']))
        
        # Verificar precisão e adicionar aviso se necessário
        precisao = verificar_precisao_prova(area.ano, area.sigla, area.co_prova)
        if precisao.get('aviso'):
            elementos.append(Paragraph(
                f"⚠ {precisao['aviso']}",
                self.styles['AvisoPrecisao']
            ))
        
        elementos.append(Spacer(1, 4))
        
        # Grade das 45 questões
        grade = grade_questoes(area.questoes)
        elementos.append(grade)
        
        # Separar erros
        erros = [q for q in area.questoes if not q.acertou]
        
        elementos.append(Spacer(1, 6))
        
        # Gráfico de impacto - subtítulo de seção
        elementos.append(Paragraph("Impacto por Questão", self.styles['SubtituloSecao']))
        grafico = grafico_impacto_questoes(area.questoes, titulo="")
        elementos.append(grafico)
        
        if erros:
            elementos.append(Spacer(1, 6))
            
            # Tabela de erros
            elementos.append(Paragraph("Análise dos Erros", self.styles['SubtituloSecao']))
            tabela = tabela_erros_completa(erros)
            if tabela:
                elementos.append(tabela)
        
        elementos.append(Spacer(1, 12))
        return elementos
    
    def _rodape(self, dados: DadosRelatorio) -> List:
        """Rodapé minimalista com disclaimer e licença."""
        elementos = []
        
        elementos.append(Spacer(1, 10))
        
        # Disclaimer
        elementos.append(Paragraph(
            "Cálculo aproximado por engenharia reversa dos microdados INEP. "
            "Precisão varia por prova. Use como referência.",
            self.styles['Disclaimer']
        ))
        
        # Licença
        elementos.append(Paragraph(
            "<b>Licença:</b> PolyForm Noncommercial 1.0.0 — Uso comercial não permitido sem autorização.",
            self.styles['Disclaimer']
        ))
        
        # Assinatura
        elementos.append(Paragraph(
            f"Gerado em {self._formatar_data_brasilia(dados.data_geracao)}  ·  "
            f"© Henrique Lindemann  ·  "
            f"github.com/HenriqueLindemann/analise-enem",
            self.styles['Disclaimer']
        ))
        
        elementos.append(Spacer(1, 10))
        
        # Promoção do site
        elementos.append(Paragraph(
            "<b>https://notatri.com</b>",
            self.styles['Disclaimer']
        ))
        elementos.append(Paragraph(
            "Acesse e gere seu relatório gratuitamente também!",
            self.styles['Disclaimer']
        ))
        
        elementos.append(Spacer(1, 15))
        
        # Citação Carl Sagan
        elementos.append(Paragraph(
            "<i>\"Nós organizamos uma sociedade baseada em ciência e tecnologia, na qual ninguém entende nada de ciência e tecnologia. "
            "E essa mistura inflamável de ignorância e poder, mais cedo ou mais tarde, vai explodir na nossa cara. "
            "Quem está no comando da ciência e tecnologia em uma democracia se as pessoas não sabem nada sobre isso?\"</i>",
            self.styles['Disclaimer']
        ))
        elementos.append(Paragraph(
            "— <b>Carl Sagan</b>",
            self.styles['Disclaimer']
        ))
        
        return elementos
