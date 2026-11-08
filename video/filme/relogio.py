"""Relógio do filme, lido pelos quadros e pela trilha.

Tempos em segundos. As colas entre cenas caem em compassos da bossa (132 BPM,
1 compasso = 4 tempos = 1,818 s). `eventos()` lista tudo o que tem som.
"""
import json
import math
from dataclasses import dataclass
from itertools import accumulate

from .formatos import DADOS, F

D = json.loads(DADOS.read_text(encoding='utf-8'))
N = D['meta']['n_itens']

BPM = 132
BEAT = 60 / BPM
BAR = 4 * BEAT
FPS = F.fps


def bar(n):
    return n * BAR


def beat(n):
    return n * BEAT


DURATION = bar(70.5)
FRAMES = round(DURATION * FPS)

S1, S2, S3, S4, S5, S6, S7 = (bar(x) for x in (0, 13, 28, 39.5, 50.5, 58, 63.5))
SCENES = [(S1, 'Mesmos acertos, notas diferentes'), (S2, 'Cada questão tem sua curva'),
          (S3, 'As respostas moldam a estimativa'), (S4, 'Na calculadora'),
          (S5, 'Onde um acerto pesa mais'), (S6, 'Validação'), (S7, 'notatri.com')]


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def type_ease(x):
    """Digitação: acelera e desacelera sem a espera longa do cúbico."""
    return (1 - math.cos(math.pi * clamp(x))) / 2


def inverse_type_ease(y):
    return math.acos(1 - 2 * y) / math.pi


def ease_out3(x):
    return 1 - (1 - clamp(x)) ** 3


# ------------------------------------------------------------------ títulos e marca-texto
WORD_STAGGER, WORD_DUR = .07, .6
MARK_SWEEP = .45


@dataclass(frozen=True)
class Titulo:
    """Título dito palavra por palavra. '|' quebra a linha no formato vertical.

    marca: índice da palavra em que o marca-texto começa; azul: idem para a cor de destaque.
    """
    texto: str
    t0: float
    saida: float
    marca: int | None = None
    azul: int | None = None

    @property
    def palavras(self):
        return self.texto.replace('|', ' ').split(' ')

    @property
    def assentado(self):
        return self.t0 + (len(self.palavras) - 1) * WORD_STAGGER + WORD_DUR

    @property
    def t_marca(self):
        return self.assentado + .05


# ------------------------------------------------------------------ S1 duelo
# No Reels o título e as bolhas já estão na tela no primeiro segundo.
H1_DUEL, DUEL_APPEAR0, DUEL_SOURCE = (.05, .3, 1.0) if F.vertical else (.45, 1.45, 3.2)
H1_DUEL_OUT = 9.55
H1_SAME = 9.9
H1_SET = 18.9


def duel_appear(k, row):
    return DUEL_APPEAR0 + row * .12 + k * .024


DUEL_GRADE0 = beat(8)
DUEL_GRADE_STEP = BEAT / 6


def duel_grade(k):
    """As duas filas são corrigidas juntas, uma questão por tercina de semicolcheia."""
    return DUEL_GRADE0 + k * DUEL_GRADE_STEP


# Contador compartilhado: sobe de 500 com a mesma curva; B para em sua nota e A segue.
DUEL_LAND_B = beat(18)
DUEL_LAND_A = beat(20)
_NA, _NB = D['duel']['A']['nota'], D['duel']['B']['nota']
_UB = 1 - (1 - (_NB - 500) / (_NA - 500)) ** (1 / 3)
DUEL_COUNT0 = DUEL_LAND_A - (DUEL_LAND_A - DUEL_LAND_B) / (1 - _UB)
DUEL_DIFF = DUEL_LAND_A + .45
DUEL_CENTENA = DUEL_LAND_A + .15        # traço sob o dígito da centena


def duel_counter(t, row):
    v = 500 + (_NA - 500) * ease_out3((t - DUEL_COUNT0) / (DUEL_LAND_A - DUEL_COUNT0))
    return min(v, _NA if row == 0 else _NB)


DUEL_SORT0 = bar(7)
DUEL_SORT_DUR = 1.15


def duel_sort(rank, row):
    return DUEL_SORT0 + rank * .018 + row * .12


DUEL_AXIS = DUEL_SORT0 + 1.3
DUEL_NOTE_A = 15.2
DUEL_NOTE_B = 16.8

# Cola S1→S2: B sai por baixo; a fila ordenada de A desce até o eixo das curvas.
COLA12_OUT = S2 - 1.9
COLA12_MOVE = (S2 - 1.65, S2 - .05)


def cola12_move(rank):
    return COLA12_MOVE[0] + rank * .012


COLA12_AXIS = (S2 - .35, S2 + .75)

# ------------------------------------------------------------------ S2 curvas
H1_CURVES = S2 + .2
CURVE_LIFT = .36
CURVE_DRAW = beat(3)
CURVE_BIRTH = [bar(13.5), bar(14), bar(14.5)]


def curve_draw(j):
    start = CURVE_BIRTH[j] + CURVE_LIFT
    return start, start + CURVE_DRAW


ICC_PHASES = (bar(16.5), bar(20), bar(24))     # beats a, b, c
ICC_MOVE = (ICC_PHASES[1] + 2.4, ICC_PHASES[1] + 3.8)
ICC_FLOOR = (ICC_PHASES[2] + .6, ICC_PHASES[2] + 1.9)

# ------------------------------------------------------------------ S3 estimativa
COLA23 = (S3 - .55, S3 + .6)
H1_EAP = S3 + .15
EAP_PRIOR = (S3 + .7, S3 + 1.7)
EAP_STEP0 = bar(29.5)
ORDEM = D['ordem_b']
OK_A = [bool(v) for v in D['duel']['A']['ok']]
FIRST_ERROR = next(j for j, k in enumerate(ORDEM) if not OK_A[k])
SLOW_STEPS = set(range(4)) | {FIRST_ERROR}


def eap_step_dur(j):
    return beat(2) if j in SLOW_STEPS else beat(.5)


EAP_STEPS = list(accumulate((eap_step_dur(j) for j in range(N - 1)), initial=EAP_STEP0))
EAP_END = EAP_STEPS[-1] + eap_step_dur(N - 1)
EAP_LAND = bar(37.5)


def eap_step(j):
    return EAP_STEPS[j]


def eap_progress(t):
    """Respostas já incorporadas (fracionário) em S3."""
    if t < EAP_STEPS[0]:
        return 0.0
    for j in range(N):
        end = EAP_STEPS[j] + eap_step_dur(j)
        if t < end:
            return j + (t - EAP_STEPS[j]) / eap_step_dur(j)
    return float(N)


# ------------------------------------------------------------------ S4 plataforma
COLA34 = (S4 - .5, S4 + 1.3)
DEMO_TYPE = (bar(40.5), bar(43.5))
DEMO_CLICK = bar(44)
DEMO_TO_GRID = (DEMO_CLICK + .12, DEMO_CLICK + .85)
DEMO_GRADE0 = bar(44.5)
DEMO_GRADE_STEP = BEAT / 6
DEMO_LAND = bar(46.5)
DEMO_PDF_CLICK = bar(48)
DEMO_PDF_FLY = (DEMO_PDF_CLICK + .15, bar(48.5))
DEMO_PDF_LAND = bar(48.5)
DEMO_SEAL = bar(49)

# Ponteiro: chega ao botão e para antes de cada clique; depois do 1º sai da frente da grade.
POINTER_IN = DEMO_CLICK - .85
POINTER_REACH1 = (DEMO_CLICK - .68, DEMO_CLICK - .12)
POINTER_AWAY = (DEMO_CLICK + .14, DEMO_CLICK + .72)
POINTER_REACH2 = (DEMO_PDF_CLICK - .74, DEMO_PDF_CLICK - .14)


def pdf_fly(x):
    """Avanço do PDF entre o clique e a bandeja; o som do voo segue a mesma curva."""
    return smooth(x)


def demo_typed_count(t):
    return int(N * type_ease((t - DEMO_TYPE[0]) / (DEMO_TYPE[1] - DEMO_TYPE[0])) + 1e-9)


def demo_type_at(k):
    """Instante em que a letra k aparece (inversa do easing da digitação)."""
    return DEMO_TYPE[0] + (DEMO_TYPE[1] - DEMO_TYPE[0]) * inverse_type_ease((k + 1) / N)


def demo_grade(k):
    return DEMO_GRADE0 + k * DEMO_GRADE_STEP


def demo_progress(t):
    """Respostas coloridas na grade da plataforma (fracionário)."""
    return max(0.0, min(float(N), (t - DEMO_GRADE0) / DEMO_GRADE_STEP + .5))


# ------------------------------------------------------------------ S5 impacto
COLA45 = (S5 - 1.1, S5 + .2)
IMPACT_BAR0 = S5 + beat(1)
IMPACT_BAR_STEP = BEAT / 8


def impact_bar(k):
    return IMPACT_BAR0 + k * IMPACT_BAR_STEP


IMPACT_CALL = bar(53)
IMPACT_SENTENCE = IMPACT_CALL + 1.0
IMPACT_FOOTER = IMPACT_CALL + 1.9

# ------------------------------------------------------------------ S6 validação
COLA56 = (S6 - .9, S6 + .4)
VALID_COUNT0 = S6 + .55
VALID_LAND = bar(59.5)
VALID_PCT = 19                                      # passos do tambor de centésimos (0 → 9 → 9) até VALID_LAND


def valid_tick(i):
    """Clique i (1..VALID_PCT) da catraca do odômetro, desacelerando até pousar em VALID_LAND."""
    x = i / VALID_PCT
    return VALID_COUNT0 + (VALID_LAND - VALID_COUNT0) * (.36 * x + .64 * x ** 2.1)


VALID_SENTENCE = VALID_LAND + .3
VALID_LINE = VALID_LAND + 1.4

# ------------------------------------------------------------------ S7 fim
COLA67 = (S7 - .7, S7 + .6)
END_TITLE = S7 + .1
END_URL = S7 + 1.3
END_REPO = S7 + 1.9
END_TONIC = bar(67.5)
END_CLEAR = (DURATION - .6, DURATION) if F.vertical else None     # o Reels repete sem corte

# ------------------------------------------------------------------ roteiro dos títulos
TITULOS = [
    Titulo('Mesma prova.|34 acertos cada.', H1_DUEL, H1_DUEL_OUT, marca=2),
    Titulo('Mesmos acertos.|Notas diferentes.', H1_SAME, H1_SET - .45, azul=2),
    Titulo('A nota depende do|conjunto das respostas.', H1_SET, COLA12_OUT, marca=4),
    Titulo('Cada questão tem|sua própria curva.', H1_CURVES, COLA23[0], marca=4),
    Titulo('Suas respostas|moldam a estimativa.', H1_EAP, COLA34[0], marca=2),
    Titulo('Onde um acerto faria|mais diferença?', S5 - .35, COLA56[0]),
    Titulo('Quão perto|da nota oficial?', S6 + .1, COLA67[0]),
]

# Varreduras do marca-texto fora dos títulos.
MARK_EAP = EAP_LAND + .05
MARK_DEMO = DEMO_LAND + .05
MARK_IMPACT = IMPACT_CALL + .4
MARK_VALID = VALID_LAND + .1
MARK_URL = END_URL + .6


def marcas():
    """Início de cada varredura do marca-texto: (instante, constante)."""
    out = [(h.t_marca, f'TITULOS[{i}].t_marca') for i, h in enumerate(TITULOS) if h.marca is not None]
    out += [(DUEL_CENTENA, 'DUEL_CENTENA'), (MARK_EAP, 'MARK_EAP'), (MARK_DEMO, 'MARK_DEMO'),
            (MARK_IMPACT, 'MARK_IMPACT'), (MARK_VALID, 'MARK_VALID'), (MARK_URL, 'MARK_URL')]
    return out


# ------------------------------------------------------------------ mapa de eventos
def eventos():
    """Todo evento visual que tem som: {time, event, constant, ...}."""
    ev = []

    def add(t, event, constant, **extra):
        ev.append({'time': round(t, 4), 'event': event, 'constant': constant, **extra})

    for k in range(N):
        for row, nome in ((0, 'A'), (1, 'B')):
            ok = bool(D['duel'][nome]['ok'][k])
            add(duel_grade(k), 'duel.grade.' + ('ok' if ok else 'erro'), f'duel_grade({k})', row=row, k=k)
    add(DUEL_LAND_B, 'duel.land', 'DUEL_LAND_B', row=1)
    add(DUEL_LAND_A, 'duel.land', 'DUEL_LAND_A', row=0)
    add(DUEL_SORT0, 'duel.sort', 'DUEL_SORT0', dur=duel_sort(N - 1, 1) + DUEL_SORT_DUR - DUEL_SORT0)
    for nome, t in (('s1s2', S2), ('s2s3', S3), ('s3s4', S4), ('s4s5', S5), ('s5s6', S6), ('s6s7', S7)):
        add(t, 'cola.' + nome, 'S' + nome[-1])
    for j in range(3):
        a, b = curve_draw(j)
        add(a, 'curve.start', f'curve_draw({j})[0]', j=j, dur=b - a)
        add(b, 'curve.end', f'curve_draw({j})[1]', j=j)
    for i, t in enumerate(ICC_PHASES):
        add(t, 'icc.beat', f'ICC_PHASES[{i}]', i=i)
    add(ICC_MOVE[0], 'icc.move', 'ICC_MOVE[0]', dur=ICC_MOVE[1] - ICC_MOVE[0])
    add(ICC_FLOOR[0], 'icc.floor', 'ICC_FLOOR[0]', dur=ICC_FLOOR[1] - ICC_FLOOR[0])
    add(EAP_PRIOR[0], 'eap.pad', 'EAP_PRIOR[0]', dur=EAP_LAND - EAP_PRIOR[0])
    for j, k in enumerate(ORDEM):
        add(eap_step(j), 'eap.step.' + ('ok' if OK_A[k] else 'erro'), f'eap_step({j})', j=j, k=k)
    add(EAP_LAND, 'eap.land', 'EAP_LAND')
    for k in range(N):
        add(demo_type_at(k), 'demo.type', f'demo_type_at({k})', k=k)
    add(DEMO_CLICK, 'demo.click', 'DEMO_CLICK')
    for k in range(N):
        add(demo_grade(k), 'demo.grade.' + ('ok' if OK_A[k] else 'erro'), f'demo_grade({k})', k=k)
    add(DEMO_LAND, 'demo.land', 'DEMO_LAND')
    add(DEMO_PDF_CLICK, 'demo.pdf_click', 'DEMO_PDF_CLICK')
    add(DEMO_PDF_FLY[0], 'demo.pdf_fly', 'DEMO_PDF_FLY[0]', dur=DEMO_PDF_FLY[1] - DEMO_PDF_FLY[0])
    add(DEMO_PDF_LAND, 'demo.pdf_land', 'DEMO_PDF_LAND')
    add(DEMO_SEAL, 'demo.seal', 'DEMO_SEAL')
    for k in range(N):
        add(impact_bar(k), 'impact.bar', f'impact_bar({k})', k=k)
    add(IMPACT_CALL, 'impact.call', 'IMPACT_CALL')
    for i in range(1, VALID_PCT + 1):
        add(valid_tick(i), 'valid.tick', f'valid_tick({i})', i=i)
    add(VALID_LAND, 'valid.land', 'VALID_LAND')
    for t, constant in marcas():
        add(t, 'marca', constant, dur=MARK_SWEEP)
    add(END_TONIC, 'end.tonic', 'END_TONIC')
    return sorted(ev, key=lambda e: (e['time'], e['event']))
