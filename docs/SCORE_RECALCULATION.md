# Método de cálculo e validação

O pacote `tri_enem` estima notas de 2009–2025 a partir das respostas e da
identificação da prova. API, terminal, Streamlit e PDF usam o mesmo catálogo.
Os dados de cálculo vêm no pacote; os microdados brutos são necessários
apenas para pesquisa e recalibração. As métricas por prova estão em
[VALIDATION_REPORT.md](VALIDATION_REPORT.md), gerado do catálogo e manifestos.

## Dados

Os 17 arquivos `ITENS_PROVA_<ano>.csv` ficam em
`src/tri_enem/data/itens/<ano>/`, sem alterações de conteúdo. O manifesto
nessa pasta registra os hashes das fontes e dos CSVs normalizados. O wheel
inclui esses dados, o mapeamento de provas e `coeficientes_data.json`.

Cada entrada de `coeficientes_data.json` (schema v3) contém, por prova:

- a transformação de theta para nota, com âncoras de extremos quando há;
- reconstruções de itens (`reconstrucao_itens`), quando necessárias;
- amostras, métricas, status, proveniência e, quando há, confirmações,
  diagnóstico adverso de treino e desempenho médio ponderado.

## Modelo

O modelo logístico de três parâmetros usa discriminação `a`, dificuldade `b`
e probabilidade de acerto casual `c`:

```text
P(acerto | θ) = c + (1 − c) / (1 + exp(−a · (θ − b)))
```

A habilidade é estimada por EAP com prior normal. A quadratura é definida por
prova: Gauss-Hermite de 80 pontos ou uma grade de 41 pontos entre −4 e 4,
ponderada por `exp(−θ²/2)`. Os cálculos escalar e em lote têm equivalência
numérica testada. O motor usa apenas NumPy e Pandas; SciPy é dependência de
desenvolvimento das ferramentas de pesquisa.

### Reconstrução dos itens

Em algumas provas, os CSVs publicados não reproduzem as notas oficiais com a
associação direta entre curva e posição. O catálogo registra a correção:
associação das curvas às posições, gabaritos, itens excluídos e quadratura.
A maioria reutiliza curvas publicadas; os poucos parâmetros estimados pelo
projeto são marcados no catálogo e não são apresentados como parâmetros
oficiais do INEP. Exemplos:

- LC/2020 digital usa a coleção de 45 itens do idioma informado.
- Os adaptados de 2013 usam uma coleção coerente, sem misturar as duas
  coleções intercaladas no arquivo.
- LC/2017/413 corrige o gabarito da posição 22; CN/2016 inclui o item 29265
  com gabarito inferido `A` no lugar do `X` publicado.

`CalculadorTRI(reconstrucoes={})` calcula com a interpretação direta dos CSVs,
para pesquisa. Itens externos em `itens_path` não recebem as reconstruções do
pacote implicitamente.

### Transformação para a escala

A transformação de theta para nota é linear ou monotônica por trechos.
Candidatos são ajustados em treino e comparados em seleção pelo erro absoluto
médio (MAE), ponderado pela frequência real das faixas de nota e idiomas;
complexidade, P95 e máximo desempatam, nessa ordem. A ponderação evita que
faixas raras, sobreamostradas pela estratificação, dominem a escolha. Os
maiores erros não guiam a seleção, mas determinam os avisos de precisão.

Âncoras de acerto total e erro total exigem evidência consistente em treino.
O trecho interno é delimitado pelos padrões com um acerto e com um erro, para
que um ajuste extremo não se espalhe por respostas comuns.

## Amostragem e avaliação

Os participantes aptos são estratificados por ano, área, prova, idioma e faixa:

```text
(0,400], (400,500], (500,600], (600,700], (700,800],
(800,900], (900,1000], (1000,+∞)
```

São retidos até 160 casos determinísticos por estrato: 100 de treino, 30 de
seleção e 30 de holdout, com tratamento explícito dos extremos. Ausentes,
notas zero, respostas ausentes e provas sem parâmetros não entram na
calibração. Casos com notas acima de 1000 são preservados.

Curvas e gabaritos são inferidos em treino; estimadores e transformações são
escolhidos em seleção; o ajuste final da escala usa treino e seleção. O
holdout não entra no ajuste, mas foi inspecionado durante a pesquisa e é
tratado como avaliação exploratória. As confirmações usam casos novos,
amostrados depois de excluir todos os casos já usados.

A identidade de um caso inclui ano, área, prova e idioma: a exclusão é por
registro nessa área/prova, já que cada área tem modelo próprio. As fixtures
não contêm identificadores pessoais; hashes permitem conferir identidade e
separação.

| Avaliação | Casos | Excluídos antes da amostragem | MAE |
|---|---:|---|---:|
| Holdout primário (exploratório) | 101.552 | Treino e seleção | 0,03601 |
| Confirmação secundária (exploratória) | 113.922 | 531.479 de desenvolvimento | 0,03143 |
| Confirmação residual dos quatro reparos | 1.144 | 645.401 anteriores | 0,02689 |
| Confirmação do erro médio | 4.444 | 646.545 anteriores | 0,03134 (ponderado) |

Os três primeiros MAEs descrevem amostras estratificadas, sem ponderação
populacional. As interseções entre amostras são zero. Os erros máximos são
279,321 pontos no holdout e 127,399 na secundária. Nenhum caso discrepante
foi retirado das avaliações.

Nos mesmos 113.922 registros da confirmação secundária, o cálculo sem as
reconstruções tem MAE de 1,523 e P95 de 5,698 pontos; com elas, 0,031 e 0,050.

### Reparos residuais

CH/2009/72, LC/2011/126 e 128 e MT/2016/367 têm reparos de item congelados
em treino/seleção e confirmados em 1.144 casos novos: o MAE nesses casos
passou de 0,61695 para 0,02689 e as violações acima de dois pontos, de 71
para zero. Os contraexemplos anteriores continuam considerados nos avisos,
inclusive os diagnósticos de treino de LC/2011/126 e 128.

### Transformações escolhidas pelo erro médio

Quatorze provas usam uma transformação escolhida pelo erro médio ponderado e
congelada antes da confirmação; nenhum candidato foi reajustado depois. A
adoção exigiu ganho mínimo de 0,005 ponto e de 20% em seleção.

| Evidência | Provas | Casos | MAE ponderado anterior → atual |
|---|---:|---:|---:|
| Confirmação em casos novos | 8 | 4.444 | 0,04314 → 0,03134 |
| Censo esgotado, avaliação exploratória | 6 | 270 | 0,31655 → 0,09341 |

As confirmadas são CN/2010/105, MT/2011/129, CH/2018/452, MT/2018/462,
MT/2019/516 e CN/2025/1483–1485. Nas outras seis — CH/2012/154, CN/2012/153,
CN/2016/332, LC/2017/441, LC/2021/896 e MT/2025/1611 — todos os participantes
disponíveis já tinham sido usados, de modo que não há casos novos para
confirmação. LC/2021/897 manteve a transformação anterior: o intervalo da
melhora nos seus 69 casos incluiu zero.

O peso de um caso é a contagem real do estrato dividida pelo número de casos
amostrados nele. Os intervalos vêm de bootstrap pareado com 2.000 réplicas
(95% por prova, sem correção para comparações múltiplas). Esses agregados não
estimam o erro de todo o ENEM. As métricas por prova estão no
[manifesto de erro médio](../tests/fixtures/mean_error_confirmation_manifest.json).

CN/2016/332 e MT/2025/1611 usam a escala de cadernos do mesmo ano e área com
curvas ativas e quadratura idênticas, ajustada sem nenhum caso do caderno-alvo.
MT/2025/1611 tem 18 casos e intervalo inconclusivo.

## Precisão na API e na interface

O status técnico considera a cobertura do holdout primário e o maior erro
observado em qualquer amostra registrada: holdout, confirmações e diagnóstico
de treino. O diagnóstico só pode piorar o status; não conta como cobertura
nem como confirmação independente.

| Status | Maior erro observado |
|---|---:|
| `ok` | ≤ 2 pontos |
| `aviso_leve` | > 2 e ≤ 5 |
| `aviso_forte` | > 5 e ≤ 15 |
| `erro_alto` | > 15 |

Menos de 30 casos no holdout, menos de duas faixas ou cobertura incompleta
resultam em `nao_calibrado`. Ausência de itens ou de participantes tem status
próprio. O catálogo tem 579 `ok`, 31 `aviso_forte`, 3 `aviso_leve`, 11
`erro_alto`, 26 `nao_calibrado`, 12 `sem_itens` e 100 `sem_participantes`.

`verificar_precisao_prova()` retorna status, perfil, métricas, origem das
métricas, `criterio_modelo` e `desempenho_tipico`. As métricas exibidas são as
da amostra com maior erro máximo, sem misturar médias e quantis de amostras
diferentes; quando vêm de treino, a interface diz “Observada” em vez de
“Validada”. Os valores retornados são cópias do catálogo.

`confiavel=True` exige `ok` e evidência em casos não usados na pesquisa. Os
seis modelos apoiados só no censo esgotado retornam `confiavel=False`,
inclusive LC/2017/441 e LC/2021/896, que têm status `ok`. A interface mostra:

> Esta nota é uma estimativa. Há poucos resultados oficiais para conferir sua precisão.

Nos detalhes, explica que esses resultados já foram usados na pesquisa e não
comprovam a precisão para outras pessoas. Em provas com poucas exceções, o
perfil comunica bom desempenho na maioria dos casos sem alterar o status
estrito.

## Limites conhecidos

- Os códigos especiais 81–84 de 2009 têm participantes, mas não parâmetros
  identificados. Inversão contínua, projeção no banco publicado e busca de
  permutações não produziram uma reconstrução que generalizasse. Os outros
  108 códigos do censo de ausências não têm registros nas fontes examinadas.
  Sem itens, a API não calcula a nota.
- Anulações seletivas de 2011 dependem de um contexto de grupo que a API não
  recebe. Em CN, excluir os itens 70052, 70617, 71172, 71251 e 71976 explica
  vários casos discrepantes, mas não vale para todos os participantes.
  Respostas idênticas com notas distintas impedem reprodução exata.
- Há indícios de códigos de prova inconsistentes em CH/2015/273 e
  CN/2015/277. Trocar o código com base na nota-alvo não é uma regra possível
  na API; os registros mantêm os códigos publicados.
- As 11 provas com `erro_alto` têm extremos sem âncora consistente ou
  discrepâncias isoladas. Em CN/2010/105 e CN/2012/153, o diagnóstico de
  treino mostra máximos de 171,206 e 31,952 pontos. Reduzir o erro médio não
  garante melhora em cada caso raro.

## Reprodução e proveniência

[tests/README.md](../tests/README.md) descreve a suíte offline e os quatro
validadores, que recalculam as métricas com o código e o catálogo atuais e
conferem hashes e separação das amostras. [tools/README.md](../tools/README.md)
descreve a geração de itens, a recalibração e como incorporar um modelo novo.

Os manifestos em `tests/fixtures/` registram as métricas pareadas e os hashes
das amostras. Os scripts de pesquisa que produziram as reconstruções e as
confirmações não são mantidos; seus resultados estão no catálogo e nas
fixtures, conferidos pelos validadores.
