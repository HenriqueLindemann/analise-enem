# Testes e validação

A suíte e as fixtures verificam o motor e o catálogo atuais sem exigir os
microdados brutos.

## Verificação offline

Na raiz do repositório, com o ambiente de desenvolvimento instalado:

```bash
python -m pip install -e ".[web,dev]"
python -m pytest -q
python tests/validar_holdout.py
python tests/validar_confirmacao.py
python tests/validar_confirmacao_residual.py
python tests/validar_erro_medio.py
```

A CI executa essas verificações, constrói o wheel e testa a instalação fora
do checkout com `smoke_instalacao.py`. Testes que dependem de Streamlit,
Plotly ou PDF são pulados quando o respectivo extra não está instalado.

## Evidência reproduzível

Cada validador recalcula as notas das suas fixtures com o código e o catálogo
atuais e compara com o manifesto e com as métricas publicadas no catálogo.
Também confere hashes, cobertura e a separação entre as amostras.

| Fixture e manifesto | Casos | Verificação |
|---|---:|---|
| `validation_holdout` / `validation_manifest` | 101.552 | Catálogo, cobertura, métricas, status e relatório gerado |
| `reconstruction_confirmation` | 113.922 | Confirmação secundária, identidades e comparação pareada |
| `residual_confirmation` | 1.144 | Quatro reparos residuais e congelamento dos modelos |
| `mean_error_confirmation` | 4.444 novos + 270 exploratórios | Quatorze transformações, métricas ponderadas e origem da evidência |

As respostas ficam em `.jsonl.gz`; os manifestos, em `.json`.
`golden_notas.json` protege a regressão numérica. `reconstruction_regressions.json`
contém casos selecionados por causa de erro específica e não substitui as
avaliações completas.

Com os caches locais de `resultados/investigacao/`, dois validadores
conferem também a exclusão de todos os casos de desenvolvimento (645.401
antes da confirmação residual e 646.545 antes da do erro médio):

```bash
python tests/validar_confirmacao_residual.py --cache-dir resultados/investigacao
python tests/validar_erro_medio.py --cache-dir resultados/investigacao
```

## Cobertura da suíte

- Motor: notas, theta, monotonicidade, extremos, reconstruções e equivalência
  escalar/lote; integridade dos itens empacotados de 2009–2025.
- API e interface: identificação da prova, atendimento especializado, idioma,
  respostas, numeração das questões, coerência das notas e geração de PDF.
- Precisão: status, perfil, origem das métricas, falha fechada e mensagens.
  Modelos sem evidência em casos novos retornam `confiavel=False`, mesmo com
  status `ok`.
- Pesquisa: seleção por erro médio, ponderação das faixas, congelamento,
  separação de casos e detecção de métricas ou modelos adulterados.

O [método](../docs/SCORE_RECALCULATION.md) explica os critérios e limitações;
[VALIDATION_REPORT.md](../docs/VALIDATION_REPORT.md) apresenta as métricas por
prova. O relatório é gerado e não deve ser editado manualmente.

## Microdados e atualização dos modelos

`run_full_validation.py` prepara os itens e recalibra a partir dos arquivos
originais; `--somente-validar` apenas confere os artefatos existentes. As
ferramentas aceitam tanto `YYYY/MICRODADOS_ENEM_YYYY.csv` quanto a estrutura
extraída do download do INEP. Consulte [tools/README.md](../tools/README.md)
antes de recalibrar: esse fluxo altera o catálogo e exige reavaliar as
confirmações.

Após uma mudança numérica, gere o golden atual:

```bash
python tests/fixtures/gerar_golden_notas.py
```

Uma confirmação nova deve excluir todos os casos anteriores antes de amostrar;
casos já examinados não contam como confirmação. Casos discrepantes nunca são
removidos das avaliações.

Para verificar digitação e layout em navegador real, consulte o smoke test
opt-in em [streamlit_app/README.md](../streamlit_app/README.md#testes).
