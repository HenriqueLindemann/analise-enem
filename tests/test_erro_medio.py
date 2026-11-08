# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Seleção pelo erro médio e validador da confirmação do erro médio."""
import sys
import json
import shutil

import numpy as np

import _utils
_utils.add_src_to_path()
sys.path.insert(0, str(_utils.ROOT))

from tri_enem.calibracao_modelos import ranking_erro_medio
from tools.avaliar_catalogo import metricas


def test_erro_medio_prioriza_maioria_sem_ocultar_excecao():
    y = np.zeros(100)
    y[-1] = 10.
    maioria = metricas(y)
    deslocamento = metricas(y - 1.)
    assert maioria['erro_maximo'] > deslocamento['erro_maximo']
    assert ranking_erro_medio(maioria) < ranking_erro_medio(deslocamento)
    assert maioria['acima_2'] == 1


def test_validador_rejeita_quantil_ponderado_adulterado(tmp_path):
    sys.path.insert(0,str(_utils.ROOT/'tests'))
    from validar_erro_medio import validar
    fixtures=tmp_path/'fixtures'
    shutil.copytree(_utils.ROOT/'tests/fixtures',fixtures)
    manifest_path=fixtures/'mean_error_confirmation_manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest['por_prova']['2016,CN,332']['after_weighted']['erro_p95']=999.
    manifest_path.write_text(json.dumps(manifest))
    assert any('ponderado.erro_p95' in f for f in validar(fixtures_dir=fixtures))


def test_validador_rejeita_censo_rebatizado_como_confirmacao(tmp_path):
    sys.path.insert(0,str(_utils.ROOT/'tests'))
    from validar_erro_medio import validar
    fixtures=tmp_path/'fixtures'
    shutil.copytree(_utils.ROOT/'tests/fixtures',fixtures)
    manifest_path=fixtures/'mean_error_confirmation_manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest['por_prova']['2016,CN,332']['independente']=True
    manifest_path.write_text(json.dumps(manifest))
    assert any('rotulada incorretamente' in f for f in validar(fixtures_dir=fixtures))
