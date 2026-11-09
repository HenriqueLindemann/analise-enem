# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Trilha original em clima de bossa nova + foley real, no relógio do filme.

132 BPM (compasso de 2/4 em dobro), fá maior. Camadas entram nas colas:
S1 violão + aro, S2 baixo, S3 pad que cresce com o sino, S4 Rhodes e escovinha,
S5 vibrafone, S6 caxixi e catraca, S7 flauta. Cada evento de `relogio.eventos()`
tem um som e vira uma linha de `audio-cues.json`.
"""
import json
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

from . import relogio as TL
from .formatos import F, SONS

SR = 48000
DUR = TL.DURATION
BEAT, BAR = TL.BEAT, TL.BAR
S16 = BEAT / 4


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(sig, cutoff, kind='lowpass', order=2):
    return sosfilt(butter(order, cutoff, btype=kind, fs=SR, output='sos'), sig)


def env_ar(n, attack, release):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(attack, 1e-4))
    tail = np.minimum(1, (n / SR - t) / max(release, 1e-4))
    return e * np.clip(tail, 0, 1)


@lru_cache(maxsize=None)
def foley(nome, fatias=1):
    """Carrega um banco de foley mono 48 kHz de `video/sons/`."""
    sr, w = wavfile.read(SONS / f'{nome}.wav')
    assert sr == SR
    return np.split(w.astype(np.float64) / 32768.0, fatias)


# ================================================================ instrumentos
@lru_cache(maxsize=None)
def nylon(m, dur=1.6, bright=.5):
    """Karplus–Strong com atraso fracionário; corda de náilon, ataque macio."""
    f = hz(m)
    period = SR / f - .5
    p = int(period)
    w = period - p
    n = int(dur * SR)
    y = np.zeros(n + p + 2)
    burst = np.random.default_rng(100 + m).uniform(-1, 1, p + 2)
    y[:p + 2] = filt(burst, 1800 + 3000 * bright)
    loss = .996 if m < 60 else .993
    i = p + 2
    while i < len(y):
        j = min(i + p, len(y))
        y[i:j] = loss * ((1 - w) * y[i - p:j - p] + w * y[i - p - 1:j - p - 1])
        i = j
    y = filt(y[p + 2:], 2600 + 2400 * bright)
    return y * env_ar(n, .002, .08) / (np.abs(y).max() + 1e-9)


def guitar(m, dur=.9, bright=.45):
    s = nylon(m, 1.6, bright)[:int(dur * SR)].copy()
    return s * env_ar(len(s), .001, min(.12, dur / 3))


def bass(m, dur=.7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = (np.sin(2 * np.pi * f * t)
         + .35 * np.sin(4 * np.pi * f * t) * np.exp(-t / .12)
         + .12 * np.sin(6 * np.pi * f * t) * np.exp(-t / .05))
    return s * np.exp(-t / .55) * env_ar(n, .006, .09)


@lru_cache(maxsize=None)
def rhodes(m, dur=2.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    index = 1.6 * np.exp(-t / .22) + .25
    s = np.sin(2 * np.pi * f * t + index * np.sin(2 * np.pi * f * t))
    s += .07 * np.sin(2 * np.pi * 7 * f * t) * np.exp(-t / .04)
    return s * np.exp(-t / 1.3) * env_ar(n, .003, .2)


@lru_cache(maxsize=None)
def vibe(m, dur=2.2, trem=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = (np.sin(2 * np.pi * f * t)
         + .22 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / .35)
         + .07 * np.sin(2 * np.pi * 9.9 * f * t) * np.exp(-t / .07))
    if trem:
        s *= 1 + .22 * np.sin(2 * np.pi * 5.4 * t)
    return s * np.exp(-t / 1.25) * env_ar(n, .002, .25)


@lru_cache(maxsize=None)
def tick_ok(m):
    n = int(.34 * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 3.9 * f * t) * np.exp(-t / .03)
    return s * np.exp(-t / .09) * env_ar(n, .0015, .05)


@lru_cache(maxsize=None)
def tick_neutral():
    """Erro: um toque de madeira abafado, sem altura definida e sem peso."""
    n = int(.12 * SR)
    t = np.arange(n) / SR
    s = filt(np.random.default_rng(5).normal(0, 1, n), [500, 1500], 'bandpass') * .6
    s += .5 * np.sin(2 * np.pi * 300 * t)
    return s * np.exp(-t / .022) * env_ar(n, .001, .02)


@lru_cache(maxsize=None)
def rim():
    n = int(.09 * SR)
    t = np.arange(n) / SR
    s = filt(np.random.default_rng(7).normal(0, 1, n), [1400, 5200], 'bandpass') * np.exp(-t / .006)
    s += .6 * np.sin(2 * np.pi * 1750 * t) * np.exp(-t / .012) + .5 * np.sin(2 * np.pi * 480 * t) * np.exp(-t / .02)
    return s * env_ar(n, .0005, .01)


@lru_cache(maxsize=None)
def brush(dur=.16, seed=0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = filt(np.random.default_rng(11 + seed).normal(0, 1, n), [2500, 9000], 'bandpass')
    return s * np.sin(np.pi * t / dur) ** 2 * np.exp(-t / .06)


@lru_cache(maxsize=None)
def kick():
    n = int(.35 * SR)
    t = np.arange(n) / SR
    phase = 2 * np.pi * np.cumsum(55 + 40 * np.exp(-t / .03)) / SR
    return np.sin(phase) * np.exp(-t / .12) * env_ar(n, .004, .05)


@lru_cache(maxsize=None)
def shaker(seed=0):
    n = int(.07 * SR)
    t = np.arange(n) / SR
    s = filt(np.random.default_rng(31 + seed).normal(0, 1, n), [4000, 11000], 'bandpass')
    return s * np.exp(-t / .018) * env_ar(n, .003, .01)


def flute(m, dur, rng, vib=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m) * (1 + (.003 * np.sin(2 * np.pi * 5 * t) * np.minimum(1, t / .4) if vib else 0))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + .18 * np.sin(2 * ph) + .05 * np.sin(3 * ph)
    s += .06 * filt(rng.normal(0, 1, n), [900, 4000], 'bandpass')
    return s * env_ar(n, .08, .18)


def pad_chord(notes, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for j, m in enumerate(notes):
        for det in (-.07, .07):
            f = hz(m) * 2 ** (det / 12)
            for h, a in ((1, 1), (2, .3), (3, .12)):
                s += a * np.sin(2 * np.pi * f * h * t + j + det * 10)
    return filt(s / (len(notes) * 3), 1800) * env_ar(n, .6, .8)


def glide(m0, m1, dur, curve=None):
    """Seno deslizando de m0 a m1; curve(p) dá o avanço 0..1."""
    n = int(dur * SR)
    p = np.arange(n) / n
    k = np.vectorize(curve)(p) if curve else p
    f = hz(m0) * 2 ** ((m1 - m0) * k / 12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + .2 * np.sin(2 * ph)) * env_ar(n, .05, .15)


def bell(m, dur=2.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t + 2.2 * np.exp(-t / .5) * np.sin(2 * np.pi * 3.5 * f * t))
    return s * np.exp(-t / .9) * env_ar(n, .002, .3)


# ================================================================ harmonia
CH = {
    'Fmaj7': (41, [53, 57, 60, 64]), 'Fmaj9': (41, [57, 60, 64, 67]),
    'G7(9)': (43, [53, 57, 59, 62]), 'Gm9': (43, [53, 57, 58, 62]),
    'C13': (36, [52, 57, 58, 62]), 'C9sus': (36, [53, 55, 58, 62]),
    'Dm9': (38, [53, 57, 60, 64]), 'Bbmaj9': (46, [57, 60, 62, 65]),
    'Am7': (45, [55, 60, 64, 67]),
}
PROG = [(0, 'Fmaj7'), (1, 'G7(9)'), (2, 'Gm9'), (3, 'C13'), (4, 'C9sus'), (5, 'Fmaj7'), (6, 'G7(9)'),
        (7, 'Gm9'), (8, 'C13'), (9, 'Fmaj7'), (10, 'G7(9)'), (11, 'Gm9'), (12, 'C13')]
for _b in (13, 17, 21):
    PROG += [(_b, 'Fmaj7'), (_b + 1, 'G7(9)'), (_b + 2, 'Gm9'), (_b + 3, 'C13')]
PROG += [(25, 'Dm9'), (26, 'Gm9'), (27, 'C13'),
         (28, 'Dm9'), (29, 'Bbmaj9'), (30, 'Gm9'), (31, 'C13'), (32, 'Dm9'), (33, 'Bbmaj9'),
         (34, 'Gm9'), (35, 'Am7'), (36, 'Gm9'), (37, 'C13'), (37.5, 'Fmaj9'),
         (39.5, 'Fmaj7'), (40.5, 'G7(9)'), (41.5, 'Gm9'), (42.5, 'C13'), (43.5, 'Fmaj7'), (44.5, 'G7(9)'),
         (45.5, 'Gm9'), (46, 'C13'), (46.5, 'Fmaj7'), (47.5, 'G7(9)'), (48.5, 'Gm9'), (49, 'C13'), (49.5, 'Fmaj7'),
         (50.5, 'Bbmaj9'), (51.5, 'Am7'), (52.5, 'Dm9'), (53.5, 'Gm9'), (54.5, 'C13'), (55.5, 'Fmaj7'),
         (56.5, 'Gm9'), (57.5, 'C13'),
         (58, 'Dm9'), (59, 'C9sus'), (59.5, 'Fmaj7'), (60.5, 'Bbmaj9'), (61.5, 'Gm9'), (62.5, 'C13'),
         (63.5, 'Fmaj7'), (64.5, 'G7(9)'), (65.5, 'Gm9'), (66.5, 'C13'), (67.5, 'Fmaj9')]
PROG.sort()
SEGS = [(TL.bar(b), TL.bar(PROG[i + 1][0]) if i + 1 < len(PROG) else DUR, name) for i, (b, name) in enumerate(PROG)]


def chord_at(t):
    for a, b, name in SEGS:
        if a <= t < b:
            return CH[name]
    return CH['Fmaj9']


def tones_high(t, octave=24):
    return [m + octave for m in chord_at(t)[1]]


# ================================================================ groove
GROOVE_END = TL.END_TONIC
CLAVE_A, CLAVE_B = (0, 3, 6), (2, 5)
RIM = (0, 3, 6, 10, 12)
SWING = .012


def level(t, marks, default=0.0):
    xs, ys = zip(*marks)
    return float(np.interp(t, xs, ys, left=default, right=ys[-1]))


def step(*marks):
    out = []
    for t, v in marks:
        if out:
            out.append((t - 1e-3, out[-1][1]))
        out.append((t, v))
    return out


GTR_MODE = [(0, 'acorde'), (TL.DUEL_LAND_A, 'polegar'), (TL.DUEL_SORT0, 'bossa')]
GTR_LVL = [(0, .15), (TL.S2, .17), (TL.S4, .2), (TL.VALID_LAND, .21), (GROOVE_END, .2)]
BASS_LVL = step((0, 0), (TL.S2, .07), (TL.S4, .09), (TL.VALID_LAND, .1))
RIM_LVL = step((0, 0), (TL.S3, .06), (TL.S4, .08), (TL.VALID_LAND, .09))
BRUSH_LVL = step((0, 0), (TL.S4, .7), (TL.DEMO_LAND, 1), (TL.S6, 0), (TL.VALID_LAND, 1.1))
KICK_LVL = step((0, 0), (TL.DEMO_LAND, 1), (TL.S6, 0), (TL.VALID_LAND, 1.1))


def gtr_mode(t):
    return [m for t0, m in GTR_MODE if t >= t0 - 1e-6][-1]


def sintetizar(raw_wav, cues_json):
    ns = int(round(TL.FRAMES / TL.FPS * SR))
    mix = np.zeros((ns, 2), dtype=np.float64)
    send = np.zeros((ns, 2), dtype=np.float64)
    cues = []
    rng = np.random.default_rng(2026)
    marca_idx = [0]

    def add(sig, t, gain=1.0, pan=0.0, rev=.15):
        i = int(round(t * SR))
        if i >= ns or gain == 0:
            return
        sig = np.asarray(sig, dtype=np.float64)
        if i < 0:
            sig, i = sig[-i:], 0
        sig = sig[:ns - i] * gain
        left, right = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        mix[i:i + len(sig), 0] += sig * left
        mix[i:i + len(sig), 1] += sig * right
        if rev:
            send[i:i + len(sig), 0] += sig * left * rev
            send[i:i + len(sig), 1] += sig * right * rev

    # groove: violão, baixo, aro, escovinha e bumbo
    for a, b, name in SEGS:
        if a >= GROOVE_END:
            break
        root, voicing = CH[name]
        fifth = root + 7 if root + 7 <= 48 else root - 5
        n2 = int(round((min(b, GROOVE_END) - a) / (BAR / 2)))
        for half in range(n2):
            t0 = a + half * BAR / 2
            g = level(t0, GTR_LVL)
            mode = gtr_mode(t0)
            if mode == 'bossa':
                for s16 in (CLAVE_A if half % 2 == 0 else CLAVE_B):
                    t = t0 + s16 * S16 + (SWING if s16 % 2 else 0) + rng.normal(0, .003)
                    vel = g * (1.0 if s16 == 0 else .82) * rng.uniform(.9, 1.05)
                    for j, m in enumerate(voicing):
                        add(guitar(m, .42 if s16 else .55), t + j * .007, vel * .42, -.25 + .12 * j, .2)
            elif half == 0:
                for j, m in enumerate(voicing):
                    add(guitar(m, 1.5, .35), t0 + j * .03, g * .4, -.25 + .12 * j, .3)
            if mode != 'acorde':
                for q, m in ((0, root), (2, fifth)):
                    add(guitar(m, .5, .3), t0 + q * S16 * 2, g * .55, -.1, .1)
            bl = level(t0, BASS_LVL)
            if bl:
                for q, m in ((0, root), (4, fifth)):
                    add(bass(m, .62), t0 + q * S16, bl, 0, .05)

    t = 0.0
    while t < GROOVE_END - .01:
        for s in range(16):
            ts = t + s * S16 + (SWING if s % 2 else 0)
            if ts >= GROOVE_END:
                break
            r, br_, kk = level(ts, RIM_LVL), level(ts, BRUSH_LVL), level(ts, KICK_LVL)
            if r and s in RIM:
                add(rim(), ts, r * rng.uniform(.85, 1), .2, .12)
            if br_:
                acc = 1.0 if s % 4 == 2 else .55 if s % 2 == 0 else .35
                add(brush(.16, s % 3), ts, .05 * br_ * acc, .35, .1)
            if kk and s in (0, 7, 8, 15):
                add(kick(), ts, .2 * kk * (1 if s in (0, 8) else .6), 0, 0)
        t += BAR

    # Rhodes a partir de S4
    for a, b, name in SEGS:
        if a < TL.S4 or a >= GROOVE_END:
            continue
        _, voicing = CH[name]
        g = .045 if a < TL.S6 else .03 if a < TL.VALID_LAND else .055
        for j, m in enumerate(voicing):
            add(rhodes(m + 12, min(2.4, b - a + .3)), a + j * .012, g, -.3 + .2 * j, .25)
        if b - a >= BAR * .99:
            for j, m in enumerate(voicing[1:]):
                add(rhodes(m + 12, 1.0), a + 6 * S16 + SWING, g * .55, .3 - .2 * j, .25)

    # Pad a partir de S3: ganho acompanha a altura do pico do sino
    peaks = np.array([max(s['post']) for s in TL.D['posterior']['steps']])

    def peak_at(tp):
        p = TL.eap_progress(tp)
        if p <= 0:
            return peaks[0] * TL.smooth((tp - TL.EAP_PRIOR[0]) / (TL.EAP_PRIOR[1] - TL.EAP_PRIOR[0]))
        j = min(int(p), len(peaks) - 2)
        return peaks[j] + (peaks[j + 1] - peaks[j]) * min(1.0, p - j)

    for a, b, name in SEGS:
        if b <= TL.S3 or a >= DUR:
            continue
        _, voicing = CH[name]
        s = pad_chord([m - 12 for m in voicing] + [voicing[-1]], b - a + .8)
        tp = a + np.arange(len(s)) / SR
        if a < TL.S4 + BAR:
            gain = np.array([.03 + .2 * peak_at(x) / peaks.max() for x in tp[::480]])
            gain = np.interp(np.arange(len(s)), np.arange(0, len(s), 480), gain)
            gain *= np.clip((tp - TL.S3) / .6, 0, 1) * np.interp(tp, [TL.S4, TL.S4 + 2.5], [1, .45])
        else:
            gain = np.full(len(s), .06 if a < TL.S7 else .075)
        add(s * gain, a, 1, 0, .35)

    # Eventos visuais (música + foley real)
    marcas = foley('marca', 4)
    teclas = foley('teclas', 8)
    catraca = foley('catraca', 6)
    som_clique = foley('clique')[0]
    som_folha = foley('folha')[0]
    som_pouso = foley('pouso')[0]
    som_carimbo = foley('carimbo')[0]

    for ev in TL.eventos():
        kind, t = ev['event'], ev['time']
        hi = tones_high(t)
        if kind.startswith('duel.grade'):
            k, row = ev['k'], ev['row']
            pan = -.3 if row == 0 else .3
            if kind.endswith('ok'):
                add(tick_ok(hi[k % 4] + (0 if row == 0 else -12)), t, .085, pan, .2)
            else:
                add(tick_neutral(), t, .032, pan, .1)
        elif kind == 'duel.land':
            if ev['row'] == 1:
                add(vibe(77 - 12), t, .12, .25, .3)
            else:
                for j, m in enumerate((77, 81, 84, 88)):
                    add(vibe(m), t + j * .03, .09, -.2 + .13 * j, .35)
                add(bass(41, 1.2), t, .12, 0, .05)
        elif kind == 'duel.sort':
            steps = int(ev['dur'] / (S16 * 2))
            for i in range(steps):
                tt = t + i * S16 * 2
                m = sorted(tones_high(tt, 12) + tones_high(tt, 24))[i % 8]
                add(guitar(m, .6, .7), tt, .12, -.4 + .8 * i / max(1, steps - 1), .3)
        elif kind.startswith('cola.'):
            voice = kind.split('.')[1]
            if voice == 's1s2':
                add(bass(chord_at(t)[0], 1.0), t, .12, 0, .05)
            elif voice == 's2s3':
                add(pad_chord([m - 12 for m in chord_at(t)[1]], 1.8), t, .05, 0, .3)
            elif voice == 's3s4':
                for j, m in enumerate(chord_at(t)[1]):
                    add(rhodes(m + 12), t + j * .012, .06, -.3 + .2 * j, .25)
                add(brush(.2, 1), t, .08, .3, .1)
            elif voice == 's4s5':
                add(vibe(hi[0]), t, .07, -.2, .35)
            elif voice == 's5s6':
                for i in range(16 * 3):
                    ts = t + i * S16
                    if ts < TL.S7:
                        add(shaker(i % 3), ts + (SWING if i % 2 else 0), .045 * (1 if i % 4 == 0 else .6), .45, .1)
            elif voice == 's6s7':
                melody = [(0, 72, 2), (2, 69, 1), (3, 72, 1), (4, 71, 2), (6, 69, 1), (7, 67, 1),
                          (8, 70, 2), (10, 69, 1), (11, 65, 1), (12, 64, 1), (13, 67, 1), (14, 70, 1.5),
                          (15.5, 76, .5)]
                for b0, m, d in melody:
                    add(flute(m, d * BEAT + .08, rng), t + b0 * BEAT, .1, .1, .35)
        elif kind == 'curve.start':
            d = ev['dur']
            m0 = hi[0] - 12
            s = glide(m0, m0 + 12, d, TL.smooth)
            p = np.arange(len(s)) / len(s)
            speed = np.gradient(np.array([TL.smooth(x) for x in p[::100]]))
            s *= .35 + np.interp(p, p[::100], speed / speed.max())
            add(filt(s, 2500), t, .05, -.3 + .3 * ev['j'], .4)
        elif kind == 'curve.end':
            add(vibe(hi[1 + ev['j'] % 3]), t, .07, -.3 + .3 * ev['j'], .35)
        elif kind == 'icc.beat':
            for j, m in enumerate((hi[1] - 12, hi[3] - 12)):
                add(vibe(m), t + j * .06, .07, -.15 + .3 * j, .35)
        elif kind == 'icc.move':
            add(filt(glide(hi[0] - 12, hi[2], ev['dur'], TL.smooth), 3000), t, .035, 0, .4)
        elif kind == 'icc.floor':
            n = int(ev['dur'] * SR)
            s = filt(rng.normal(0, 1, n), [1200, 5000], 'bandpass') * np.sin(np.pi * np.arange(n) / n) ** 2
            add(s, t, .02, -.4, .3)
        elif kind == 'eap.pad':
            pass
        elif kind.startswith('eap.step'):
            j = ev['j']
            slow = j in TL.SLOW_STEPS
            if kind.endswith('ok'):
                add(tick_ok(hi[j % 4]), t, .16 if slow else .11, -.3 + .6 * j / 44, .25)
                if slow:
                    add(vibe(hi[j % 4] - 12), t, .05, 0, .3)
            else:
                add(tick_neutral(), t, .07 if slow else .05, -.3 + .6 * j / 44, .12)
                if slow:
                    add(vibe(chord_at(t)[1][0] + 12), t, .045, 0, .3)
        elif kind == 'eap.land':
            for j, m in enumerate((65, 72, 77, 81)):
                add(vibe(m, 3.0), t + j * .025, .08, -.3 + .2 * j, .4)
            add(bass(41, 1.5), t, .12, 0, .05)
        elif kind == 'demo.type':
            k = ev['k']
            pan = -.2 + .4 * k / 44
            add(teclas[(k * 3) % len(teclas)], t, .065, pan, .06)
            add(tick_ok(tones_high(t, 12)[k % 4]), t, .028, pan, .12)
        elif kind in ('demo.click', 'demo.pdf_click'):
            add(som_clique, t, .16, .1, .06)
        elif kind.startswith('demo.grade'):
            k = ev['k']
            if kind.endswith('ok'):
                add(tick_ok(hi[k % 4]), t, .1, -.35 + .7 * (k % 15) / 14, .2)
            else:
                add(tick_neutral(), t, .045, -.35 + .7 * (k % 15) / 14, .1)
        elif kind == 'demo.land':
            for j, m in enumerate((77, 81, 84)):
                add(vibe(m), t + j * .03, .065, -.2 + .2 * j, .35)
            add(bass(41, 1.2), t, .09, 0, .05)
        elif kind == 'demo.pdf_fly':
            d = ev['dur']
            add(som_folha[:int(d * SR)], t, .13, .25, .12)
            add(filt(glide(hi[0], hi[2] + 12, d, TL.pdf_fly), 3500), t, .025, .3, .35)
        elif kind == 'demo.pdf_land':
            add(som_pouso, t, .13, .3, .08)
            add(guitar(hi[1] - 12, .6, .6), t, .11, .3, .2)
        elif kind == 'demo.seal':
            add(som_carimbo, t, .14, .35, .1)
            add(bell(89), t, .04, .4, .35)
        elif kind == 'impact.bar':
            v = TL.D['impact'][ev['k']]['v']
            vals = [x['v'] for x in TL.D['impact']]
            scale = [65, 67, 69, 72, 74, 77, 79, 81, 84, 86, 89]
            m = scale[int(round((v - min(vals)) / (max(vals) - min(vals)) * (len(scale) - 1)))]
            add(vibe(m, .9), t, .016, -.4 + .8 * ev['k'] / 44, .25)
        elif kind == 'impact.call':
            for j, m in enumerate(hi):
                add(vibe(m - 12, 2.6), t + j * .04, .045, -.2 + .13 * j, .4)
        elif kind == 'valid.tick':
            i = ev['i']
            add(catraca[i % len(catraca)], t, .045 + .03 * i / TL.VALID_PCT, .15, .05)
        elif kind == 'valid.land':
            for j, m in enumerate((65, 69, 72, 76, 77)):
                add(vibe(m, 2.6), t + j * .02, .045, -.3 + .15 * j, .4)
            add(flute(77, 1.4, rng), t, .05, .1, .35)
            add(bass(41, 1.4), t, .09, 0, .05)
        elif kind == 'marca':
            s = marcas[marca_idx[0] % len(marcas)]
            marca_idx[0] += 1
            arco = .35 + .65 * np.sin(np.pi * np.linspace(0, 1, len(s)))
            add(s * arco, t, .045, .08, .06)
        elif kind == 'end.tonic':
            for j, m in enumerate((53, 57, 60, 64, 67)):
                add(rhodes(m + 12, 6.0), t + j * .015, .075, -.3 + .15 * j, .45)
            add(vibe(77, 5.0), t, .06, .2, .5)
            add(flute(77, 4.2, rng), t, .085, .1, .4)
            add(bass(41, 3.0), t, .12, 0, .05)
            add(guitar(41, 2.5, .3), t, .15, -.1, .2)
            add(pad_chord([41 + 12, 57, 64, 67], DUR - t), t, .12, 0, .4)
        else:
            raise KeyError(f'evento sem som: {kind}')
        cues.append({'time': round(t, 4), 'event': kind, 'constant': ev['constant']})

    # Sala: resposta ao impulso curta e descorrelacionada entre canais
    n = int(1.6 * SR)
    tr = np.arange(n) / SR
    for ch in range(2):
        ir = np.random.default_rng(40 + ch).normal(0, 1, n) * np.exp(-tr / .38)
        ir = filt(ir, 5000)
        ir[:int(.012 * SR)] = 0
        wet = fftconvolve(send[:, ch], ir / np.sqrt(np.sum(ir ** 2)))[:ns]
        mix[:, ch] += wet * .9

    tt = np.arange(ns) / SR
    fade_in = .03 if F.vertical else .5
    mix *= (np.minimum(1, tt / fade_in) * np.clip((DUR - tt) / 1.6, 0, 1))[:, None]
    mix *= .8 / np.abs(mix).max()
    wavfile.write(raw_wav, SR, (mix * 32767).astype(np.int16))
    cues_json.write_text(json.dumps(sorted(cues, key=lambda c: (c['time'], c['event'])), ensure_ascii=False, indent=1))


def masterizar(raw_wav, master_wav):
    """Normalização EBU R128 em duas passagens (`F.lufs`, pico verdadeiro −1,5 dBTP)."""
    alvo = f'loudnorm=I={F.lufs}:TP=-1.5:LRA=8'
    res = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(raw_wav), '-af', f'{alvo}:print_format=json',
                          '-f', 'null', '-'], capture_output=True, text=True, check=True)
    stats = json.loads(res.stderr[res.stderr.rfind('{'):])
    opts = f'{alvo}:linear=true:' + ':'.join([
        f'measured_I={stats["input_i"]}', f'measured_TP={stats["input_tp"]}',
        f'measured_LRA={stats["input_lra"]}', f'measured_thresh={stats["input_thresh"]}',
        f'offset={stats["target_offset"]}',
    ])
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(raw_wav),
                    '-af', opts, '-ar', str(SR), '-c:a', 'pcm_s16le', str(master_wav)], check=True)
    master_wav.with_suffix('.loudness.json').write_text(json.dumps(stats, indent=2))


def gerar(pasta=None):
    pasta = Path(pasta or F.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    raw = pasta / 'trilha-raw.wav'
    master = pasta / 'trilha.wav'
    cues = pasta / 'audio-cues.json'
    sintetizar(raw, cues)
    masterizar(raw, master)
    raw.unlink(missing_ok=True)
    print(f'{master}: {DUR:.2f}s, {F.lufs} LUFS, 48 kHz estéreo')
