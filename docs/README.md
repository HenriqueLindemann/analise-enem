# Documentação

Documentação técnica da Calculadora Nota TRI ENEM.

## Documentos técnicos

| Documento | Descrição |
|-----------|-----------|
| [SCORE_RECALCULATION.md](SCORE_RECALCULATION.md) | (EN) Método de estimativa TRI e validação contra os microdados públicos |

As decisões empíricas sobre transformação, indexação das respostas, estrutura
de LC por ano e metodologia ML3 + EAP ficam junto do código que as implementa,
para não divergirem dele:

- [`../src/tri_enem/calculador.py`](../src/tri_enem/calculador.py) — método, transformação de escala, indexação das respostas e estrutura de LC por ano
- [`../src/tri_enem/precisao.py`](../src/tri_enem/precisao.py) — causas de imprecisão por prova e limiares de erro
- [`../src/tri_enem/tradutor.py`](../src/tri_enem/tradutor.py) — filtragem de itens de língua estrangeira

## Documentação por componente

- [`../README.md`](../README.md) — visão geral, instalação e uso
- [`../src/tri_enem/README.md`](../src/tri_enem/README.md) — módulo de cálculo TRI
- [`../streamlit_app/README.md`](../streamlit_app/README.md) — interface web
- [`../tests/README.md`](../tests/README.md) — testes unitários e scripts de validação
- [`../tools/README.md`](../tools/README.md) — ferramentas de calibração e limpeza de microdados
- [`../examples/README.md`](../examples/README.md) — exemplos de uso via código
