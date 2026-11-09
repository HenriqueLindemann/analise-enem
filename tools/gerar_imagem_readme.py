#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Gera os SVGs do README (exemplo de Matemática e artigo), em versão clara e escura.

Execute da raiz: python tools/gerar_imagem_readme.py
"""
from math import ceil
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from reportlab.pdfbase.pdfmetrics import stringWidth

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import meu_simulado as exemplo
from tri_enem.formatacao import formatar_numero

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

# Ambas as imagens usam a largura do README do GitHub (~880 px), sem redução de escala.
LARGURA = 880
MARGEM = 28
SANS = 'Arial, Helvetica, sans-serif'
MONO = 'ui-monospace, Menlo, Consolas, "Liberation Mono", monospace'
SECUNDARIO, CORPO, TITULO = 14, 16, 20
ALTURA_MAIUSCULA = 0.718  # Helvetica/Arial, em fração do corpo

PALETAS = {
    '': {'texto': '#253746', 'secundario': '#596873', 'resposta': '#405562',
         'acerto': '#20805f', 'erro': '#bb503e', 'grade': '#dce3e7', 'seta': '#8a979f'},
    '-dark': {'texto': '#e6edf3', 'secundario': '#a7b3bd', 'resposta': '#c1cdd7',
              'acerto': '#63cba5', 'erro': '#fa9a87', 'grade': '#303b46', 'seta': '#82939f'},
}
TRACOS = {'grade', 'seta', 'ligacao'}


def largura_texto(conteudo, tamanho, negrito=False):
    return stringWidth(conteudo, 'Helvetica-Bold' if negrito else 'Helvetica', tamanho)


def base_por_topo(topo, tamanho):
    """Linha de base para que o topo das maiúsculas fique em `topo`."""
    return topo + ALTURA_MAIUSCULA * tamanho


def elemento(pai, tag, texto=None, **atributos):
    item = ET.SubElement(pai, f'{{{NS}}}{tag}', {
        chave.rstrip('_').replace('_', '-'): str(valor) for chave, valor in atributos.items()
    })
    item.text = texto
    return item


class Desenho:
    def __init__(self, altura, titulo, descricao):
        self.raiz = ET.Element(f'{{{NS}}}svg', {
            'viewBox': f'0 0 {LARGURA} {altura}', 'width': str(LARGURA),
            'height': str(altura), 'role': 'img', 'aria-labelledby': 'titulo descricao',
        })
        elemento(self.raiz, 'title', titulo, id='titulo')
        elemento(self.raiz, 'desc', descricao, id='descricao')
        self.estilo = elemento(self.raiz, 'style')
        self.grupo = elemento(self.raiz, 'g', font_family=SANS)

    def texto(self, x, y, conteudo, tamanho, classe='texto', negrito=False, **attrs):
        if negrito:
            attrs['font_weight'] = 'bold'
        return elemento(self.grupo, 'text', conteudo, x=x, y=y, font_size=tamanho,
                        class_=classe, **attrs)

    def forma(self, tag, **attrs):
        return elemento(self.grupo, tag, **attrs)

    def salvar(self, nome):
        # O <picture> do README escolhe a paleta; o fundo fica transparente.
        for sufixo, cores in PALETAS.items():
            self.estilo.text = '\n'.join(
                f'.{classe} {{ {"stroke" if classe in TRACOS else "fill"}: {cor}; }}'
                for classe, cor in {**cores, 'ligacao': cores['acerto']}.items()
            )
            destino = RAIZ / f'docs/imagens/{nome}{sufixo}.svg'
            destino.parent.mkdir(parents=True, exist_ok=True)
            ET.indent(self.raiz)
            ET.ElementTree(self.raiz).write(destino, encoding='utf-8', xml_declaration=True)
            print(destino)


def imagem_exemplo():
    resultado = exemplo.calcular_e_analisar(
        exemplo.CalculadorTRI(), 'MT', exemplo.ANO, exemplo.RESPOSTAS_MT,
        cor_prova=exemplo.COR_MT, tipo_aplicacao=exemplo.TIPO_APLICACAO,
    )
    if resultado is None:
        raise RuntimeError('Não foi possível calcular o exemplo de Matemática.')
    erros = resultado['questoes_erradas']
    questoes = sorted(
        [(q, q['perda_se_errasse'], 'acerto') for q in resultado['questoes_acertadas']]
        + [(q, q['ganho_se_acertasse'], 'erro') for q in erros],
        key=lambda item: (-item[1], item[0]['posicao_caderno']),
    )
    nota = formatar_numero(resultado['nota'])
    acertos = f"{resultado['acertos']}/{resultado['total_itens']} acertos válidos"

    # Topo: respostas → nota, alinhadas pelo topo e pela última linha.
    base_titulo = base_por_topo(MARGEM, TITULO)
    tamanho_resposta, passo_letra, passo_linha = 20, 26, 32
    topo_respostas = base_titulo + 20
    bases_respostas = [base_por_topo(topo_respostas, tamanho_resposta) + i * passo_linha
                       for i in range(3)]
    tamanho_nota = 56
    x_nota = LARGURA - MARGEM - max(largura_texto(nota, tamanho_nota, True),
                                    largura_texto(acertos, SECUNDARIO))
    fim_respostas = MARGEM + 14 * passo_letra + 12

    # Gráfico de impacto.
    base_secao = bases_respostas[-1] + 62
    x0, x1 = 60, LARGURA - MARGEM
    topo_grafico = base_secao + 52
    altura_grafico = 200
    y0 = topo_grafico + altura_grafico
    base_rodape = y0 + 26
    altura = round(base_rodape + MARGEM)

    desenho = Desenho(
        altura, 'Respostas → nota → impacto por questão',
        f"Matemática, ENEM {exemplo.ANO}. Nota estimada: {nota}. " + ' '.join(
            f"Q{q['posicao_caderno']}: ganho de "
            f"{formatar_numero(q['ganho_se_acertasse'])} pontos se acertasse."
            for q in erros
        ),
    )
    t = desenho.texto

    t(MARGEM, f'{base_titulo:.1f}', 'Respostas', TITULO, negrito=True)
    t(f'{x_nota:.1f}', f'{base_titulo:.1f}', 'Nota', TITULO, negrito=True)
    for linha, base in enumerate(bases_respostas):
        letras = exemplo.RESPOSTAS_MT[linha * 15:(linha + 1) * 15]
        for coluna, letra in enumerate(letras):
            t(MARGEM + coluna * passo_letra, f'{base:.1f}', letra, tamanho_resposta,
              classe='resposta', font_family=MONO)
    y_seta = round(bases_respostas[1] - ALTURA_MAIUSCULA * tamanho_resposta / 2)
    xa, xb = round(fim_respostas + 40), round(x_nota - 40)
    desenho.forma('path', d=f'M {xa} {y_seta} H {xb} M {xb - 8} {y_seta - 8} '
                            f'L {xb} {y_seta} L {xb - 8} {y_seta + 8}',
                  fill='none', stroke_width=1.8, stroke_linecap='round',
                  stroke_linejoin='round', class_='seta')
    t(f'{x_nota:.1f}', f'{base_por_topo(topo_respostas, tamanho_nota):.1f}',
      nota, tamanho_nota, negrito=True)
    t(f'{x_nota:.1f}', f'{bases_respostas[-1]:.1f}', acertos, SECUNDARIO,
      classe='secundario')

    t(MARGEM, f'{base_secao:.1f}', 'Impacto por questão', TITULO, negrito=True)
    lado, folga = 11, 8
    x = LARGURA - MARGEM
    for classe, legenda in reversed((
        ('acerto', 'Acerto · perda se errasse'),
        ('erro', 'Erro (*) · ganho se acertasse'),
    )):
        x -= largura_texto(legenda, SECUNDARIO)
        t(f'{x:.1f}', f'{base_secao:.1f}', legenda, SECUNDARIO, classe='secundario')
        x -= folga + lado
        desenho.forma('rect', x=f'{x:.1f}', y=f'{base_secao - lado:.1f}',
                      width=lado, height=lado, rx=2, class_=classe)
        x -= 24

    escala = max(10, ceil(max((v for _, v, _ in questoes), default=0) / 10) * 10)
    t(x0 - 10, f'{topo_grafico - 20:.1f}', 'pts', SECUNDARIO, classe='secundario',
      text_anchor='end')
    for indice in range(5):
        y = y0 - altura_grafico * indice / 4
        desenho.forma('line', x1=x0, y1=y, x2=x1, y2=y, stroke_width=1, class_='grade')
        t(x0 - 10, f'{y + 5:.1f}', f'{escala * indice / 4:g}', SECUNDARIO,
          classe='secundario', text_anchor='end')
    passo = (x1 - x0) / max(1, len(questoes))
    vao = 5
    for indice, (questao, valor, classe) in enumerate(questoes):
        xb = x0 + indice * passo + vao / 2
        h = max(0.8, altura_grafico * max(0, valor) / escala)
        barra = desenho.forma('rect', x=f'{xb:.2f}', y=f'{y0 - h:.2f}',
                              width=f'{passo - vao:.2f}', height=f'{h:.2f}', rx=2,
                              class_=classe)
        elemento(barra, 'title',
                 f"Q{questao['posicao_caderno']}: {formatar_numero(valor)} pontos")
        cx = xb + (passo - vao) / 2 + ALTURA_MAIUSCULA * SECUNDARIO / 2
        cy = y0 - h - 8
        rotulo = str(questao['posicao_caderno']) + ('*' if classe == 'erro' else '')
        t(f'{cx:.2f}', f'{cy:.2f}', rotulo, SECUNDARIO, classe=classe,
          transform=f'rotate(-90 {cx:.2f} {cy:.2f})')
    t(f'{x0 + vao / 2:.1f}', base_rodape, 'Maior impacto', SECUNDARIO, classe='secundario')
    t(f'{x1 - vao / 2:.1f}', base_rodape, 'Menor impacto', SECUNDARIO, classe='secundario',
      text_anchor='end')
    desenho.salvar('exemplo-matematica')


def imagem_artigo():
    numero = '≈ 14,7 milhões'
    tamanho_numero = 32
    base_rotulos = base_por_topo(MARGEM, SECUNDARIO)
    topo_caixa, altura_caixa = base_rotulos + 14, 72
    meio = topo_caixa + altura_caixa / 2
    y_divisoria = topo_caixa + altura_caixa + 28
    topo_numero = y_divisoria + 28
    base_numero = base_por_topo(topo_numero, tamanho_numero)
    # Bloco de duas linhas centralizado na altura das maiúsculas do número.
    entrelinha = 22
    centro = topo_numero + ALTURA_MAIUSCULA * tamanho_numero / 2
    base_linha1 = centro - (entrelinha - ALTURA_MAIUSCULA * CORPO) / 2
    base_linha2 = base_linha1 + entrelinha
    altura = round(max(base_numero, base_linha2) + MARGEM)

    desenho = Desenho(
        altura, 'As notas conectam identidade e microdados',
        'Notas conectam identidade e microdados. Estimativa de 14,7 milhões de pessoas '
        'distintas com registros vinculados no SISU–ENEM (2010–2023).',
    )
    t = desenho.texto
    direita = LARGURA - MARGEM
    t(MARGEM, f'{base_rotulos:.1f}', 'Divulgações públicas', SECUNDARIO, classe='secundario')
    t(direita, f'{base_rotulos:.1f}', 'Microdados do ENEM', SECUNDARIO, classe='secundario',
      text_anchor='end')

    largura_caixa, largura_nota = 332, 113
    base_caixa = f'{meio + ALTURA_MAIUSCULA * TITULO / 2:.1f}'
    x_direita = direita - largura_caixa
    # (caixa, destaque "Notas", centro do rótulo na área livre da caixa)
    for x, x_nota, x_rotulo, rotulo in (
        (MARGEM, MARGEM + largura_caixa - largura_nota - 1,
         MARGEM + (largura_caixa - largura_nota) / 2, 'Identidade'),
        (x_direita, x_direita + 1,
         x_direita + (largura_caixa + largura_nota) / 2, 'Dados associados'),
    ):
        desenho.forma('rect', x=x, y=f'{topo_caixa:.1f}', width=largura_caixa,
                      height=altura_caixa, rx=8, fill_opacity='.025', class_='acerto grade')
        desenho.forma('rect', x=x_nota, y=f'{topo_caixa + 1:.1f}', width=largura_nota,
                      height=altura_caixa - 2, rx=7, fill_opacity='.10', class_='acerto')
        t(x_nota + largura_nota / 2, base_caixa, 'Notas', TITULO, classe='acerto',
          negrito=True, text_anchor='middle')
        t(f'{x_rotulo:.1f}', base_caixa, rotulo, TITULO, negrito=True, text_anchor='middle')

    xa, xb = MARGEM + largura_caixa, direita - largura_caixa
    desenho.forma('path', d=f'M{xa} {meio:.1f}H{xb}', stroke_width=2, stroke_opacity='.55',
                  fill='none', class_='ligacao')
    for cx in (xa, xb):
        desenho.forma('circle', cx=cx, cy=f'{meio:.1f}', r=3, class_='acerto')
    t((xa + xb) / 2, f'{meio - 12:.1f}', 'score linkage', SECUNDARIO, classe='secundario',
      font_style='italic', text_anchor='middle')

    desenho.forma('path', d=f'M{MARGEM} {y_divisoria:.1f}H{direita}', class_='grade')
    t(MARGEM, f'{base_numero:.1f}', numero, tamanho_numero, classe='acerto', negrito=True)
    x_bloco = MARGEM + largura_texto(numero, tamanho_numero, True) + 24
    t(f'{x_bloco:.1f}', f'{base_linha1:.1f}',
      'de pessoas distintas estimadas com registros vinculados', CORPO, negrito=True)
    t(f'{x_bloco:.1f}', f'{base_linha2:.1f}', 'SISU–ENEM · 2010–2023', SECUNDARIO,
      classe='secundario')
    desenho.salvar('artigo-score-linkage')


if __name__ == '__main__':
    imagem_exemplo()
    imagem_artigo()
