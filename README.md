# Calculadora Nota TRI ENEM

Calcule sua nota do ENEM usando **Teoria de Resposta ao Item (TRI)** com alta precisão.

Suporta todas as provas de **2009 a 2024** com análise detalhada e relatórios completos.

---

## 🌐 Interface Web - Sem Instalação

**👉 Acesse direto no navegador:** [https://notatri.com/](https://notatri.com/)

✅ Não precisa instalar Python  
✅ Visualize análises e gráficos interativos em seu navegador

---

## 📥 Instalação (apenas versão local)

### Para quem nunca programou

**Este programa calcula sua nota do ENEM como o INEP calcula.** Você precisa:

1. **Baixar este projeto** (botão verde "Code" → Download ZIP)
2. **Instalar Python**: https://www.python.org/downloads/
3. **Instalar as bibliotecas necessárias**: abra o terminal/prompt na pasta do projeto e digite:
   ```bash
   pip install -r requirements.txt
   ```
4. **Abrir o arquivo `meu_simulado.py`** com Bloco de Notas
5. **Trocar as alternativas** pelas suas respostas da prova
6. **Clicar duas vezes** no arquivo para rodar

**Pronto!** Sua nota aparece na tela e um PDF é criado na pasta `relatorios/`.

**Precisa de ajuda?** Pergunte para sua IA favorita como instalar e rodar um programa Python no seu sistema operacional.

### Para desenvolvedores

```bash
git clone https://github.com/HenriqueLindemann/analise-enem.git
cd analise-enem
pip install -r requirements.txt
```

---

## Uso Rápido

Edite o arquivo **`meu_simulado.py`** com suas respostas:

```python
ANO = 2023
TIPO_APLICACAO = '1a_aplicacao'  # 1a_aplicacao, digital, reaplicacao

# DIA 1
COR_LC = 'azul'
RESPOSTAS_LC = 'ACABC...'  # 45 respostas

COR_CH = 'azul'
RESPOSTAS_CH = 'BDCEA...'

# DIA 2
COR_CN = 'azul'
RESPOSTAS_CN = 'ACDAE...'

COR_MT = 'azul'
RESPOSTAS_MT = 'CEAEA...'
```

Execute:

```bash
python meu_simulado.py
```

Resultado:

```
============================================================
       CALCULADORA NOTA TRI ENEM - PROVA 2023
============================================================

Aplicação: 1a_aplicacao

------------------------------------------------------------
RESULTADOS
------------------------------------------------------------
Linguagens..........................   654.2 pts (33/45)
Ciências Humanas....................   712.4 pts (38/45)
Ciências da Natureza................   695.1 pts (35/45)
Matemática..........................   782.3 pts (40/45)
------------------------------------------------------------
MÉDIA...............................   711.0 pts
```

## Funcionalidades

- ✅ **Cálculo TRI preciso** (erro < 1 ponto em provas calibradas)
- ✅ **Relatórios PDF** com análise de cada questão
- ✅ **Análise de impacto** - descubra quais erros mais afetaram sua nota
- ✅ **Todas as áreas**: MT, CN, CH, LC (inglês/espanhol)
- ✅ **16 anos**: 2009 a 2024

## Uso Avançado

### Via código Python

```python
import sys; sys.path.insert(0, 'src')
from tri_enem import MapeadorProvas, CalculadorTRI

mapeador = MapeadorProvas()
calc = CalculadorTRI()

# Obter código da prova pela cor
co_prova = mapeador.obter_codigo(2023, 'MT', '1a_aplicacao', 'azul')

# Calcular nota
respostas = 'CEAEACCCDABCDAACEDDBAAEBABDDEEBDAECABDBCBCADE'
resultado = calc.calcular_nota_tri(2023, 'MT', co_prova, respostas)
print(f"Nota: {resultado:.1f}")
```

### Análise de impacto dos erros

```python
analise = calc.analisar_todas_questoes(2023, 'MT', co_prova, respostas)

print("Erros que mais impactaram sua nota:")
for erro in analise['erros'][:5]:
    print(f"  Q{erro['posicao']}: +{erro['ganho_se_acertasse']:.1f} pts | Gabarito: {erro['gabarito']}")
```

## Relatório PDF

Defina `GERAR_PDF = True` em `meu_simulado.py` e um relatório será salvo em `relatorios/` com:
- Notas de cada área
- Erros ordenados por impacto
- Parâmetros TRI de cada questão
- **Avisos de precisão** para provas não calibradas ou com erro alto

## Como Funciona

O cálculo usa o **Modelo Logístico de 3 Parâmetros (ML3P)** com estimação EAP:

- **A (Discriminação)**: Quão bem a questão diferencia alunos
- **B (Dificuldade)**: Nível de dificuldade
- **C (Chute)**: Probabilidade de acerto casual

A nota final: `nota = slope × theta + intercept`

> Os parâmetros são disponíveis publicamente pelo INEP. Para resultados corretos, foi necessário descobrir os valores corretos de transformação (slope e intercept) para cada prova via engenharia reversa.

## Precisão e Calibração

| Métrica | Valor |
|---------|-------|
| Erro Médio | < 1 ponto |
| Anos | 2009-2024 |

> **⚠️ ATENÇÃO:** Nem todas as provas estão calibradas. Algumas provas (especialmente de reaplicacões e anos mais antigos) podem apresentar erros maiores. Provas da 1ª aplicação de anos recentes (2018+) têm maior precisão.

## 🧪 Desenvolvimento e Testes

O projeto possui uma suite de testes abrangente para garantir a precisão dos cálculos e a integridade do mapeamento de questões ao longo dos anos.

### Suite de Testes TRI
Para validar os cálculos contra dados oficiais do INEP e garantir que não existam regressões na ordem das questões:

1. **Extrair Casos**: `python3 tests/extrair_exemplos_completos.py`
   - Gera a base `tests/suite_testes_completos.txt` com centenas de estudantes reais extraídos dos microdados.
2. **Executar Testes**: `python3 tests/executar_testes_completos.py`
   - Simula o comportamento do App Streamlit.
   - Compara a nota calculada com a nota oficial (precisão).
   - Valida se a **ordem das questões** está correta (ex: 2016 CH iniciando na 1, 2017+ CH na 46).
   - Lida corretamente com questões anuladas.

## Estrutura do Projeto

```
analise-enem/
├── meu_simulado.py               # 👉 EDITE com suas respostas
├── requirements.txt
├── streamlit_app/                # 🌐 Interface Web
├── src/tri_enem/
│   ├── calculador.py             # Motor de cálculo TRI
│   ├── simulador.py              # Interface simplificada
│   ├── calibrador.py             # Calibração de coeficientes
│   ├── mapeador_provas.py        # API do mapeamento
│   ├── mapeamento_provas.yaml    # 🗺️ Todas as provas 2009-2024
│   ├── coeficientes_data.json    # 📊 Coeficientes + status
│   ├── precisao.py               # Verificação de erros intrínsecos
│   ├── tradutor.py               # LC (inglês/espanhol)
│   └── relatorios/               # Gerador de PDF
├── tools/                        # Ferramentas de calibração
├── examples/                     # Exemplos de uso via código
├── tests/
│   ├── extrair_exemplos_completos.py # Gerador de suite de testes
│   ├── executar_testes_completos.py  # Validador TRI + Ordem (Streamlit)
│   ├── executar_testes_tri.py        # Validador TRI simplificado
│   └── test_mapeador_provas.py
└── relatorios/                  # PDFs gerados
```

## Para Estudantes

1. **Faça um simulado** com uma prova antiga
2. **Anote suas 45 respostas** de cada área
3. **Preencha `meu_simulado.py`** com ano, cor e respostas
4. **Execute e analise** - foque nos erros de questões fáceis!

## Contribuição

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[PolyForm Noncommercial 1.0.0](LICENSE) - Uso pessoal e educacional permitido.

## Autor

**Henrique Lindemann** - Eng. Computação UFRGS  
[LinkedIn](https://www.linkedin.com/in/henriquelindemann/)
