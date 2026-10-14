# Método de cálculo e validação

O pacote `tri_enem` estima a nota de uma prova do ENEM (2009–2025) a partir
das respostas e da identificação da prova. API, terminal, Streamlit e PDF usam
o mesmo catálogo. Os dados de cálculo acompanham o pacote; os microdados brutos
são necessários apenas para pesquisa e recalibração.

Na confirmação secundária (113.922 registros), o erro absoluto médio (MAE) é
**0,031 ponto** e o P95 é **0,050**; sem as reconstruções de itens, seriam
1,523 e 5,698. As métricas de cada prova estão em
[VALIDATION_REPORT.md](VALIDATION_REPORT.md).

| Etapa | Descrição |
|---|---|
| [Dados](#dados) | Parâmetros dos itens publicados pelo INEP e catálogo por prova |
| [Modelo](#modelo) | 3PL com habilidade estimada por EAP |
| [Reconstrução dos itens](#reconstrução-dos-itens) | Correções onde os CSVs não reproduzem as notas oficiais |
| [Escala](#transformação-para-a-escala) | Transformação de θ para nota, ajustada por prova |
| [Avaliação](#amostragem-e-avaliação) | Comparação com notas oficiais em amostras separadas |
| [Status de precisão](#status-de-precisão) | Classificação de cada prova pelo maior erro observado |

## Dados

Os 17 arquivos `ITENS_PROVA_<ano>.csv` ficam em
`src/tri_enem/data/itens/<ano>/`, sem alterações de conteúdo. O manifesto
dessa pasta registra os hashes das fontes e dos CSVs normalizados. O wheel
inclui esses dados, o mapeamento de provas e `coeficientes_data.json`.

Cada entrada de `coeficientes_data.json` (schema v3) contém, por prova:

- a transformação de θ para nota, com âncoras de extremos quando há;
- reconstruções de itens (`reconstrucao_itens`), quando necessárias;
- amostras, métricas, status e proveniência; quando há, confirmações,
  diagnóstico adverso de treino e desempenho médio ponderado.

## Modelo

O modelo logístico de três parâmetros usa discriminação `a`, dificuldade `b`
e probabilidade de acerto casual `c`:

```text
P(acerto | θ) = c + (1 − c) / (1 + exp(−a · (θ − b)))
```

A habilidade é estimada por EAP com prior normal. A quadratura é definida por
prova: Gauss-Hermite de 80 pontos ou grade de 41 pontos entre −4 e 4,
ponderada por `exp(−θ²/2)`. Os cálculos escalar e em lote têm equivalência
numérica testada. O motor usa apenas NumPy e Pandas; SciPy é dependência de
desenvolvimento das ferramentas de pesquisa.

### Reconstrução dos itens

Em algumas provas, a associação direta entre curva e posição nos CSVs
publicados não reproduz as notas oficiais. O catálogo registra a correção:
associação das curvas às posições, gabaritos, itens excluídos e quadratura.
A maioria reutiliza curvas publicadas. Os poucos parâmetros estimados pelo
projeto são marcados no catálogo e não são apresentados como parâmetros
oficiais do INEP. Exemplos:

- LC/2020 digital usa a coleção de 45 itens do idioma informado.
- Os adaptados de 2013 usam uma coleção coerente, sem misturar as duas
  coleções intercaladas no arquivo.
- LC/2017/413 corrige o gabarito da posição 22; CN/2016 inclui o item 29265
  com gabarito inferido `A` no lugar do `X` publicado.

`CalculadorTRI(reconstrucoes={})` calcula com a interpretação direta dos CSVs,
para pesquisa. Itens externos passados em `itens_path` não recebem as
reconstruções do pacote implicitamente.

### Transformação para a escala

A transformação de θ para nota é linear ou monotônica por trechos. Os
candidatos são ajustados em treino e comparados em seleção pelo MAE, ponderado
pela frequência real das faixas de nota e dos idiomas; complexidade, P95 e
máximo desempatam, nessa ordem. A ponderação evita que faixas raras,
sobreamostradas pela estratificação, dominem a escolha. Os maiores erros não
guiam a seleção, mas determinam os avisos de precisão.

Âncoras de acerto total e de erro total exigem evidência consistente em
treino. O trecho interno é delimitado pelos padrões com um acerto e com um
erro, para que um ajuste extremo não se espalhe por respostas comuns.

## Amostragem e avaliação

Os participantes aptos são estratificados por ano, área, prova, idioma e faixa
de nota:

```text
(0,400], (400,500], (500,600], (600,700], (700,800],
(800,900], (900,1000], (1000,+∞)
```

São retidos até 160 casos determinísticos por estrato, com tratamento
explícito dos extremos. Faltantes, notas zero, respostas ausentes e provas sem
parâmetros não entram na calibração; notas acima de 1000 são preservadas.

| Partição | Casos por estrato | Uso |
|---|---:|---|
| Treino | 100 | Inferência de curvas e gabaritos; ajuste da escala |
| Seleção | 30 | Escolha de estimadores e transformações; ajuste final da escala |
| Holdout | 30 | Avaliação; inspecionado durante a pesquisa, logo exploratório |

As confirmações usam casos novos, amostrados após excluir todos os casos já
usados. A identidade de um caso inclui ano, área, prova e idioma: como cada
área tem modelo próprio, a exclusão é por registro nessa área e prova. As
fixtures não contêm identificadores pessoais; hashes permitem conferir
identidade e separação.

| Avaliação | Casos | Excluídos antes da amostragem | MAE |
|---|---:|---|---:|
| Holdout primário (exploratório) | 101.552 | Treino e seleção | 0,03601 |
| Confirmação secundária (exploratória) | 113.922 | 531.479 de desenvolvimento | 0,03143 |
| Confirmação residual dos quatro reparos | 1.144 | 645.401 anteriores | 0,02689 |
| Confirmação do erro médio | 4.444 | 646.545 anteriores | 0,03134 (ponderado) |

Os três primeiros MAEs descrevem amostras estratificadas, sem ponderação
populacional. As interseções entre amostras são vazias. Os erros máximos são
279,321 pontos no holdout e 127,399 na confirmação secundária. Nenhum caso
discrepante foi retirado das avaliações.

### Reparos residuais

CH/2009/72, LC/2011/126 e 128 e MT/2016/367 têm reparos de item congelados em
treino e seleção e confirmados em 1.144 casos novos: o MAE nesses casos passou
de 0,61695 para 0,02689, e as violações acima de dois pontos, de 71 para zero.
Os contraexemplos anteriores continuam considerados nos avisos, inclusive os
diagnósticos de treino de LC/2011/126 e 128.

### Transformações escolhidas pelo erro médio

Quatorze provas usam uma transformação escolhida pelo erro médio ponderado e
congelada antes da confirmação; nenhum candidato foi reajustado depois. A
adoção exigiu ganho mínimo de 0,005 ponto e de 20% em seleção.

| Evidência | Provas | Casos | MAE ponderado anterior → atual |
|---|---:|---:|---:|
| Confirmação em casos novos | 8 | 4.444 | 0,04314 → 0,03134 |
| Censo esgotado, avaliação exploratória | 6 | 270 | 0,31655 → 0,09341 |

- **Confirmadas:** CN/2010/105, MT/2011/129, CH/2018/452, MT/2018/462,
  MT/2019/516 e CN/2025/1483–1485.
- **Censo esgotado** (todos os participantes disponíveis já haviam sido
  usados, sem casos novos para confirmar): CH/2012/154, CN/2012/153,
  CN/2016/332, LC/2017/441, LC/2021/896 e MT/2025/1611.
- **Mantida:** LC/2021/897 conservou a transformação anterior, pois o
  intervalo da melhora nos seus 69 casos incluiu zero.

CN/2016/332 e MT/2025/1611 usam a escala de cadernos do mesmo ano e área com
curvas ativas e quadratura idênticas, ajustada sem nenhum caso do
caderno-alvo. MT/2025/1611 tem 18 casos e intervalo inconclusivo.

O peso de um caso é a contagem real do estrato dividida pelo número de casos
amostrados nele. Os intervalos vêm de bootstrap pareado com 2.000 réplicas
(95% por prova, sem correção para comparações múltiplas). Esses agregados não
estimam o erro de todo o ENEM. As métricas por prova estão no
[manifesto de erro médio](../tests/fixtures/mean_error_confirmation_manifest.json).

<a id="precisão-na-api-e-na-interface"></a>

## Status de precisão

O status considera a cobertura do holdout primário e o maior erro observado
em qualquer amostra registrada: holdout, confirmações e diagnóstico de treino.
O diagnóstico só pode piorar o status; não conta como cobertura nem como
confirmação independente.

| Status | Maior erro observado | Provas |
|---|---:|---:|
| `ok` | ≤ 2 pontos | 579 |
| `aviso_leve` | > 2 e ≤ 5 | 3 |
| `aviso_forte` | > 5 e ≤ 15 | 31 |
| `erro_alto` | > 15 | 11 |
| `nao_calibrado` | < 30 casos no holdout, < 2 faixas ou cobertura incompleta | 26 |
| `sem_itens` | Parâmetros dos itens indisponíveis | 12 |
| `sem_participantes` | Sem participantes nos microdados | 100 |

`verificar_precisao_prova()` retorna status, perfil, métricas, origem das
métricas, `criterio_modelo` e `desempenho_tipico`, como cópias do catálogo.
As métricas exibidas são as da amostra com maior erro máximo, sem misturar
médias e quantis de amostras diferentes; quando vêm de treino, a interface diz
“Observada” em vez de “Validada”.

`confiavel=True` exige `ok` e evidência em casos não usados na pesquisa. Os
seis modelos apoiados só no censo esgotado retornam `confiavel=False`,
inclusive LC/2017/441 e LC/2021/896, que têm status `ok`. Para eles, a
interface mostra:

> Esta nota é uma estimativa. Há poucos resultados oficiais para conferir sua precisão.

Nos detalhes, explica que esses resultados já foram usados na pesquisa e não
comprovam a precisão para outras pessoas. Em provas com poucas exceções, o
perfil comunica bom desempenho na maioria dos casos sem alterar o status
estrito.

## Limites conhecidos

- **2009, códigos especiais 81–84:** têm participantes, mas não parâmetros
  identificados. Inversão contínua, projeção no banco publicado e busca de
  permutações não produziram uma reconstrução que generalizasse. Os outros
  108 códigos do censo de ausências não têm registros nas fontes examinadas.
  Sem itens, a API não calcula a nota.
- **Anulações seletivas de 2011:** dependem de um contexto de grupo que a API
  não recebe. Em CN, excluir os itens 70052, 70617, 71172, 71251 e 71976
  explica vários casos discrepantes, mas não vale para todos os participantes.
  Respostas idênticas com notas distintas impedem reprodução exata.
- **Códigos de prova em 2015:** há indícios de inconsistência em CH/2015/273 e
  CN/2015/277. Trocar o código com base na nota-alvo não é uma regra possível
  na API; os registros mantêm os códigos publicados.
- **Provas com `erro_alto`:** as 11 têm extremos sem âncora consistente ou
  discrepâncias isoladas. Em CN/2010/105 e CN/2012/153, o diagnóstico de
  treino mostra máximos de 171,206 e 31,952 pontos. Reduzir o erro médio não
  garante melhora em cada caso raro.

## Reprodução e proveniência

- [tests/README.md](../tests/README.md): suíte offline e os quatro
  validadores, que recalculam as métricas com o código e o catálogo atuais e
  conferem hashes e separação das amostras.
- [tools/README.md](../tools/README.md): geração de itens, recalibração e
  incorporação de um modelo novo.
- `tests/fixtures/`: manifestos com as métricas pareadas e os hashes das
  amostras.

Os scripts de pesquisa que produziram as reconstruções e as confirmações não
são mantidos; seus resultados estão no catálogo e nas fixtures, conferidos
pelos validadores.
