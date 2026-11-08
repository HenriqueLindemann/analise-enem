# Contribuindo para TRI ENEM

Obrigado pelo interesse em contribuir!

## Ambiente de desenvolvimento

O projeto requer Python 3.10 ou superior. A partir da raiz do repositório:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[web,dev]"
```

O pacote usa layout `src/`; a instalação editável evita ajustes manuais no
`sys.path` durante o desenvolvimento. As dependências de runtime continuam em
`requirements.txt`, pois esse é também o fluxo usado no deploy.

## Verificações antes do pull request

```bash
pytest -q
python tests/validar_holdout.py
python tests/validar_confirmacao.py
python tests/validar_confirmacao_residual.py
python tests/validar_erro_medio.py
python -m build --wheel
```

Os testes e o validador usam apenas artefatos versionados. Não é necessário
baixar os microdados brutos do INEP para uma mudança comum de código ou
documentação.

Se a alteração afetar cálculo, seleção de itens, escala, mapeamento ou
mensagens de precisão, inclua um teste de regressão.
A integração contínua (`.github/workflows/testes.yml`) roda a suíte e os
validadores, instala o wheel e executa um smoke test fora do checkout.

## Dados e artefatos gerados

- Os parâmetros de itens ficam somente em
  `src/tri_enem/data/itens/<ano>/` e são reproduzidos por
  `tools/gerar_dados_itens.py`.
- O catálogo `src/tri_enem/coeficientes_data.json`, os manifestos e
  `docs/VALIDATION_REPORT.md` são publicados juntos por
  `tools/atualizar_catalogo.py`.
- Não edite `docs/VALIDATION_REPORT.md` manualmente: ele é validado contra os
  demais artefatos.
- Microdados brutos e extratos de participantes não devem ser commitados.
- Método e limites ficam em `docs/SCORE_RECALCULATION.md`. Relatórios de
  experimentos e notas de pesquisa ficam em `resultados/investigacao/`,
  evitando novos Markdown redundantes em `docs/`.

Atualizar o catálogo exige os microdados completos; veja
[`tools/README.md`](tools/README.md).

## Acordo de Licença para Contribuidores (CLA)

Ao enviar um Pull Request para este repositório, você concorda com os seguintes termos:

1. **Licenciamento**: Sua contribuição será distribuída sob a mesma licença do projeto ([PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0))

2. **Permissão Comercial**: Você concede ao mantenedor do projeto (Henrique
   Lindemann) permissão para:

   - Licenciar sua contribuição sob termos comerciais
   - Incluir sua contribuição em versões comerciais do software

3. **Originalidade**: Você declara que sua contribuição é trabalho original seu e que tem autoridade para conceder estes direitos

Este acordo é necessário para manter a possibilidade de oferecer licenciamento comercial do projeto.
