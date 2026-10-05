# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Contrato do produto: minimizar o erro médio mantendo as exceções visíveis."""
import sys
import json
import gzip
import shutil

import numpy as np
import pytest

import _utils
_utils.add_src_to_path()
sys.path.insert(0, str(_utils.ROOT))

from tri_enem.calibracao_modelos import metricas_modelo, ranking_erro_medio


def test_erro_medio_prioriza_maioria_sem_ocultar_excecao():
    x = np.arange(100.)
    y = np.zeros(100)
    y[-1] = 10.
    maioria = metricas_modelo(x, y, {'tipo':'linear','slope':0.,'intercept':0.})
    deslocamento = metricas_modelo(x, y, {'tipo':'linear','slope':0.,'intercept':1.})
    assert maioria['erro_maximo'] > deslocamento['erro_maximo']
    assert ranking_erro_medio(maioria) < ranking_erro_medio(deslocamento)
    assert maioria['acima_2'] == 1


def test_metricas_apresentadas_nao_podem_ser_mutadas_pelo_consumidor():
    from tri_enem.precisao import verificar_precisao_prova
    p=verificar_precisao_prova(2016,'CN',332)
    original=p['desempenho_tipico']['mae']
    p['desempenho_tipico']['mae']=999.
    assert verificar_precisao_prova(2016,'CN',332)['desempenho_tipico']['mae']==original


def test_validador_rejeita_quantil_ponderado_adulterado_com_hash_atualizado(tmp_path):
    sys.path.insert(0,str(_utils.ROOT/'tests'))
    from validar_erro_medio import validar,sha256
    fixtures=tmp_path/'fixtures'
    shutil.copytree(_utils.ROOT/'tests/fixtures',fixtures)
    path=tmp_path/'catalogo.json'
    catalogo=json.loads((_utils.ROOT/'src/tri_enem/coeficientes_data.json').read_text())
    catalogo['por_prova']['2016,CN,332']['desempenho_tipico']['erro_p95']=999.
    path.write_text(json.dumps(catalogo))
    manifest_path=fixtures/'mean_error_confirmation_manifest.json'
    manifest=json.loads(manifest_path.read_text())
    manifest['catalogo_sha256']=sha256(path)
    manifest_path.write_text(json.dumps(manifest))
    assert any('desempenho_tipico.erro_p95' in f for f in validar(path,fixtures))


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


MANIFEST_MEDIA = json.loads((_utils.ROOT/'tests/fixtures/mean_error_confirmation_manifest.json').read_text())
PUBLICADOS = MANIFEST_MEDIA['models']


@pytest.mark.parametrize('key',['2010,CN,105']+[k for k,r in MANIFEST_MEDIA['por_prova'].items() if not r['independente']])
def test_interface_exibe_origem_do_erro_medio_e_diagnostico(key):
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    ano,area,code=key.split(',')
    independente=MANIFEST_MEDIA['por_prova'][key]['independente']
    rotulo='novos resultados oficiais' if independente else 'não comprova a precisão para outras pessoas'
    app=AppTest.from_string(f'''
from tri_enem.precisao import verificar_precisao_prova
from streamlit_app.components.resultados import exibir_aviso_acuracia
p=verificar_precisao_prova({ano},'{area}',{code})
exibir_aviso_acuracia({{
    **p,'status_precisao':p['status'],'perfil_precisao':p['perfil'],
    'aviso_precisao':p['aviso'],'severidade_precisao':p['severidade']
}})
''').run()
    assert not app.exception
    legendas=[c.value for c in app.caption]
    assert any(rotulo in c and 'diferença média estimada' in c for c in legendas)
    if not independente:
        assert any('Há poucos resultados oficiais' in m.value for m in app.markdown)
        assert not any('exploratória' in c or 'holdout' in c for c in legendas)
        assert not any('ainda' in c.lower() for c in legendas)
        assert not any('ainda' in m.value.lower() for m in app.markdown)
    if key=='2010,CN,105':
        assert any(c.startswith('Observada em ') for c in legendas)


@pytest.mark.parametrize('key',sorted(PUBLICADOS))
def test_modelos_publicados_chegam_a_api_e_interface(key):
    pytest.importorskip('streamlit')
    from tri_enem import CalculadorTRI, MapeadorProvas, SimuladorNota
    from streamlit_app.calculador import CalculadorEnem
    with gzip.open(_utils.ROOT/'tests/fixtures/mean_error_confirmation.jsonl.gz','rt') as stream:
        casos=(json.loads(line) for line in stream)
        row=next(r for r in casos if f"{r['ano']},{r['area']},{r['co_prova']}"==key)
    calc=CalculadorTRI()
    texto=calc.normalizar_respostas(row['respostas'],row['area'],row['ano'],row['tp_lingua'])
    api=calc.calcular_nota(row['ano'],row['area'],row['co_prova'],texto,row['tp_lingua'])
    simples=SimuladorNota().calcular(area=row['area'],ano=row['ano'],co_prova=row['co_prova'],
        respostas=texto,lingua='espanhol' if row['tp_lingua']==1 else 'ingles')
    assert simples.nota == pytest.approx(api['nota'],abs=1e-10)
    prova=MapeadorProvas().descobrir_prova_por_codigo(row['co_prova'],row['ano'],row['area'])
    web=CalculadorEnem().calcular_area(row['ano'],row['area'],texto,prova.cor,prova.tipo_aplicacao,
        'espanhol' if row['tp_lingua']==1 else 'ingles')
    assert web is not None and 'erro' not in web
    assert web['nota'] == pytest.approx(api['nota'],abs=1e-10)
    assert web['criterio_modelo_nota'] == 'menor_erro_absoluto_medio_ponderado'
    assert web['desempenho_tipico']['n'] > 0
    assert 'diferença média estimada' in web['resumo_validacao']
    if not MANIFEST_MEDIA['por_prova'][key]['independente']:
        assert web['confiavel'] is False
        assert web['perfil_precisao'] == 'sem_validacao'
        assert web['severidade_precisao'] != 'sucesso'
