# Mapeamento das Provas na Suite de Validação

Este arquivo lista todas as provas cobertas pela suite de validação, com nomes
legíveis extraídos do `mapeamento_provas.yaml` em vez dos códigos brutos (`CO_PROVA`).

**Fontes de dados:**
- `tests/fixtures/exemplos_microdados.json` — exemplos extraídos dos microdados reais (10 por prova)
- `src/tri_enem/mapeamento_provas.yaml` — mapeamento CO_PROVA → ano/área/tipo/cor
- `src/tri_enem/coeficientes_data.json` — status de calibração e MAE por prova

**Para regenerar este arquivo** (após um novo ciclo de validação):

```bash
python tests/fixtures/gerar_provas_validacao.py
```

Ou, para rodar o pipeline completo do zero:

```bash
python tests/run_full_validation.py \
  --microdados-dir /caminho/para/microdados_inep \
  --n-max 10 --atualizar-status
```

---

## Legenda

### Tipos de Aplicação

| Código YAML | Nome |
|-------------|------|
| `1a_aplicacao` | 1ª Aplicação (aplicação regular) |
| `reaplicacao` | Reaplicação (segunda chance) |
| `digital` | Aplicação Digital (2020+) |
| `segunda_oportunidade` | 2ª Oportunidade |
| `especiais` | Provas especiais (adaptadas, Libras, etc.) |
| `ppl` | Pessoas Privadas de Liberdade |

### Status de Calibração

O status é derivado do MAE (Erro Absoluto Médio) entre nota calculada e nota oficial,
medido sobre os 10 exemplos reais de cada prova.

| Emoji | Status | Critério | Interpretação |
|-------|--------|----------|---------------|
| ✅ | `ok` | MAE ≤ 2 pts | Calibração confiável |
| ℹ️ | `aviso_leve` | 2 < MAE ≤ 5 pts | Boa estimativa, pequena diferença possível |
| ⚠️ | `aviso_forte` | 5 < MAE ≤ 15 pts | Estimativa com margem maior |
| ❌ | `erro_alto` | MAE > 15 pts | Calibração ruim — use com cautela |
| ❌ | `falhou` | Erro na calibração | Coeficientes inválidos ou ausentes |
| ❓ | `desconhecido` | Sem dados suficientes | Não há exemplos válidos para estimar MAE |

> **MAE `-`**: prova com status definido pela calibração (`calibrar_com_mapeamento.py`),
> sem coeficientes lineares em `por_prova` (comum em provas de reaplicação e especiais).

---

## Resumo

| Métrica | Valor |
|---------|-------|
| Anos cobertos | 2009 – 2024 |
| Provas únicas | 580 |
| Exemplos totais | 5800 (10 por prova) |

### Status de Calibração

| Status | Provas |
|--------|--------|
| ok | 503 |
| aviso_leve | 9 |
| aviso_forte | 10 |
| erro_alto | 47 |
| falhou | 8 |
| desconhecido | 3 |

---

## Provas por Ano

Colunas: **CO_PROVA** · **Área** · **Tipo de Aplicação** · **Cor** · **N exemplos** · **Status** · **MAE (pts)**

### 2009

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 49 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 50 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.04 |
| 51 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.04 |
| 52 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.03 |
| 53 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 54 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.05 |
| 55 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.03 |
| 56 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.03 |
| 57 | LC | 1ª Aplicação | amarela | 10 | ❌ erro_alto | 70.73 |
| 58 | LC | 1ª Aplicação | cinza | 10 | ❌ erro_alto | 66.99 |
| 59 | LC | 1ª Aplicação | azul | 10 | ❌ erro_alto | 45.92 |
| 60 | LC | 1ª Aplicação | rosa | 10 | ❌ erro_alto | 57.83 |
| 61 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.16 |
| 62 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.14 |
| 63 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.18 |
| 64 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.15 |
| 65 | CN | Reaplicação | azul | 10 | ✅ ok | - |
| 66 | CN | Reaplicação | amarela | 10 | ✅ ok | - |
| 67 | CN | Reaplicação | branca | 10 | ✅ ok | - |
| 68 | CN | Reaplicação | rosa | 10 | ✅ ok | - |
| 69 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 70 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 71 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 72 | CH | Reaplicação | rosa | 10 | ℹ️ aviso_leve | - |
| 73 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 74 | LC | Reaplicação | cinza | 10 | ✅ ok | - |
| 75 | LC | Reaplicação | azul | 10 | ✅ ok | - |
| 76 | LC | Reaplicação | rosa | 10 | ✅ ok | - |
| 77 | MT | Reaplicação | amarela | 10 | ✅ ok | - |
| 78 | MT | Reaplicação | cinza | 10 | ✅ ok | - |
| 79 | MT | Reaplicação | azul | 10 | ✅ ok | - |
| 80 | MT | Reaplicação | rosa | 10 | ✅ ok | - |
| 81 | CN | Especial | branca_adaptada_ledor | 10 | ❓ desconhecido | - |
| 82 | CH | Especial | branca_adaptada_ledor | 10 | ❓ desconhecido | - |
| 83 | LC | Especial | cinza_adaptada_ledor | 10 | ❌ erro_alto | - |
| 84 | MT | Especial | cinza_adaptada_ledor | 10 | ❓ desconhecido | - |

### 2010

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 85 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 86 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.03 |
| 87 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.03 |
| 88 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.03 |
| 89 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.07 |
| 90 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.07 |
| 91 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.07 |
| 92 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.07 |
| 93 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.10 |
| 94 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.11 |
| 95 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.13 |
| 96 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.14 |
| 97 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.04 |
| 98 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.22 |
| 99 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.04 |
| 100 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.13 |
| 101 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 102 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 103 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 104 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 105 | CN | Reaplicação | azul | 10 | ✅ ok | - |
| 106 | CN | Reaplicação | amarela | 10 | ✅ ok | - |
| 107 | CN | Reaplicação | branca | 10 | ✅ ok | - |
| 108 | CN | Reaplicação | rosa | 10 | ✅ ok | - |

### 2011

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 117 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.13 |
| 118 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | - |
| 119 | CH | 1ª Aplicação | branca | 10 | ✅ ok | - |
| 120 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | - |
| 121 | CN | 1ª Aplicação | azul | 10 | ⚠️ aviso_forte | 16.25 |
| 122 | CN | 1ª Aplicação | amarela | 10 | ❌ erro_alto | - |
| 123 | CN | 1ª Aplicação | branca | 10 | ❌ erro_alto | - |
| 124 | CN | 1ª Aplicação | rosa | 10 | ❌ erro_alto | - |
| 125 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.27 |
| 126 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.30 |
| 127 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.25 |
| 128 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.28 |
| 129 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.14 |
| 130 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.11 |
| 131 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.12 |
| 132 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.09 |

### 2012

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 137 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 138 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.03 |
| 139 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.04 |
| 140 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.03 |
| 141 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.20 |
| 142 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.22 |
| 143 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.19 |
| 144 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.18 |
| 145 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.07 |
| 146 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.07 |
| 147 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.07 |
| 148 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.07 |
| 149 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.05 |
| 150 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.11 |
| 151 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.33 |
| 152 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.06 |
| 153 | CN | Especial | branca_ledor | 10 | ✅ ok | - |
| 154 | CH | Especial | branca_ledor | 10 | ✅ ok | - |
| 155 | LC | Especial | cinza_ledor | 10 | ✅ ok | - |
| 156 | MT | Especial | cinza_ledor | 10 | ✅ ok | - |

### 2013

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 167 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.07 |
| 168 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.06 |
| 169 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.06 |
| 170 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.07 |
| 171 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.06 |
| 172 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.05 |
| 173 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.05 |
| 174 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.06 |
| 175 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.09 |
| 176 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.09 |
| 177 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.08 |
| 178 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.09 |
| 179 | MT | 1ª Aplicação | amarela | 10 | ❌ erro_alto | 18.34 |
| 180 | MT | 1ª Aplicação | cinza | 10 | ❌ erro_alto | 16.86 |
| 181 | MT | 1ª Aplicação | azul | 10 | ❌ erro_alto | 15.53 |
| 182 | MT | 1ª Aplicação | rosa | 10 | ❌ erro_alto | 14.22 |
| 187 | CH | Especial | branca_adaptada_ledor | 10 | ❌ erro_alto | - |
| 188 | CN | Especial | branca_adaptada_ledor | 10 | ❌ erro_alto | - |
| 189 | LC | Especial | cinza_adaptada_ledor | 10 | ❌ erro_alto | - |
| 190 | MT | Especial | cinza_adaptada_ledor | 10 | ❌ erro_alto | - |

### 2014

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 195 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.14 |
| 196 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.15 |
| 197 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.16 |
| 198 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.16 |
| 199 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.09 |
| 200 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.09 |
| 201 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.11 |
| 202 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.11 |
| 203 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.37 |
| 204 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.38 |
| 205 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.38 |
| 206 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.37 |
| 207 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.04 |
| 208 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.04 |
| 209 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.05 |
| 210 | MT | 1ª Aplicação | rosa | 10 | ❌ erro_alto | 0.51 |
| 213 | LC | Reaplicação | cinza | 10 | ✅ ok | - |
| 214 | MT | Reaplicação | cinza | 10 | ✅ ok | - |
| 215 | CH | Especial | branca_adaptada | 10 | ✅ ok | - |
| 216 | CN | Especial | branca_adaptada | 10 | ✅ ok | - |
| 217 | LC | Especial | cinza_adaptada | 10 | ✅ ok | - |
| 218 | MT | Especial | cinza_adaptada | 10 | ❌ erro_alto | - |

### 2015

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 231 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.39 |
| 232 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.41 |
| 233 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.40 |
| 234 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.40 |
| 235 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.18 |
| 236 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.20 |
| 237 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.17 |
| 238 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.19 |
| 239 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.28 |
| 240 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.27 |
| 241 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.29 |
| 242 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.23 |
| 243 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.04 |
| 244 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.03 |
| 245 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 246 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.22 |
| 251 | CH | Especial | branca_adaptada | 10 | ✅ ok | - |
| 252 | CN | Especial | branca_adaptada | 10 | ⚠️ aviso_forte | - |
| 253 | LC | Especial | cinza_adaptada | 10 | ✅ ok | - |
| 254 | MT | Especial | cinza_adaptada | 10 | ✅ ok | - |
| 271 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 272 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 273 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 274 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 275 | CN | Reaplicação | azul | 10 | ✅ ok | - |
| 276 | CN | Reaplicação | amarela | 10 | ✅ ok | - |
| 277 | CN | Reaplicação | branca | 10 | ✅ ok | - |
| 278 | CN | Reaplicação | rosa | 10 | ✅ ok | - |
| 279 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 280 | LC | Reaplicação | cinza | 10 | ✅ ok | - |
| 281 | LC | Reaplicação | azul | 10 | ✅ ok | - |
| 282 | LC | Reaplicação | rosa | 10 | ✅ ok | - |
| 283 | MT | Reaplicação | amarela | 10 | ✅ ok | - |
| 284 | MT | Reaplicação | cinza | 10 | ✅ ok | - |
| 285 | MT | Reaplicação | azul | 10 | ✅ ok | - |
| 286 | MT | Reaplicação | rosa | 10 | ✅ ok | - |

### 2016

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 291 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.24 |
| 292 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.17 |
| 293 | CN | 1ª Aplicação | branca | 10 | ✅ ok | 0.19 |
| 294 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.21 |
| 295 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.22 |
| 296 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.12 |
| 297 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.13 |
| 298 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.12 |
| 299 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.35 |
| 300 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.36 |
| 301 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.33 |
| 302 | LC | 1ª Aplicação | cinza | 10 | ✅ ok | 0.33 |
| 303 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 304 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.10 |
| 305 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 1.06 |
| 306 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.06 |
| 307 | CN | Especial | branca_adaptada | 10 | ✅ ok | - |
| 308 | CH | Especial | branca_adaptada | 10 | ✅ ok | - |
| 309 | LC | Especial | cinza_adaptada | 10 | ✅ ok | - |
| 310 | MT | Especial | cinza_adaptada | 10 | ✅ ok | - |
| 331 | CN | Reaplicação | azul | 10 | ℹ️ aviso_leve | - |
| 332 | CN | Reaplicação | amarela | 10 | ℹ️ aviso_leve | - |
| 333 | CN | Reaplicação | branca | 10 | ℹ️ aviso_leve | - |
| 336 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 337 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 338 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 351 | CN | reaplicacao_2 | azul | 10 | ✅ ok | 2.07 |
| 352 | CN | reaplicacao_2 | amarela | 10 | ✅ ok | 2.00 |
| 353 | CN | reaplicacao_2 | branca | 10 | ℹ️ aviso_leve | 2.77 |
| 354 | CN | reaplicacao_2 | rosa | 10 | ℹ️ aviso_leve | 2.88 |
| 356 | CH | reaplicacao_2 | azul | 10 | ✅ ok | 0.17 |
| 357 | CH | reaplicacao_2 | amarela | 10 | ✅ ok | 0.14 |
| 358 | CH | reaplicacao_2 | branca | 10 | ✅ ok | 0.18 |
| 359 | CH | reaplicacao_2 | rosa | 10 | ✅ ok | 0.09 |
| 361 | LC | reaplicacao_2 | azul | 10 | ✅ ok | 0.14 |
| 362 | LC | reaplicacao_2 | amarela | 10 | ✅ ok | 0.12 |
| 363 | LC | reaplicacao_2 | rosa | 10 | ✅ ok | 0.10 |
| 364 | LC | reaplicacao_2 | cinza | 10 | ✅ ok | 0.11 |
| 366 | MT | reaplicacao_2 | azul | 10 | ✅ ok | 0.19 |
| 367 | MT | reaplicacao_2 | amarela | 10 | ✅ ok | 0.15 |
| 368 | MT | reaplicacao_2 | rosa | 10 | ✅ ok | 0.10 |
| 369 | MT | reaplicacao_2 | cinza | 10 | ✅ ok | 0.09 |

### 2017

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 391 | CN | 1ª Aplicação | azul | 10 | ❌ erro_alto | - |
| 392 | CN | 1ª Aplicação | amarela | 10 | ❌ erro_alto | - |
| 393 | CN | 1ª Aplicação | cinza | 10 | ❌ erro_alto | - |
| 394 | CN | 1ª Aplicação | rosa | 10 | ❌ erro_alto | - |
| 395 | CH | 1ª Aplicação | azul | 10 | ❌ erro_alto | - |
| 396 | CH | 1ª Aplicação | amarela | 10 | ❌ erro_alto | - |
| 397 | CH | 1ª Aplicação | branca | 10 | ❌ erro_alto | - |
| 398 | CH | 1ª Aplicação | rosa | 10 | ❌ erro_alto | - |
| 399 | LC | 1ª Aplicação | azul | 10 | ✅ ok | - |
| 400 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | - |
| 401 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | - |
| 402 | LC | 1ª Aplicação | branca | 10 | ✅ ok | - |
| 403 | MT | 1ª Aplicação | azul | 10 | ❌ erro_alto | - |
| 404 | MT | 1ª Aplicação | amarela | 10 | ❌ erro_alto | - |
| 405 | MT | 1ª Aplicação | rosa | 10 | ❌ erro_alto | - |
| 406 | MT | 1ª Aplicação | cinza | 10 | ❌ erro_alto | - |
| 407 | CN | Especial | laranja_adaptada_ledor | 10 | ❌ erro_alto | - |
| 408 | CH | Especial | laranja_adaptada_ledor | 10 | ❌ erro_alto | - |
| 409 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 410 | MT | Especial | laranja_adaptada_ledor | 10 | ❌ erro_alto | - |
| 411 | CN | Especial | verde_videoprova_libras | 10 | ℹ️ aviso_leve | - |
| 412 | CH | Especial | verde_videoprova_libras | 10 | ℹ️ aviso_leve | - |
| 413 | LC | Especial | verde_videoprova_libras | 10 | ℹ️ aviso_leve | - |
| 414 | MT | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 435 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 436 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 437 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 438 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 439 | LC | Reaplicação | azul | 10 | ✅ ok | - |
| 440 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 441 | LC | Reaplicação | branca | 10 | ✅ ok | - |
| 442 | LC | Reaplicação | rosa | 10 | ✅ ok | - |

### 2018

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 447 | CN | 1ª Aplicação | azul | 10 | ⚠️ aviso_forte | 9.95 |
| 448 | CN | 1ª Aplicação | amarela | 10 | ⚠️ aviso_forte | 8.64 |
| 449 | CN | 1ª Aplicação | cinza | 10 | ⚠️ aviso_forte | 9.17 |
| 450 | CN | 1ª Aplicação | rosa | 10 | ⚠️ aviso_forte | 10.72 |
| 451 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 1.33 |
| 452 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 1.32 |
| 453 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 1.23 |
| 454 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 1.30 |
| 455 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.21 |
| 456 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.25 |
| 457 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.25 |
| 458 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.22 |
| 459 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.18 |
| 460 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.17 |
| 461 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.16 |
| 462 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.15 |
| 463 | CN | Especial | laranja_adaptada_ledor | 10 | ⚠️ aviso_forte | - |
| 464 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 465 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 466 | MT | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 467 | CN | Especial | verde_videoprova_libras | 10 | ⚠️ aviso_forte | - |
| 468 | CH | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 469 | LC | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 470 | MT | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 491 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 492 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 493 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 494 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 495 | LC | Reaplicação | azul | 10 | ✅ ok | - |
| 496 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 497 | LC | Reaplicação | branca | 10 | ✅ ok | - |
| 498 | LC | Reaplicação | rosa | 10 | ✅ ok | - |

### 2019

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 503 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.08 |
| 504 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.07 |
| 505 | CN | 1ª Aplicação | cinza | 10 | ✅ ok | 0.07 |
| 506 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.08 |
| 507 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.22 |
| 508 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.17 |
| 509 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.21 |
| 510 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.21 |
| 511 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.92 |
| 512 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.74 |
| 513 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.84 |
| 514 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.90 |
| 515 | MT | 1ª Aplicação | azul | 10 | ❌ erro_alto | 25.90 |
| 516 | MT | 1ª Aplicação | amarela | 10 | ❌ erro_alto | 24.27 |
| 517 | MT | 1ª Aplicação | rosa | 10 | ❌ erro_alto | 23.44 |
| 518 | MT | 1ª Aplicação | cinza | 10 | ❌ erro_alto | 26.09 |
| 519 | CN | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 520 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 521 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 522 | MT | Especial | laranja_adaptada_ledor | 10 | ❌ erro_alto | - |
| 523 | CN | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 524 | CH | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 525 | LC | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 526 | MT | Especial | verde_videoprova_libras | 10 | ❌ erro_alto | - |

### 2020

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 567 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.31 |
| 568 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.26 |
| 569 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.24 |
| 570 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.29 |
| 574 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 575 | CH | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 577 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.05 |
| 578 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.04 |
| 579 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.04 |
| 580 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.05 |
| 584 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 585 | LC | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 587 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.09 |
| 588 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.10 |
| 589 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.10 |
| 590 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.09 |
| 594 | MT | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 595 | MT | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 597 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.16 |
| 598 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.14 |
| 599 | CN | 1ª Aplicação | cinza | 10 | ✅ ok | 0.16 |
| 600 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.15 |
| 604 | CN | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 605 | CN | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 647 | CH | Reaplicação | azul | 10 | ✅ ok | 0.42 |
| 648 | CH | Reaplicação | amarela | 10 | ✅ ok | 0.20 |
| 649 | CH | Reaplicação | branca | 10 | ✅ ok | 0.25 |
| 650 | CH | Reaplicação | rosa | 10 | ✅ ok | 0.26 |
| 657 | LC | Reaplicação | azul | 10 | ✅ ok | 0.14 |
| 658 | LC | Reaplicação | amarela | 10 | ✅ ok | 0.13 |
| 659 | LC | Reaplicação | rosa | 10 | ✅ ok | 0.18 |
| 660 | LC | Reaplicação | branca | 10 | ✅ ok | 0.17 |
| 667 | MT | Reaplicação | azul | 10 | ✅ ok | 0.03 |
| 668 | MT | Reaplicação | amarela | 10 | ✅ ok | 0.04 |
| 669 | MT | Reaplicação | rosa | 10 | ✅ ok | 0.04 |
| 670 | MT | Reaplicação | cinza | 10 | ✅ ok | 0.06 |
| 677 | CN | Reaplicação | azul | 10 | ✅ ok | 0.15 |
| 678 | CN | Reaplicação | amarela | 10 | ✅ ok | 0.07 |
| 679 | CN | Reaplicação | cinza | 10 | ✅ ok | 0.08 |
| 680 | CN | Reaplicação | rosa | 10 | ✅ ok | 0.15 |
| 687 | CH | Digital | azul | 10 | ✅ ok | 0.22 |
| 688 | CH | Digital | amarela | 10 | ✅ ok | 0.29 |
| 689 | CH | Digital | branca | 10 | ✅ ok | 0.20 |
| 690 | CH | Digital | rosa | 10 | ✅ ok | 0.17 |
| 691 | LC | Digital | azul | 10 | ❌ erro_alto | 39.60 |
| 692 | LC | Digital | amarela | 10 | ❌ erro_alto | 36.15 |
| 693 | LC | Digital | branca | 10 | ❌ erro_alto | 36.72 |
| 694 | LC | Digital | rosa | 10 | ❌ erro_alto | 34.64 |
| 695 | MT | Digital | azul | 10 | ✅ ok | 0.18 |
| 696 | MT | Digital | amarela | 10 | ✅ ok | 0.43 |
| 697 | MT | Digital | rosa | 10 | ✅ ok | 0.10 |
| 698 | MT | Digital | cinza | 10 | ✅ ok | 0.18 |
| 699 | CN | Digital | azul | 10 | ✅ ok | 0.18 |
| 700 | CN | Digital | amarela | 10 | ✅ ok | 0.22 |
| 701 | CN | Digital | rosa | 10 | ✅ ok | 0.15 |
| 702 | CN | Digital | cinza | 10 | ✅ ok | 0.16 |

### 2021

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 879 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.19 |
| 880 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.23 |
| 881 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.22 |
| 882 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.20 |
| 886 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 887 | CH | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 889 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.09 |
| 890 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.09 |
| 891 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.10 |
| 892 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.08 |
| 896 | LC | Especial | laranja_adaptada_ledor | 10 | ⚠️ aviso_forte | - |
| 897 | LC | Especial | verde_videoprova_libras | 10 | ⚠️ aviso_forte | - |
| 899 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.14 |
| 900 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.13 |
| 901 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.14 |
| 902 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.13 |
| 906 | MT | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 907 | MT | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 909 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.14 |
| 910 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.14 |
| 911 | CN | 1ª Aplicação | cinza | 10 | ✅ ok | 0.13 |
| 912 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.15 |
| 916 | CN | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 917 | CN | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 959 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 960 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 961 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 962 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 969 | LC | Reaplicação | azul | 10 | ✅ ok | - |
| 970 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 971 | LC | Reaplicação | rosa | 10 | ✅ ok | - |
| 972 | LC | Reaplicação | branca | 10 | ✅ ok | - |
| 979 | MT | Reaplicação | azul | 10 | ✅ ok | - |
| 980 | MT | Reaplicação | amarela | 10 | ✅ ok | - |
| 981 | MT | Reaplicação | rosa | 10 | ✅ ok | - |
| 982 | MT | Reaplicação | cinza | 10 | ✅ ok | - |
| 989 | CN | Reaplicação | azul | 10 | ✅ ok | - |
| 990 | CN | Reaplicação | amarela | 10 | ✅ ok | - |
| 991 | CN | Reaplicação | cinza | 10 | ✅ ok | - |
| 992 | CN | Reaplicação | rosa | 10 | ✅ ok | - |
| 999 | CH | Digital | azul | 10 | ✅ ok | 0.14 |
| 1000 | CH | Digital | amarela | 10 | ✅ ok | 0.17 |
| 1001 | CH | Digital | branca | 10 | ✅ ok | 0.18 |
| 1002 | CH | Digital | rosa | 10 | ✅ ok | 0.24 |
| 1003 | LC | Digital | azul | 10 | ✅ ok | 0.06 |
| 1004 | LC | Digital | amarela | 10 | ✅ ok | 0.10 |
| 1005 | LC | Digital | branca | 10 | ✅ ok | 0.08 |
| 1006 | LC | Digital | rosa | 10 | ✅ ok | 0.09 |
| 1007 | MT | Digital | azul | 10 | ✅ ok | 0.08 |
| 1008 | MT | Digital | amarela | 10 | ✅ ok | 0.07 |
| 1009 | MT | Digital | rosa | 10 | ✅ ok | 0.44 |
| 1010 | MT | Digital | cinza | 10 | ✅ ok | 0.08 |
| 1011 | CN | Digital | azul | 10 | ✅ ok | 0.06 |
| 1012 | CN | Digital | amarela | 10 | ✅ ok | 0.06 |
| 1013 | CN | Digital | rosa | 10 | ✅ ok | 0.09 |
| 1014 | CN | Digital | cinza | 10 | ✅ ok | 0.07 |
| 1015 | CH | 2ª Oportunidade | azul | 10 | ✅ ok | - |
| 1016 | CH | 2ª Oportunidade | amarela | 10 | ✅ ok | - |
| 1017 | CH | 2ª Oportunidade | branca | 10 | ✅ ok | - |
| 1018 | CH | 2ª Oportunidade | rosa | 10 | ✅ ok | - |
| 1025 | LC | 2ª Oportunidade | azul | 10 | ✅ ok | - |
| 1026 | LC | 2ª Oportunidade | amarela | 10 | ✅ ok | - |
| 1027 | LC | 2ª Oportunidade | rosa | 10 | ✅ ok | - |
| 1028 | LC | 2ª Oportunidade | branca | 10 | ✅ ok | - |
| 1035 | MT | 2ª Oportunidade | azul | 10 | ✅ ok | - |
| 1036 | MT | 2ª Oportunidade | amarela | 10 | ✅ ok | - |
| 1037 | MT | 2ª Oportunidade | cinza | 10 | ✅ ok | - |
| 1038 | MT | 2ª Oportunidade | rosa | 10 | ✅ ok | - |
| 1045 | CN | 2ª Oportunidade | azul | 10 | ✅ ok | - |
| 1046 | CN | 2ª Oportunidade | amarela | 10 | ✅ ok | - |
| 1047 | CN | 2ª Oportunidade | cinza | 10 | ✅ ok | - |
| 1048 | CN | 2ª Oportunidade | rosa | 10 | ✅ ok | - |

### 2022

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1055 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.29 |
| 1056 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.24 |
| 1057 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.29 |
| 1058 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.30 |
| 1062 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1063 | CH | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1065 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.06 |
| 1066 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.07 |
| 1067 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.06 |
| 1068 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.06 |
| 1072 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1073 | LC | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1075 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.03 |
| 1076 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.05 |
| 1077 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.05 |
| 1078 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.06 |
| 1082 | MT | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1083 | MT | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1085 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.11 |
| 1086 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.13 |
| 1087 | CN | 1ª Aplicação | cinza | 10 | ✅ ok | 0.15 |
| 1088 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.12 |
| 1092 | CN | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1093 | CN | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1135 | CH | Reaplicação | azul | 10 | ✅ ok | - |
| 1136 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 1137 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 1138 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 1145 | LC | Reaplicação | azul | 10 | ✅ ok | - |
| 1146 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 1147 | LC | Reaplicação | rosa | 10 | ✅ ok | - |
| 1148 | LC | Reaplicação | branca | 10 | ✅ ok | - |
| 1155 | MT | Reaplicação | azul | 10 | ✅ ok | - |
| 1156 | MT | Reaplicação | amarela | 10 | ✅ ok | - |
| 1157 | MT | Reaplicação | rosa | 10 | ✅ ok | - |
| 1158 | MT | Reaplicação | cinza | 10 | ✅ ok | - |
| 1165 | CN | Reaplicação | azul | 10 | ✅ ok | - |
| 1166 | CN | Reaplicação | amarela | 10 | ✅ ok | - |
| 1167 | CN | Reaplicação | cinza | 10 | ✅ ok | - |
| 1168 | CN | Reaplicação | rosa | 10 | ✅ ok | - |
| 1175 | CH | Digital | azul | 10 | ✅ ok | 0.24 |
| 1176 | CH | Digital | amarela | 10 | ✅ ok | 0.20 |
| 1177 | CH | Digital | branca | 10 | ✅ ok | 0.19 |
| 1178 | CH | Digital | rosa | 10 | ✅ ok | 0.25 |
| 1179 | LC | Digital | azul | 10 | ✅ ok | 0.09 |
| 1180 | LC | Digital | amarela | 10 | ✅ ok | 0.06 |
| 1181 | LC | Digital | branca | 10 | ✅ ok | 0.06 |
| 1182 | LC | Digital | rosa | 10 | ✅ ok | 0.06 |
| 1183 | MT | Digital | azul | 10 | ✅ ok | 0.03 |
| 1184 | MT | Digital | amarela | 10 | ✅ ok | 0.04 |
| 1185 | MT | Digital | rosa | 10 | ✅ ok | 0.03 |
| 1186 | MT | Digital | cinza | 10 | ✅ ok | 0.03 |
| 1187 | CN | Digital | azul | 10 | ✅ ok | 0.07 |
| 1188 | CN | Digital | amarela | 10 | ✅ ok | 0.06 |
| 1189 | CN | Digital | rosa | 10 | ✅ ok | 0.08 |
| 1190 | CN | Digital | cinza | 10 | ✅ ok | 0.06 |

### 2023

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1191 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.30 |
| 1192 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.31 |
| 1193 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.31 |
| 1194 | CH | 1ª Aplicação | rosa | 10 | ✅ ok | 0.30 |
| 1195 | CH | Especial | rosa_ampliada | 10 | ✅ ok | - |
| 1196 | CH | Especial | rosa_superampliada | 10 | ✅ ok | - |
| 1197 | CH | Especial | laranja_braille | 10 | ✅ ok | - |
| 1198 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1199 | CH | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1201 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.10 |
| 1202 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.09 |
| 1203 | LC | 1ª Aplicação | rosa | 10 | ✅ ok | 0.10 |
| 1204 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.11 |
| 1205 | LC | Especial | rosa_ampliada | 10 | ✅ ok | - |
| 1206 | LC | Especial | rosa_superampliada | 10 | ✅ ok | - |
| 1207 | LC | Especial | laranja_braille | 10 | ✅ ok | - |
| 1208 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1209 | LC | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1211 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.09 |
| 1212 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.13 |
| 1213 | MT | 1ª Aplicação | rosa | 10 | ✅ ok | 0.14 |
| 1214 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.09 |
| 1215 | MT | Especial | rosa_ampliada | 10 | ❌ erro_alto | - |
| 1216 | MT | Especial | rosa_superampliada | 10 | ✅ ok | - |
| 1217 | MT | Especial | laranja_braille | 10 | ✅ ok | - |
| 1218 | MT | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1219 | MT | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1221 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.31 |
| 1222 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.29 |
| 1223 | CN | 1ª Aplicação | rosa | 10 | ✅ ok | 0.29 |
| 1224 | CN | 1ª Aplicação | cinza | 10 | ✅ ok | 0.32 |
| 1225 | CN | Especial | rosa_ampliada | 10 | ❌ erro_alto | - |
| 1226 | CN | Especial | rosa_superampliada | 10 | ✅ ok | - |
| 1227 | CN | Especial | laranja_braille | 10 | ✅ ok | - |
| 1228 | CN | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1229 | CN | Especial | verde_videoprova_libras | 10 | ✅ ok | - |
| 1271 | CH | Reaplicação | azul | 10 | ❌ erro_alto | - |
| 1272 | CH | Reaplicação | amarela | 10 | ✅ ok | - |
| 1273 | CH | Reaplicação | branca | 10 | ✅ ok | - |
| 1274 | CH | Reaplicação | rosa | 10 | ✅ ok | - |
| 1281 | LC | Reaplicação | azul | 10 | ❌ erro_alto | - |
| 1282 | LC | Reaplicação | amarela | 10 | ✅ ok | - |
| 1283 | LC | Reaplicação | rosa | 10 | ✅ ok | - |
| 1284 | LC | Reaplicação | branca | 10 | ✅ ok | - |
| 1291 | MT | Reaplicação | azul | 10 | ✅ ok | - |
| 1292 | MT | Reaplicação | amarela | 10 | ✅ ok | - |
| 1293 | MT | Reaplicação | rosa | 10 | ✅ ok | - |
| 1294 | MT | Reaplicação | cinza | 10 | ✅ ok | - |
| 1301 | CN | Reaplicação | azul | 10 | ✅ ok | - |
| 1302 | CN | Reaplicação | amarela | 10 | ✅ ok | - |
| 1303 | CN | Reaplicação | cinza | 10 | ✅ ok | - |
| 1304 | CN | Reaplicação | rosa | 10 | ✅ ok | - |

### 2024

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1363 | MT | Reaplicação | azul | 10 | ❌ falhou | - |
| 1364 | MT | Reaplicação | amarela | 10 | ❌ falhou | - |
| 1365 | MT | Reaplicação | verde | 10 | ❌ falhou | - |
| 1366 | MT | Reaplicação | cinza | 10 | ❌ falhou | - |
| 1373 | CN | Reaplicação | azul | 10 | ❌ falhou | - |
| 1374 | CN | Reaplicação | amarela | 10 | ❌ falhou | - |
| 1375 | CN | Reaplicação | cinza | 10 | ❌ falhou | - |
| 1376 | CN | Reaplicação | verde | 10 | ❌ falhou | - |
| 1383 | CH | 1ª Aplicação | azul | 10 | ✅ ok | 0.19 |
| 1384 | CH | 1ª Aplicação | amarela | 10 | ✅ ok | 0.15 |
| 1385 | CH | 1ª Aplicação | branca | 10 | ✅ ok | 0.18 |
| 1386 | CH | 1ª Aplicação | verde | 10 | ✅ ok | 0.18 |
| 1387 | CH | Especial | verde_ampliada | 10 | ✅ ok | - |
| 1388 | CH | Especial | verde_superampliada | 10 | ✅ ok | - |
| 1390 | CH | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1391 | CH | Especial | roxa_videoprova_libras | 10 | ✅ ok | - |
| 1395 | LC | 1ª Aplicação | azul | 10 | ✅ ok | 0.64 |
| 1396 | LC | 1ª Aplicação | amarela | 10 | ✅ ok | 0.55 |
| 1397 | LC | 1ª Aplicação | verde | 10 | ✅ ok | 0.59 |
| 1398 | LC | 1ª Aplicação | branca | 10 | ✅ ok | 0.59 |
| 1399 | LC | Especial | verde_ampliada | 10 | ✅ ok | - |
| 1400 | LC | Especial | verde_superampliada | 10 | ✅ ok | - |
| 1402 | LC | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1403 | LC | Especial | roxa_videoprova_libras | 10 | ✅ ok | - |
| 1407 | MT | 1ª Aplicação | azul | 10 | ✅ ok | 0.23 |
| 1408 | MT | 1ª Aplicação | amarela | 10 | ✅ ok | 0.20 |
| 1409 | MT | 1ª Aplicação | verde | 10 | ✅ ok | 0.24 |
| 1410 | MT | 1ª Aplicação | cinza | 10 | ✅ ok | 0.21 |
| 1411 | MT | Especial | verde_ampliada | 10 | ✅ ok | - |
| 1412 | MT | Especial | verde_superampliada | 10 | ✅ ok | - |
| 1414 | MT | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1415 | MT | Especial | roxa_videoprova_libras | 10 | ✅ ok | - |
| 1419 | CN | 1ª Aplicação | azul | 10 | ✅ ok | 0.20 |
| 1420 | CN | 1ª Aplicação | amarela | 10 | ✅ ok | 0.20 |
| 1421 | CN | 1ª Aplicação | verde | 10 | ✅ ok | 0.20 |
| 1422 | CN | 1ª Aplicação | cinza | 10 | ✅ ok | 0.18 |
| 1423 | CN | Especial | verde_ampliada | 10 | ✅ ok | - |
| 1424 | CN | Especial | verde_superampliada | 10 | ✅ ok | - |
| 1426 | CN | Especial | laranja_adaptada_ledor | 10 | ✅ ok | - |
| 1427 | CN | Especial | roxa_videoprova_libras | 10 | ✅ ok | - |
