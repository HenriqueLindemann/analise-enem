# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Composição determinística do relatório A4."""

from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from typing import List, Sequence

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer,
        Table, TableStyle,
    )
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

from .base import AreaAnalise, DadosRelatorio
from .estilos import Cores, Medidas, criar_estilos
from .graficos import grafico_barras_notas, grafico_impacto_questoes, grade_questoes
from .tabelas import tabela_diagnostico_questoes, tabela_resumo_areas
from .utils import formatar_lingua, formatar_numero
from ..mapeador_provas import MapeadorProvas
from ..precisao import formatar_aviso_curto, formatar_resumo_validacao, verificar_precisao_prova


TZ_BRASILIA = timezone(timedelta(hours=-3))
URL_SITE = "https://notatri.com"
URL_GITHUB = "https://github.com/HenriqueLindemann/analise-enem"
URL_LINKEDIN = "https://www.linkedin.com/in/henriquelindemann/"


class RelatorioPDF:
    """Gera a visão geral e uma página analítica por área."""

    def __init__(self):
        if not REPORTLAB_DISPONIVEL:
            raise RuntimeError("reportlab não está instalado. Instale com: pip install reportlab")
        self.styles = criar_estilos()

    def gerar(self, dados: DadosRelatorio, caminho_saida: str) -> str:
        """Gera o PDF e rejeita entradas que produziriam um documento vazio."""

        if not dados.areas:
            raise ValueError("O relatório precisa conter ao menos uma área")

        caminho = Path(caminho_saida)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self._dados = dados

        doc = BaseDocTemplate(
            str(caminho), pagesize=A4,
            leftMargin=Medidas.MARGEM_HORIZONTAL,
            rightMargin=Medidas.MARGEM_HORIZONTAL,
            topMargin=Medidas.MARGEM_SUPERIOR,
            bottomMargin=Medidas.MARGEM_INFERIOR,
            title=f"Desempenho no Simulado ENEM {dados.ano_prova}",
            author="Henrique Lindemann - Calculadora Nota TRI ENEM",
            subject=f"Estimativa TRI do Simulado ENEM {dados.ano_prova}",
            creator="Calculadora Nota TRI ENEM - https://notatri.com",
        )
        frame = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
            id="conteudo-a4",
        )
        doc.addPageTemplates(PageTemplate(
            id="relatorio", frames=[frame], onPage=self._desenhar_pagina,
        ))
        areas = self._ordenar_areas_por_prova(dados.areas)
        self._pagina_unica = len(areas) == 1
        paginas: List[List] = []

        if len(areas) >= 2:
            paginas.append(self._pagina_resumo(dados, areas))
            for area in areas:
                paginas.append(self._pagina_area(
                    area, incluir_identidade=False, incluir_diagnostico=True,
                ))
        else:
            paginas.append(self._pagina_area(
                areas[0], incluir_identidade=True, dados=dados,
                incluir_explicacao_b=True, incluir_diagnostico=True,
            ))

        for indice, pagina in enumerate(paginas, start=1):
            self._validar_altura_pagina(pagina, f"página lógica {indice}")

        story = []
        for indice, pagina in enumerate(paginas):
            story.extend(pagina)
            if indice < len(paginas) - 1:
                story.append(PageBreak())

        doc.build(story)
        return str(caminho.absolute())

    def _desenhar_pagina(self, canvas, doc):
        """Metadados e identificação discreta, fora da área de conteúdo."""

        if doc.page == 1:
            canvas.setTitle(
                f"Desempenho no Simulado ENEM {self._dados.ano_prova}"
            )
            canvas.setAuthor("Henrique Lindemann - Calculadora Nota TRI ENEM")
            canvas.setSubject(
                f"Estimativa TRI do Simulado ENEM {self._dados.ano_prova}"
            )
            canvas.setCreator("Calculadora Nota TRI ENEM - https://notatri.com")
        canvas.saveState()
        canvas.setStrokeColor(Cores.CINZA_CLARO)
        canvas.setLineWidth(0.35)
        y_linha, y_texto = 0.92 * cm, 0.58 * cm
        canvas.line(Medidas.MARGEM_HORIZONTAL, y_linha,
                    A4[0] - Medidas.MARGEM_HORIZONTAL, y_linha)
        canvas.setFillColor(Cores.CINZA)
        x = Medidas.MARGEM_HORIZONTAL
        partes_rodape = (
            ("notatri.com", URL_SITE, "Helvetica-Bold"),
            (" · Desenvolvido por ", None, "Helvetica"),
            ("Henrique Lindemann", URL_LINKEDIN, "Helvetica-Bold"),
            (" · ", None, "Helvetica"),
            ("GitHub", URL_GITHUB, "Helvetica-BoldOblique"),
            (" · ", None, "Helvetica"),
            ("LinkedIn", URL_LINKEDIN, "Helvetica-BoldOblique"),
            (" · PolyForm Noncommercial 1.0.0", None, "Helvetica"),
        )
        for texto, url, fonte in partes_rodape:
            canvas.setFont(fonte, 5.8)
            largura = canvas.stringWidth(texto, fonte, 5.8)
            canvas.drawString(x, y_texto, texto)
            if url:
                canvas.linkURL(
                    url, (x, y_texto - 1, x + largura, y_texto + 6),
                    relative=0, thickness=0,
                )
            x += largura
        canvas.setFont("Helvetica", 5.8)
        canvas.drawRightString(A4[0] - Medidas.MARGEM_HORIZONTAL, y_texto,
                               f"Página {doc.page}")
        canvas.restoreState()

    def _formatar_data_local(self, data: datetime | None, com_as: bool = False) -> str:
        """Formata o horário fornecido sem trocar seu fuso local."""

        if data is None:
            try:
                data = datetime.now().astimezone()
            except (OSError, ValueError):
                data = datetime.now(TZ_BRASILIA)
        formato = "%d/%m/%Y às %H:%M" if com_as else "%d/%m/%Y %H:%M"
        return data.strftime(formato)

    def _identidade(self, dados: DadosRelatorio, compacta: bool = False) -> List:
        titulo_style = self.styles["TituloArea"] if compacta else self.styles["TituloPrincipal"]
        subtitulo_style = self.styles["SubtituloCompacto"] if compacta else self.styles["Subtitulo"]
        meta_style = self.styles["MetaCompacta"] if compacta else self.styles["MetaCapa"]
        partes = ["Estimativa TRI", f"ENEM {dados.ano_prova}"]
        if dados.tipo_aplicacao:
            partes.append(escape(str(dados.tipo_aplicacao)))
        if dados.cor_prova:
            partes.append(escape(str(dados.cor_prova).capitalize()))
        data = self._formatar_data_local(dados.data_geracao, com_as=True)
        return [
            Paragraph(escape(str(dados.titulo)), titulo_style),
            Paragraph(" · ".join(partes), subtitulo_style),
            Paragraph(
                f"Gerado em <b>{escape(str(dados.origem_geracao))}</b> em {data}",
                meta_style,
            ),
            Spacer(1, 0 if compacta else 10),
        ]

    def _pagina_resumo(self, dados: DadosRelatorio,
                       areas: Sequence[AreaAnalise]) -> List:
        elementos = self._identidade(dados)
        espacos_distribuidos = [elementos[-1]]
        total_validos = sum(a.total_itens_validos for a in areas)
        total_acertos = sum(a.acertos for a in areas)
        aproveitamento = 100 * total_acertos / total_validos if total_validos else 0.0
        media = sum(a.nota for a in areas) / len(areas)

        def metrica(valor: str, rotulo: str):
            return [Paragraph(valor, self.styles["ValorMetrica"]),
                    Paragraph(rotulo, self.styles["RotuloMetrica"])]

        faixa = Table([[
            metrica(formatar_numero(media), "Média simples das áreas"),
            metrica(f"{total_acertos}/{total_validos}", "Acertos em itens válidos"),
            metrica(f"{aproveitamento:.0f}%", "Aproveitamento geral"),
        ]], colWidths=[Medidas.LARGURA_UTIL / 3] * 3)
        faixa.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LINEBEFORE", (1, 0), (-1, 0), 0.45, Cores.CINZA_CLARO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        espaco_metricas = Spacer(1, 12)
        elementos += [faixa, espaco_metricas]
        espacos_distribuidos.append(espaco_metricas)
        grafico_notas = grafico_barras_notas(areas, largura=14.5 * cm)
        grafico_centralizado = Table([[grafico_notas]], colWidths=[Medidas.LARGURA_UTIL])
        grafico_centralizado.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        espaco_grafico = Spacer(1, 10)
        elementos += [Paragraph("Notas por área", self.styles["SubtituloSecao"]),
                      grafico_centralizado, espaco_grafico]
        espacos_distribuidos.append(espaco_grafico)
        elementos += [Paragraph("Visão geral", self.styles["SubtituloSecao"]),
                      tabela_resumo_areas(areas)]
        if dados.observacoes:
            elementos.append(Paragraph(
                f"<b>Observação:</b> {escape(str(dados.observacoes))}",
                self.styles["Legenda"],
            ))
        espaco_tabela = Spacer(1, 10)
        elementos += [espaco_tabela, self._bloco_como_ler()]
        espacos_distribuidos.append(espaco_tabela)
        citacao = self._citacao_sagan(compacta=False)
        espaco_citacao = Spacer(1, 18)
        elementos.append(espaco_citacao)
        espacos_distribuidos.append(espaco_citacao)
        altura_sem_fechamento = self._validar_altura_pagina(
            elementos + [citacao], "capa antes da distribuição vertical",
        )
        sobra = max(0, Medidas.ALTURA_UTIL - altura_sem_fechamento - 0.55 * cm)
        pesos = (0.15, 0.22, 0.20, 0.20, 0.23)
        for espaco, peso in zip(espacos_distribuidos, pesos):
            espaco.height += sobra * peso
        elementos.append(citacao)
        return elementos

    def _bloco_como_ler(self) -> Table:
        definicoes = [
            ("Nota TRI", "Estima a proficiência a partir dos acertos, da dificuldade dos itens e da coerência do padrão de respostas."),
            ("Dificuldade (b)", "Valor obtido diretamente dos microdados do INEP que posiciona cada questão na escala TRI, das mais acessíveis às mais exigentes."),
            ("Impacto", "Estima quanto cada resposta sustenta a nota e ajuda a priorizar a revisão."),
        ]
        celulas = []
        for titulo, texto in definicoes:
            celulas.append(Paragraph(
                f"<b>{titulo}</b><br/><font color='#607080'>{texto}</font>",
                self.styles["TextoNormal"],
            ))
        tabela = Table([
            [Paragraph("Como ler este relatório", self.styles["SubtituloSecao"]), "", ""],
            celulas,
        ], colWidths=[Medidas.LARGURA_UTIL / 3] * 3, hAlign="LEFT")
        tabela.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, Cores.CINZA_CLARO),
            ("LINEBEFORE", (1, 1), (-1, 1), 0.35, Cores.CINZA_CLARO),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, 0), 0),
            ("RIGHTPADDING", (0, 0), (-1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return tabela

    def _pagina_area(self, area: AreaAnalise, incluir_identidade: bool,
                     dados: DadosRelatorio | None = None,
                     incluir_explicacao_b: bool = False,
                     incluir_citacao: bool = False,
                     incluir_diagnostico: bool = True) -> List:
        elementos: List = []
        if incluir_identidade and dados is not None:
            elementos.extend(self._identidade(dados, compacta=True))

        titulo = f"{area.sigla} — {area.nome}"
        lingua = formatar_lingua(area.lingua) if area.sigla.upper() == "LC" else ""
        if lingua:
            titulo += f" ({lingua})"
        elementos.append(Paragraph(escape(titulo), self.styles["TituloArea"]))

        prova = f"Prova {area.co_prova}" if area.co_prova else "Prova não informada"
        if area.cor_prova:
            prova += f" · {escape(str(area.cor_prova).capitalize())}"
        info = (
            f"{prova}  ·  <b>{formatar_numero(area.nota)} pontos</b>  ·  "
            f"{area.acertos}/{area.total_itens_validos} acertos válidos  ·  "
            f"{area.percentual_acertos:.0f}%"
        )
        if area.total_anulados:
            info += f"  ·  <b>{escape(area.texto_anuladas_breve())}</b>"
        elementos.append(Paragraph(info, self.styles["TextoNormal"]))
        elementos.append(Spacer(1, 3 if incluir_identidade else 6))

        precisao = verificar_precisao_prova(area.ano, area.sigla, area.co_prova)
        aviso = formatar_aviso_curto(precisao, formato="reportlab")
        resumo = formatar_resumo_validacao(precisao, formato="reportlab")
        if aviso:
            elementos.append(Paragraph(aviso, self.styles["AvisoCalibracao"]))
        if resumo:
            elementos.append(Paragraph(resumo, self.styles["MetricasValidacao"]))
        pagina_densa = incluir_identidade and len(area.questoes_erradas) >= 40
        espaco_antes_grade = 1 if pagina_densa else (5 if incluir_identidade else 10)
        espaco_depois_grade = 1 if pagina_densa else 6
        elementos += [Spacer(1, espaco_antes_grade),
                      grade_questoes(area.questoes), Spacer(1, espaco_depois_grade)]
        elementos.append(Paragraph("Impacto por questão", self.styles["SubtituloSecao"]))
        elementos += [grafico_impacto_questoes(area.questoes), Spacer(1, 3)]
        if incluir_diagnostico:
            apos_erros = None
            if incluir_explicacao_b:
                apos_erros = [Spacer(1, 2), Paragraph(
                    "<b>Dificuldade (b):</b> valor dos microdados do INEP que ordena as "
                    "questões das mais acessíveis às mais exigentes.",
                    self.styles["Legenda"],
                ), Spacer(1, 2)]
            elementos.append(tabela_diagnostico_questoes(
                area.questoes, apos_erros=apos_erros,
            ))
        if incluir_citacao:
            elementos += [Spacer(1, 5), self._citacao_sagan(compacta=True)]
        return elementos

    def _citacao_sagan(self, compacta: bool) -> Table:
        if compacta:
            texto = (
                "“Nós organizamos uma sociedade baseada em ciência e tecnologia, "
                "na qual ninguém entende nada de ciência e tecnologia.” — <b>Carl Sagan</b>"
            )
        else:
            texto = (
                "“Nós organizamos uma sociedade baseada em ciência e tecnologia, na qual "
                "ninguém entende nada de ciência e tecnologia. E essa mistura inflamável de "
                "ignorância e poder, mais cedo ou mais tarde, vai explodir na nossa cara. Quem está "
                "no comando da ciência e tecnologia em uma democracia se as pessoas não sabem nada "
                "sobre isso?”<br/><b>— Carl Sagan</b>"
            )
        tabela = Table([[Paragraph(f"<i>{texto}</i>", self.styles["Disclaimer"])]],
                       colWidths=[Medidas.LARGURA_UTIL])
        tabela.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 10 if not compacta else 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8 if not compacta else 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        return tabela

    def _ordenar_areas_por_prova(self, areas: Sequence[AreaAnalise]) -> List[AreaAnalise]:
        ano = areas[0].ano if areas else self._dados.ano_prova
        try:
            ordem = MapeadorProvas().listar_ordem_provas(ano)
        except (KeyError, ValueError):
            ordem = ["LC", "CH", "CN", "MT"]
        indices = {sigla.upper(): indice for indice, sigla in enumerate(ordem)}
        return sorted(areas, key=lambda area: indices.get(area.sigla.upper(), 99))

    def _validar_altura_pagina(self, elementos: Sequence, identificacao: str) -> float:
        """Mede a composição real antes do build para impedir overflow silencioso."""

        total = 0.0
        for elemento in elementos:
            _, altura = elemento.wrap(Medidas.LARGURA_UTIL, Medidas.ALTURA_UTIL)
            total += altura
            if hasattr(elemento, "getSpaceBefore"):
                total += elemento.getSpaceBefore()
            if hasattr(elemento, "getSpaceAfter"):
                total += elemento.getSpaceAfter()
        if total > Medidas.ALTURA_UTIL + 0.5:
            raise RuntimeError(
                f"{identificacao} excede a altura útil do A4: "
                f"{total / cm:.1f} cm para {Medidas.ALTURA_UTIL / cm:.1f} cm"
            )
        return total
