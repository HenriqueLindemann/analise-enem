"""Verificações automáticas do filme: dados, enquadramento, marca-texto, colas, trilha e MP4."""
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from . import cenas as C
from . import desenho as D_MOD
from . import relogio as TL
from .formatos import F


def conteudo(pasta=None):
    """Valida dados, textos, área segura, marca-texto, ponteiro, continuidade das colas e cues."""
    pasta = Path(pasta or F.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    d = TL.D
    meta, duel = d['meta'], d['duel']
    report, falhas = {}, []

    def check(nome, ok, detail=None):
        report[nome] = {'ok': bool(ok), **({'detail': detail} if detail is not None else {})}
        if not ok:
            falhas.append(nome)

    check('prova', (meta['ano'], meta['area'], meta['co_prova'], meta['cor'], meta['n_itens'])
          == (2024, 'MT', 1407, 'azul', 45) and len(d['items']) == 45, meta)
    check('duelo', duel['A']['acertos'] == duel['B']['acertos'] == 34
          and int(duel['A']['nota'] // 100) != int(duel['B']['nota'] // 100)
          and sum(duel['A']['ok']) == sum(duel['B']['ok']) == 34
          and abs(d['posterior']['steps'][-1]['nota'] - duel['A']['nota']) < 1e-6
          and abs(d['posterior']['steps_q'][-1]['nota'] - duel['A']['nota']) < 1e-6,
          {'A': round(duel['A']['nota'], 4), 'B': round(duel['B']['nota'], 4)})
    best = C.IMPACT[C.BEST]
    check('impacto', best['q'] == 171 and not best['ok'] and all(v['q'] == 136 + k for k, v in enumerate(C.IMPACT)),
          {'q': best['q'], 'ganho': round(best['v'], 2)})
    check('duracao', 125 <= TL.DURATION <= 135, round(TL.DURATION, 3))

    # Textos dentro do quadro (ou da área segura do Reels) e marca-texto só após assentar
    drawn, fora, early, active_words = {}, [], [], []
    atual = [0.0]
    orig_text, orig_number = D_MOD.text, D_MOD.number
    orig_words, orig_marker = D_MOD.words, D_MOD.marker
    sx0, sy0, sx1, sy1 = C.SAFE if F.vertical else (-2, -2, C.W + 2, C.H + 2)

    def spy(kind, orig):
        def wrap(c, s, x, y, size, col, a=1.0, f='reg' if kind == 'text' else 'black', align='l', *args, **kw):
            if s and a > .05:
                drawn.setdefault(s, round(atual[0], 2))
                if a > .99:
                    w = D_MOD.tw(c, s, f, size, kw.get('track', 0)) if kind == 'text' else D_MOD.num_w(c, s, f, size)[0]
                    x0 = x - (w if align == 'r' else w / 2 if align == 'c' else 0)
                    x1, y1 = c.user_to_device(x0, y - size * .75)
                    x2, y2 = c.user_to_device(x0 + w, y + size * .22)
                    xa, xb, ya, yb = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
                    inv_botoes = F.vertical and yb > 1080 and xb > 980
                    if xa < sx0 or xb > sx1 or ya < sy0 or yb > sy1 or inv_botoes:
                        fora.append((round(atual[0], 2), s, [round(v) for v in (xa, ya, xb, yb)]))
            return orig(c, s, x, y, size, col, a, f, align, *args, **kw)
        return wrap

    def words_spy(c, s, x, y, size, col, t, t0, *args, **kw):
        assentado = t0 + (len(s.split(' ')) - 1) * TL.WORD_STAGGER + TL.WORD_DUR
        active_words.append((s, assentado))
        try:
            return orig_words(c, s, x, y, size, col, t, t0, *args, **kw)
        finally:
            active_words.pop()

    def marker_spy(c, x, y, w, size, k, a=1.0):
        if active_words and k > 0 and a > 0:
            s, assentado = active_words[-1]
            if atual[0] < assentado:
                early.append((round(atual[0], 3), s))
        return orig_marker(c, x, y, w, size, k, a)

    D_MOD.text = C.text = spy('text', orig_text)
    D_MOD.number = C.number = spy('number', orig_number)
    D_MOD.words = C.words = words_spy
    D_MOD.marker = C.marker = marker_spy
    try:
        for atual[0] in np.arange(0, TL.DURATION, .25):
            C.frame(float(atual[0]))
        for h in TL.TITULOS:
            if h.marca is not None:
                for atual[0] in np.arange(h.t0, h.t_marca + .3, 1 / TL.FPS):
                    C.frame(float(atual[0]))
    finally:
        D_MOD.text = C.text = orig_text
        D_MOD.number = C.number = orig_number
        D_MOD.words = C.words = orig_words
        D_MOD.marker = C.marker = orig_marker

    check('texto_na_area_segura' if F.vertical else 'texto_dentro_do_quadro', not fora, fora[:10])
    check('marca_texto_apos_assentar', not early, early[:10])
    check('duelo_na_tela', C.br(duel['A']['nota']) in drawn and C.br(duel['B']['nota']) in drawn
          and '+' + C.br(duel['A']['nota'] - duel['B']['nota']) in drawn)

    # Escala contínua entre S2, S3 e o mini gráfico da calculadora
    mini = [C.XF_MINI[0] + C.ix(n) * C.XF_MINI[2] for n in (200, 600, 1000)]
    check('escala_continua',
          np.allclose(C.GX, [C.ix(n) for n in C.GRID_NOTA[C.MASK]])
          and all(abs(C.TAPETE[k][0] - C.ix(C.ITENS[k]['b_nota'])) < 1e-9 for k in range(45))
          and np.allclose(mini, [C.mini_x(n) for n in (200, 600, 1000)]))

    # Ponteiro fora da grade da plataforma
    over, cursor = [], []
    orig_cursor = C.draw_cursor
    C.draw_cursor = lambda c, x, y, a=1.0, press=0.0: (
        cursor.append((x, y)) if a > .05 else None, orig_cursor(c, x, y, a, press)
    )
    D_MOD.TRACK = {}
    cw, ch = (30, 47) if F.vertical else (25, 36)
    hw, hh = (25, 33) if F.vertical else (25, 31)
    step_f = 1 if F.vertical else 2
    try:
        for f in range(round(TL.POINTER_IN * TL.FPS), round(TL.COLA45[0] * TL.FPS), step_f):
            cursor.clear()
            D_MOD.TRACK.clear()
            C.frame(f / TL.FPS)
            for x, y in cursor:
                if any(x - hw < cx < x + cw + hw and y - hh < cy < y + ch + hh for cx, cy in D_MOD.TRACK.values()):
                    over.append(round(f / TL.FPS, 2))
    finally:
        C.draw_cursor, D_MOD.TRACK = orig_cursor, None
    check('ponteiro_fora_da_grade', not over, over[:5])

    # Continuidade das colas: rastreio das 45 bolhas e diferença entre quadros
    colas = {'S1→S2': (TL.COLA12_OUT - .2, TL.S2 + 1.0), 'S2→S3': (TL.COLA23[0] - .2, TL.COLA23[1] + 1.2),
             'S3→S4': (TL.COLA34[0] - .2, TL.COLA34[1] + .6), 'S4→S5': (TL.COLA45[0] - .2, TL.COLA45[1] + .8),
             'S5→S6': (TL.COLA56[0] - .2, TL.VALID_COUNT0 - .05), 'S6→S7': (TL.COLA67[0] - .2, TL.COLA67[1] + .6)}
    escala_fps = 60 / TL.FPS
    px_limit = 60 * escala_fps
    cola_stats = {}

    def spikes(series, floor):
        out = []
        for i, v in enumerate(series):
            viz = series[max(0, i - 3):i] + series[i + 1:i + 4]
            if viz and v > floor and v > 3.5 * max(np.median(viz), floor / 4):
                out.append(i)
        return out

    D_MOD.TRACK = {}
    try:
        for nome, (a, b) in colas.items():
            prev_pos, prev_img = None, None
            disp, diffs, missing = {k: [] for k in range(45)}, [], 0
            for f in range(int(a * TL.FPS), int(b * TL.FPS)):
                D_MOD.TRACK.clear()
                s = C.frame(f / TL.FPS)
                img = np.frombuffer(bytes(s.get_data()), np.uint8).reshape(C.H, C.W, 4)[::4, ::4, :3].astype(np.float32)
                pos = dict(D_MOD.TRACK)
                missing += len(pos) != 45
                if prev_pos:
                    for k in pos:
                        disp[k].append(float(np.hypot(pos[k][0] - prev_pos[k][0], pos[k][1] - prev_pos[k][1])))
                    diffs.append(float(np.abs(img - prev_img).mean()))
                prev_pos, prev_img = pos, img
            saltos = sum(len(spikes(d_, 12 * escala_fps)) for d_ in disp.values())
            cortes = spikes(diffs, 1.5 * escala_fps)
            cola_stats[nome] = {'max_px_por_quadro': round(max(max(d_) for d_ in disp.values()), 1), 'saltos': saltos,
                                'max_dif_quadro': round(max(diffs), 2), 'picos_dif': len(cortes),
                                'mediana_dif_quadro': round(float(np.median(diffs)), 3), 'quadros_sem_45': missing}
    finally:
        D_MOD.TRACK = None
    check('colas_continuas', all(v['saltos'] == 0 and v['picos_dif'] == 0 and v['quadros_sem_45'] == 0
                                 and v['max_px_por_quadro'] < px_limit for v in cola_stats.values()), cola_stats)

    # Trilha × eventos visuais
    cues = json.loads((pasta / 'audio-cues.json').read_text(encoding='utf-8'))
    events = TL.eventos()
    key = lambda e: (e['event'], e['constant'])
    by_key = {}
    for c_ in cues:
        by_key.setdefault(key(c_), []).append(c_['time'])
    sem_cue = [e for e in events if not any(abs(t - e['time']) <= 1 / TL.FPS for t in by_key.get(key(e), []))]
    ev_keys = {key(e): e['time'] for e in events}
    orfaos = [c_ for c_ in cues if key(c_) not in ev_keys or abs(ev_keys[key(c_)] - c_['time']) > 1 / TL.FPS]
    check('trilha_sincronizada', not sem_cue and not orfaos and len(cues) == len(events),
          {'eventos': len(events), 'cues': len(cues), 'sem_cue': sem_cue[:5], 'orfaos': orfaos[:5]})

    (pasta / 'verification-content.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    for nome, r in report.items():
        print(('OK   ' if r['ok'] else 'FALHA'), nome, '' if r['ok'] else r.get('detail'))
    assert not falhas, f'verificações falharam: {falhas}'


def quadros_mp4(pasta=None):
    """Confere 21 quadros do MP4 final contra o render atual."""
    pasta = Path(pasta or F.pasta)
    mp4 = F.mp4 if pasta == F.pasta else pasta / F.mp4.name
    tempos = sorted({round(t, 3) for t in [5, 11, 21, TL.S2 + .5, 32, 40, 47, TL.S3 + 1.5, 58, 64, 69.5, TL.S4 + 1,
                                           77, 83, 89.5, TL.S5 + 1, 99, TL.S6 + 1, 110, TL.S7 + 1, 121]})
    results = []
    with tempfile.TemporaryDirectory(prefix=f'nota-tri-{F.nome}-') as tmp:
        root = Path(tmp)
        for t in tempos:
            ref, enc = root / 'ref.png', root / 'enc.png'
            f = round(t * TL.FPS)
            C.frame(f / TL.FPS).write_to_png(str(ref))
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(mp4),
                            '-vf', f'select=eq(n\\,{f})', '-vsync', '0', '-frames:v', '1', str(enc)], check=True)
            a = np.asarray(Image.open(ref).convert('RGB'), dtype=np.float32)
            b = np.asarray(Image.open(enc).convert('RGB'), dtype=np.float32)
            mae = float(np.abs(a - b).mean())
            results.append({'time': t, 'frame': f, 'mean_pixel_error_255': round(mae, 4)})
            assert mae < 2.5, f'quadro {f} ({t}s) diverge do render atual: {mae}'
    (pasta / 'verification-frames.json').write_text(json.dumps(results, indent=2))
    print(f'{len(results)} quadros do MP4 conferem com o render atual.')
