"""Dados do filme, tirados do motor TRI do projeto. Roda com o .venv do repositório:

    .venv/bin/python -m filme dados
"""
import json
import sys

import numpy as np

from .formatos import DADOS, REPO

sys.path.insert(0, str(REPO / 'src'))
from tri_enem.calculador import CalculadorTRI  # noqa: E402
from tri_enem.precisao import DATA_FILE, metricas_prova  # noqa: E402

ANO, AREA, CO_PROVA, COR = 2024, 'MT', 1407, 'azul'
PRIMEIRA = 136
# Mesmos 34 acertos, centenas diferentes (A acerta as fáceis; B erra fáceis e acerta difíceis).
DUELO = {'A': 'ABBABBAADDABEEBEADCEBCCCDBDCCDEAABCBDACDBCECB',
         'B': 'ABBABBADDDBBAECEACBEBCCCCCAACBEDDECBDACABDECC'}
DESTAQUES = {'facil': 154, 'discriminacao': 160, 'dificil': 143}
NOTA_MIN, NOTA_MAX, PONTOS = 190.0, 1010.0, 801


def prob(item, th):
    return item.param_c + (1 - item.param_c) / (1 + np.exp(-item.param_a * (th - item.param_b)))


def validacao():
    """Totais do censo: todas as notas oficiais dos microdados contra as calculadas."""
    catalogo = json.loads(DATA_FILE.read_text(encoding='utf-8'))['por_prova']
    metricas = [m for m in map(metricas_prova, catalogo.values()) if m.get('n')]
    n = sum(int(m['n']) for m in metricas)
    acima = sum(int(m['acima_2']) for m in metricas)
    anos = [int(chave.split(',')[0]) for chave in catalogo]
    return {'provas': len(catalogo), 'notas': n, 'acima_2': acima, 'pct_ate_2': 100 * (n - acima) / n,
            'mae': sum(float(m['mae']) * int(m['n']) for m in metricas) / n,
            'ano_min': min(anos), 'ano_max': max(anos)}


def extrair():
    calc = CalculadorTRI()
    itens = calc.carregar_itens(ANO, AREA, CO_PROVA)
    assert len(itens) == 45 and not any(i.abandonado for i in itens)

    def nota_de(th):
        return calc.transformar_escala(float(th), ANO, AREA, CO_PROVA)

    duel = {}
    for nome, resp in DUELO.items():
        r = calc.calcular_nota(ANO, AREA, CO_PROVA, resp)
        duel[nome] = {'resp': resp, 'nota': r['nota'], 'acertos': r['acertos'],
                      'ok': calc.converter_respostas(resp, itens)}
    assert duel['A']['acertos'] == duel['B']['acertos']
    assert int(duel['A']['nota'] // 100) != int(duel['B']['nota'] // 100)

    ordem_b = sorted(range(45), key=lambda k: (itens[k].param_b, k))

    # Grade uniforme em nota; theta pela inversa da transformação (monotônica) da prova.
    theta_fino = np.linspace(-4, 5, 20001)
    nota_fina = np.array([nota_de(t) for t in theta_fino])
    assert np.all(np.diff(nota_fina) > 0)
    grid_nota = np.linspace(NOTA_MIN, NOTA_MAX, PONTOS)
    grid_theta = np.interp(grid_nota, nota_fina, theta_fino)
    prior = np.exp(-grid_theta ** 2 / 2)

    def passos(ordem, acertos):
        """Posterior na grade e nota do motor depois de cada resposta, na ordem dada."""
        log_l = np.zeros_like(grid_theta)
        out = []
        for j in range(len(ordem) + 1):
            if j:
                k = ordem[j - 1]
                p = prob(itens[k], grid_theta)
                fator = p if acertos[k] else 1 - p
                log_l += np.log(fator)
            dens = prior * np.exp(log_l - log_l.max())
            dens /= np.trapezoid(dens, grid_theta)
            feitos = ordem[:j]
            theta = calc.estimar_theta_eap([acertos[i] for i in feitos], [itens[i] for i in feitos])
            passo = {'post': np.round(dens, 5).tolist(), 'nota': nota_de(theta)}
            if j:
                passo['fator'] = np.round(fator, 5).tolist()
            out.append(passo)
        return out

    ok_a = duel['A']['ok']
    steps = passos(ordem_b, ok_a)
    steps_q = [{'post': s['post'], 'nota': s['nota']} for s in passos(list(range(45)), ok_a)]
    assert abs(steps[-1]['nota'] - duel['A']['nota']) < 1e-6
    assert abs(steps_q[-1]['nota'] - duel['A']['nota']) < 1e-6

    an = calc.analisar_todas_questoes(ANO, AREA, CO_PROVA, DUELO['A'])
    impacto = [None] * 45
    for q in an['acertos']:
        impacto[q['idx_area']] = {'q': q['posicao_caderno'], 'ok': True, 'v': q['perda_se_errasse']}
    for q in an['erros']:
        impacto[q['idx_area']] = {'q': q['posicao_caderno'], 'ok': False, 'v': q['ganho_se_acertasse']}
    assert [v['q'] for v in impacto] == list(range(PRIMEIRA, PRIMEIRA + 45))

    return {
        'meta': {'ano': ANO, 'area': AREA, 'cor': COR, 'co_prova': CO_PROVA, 'n_itens': 45,
                 'primeira_questao': PRIMEIRA},
        'items': [{'q': PRIMEIRA + k, 'a': i.param_a, 'b': i.param_b, 'c': i.param_c, 'b_nota': nota_de(i.param_b)}
                  for k, i in enumerate(itens)],
        'ordem_b': ordem_b,
        'duel': duel,
        'destaques': DESTAQUES,
        'grid': {'nota': np.round(grid_nota, 4).tolist(), 'theta': np.round(grid_theta, 6).tolist()},
        'posterior': {'steps': steps, 'steps_q': steps_q},
        'impact': impacto,
        'validacao': validacao(),
    }


def main():
    data = extrair()
    DADOS.parent.mkdir(parents=True, exist_ok=True)
    DADOS.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    duel, val = data['duel'], data['validacao']
    best = max((v for v in data['impact'] if not v['ok']), key=lambda v: v['v'])
    print(f"A {duel['A']['nota']:.2f} · B {duel['B']['nota']:.2f} · {duel['A']['acertos']} acertos cada")
    print(f"maior ganho: Q{best['q']} +{best['v']:.2f}")
    print(f"validação: {val['notas']:,} notas, {val['pct_ate_2']:.3f}% a até 2 pontos, {val['provas']} provas, "
          f"{val['ano_min']}–{val['ano_max']}")


if __name__ == '__main__':
    main()
