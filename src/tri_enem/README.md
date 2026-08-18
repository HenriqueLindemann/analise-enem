# Módulo TRI ENEM

Este é o módulo principal para cálculo de notas do ENEM usando TRI. Os
parâmetros dos itens e o catálogo de transformação são incluídos no pacote.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `simulador.py` | **SimuladorNota** - Interface simplificada (use este!) |
| `calculador.py` | **CalculadorTRI** - Motor de cálculo com ML3 + EAP |
| `mapeador_provas.py` | Resolve ano, área, aplicação e cor para o código da prova |
| `calibracao_modelos.py` | Ajuste, seleção e avaliação dos modelos de escala |
| `coeficientes.py` | Carrega e aplica o catálogo `coeficientes_data.json` |
| `coeficientes_data.json` | Modelos, métricas do holdout e status por prova |
| `precisao.py` | Converte o status e as métricas em mensagens para o usuário |
| `tradutor.py` | Tratamento especial para LC (múltiplas línguas) |
| `config.py` | Configurações de dificuldade e relatório |
| `data/itens/` | Parâmetros oficiais de 2009-2025 e manifesto de integridade |
| `relatorios/` | Gerador de relatórios PDF |

## Uso

```python
from tri_enem import SimuladorNota

sim = SimuladorNota()
resultado = sim.calcular(
    area='MT',
    ano=2023,
    respostas='CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE',
    cor_prova='azul',
    tipo_aplicacao='1a_aplicacao',
)
print(f"Nota: {resultado.nota:.1f}")
```

Também é possível informar `co_prova=1211` diretamente. Quando houver mais de
um caderno, omitir essas informações causa erro em vez de escolher uma prova
arbitrariamente. Para LC, passe ainda `lingua='ingles'` ou
`lingua='espanhol'`.

`ResultadoNota.questoes_anuladas` sempre usa a numeração global impressa no
caderno. A posição bruta do arquivo de itens, `CO_POSICAO`, fica em
`ResultadoNota.questoes_anuladas_brutas`. Na API avançada,
`analisar_todas_questoes()` mantém `q['posicao']` bruto para o pareamento e
fornece `q['posicao_caderno']` para exibição. A ordem das áreas é
`CH, CN, LC, MT` de 2009 a 2016 e `LC, CH, CN, MT` de 2017 em diante.

Resultados detalhados podem ser convertidos sem efeito colateral com
`normalizar_posicoes_resultados(resultados, ordem_provas)`, que devolve cópias
novas e recalcula `questoes_anuladas` a partir dos detalhes.

Para gerar um relatório a partir de qualquer desses resultados, use
`tri_enem.relatorios.adaptar_resultados_para_relatorio(resultados, ano, ...)`.
O adaptador normaliza a numeração e cria os objetos `DadosRelatorio`,
`AreaAnalise` e `QuestaoAnalise`; os geradores do Streamlit e do script local
compartilham esse caminho.

`SimuladorNota.calcular_todas_areas()` retorna `ResultadoNota` para áreas
calculadas e `ResultadoErro(area, erro)` para falhas individuais; erros não são
mais representados por dicionários legados.

## Geração de PDF

```python
from tri_enem.relatorios import RelatorioPDF, DadosRelatorio

dados = DadosRelatorio(titulo="Meu Simulado", ano_prova=2024)
# ... adicionar áreas

relatorio = RelatorioPDF()
relatorio.gerar(dados, './relatorios/resultado.pdf')
```

Veja mais exemplos em `examples/`.
