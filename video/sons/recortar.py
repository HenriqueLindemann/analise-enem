"""Regenera os recortes de foley em `video/sons/` a partir das gravações originais.

    python3 video/sons/recortar.py [pasta_originais]

Se um arquivo original não estiver em `pasta_originais`, é baixado da URL em `fontes.json`
e conferido pelo SHA-1 antes do recorte.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SONS = Path(__file__).resolve().parent
FONTES = json.loads((SONS / 'fontes.json').read_text(encoding='utf-8'))
SR = 48000
UA = {'User-Agent': 'notatri-video/1.0 (https://github.com/HenriqueLindemann/analise-enem)'}


def obter_original(meta, pasta):
    caminho = pasta / meta['arquivo']
    if not caminho.exists():
        time.sleep(2)
        req = urllib.request.Request(meta['url'], headers=UA)
        caminho.write_bytes(urllib.request.urlopen(req).read())
    sha1 = hashlib.sha1(caminho.read_bytes()).hexdigest()
    assert sha1 == meta['sha1'], f"SHA-1 divergente para {meta['arquivo']}: {sha1}"
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(caminho), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def envelope(n, ataque, queda):
    t = np.arange(n) / SR
    return np.clip(np.minimum(1.0, t / max(ataque, 1e-4)) * np.minimum(1.0, (n / SR - t) / max(queda, 1e-4)), 0, 1)


def recortar(meta, x):
    x = sosfilt(butter(2, meta['passa_altas_hz'], 'highpass', fs=SR, output='sos'), x)
    n = int(round(meta['duracao_s'] * SR))
    env = envelope(n, meta['ataque_s'], meta['queda_s'])
    if 'picos_s' in meta:
        pre = int(round(meta['pre_pico_s'] * SR))
        janela = int(0.025 * SR)
        inicios = []
        for t in meta['picos_s']:
            ia = max(0, int((t - 0.012) * SR))
            inicios.append(ia + int(np.argmax(np.abs(x[ia:ia + janela]))) - pre)
    else:
        inicios = [int(round(t * SR)) for t in meta['fatias_s']]
    fatias = []
    for i0 in inicios:
        s = x[i0:i0 + n] * env
        s /= np.sqrt(np.mean(s ** 2)) + 1e-9
        fatias.append(s)
    out = np.concatenate(fatias)
    out *= 0.85 / (np.abs(out).max() + 1e-9)
    return (out * 32767).astype(np.int16)


def main(pasta_originais=None):
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(pasta_originais) if pasta_originais else Path(tmp)
        pasta.mkdir(parents=True, exist_ok=True)
        for nome, meta in FONTES.items():
            wav = recortar(meta, obter_original(meta, pasta))
            wavfile.write(SONS / nome, SR, wav)
            print(f"{nome:12s} {len(wav) / SR:5.2f}s  ({meta['licenca']} · {meta['autor']})")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
