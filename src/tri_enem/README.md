# Módulo TRI ENEM

Este é o módulo principal para cálculo de notas do ENEM usando TRI. Os
parâmetros dos itens e o catálogo de transformação são incluídos no pacote.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `simulador.py` | **SimuladorNota** - Interface simplificada (alto nível) |
| `calculador.py` | **CalculadorTRI** - Motor de cálculo com ML3 + EAP |
| `mapeador_provas.py` | Resolve ano, área, aplicação e cor para o código da prova |
| `posicoes.py` | Normalização de posições no caderno e ordem das áreas |
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

> **Nota:** Também é possível informar `co_prova` diretamente. Para LC, informe `lingua='ingles'` ou `lingua='espanhol'`.

## Regras de Numeração e Integração

- **Numeração e Anulações**: `ResultadoNota.questoes_anuladas` usa a numeração global impressa no caderno. A posição relativa no arquivo de itens fica em `questoes_anuladas_brutas`. Na API detalhada (`analisar_todas_questoes`), `posicao` é a relativa e `posicao_caderno` é a do caderno.
- **Ordem das Áreas**: `CH, CN, LC, MT` (2009 a 2016) e `LC, CH, CN, MT` (2017 em diante).
- **Normalização**: Use `posicoes.normalizar_posicoes_resultados()` para converter posições relativas em posições de caderno sem mutação.
- **Adaptador de Relatório**: `tri_enem.relatorios.adaptar_resultados_para_relatorio()` converte resultados em objetos estruturados (`DadosRelatorio`, `AreaAnalise`, `QuestaoAnalise`).
- **Retornos da API**: `SimuladorNota.calcular_todas_areas()` retorna objetos tipados: `ResultadoNota` para áreas calculadas e `ResultadoErro` para eventuais falhas individuais.

## Geração de PDF

```python
from tri_enem.relatorios import RelatorioPDF, DadosRelatorio

dados = DadosRelatorio(titulo="Meu Simulado", ano_prova=2024)
# ... adicionar áreas

relatorio = RelatorioPDF()
relatorio.gerar(dados, './relatorios/resultado.pdf')
```

Consulte exemplos detalhados em [`examples/`](../../examples/README.md).
