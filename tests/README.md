# Testes de Validacao

Scripts para testar a precisao do calculo TRI contra os microdados reais.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `validar_todos_anos.py` | Validação completa 2009-2024 |
| `validar_completo.py` | Validação por área/ano |
| `test_module.py` | Teste rápido do módulo |
| `test_lc_50char.py` | Teste específico para LC (50 chars) |
| `teste_final.py` | Teste de notas altas (850+) |

## Uso

Execute da raiz do projeto (requer microdados_limpos/):

```bash
python tests/test_module.py
python tests/validar_completo.py
```

## Resultados Esperados

- MAE (Erro Médio Absoluto): < 0.5 pontos
- R²: > 0.999
