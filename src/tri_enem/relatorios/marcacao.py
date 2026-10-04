# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Henrique Lindemann
"""Marcação do PDF para tecnologias assistivas (Tagged PDF, ISO 14289).

O ReportLab desenha as páginas; este módulo delimita cada trecho desenhado
como conteúdo de um elemento lógico ou como artefato e, ao final, grava a
árvore de estrutura no arquivo.
"""

from __future__ import annotations

from contextlib import contextmanager
from io import BytesIO
from typing import Iterator, List, NamedTuple, Sequence
import warnings

import pikepdf
from pikepdf import Array, Dictionary, Name, String
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, Table

IDIOMA = "pt-BR"
ARTEFATO_PAGINACAO = "<</Type /Pagination /Subtype /Footer>>"


class _Conteudo(NamedTuple):
    pagina: int
    mcid: int


class _Anotacao(NamedTuple):
    pagina: int
    indice: int
    url: str
    descricao: str


class Elemento:
    """Nó da árvore de estrutura (StructElem)."""

    def __init__(self, tipo: str, filhos: Sequence = (), alt: str | None = None,
                 escopo: str | None = None):
        self.tipo = tipo
        self.filhos: List = [filho for filho in filhos if filho is not None]
        self.alt = alt
        self.escopo = escopo
        self.bbox: tuple | None = None

    def novo(self, tipo: str, **kwargs) -> "Elemento":
        filho = Elemento(tipo, **kwargs)
        self.filhos.append(filho)
        return filho


def estrutura_de(flowables: Sequence) -> List[Elemento]:
    """Elementos dos flowables, na ordem de leitura."""

    return [f.estrutura for f in flowables if getattr(f, "estrutura", None)]


class Marcacao:
    """Registra conteúdo marcado (MCID) e links durante o build."""

    def __init__(self):
        self._mcids: dict[int, int] = {}
        self._links: dict[int, int] = {}
        self._pilha: List[bool] = []
        self._chaves = 0

    def criar_canvas(self, *args, **kwargs) -> Canvas:
        """Uso: ``doc.build(story, canvasmaker=marcacao.criar_canvas)``."""

        canvas = Canvas(*args, **kwargs)
        canvas.marcacao = self
        return canvas

    def iniciar(self, canv: Canvas, elemento: Elemento | None,
                propriedades: str = "") -> None:
        # Sequências não são aninhadas: o trecho interno pertence ao externo.
        if any(self._pilha):
            self._pilha.append(False)
            return
        if elemento is None:
            canv.addLiteral(
                f"/Artifact {propriedades} BDC" if propriedades else "/Artifact BMC"
            )
        else:
            pagina = canv.getPageNumber()
            mcid = self._mcids.get(pagina, 0)
            self._mcids[pagina] = mcid + 1
            canv.addLiteral(f"/{elemento.tipo} <</MCID {mcid}>> BDC")
            elemento.filhos.append(_Conteudo(pagina, mcid))
        self._pilha.append(True)

    def transparente(self) -> None:
        """Abre um trecho sem marcação própria; o conteúdo interno se marca."""

        self._pilha.append(False)

    def encerrar(self, canv: Canvas) -> None:
        if self._pilha.pop():
            canv.addLiteral("EMC")

    def registrar_link(self, canv: Canvas, url: str, elemento: Elemento,
                       descricao: str) -> None:
        pagina = canv.getPageNumber()
        indice = self._links.get(pagina, 0)
        self._links[pagina] = indice + 1
        elemento.filhos.append(_Anotacao(pagina, indice, url, descricao))

    def nova_chave(self) -> str:
        self._chaves += 1
        return f"secao-{self._chaves}"

    def gravar(self, pdf_reportlab: bytes, documento: Elemento, destino: str) -> None:
        """Grava o PDF com árvore de estrutura, idioma e metadados XMP."""

        with pikepdf.open(BytesIO(pdf_reportlab)) as pdf:
            _Serializador(pdf, self._mcids).aplicar(documento)
            pdf.Root.MarkInfo = Dictionary(Marked=True)
            pdf.Root.Lang = String(IDIOMA)
            pdf.Root.ViewerPreferences = Dictionary(DisplayDocTitle=True)
            _mapear_unicode_symbol(pdf)
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                with warnings.catch_warnings():
                    # /Trapped do ReportLab não tem equivalente XMP.
                    warnings.filterwarnings("ignore", "The metadata field /Trapped")
                    meta.load_from_docinfo(pdf.docinfo)
            pdf.save(
                destino, min_version="1.7",
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )


def _mapear_unicode_symbol(pdf: pikepdf.Pdf) -> None:
    """ToUnicode da fonte Symbol, usada pelo ReportLab em glifos como ← e →."""

    cmap = None
    for pagina in pdf.pages:
        fontes = pagina.obj.get("/Resources", Dictionary()).get("/Font", Dictionary())
        for _, fonte in fontes.items():
            if fonte.get("/BaseFont") == Name.Symbol and "/ToUnicode" not in fonte:
                cmap = cmap or pdf.make_stream(_cmap_symbol())
                fonte.ToUnicode = cmap


def _cmap_symbol() -> bytes:
    pares = []
    for codigo in range(256):
        try:
            texto = bytes([codigo]).decode("symbol")  # codec do ReportLab
        except UnicodeDecodeError:
            continue
        if texto and texto != "\ufffd":
            pares.append(f"<{codigo:02X}> <{texto.encode('utf-16-be').hex().upper()}>")
    blocos = "".join(
        f"{len(bloco)} beginbfchar\n" + "\n".join(bloco) + "\nendbfchar\n"
        for bloco in (pares[i:i + 100] for i in range(0, len(pares), 100))
    )
    return (
        "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n"
        "1 begincodespacerange\n<00> <FF>\nendcodespacerange\n"
        f"{blocos}endcmap\nCMapName currentdict /CMapResource defineresource pop\n"
        "end\nend\n"
    ).encode("ascii")


class _Serializador:
    """Converte a árvore de ``Elemento`` em StructTreeRoot e ParentTree."""

    def __init__(self, pdf: pikepdf.Pdf, mcids: dict[int, int]):
        self.pdf = pdf
        self.mcids = mcids
        self.paginas = list(pdf.pages)
        self.por_pagina: List[dict] = [{} for _ in self.paginas]
        self.anotacoes: List[tuple] = []

    def aplicar(self, documento: Elemento) -> None:
        raiz = self.pdf.make_indirect(Dictionary(Type=Name.StructTreeRoot))
        raiz.K = self._converter(documento, raiz)
        nums = Array()
        for indice, (pagina, mapa) in enumerate(zip(self.paginas, self.por_pagina)):
            if set(mapa) != set(range(self.mcids.get(indice + 1, 0))):
                raise RuntimeError(
                    f"Conteúdo marcado fora da árvore de estrutura na página {indice + 1}"
                )
            pagina.obj.StructParents = indice
            pagina.obj.Tabs = Name.S
            nums.extend([indice, self.pdf.make_indirect(Array(
                [mapa[mcid] for mcid in range(len(mapa))]
            ))])
        for chave, elemento in self.anotacoes:
            nums.extend([chave, elemento])
        raiz.ParentTree = self.pdf.make_indirect(Dictionary(Nums=nums))
        raiz.ParentTreeNextKey = len(self.paginas) + len(self.anotacoes)
        self.pdf.Root.StructTreeRoot = raiz

    def _converter(self, elemento: Elemento, pai) -> pikepdf.Object | None:
        no = self.pdf.make_indirect(Dictionary(
            Type=Name.StructElem, S=Name("/" + elemento.tipo), P=pai,
        ))
        filhos = Array()
        for filho in elemento.filhos:
            if isinstance(filho, Elemento):
                convertido = self._converter(filho, no)
                if convertido is not None:
                    filhos.append(convertido)
            elif isinstance(filho, _Conteudo):
                pagina = self.paginas[filho.pagina - 1].obj
                filhos.append(Dictionary(Type=Name.MCR, Pg=pagina, MCID=filho.mcid))
                self.por_pagina[filho.pagina - 1][filho.mcid] = no
            else:
                filhos.append(self._anotacao(filho, no))
        if not filhos and elemento.tipo not in ("TD", "TH"):
            return None
        if filhos:
            no.K = filhos
        if elemento.alt:
            no.Alt = String(elemento.alt)
        if elemento.escopo:
            no.A = Dictionary(O=Name.Table, Scope=Name("/" + elemento.escopo))
        elif elemento.bbox:
            no.A = Dictionary(O=Name.Layout, BBox=Array(elemento.bbox))
        return no

    def _anotacao(self, filho: _Anotacao, no) -> Dictionary:
        pagina = self.paginas[filho.pagina - 1].obj
        anotacao = pagina.Annots[filho.indice]
        if str(anotacao.A.URI) != filho.url:
            raise RuntimeError(f"Link fora de ordem na página {filho.pagina}")
        chave = len(self.paginas) + len(self.anotacoes)
        anotacao.StructParent = chave
        anotacao.Contents = String(filho.descricao)
        self.anotacoes.append((chave, no))
        return Dictionary(Type=Name.OBJR, Obj=anotacao, Pg=pagina)


@contextmanager
def _marcar(canv: Canvas, elemento: Elemento | None,
            propriedades: str = "") -> Iterator[None]:
    marcacao = getattr(canv, "marcacao", None)
    if marcacao is None:
        yield
        return
    marcacao.iniciar(canv, elemento, propriedades)
    try:
        yield
    finally:
        marcacao.encerrar(canv)


def conteudo(canv: Canvas, elemento: Elemento):
    """Marca o que for desenhado no bloco como conteúdo de ``elemento``."""

    return _marcar(canv, elemento)


def artefato(canv: Canvas, propriedades: str = ""):
    """Marca o que for desenhado no bloco como artefato (ignorado na leitura)."""

    return _marcar(canv, None, propriedades)


def link(canv: Canvas, url: str, rect: tuple, elemento: Elemento,
         descricao: str) -> None:
    """Anotação de link associada ao elemento ``Link`` que contém seu texto."""

    canv.linkURL(url, rect, relative=0, thickness=0)
    marcacao = getattr(canv, "marcacao", None)
    if marcacao is not None:
        marcacao.registrar_link(canv, url, elemento, descricao)


class Marcado(Flowable):
    """Envolve um flowable e marca tudo o que ele desenha como um elemento."""

    def __init__(self, conteudo: Flowable, estrutura: Elemento):
        super().__init__()
        self.conteudo = conteudo
        self.estrutura = estrutura
        self.hAlign = getattr(conteudo, "hAlign", "LEFT")

    def wrap(self, largura, altura):
        self.width, self.height = self.conteudo.wrap(largura, altura)
        return self.width, self.height

    def getSpaceBefore(self):
        return self.conteudo.getSpaceBefore()

    def getSpaceAfter(self):
        return self.conteudo.getSpaceAfter()

    def split(self, largura, altura):
        return [Marcado(parte, self.estrutura)
                for parte in self.conteudo.split(largura, altura)]

    def drawOn(self, canv, x, y, _sW=0):
        marcacao = getattr(canv, "marcacao", None)
        if marcacao is not None:
            tipo = self.estrutura.tipo
            if tipo in ("H1", "H2") and hasattr(self.conteudo, "getPlainText"):
                chave = marcacao.nova_chave()
                canv.bookmarkHorizontal(chave, x, y + self.height)
                canv.addOutlineEntry(
                    self.conteudo.getPlainText(), chave, level=int(tipo[1]) - 1,
                )
            if tipo == "Figure":
                x0 = self.conteudo._hAlignAdjust(x, _sW)
                self.estrutura.bbox = (
                    *canv.absolutePosition(x0, y),
                    *canv.absolutePosition(x0 + self.width, y + self.height),
                )
        with conteudo(canv, self.estrutura):
            self.conteudo.drawOn(canv, x, y, _sW)


def marcado(flowable: Flowable, tipo: str, **kwargs) -> Marcado:
    return Marcado(flowable, Elemento(tipo, **kwargs))


class MarcacaoTabela:
    """``renderCB`` do Table: fundos e linhas como artefato.

    ``celulas[linha][coluna]`` indica o elemento de cada célula. Sem ele, as
    células com flowables os desenham com a própria marcação e as de texto
    simples viram artefato.
    """

    def __init__(self, celulas: Sequence[Sequence[Elemento | None]] | None = None):
        self.celulas = celulas

    def __call__(self, tabela: Table, evento: str, *args) -> None:
        marcacao = getattr(tabela.canv, "marcacao", None)
        if marcacao is None:
            return
        if evento in ("startBG", "startLines"):
            marcacao.iniciar(tabela.canv, None)
        elif evento in ("endBG", "endLines"):
            marcacao.encerrar(tabela.canv)
        elif evento == "startCell":
            linha, coluna, valor = args[:3]
            elemento = self.celulas[linha][coluna] if self.celulas else None
            if elemento is not None:
                marcacao.iniciar(tabela.canv, elemento)
            elif isinstance(valor, (Flowable, list, tuple)):
                marcacao.transparente()
            else:
                marcacao.iniciar(tabela.canv, None)
        elif evento == "endCell":
            marcacao.encerrar(tabela.canv)


def tabela_dados(dados: Sequence[Sequence], cabecalho_colunas: int = 1,
                 **kwargs) -> Table:
    """Tabela de dados: primeira linha com TH de coluna e TH de linha à esquerda."""

    estrutura = Elemento("Table")
    celulas = []
    for indice_linha, linha in enumerate(dados):
        tr = estrutura.novo("TR")
        celulas.append([
            tr.novo("TH", escopo="Column") if indice_linha == 0
            else tr.novo("TH", escopo="Row") if indice_coluna < cabecalho_colunas
            else tr.novo("TD")
            for indice_coluna in range(len(linha))
        ])
    tabela = Table(dados, renderCB=MarcacaoTabela(celulas), **kwargs)
    tabela.estrutura = estrutura
    return tabela


def tabela_layout(dados: Sequence[Sequence], estrutura: Elemento | None,
                  celulas: Sequence[Sequence[Elemento | None]] | None = None,
                  **kwargs) -> Table:
    """Tabela só de diagramação: não aparece como tabela na leitura."""

    tabela = Table(dados, renderCB=MarcacaoTabela(celulas), **kwargs)
    tabela.estrutura = estrutura
    return tabela
