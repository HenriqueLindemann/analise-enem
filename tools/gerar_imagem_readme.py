#!/usr/bin/env python3
"""Gera o SVG do README com os mesmos dados usados no relatório de exemplo.

Execute da raiz: python tools/gerar_imagem_readme.py
"""
from math import ceil
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import meu_simulado as exemplo
from tri_enem.formatacao import formatar_numero

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def elemento(pai, tag, texto=None, **atributos):
    item = ET.SubElement(pai, f'{{{NS}}}{tag}', {
        chave.replace('_', '-'): str(valor) for chave, valor in atributos.items()
    })
    item.text = texto
    return item


def main():
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
    raiz = ET.Element(f'{{{NS}}}svg', {
        'viewBox': '0 0 1100 650', 'width': '1100', 'height': '650',
        'role': 'img', 'aria-labelledby': 'titulo descricao',
    })
    elemento(raiz, 'title', 'Respostas → nota → impacto por questão', id='titulo')
    elemento(raiz, 'desc',
             f"Matemática, ENEM {exemplo.ANO}. "
             f"Nota estimada: {formatar_numero(resultado['nota'])}. "
             + ' '.join(
                 f"Q{q['posicao_caderno']}: ganho de "
                 f"{formatar_numero(q['ganho_se_acertasse'])} pontos se acertasse."
                 for q in erros
             ), id='descricao')
    estilo = elemento(raiz, 'style')
    grupo = elemento(raiz, 'g', font_family='Arial, Helvetica, sans-serif')

    def texto(x, y, conteudo, tamanho=17, classe='texto', **attrs):
        return elemento(grupo, 'text', conteudo, x=x, y=y, font_size=tamanho,
                        **{'class': classe}, **attrs)

    def seta(caminho):
        elemento(grupo, 'path', d=caminho, fill='none', stroke_width=1.8,
                 stroke_linecap='round', stroke_linejoin='round',
                 **{'class': 'seta'})

    texto(36, 35,
          f"ENEM {exemplo.ANO} · Matemática · {exemplo.COR_MT.capitalize()}",
          15, classe='secundario')
    texto(36, 88, 'Respostas', 23, font_weight='bold')
    texto(728, 88, 'Nota', 23, font_weight='bold')
    for linha in range(3):
        letras = exemplo.RESPOSTAS_MT[linha * 15:(linha + 1) * 15]
        for coluna, letra in enumerate(letras):
            texto(36 + coluna * 27, 136 + linha * 32, letra, 20,
                  font_family='monospace', classe='resposta')
    seta('M 529 156 H 645 M 637 148 L 645 156 L 637 164')
    texto(728, 166, formatar_numero(resultado['nota']), 64, font_weight='bold')
    texto(732, 201, f"{resultado['acertos']}/{resultado['total_itens']} acertos válidos",
          17, classe='secundario')

    texto(36, 317, 'Impacto por questão', 23, font_weight='bold')
    for y, classe, legenda in (
        (296, 'acerto', 'Acerto · perda se errasse'),
        (324, 'erro', 'Erro (*) · ganho se acertasse'),
    ):
        elemento(grupo, 'rect', x=769, y=y - 12, width=11, height=11,
                 rx=2, **{'class': classe})
        texto(790, y, legenda, 16, classe='secundario')

    x0, y0, largura, altura = 66, 593, 998, 208
    escala = max(10, ceil(max((valor for _, valor, _ in questoes), default=0) / 10) * 10)
    texto(36, 367, 'pts', 13, classe='secundario')
    for indice in range(5):
        valor = escala * indice / 4
        y = y0 - altura * indice / 4
        elemento(grupo, 'line', x1=x0, y1=y, x2=x0 + largura, y2=y,
                 stroke_width=1, **{'class': 'grade'})
        texto(x0 - 14, y + 4, f'{valor:g}', 13,
              classe='secundario', text_anchor='end')
    passo = largura / max(1, len(questoes))
    for indice, (questao, valor, classe) in enumerate(questoes):
        x = x0 + indice * passo + 3
        h = max(0.8, altura * max(0, valor) / escala)
        barra = elemento(grupo, 'rect', x=f'{x:.2f}', y=f'{y0 - h:.2f}',
                         width=f'{passo - 6:.2f}', height=f'{h:.2f}', rx=2,
                         **{'class': classe})
        elemento(barra, 'title',
                 f"Q{questao['posicao_caderno']}: {formatar_numero(valor)} pontos")
        cx, cy = x + (passo - 6) / 2 + 4, y0 - h - 9
        rotulo = str(questao['posicao_caderno']) + ('*' if classe == 'erro' else '')
        texto(f'{cx:.2f}', f'{cy:.2f}', rotulo, 13, classe=classe,
              transform=f'rotate(-90 {cx:.2f} {cy:.2f})')
    texto(66, 628, 'Maior impacto', 14, classe='secundario')
    texto(1064, 628, 'Menor impacto', 14, classe='secundario', text_anchor='end')
    # O <picture> do README escolhe a paleta, mantendo o fundo transparente.
    for sufixo, cores in (
        ('', ('#253746', '#596873', '#405562', '#20805f', '#bb503e', '#dce3e7', '#8a979f')),
        ('-dark', ('#e6edf3', '#a7b3bd', '#c1cdd7', '#63cba5', '#fa9a87', '#303b46', '#82939f')),
    ):
        estilo.text = '\n'.join(
            f'.{nome} {{ {"stroke" if nome in {"grade", "seta"} else "fill"}: {cor}; }}'
            for nome, cor in zip(
                ('texto', 'secundario', 'resposta', 'acerto', 'erro', 'grade', 'seta'), cores
            )
        )
        destino = RAIZ / f'docs/imagens/exemplo-matematica{sufixo}.svg'
        destino.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(raiz)
        ET.ElementTree(raiz).write(destino, encoding='utf-8', xml_declaration=True)
        print(destino)



if __name__ == '__main__':
    main()
