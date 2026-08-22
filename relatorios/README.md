# Relatórios Gerados

Esta pasta contém os relatórios PDF gerados pelo `meu_simulado.py`.

## Como gerar um relatório

1. Edite `meu_simulado.py` com suas respostas
2. Defina `GERAR_PDF = True`
3. Execute: `python meu_simulado.py`
4. O PDF será salvo aqui com nome automático

## Estrutura do relatório

O PDF contém:

- **Visão geral**: média simples, acertos válidos, anuladas, aproveitamento
  e barras de notas em escala fixa de 0 a 1000
- **Como ler**: explicações curtas de nota TRI, dificuldade (`b`) e impacto
- **Validação por prova**: erro absoluto médio, limite observado em 95% dos
  resultados, maior diferença e mensagem de cautela quando aplicável
- **Detalhes por Área**: para cada área (MT, CN, CH, LC):

  - Grade vetorial de acertos, erros e anuladas
  - Ranking de todas as questões válidas por impacto
  - Tabela única de erros com resposta, gabarito, dificuldade e ganho estimado
  - Faixa compacta de acertos com questão e contribuição estimada em pontos
  - Parâmetro de dificuldade (`b`) dos itens que pedem revisão

Relatórios com duas ou mais áreas usam uma página de visão geral e uma por
área. Com uma única área, todo o conteúdo é composto em uma página, sem capa
separada. Questões anuladas não entram nos percentuais, no impacto nem no
diagnóstico.

Gráficos, grades e textos são desenhados como vetores no próprio PDF, mantendo
nitidez em tela, impressão e ampliação sem imagens rasterizadas.
Acertos, erros e anuladas usam cor e sinais gráficos redundantes, preservando a
distinção quando as cores não são percebidas ou o documento é impresso em cinza.
O rodapé identifica o desenvolvedor e inclui links discretos para o projeto e
o perfil profissional.
Na interface web, a data de geração usa o fuso informado pelo navegador; no
CLI, usa o horário local do computador. Se o fuso não estiver disponível, o
gerador usa o horário de Brasília (UTC−03:00).

Consulte o [`EXEMPLO_relatorio.pdf`](EXEMPLO_relatorio.pdf) para ver a saída
completa de quatro áreas.

Para gerar relatórios por código, use `RelatorioPDF`, `DadosRelatorio`,
`AreaAnalise` e `QuestaoAnalise`, exportados por `tri_enem.relatorios`. Há um
exemplo completo em [`../examples/analise_completa_2024.py`](../examples/analise_completa_2024.py).
