# Testes e validação

A suíte e as fixtures verificam o motor e o catálogo sem os microdados brutos.

```bash
python -m pip install -e ".[web,dev]"
python -m pytest -q
python tests/validar_holdout.py
python tests/validar_confirmacao.py
python tests/validar_confirmacao_residual.py
python tests/validar_erro_medio.py
```

Testes de Streamlit, Plotly ou PDF são pulados sem o extra correspondente.
`smoke_instalacao.py` testa o wheel fora do checkout.

## Validadores

Cada validador recalcula as notas da sua fixture com o código e o catálogo
atuais e confere métricas, hashes e separação entre as amostras. Holdout e
confirmação somados formam a amostra de teste citada no
[método](../docs/SCORE_RECALCULATION.md).

| Fixture | Casos | Validador |
|---|---:|---|
| `validation_holdout` | 101.552 | `validar_holdout.py`: catálogo, status (com o censo), relatório |
| `reconstruction_confirmation` | 113.922 | `validar_confirmacao.py` |
| `residual_confirmation` | 1.144 | `validar_confirmacao_residual.py` |
| `mean_error_confirmation` | 4.444 | `validar_erro_medio.py` |

Registros de `fixtures/registros_inconsistentes.json` ficam fora das métricas.
`golden_notas.json` protege a regressão numérica. Depois de mudar o modelo,
gere-o de novo com `python tests/fixtures/gerar_golden_notas.py`.

## Microdados

Com os microdados locais, `validar_exemplos_microdados.py` confere casos reais
e `run_full_validation.py` refaz o fluxo completo. Para atualizar o catálogo,
veja [tools/README.md](../tools/README.md).

O teste de digitação e layout em navegador real está em
[streamlit_app/README.md](../streamlit_app/README.md#testes).
