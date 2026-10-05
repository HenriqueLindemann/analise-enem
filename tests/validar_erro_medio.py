#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Reproduz os modelos atuais e separa confirmação nova de censo exploratório."""
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import gzip
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from tri_enem import CalculadorTRI
from tri_enem.calibracao_modelos import aplicar_modelo, faixa_nota
from validar_confirmacao_residual import avaliar,comparar,ler_fixture,sha256,assinatura


def validar(catalogo_path=None, fixtures_dir=None, cache_dir=None):
    fixtures_dir=fixtures_dir or ROOT/'tests/fixtures'
    fixture=fixtures_dir/'mean_error_confirmation.jsonl.gz'
    mp=fixtures_dir/'mean_error_confirmation_manifest.json'
    cp=catalogo_path or ROOT/'src/tri_enem/coeficientes_data.json'
    manifest=json.loads(mp.read_text());catalogo=json.loads(cp.read_text())['por_prova']
    failures=[]
    for path,expected in ((fixture,manifest['fixture_sha256']),(cp,manifest['catalogo_sha256']),
                         (fixtures_dir/'validation_manifest.json',manifest['primary_manifest_sha256'])):
        if sha256(path)!=expected:failures.append(f'hash divergente: {path.name}')
    rows=ler_fixture(fixture)
    ids=[r['case_id'] for r in rows]
    if len(ids)!=len(set(ids)):failures.append('casos repetidos')
    for r in rows:
        if (set(r)!={'case_id','ano','area','co_prova','tp_lingua','nota_oficial','respostas','faixa','split'}
                or not np.isfinite(r['nota_oficial']) or r['nota_oficial']<=0
                or r['faixa']!=faixa_nota(r['nota_oficial'])
                or len(r['case_id'])!=24 or any(c not in '0123456789abcdef' for c in r['case_id'])):
            failures.append('campos, identidade, nota ou faixa inválidos')
    keys={f"{r['ano']},{r['area']},{r['co_prova']}" for r in rows}
    if keys!=set(manifest['models']) or keys!=set(manifest['por_prova']):failures.append('cobertura divergente')
    previous=set()
    for name in ('validation_holdout','reconstruction_confirmation','residual_confirmation'):
        previous.update(r['case_id'] for r in ler_fixture(fixtures_dir/f'{name}.jsonl.gz'))
    holdout={r['case_id'] for r in ler_fixture(fixtures_dir/'validation_holdout.jsonl.gz')}
    grouped=defaultdict(list)
    for r in rows:
        key=f"{r['ano']},{r['area']},{r['co_prova']}"
        grouped[key].append(r)
        independent=manifest['por_prova'][key]['independente']
        if independent:
            if r['split']!='confirmacao_media' or r['case_id'] in previous:
                failures.append('confirmação nova sobreposta ou rotulada incorretamente')
        elif r['split']!='exploratoria_media' or r['case_id'] not in holdout:
            failures.append('censo exploratório rotulado incorretamente')
    calc=CalculadorTRI()
    counts={(k,li,b):n for k,li,b,n in manifest['counts']}
    if len(counts)!=len(manifest['counts']) or any(not isinstance(n,int) or n<=0 for n in counts.values()):
        failures.append('contagens de frequência inválidas')
    for key in sorted(keys):
        for field,expected in manifest['models'][key].items():
            if catalogo[key].get(field)!=expected:failures.append(f'{key}: modelo atual diverge: {field}')
        result=avaliar({key:catalogo[key]},grouped[key])
        expected=manifest['por_prova'][key]
        comparar(result['por_prova'][key],expected['after'],key,failures)
        if assinatura(r['case_id'] for r in grouped[key])!=expected['case_ids_sha256']:
            failures.append(f'{key}: comparação pareada com identidades diferentes')
        by_language=defaultdict(list)
        for r in grouped[key]:by_language[r['tp_lingua']].append(r)
        errors,weights=[],[]
        for lingua,cases in sorted(by_language.items(),key=lambda kv:str(kv[0])):
            ano,area,code=key.split(',')
            itens,u=calc.preparar_respostas_batch(int(ano),area,int(code),[r['respostas'] for r in cases],lingua)
            theta=calc.estimar_theta_eap_batch(u,itens)
            errors.extend(abs(aplicar_modelo(theta,catalogo[key]['transformacao'])-np.array([r['nota_oficial'] for r in cases])).tolist())
            sample_counts=Counter(r['faixa'] for r in cases)
            weights.extend(counts[(key,lingua,r['faixa'])]/sample_counts[r['faixa']] for r in cases)
        e,w=np.asarray(errors),np.asarray(weights)
        order=np.argsort(e)
        quantile=min(np.searchsorted(np.cumsum(w[order]),.95*w.sum()),len(w)-1)
        weighted={'n':len(e),'mae':float(np.average(e,weights=w)),
            'erro_p95':float(e[order[quantile]]),'erro_maximo':float(e.max()),
            'acima_2':int((e>2+1e-12).sum()),'fracao_acima_2':float(np.average(e>2+1e-12,weights=w))}
        comparar(weighted,expected['after_weighted'],f'{key}.ponderado',failures)
        comparar(catalogo[key]['desempenho_tipico'],weighted,f'{key}.desempenho_tipico',failures)
        if catalogo[key]['desempenho_tipico']['independente']!=expected['independente']:
            failures.append(f'{key}: independência apresentada diverge')
        comparar(catalogo[key]['desempenho_tipico']['intervalo_melhora_media_95'],
                 expected['mean_improvement_ci95'],f'{key}.intervalo',failures)
        if expected['independente']:
            comparar(catalogo[key].get('validacao_media'),
                     {**expected['after'],'origem':'confirmacao_erro_medio','independente':True},
                     f'{key}.validacao_media',failures)
    if manifest['models_refitted'] or manifest['overlapping_independent_cases']:
        failures.append('estado de confirmação inválido')
    if cache_dir is not None:
        residual=json.loads((fixtures_dir/'residual_confirmation_manifest.json').read_text())
        excluded={r['case_id'] for r in ler_fixture(fixtures_dir/'residual_confirmation.jsonl.gz')}
        for name,expected in residual['excluded_caches'].items():
            path=cache_dir/name
            if sha256(path)!=expected['cache_sha256']:failures.append(f'hash do cache divergente: {name}')
            with gzip.open(path,'rt',encoding='utf-8') as stream:cache=json.load(stream)
            cached=[c['case_id'] for roles in cache['splits'].values() for cs in roles.values() for c in cs]
            if (len(cached)!=expected['cases'] or len(set(cached))!=len(cached)
                    or assinatura(cached)!=expected['case_ids_sha256']):
                failures.append(f'identidades do cache divergentes: {name}')
            excluded.update(cached)
        independent={r['case_id'] for r in rows if r['split']=='confirmacao_media'}
        if len(excluded)!=manifest['excluded_previous_cases'] or independent&excluded:
            failures.append('exclusão dos 646.545 casos anteriores diverge')
        frozen_path=cache_dir/'erro_medio_congelado.json'
        frozen=json.loads(frozen_path.read_text())
        if (sha256(frozen_path)!=manifest['frozen_sha256'] or not frozen['models_frozen']
                or frozen['holdout_consulted']):failures.append('congelamento divergente')
        for key in keys:
            if frozen['por_prova'][key]['transformacao']!=catalogo[key]['transformacao']:
                failures.append(f'{key}: modelo diverge do congelamento original')
    return failures


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogo',type=Path)
    parser.add_argument('--fixtures-dir',type=Path)
    parser.add_argument('--cache-dir',type=Path)
    args=parser.parse_args()
    try:failures=validar(args.catalogo,args.fixtures_dir,args.cache_dir)
    except (OSError,ValueError,KeyError,TypeError) as exc:failures=[f'artefatos inválidos: {exc}']
    if failures:
        print('\n'.join(failures));raise SystemExit(1)
    print('Erro médio: modelos atuais, métricas ponderadas, hashes e origem das amostras conferidos.')
