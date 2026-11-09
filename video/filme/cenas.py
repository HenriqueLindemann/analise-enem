# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""As cenas do filme. A fila de 45 respostas do estudante A atravessa todas elas:

bolhas → ordenadas por dificuldade → pontos no eixo → curvas → sino → campo de
respostas → grade da calculadora → base das barras de impacto → faixa → fila final.

Cada cena tem a sua geometria para os dois formatos lado a lado (`if V:`).
"""
import math

import cairo
import numpy as np

from . import relogio as TL
from .desenho import *  # noqa: F403
from .formatos import F

V = F.vertical
D = TL.D
N = TL.N

# ---------------------------------------------------------------- dados
ITENS = D['items']
Q0 = D['meta']['primeira_questao']
ORDEM = TL.ORDEM
RANK = {k: r for r, k in enumerate(ORDEM)}
ROWS = [D['duel']['A'], D['duel']['B']]
RESP_A = ROWS[0]['resp']
OK_A = TL.OK_A
ACERTOS_A = sum(OK_A)
NOTA_A, NOTA_B = ROWS[0]['nota'], ROWS[1]['nota']
GRID_NOTA = np.array(D['grid']['nota'])
GRID_THETA = np.array(D['grid']['theta'])
STEPS = D['posterior']['steps']
PSTEP = [np.array(s['post']) for s in STEPS]
FSTEP = [None] + [np.array(s['fator']) for s in STEPS[1:]]
NSTEP = [s['nota'] for s in STEPS]
PSTEP_Q = [np.array(s['post']) for s in D['posterior']['steps_q']]
NSTEP_Q = [s['nota'] for s in D['posterior']['steps_q']]
PMAX = max(float(p.max()) for p in PSTEP + PSTEP_Q)
IMPACT = D['impact']
BEST = max(range(N), key=lambda k: -1 if IMPACT[k]['ok'] else IMPACT[k]['v'])
HL = D['destaques']
VAL = D['validacao']


def sv(site, vertical):
    """Valor do site ou do formato vertical."""
    return vertical if V else site


def to_theta(n):
    return float(np.interp(n, GRID_NOTA, GRID_THETA))


def pcurve(it, n):
    """Probabilidade de acerto (ML3) na nota n."""
    th = to_theta(n)
    return it['c'] + (1 - it['c']) / (1 + math.exp(-it['a'] * (th - it['b'])))


def item(q):
    return ITENS[q - Q0]


def pct_truncado(p, casas=2):
    """99,996 → '99,99%': nunca arredonda para cima."""
    v = math.floor(p * 10 ** casas) / 10 ** casas
    return f'{v:.{casas}f}'.replace('.', ',') + '%'


# ================================================================ títulos
X0 = 72 if V else 150
XR = 944                                    # borda direita da coluna de conteúdo (vertical)
H1_Y, H1_SIZE, H1_LH = (340, 74, 88) if V else (200, 62, 0)
SUB_Y = 500 if V else 262


def headline(c, t, h):
    """Título do roteiro: uma linha no site, quebrado em '|' na vertical."""
    if not V:
        ws = h.palavras
        cols = None if h.azul is None else [BLUE if i >= h.azul else INK for i in range(len(ws))]
        words(c, ' '.join(ws), X0, H1_Y, H1_SIZE, INK, t, h.t0, mark=h.marca, out=h.saida, cols=cols)
        return
    before = 0
    for i, line in enumerate(h.texto.split('|')):
        n = len(line.split(' '))
        inside = lambda j: j is not None and before <= j < before + n
        cols = [BLUE] * n if inside(h.azul) else None
        words(c, line, X0, H1_Y + i * H1_LH, H1_SIZE, INK, t, h.t0 + before * TL.WORD_STAGGER,
              mark=h.marca - before if inside(h.marca) else None, out=h.saida, cols=cols)
        before += n


def headlines(c, t):
    for h in TL.TITULOS:
        if h.t0 - .5 <= t < h.saida + .5:
            headline(c, t, h)
    if TL.S2 <= t < TL.S3 + .5:
        out = TL.ICC_PHASES[0] - .5 if V else TL.COLA23[0]
        words(c, 'Parâmetros reais, publicados pelo INEP.', X0, SUB_Y, 32 if V else 30, BODY, t,
              TL.H1_CURVES + 1.0, f='med', out=out)


# ================================================================ S1: duelo
# Site: duas filas de 45. Vertical: duas grades 3×15 que, ordenadas, viram fáceis / médias / difíceis.
if V:
    CELL, PITCH = 40, 48
    GRID_CX0 = XR - CELL / 2 - 14 * PITCH
    BLOCK_Y = (648, 1030)               # linha de base do cabeçalho de cada estudante
    EASY, HARD = range(0, 15), range(N - 15, N)
else:
    CELL, PITCH = 26, 29
    ROW_Y = (433, 643)                  # centro das bolhas de A e B
    SCORE_X = 1770


def sorted_xy(r, row):
    """Centro da bolha na posição r (ordem da prova ou de dificuldade)."""
    if V:
        return GRID_CX0 + (r % 15) * PITCH, BLOCK_Y[row] + 60 + (r // 15) * PITCH
    return X0 + CELL / 2 + r * PITCH, ROW_Y[row]


def note_y(row):
    return BLOCK_Y[row] + 216 if V else ROW_Y[row] + 62


def duel_xy(t, k, row):
    """Bolha k: da ordem da prova à ordem de dificuldade, num arco."""
    r = RANK[k]
    m = eio(seg(t, TL.duel_sort(r, row), TL.duel_sort(r, row) + TL.DUEL_SORT_DUR))
    (x0, y0), (x1, y1) = sorted_xy(k, row), sorted_xy(r, row)
    arc = math.sin(math.pi * m) * min(1, abs(r - k) / 12 + .25) * (26 if V else 34)
    return lerp(x0, x1, m), lerp(y0, y1, m) + (arc if row and not V else -arc)


def band_count(row, ranks, ok=True):
    return sum(1 for r in ranks if bool(ROWS[row]['ok'][ORDEM[r]]) == ok)


def scene_duel(c, t):
    if t >= TL.S2 + .5:
        return
    out_b = eio(seg(t, TL.COLA12_OUT, TL.COLA12_OUT + .9))        # B sai por baixo
    fade_a = 1 - eio(seg(t, TL.COLA12_OUT, TL.COLA12_OUT + .5))   # rótulos de A somem
    drop_b = out_b * (420 if V else 380)
    keep = (fade_a, 1 - min(1, out_b * 2.5))

    for row in (0, 1):
        y = BLOCK_Y[row] if V else ROW_Y[row]
        drop = drop_b if row else 0
        la0, lstep = (.2, .1) if V else (1.25, .12)
        la = eo3(seg(t, la0 + row * lstep, la0 + .5 + row * lstep)) * keep[row]
        text(c, 'ESTUDANTE ' + 'AB'[row], X0, (y if V else y - 36) + drop, 26 if V else 22, BODY, la, 'bold',
             track=3)

        stu = ROWS[row]
        n_ok = 0
        for k in range(N):
            ok = bool(stu['ok'][k])
            tg = TL.duel_grade(k)
            if ok and t >= tg:
                n_ok += 1
            if row == 0 and t >= TL.COLA12_MOVE[0]:
                continue        # a fila de A segue para o eixo (fila_tapete)
            pk = seg(t, TL.duel_appear(k, row), TL.duel_appear(k, row) + (.4 if V else .45))
            if pk <= 0:
                continue
            x, yy = duel_xy(t, k, row)
            yy += drop + (out_b * 60 * (k / N) if row else 0)
            bump = math.sin(math.pi * seg(t, tg, tg + .28)) * .16 if ok else 0
            if row == 0:
                track(k, x, yy)
            bubble(c, x, yy, CELL * (.45 + .55 * eoback(pk) + bump), stu['resp'][k], eo3(seg(t, tg, tg + .3)), ok,
                   min(1, pk * 2) * (1 - out_b if row else 1))

        # contador de acertos; dá lugar à anotação depois da ordenação
        ca = eo3(seg(t, TL.DUEL_GRADE0 - .2, TL.DUEL_GRADE0 + .3)) * (1 - eio(seg(t, TL.DUEL_SORT0 - .4, TL.DUEL_SORT0)))
        if ca > 0:
            yc = (note_y(row) if V else y + 60) + drop
            w = number(c, str(n_ok), X0, yc, 34 if V else 28, GREEN, ca, 'black')
            text(c, ' de 45 acertos', X0 + w, yc, 30 if V else 24, BODY, ca, 'med')

        # nota: contador compartilhado; B para antes, A cruza a centena
        land = TL.DUEL_LAND_A if row == 0 else TL.DUEL_LAND_B
        na = eo3(seg(t, TL.DUEL_COUNT0 - .3, TL.DUEL_COUNT0 + .2)) * (fade_a if row == 0 else 1 - out_b)
        if na > 0:
            size = 92 if V else 84
            if V:
                final_w, _ = num_w(c, br(NOTA_A if row == 0 else NOTA_B), 'black', size)
                text(c, 'NOTA', XR - final_w - 18, y + drop, 22, BODY, na, 'bold', 'r', track=3)
                sx, sy = XR, y + 8 + drop
            else:
                text(c, 'NOTA', SCORE_X, y - 36 + drop, 20, BODY, na, 'bold', 'r', track=3)
                sx, sy = SCORE_X, y + 34 + drop
            col = mix(INK, BLUE if row == 0 else BODY, seg(t, land, land + .5))
            pop = 1 + .06 * math.sin(math.pi * seg(t, land, land + .35))
            c.save()
            c.translate(sx, sy)
            c.scale(pop, pop)
            s = br(TL.duel_counter(t, row))
            w, dw = num_w(c, s, 'black', size)
            hk = sweep(t, TL.DUEL_CENTENA)
            if hk > 0:     # traço sob a centena: 8 contra 7
                c.set_source_rgba(*YELLOW, .95 * hk * na)
                c.rectangle(-w, 12 if V else 10, dw * hk, 8 if V else 7)
                c.fill()
            number(c, s, 0, 0, size, col, na, 'black', 'r')
            c.restore()

    # colchete da diferença
    dk = eo3(seg(t, TL.DUEL_DIFF, TL.DUEL_DIFF + .7)) * (1 - out_b)
    if dk > 0:
        diff = '+' + br(NOTA_A - NOTA_B)
        if V:
            y0 = BLOCK_Y[0] - 62
            bracket(c, 968, y0, y0 + (BLOCK_Y[1] + 14 - y0) * dk, -10, INK, .75 * dk, 2.4)
            number(c, diff, 950, note_y(0) + 4, 44, BLUE, dk, 'black', 'r')
        else:
            y0 = ROW_Y[0] - 30
            bracket(c, 1810, y0, y0 + (ROW_Y[1] + 40 - y0) * dk, -9, INK, .75 * dk, 2)
            c.save()
            c.translate(1844, (ROW_Y[0] + ROW_Y[1]) / 2 + 5)
            c.rotate(-math.pi / 2)
            number(c, diff, 0, 12, 34, INK, dk, 'black', 'c')
            c.restore()

    duel_difficulty(c, t, out_b, keep, drop_b)
    duel_notes(c, t, keep, drop_b)

    fa = eo3(seg(t, TL.DUEL_SOURCE, TL.DUEL_SOURCE + .6)) * (1 - eio(seg(t, TL.COLA12_OUT - .3, TL.COLA12_OUT + .2)))
    if V:
        text(c, 'Matemática · ENEM 2024 · parâmetros reais do INEP', X0, SUB_Y, 30, MUTED, fa, 'med')
    else:
        text(c, 'Parâmetros reais publicados pelo INEP · Matemática, ENEM 2024', W / 2, 1012, 22, MUTED, fa, 'reg', 'c')


def duel_difficulty(c, t, out_b, keep, drop_b):
    """Depois da ordenação: eixo fácil → difícil (site) ou rótulos das faixas (vertical)."""
    if V:
        ax = eo3(seg(t, TL.DUEL_AXIS, TL.DUEL_AXIS + .6))
        if ax <= 0:
            return
        for row in (0, 1):
            for ln, (s, col) in enumerate((('FÁCEIS', GREEN), ('MÉDIAS', MUTED), ('DIFÍCEIS', CORAL))):
                _, yy = sorted_xy(ln * 15, row)
                text(c, s, X0 - (1 - ax) * 12, yy + 8 + (drop_b if row else 0), 22, col, ax * keep[row], 'bold',
                     track=2)
        return
    ax = eo3(seg(t, TL.DUEL_AXIS, TL.DUEL_AXIS + .8)) * (1 - out_b)
    if ax <= 0:
        return
    y = ROW_Y[1] + 118 + out_b * 300
    x1 = X0 + (N * PITCH - 6) * ax
    g = cairo.LinearGradient(X0, 0, X0 + N * PITCH, 0)
    g.add_color_stop_rgba(0, *GREEN, ax)
    g.add_color_stop_rgba(1, *CORAL, ax)
    c.new_path()
    c.set_source(g)
    c.set_line_width(3)
    c.move_to(X0, y)
    c.line_to(x1, y)
    c.stroke()
    arrow_head(c, x1, y, 10, CORAL, ax)
    la = eo3(seg(t, TL.DUEL_AXIS + .4, TL.DUEL_AXIS + 1.0)) * (1 - out_b)
    text(c, 'MAIS FÁCIL', X0, y + 36, 19, GREEN, la, 'bold', track=3)
    text(c, 'MAIS DIFÍCIL', X0 + N * PITCH, y + 36, 19, CORAL, la, 'bold', 'r', track=3)


def _dashed_box(c, x, y, w, h, r, col, fill_a, line_a):
    rrect(c, x, y, w, h, r)
    c.set_source_rgba(*col, fill_a)
    c.fill_preserve()
    c.set_source_rgba(*col, line_a)
    c.stroke()


def duel_notes(c, t, keep, drop_b):
    """Por que as notas diferem: onde cada estudante acertou e errou."""
    if V:
        notes = ((0, TL.DUEL_NOTE_A, f'Acertou todas as fáceis e {band_count(0, HARD)} difíceis.', GREEN),
                 (1, TL.DUEL_NOTE_B, f'Errou {band_count(1, EASY, False)} fáceis e acertou {band_count(1, HARD)} '
                                     'difíceis.', INK))
    else:
        notes = ((0, TL.DUEL_NOTE_A, 'Acertou todas as fáceis.', GREEN),
                 (1, TL.DUEL_NOTE_B, 'Errou fáceis e acertou as mais difíceis.', INK))
    for row, t0, s, col in notes:
        ak = eo3(seg(t, t0, t0 + .6)) * keep[row]
        if ak <= 0:
            continue
        dy = drop_b if row else 0
        wk = eio(seg(t, t0, t0 + .8))
        c.set_dash([6, 5] if V else [5, 4])
        c.set_line_width(2 if V else 1.6)
        if V:
            x_l, span = GRID_CX0 - CELL / 2 - 7, 14 * PITCH + CELL + 14
            band = EASY if row == 0 else HARD
            _, yb = sorted_xy(band[0], row)
            _dashed_box(c, x_l, yb - CELL / 2 - 7 + dy, span * wk, CELL + 14, 10, col,
                        .07 * ak if row == 0 else .05 * ak, .8 * ak if row == 0 else .7 * ak)
        elif row == 0:
            n_easy = next(r for r, k in enumerate(ORDEM) if not OK_A[k])
            _dashed_box(c, X0 - 6, ROW_Y[0] - CELL / 2 - 7, (n_easy * PITCH + 9) * wk, CELL + 14, 8, GREEN,
                        .07 * ak, .8 * ak)
        if row == 1:
            for r in (EASY if V else range(10)):
                if not ROWS[1]['ok'][ORDEM[r]]:
                    x, yy = sorted_xy(r, 1)
                    c.new_path()
                    c.arc(x, yy + dy, CELL / 2 + (6 if V else 5), 0, 2 * math.pi * wk)
                    c.set_source_rgba(*INK, .75 * ak)
                    c.stroke()
            if not V:
                _dashed_box(c, X0 + (N - 10) * PITCH - 6, ROW_Y[1] + dy - CELL / 2 - 7, (10 * PITCH + 9) * wk,
                            CELL + 14, 8, INK, .05 * ak, .7 * ak)
        c.set_dash([])
        text(c, s, X0 - (1 - ak) * 10, note_y(row) + dy, 30 if V else 28, col, ak, 'bold')


# ================================================================ S2/S3: um gráfico, o mesmo eixo de notas
IX = sv((150, 1240), (156, 944))
IY0, IY1 = sv((850, 350), (1300, 800))
NX = (200, 1000)
DENS_H = sv(460, 390)
DOT_D = sv(11, 12)
PANEL_X, PANEL_Y = 1350, 600            # painel à direita (site) ou entre título e gráfico (vertical)


def ix(n):
    return IX[0] + (n - NX[0]) / (NX[1] - NX[0]) * (IX[1] - IX[0])


def iy(p):
    return IY0 + p * (IY1 - IY0)


def _beeswarm(d=sv(13, 14)):
    """Um ponto por questão em x = dificuldade; empilha os que se tocam."""
    placed, out = [], {}
    for k in ORDEM:
        x = ix(ITENS[k]['b_nota'])
        lv = 0
        while any(abs(x - px) < d and pl == lv for px, pl in placed):
            lv += 1
        placed.append((x, lv))
        out[k] = (x, IY0 - sv(10, 11) - d * lv)
    return out


TAPETE = _beeswarm()
TAPETE_X0 = min(x for x, _ in TAPETE.values())
TAPETE_CX = (TAPETE_X0 + max(x for x, _ in TAPETE.values())) / 2
MASK = (GRID_NOTA >= NX[0]) & (GRID_NOTA <= NX[1])
GX = np.array([ix(n) for n in GRID_NOTA[MASK]])
CURVES = [(HL['facil'], GREEN), (HL['discriminacao'], BLUE), (HL['dificil'], BERRY)]
CURVE_P = {q: np.array([pcurve(item(q), n) for n in GRID_NOTA[MASK]]) for q, _ in CURVES}


def chart_axes(c, t, a=1.0, labels=1.0):
    """O eixo de notas nasce sob os pontos; a grade de probabilidade só existe enquanto há curvas."""
    base = eio(seg(t, *TL.COLA12_AXIS))
    if base <= 0 or a <= 0.003:
        return
    ga = eo3(seg(t, TL.S2 + .5, TL.S2 + 1.3)) * labels
    prob = ga * (1 - eio(seg(t, TL.COLA23[0], TL.COLA23[0] + .5)))
    c.set_line_width(sv(1.2, 1.4))
    for p in (.25, .5, .75, 1):
        c.new_path()
        c.set_source_rgba(*LINE, prob * a)
        c.move_to(IX[0], iy(p))
        c.line_to(IX[1], iy(p))
        c.stroke()
    for p in (0, .25, .5, .75, 1):
        text(c, f'{int(p * 100)}%', IX[0] - sv(20, 14), iy(p) + sv(8, 9), sv(22, 26), BODY, prob * a, 'med', 'r')
    text(c, 'CHANCE DE ACERTAR', X0, IY1 - sv(30, 38), sv(20, 22), BODY, prob * a, 'bold', track=sv(1.4, 1.6))
    c.new_path()
    c.set_source_rgba(*BORDER, a)
    c.set_line_width(sv(1.6, 2))
    c.move_to(lerp(TAPETE_CX, IX[0], base), IY0)
    c.line_to(lerp(TAPETE_CX, IX[1], base), IY0)
    c.stroke()
    cap = eo3(seg(t, TL.S2 + .1, TL.S2 + .7)) * (1 - eio(seg(t, TL.ICC_PHASES[0] - .6, TL.ICC_PHASES[0])))
    caption = ['Respostas de A, na', 'dificuldade de cada questão'] if V else \
        ['Respostas de A, na dificuldade de cada questão']
    for i, line in enumerate(reversed(caption)):
        text(c, line, TAPETE_X0 - 22, IY0 - sv(7, 12) - 32 * i, sv(21, 25), BODY, cap * a, 'semi', 'r')
    for n in range(200, 1001, 200):
        text(c, str(n), ix(n), IY0 + sv(34, 42), sv(22, 26), BODY, ga * a, 'med', 'c')
    text(c, 'NOTA NA ESCALA DO ENEM', IX[1], IY0 + sv(76, 86), sv(19, 22), BODY, ga * a, 'bold', 'r', track=sv(1.4, 1.6))


def beat_weights(t):
    P = TL.ICC_PHASES
    wa = win(t, P[0], P[1], .45, .45)
    wb = win(t, P[1], P[2], .45, .45)
    wc = eo3(seg(t, P[2], P[2] + .6)) * (1 - eio(seg(t, TL.COLA23[0], TL.COLA23[0] + .4)))
    return wa, wb, wc, eio(seg(t, *TL.ICC_MOVE))


def curve_state(t, j):
    """(subida do ponto, traçado) da curva j; recolhem ao ponto na cola S2→S3."""
    birth = TL.CURVE_BIRTH[j]
    r0 = TL.COLA23[0] + .06 * j
    lift = eo3(seg(t, birth, birth + TL.CURVE_LIFT)) * (1 - eio(seg(t, r0 + .35, r0 + .8)))
    draw = eio(seg(t, *TL.curve_draw(j))) * (1 - eio(seg(t, r0, r0 + .45)))
    return lift, draw


def scene_curves(c, t):
    if not TL.CURVE_BIRTH[0] <= t < TL.S3 + .6:
        return
    wa, wb, wc, move = beat_weights(t)
    for j, (q, col) in enumerate(CURVES):
        lift, draw = curve_state(t, j)
        if lift <= 0:
            continue
        it = item(q)
        bx, ty = TAPETE[q - Q0]
        by = iy((1 + it['c']) / 2)
        focus_b = (1 - move) if q == HL['facil'] else move if q == HL['dificil'] else 0
        alpha = ((1 - .78 * wa * (q != HL['discriminacao']))
                 * (1 - .86 * wc * (q != HL['facil']))
                 * (1 - .6 * wb * (1 - focus_b)))
        y = lerp(ty, by, lift)
        dashed_line(c, bx, ty - sv(7, 8), bx, y, col, .55 * alpha * min(1, lift * 3), sv(1.6, 1.8), sv((4, 6), (5, 7)))
        if draw > 0:            # a curva se desenha do ponto para os dois lados
            i0 = np.searchsorted(GX, bx)
            lo = int(i0 - i0 * draw)
            hi = int(i0 + (len(GX) - 1 - i0) * draw)
            stroke_path(c, list(zip(GX[lo:hi + 1], iy(CURVE_P[q][lo:hi + 1]))), col, alpha, sv(4.5, 5))
        dot(c, bx, y, sv(6, 7), col, alpha)
        la = eo3(seg(t, TL.curve_draw(j)[1] - .4, TL.curve_draw(j)[1] + .2)) * alpha * (draw > .5)
        text(c, f'Q{q}', bx - 18, by - sv(20, 22), sv(27, 30), col, la, 'bold', 'r')
        vb = wb * focus_b * (draw > .9)
        if vb > 0:
            c.new_path()
            c.set_source_rgba(*col, .08 * vb)
            c.rectangle(bx - sv(13, 14), IY1, sv(26, 28), IY0 - IY1)
            c.fill()
            text(c, br(it['b_nota']), bx + 18, by + sv(34, 38), sv(28, 30), col, vb, 'bold')

    if wa > 0:      # a: tangente da Q160 no ponto de dificuldade
        it = item(HL['discriminacao'])
        nb, pm = it['b_nota'], (1 + it['c']) / 2
        dth = (to_theta(nb + 1) - to_theta(nb - 1)) / 2
        slope = (1 - it['c']) * it['a'] / 4 * dth
        dn = 62
        stroke_path(c, [(ix(nb - dn), iy(pm - slope * dn)), (ix(nb + dn), iy(pm + slope * dn))], INK, wa, sv(3, 3.5))

    if wb > 0:      # b: seta da fácil para a difícil
        left, right = ix(item(HL['facil'])['b_nota']), ix(item(HL['dificil'])['b_nota'])
        tip = lerp(left, right, move)
        ya, head = IY0 + sv(110, 112), sv((11, 8), (13, 9))
        c.new_path()
        c.set_source_rgba(*BLUE, wb)
        c.set_line_width(sv(3, 3.5))
        c.move_to(left, ya)
        c.line_to(tip, ya)
        if move > .03:
            c.stroke()
            c.move_to(tip - head[0], ya - head[1])
            c.line_to(tip, ya)
            c.line_to(tip - head[0], ya + head[1])
            c.stroke()
        c.new_path()
        text(c, 'MAIOR DIFICULDADE', (left + right) / 2, ya + sv(36, 40), sv(21, 24), BLUE, wb * seg(move, .2, .6),
             'bold', 'c', track=sv(1.4, 1.6))

    if wc > 0:      # c: piso da Q154
        it = item(HL['facil'])
        yf = iy(it['c'])
        reveal = eio(seg(t, *TL.ICC_FLOOR))
        right = IX[0] + (IX[1] - IX[0]) * reveal
        c.new_path()
        c.set_source_rgba(*GREEN, .05 * wc)
        c.rectangle(IX[0], yf, right - IX[0], IY0 - yf)
        c.fill()
        dashed_line(c, IX[0], yf, right, yf, GREEN, wc, sv(3, 3.5), sv((9, 6), (10, 7)))
        bx = IX[0] + sv(32, 30)
        bracket(c, bx, yf, IY0, 10, GREEN, wc * reveal, sv(2.5, 2.8))
        la = eo3(seg(t, TL.ICC_FLOOR[1] - .3, TL.ICC_FLOOR[1] + .4)) * wc
        text(c, 'c = ' + br(it['c'] * 100, 2) + '%', bx + sv(26, 24), (yf + IY0) / 2 + sv(11, 12), sv(32, 34), GREEN,
             la, 'bold')
        text(c, f'piso da Q{HL["facil"]}', IX[1] - sv(18, 12), yf - sv(16, 18), sv(25, 28), GREEN, la, 'bold', 'r')

    panel_beats(c, t)


def panel_beats(c, t):
    """Uma explicação por vez: a, b, c."""
    P = TL.ICC_PHASES
    if not P[0] <= t < TL.S3:
        return
    i = 0 if t < P[1] else 1 if t < P[2] else 2
    a = win(t, P[i], P[i + 1] if i < 2 else TL.COLA23[0] + .35, .55, .4)
    letter, heading = [('a', 'Discriminação'), ('b', 'Dificuldade'), ('c', 'Acerto casual')][i]
    piso = br(100 * item(HL['facil'])['c'], 2) + '%'
    if V:
        desc, detail, col = [
            ('Inclinação da curva perto da dificuldade.', f'Q{HL["discriminacao"]}: uma subida mais rápida.', BLUE),
            ('Posição da curva na escala de notas.', 'Mais à direita, maior dificuldade.', BLUE),
            ('Chance de acertar sem saber a resposta.', f'Q{HL["facil"]}: {piso} de piso.', GREEN)][i]
        dy = (1 - eo3(seg(t, P[i], P[i] + .55))) * 14
        w = text(c, letter, X0, PANEL_Y + dy, 64, BLUE, a, 'black')
        text(c, heading, X0 + w + 20, PANEL_Y + dy, 46, INK, a, 'bold')
        text(c, desc, X0, PANEL_Y + 54 + dy, 34, BODY, a, 'med')
        text(c, detail, X0, PANEL_Y + 104 + dy, 34, col, a, 'bold')
        return
    px = PANEL_X
    lines = [['Inclinação da curva', 'perto da dificuldade.'], ['Posição da curva', 'na escala de notas.'],
             ['Chance de acertar sem', 'saber a resposta.']][i]
    text(c, letter, px, 432, 52, BLUE, a, 'black')
    text(c, heading, px, 488, 36, INK, a, 'bold')
    for n, line in enumerate(lines):
        text(c, line, px, 537 + n * 36, 28, BODY, a, 'med')
    if i == 0:
        text(c, f'Q{HL["discriminacao"]} em destaque', px, 655, 28, BLUE, a, 'bold')
        text(c, 'Uma subida mais rápida.', px, 693, 26, BODY, a, 'med')
    elif i == 1:
        move = eio(seg(t, *TL.ICC_MOVE))
        text(c, 'Mais à direita,', px, 647, 30, BLUE, a, 'bold')
        text(c, 'maior dificuldade.', px, 688, 30, INK, a, 'bold')
        for n, (q, col) in enumerate(((HL['facil'], GREEN), (HL['dificil'], BERRY))):
            act = (1 - move) if n == 0 else move
            text(c, f'Q{q}', px, 765 + n * 60, 28, col, a * (.45 + .55 * act), 'bold')
            number(c, br(item(q)['b_nota']), 1770, 765 + n * 60, 32, col, a * (.45 + .55 * act), 'bold', 'r')
    else:
        text(c, f'Q{HL["facil"]}', px, 644, 28, GREEN, a, 'bold')
        text(c, piso, px, 730, 64, GREEN, a, 'black')


# ---------------------------------------------------------------- S3: as respostas esculpem a estimativa
def eap_state(t):
    """(densidade, faixa retirada, passo ativo, nota) em S3."""
    p = TL.eap_progress(t)
    if p >= N:
        return PSTEP[-1], None, None, NSTEP[-1]
    if p <= 0:
        return PSTEP[0] * eio(seg(t, *TL.EAP_PRIOR)), None, None, NSTEP[0]
    j = int(p)
    f = p - j
    base, nxt = PSTEP[j], PSTEP[j + 1]
    carved = base * FSTEP[j + 1]
    if f < .3:
        return base, None, j, NSTEP[j]
    if f < .65:
        s = eio((f - .3) / .35)
        return base + (carved - base) * s, (base, base + (carved - base) * s, 1.0), j, NSTEP[j]
    s = eio((f - .65) / .35)
    return carved + (nxt - carved) * s, (base, carved, 1 - s), j, lerp(NSTEP[j], NSTEP[j + 1], s)


def dens_ys(dens):
    return IY0 - dens[MASK] / PMAX * DENS_H


def draw_density(c, dens, a=1.0):
    ys = dens_ys(dens)
    c.new_path()
    c.move_to(GX[0], IY0)
    for x, y in zip(GX, ys):
        c.line_to(x, y)
    c.line_to(GX[-1], IY0)
    c.close_path()
    g = cairo.LinearGradient(0, IY0 - DENS_H, 0, IY0)
    g.add_color_stop_rgba(0, *BLUE, .30 * a)
    g.add_color_stop_rgba(1, *BLUE, .04 * a)
    c.set_source(g)
    c.fill()
    stroke_path(c, list(zip(GX, ys)), BLUE, a, sv(4, 4.5))
    return ys


def step_curve_alpha(t, j):
    start, dur = TL.eap_step(j), TL.eap_step_dur(j)
    slow = j in TL.SLOW_STEPS
    return (eo3(seg(t, start, start + .3 * dur)) * (1 - seg(t, start + dur, start + dur + (.5 if slow else sv(.45, .4))))
            * (.95 if slow else .6))


def scene_eap(c, t):
    if not TL.EAP_PRIOR[0] <= t < TL.COLA34[0] + 1.7:
        return
    out = 1 - eio(seg(t, TL.COLA34[0], TL.COLA34[0] + .4))             # textos saem
    deflate = 1 - eio(seg(t, TL.COLA34[0] + 1.1, TL.COLA34[0] + 1.6))  # o painel fica vazio
    dens, removed, jcur, nota = eap_state(t)
    dens = dens * deflate
    if removed is not None:         # a faixa que a resposta torna menos provável
        upper, lower, ra = removed
        col = GREEN if OK_A[ORDEM[jcur]] else CORAL
        c.new_path()
        for x, y in zip(GX, dens_ys(upper)):
            c.line_to(x, y)
        for x, y in zip(GX[::-1], dens_ys(lower)[::-1]):
            c.line_to(x, y)
        c.close_path()
        c.set_source_rgba(*col, (.28 if jcur in TL.SLOW_STEPS else .15) * ra * out)
        c.fill()
    ys = draw_density(c, dens)

    if jcur is not None or TL.EAP_STEPS[0] <= t < TL.EAP_END + .6:     # curvas das questões, na ordem do tapete
        jj = jcur if jcur is not None else N - 1
        for j in range(max(0, jj - 5), jj + 1):
            ca = step_curve_alpha(t, j) * out
            if ca <= 0.003:
                continue
            k = ORDEM[j]
            col = GREEN if OK_A[k] else CORAL
            slow = j in TL.SLOW_STEPS
            stroke_path(c, list(zip(GX, iy(FSTEP[j + 1][MASK]))), col, ca, (sv(3.5, 4) if slow else sv(2.5, 3)))
            if slow:
                it = ITENS[k]
                start = TL.eap_step(j)
                la = win(t, start + .15, start + TL.eap_step_dur(j) + .3, .25, .3) * out
                my = iy((1 + it['c']) / 2 if OK_A[k] else (1 - it['c']) / 2)
                text(c, f'Q{it["q"]}', TAPETE[k][0] + sv(16, 18), my - sv(14, 16), sv(26, 30), col, la, 'bold')

    ma = eo3(seg(t, TL.EAP_STEPS[0] - .3, TL.EAP_STEPS[0] + .2)) * deflate
    if ma > 0:                      # a estimativa: linha na nota do motor e número sobre o pico
        x = ix(nota)
        ytop = float(np.interp(x, GX, ys))
        c.new_path()
        c.set_source_rgba(*INK, .75 * ma)
        c.set_line_width(sv(2, 2.4))
        c.move_to(x, IY0)
        c.line_to(x, ytop)
        c.stroke()
        dot(c, x, ytop, sv(6, 7), INK, ma)
        fin = eio(seg(t, TL.EAP_END, TL.EAP_LAND))
        size = sv(30, 34) + 66 * fin
        s = br(nota)
        yn = ytop - sv(22, 24) - 14 * fin
        w, _ = num_w(c, s, 'black', size)
        xc = min(x, XR - w / 2) if V else x
        marker(c, xc - w / 2, yn, w, size, sweep(t, TL.MARK_EAP), ma)
        number(c, s, xc, yn, size, mix(BODY, INK, fin), ma, 'black', 'c')

    rules = [(TL.eap_step(0) + .2, 'Acerto', GREEN, 'Notas abaixo da dificuldade|ficam menos prováveis.'),
             (TL.eap_step(TL.FIRST_ERROR) + .2, 'Erro', CORAL, 'Notas acima da dificuldade|ficam menos prováveis.')]
    for n, (t0, head, col, rule) in enumerate(rules):
        ra = win(t, t0, TL.EAP_END + .3, .5, .5)
        if V:
            y0 = PANEL_Y - 30 + n * 112
            text(c, head, X0, y0, 40, col, ra, 'bold')
            text(c, rule.replace('|', ' '), X0, y0 + 44, 32, BODY, ra, 'med')
        else:
            y0 = 452 + n * 170
            text(c, head, PANEL_X, y0, 32, col, ra, 'bold')
            for i, line in enumerate(rule.split('|')):
                text(c, line, PANEL_X, y0 + 44 + i * 36, 27, BODY, ra, 'med')
    fa = eo3(seg(t, TL.EAP_LAND + .25, TL.EAP_LAND + .8)) * out
    if fa > 0:
        x, y = (X0, PANEL_Y + 20) if V else (PANEL_X, IY0 - float(PSTEP[-1].max()) / PMAX * DENS_H - 36)
        w = number(c, str(ACERTOS_A), x, y, sv(64, 72), GREEN, fa, 'black')
        text(c, ' de 45 acertos', x + w, y, sv(30, 34), BODY, fa, 'med')


def tapete_departure(k):
    return TL.COLA34[0] + .3 + k * .012


def scene_chart(c, t):
    """S2 e S3; na cola S3→S4 o gráfico encolhe até o painel da calculadora."""
    m = eio(seg(t, TL.COLA34[0] + .15, TL.COLA34[0] + 1.2))
    if m <= 0:
        chart_axes(c, t)
        scene_eap(c, t)
    elif t < TL.COLA34[0] + 1.7:
        xf = (XF_MINI[0] * m, XF_MINI[1] * m, lerp(1, XF_MINI[2], m), lerp(1, XF_MINI[3], m))
        with_xf(c, xf, lambda: (chart_axes(c, t, 1 - seg(m, .9, 1), 1 - m), scene_eap(c, t)))
    fila_tapete(c, t)
    scene_curves(c, t)


def fila_tapete(c, t):
    """Fila ordenada de A → pontos sob o eixo (S2); em S3 cada ponto acende quando age."""
    if not TL.COLA12_MOVE[0] <= t < TL.S4 + 1.5:
        return
    for k in range(N):
        if t >= tapete_departure(k):
            continue        # segue para o campo de respostas (fila_demo)
        r = RANK[k]
        ok = OK_A[k]
        x1, y1 = TAPETE[k]
        m = eio(seg(t, TL.cola12_move(r), TL.COLA12_MOVE[1]))
        if m < 1:
            x0, y0 = sorted_xy(r, 0)
            x = lerp(x0, x1, m)
            y = lerp(y0, y1, m) - math.sin(math.pi * m) * sv(40, 50)
            bubble(c, x, y, lerp(CELL, DOT_D, eio(seg(m, .15, .85))), RESP_A[k], 1, ok, 1,
                   letter_a=1 - seg(m, 0, .45))
            track(k, x, y)
            continue
        track(k, x1, y1)
        a, ring = 1.0, 0.0
        if t >= TL.S3:
            ts = TL.eap_step(r)
            pending = eio(seg(t, TL.S3 + .2, TL.S3 + .7)) * (1 - seg(t, ts - .05, ts + .1))
            a = 1 - .62 * pending
            ring = math.sin(math.pi * seg(t, ts - .05, ts + (.5 if r in TL.SLOW_STEPS else .3))) * .9
        bubble(c, x1, y1, DOT_D, None, 1, ok, a, ring=ring)


# ================================================================ S4: a plataforma, numa respiração
if V:
    WIN = (60, 250, 960, 1232)
    CL, CW = 108, 864                       # coluna interna da janela
    FIELD = (CL, 584, CW, 76)
    GRID_BOX = (CL - 10, 570, CW + 20, 250)
    BUTTON0, BUTTON1, BUTTON_H = 736, 884, 72
    RCARD = (CL, 990, CW, 462)
    SLOT = (CL + CW / 2, 1160)
    MB = 1400                               # linha de base do gráfico da plataforma
    _SX = (CW - 120) / (IX[1] - IX[0])
    XF_MINI = (CL + 60 - IX[0] * _SX, MB - IY0 * .5, _SX, .5)
    TRAY = (WIN[0] + WIN[2] - 56, WIN[1] + 28)
    POINTER_HOME, POINTER_REST = (900, 905), (900, 1032)
    PDF_CTRL = (1080, 760)                  # o voo do PDF sobe pela borda direita
else:
    WIN = (110, 64, 1700, 976)
    CL, CW = 170, 890
    FIELD = (CL, 520, CW, 70)
    GRID_BOX = (CL - 10, 512, CW + 20, 256)
    BUTTON0, BUTTON1, BUTTON_H = 650, 930, 64
    RCARD = (1120, 150, 640, 850)
    SLOT = (1440, 350)
    MB = 800
    _SX = 560 / (IX[1] - IX[0])
    XF_MINI = (1160 - IX[0] * _SX, MB - IY0 * _SX, _SX, _SX)
    TRAY = (1712, 90)
    POINTER_HOME, POINTER_REST = (1040, 846), (1082, 792)
    PDF_CTRL = (1330, 980)                  # o voo contorna a grade por baixo e sobe pela direita
BIG = (-30, -30, W + 60, H + 60)
CMID = CL + CW / 2
FIELD_CY = FIELD[1] + FIELD[3] / 2
CLICK1 = (CMID + 250, BUTTON0 + BUTTON_H / 2 + 2)      # o ponteiro clica à direita do rótulo
CLICK2 = (CMID + 250, BUTTON1 + BUTTON_H / 2 + 2)
NOTA_SIZE = sv(104, 116)


def slot_x(k):
    """Letra k no campo de respostas, em grupos de 5."""
    return CL + sv(22, 34) + k * sv(17, 16) + (k // 5) * sv(9, 10) + sv(8.5, 8)


def cell_c(k):
    return CL + CW / 15 * (k % 15 + .5), sv(556, 614) + sv(82, 78) * (k // 15)


def mini_x(n):
    return XF_MINI[0] + ix(n) * XF_MINI[2]


def button_y(t):
    return lerp(BUTTON0, BUTTON1, eio(seg(t, TL.DEMO_TO_GRID[0], TL.DEMO_TO_GRID[1] + .2)))


def window_k(t):
    return eio(seg(t, TL.COLA34[0] + .15, TL.COLA34[0] + 1.25)) * (1 - eio(seg(t, TL.COLA45[0], TL.COLA45[0] + .9)))


def ui_alpha(t):
    return eo3(seg(t, TL.COLA34[0] + .8, TL.COLA34[0] + 1.4)) * (1 - eio(seg(t, TL.COLA45[0], TL.COLA45[0] + .35)))


def press_k(t):
    return sum(math.sin(math.pi * seg(t, tc, tc + .22)) for tc in (TL.DEMO_CLICK, TL.DEMO_PDF_CLICK))


def draw_cursor(c, x, y, a=1.0, press=0.0):
    if a <= 0.003:
        return
    s = sv(1.35, 1.8) * (1 - .12 * press)
    p = [(0, 0), (0, 22), (5.5, 17), (9.5, 26), (13.5, 24.3), (9.6, 15.6), (16.5, 15.6)]
    c.save()
    c.translate(x, y)
    for dx, col, al in ((sv(2, 2.5), INK, .18), (0, WHITE, 1)):
        c.new_path()
        for q in p:
            c.line_to(q[0] * s + dx, q[1] * s + dx * 1.5)
        c.close_path()
        c.set_source_rgba(*col, al * a)
        if dx:
            c.fill()
        else:
            c.fill_preserve()
            c.set_source_rgba(*INK, a)
            c.set_line_width(sv(1.6, 2))
            c.set_line_join(cairo.LINE_JOIN_ROUND)
            c.stroke()
    c.restore()


def reach(t, t0, t1, p0, p1, bend):
    """Gesto de mão: velocidade de jerk mínimo num arco leve (bend = flecha / distância)."""
    s = clamp((t - t0) / (t1 - t0))
    s = s ** 3 * (10 - 15 * s + 6 * s * s)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    q = ((p0[0] + p1[0]) / 2 - 2 * bend * dy, (p0[1] + p1[1]) / 2 + 2 * bend * dx)
    return bezier(p0, q, p1, s)


def ripple(c, x, y, t, tc, col):
    k = seg(t, tc, tc + .5)
    if 0 < k < 1:
        c.new_path()
        c.set_source_rgba(*col, .5 * (1 - k))
        c.set_line_width(sv(3, 3.5))
        c.arc(x, y, sv(6, 8) + sv(30, 36) * eo3(k), 0, 2 * math.pi)
        c.stroke()


def select_box(c, x, y, w, label, value, a, swatch=None):
    h = sv(54, 62)
    text(c, label, x, y - sv(14, 16), sv(22, 26), BODY, a, 'semi')
    card(c, x, y, w, h, sv(7, 8), a, fill=PAPER, sh=False)
    vx = x + sv(18, 20)
    if swatch:
        r = sv(8, 9)
        c.new_path()
        c.set_source_rgba(*swatch, a)
        c.arc(vx + r, y + h / 2, r, 0, 2 * math.pi)
        c.fill()
        vx += sv(26, 30)
    text(c, value, vx, y + sv(36, 41), sv(25, 30), INK, a, 'med')
    cx, cy, s = x + w - sv(23, 28), y + sv(24, 27), sv(5, 6)
    c.new_path()
    c.set_source_rgba(*MUTED, a)
    c.set_line_width(sv(2.2, 2.6))
    c.move_to(cx - s, cy)
    c.line_to(cx, cy + s)
    c.line_to(cx + s, cy)
    c.stroke()


def pdf_icon(c, x, y, scale, a=1.0, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    card(c, -43, -58, 86, 116, 6, a, fill=WHITE, border=BORDER, sh=scale > .6)
    c.new_path()
    c.set_source_rgba(*CORAL, a)
    rrect(c, -30, -42, 34, 16, 3)
    c.fill()
    text(c, 'PDF', -13, -29.5, 12, WHITE, a, 'bold', 'c')
    for j in range(5):
        c.new_path()
        c.set_source_rgba(*LINE, a)
        c.rectangle(-30, -12 + j * 13, 60 - (j % 2) * 14, 4)
        c.fill()
    c.restore()


def demo_state(t):
    """(densidade, nota) da plataforma: vazia, depois os passos na ordem das questões."""
    p = TL.demo_progress(t)
    if p <= 0:
        return PSTEP_Q[0] * eio(seg(t, TL.DEMO_GRADE0 - .5, TL.DEMO_GRADE0)), NSTEP_Q[0]
    if p >= N:
        return PSTEP_Q[-1], NSTEP_Q[-1]
    j = int(p)
    e = eio(p - j)
    return PSTEP_Q[j] + (PSTEP_Q[j + 1] - PSTEP_Q[j]) * e, lerp(NSTEP_Q[j], NSTEP_Q[j + 1], e)


def demo_window(c, t):
    """Moldura da janela: cresce das bordas na cola S3→S4 e se abre na cola S4→S5."""
    if not TL.COLA34[0] <= t < TL.S5 + .3:
        return
    wk = window_k(t)
    if wk <= .003:
        return
    x, y, w, h = (lerp(b, a, wk) for a, b in zip(WIN, BIG))
    al = min(1, wk * 1.4)
    bar_h = sv(52, 58)
    card(c, x, y, w, h, sv(16, 20), al, fill=WHITE, sh=wk > .5)
    c.new_path()
    c.set_source_rgba(*PAPER, al)
    rrect(c, x + 1, y + 1, w - 2, bar_h, sv(15, 19))
    c.fill()
    c.new_path()
    c.rectangle(x + 1, y + bar_h - sv(12, 14), w - 2, sv(13, 15))
    c.fill()
    c.set_source_rgba(*LINE, al)
    c.set_line_width(sv(1.2, 1.4))
    c.move_to(x + 1, y + bar_h + 1)
    c.line_to(x + w - 1, y + bar_h + 1)
    c.stroke()
    ta = eo3(seg(wk, .7, 1)) * ui_alpha(t) ** .3
    ph = sv(31, 37)
    card(c, x + 26, y + 11, sv(190, 220), ph, ph / 2, ta, fill=WHITE, sh=False)
    text(c, 'notatri.com', x + sv(44, 46), y + sv(34, 38), sv(21, 26), BLUE, ta, 'bold')


def scene_demo(c, t):
    if not TL.COLA34[0] <= t < TL.S5 + .3:
        return
    ua = ui_alpha(t)
    if ua <= 0.003:
        return
    grid_k = eio(seg(t, *TL.DEMO_TO_GRID))

    if V:                           # formulário já preenchido
        text(c, 'Sua prova', CL, 372, 40, INK, ua, 'bold')
        select_box(c, CL, 438, 380, 'Ano da prova', str(D['meta']['ano']), ua)
        select_box(c, CL + 420, 438, CW - 420, 'Cor do caderno', D['meta']['cor'].capitalize(), ua, BLUE)
        text(c, 'Respostas · Matemática', CL, FIELD[1] - 16, 26, BODY, ua, 'semi')
    else:
        text(c, 'Sua prova', CL, 180, 30, INK, ua, 'bold')
        select_box(c, CL, 244, 300, 'Ano da prova', str(D['meta']['ano']), ua)
        text(c, 'Matemática', CL, 352, 28, INK, ua, 'bold')
        select_box(c, CL, 412, 300, 'Cor do caderno', D['meta']['cor'].capitalize(), ua, BLUE)
        text(c, 'Respostas', CL, FIELD[1] - 14, 22, BODY, ua, 'semi')
    focus = eo3(seg(t, TL.COLA34[1] - .3, TL.COLA34[1]))
    fx, fy, fw, fh = (lerp(a, b, grid_k) for a, b in zip(FIELD, GRID_BOX))
    card(c, fx, fy, fw, fh, sv(8, 10), ua * (1 - grid_k), fill=PAPER, border=mix(LINE, BLUE, focus), sh=False,
         lw=sv(1.6, 2))

    n_typed = TL.demo_typed_count(t)
    if TL.COLA34[1] - .3 < t < TL.DEMO_CLICK:     # cursor de texto, fixo enquanto digita
        cx = slot_x(n_typed - 1) + sv(11, 12) if n_typed else CL + sv(18, 30)
        c.new_path()
        c.set_source_rgba(*BLUE, focus * ua)
        c.rectangle(cx, FIELD_CY - sv(19, 22), sv(2.2, 2.6), sv(38, 44))
        c.fill()

    # contador: respostas digitadas, depois acertos
    n_ok = sum(1 for k in range(N) if OK_A[k] and t >= TL.demo_grade(k))
    cy_count = lerp(FIELD[1] + FIELD[3] + sv(34, 44), GRID_BOX[1] + GRID_BOX[3] + sv(44, 40), grid_k)
    if grid_k < 1:
        text(c, f'{n_typed}/45 respostas', CL, cy_count, sv(24, 28), GREEN if n_typed == N else MUTED,
             ua * (1 - grid_k), 'semi')
    if grid_k > 0:
        w_ = number(c, str(n_ok), CL, cy_count, sv(30, 34), GREEN, ua * grid_k, 'black')
        text(c, ' de 45 acertos', CL + w_, cy_count, sv(26, 30), BODY, ua * grid_k, 'semi')

    # botão: calcular, depois baixar o relatório
    ready = eo3(seg(t, TL.DEMO_TYPE[1], TL.DEMO_TYPE[1] + .35))
    morph = eio(seg(t, TL.DEMO_LAND + .4, TL.DEMO_LAND + .9))
    press = press_k(t)
    c.save()
    c.translate(CMID, button_y(t) + BUTTON_H / 2)
    c.scale(1 - .015 * press, 1 - .05 * press)
    card(c, -CW / 2, -BUTTON_H / 2, CW, BUTTON_H, sv(8, 10), ua, fill=mix(mix(LINE, BLUE, ready), PAPER, morph),
         border=mix(mix(LINE, BLUE, ready), BLUE, morph), sh=False, lw=sv(1.6, 2))
    text(c, 'Calcular nota', 0, sv(10, 11), sv(27, 32), WHITE, ua * (1 - morph), 'bold', 'c')
    text(c, 'Baixar Relatório PDF', 0, sv(10, 11), sv(27, 32), BLUE, ua * morph, 'bold', 'c')
    c.restore()
    ripple(c, *CLICK1, t, TL.DEMO_CLICK, WHITE)
    ripple(c, *CLICK2, t, TL.DEMO_PDF_CLICK, BLUE)

    # painel de resultado
    card(c, *RCARD, sv(12, 14), ua, fill=PAPER, sh=False)
    text(c, 'Sua nota', RCARD[0] + sv(40, 36), RCARD[1] + 56, sv(24, 30), BODY, ua, 'semi')
    empty = eo3(seg(t, TL.COLA34[0] + 1.3, TL.COLA34[0] + 1.8)) * (1 - eo3(seg(t, TL.DEMO_GRADE0 - .5, TL.DEMO_GRADE0)))
    if empty > 0:
        sw, sh_ = sv((340, 118), (360, 124))
        c.set_dash([sv(7, 8)] * 2)
        card(c, SLOT[0] - sw / 2, SLOT[1] - sv(88, 92), sw, sh_, sv(12, 14), ua * empty, fill=PAPER, border=BORDER,
             sh=False)
        c.set_dash([])
    la = ua * eo3(seg(t, TL.COLA34[0] + .9, TL.COLA34[0] + 1.4))
    c.new_path()
    c.set_source_rgba(*BORDER, la)
    c.set_line_width(sv(1.4, 1.8))
    c.move_to(mini_x(200), MB)
    c.line_to(mini_x(1000), MB)
    c.stroke()
    for n in range(200, 1001, 200):
        text(c, str(n), mini_x(n), MB + sv(30, 32), sv(17, 22), MUTED, la, 'med', 'c')

    if t >= TL.DEMO_GRADE0 - .5:
        dens, nota = demo_state(t)
        with_xf(c, XF_MINI, lambda: draw_density(c, dens, ua))
        ma = eo3(seg(t, TL.DEMO_GRADE0 - .3, TL.DEMO_GRADE0 + .1)) * ua
        s = br(nota)
        wn, _ = num_w(c, s, 'black', NOTA_SIZE)
        if t < TL.COLA45[0]:
            marker(c, SLOT[0] - wn / 2, SLOT[1], wn, NOTA_SIZE, sweep(t, TL.MARK_DEMO), ma)
            land = eio(seg(t, TL.DEMO_LAND - .3, TL.DEMO_LAND))
            number(c, s, SLOT[0], SLOT[1], NOTA_SIZE, mix(MUTED, INK, land), ma, 'black', 'c')
        xm = mini_x(nota)
        ym = XF_MINI[1] + float(np.interp(ix(nota), GX, dens_ys(dens))) * XF_MINI[3]
        dashed_line(c, xm, MB, xm, ym, INK, .6 * ma, sv(1.4, 1.8), sv((4, 4), (5, 5)))
        dot(c, xm, ym, sv(4.5, 5.5), INK, ma, halo=False)


def demo_pdf(c, t):
    """O PDF salta do clique e voa até a bandeja por cima de tudo; o selo confirma."""
    if not TL.DEMO_PDF_FLY[0] <= t < TL.S5 + .3:
        return
    ua = ui_alpha(t)
    f0, f1 = TL.DEMO_PDF_FLY
    fk = TL.pdf_fly(seg(t, f0, f1))
    pop = eoback(seg(t, f0, f0 + .28), 2.2)
    px, py = bezier((CLICK2[0] - 6, CLICK2[1] - sv(52, 56)), PDF_CTRL, TRAY, fk)
    bounce = math.sin(math.pi * seg(t, TL.DEMO_PDF_LAND, TL.DEMO_PDF_LAND + .3)) * .12
    scale = lerp(sv(.9, 1.1), sv(.36, .4), fk) * pop * (1 + bounce)
    if scale > .01:
        pdf_icon(c, px, py, scale, ua, -.25 * math.sin(math.pi * fk))
    sk = eoback(seg(t, TL.DEMO_SEAL, TL.DEMO_SEAL + .45), 1.4)
    if sk > 0:
        sw, sh_ = sv((210, 34), (250, 40))
        c.save()
        c.translate(TRAY[0] - sv(130, 170), TRAY[1])
        c.scale(max(sk, 0), max(sk, 0))
        card(c, -sw / 2, -sh_ / 2, sw, sh_, sh_ / 2, ua, fill=GREEN_L, border=GREEN_L, sh=False)
        check(c, sv(-80, -96), 0, sv(14, 16), GREEN, ua, sv(2.6, 3), seg(t, TL.DEMO_SEAL + .15, TL.DEMO_SEAL + .5))
        text(c, 'Relatório PDF', sv(-60, -72), sv(8, 9), sv(20, 24), GREEN, ua, 'bold')
        c.restore()


def demo_cursor(c, t):
    """Ponteiro por cima de tudo: vai ao botão, para e clica; depois sai para longe da grade."""
    if not TL.COLA34[0] <= t < TL.S5 + .3:
        return
    pa = eo3(seg(t, TL.POINTER_IN, TL.POINTER_IN + .25)) * (1 - eio(seg(t, TL.COLA45[0], TL.COLA45[0] + .3)))
    if pa <= 0:
        return
    if t < TL.POINTER_AWAY[0]:
        x, y = reach(t, *TL.POINTER_REACH1, POINTER_HOME, CLICK1, .1)
    elif t < TL.POINTER_REACH2[0]:
        x, y = reach(t, *TL.POINTER_AWAY, CLICK1, POINTER_REST, sv(-.14, -.12))
    else:
        x, y = reach(t, *TL.POINTER_REACH2, POINTER_REST, CLICK2, sv(-.12, .1))
    draw_cursor(c, x, y, pa * (ui_alpha(t) ** .3 if V else 1), press_k(t))


def fila_demo(c, t):
    """Tapete → pontos no campo → letras digitadas → células da grade → base das barras."""
    if not TL.COLA34[0] <= t < TL.S5 + 2:
        return
    ua = ui_alpha(t) if t < TL.COLA45[0] else 1.0
    for k in range(N):
        ok = OK_A[k]
        x0, y0 = TAPETE[k]
        d0 = tapete_departure(k)
        if t < d0:
            continue
        fly = eio(seg(t, d0, d0 + 1.1))
        if fly < 1:
            x = lerp(x0, slot_x(k), fly)
            y = lerp(y0, FIELD_CY, fly) - math.sin(math.pi * fly) * sv(90, 120)
            bubble(c, x, y, lerp(DOT_D, sv(6, 7), fly), None, 1 - fly, ok, 1)
            track(k, x, y)
            continue
        tt = TL.demo_type_at(k)
        g0 = TL.DEMO_TO_GRID[0] + k * .006
        gk = eio(seg(t, g0, g0 + .5))
        gx, gy = cell_c(k)
        if gk <= 0:
            track(k, slot_x(k), FIELD_CY)
            if t < tt:
                c.new_path()
                c.set_source_rgba(*BORDER, ua)
                c.arc(slot_x(k), FIELD_CY, sv(3, 3.5), 0, 2 * math.pi)
                c.fill()
            else:
                pop = 1 + .25 * (1 - eo3(seg(t, tt, tt + .15)))
                text(c, RESP_A[k], slot_x(k), FIELD_CY + sv(9, 10) * pop, sv(25, 28) * pop, INK, ua, 'semi', 'c')
            continue
        tg = TL.demo_grade(k)
        gr = eo3(seg(t, tg, tg + .25))
        col = GREEN if ok else CORAL
        mk = bar_merge(t, k)
        if mk >= 1:
            continue        # scene_impact desenha a base e a barra
        cx = lerp(lerp(slot_x(k), gx, gk), bar_x(k), mk)
        cy = lerp(lerp(FIELD_CY, gy, gk), bar_base(k) - BW / 2, mk)
        cw = lerp(lerp(16, 50, gk), BW, mk)
        ch = lerp(lerp(sv(24, 26), sv(62, 66), gk), BW, mk)
        track(k, cx, cy)
        c.new_path()
        rrect(c, cx - cw / 2, cy - ch / 2, cw, ch, lerp(sv(6, 7), sv(5, 6), mk))
        c.set_source_rgba(*mix(PAPER, col, gr), gk)
        c.fill_preserve()
        c.set_source_rgba(*mix(LINE, col, gr), gk)
        c.set_line_width(sv(1.2, 1.4))
        c.stroke()
        bump = math.sin(math.pi * seg(t, tg, tg + .25)) * .15
        la = 1 - seg(mk, 0, .5)
        text(c, str(Q0 + k), cx, cy - sv(12, 14) * (1 - mk), sv(14, 16), mix(MUTED, WHITE, gr), gk * la, 'med', 'c')
        text(c, RESP_A[k], cx, cy + lerp(sv(9, 10), sv(22, 24), gk) * (1 - mk),
             lerp(sv(25, 28), sv(27, 30), gk) * (1 + bump), mix(INK, WHITE, gr), la * ua, 'bold' if gk > .5 else 'semi',
             'c')


# ================================================================ S5: impacto
# Site: 45 barras numa linha. Vertical: três faixas de 15, cada célula da grade vira a base da sua barra.
BW = sv(24, 34)
BH = sv(400, 210) / max(v['v'] for v in IMPACT)
LEGEND_Y = sv(SUB_Y, 500)


def bar_x(k):
    return cell_c(k)[0] if V else 162 + k * 36


def bar_base(k):
    return (812, 1112, 1412)[k // 15] if V else 860


def bar_merge(t, k):
    """Célula da grade → base da barra."""
    return eio(seg(t, TL.COLA45[0] + .15 + k * .008, TL.COLA45[0] + 1.25 + k * .008))


def bar_back(t, k):
    """Barra → fila de bolhas na cola S5→S6."""
    return eio(seg(t, TL.COLA56[0] + k * .004, TL.COLA56[0] + .5 + k * .004))


def scene_impact(c, t):
    if not TL.COLA45[0] <= t < TL.S6 + .6:
        return
    out = 1 - eio(seg(t, TL.COLA56[0], TL.COLA56[0] + .5))
    swap = eio(seg(t, TL.IMPACT_CALL + .2, TL.IMPACT_CALL + .6)) if V else 0      # a legenda dá lugar à frase

    # a nota sai do painel para o canto
    rise = eio(seg(t, TL.COLA45[0] + .1, TL.COLA45[0] + 1.0))
    s = br(NOTA_A)
    size = lerp(NOTA_SIZE, sv(64, 48), rise)
    wn, _ = num_w(c, s, 'black', size)
    right, y_top = sv((1770, 200), (XR, LEGEND_Y + 4))
    cx, cy = lerp(SLOT[0], right - wn / 2, rise), lerp(SLOT[1], y_top, rise)
    na = out * (1 - swap)
    marker(c, cx - wn / 2, cy, wn, size, 1, na * (1 - eio(seg(t, TL.IMPACT_BAR0 + .6, TL.IMPACT_BAR0 + 1.3))))
    number(c, s, cx, cy, size, INK, na, 'black', 'c')
    if V:
        text(c, 'nota', XR - wn - 14, LEGEND_Y, 24, BODY, rise * na, 'semi', 'r')
    else:
        text(c, 'Sua nota', right, y_top - size - 6, 20, BODY, rise * na, 'semi', 'r')

    hl = eo3(seg(t, TL.IMPACT_CALL, TL.IMPACT_CALL + .6)) * out
    for k in range(N):
        v = IMPACT[k]
        back = bar_back(t, k)
        if bar_merge(t, k) < 1 or back >= 1:
            continue
        gk = eoback(seg(t, TL.impact_bar(k), TL.impact_bar(k) + .7), 1.2)
        h = BW + (v['v'] * BH - BW) * max(gk, 0) * (1 - back)
        x, base = bar_x(k) - BW / 2, bar_base(k)
        track(k, x + BW / 2, base - BW / 2)
        err = not v['ok']
        col = CORAL if err else GREEN
        a = 1 if err else (.85 - .4 * hl)
        if err and k == BEST and hl > 0:
            for inf, al in ((14, .05), (8, .08), (4, .12)):
                c.new_path()
                rrect(c, x - inf, base - h - inf, BW + 2 * inf, h + inf, 6 + inf)
                c.set_source_rgba(*CORAL, al * hl)
                c.fill()
        c.new_path()
        rrect(c, x, base - h, BW, h, sv(5, 6))
        g = cairo.LinearGradient(0, base - h, 0, base)
        g.add_color_stop_rgba(0, *col, a)
        g.add_color_stop_rgba(1, *col, a * .55)
        c.set_source(g)
        c.fill()
        la = eo3(seg(t, TL.impact_bar(k), TL.impact_bar(k) + .4)) * out
        text(c, str(v['q']), x + BW / 2, base + sv(28, 30), sv(14, 19), CORAL if err else MUTED,
             la * (1 if err else .9 - .4 * hl), 'black' if err else 'med', 'c')

    la = eo3(seg(t, TL.S5 + 1.2, TL.S5 + 1.8)) * na
    sq, gap = sv(17, 22), sv(76, 70)
    c.new_path()
    c.set_source_rgba(*CORAL, la)
    c.rectangle(X0, LEGEND_Y - sv(16, 20), sq, sq)
    c.fill()
    w = text(c, 'ganharia se acertasse', X0 + sv(28, 34), LEGEND_Y, sv(23, 28), BODY, la, 'med')
    c.set_source_rgba(*GREEN, .85 * la)
    c.rectangle(X0 + w + gap, LEGEND_Y - sv(16, 20), sq, sq)
    c.fill()
    text(c, 'perderia se errasse', X0 + w + 104, LEGEND_Y, sv(23, 28), BODY, la, 'med')

    best = IMPACT[BEST]
    ck = eoback(seg(t, TL.IMPACT_CALL, TL.IMPACT_CALL + .6), 1.4)
    if ck > 0:
        x = bar_x(BEST)
        ytxt = bar_base(BEST) - best['v'] * BH - sv(30, 34)
        s = '+' + br(best['v'])
        size = sv(46, 52)
        wv, _ = num_w(c, s, 'black', size)
        marker(c, x - wv / 2, ytxt, wv, size, sweep(t, TL.MARK_IMPACT), out)
        number(c, s, x, ytxt, size * (.7 + .3 * ck), INK, clamp(ck) * out, 'black', 'c')
        if V:           # ao lado do número: acima dele ficaria sobre a faixa de cima
            text(c, f'Q{best["q"]}', x - wv / 2 - 16, ytxt, 26, CORAL, clamp(ck) * out, 'bold', 'r')
        else:
            text(c, f'Q{best["q"]}', x, ytxt - 50, 22, CORAL, clamp(ck) * out, 'bold', 'c')
    sa = eo3(seg(t, TL.IMPACT_SENTENCE, TL.IMPACT_SENTENCE + .6)) * out
    fa = eo3(seg(t, TL.IMPACT_FOOTER, TL.IMPACT_FOOTER + .6)) * out
    if V:
        text(c, f'Acertar a Q{best["q"]} somaria {br(best["v"])} pontos à nota.', X0, LEGEND_Y - 6, 32, INK, sa,
             'semi')
        text(c, 'Calculado para este conjunto de respostas; não é um peso fixo.', X0, LEGEND_Y + 38, 26, MUTED, fa)
    else:
        text(c, f'Neste conjunto de respostas, acertar a Q{best["q"]} elevaria a nota em {br(best["v"])} pontos.',
             W / 2, 972, 27, BODY, sa, 'med', 'c')
        text(c, 'Impacto calculado trocando uma resposta por vez; não é um valor fixo da questão.',
             W / 2, 1024, 21, MUTED, fa, 'reg', 'c')


# ================================================================ S6/S7: faixa, validação e fim
STRIP_P, STRIP_Y = sv((16, 1004), (18, 1360))


def end_clear(t):
    """No Reels o conteúdo sai no fim e fica o papel, para a repetição não ter corte."""
    return 1 - eio(seg(t, *TL.END_CLEAR)) if TL.END_CLEAR else 1.0


def strip_x(k):
    return W / 2 + (k - (N - 1) / 2) * STRIP_P


def end_xy(k):
    if V:
        return W / 2 + (k % 15 - 7) * 48, 744 + (k // 15) * 48
    return W / 2 + (k - (N - 1) / 2) * PITCH, 566


def fila_final(c, t):
    """As barras recolhem às bolhas; a fila desce como faixa e sobe ao centro no fim."""
    if t < TL.COLA56[0]:
        return
    clear = end_clear(t)
    for k in range(N):
        if bar_back(t, k) < 1:
            continue
        down = eio(seg(t, TL.COLA56[0] + .45 + k * .006, TL.COLA56[0] + 1.25 + k * .006))
        up = eio(seg(t, TL.COLA67[0] + .1 + k * .008, TL.COLA67[0] + 1.0 + k * .008))
        (ex, ey), bx, by = end_xy(k), bar_x(k), bar_base(k) - BW / 2
        x = lerp(lerp(bx, strip_x(k), down), ex, up)
        y = lerp(lerp(by, STRIP_Y, down), ey, up) - math.sin(math.pi * up) * sv(30, 40)
        d = lerp(lerp(BW, sv(10, 13), down), CELL, up)
        sq = (1 - down) * (1 - up)
        track(k, x, y)
        if OK_A[k]:
            bubble(c, x, y, d, RESP_A[k] if up > .5 else None, 1, True, clear, letter_a=seg(up, .5, 1), square=sq)
            continue
        c.new_path()
        rrect(c, x - d / 2, y - d / 2, d, d, lerp(d / 2, sv(5, 6), sq))
        c.set_source_rgba(*mix(CORAL, WHITE, max(down, up)), clear)
        c.fill_preserve()
        c.set_source_rgba(*mix(CORAL, BORDER, max(down, up)), clear)
        c.set_line_width(sv(1.4, 1.6))
        c.stroke()
        if up > .5:
            text(c, RESP_A[k], x, y + d * .19, d * .5, mix(INK, MUTED, .75), seg(up, .5, 1) * clear, 'bold', 'c')


def odometro_valid(c, u, label, x0, yb, size, col_spin, col_land, a):
    """Odômetro de tambores verticais com máscara de gradiente; trava da esquerda para a direita."""
    if a <= 0.003:
        return
    if u >= 1.0:
        number(c, label, x0, yb, size, col_land, a, 'black')
        return
    _, dw = num_w(c, label, 'black', size)
    slots = [
        ('d', 0, int(label[0]), int(label[0]), .58),
        ('d', 1, int(label[1]), int(label[1]), .74),
        ('s', ',', 0, 0, 0),
        ('d', 2, int(label[3]), 10 + int(label[3]), .88),
        ('d', 3, int(label[4]), 10 + int(label[4]), 1.0),
        ('s', '%', 0, 0, 0),
    ]
    h_roll = size * .92
    cx = x0
    for kind, id_, _, _, _ in slots:
        if kind == 's':
            adv = c.text_extents(id_).x_advance
            col = mix(col_spin, col_land, eio(clamp((u - .7) / .3)))
            c.set_source_rgba(*col, a)
            c.move_to(cx, yb)
            c.show_text(id_)
            cx += adv
        else:
            cx += dw

    c.push_group()
    font(c, 'black', size)
    cx = x0
    for kind, id_, fin, steps, u_end in slots:
        if kind == 's':
            cx += c.text_extents(id_).x_advance
            continue
        u_start = id_ * .02
        uk = clamp((u - u_start) / (u_end - u_start))
        s = steps * (.94 * (1 - (1 - uk) ** 2.4) + .06 * uk)
        i0 = min(int(math.floor(s)), steps)
        frac_s = eio(s - i0)
        col = mix(col_spin, col_land, eio(clamp((uk - .82) / .18)))
        for di, off in ((0, -frac_s), (1, 1.0 - frac_s)):
            if abs(off) >= .999 or i0 + di > steps:
                continue
            dig = str((fin - (steps - (i0 + di))) % 10)
            adv = c.text_extents(dig).x_advance
            sy = 1.0 - .18 * (off ** 2)
            ymid = yb - size * .36 + off * h_roll
            c.save()
            c.translate(cx + dw / 2, ymid)
            c.scale(1.0, sy)
            c.set_source_rgba(*col, a)
            c.move_to(-adv / 2, size * .36)
            c.show_text(dig)
            c.restore()
        cx += dw
    c.pop_group_to_source()
    g = cairo.LinearGradient(0, yb - size * .86, 0, yb + size * .08)
    g.add_color_stop_rgba(0.00, 0, 0, 0, 0.0)
    g.add_color_stop_rgba(0.14, 0, 0, 0, 1.0)
    g.add_color_stop_rgba(0.88, 0, 0, 0, 1.0)
    g.add_color_stop_rgba(1.00, 0, 0, 0, 0.0)
    c.mask(g)


def scene_valid(c, t):
    if not TL.COLA56[0] <= t < TL.S7 + .6:
        return
    out = 1 - eio(seg(t, TL.COLA67[0], TL.COLA67[0] + .5))
    label = pct_truncado(VAL['pct_ate_2'])
    ka = eo3(seg(t, TL.VALID_COUNT0 - .35, TL.VALID_COUNT0 + .1)) * out
    u = seg(t, TL.VALID_COUNT0, TL.VALID_LAND)
    size, yb = sv((220, 600), (252, 825))
    wn, _ = num_w(c, label, 'black', size)
    marker(c, X0 + sv(0, 6), yb, wn, size * .8, sweep(t, TL.MARK_VALID), out)
    pop = 1 + .022 * math.sin(math.pi * seg(t, TL.VALID_LAND - .04, TL.VALID_LAND + .34)) ** 2
    cx, cy = X0 + wn / 2, yb - size * .36
    c.save()
    c.translate(cx, cy)
    c.scale(pop, pop)
    odometro_valid(c, u, label, -wn / 2, size * .36, size, mix(INK, BLUE, .55), BLUE, ka)
    c.restore()

    sa = eo3(seg(t, TL.VALID_SENTENCE, TL.VALID_SENTENCE + .6)) * out
    sx, sy, ss = sv((X0 + wn + 64, 548, 42), (X0, 955, 40))
    text(c, 'das notas a até 2 pontos da oficial.', sx, sy, ss, INK, sa, 'bold')
    la = eo3(seg(t, TL.VALID_LINE, TL.VALID_LINE + .6)) * out
    notas = f'{br(VAL["notas"] / 1e6)} milhões de notas oficiais comparadas'
    provas = f'{VAL["provas"]} provas · {VAL["ano_min"]} a {VAL["ano_max"]}'
    if V:
        text(c, notas, X0, 1055, 30, MUTED, la, 'med')
        text(c, provas, X0, 1097, 30, MUTED, la, 'med')
    else:
        text(c, f'{notas} · {provas}', X0, 724, 26, MUTED, la, 'med')


def scene_end(c, t):
    if t < TL.COLA67[0]:
        return
    clear = end_clear(t)
    if V:
        words(c, 'Calculadora', W / 2, 540, 80, INK, t, TL.END_TITLE, a=clear, align='c')
        words(c, 'Nota TRI ENEM', W / 2, 632, 80, INK, t, TL.END_TITLE + TL.WORD_STAGGER, a=clear, align='c')
    else:
        words(c, 'Calculadora Nota TRI ENEM', W / 2, 420, 76, INK, t, TL.END_TITLE, align='c')
    a = eo3(seg(t, TL.END_URL, TL.END_URL + .6)) * clear
    y, size = sv((730, 64), (1010, 84))
    w = tw(c, 'notatri.com', 'black', size)
    marker(c, (W - w) / 2, y, w, size, sweep(t, TL.MARK_URL), a)
    text(c, 'notatri.com', W / 2, y + (1 - a) * 18, size, INK, a, 'black', 'c')
    a = eo3(seg(t, TL.END_REPO, TL.END_REPO + .6)) * clear
    text(c, 'github.com/HenriqueLindemann/analise-enem', W / 2, y + sv(80, 76), sv(26, 30), BLUE, a, 'med', 'c')
    text(c, 'Projeto gratuito e software livre.', W / 2, y + sv(126, 124), sv(24, 28), MUTED, a,
         'med', 'c')


# ================================================================ quadro
def frame(t, surf=None):
    surf = surf or cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    c.set_antialias(cairo.ANTIALIAS_BEST)
    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_GRAY)
    fo.set_hint_style(cairo.HINT_STYLE_NONE)
    fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    c.set_font_options(fo)
    background(c)
    for scene in (demo_window, scene_duel, scene_chart, scene_demo, fila_demo, demo_pdf, demo_cursor, scene_impact,
                  fila_final, scene_valid, scene_end, headlines):
        scene(c, t)
    if not V:               # o site abre do papel; o Reels já começa com tudo na tela
        v = 1 - eio(seg(t, 0, .5))
        if v > 0:
            c.set_source_rgba(*PAPER, v)
            c.paint()
    return surf


SAFE = (60, 240, 1020, 1500)        # área livre da interface do Reels


def reels_overlay(surf):
    """Interface aproximada do Reels por cima do quadro, para revisar o enquadramento."""
    c = cairo.Context(surf)
    c.set_source_rgba(0, 0, 0, .28)
    c.rectangle(0, 0, W, SAFE[1])
    c.rectangle(0, SAFE[3], W, H - SAFE[3])
    c.rectangle(SAFE[2] - 60, 1080, W - SAFE[2] + 60, SAFE[3] - 1080)
    c.fill()
    c.set_source_rgba(1, 1, 1, .9)
    for i in range(5):
        c.arc(1000, 1160 + i * 120, 30, 0, 2 * math.pi)
        c.fill()
    for i, wdt in enumerate((420, 760, 300)):
        rrect(c, 40, 1600 + i * 70, wdt, 34, 17)
        c.fill()
    rrect(c, 40, 140, 160, 40, 20)
    c.fill()
    return surf
