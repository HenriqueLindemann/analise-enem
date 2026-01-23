# Testes de Validação

Scripts para testar a precisão do cálculo TRI contra os microdados reais.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `test_mapeador_provas.py` | Testes unitários do mapeamento YAML |
| `validar_todos_anos.py` | Validação completa 2009-2024 |
| `validar_completo.py` | Validação por área/ano |

## Uso

Execute da raiz do projeto:

```bash
# Testes unitários
pytest tests/test_mapeador_provas.py

# Validação completa (requer microdados_limpos/)
python tests/validar_todos_anos.py
python tests/validar_completo.py
```

## Resultados Esperados

Para provas calibradas:
- **MAE** (Erro Médio Absoluto): < 1 ponto
- **R²**: > 0.999

Provas da 1ª aplicação de anos recentes (2018+) têm maior precisão.
