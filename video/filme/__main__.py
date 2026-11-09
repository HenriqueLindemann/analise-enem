# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2026 Henrique Lindemann
"""CLI do filme: `python3 -m filme [--formato site|reels] <comando>`."""
import argparse
import json
import os
import subprocess
import sys

TEMPOS_STILLS_SITE = (5, 11, 21, 24.5, 32, 40, 47, 52.5, 58, 64, 69.5, 73, 77, 83, 89.5, 93, 99, 106.5, 110, 117, 121)
TEMPOS_STILLS_REELS = (1, 5, 11, 17.5, 21, 24.5, 32, 40, 47, 52.5, 58, 64, 69.5, 73, 77, 83, 89.5, 93, 99, 106.5, 110,
                       117, 121)


def montar():
    from . import relogio as TL
    from . import verificacao
    from .formatos import F

    pasta = F.pasta
    parts_dir = pasta / 'parts'
    parts = sorted(parts_dir.glob('p*.mp4'), key=lambda p: int(p.stem[1:]))
    (parts_dir / 'concat.txt').write_text(''.join(f"file '{p.name}'\n" for p in parts))
    tmp = F.mp4.with_suffix('.tmp.mp4')

    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
           '-i', str(parts_dir / 'concat.txt'), '-i', str(pasta / 'trilha.wav')]
    if F.vertical:
        cmd += ['-map', '0:v:0', '-map', '1:a:0', '-map_metadata', '-1',
                '-metadata', 'title=Nota TRI ENEM — Reels']
    else:
        meta = ';FFMETADATA1\ntitle=Nota TRI ENEM\ncomment=UI ilustrada a partir da aplicação atual.\n'
        for i, (start, title) in enumerate(TL.SCENES):
            end = TL.SCENES[i + 1][0] if i + 1 < len(TL.SCENES) else TL.DURATION
            meta += f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(start * 1000)}\nEND={round(end * 1000)}\ntitle={title}\n'
        chapters = parts_dir / 'chapters.txt'
        chapters.write_text(meta, encoding='utf-8')
        cmd += ['-i', str(chapters), '-map', '0:v:0', '-map', '1:a:0', '-map_metadata', '2', '-map_chapters', '2']
    cmd += ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(tmp)]
    subprocess.run(cmd, check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-v', 'error', '-i', str(tmp), '-f', 'null', '-'], check=True)

    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,sample_rate,nb_frames',
                            '-of', 'json', str(tmp)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    assert abs(float(info['format']['duration']) - TL.DURATION) < .05, info['format']['duration']
    video = next(s for s in info['streams'] if s.get('width'))
    assert (video['width'], video['height'], video['r_frame_rate']) == (F.largura, F.altura, f'{F.fps}/1')
    assert int(video['nb_frames']) == TL.FRAMES, video['nb_frames']
    assert any(s.get('sample_rate') == '48000' for s in info['streams'])
    (pasta / 'verification-media.json').write_text(json.dumps(info, indent=2))
    tmp.replace(F.mp4)
    verificacao.quadros_mp4(pasta)
    print('Verificado e entregue:', F.mp4)


def gerar_stills():
    from . import cenas as C
    from . import quadros
    from .formatos import F

    pasta = F.pasta
    tempos = TEMPOS_STILLS_REELS if F.vertical else TEMPOS_STILLS_SITE
    quadros.stills(pasta / 'stills', tempos)
    if F.vertical:
        quadros.stills(pasta / 'stills-safe', tempos, interface=True)
        C.frame(11.5).write_to_png(str(pasta / 'capa-reels.png'))


def publicar():
    import shutil

    import cairo
    from PIL import Image

    from . import cenas as C
    from . import relogio as TL
    from .formatos import F, REELS, REPO, SITE

    if F.vertical:
        destino = REPO / 'streamlit_app' / 'assets' / 'video-nota-tri-reels.mp4'
        shutil.copy2(REELS.mp4, destino)
        print(f'{destino.relative_to(REPO)}: {destino.stat().st_size / 1e6:.1f} MB')
        return

    source = SITE.mp4
    video_app = REPO / 'streamlit_app' / 'assets' / 'video-nota-tri.mp4'
    preview = REPO / 'docs' / 'imagens' / 'video-preview.jpg'
    limit = 10_000_000

    tmp = video_app.with_suffix('.tmp.mp4')
    subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(source),
                    '-map', '0:v:0', '-map', '0:a:0', '-map_metadata', '-1', '-map_chapters', '-1',
                    '-r', '30', '-c:v', 'libx264', '-preset', 'slow', '-tune', 'animation', '-crf', '23',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                    '-metadata', 'title=Como a nota TRI do ENEM é calculada',
                    '-movflags', '+faststart', str(tmp)], check=True)
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                      'format=duration,size:stream=width,height,r_frame_rate', '-of', 'json', str(tmp)],
                                     capture_output=True, text=True, check=True).stdout)
    assert abs(float(info['format']['duration']) - TL.DURATION) < .1, info['format']
    assert int(info['format']['size']) < limit, info['format']['size']
    video = next(s for s in info['streams'] if s.get('width'))
    assert (video['width'], video['height'], video['r_frame_rate']) == (1920, 1080, '30/1'), video
    tmp.replace(video_app)

    surf = C.frame(42.0)
    c = cairo.Context(surf)
    minutes, seconds = divmod(round(TL.DURATION), 60)
    label = f'Assista · {minutes}:{seconds:02d}'
    w = C.tw(c, label, 'bold', 40)
    x, y, h = 150, 960, 66
    C.card(c, x, y, w + 98, h, h / 2, fill=C.INK, border=C.INK, sh=False)
    c.set_source_rgb(*C.YELLOW)
    c.move_to(x + 30, y + 18)
    c.line_to(x + 30, y + h - 18)
    c.line_to(x + 56, y + h / 2)
    c.close_path()
    c.fill()
    C.text(c, label, x + 70, y + 47, 40, C.WHITE, 1, 'bold')
    surf.flush()
    png = SITE.pasta / 'video-preview.png'
    surf.write_to_png(str(png))
    Image.open(png).convert('RGB').resize((1280, 720), Image.LANCZOS).save(preview, quality=90, optimize=True)
    png.unlink(missing_ok=True)
    print(f'{video_app.relative_to(REPO)}: {int(info["format"]["size"]) / 1e6:.1f} MB · {preview.relative_to(REPO)}')


def main():
    p = argparse.ArgumentParser(prog='python3 -m filme')
    p.add_argument('--formato', choices=('site', 'reels'), default=os.environ.get('FILME_FORMATO', 'site'))
    p.add_argument('comando', choices=('dados', 'trilha', 'verificar', 'quadros', 'montar', 'stills', 'publicar'))
    p.add_argument('args', nargs='*')
    ns = p.parse_args()
    os.environ['FILME_FORMATO'] = ns.formato

    if ns.comando == 'dados':
        from . import dados
        dados.main()
    elif ns.comando == 'trilha':
        from . import trilha
        trilha.gerar()
    elif ns.comando == 'verificar':
        from . import verificacao
        verificacao.conteudo()
    elif ns.comando == 'quadros':
        from . import quadros, relogio
        if not ns.args:
            print(relogio.FRAMES)
        else:
            f0, f1, saida = ns.args
            quadros.trecho(int(f0), int(f1), saida)
    elif ns.comando == 'montar':
        montar()
    elif ns.comando == 'stills':
        gerar_stills()
    elif ns.comando == 'publicar':
        publicar()


if __name__ == '__main__':
    main()
