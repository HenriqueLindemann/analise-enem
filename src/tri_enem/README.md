# Modulo TRI ENEM

Este e o modulo principal para calculo de notas do ENEM usando TRI.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `simulador.py` | **SimuladorNota** - Interface simplificada (use este!) |
| `calculador.py` | **CalculadorTRI** - Motor de cálculo com ML3 + EAP |
| `calibrador.py` | **Calibrador** - Descoberta de coeficientes via regressão |
| `coeficientes.py` | Carrega coeficientes de `coeficientes_data.json` |
| `coeficientes_data.json` | Coeficientes pré-calibrados (2009-2024) |
| `tradutor.py` | Tratamento especial para LC (múltiplas línguas) |
| `config.py` | Configurações de dificuldade e relatório |
| `relatorios/` | Gerador de relatórios PDF |

## Uso

```python
from tri_enem import SimuladorNota

sim = SimuladorNota()
resultado = sim.calcular('MT', 2023, 'ABCDE...')  # 45 respostas
print(f"Nota: {resultado.nota:.1f}")
```

## Geração de PDF

```python
from tri_enem.relatorios import RelatorioPDF, DadosRelatorio

dados = DadosRelatorio(titulo="Meu Simulado", ano_prova=2024)
# ... adicionar áreas

relatorio = RelatorioPDF()
relatorio.gerar(dados, './relatorios/resultado.pdf')
```

Veja mais exemplos em `examples/`.
