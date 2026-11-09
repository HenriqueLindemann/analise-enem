# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""Quadros: stills PNG e trechos de vídeo via ffmpeg."""
import subprocess
from pathlib import Path

import cairo

from . import relogio as TL
from .cenas import W, H, frame, reels_overlay
from .formatos import F


def stills(pasta, tempos, interface=False):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    for t in tempos:
        s = frame(float(t))
        if interface:
            reels_overlay(s)
        s.write_to_png(str(pasta / f'f_{float(t):07.3f}.png'))


def trecho(f0, f1, saida):
    """Renderiza os quadros [f0, f1) num MP4 sem áudio."""
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
           '-r', str(TL.FPS), '-i', '-', '-c:v', 'libx264', '-preset', F.preset, '-crf', str(F.crf),
           '-threads', '2', '-pix_fmt', 'yuv420p', '-tune', 'animation', str(saida)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for f in range(f0, f1):
        frame(f / TL.FPS, surf)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    if p.wait():
        raise RuntimeError('ffmpeg falhou durante a renderização')
