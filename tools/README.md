# Ferramentas de desenvolvimento

Preparam dados e mantêm o catálogo. A API e a interface usam só o catálogo
incluído no pacote. O [método](../docs/SCORE_RECALCULATION.md) explica o
modelo e a validação. Os microdados do INEP são apenas lidos.

## Atualizar o catálogo

```bash
M=/caminho/MICRODADOS_ENEM
python tools/levantar_notas_gabarito.py --microdados-dir $M --saida notas.json
python tools/levantar_censo.py --microdados-dir $M --saida censo.json --processos 3
python tools/atualizar_catalogo.py --notas-gabarito notas.json --censo censo.json
```

1. `levantar_notas_gabarito.py`: nota oficial de quem acerta todos os itens.
2. `levantar_censo.py`: compara a nota calculada com a oficial de todos os
   participantes. Cada processo trata um ano (cerca de 1 GB de RAM).
3. `atualizar_catalogo.py`: grava notas de gabarito e censo, recalcula as
   métricas das amostras e o status, atualiza manifestos e chama
   `relatorio_validacao.py`, que gera `docs/VALIDATION_REPORT.md`.
   `--cache-dir` reajusta também a escala por área. O censo precisa ter sido
   gerado com o mesmo modelo do catálogo.

Depois, regenere `tests/fixtures/golden_notas.json` se as notas mudarem e rode
a verificação de [tests/README.md](../tests/README.md).

## Outras ferramentas

- `gerar_dados_itens.py --microdados-dir $M`: publica os CSVs de itens
  normalizados, com manifesto SHA-256.
- `levantar_notas_por_acertos.py --microdados-dir $M --saida notas.json --app
  streamlit_app/assets/notas_por_acertos.json`: distribuição da nota oficial
  por número de acertos. `--app` grava o recorte usado na interface; sem
  `--microdados-dir`, refaz só o recorte a partir da saída e do `.npz`.
- `recalibrar_validacao.py` e `fechar_gap_validacao.py`: reamostragem
  completa e pesquisa de reconstrução de itens (associação e gabarito). Use
  `OPENBLAS_NUM_THREADS=1` com `--workers`.
- `reconstruir_associacao_itens.py`: pesquisa a associação curva/posição de
  uma prova.
- `avaliar_catalogo.py`: avaliação compartilhada por ferramentas e validadores.
- `perfil_streamlit.py`: mede o desempenho do app.
- `gerar_imagem_readme.py`: imagens do README (exemplo e artigo).

Caches de pesquisa ficam em `resultados/investigacao/`, ignorado pelo Git.
