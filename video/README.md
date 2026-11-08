# Vídeo explicativo

Gera o vídeo da calculadora em dois formatos a partir do mesmo roteiro e relógio (132 BPM):

- `site`: `1920×1080`, 60 fps, −18 LUFS (`video/saida/site/nota-tri-site.mp4`)
- `reels`: `1080×1920`, 30 fps, −14 LUFS (`video/saida/reels/nota-tri-reels.mp4`)

## Como gerar

Requer `python3` (`pycairo`, `numpy`, `scipy`, `Pillow`), `ffmpeg`, fonte Lato e o `.venv` da raiz:

```bash
./video/build.sh site reels
PUBLICAR=1 ./video/build.sh site reels   # atualiza streamlit_app/assets/video-nota-tri*.mp4 e docs/imagens/video-preview.jpg
```

Ou por etapa (`--formato site|reels`):

```bash
.venv/bin/python -m filme dados
python3 -m filme --formato site <trilha|verificar|quadros|montar|stills|publicar>
```

## Sons (`sons/`)

Recortes mono 48 kHz em domínio público / CC0 1.0, detalhados em `sons/fontes.json` e regenerados por `python3 video/sons/recortar.py`:

- `marca.wav`: *377124 tubbsmedia marker-lines.wav* — TubbsMedia (Wikimedia Commons, CC0)
- `clique.wav`: *Computer mouse single click.ogg* — Darklanlan (Wikimedia Commons, CC0)
- `teclas.wav`: *Typing medium speed.ogg* — teto_yasha (Wikimedia Commons, domínio público)
- `folha.wav`: *Turning a page.ogg* — planish (Wikimedia Commons, domínio público)
- `pouso.wav`: *Book paper pages assorted.ogg* — stephan (Wikimedia Commons, domínio público)
- `catraca.wav`: *Tools Ratchet.ogg* — CapsLok (Wikimedia Commons, CC0)
- `carimbo.wav`: *es-stamp.wav* (`448474`) — eddies2000 (Freesound, CC0)
