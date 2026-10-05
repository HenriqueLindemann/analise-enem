#!/usr/bin/env python3
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Mede inicialização, cálculo e reruns offline, sem alterar dados ou fixtures.

Execute na raiz com o ambiente que contém as dependências web:
    python tools/perfil_streamlit.py --repeticoes 15

--repo permite medir outra cópia do código com o mesmo Python/dependências.
Execute as duas medições em processos separados e sem testes em paralelo.
AppTest mede Python e serialização; não mede rede ou renderização do navegador.
O cálculo mede a espera até o resumo; o PDF e os detalhes abertos são medidos
separadamente. Em versões antigas, a espera até o resumo inclui o PDF.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path


def medir(funcao, repeticoes: int) -> dict:
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao()
        tempos.append((time.perf_counter() - inicio) * 1000)
    return {
        "mediana_ms": round(statistics.median(tempos), 3),
        "min_ms": round(min(tempos), 3),
        "max_ms": round(max(tempos), 3),
        "n": repeticoes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repeticoes", type=int, default=15)
    args = parser.parse_args()
    if args.repeticoes < 1:
        parser.error("--repeticoes deve ser positivo")
    root = args.repo.resolve()
    if not (root / "streamlit_app/app.py").is_file():
        parser.error("--repo precisa conter streamlit_app/app.py")
    os.chdir(root)
    sys.path[:0] = [str(root / "src"), str(root)]

    # Não importar o app, Plotly ou o motor antes da primeira execução.
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(root / "streamlit_app/app.py"), default_timeout=180)

    def executar():
        at.run()
        if at.exception:
            raise RuntimeError(str(at.exception))

    medidas = {"app_inicial": medir(executar, 1)}
    medidas["rerun_sem_resultados"] = medir(executar, args.repeticoes)

    # Entradas reais do golden, em 2024 e nas quatro áreas.
    casos = json.loads((root / "tests/fixtures/golden_notas.json").read_text(encoding="utf-8"))
    casos = [next(c for c in casos if c['ano'] == 2024 and c['area'] == area)
             for area in ("LC", "CH", "CN", "MT")]
    at.selectbox(key="ano_prova").set_value(2024)
    executar()
    for caso in casos:
        at.session_state[f"resp_{caso['area'].lower()}"] = caso['respostas']
    executar()

    def calcular():
        at.button(key="calcular").click()
        executar()
        if len(at.session_state['resultados']) != 4:
            raise RuntimeError("O cálculo precisa produzir quatro resultados")

    medidas["primeiro_calculo_ate_resumo"] = medir(calcular, 1)
    medidas["rerun_com_resumo"] = medir(executar, args.repeticoes)
    medidas["recalculo_ate_resumo"] = medir(calcular, args.repeticoes)

    from streamlit_app.components.impressao import _gerar_pdf

    resultados = at.session_state['resultados']

    def gerar_pdf():
        pdf = _gerar_pdf(resultados, 2024, '1a_aplicacao', resultados[0]['cor_prova'])
        if not pdf or not pdf.startswith(b'%PDF-'):
            raise RuntimeError('O relatório precisa produzir um PDF válido')
        return pdf

    medidas["geracao_pdf_primeira_chamada_separada"] = medir(gerar_pdf, 1)
    medidas["geracao_pdf"] = medir(gerar_pdf, args.repeticoes)
    def executar_detalhes():
        # AppTest não envia o estado dos expanders dinâmicos de volta ao
        # servidor: manter abertos explicitamente em cada execução medida.
        for area in ('LC', 'CH', 'CN', 'MT'):
            at.session_state[f'detalhes_{area}'] = True
        executar()

    medidas["abrir_4_detalhes"] = medir(executar_detalhes, 1)
    medidas["rerun_com_4_detalhes_abertos"] = medir(executar_detalhes, args.repeticoes)

    from tri_enem import CalculadorTRI
    import numpy
    import pandas
    import plotly
    import streamlit
    import yaml

    from tri_enem.mapeador_provas import _carregar_yaml_cache

    def carregar_mapeador_sem_cache():
        from tri_enem import MapeadorProvas
        _carregar_yaml_cache.cache_clear()
        return MapeadorProvas()

    medidas["mapeador_sem_cache"] = medir(carregar_mapeador_sem_cache, args.repeticoes)

    calc = CalculadorTRI()

    def analisar():
        return [calc.analisar_todas_questoes(
            c['ano'], c['area'], c['co_prova'], c['respostas'], c['tp_lingua'],
        ) for c in casos]

    # Aquecer apenas leitura/itens para separar a primeira preparação numérica.
    for c in casos:
        calc.carregar_itens(c['ano'], c['area'], c['co_prova'], c['tp_lingua'])
    medidas["analise_motor_primeira_preparacao"] = medir(analisar, 1)
    medidas["analise_motor_4_areas"] = medir(analisar, args.repeticoes)
    if hasattr(calc, '_cache_logs_quadratura'):
        medidas['cache_logs_arrays_mib'] = round(sum(
            log_p.nbytes + log_q.nbytes
            for log_p, log_q in calc._cache_logs_quadratura.values()
        ) / 1024**2, 3)
        medidas['cache_logs_limite_entradas'] = calc.MAX_CACHE_QUADRATURA

    def carregar_itens_sem_cache():
        calc._cache_itens.clear()
        return [calc.carregar_itens(
            c['ano'], c['area'], c['co_prova'], c['tp_lingua'],
        ) for c in casos]

    medidas["carregar_itens_4_cadernos"] = medir(carregar_itens_sem_cache, args.repeticoes)
    # Todos os anos: medir o tamanho real dos DataFrames que o recurso pode reter.
    for ano in range(2009, 2026):
        calc.listar_provas(ano)
    medidas["dataframes_todos_anos_mib"] = round(sum(
        df.memory_usage(deep=True).sum() for df in calc._cache_df_itens.values()
    ) / 1024**2, 3)

    ambiente = {
        "python": platform.python_version(), "numpy": numpy.__version__,
        "pandas": pandas.__version__, "plotly": plotly.__version__,
        "streamlit": streamlit.__version__, "pyyaml": yaml.__version__,
        "libyaml": yaml.__with_libyaml__,
    }
    print(json.dumps({"ambiente": ambiente, "medidas": medidas}, indent=2))


if __name__ == "__main__":
    main()
