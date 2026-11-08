"""Os dois cortes do filme: mesmo roteiro e relógio, enquadramentos diferentes."""
import os
from dataclasses import dataclass
from pathlib import Path

VIDEO = Path(__file__).resolve().parents[1]
REPO = VIDEO.parent
SAIDA = VIDEO / 'saida'
SONS = VIDEO / 'sons'


@dataclass(frozen=True)
class Formato:
    nome: str
    largura: int
    altura: int
    fps: int
    lufs: float          # loudness integrada da trilha
    crf: int
    preset: str

    @property
    def vertical(self):
        return self.altura > self.largura

    @property
    def pasta(self):
        return SAIDA / self.nome

    @property
    def mp4(self):
        return self.pasta / f'nota-tri-{self.nome}.mp4'


SITE = Formato('site', 1920, 1080, 60, -18, 17, 'fast')
REELS = Formato('reels', 1080, 1920, 30, -14, 16, 'slow')
FORMATOS = {f.nome: f for f in (SITE, REELS)}

# O formato vale para o processo inteiro; `python -m filme --formato reels` define a variável.
F = FORMATOS[os.environ.get('FILME_FORMATO', 'site')]
DADOS = Path(os.environ.get('FILME_DADOS', SAIDA / 'dados.json'))
