"""Vocabulário visual do filme: paleta, easing, texto, formas, bolha e marca-texto (cairo)."""
import math

import cairo

from .formatos import F
from .relogio import MARK_SWEEP, WORD_DUR, WORD_STAGGER, clamp

W, H = F.largura, F.altura


# ---------------------------------------------------------------- paleta
def hx(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


PAPER = hx('#FAF8F3')
PAPER_C = hx('#FFFEFB')
WHITE = hx('#FFFFFF')
INK = hx('#071D41')
BODY = hx('#33415C')
MUTED = hx('#6B7A90')
LINE = hx('#D5DDE8')
BORDER = hx('#9AAFCB')
BLUE = hx('#1351B4')
YELLOW = hx('#FFCD07')
GREEN = hx('#18844D')
GREEN_L = hx('#E3F5E1')
CORAL = hx('#C4574F')
BERRY = hx('#B54E77')


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


# ---------------------------------------------------------------- easing
def seg(t, a, b):
    return clamp((t - a) / (b - a))


def eo3(x):
    return 1 - (1 - x) ** 3


def eio(x):
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def eoback(x, s=1.7):
    c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2


def win(t, a, b, fin=.5, fout=.5):
    """Entra em [a, a + fin] e sai em [b - fout, b]."""
    return eo3(seg(t, a, a + fin)) * (1 - eio(seg(t, b - fout, b)))


def lerp(a, b, k):
    return a + (b - a) * k


def bezier(p0, q, p1, s):
    return tuple((1 - s) ** 2 * a + 2 * s * (1 - s) * b + s ** 2 * d for a, b, d in zip(p0, q, p1))


# ---------------------------------------------------------------- texto
FONTS = {'reg': 'Lato', 'med': 'Lato Medium', 'semi': 'Lato Semibold', 'bold': 'Lato Heavy', 'black': 'Lato Heavy'}


def font(c, f, size):
    c.select_font_face(FONTS[f], cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)


def tw(c, s, f, size, track=0):
    font(c, f, size)
    return c.text_extents(s).x_advance + track * max(len(s) - 1, 0)


def text(c, s, x, y, size, col, a=1.0, f='reg', align='l', track=0):
    if a <= 0.003 or not s:
        return 0
    w = tw(c, s, f, size, track)
    x0 = x - (w if align == 'r' else w / 2 if align == 'c' else 0)
    c.set_source_rgba(*col, a)
    if track:
        cx = x0
        for ch in s:
            c.move_to(cx, y)
            c.show_text(ch)
            cx += c.text_extents(ch).x_advance + track
    else:
        c.move_to(x0, y)
        c.show_text(s)
    return w


def num_w(c, s, f, size):
    font(c, f, size)
    dw = max(c.text_extents(d).x_advance for d in '0123456789')
    return sum(dw if ch.isdigit() else c.text_extents(ch).x_advance for ch in s), dw


def number(c, s, x, y, size, col, a=1.0, f='black', align='l'):
    """Dígitos de largura fixa: contadores não tremem."""
    if a <= 0.003:
        return 0
    w, dw = num_w(c, s, f, size)
    cx = x - (w if align == 'r' else w / 2 if align == 'c' else 0)
    c.set_source_rgba(*col, a)
    for ch in s:
        adv = c.text_extents(ch).x_advance
        if ch.isdigit():
            c.move_to(cx + (dw - adv) / 2, y)
            c.show_text(ch)
            cx += dw
        else:
            c.move_to(cx, y)
            c.show_text(ch)
            cx += adv
    return w


def br(v, dec=1):
    """Número no formato brasileiro: 1.234,5."""
    s = f'{v:,.{dec}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


def marker(c, x, y, w, size, k, a=1.0):
    """Marca-texto atrás da linha de base; k é a varredura 0..1 já suavizada.

    A frente é um degradê que em k = 1 já passou da borda: não há salto ao repousar.
    """
    if k <= 0 or a <= 0.003:
        return
    x0, x1 = x - size * .12, x + w + size * .12
    y0, hh = y - size * .52, size * .62
    feather = size * .7
    front = x0 + (x1 - x0 + feather) * k
    grad = cairo.LinearGradient(front - feather, 0, front, 0)
    grad.add_color_stop_rgba(0, *YELLOW, .9 * a)
    grad.add_color_stop_rgba(1, *YELLOW, 0)
    for grow, alpha in ((1.6, .35), (0, 1)):
        c.new_path()
        c.move_to(x0 + 6 - grow, y0 - grow)
        c.line_to(x1 + grow, y0 - 2 - grow)
        c.line_to(x1 - 4 + grow, y0 + hh + grow)
        c.line_to(x0 - grow, y0 + hh + 2 + grow)
        c.close_path()
        c.push_group()
        c.set_source(grad)
        c.fill()
        c.pop_group_to_source()
        c.paint_with_alpha(alpha)


def sweep(t, t0):
    """Varredura do marca-texto iniciada em t0."""
    return eio(seg(t, t0, t0 + MARK_SWEEP))


def words(c, s, x, y, size, col, t, t0, a=1.0, f='black', align='l', mark=None, out=None, cols=None):
    """Palavra por palavra a partir de t0; saem subindo a partir de `out`.

    mark=i marca da palavra i ao fim depois de a linha assentar; cols dá a cor de cada palavra.
    """
    ws = s.split(' ')
    font(c, f, size)
    sp = c.text_extents(' ').x_advance
    widths = [c.text_extents(w).x_advance for w in ws]
    total = sum(widths) + sp * (len(ws) - 1)
    cx0 = x - (total if align == 'r' else total / 2 if align == 'c' else 0)
    gone = 0.0
    if out is not None:
        gone = eio(seg(t, out, out + .4))
        if gone >= 1:
            return total
    if mark is not None:
        tm = t0 + (len(ws) - 1) * WORD_STAGGER + WORD_DUR + .05
        mx = cx0 + sum(widths[:mark]) + sp * mark
        marker(c, mx, y, total - (mx - cx0), size, sweep(t, tm), a * (1 - gone))
    cx = cx0
    for i, w in enumerate(ws):
        k = eo3(seg(t, t0 + i * WORD_STAGGER, t0 + i * WORD_STAGGER + WORD_DUR))
        dy = (1 - k) * size * .35 - gone * size * .3
        text(c, w, cx, y + dy, size, cols[i] if cols else col, a * k * (1 - gone), f)
        cx += widths[i] + sp
    return total


# ---------------------------------------------------------------- formas
def rrect(c, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    c.close_path()


def shadow(c, x, y, w, h, r, a=1.0, spread=18, dy=10):
    for i in range(6):
        k = i / 5
        s = spread * (1 - k)
        rrect(c, x - s, y - s + dy * (1 - k * .5), w + 2 * s, h + 2 * s, r + s)
        c.set_source_rgba(*INK, .006 * a * (1 + i))
        c.fill()


def card(c, x, y, w, h, r=14, a=1.0, fill=WHITE, border=LINE, sh=True, lw=1.2):
    if a <= 0.003:
        return
    if sh:
        shadow(c, x, y, w, h, r, a)
    rrect(c, x, y, w, h, r)
    c.set_source_rgba(*fill, a)
    c.fill_preserve()
    c.set_source_rgba(*border, a)
    c.set_line_width(lw)
    c.stroke()


def stroke_path(c, pts, col, a=1.0, width=4):
    if len(pts) < 2 or a <= 0.003:
        return
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.new_path()
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.set_source_rgba(*col, a)
    c.set_line_width(width)
    c.stroke()


def dashed_line(c, x0, y0, x1, y1, col, a, w=1.5, dash=(6, 6)):
    if a <= 0.003:
        return
    c.new_path()
    c.set_dash(list(dash))
    c.set_line_width(w)
    c.set_source_rgba(*col, a)
    c.move_to(x0, y0)
    c.line_to(x1, y1)
    c.stroke()
    c.set_dash([])


def dot(c, x, y, r, col, a=1.0, halo=True):
    if a <= 0.003:
        return
    c.new_path()
    if halo:
        c.set_source_rgba(*col, .18 * a)
        c.arc(x, y, r * 2.4, 0, 2 * math.pi)
        c.fill()
    c.set_source_rgba(*WHITE, a)
    c.arc(x, y, r + 2.5, 0, 2 * math.pi)
    c.fill()
    c.set_source_rgba(*col, a)
    c.arc(x, y, r, 0, 2 * math.pi)
    c.fill()


def arrow_head(c, x, y, size, col, a):
    c.set_source_rgba(*col, a)
    c.move_to(x + 4, y)
    c.line_to(x - size, y - size * .7)
    c.line_to(x - size, y + size * .7)
    c.close_path()
    c.fill()


def check(c, x, y, s, col, a, w=2.5, k=1.0):
    """Sinal de visto desenhado até a fração k."""
    if k <= 0 or a <= 0.003:
        return
    p = [(x - s * .5, y), (x - s * .15, y + s * .35), (x + s * .55, y - s * .4)]
    c.new_path()
    c.set_source_rgba(*col, a)
    c.set_line_width(w)
    c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(*p[0])
    if k < .4:
        kk = k / .4
        c.line_to(lerp(p[0][0], p[1][0], kk), lerp(p[0][1], p[1][1], kk))
    else:
        kk = (k - .4) / .6
        c.line_to(*p[1])
        c.line_to(lerp(p[1][0], p[2][0], kk), lerp(p[1][1], p[2][1], kk))
    c.stroke()


def bracket(c, x, y0, y1, arm, col, a, lw):
    c.new_path()
    c.set_source_rgba(*col, a)
    c.set_line_width(lw)
    c.move_to(x + arm, y0)
    c.line_to(x, y0)
    c.line_to(x, y1)
    c.line_to(x + arm, y1)
    c.stroke()


def with_xf(c, xf, fn):
    """Desenha fn sob translação (ox, oy) e escala (sx, sy)."""
    ox, oy, sx, sy = xf
    c.save()
    c.translate(ox, oy)
    c.scale(sx, sy)
    fn()
    c.restore()


# ---------------------------------------------------------------- bolha: o elemento que atravessa o filme
TRACK = None     # a verificação liga: {k: (x, y)} das bolhas de A no quadro atual

# Traços um pouco mais grossos na vertical, onde as bolhas são maiores.
_SOMBRA, _TRACO, _ANEL = (1.8, (1.5, 1.6), (5, 2.4)) if F.vertical else (1.6, (1.3, 1.5), (4.5, 2))


def track(k, x, y):
    if TRACK is not None:
        TRACK[k] = (float(x), float(y))


def bubble(c, cx, cy, d, letter, graded, ok, a=1.0, ring=0.0, letter_a=1.0, square=0.0):
    """Bolha de resposta centrada em (cx, cy), diâmetro d.

    graded 0..1 leva a bolha ao estado corrigido (acerto verde cheio, erro branco
    com a letra apagada); square 0..1 transforma o círculo em cartão.
    """
    if a <= 0.003 or d <= 0.2:
        return
    r = lerp(d / 2, d * .16, square)
    x, y = cx - d / 2, cy - d / 2
    if ok:
        fill = mix(WHITE, GREEN, graded)
        border = mix(BORDER, GREEN, graded)
        lcol = mix(INK, WHITE, graded)
    else:
        fill = WHITE
        border = mix(BORDER, LINE, graded * .35)
        lcol = mix(INK, MUTED, graded * .75)
    c.new_path()
    if d > 8:
        rrect(c, x, y + _SOMBRA, d, d, r)
        c.set_source_rgba(*INK, .06 * a)
        c.fill()
    rrect(c, x, y, d, d, r)
    c.set_source_rgba(*fill, a)
    c.fill_preserve()
    c.set_source_rgba(*border, a)
    c.set_line_width(_TRACO[0] if d > 12 else _TRACO[1])
    c.stroke()
    if ring > 0:
        c.new_path()
        c.arc(cx, cy, d / 2 + _ANEL[0], 0, 2 * math.pi)
        c.set_source_rgba(*INK, ring * a)
        c.set_line_width(_ANEL[1])
        c.stroke()
    if letter and letter_a > 0.01 and d > 10:
        text(c, letter, cx, cy + d * .19, d * .5, lcol, a * letter_a, 'bold', 'c')


# ---------------------------------------------------------------- fundo
def _paper():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(s)
    if F.vertical:
        g = cairo.RadialGradient(W * .5, H * .4, 60, W * .5, H * .5, H * .62)
    else:
        g = cairo.RadialGradient(W * .5, H * .42, 60, W * .5, H * .5, W * .78)
    g.add_color_stop_rgb(0, *PAPER_C)
    g.add_color_stop_rgb(1, *PAPER)
    c.set_source(g)
    c.paint()
    return s


_PAPER = _paper()


def background(c):
    c.set_source_surface(_PAPER, 0, 0)
    c.paint()
