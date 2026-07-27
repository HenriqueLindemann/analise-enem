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

| Status | Critério | Interpretação |
|--------|----------|---------------|
| `ok` | MAE ≤ 2 pts | Calibração confiável |
| `aviso_leve` | 2 < MAE ≤ 5 pts | Boa estimativa, pequena diferença possível |
| `aviso_forte` | 5 < MAE ≤ 15 pts | Estimativa com margem maior |
| `erro_alto` | MAE > 15 pts | Calibração ruim — use com cautela |
| `falhou` | Erro na calibração | Coeficientes inválidos ou ausentes |
| `desconhecido` | Sem dados suficientes | Não há exemplos válidos para estimar MAE |

> **MAE `-`**: prova com status definido pela calibração (`calibrar_com_mapeamento.py`),
> sem coeficientes lineares em `por_prova` (comum em provas de reaplicação e especiais).

---

## Resumo

| Métrica | Valor |
|---------|-------|
| Anos cobertos | 2009 – 2025 |
| Provas únicas | 630 |
| Exemplos totais | 6300 (10 por prova) |

### Status de Calibração

| Status | Provas |
|--------|--------|
| ok | 556 |
| aviso_leve | 17 |
| aviso_forte | 13 |
| erro_alto | 41 |
| desconhecido | 3 |

---

## Provas por Ano

Colunas: **CO_PROVA** · **Área** · **Tipo de Aplicação** · **Cor** · **N exemplos** · **Status** · **MAE (pts)**

### 2009

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 49 | CN | 1ª Aplicação | azul | 10 | ok | 0.07 |
| 50 | CN | 1ª Aplicação | amarela | 10 | ok | 0.03 |
| 51 | CN | 1ª Aplicação | branca | 10 | ok | 0.06 |
| 52 | CN | 1ª Aplicação | rosa | 10 | ok | 0.23 |
| 53 | CH | 1ª Aplicação | azul | 10 | ok | 0.04 |
| 54 | CH | 1ª Aplicação | amarela | 10 | ok | 0.04 |
| 55 | CH | 1ª Aplicação | branca | 10 | ok | 0.03 |
| 56 | CH | 1ª Aplicação | rosa | 10 | ok | 0.05 |
| 57 | LC | 1ª Aplicação | amarela | 10 | ok | 0.10 |
| 58 | LC | 1ª Aplicação | cinza | 10 | ok | 0.14 |
| 59 | LC | 1ª Aplicação | azul | 10 | ok | 0.03 |
| 60 | LC | 1ª Aplicação | rosa | 10 | ok | 0.04 |
| 61 | MT | 1ª Aplicação | amarela | 10 | ok | 0.23 |
| 62 | MT | 1ª Aplicação | cinza | 10 | ok | 0.18 |
| 63 | MT | 1ª Aplicação | azul | 10 | ok | 0.22 |
| 64 | MT | 1ª Aplicação | rosa | 10 | ok | 0.25 |
| 65 | CN | Reaplicação | azul | 10 | ok | 0.04 |
| 66 | CN | Reaplicação | amarela | 10 | ok | 0.03 |
| 67 | CN | Reaplicação | branca | 10 | ok | 0.03 |
| 68 | CN | Reaplicação | rosa | 10 | ok | 0.03 |
| 69 | CH | Reaplicação | azul | 10 | ok | 0.03 |
| 70 | CH | Reaplicação | amarela | 10 | ok | 0.03 |
| 71 | CH | Reaplicação | branca | 10 | ok | 0.03 |
| 72 | CH | Reaplicação | rosa | 10 | ok | 3.81 |
| 73 | LC | Reaplicação | amarela | 10 | ok | 0.03 |
| 74 | LC | Reaplicação | cinza | 10 | ok | 0.03 |
| 75 | LC | Reaplicação | azul | 10 | ok | 0.03 |
| 76 | LC | Reaplicação | rosa | 10 | ok | 0.04 |
| 77 | MT | Reaplicação | amarela | 10 | ok | 0.05 |
| 78 | MT | Reaplicação | cinza | 10 | ok | 0.05 |
| 79 | MT | Reaplicação | azul | 10 | ok | 0.05 |
| 80 | MT | Reaplicação | rosa | 10 | ok | 0.04 |
| 81 | CN | Especial | branca_adaptada_ledor | 10 | desconhecido | - |
| 82 | CH | Especial | branca_adaptada_ledor | 10 | desconhecido | - |
| 83 | LC | Especial | cinza_adaptada_ledor | 10 | erro_alto | - |
| 84 | MT | Especial | cinza_adaptada_ledor | 10 | desconhecido | - |

### 2010

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 85 | CH | 1ª Aplicação | azul | 10 | ok | 0.03 |
| 86 | CH | 1ª Aplicação | amarela | 10 | ok | 0.05 |
| 87 | CH | 1ª Aplicação | branca | 10 | ok | 0.03 |
| 88 | CH | 1ª Aplicação | rosa | 10 | ok | 0.05 |
| 89 | CN | 1ª Aplicação | azul | 10 | ok | 0.06 |
| 90 | CN | 1ª Aplicação | amarela | 10 | ok | 0.07 |
| 91 | CN | 1ª Aplicação | branca | 10 | ok | 0.07 |
| 92 | CN | 1ª Aplicação | rosa | 10 | ok | 0.07 |
| 93 | LC | 1ª Aplicação | amarela | 10 | ok | 0.08 |
| 94 | LC | 1ª Aplicação | cinza | 10 | ok | 0.08 |
| 95 | LC | 1ª Aplicação | azul | 10 | ok | 0.10 |
| 96 | LC | 1ª Aplicação | rosa | 10 | ok | 0.09 |
| 97 | MT | 1ª Aplicação | amarela | 10 | ok | 0.15 |
| 98 | MT | 1ª Aplicação | cinza | 10 | ok | 0.33 |
| 99 | MT | 1ª Aplicação | azul | 10 | ok | 0.29 |
| 100 | MT | 1ª Aplicação | rosa | 10 | ok | 0.06 |
| 101 | CH | Reaplicação | azul | 10 | ok | 0.04 |
| 102 | CH | Reaplicação | amarela | 10 | ok | 0.03 |
| 103 | CH | Reaplicação | branca | 10 | ok | 0.03 |
| 104 | CH | Reaplicação | rosa | 10 | ok | 0.02 |
| 105 | CN | Reaplicação | azul | 10 | ok | 0.43 |
| 106 | CN | Reaplicação | amarela | 10 | ok | 0.50 |
| 107 | CN | Reaplicação | branca | 10 | ok | 0.49 |
| 108 | CN | Reaplicação | rosa | 10 | ok | 0.57 |

### 2011

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 117 | CH | 1ª Aplicação | azul | 10 | ok | 0.14 |
| 118 | CH | 1ª Aplicação | amarela | 10 | ok | 0.18 |
| 119 | CH | 1ª Aplicação | branca | 10 | ok | 0.13 |
| 120 | CH | 1ª Aplicação | rosa | 10 | ok | 0.15 |
| 121 | CN | 1ª Aplicação | azul | 10 | aviso_forte | 16.25 |
| 122 | CN | 1ª Aplicação | amarela | 10 | erro_alto | - |
| 123 | CN | 1ª Aplicação | branca | 10 | erro_alto | - |
| 124 | CN | 1ª Aplicação | rosa | 10 | erro_alto | - |
| 125 | LC | 1ª Aplicação | amarela | 10 | ok | 0.28 |
| 126 | LC | 1ª Aplicação | cinza | 10 | ok | 0.25 |
| 127 | LC | 1ª Aplicação | azul | 10 | ok | 0.23 |
| 128 | LC | 1ª Aplicação | rosa | 10 | ok | 0.25 |
| 129 | MT | 1ª Aplicação | amarela | 10 | ok | 0.09 |
| 130 | MT | 1ª Aplicação | cinza | 10 | ok | 0.14 |
| 131 | MT | 1ª Aplicação | azul | 10 | ok | 0.11 |
| 132 | MT | 1ª Aplicação | rosa | 10 | ok | 0.11 |

### 2012

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 137 | CH | 1ª Aplicação | azul | 10 | ok | 0.03 |
| 138 | CH | 1ª Aplicação | amarela | 10 | ok | 0.03 |
| 139 | CH | 1ª Aplicação | branca | 10 | ok | 0.03 |
| 140 | CH | 1ª Aplicação | rosa | 10 | ok | 0.03 |
| 141 | CN | 1ª Aplicação | azul | 10 | ok | 0.17 |
| 142 | CN | 1ª Aplicação | amarela | 10 | ok | 0.17 |
| 143 | CN | 1ª Aplicação | branca | 10 | ok | 0.24 |
| 144 | CN | 1ª Aplicação | rosa | 10 | ok | 0.16 |
| 145 | LC | 1ª Aplicação | amarela | 10 | ok | 0.07 |
| 146 | LC | 1ª Aplicação | cinza | 10 | ok | 0.06 |
| 147 | LC | 1ª Aplicação | azul | 10 | ok | 0.06 |
| 148 | LC | 1ª Aplicação | rosa | 10 | ok | 0.07 |
| 149 | MT | 1ª Aplicação | amarela | 10 | ok | 0.06 |
| 150 | MT | 1ª Aplicação | cinza | 10 | ok | 0.05 |
| 151 | MT | 1ª Aplicação | azul | 10 | ok | 0.06 |
| 152 | MT | 1ª Aplicação | rosa | 10 | ok | 0.08 |
| 153 | CN | Especial | branca_ledor | 10 | ok | - |
| 154 | CH | Especial | branca_ledor | 10 | ok | - |
| 155 | LC | Especial | cinza_ledor | 10 | ok | - |
| 156 | MT | Especial | cinza_ledor | 10 | ok | - |

### 2013

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 167 | CH | 1ª Aplicação | azul | 10 | ok | 0.09 |
| 168 | CH | 1ª Aplicação | amarela | 10 | ok | 0.07 |
| 169 | CH | 1ª Aplicação | branca | 10 | ok | 0.06 |
| 170 | CH | 1ª Aplicação | rosa | 10 | ok | 0.08 |
| 171 | CN | 1ª Aplicação | azul | 10 | ok | 0.19 |
| 172 | CN | 1ª Aplicação | amarela | 10 | ok | 0.16 |
| 173 | CN | 1ª Aplicação | branca | 10 | ok | 0.21 |
| 174 | CN | 1ª Aplicação | rosa | 10 | ok | 0.21 |
| 175 | LC | 1ª Aplicação | amarela | 10 | ok | 0.08 |
| 176 | LC | 1ª Aplicação | cinza | 10 | ok | 0.08 |
| 177 | LC | 1ª Aplicação | azul | 10 | ok | 0.07 |
| 178 | LC | 1ª Aplicação | rosa | 10 | ok | 0.08 |
| 179 | MT | 1ª Aplicação | amarela | 10 | erro_alto | 13.97 |
| 180 | MT | 1ª Aplicação | cinza | 10 | erro_alto | 14.42 |
| 181 | MT | 1ª Aplicação | azul | 10 | erro_alto | 14.24 |
| 182 | MT | 1ª Aplicação | rosa | 10 | aviso_forte | 13.19 |
| 187 | CH | Especial | branca_adaptada_ledor | 10 | erro_alto | - |
| 188 | CN | Especial | branca_adaptada_ledor | 10 | erro_alto | - |
| 189 | LC | Especial | cinza_adaptada_ledor | 10 | erro_alto | - |
| 190 | MT | Especial | cinza_adaptada_ledor | 10 | erro_alto | - |

### 2014

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 195 | CH | 1ª Aplicação | azul | 10 | ok | 0.14 |
| 196 | CH | 1ª Aplicação | amarela | 10 | ok | 0.13 |
| 197 | CH | 1ª Aplicação | branca | 10 | ok | 0.14 |
| 198 | CH | 1ª Aplicação | rosa | 10 | ok | 0.14 |
| 199 | CN | 1ª Aplicação | azul | 10 | ok | 0.13 |
| 200 | CN | 1ª Aplicação | amarela | 10 | ok | 0.13 |
| 201 | CN | 1ª Aplicação | branca | 10 | ok | 0.12 |
| 202 | CN | 1ª Aplicação | rosa | 10 | ok | 0.09 |
| 203 | LC | 1ª Aplicação | amarela | 10 | ok | 0.32 |
| 204 | LC | 1ª Aplicação | cinza | 10 | ok | 0.35 |
| 205 | LC | 1ª Aplicação | azul | 10 | ok | 0.32 |
| 206 | LC | 1ª Aplicação | rosa | 10 | ok | 0.38 |
| 207 | MT | 1ª Aplicação | amarela | 10 | ok | 0.36 |
| 208 | MT | 1ª Aplicação | cinza | 10 | ok | 0.40 |
| 209 | MT | 1ª Aplicação | azul | 10 | ok | 0.13 |
| 210 | MT | 1ª Aplicação | rosa | 10 | erro_alto | 0.05 |
| 213 | LC | Reaplicação | cinza | 10 | ok | 0.21 |
| 214 | MT | Reaplicação | cinza | 10 | ok | 0.11 |
| 215 | CH | Especial | branca_adaptada | 10 | ok | - |
| 216 | CN | Especial | branca_adaptada | 10 | ok | - |
| 217 | LC | Especial | cinza_adaptada | 10 | ok | - |
| 218 | MT | Especial | cinza_adaptada | 10 | erro_alto | - |

### 2015

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 231 | CH | 1ª Aplicação | azul | 10 | ok | 0.37 |
| 232 | CH | 1ª Aplicação | amarela | 10 | ok | 0.40 |
| 233 | CH | 1ª Aplicação | branca | 10 | ok | 0.41 |
| 234 | CH | 1ª Aplicação | rosa | 10 | ok | 0.35 |
| 235 | CN | 1ª Aplicação | azul | 10 | ok | 0.21 |
| 236 | CN | 1ª Aplicação | amarela | 10 | ok | 0.18 |
| 237 | CN | 1ª Aplicação | branca | 10 | ok | 0.19 |
| 238 | CN | 1ª Aplicação | rosa | 10 | ok | 0.21 |
| 239 | LC | 1ª Aplicação | amarela | 10 | ok | 0.22 |
| 240 | LC | 1ª Aplicação | cinza | 10 | ok | 0.21 |
| 241 | LC | 1ª Aplicação | azul | 10 | ok | 0.21 |
| 242 | LC | 1ª Aplicação | rosa | 10 | ok | 0.29 |
| 243 | MT | 1ª Aplicação | amarela | 10 | ok | 0.04 |
| 244 | MT | 1ª Aplicação | cinza | 10 | ok | 0.03 |
| 245 | MT | 1ª Aplicação | azul | 10 | ok | 0.03 |
| 246 | MT | 1ª Aplicação | rosa | 10 | ok | 0.12 |
| 251 | CH | Especial | branca_adaptada | 10 | ok | - |
| 252 | CN | Especial | branca_adaptada | 10 | aviso_forte | - |
| 253 | LC | Especial | cinza_adaptada | 10 | ok | - |
| 254 | MT | Especial | cinza_adaptada | 10 | ok | - |
| 271 | CH | Reaplicação | azul | 10 | ok | 0.13 |
| 272 | CH | Reaplicação | amarela | 10 | ok | 0.14 |
| 273 | CH | Reaplicação | branca | 10 | ok | 0.14 |
| 274 | CH | Reaplicação | rosa | 10 | ok | 0.15 |
| 275 | CN | Reaplicação | azul | 10 | ok | 0.18 |
| 276 | CN | Reaplicação | amarela | 10 | ok | 0.18 |
| 277 | CN | Reaplicação | branca | 10 | ok | 0.19 |
| 278 | CN | Reaplicação | rosa | 10 | ok | 0.16 |
| 279 | LC | Reaplicação | amarela | 10 | ok | 0.29 |
| 280 | LC | Reaplicação | cinza | 10 | ok | 0.32 |
| 281 | LC | Reaplicação | azul | 10 | ok | 0.34 |
| 282 | LC | Reaplicação | rosa | 10 | ok | 0.33 |
| 283 | MT | Reaplicação | amarela | 10 | ok | 0.08 |
| 284 | MT | Reaplicação | cinza | 10 | ok | 0.07 |
| 285 | MT | Reaplicação | azul | 10 | ok | 0.08 |
| 286 | MT | Reaplicação | rosa | 10 | ok | 0.08 |

### 2016

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 291 | CN | 1ª Aplicação | azul | 10 | ok | 0.22 |
| 292 | CN | 1ª Aplicação | amarela | 10 | ok | 0.21 |
| 293 | CN | 1ª Aplicação | branca | 10 | ok | 0.21 |
| 294 | CN | 1ª Aplicação | rosa | 10 | ok | 0.20 |
| 295 | CH | 1ª Aplicação | azul | 10 | ok | 0.13 |
| 296 | CH | 1ª Aplicação | amarela | 10 | ok | 0.13 |
| 297 | CH | 1ª Aplicação | branca | 10 | ok | 0.12 |
| 298 | CH | 1ª Aplicação | rosa | 10 | ok | 0.11 |
| 299 | LC | 1ª Aplicação | azul | 10 | ok | 0.38 |
| 300 | LC | 1ª Aplicação | amarela | 10 | ok | 0.36 |
| 301 | LC | 1ª Aplicação | rosa | 10 | ok | 0.34 |
| 302 | LC | 1ª Aplicação | cinza | 10 | ok | 0.34 |
| 303 | MT | 1ª Aplicação | azul | 10 | ok | 0.03 |
| 304 | MT | 1ª Aplicação | amarela | 10 | ok | 0.12 |
| 305 | MT | 1ª Aplicação | rosa | 10 | ok | 0.21 |
| 306 | MT | 1ª Aplicação | cinza | 10 | ok | 0.04 |
| 307 | CN | Especial | branca_adaptada | 10 | ok | - |
| 308 | CH | Especial | branca_adaptada | 10 | ok | - |
| 309 | LC | Especial | cinza_adaptada | 10 | ok | - |
| 310 | MT | Especial | cinza_adaptada | 10 | ok | - |
| 331 | CN | Reaplicação | azul | 10 | aviso_leve | 2.58 |
| 332 | CN | Reaplicação | amarela | 10 | aviso_leve | 2.37 |
| 333 | CN | Reaplicação | branca | 10 | aviso_leve | 2.25 |
| 336 | CH | Reaplicação | azul | 10 | ok | 0.15 |
| 337 | CH | Reaplicação | amarela | 10 | ok | 0.13 |
| 338 | CH | Reaplicação | branca | 10 | ok | 0.15 |
| 351 | CN | reaplicacao_2 | azul | 10 | aviso_leve | 2.42 |
| 352 | CN | reaplicacao_2 | amarela | 10 | aviso_leve | 2.68 |
| 353 | CN | reaplicacao_2 | branca | 10 | aviso_leve | 2.73 |
| 354 | CN | reaplicacao_2 | rosa | 10 | aviso_leve | 2.57 |
| 356 | CH | reaplicacao_2 | azul | 10 | ok | 0.13 |
| 357 | CH | reaplicacao_2 | amarela | 10 | ok | 0.12 |
| 358 | CH | reaplicacao_2 | branca | 10 | ok | 0.13 |
| 359 | CH | reaplicacao_2 | rosa | 10 | ok | 0.12 |
| 361 | LC | reaplicacao_2 | azul | 10 | ok | 0.08 |
| 362 | LC | reaplicacao_2 | amarela | 10 | ok | 0.08 |
| 363 | LC | reaplicacao_2 | rosa | 10 | ok | 0.07 |
| 364 | LC | reaplicacao_2 | cinza | 10 | ok | 0.08 |
| 366 | MT | reaplicacao_2 | azul | 10 | ok | 0.25 |
| 367 | MT | reaplicacao_2 | amarela | 10 | ok | 0.25 |
| 368 | MT | reaplicacao_2 | rosa | 10 | ok | 0.27 |
| 369 | MT | reaplicacao_2 | cinza | 10 | ok | 0.27 |

### 2017

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 391 | CN | 1ª Aplicação | azul | 10 | erro_alto | - |
| 392 | CN | 1ª Aplicação | amarela | 10 | erro_alto | - |
| 393 | CN | 1ª Aplicação | cinza | 10 | erro_alto | - |
| 394 | CN | 1ª Aplicação | rosa | 10 | erro_alto | - |
| 395 | CH | 1ª Aplicação | azul | 10 | erro_alto | 14.06 |
| 396 | CH | 1ª Aplicação | amarela | 10 | erro_alto | - |
| 397 | CH | 1ª Aplicação | branca | 10 | aviso_forte | 14.55 |
| 398 | CH | 1ª Aplicação | rosa | 10 | erro_alto | - |
| 399 | LC | 1ª Aplicação | azul | 10 | ok | 0.45 |
| 400 | LC | 1ª Aplicação | amarela | 10 | ok | 0.39 |
| 401 | LC | 1ª Aplicação | rosa | 10 | ok | 0.37 |
| 402 | LC | 1ª Aplicação | branca | 10 | ok | 0.37 |
| 403 | MT | 1ª Aplicação | azul | 10 | erro_alto | - |
| 404 | MT | 1ª Aplicação | amarela | 10 | erro_alto | - |
| 405 | MT | 1ª Aplicação | rosa | 10 | erro_alto | - |
| 406 | MT | 1ª Aplicação | cinza | 10 | erro_alto | - |
| 407 | CN | Especial | laranja_adaptada_ledor | 10 | erro_alto | - |
| 408 | CH | Especial | laranja_adaptada_ledor | 10 | erro_alto | - |
| 409 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 410 | MT | Especial | laranja_adaptada_ledor | 10 | erro_alto | - |
| 411 | CN | Especial | verde_videoprova_libras | 10 | aviso_leve | - |
| 412 | CH | Especial | verde_videoprova_libras | 10 | aviso_leve | - |
| 413 | LC | Especial | verde_videoprova_libras | 10 | aviso_leve | - |
| 414 | MT | Especial | verde_videoprova_libras | 10 | ok | - |
| 435 | CH | Reaplicação | azul | 10 | ok | 0.37 |
| 436 | CH | Reaplicação | amarela | 10 | ok | 0.36 |
| 437 | CH | Reaplicação | branca | 10 | ok | 0.34 |
| 438 | CH | Reaplicação | rosa | 10 | ok | 0.32 |
| 439 | LC | Reaplicação | azul | 10 | ok | 0.68 |
| 440 | LC | Reaplicação | amarela | 10 | ok | 0.72 |
| 441 | LC | Reaplicação | branca | 10 | ok | 0.70 |
| 442 | LC | Reaplicação | rosa | 10 | ok | 0.63 |

### 2018

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 447 | CN | 1ª Aplicação | azul | 10 | aviso_forte | 9.73 |
| 448 | CN | 1ª Aplicação | amarela | 10 | aviso_forte | 9.14 |
| 449 | CN | 1ª Aplicação | cinza | 10 | aviso_forte | 9.73 |
| 450 | CN | 1ª Aplicação | rosa | 10 | aviso_forte | 9.09 |
| 451 | CH | 1ª Aplicação | azul | 10 | ok | 1.34 |
| 452 | CH | 1ª Aplicação | amarela | 10 | ok | 1.30 |
| 453 | CH | 1ª Aplicação | branca | 10 | ok | 1.34 |
| 454 | CH | 1ª Aplicação | rosa | 10 | ok | 1.34 |
| 455 | LC | 1ª Aplicação | azul | 10 | ok | 0.23 |
| 456 | LC | 1ª Aplicação | amarela | 10 | ok | 0.20 |
| 457 | LC | 1ª Aplicação | rosa | 10 | ok | 0.17 |
| 458 | LC | 1ª Aplicação | branca | 10 | ok | 0.17 |
| 459 | MT | 1ª Aplicação | azul | 10 | ok | 0.45 |
| 460 | MT | 1ª Aplicação | amarela | 10 | ok | 0.30 |
| 461 | MT | 1ª Aplicação | rosa | 10 | ok | 0.61 |
| 462 | MT | 1ª Aplicação | cinza | 10 | ok | 0.36 |
| 463 | CN | Especial | laranja_adaptada_ledor | 10 | aviso_forte | - |
| 464 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 465 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 466 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 467 | CN | Especial | verde_videoprova_libras | 10 | aviso_forte | - |
| 468 | CH | Especial | verde_videoprova_libras | 10 | ok | - |
| 469 | LC | Especial | verde_videoprova_libras | 10 | ok | - |
| 470 | MT | Especial | verde_videoprova_libras | 10 | ok | - |
| 491 | CH | Reaplicação | azul | 10 | ok | 0.08 |
| 492 | CH | Reaplicação | amarela | 10 | ok | 0.07 |
| 493 | CH | Reaplicação | branca | 10 | ok | 0.07 |
| 494 | CH | Reaplicação | rosa | 10 | ok | 0.09 |
| 495 | LC | Reaplicação | azul | 10 | ok | 0.52 |
| 496 | LC | Reaplicação | amarela | 10 | ok | 0.55 |
| 497 | LC | Reaplicação | branca | 10 | ok | 0.53 |
| 498 | LC | Reaplicação | rosa | 10 | ok | 0.50 |

### 2019

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 503 | CN | 1ª Aplicação | azul | 10 | ok | 0.14 |
| 504 | CN | 1ª Aplicação | amarela | 10 | ok | 0.10 |
| 505 | CN | 1ª Aplicação | cinza | 10 | ok | 0.10 |
| 506 | CN | 1ª Aplicação | rosa | 10 | ok | 0.11 |
| 507 | CH | 1ª Aplicação | azul | 10 | ok | 0.15 |
| 508 | CH | 1ª Aplicação | amarela | 10 | ok | 0.19 |
| 509 | CH | 1ª Aplicação | branca | 10 | ok | 0.17 |
| 510 | CH | 1ª Aplicação | rosa | 10 | ok | 0.18 |
| 511 | LC | 1ª Aplicação | azul | 10 | ok | 0.95 |
| 512 | LC | 1ª Aplicação | amarela | 10 | ok | 0.85 |
| 513 | LC | 1ª Aplicação | rosa | 10 | ok | 0.84 |
| 514 | LC | 1ª Aplicação | branca | 10 | ok | 0.91 |
| 515 | MT | 1ª Aplicação | azul | 10 | erro_alto | 25.90 |
| 516 | MT | 1ª Aplicação | amarela | 10 | erro_alto | 24.27 |
| 517 | MT | 1ª Aplicação | rosa | 10 | erro_alto | 23.44 |
| 518 | MT | 1ª Aplicação | cinza | 10 | erro_alto | 26.09 |
| 519 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 520 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 521 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 522 | MT | Especial | laranja_adaptada_ledor | 10 | erro_alto | - |
| 523 | CN | Especial | verde_videoprova_libras | 10 | ok | - |
| 524 | CH | Especial | verde_videoprova_libras | 10 | ok | - |
| 525 | LC | Especial | verde_videoprova_libras | 10 | ok | - |
| 526 | MT | Especial | verde_videoprova_libras | 10 | erro_alto | - |

### 2020

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 567 | CH | 1ª Aplicação | azul | 10 | ok | 0.27 |
| 568 | CH | 1ª Aplicação | amarela | 10 | ok | 0.25 |
| 569 | CH | 1ª Aplicação | branca | 10 | ok | 0.26 |
| 570 | CH | 1ª Aplicação | rosa | 10 | ok | 0.22 |
| 574 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 575 | CH | Especial | verde_videoprova_libras | 10 | ok | - |
| 577 | LC | 1ª Aplicação | azul | 10 | ok | 0.04 |
| 578 | LC | 1ª Aplicação | amarela | 10 | ok | 0.05 |
| 579 | LC | 1ª Aplicação | rosa | 10 | ok | 0.04 |
| 580 | LC | 1ª Aplicação | branca | 10 | ok | 0.05 |
| 584 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 585 | LC | Especial | verde_videoprova_libras | 10 | ok | - |
| 587 | MT | 1ª Aplicação | azul | 10 | ok | 0.09 |
| 588 | MT | 1ª Aplicação | amarela | 10 | ok | 0.10 |
| 589 | MT | 1ª Aplicação | rosa | 10 | ok | 0.62 |
| 590 | MT | 1ª Aplicação | cinza | 10 | ok | 0.36 |
| 594 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 595 | MT | Especial | verde_videoprova_libras | 10 | ok | - |
| 597 | CN | 1ª Aplicação | azul | 10 | ok | 0.17 |
| 598 | CN | 1ª Aplicação | amarela | 10 | ok | 0.17 |
| 599 | CN | 1ª Aplicação | cinza | 10 | ok | 0.17 |
| 600 | CN | 1ª Aplicação | rosa | 10 | ok | 0.16 |
| 604 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 605 | CN | Especial | verde_videoprova_libras | 10 | ok | - |
| 647 | CH | Reaplicação | azul | 10 | ok | 0.26 |
| 648 | CH | Reaplicação | amarela | 10 | ok | 0.33 |
| 649 | CH | Reaplicação | branca | 10 | ok | 0.25 |
| 650 | CH | Reaplicação | rosa | 10 | ok | 0.28 |
| 657 | LC | Reaplicação | azul | 10 | ok | 0.12 |
| 658 | LC | Reaplicação | amarela | 10 | ok | 0.12 |
| 659 | LC | Reaplicação | rosa | 10 | ok | 0.11 |
| 660 | LC | Reaplicação | branca | 10 | ok | 0.12 |
| 667 | MT | Reaplicação | azul | 10 | ok | 0.53 |
| 668 | MT | Reaplicação | amarela | 10 | ok | 0.23 |
| 669 | MT | Reaplicação | rosa | 10 | ok | 0.32 |
| 670 | MT | Reaplicação | cinza | 10 | ok | 0.12 |
| 677 | CN | Reaplicação | azul | 10 | ok | 0.29 |
| 678 | CN | Reaplicação | amarela | 10 | ok | 0.25 |
| 679 | CN | Reaplicação | cinza | 10 | ok | 0.27 |
| 680 | CN | Reaplicação | rosa | 10 | ok | 0.28 |
| 687 | CH | Digital | azul | 10 | ok | 0.21 |
| 688 | CH | Digital | amarela | 10 | ok | 0.20 |
| 689 | CH | Digital | branca | 10 | ok | 0.20 |
| 690 | CH | Digital | rosa | 10 | ok | 0.22 |
| 691 | LC | Digital | azul | 10 | erro_alto | 39.60 |
| 692 | LC | Digital | amarela | 10 | erro_alto | 36.15 |
| 693 | LC | Digital | branca | 10 | erro_alto | 36.72 |
| 694 | LC | Digital | rosa | 10 | erro_alto | 34.64 |
| 695 | MT | Digital | azul | 10 | ok | 0.50 |
| 696 | MT | Digital | amarela | 10 | ok | 0.42 |
| 697 | MT | Digital | rosa | 10 | ok | 0.55 |
| 698 | MT | Digital | cinza | 10 | ok | 0.40 |
| 699 | CN | Digital | azul | 10 | ok | 0.37 |
| 700 | CN | Digital | amarela | 10 | ok | 0.35 |
| 701 | CN | Digital | rosa | 10 | ok | 0.44 |
| 702 | CN | Digital | cinza | 10 | ok | 0.39 |

### 2021

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 879 | CH | 1ª Aplicação | azul | 10 | ok | 0.16 |
| 880 | CH | 1ª Aplicação | amarela | 10 | ok | 0.21 |
| 881 | CH | 1ª Aplicação | branca | 10 | ok | 0.17 |
| 882 | CH | 1ª Aplicação | rosa | 10 | ok | 0.19 |
| 886 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 887 | CH | Especial | verde_videoprova_libras | 10 | ok | - |
| 889 | LC | 1ª Aplicação | azul | 10 | ok | 0.09 |
| 890 | LC | 1ª Aplicação | amarela | 10 | ok | 0.10 |
| 891 | LC | 1ª Aplicação | rosa | 10 | ok | 0.08 |
| 892 | LC | 1ª Aplicação | branca | 10 | ok | 0.08 |
| 896 | LC | Especial | laranja_adaptada_ledor | 10 | aviso_forte | - |
| 897 | LC | Especial | verde_videoprova_libras | 10 | aviso_forte | - |
| 899 | MT | 1ª Aplicação | azul | 10 | ok | 0.26 |
| 900 | MT | 1ª Aplicação | amarela | 10 | ok | 0.23 |
| 901 | MT | 1ª Aplicação | rosa | 10 | ok | 0.16 |
| 902 | MT | 1ª Aplicação | cinza | 10 | ok | 0.13 |
| 906 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 907 | MT | Especial | verde_videoprova_libras | 10 | ok | - |
| 909 | CN | 1ª Aplicação | azul | 10 | ok | 0.17 |
| 910 | CN | 1ª Aplicação | amarela | 10 | ok | 0.18 |
| 911 | CN | 1ª Aplicação | cinza | 10 | ok | 0.20 |
| 912 | CN | 1ª Aplicação | rosa | 10 | ok | 0.25 |
| 916 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 917 | CN | Especial | verde_videoprova_libras | 10 | ok | - |
| 959 | CH | Reaplicação | azul | 10 | ok | 0.06 |
| 960 | CH | Reaplicação | amarela | 10 | ok | 0.05 |
| 961 | CH | Reaplicação | branca | 10 | ok | 0.05 |
| 962 | CH | Reaplicação | rosa | 10 | ok | 0.05 |
| 969 | LC | Reaplicação | azul | 10 | ok | 0.13 |
| 970 | LC | Reaplicação | amarela | 10 | ok | 0.14 |
| 971 | LC | Reaplicação | rosa | 10 | ok | 0.15 |
| 972 | LC | Reaplicação | branca | 10 | ok | 0.14 |
| 979 | MT | Reaplicação | azul | 10 | ok | 0.10 |
| 980 | MT | Reaplicação | amarela | 10 | ok | 0.10 |
| 981 | MT | Reaplicação | rosa | 10 | ok | 0.11 |
| 982 | MT | Reaplicação | cinza | 10 | ok | 0.09 |
| 989 | CN | Reaplicação | azul | 10 | ok | 0.22 |
| 990 | CN | Reaplicação | amarela | 10 | ok | 0.24 |
| 991 | CN | Reaplicação | cinza | 10 | ok | 0.24 |
| 992 | CN | Reaplicação | rosa | 10 | ok | 0.23 |
| 999 | CH | Digital | azul | 10 | ok | 0.18 |
| 1000 | CH | Digital | amarela | 10 | ok | 0.24 |
| 1001 | CH | Digital | branca | 10 | ok | 0.18 |
| 1002 | CH | Digital | rosa | 10 | ok | 0.19 |
| 1003 | LC | Digital | azul | 10 | ok | 0.08 |
| 1004 | LC | Digital | amarela | 10 | ok | 0.09 |
| 1005 | LC | Digital | branca | 10 | ok | 0.09 |
| 1006 | LC | Digital | rosa | 10 | ok | 0.09 |
| 1007 | MT | Digital | azul | 10 | ok | 0.14 |
| 1008 | MT | Digital | amarela | 10 | ok | 0.15 |
| 1009 | MT | Digital | rosa | 10 | ok | 0.27 |
| 1010 | MT | Digital | cinza | 10 | ok | 0.14 |
| 1011 | CN | Digital | azul | 10 | ok | 0.18 |
| 1012 | CN | Digital | amarela | 10 | ok | 0.16 |
| 1013 | CN | Digital | rosa | 10 | ok | 0.15 |
| 1014 | CN | Digital | cinza | 10 | ok | 0.17 |
| 1015 | CH | 2ª Oportunidade | azul | 10 | ok | 0.05 |
| 1016 | CH | 2ª Oportunidade | amarela | 10 | ok | 0.05 |
| 1017 | CH | 2ª Oportunidade | branca | 10 | ok | 0.05 |
| 1018 | CH | 2ª Oportunidade | rosa | 10 | ok | 0.06 |
| 1025 | LC | 2ª Oportunidade | azul | 10 | ok | 0.13 |
| 1026 | LC | 2ª Oportunidade | amarela | 10 | ok | 0.15 |
| 1027 | LC | 2ª Oportunidade | rosa | 10 | ok | 0.14 |
| 1028 | LC | 2ª Oportunidade | branca | 10 | ok | 0.12 |
| 1035 | MT | 2ª Oportunidade | azul | 10 | ok | 0.09 |
| 1036 | MT | 2ª Oportunidade | amarela | 10 | ok | 0.12 |
| 1037 | MT | 2ª Oportunidade | cinza | 10 | ok | 0.10 |
| 1038 | MT | 2ª Oportunidade | rosa | 10 | ok | 0.08 |
| 1045 | CN | 2ª Oportunidade | azul | 10 | ok | 0.21 |
| 1046 | CN | 2ª Oportunidade | amarela | 10 | ok | 0.23 |
| 1047 | CN | 2ª Oportunidade | cinza | 10 | ok | 0.24 |
| 1048 | CN | 2ª Oportunidade | rosa | 10 | ok | 0.21 |

### 2022

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1055 | CH | 1ª Aplicação | azul | 10 | ok | 0.20 |
| 1056 | CH | 1ª Aplicação | amarela | 10 | ok | 0.22 |
| 1057 | CH | 1ª Aplicação | branca | 10 | ok | 0.23 |
| 1058 | CH | 1ª Aplicação | rosa | 10 | ok | 0.24 |
| 1062 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1063 | CH | Especial | verde_videoprova_libras | 10 | ok | - |
| 1065 | LC | 1ª Aplicação | azul | 10 | ok | 0.07 |
| 1066 | LC | 1ª Aplicação | amarela | 10 | ok | 0.07 |
| 1067 | LC | 1ª Aplicação | rosa | 10 | ok | 0.07 |
| 1068 | LC | 1ª Aplicação | branca | 10 | ok | 0.07 |
| 1072 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1073 | LC | Especial | verde_videoprova_libras | 10 | ok | - |
| 1075 | MT | 1ª Aplicação | azul | 10 | ok | 0.15 |
| 1076 | MT | 1ª Aplicação | amarela | 10 | ok | 0.09 |
| 1077 | MT | 1ª Aplicação | rosa | 10 | ok | 0.08 |
| 1078 | MT | 1ª Aplicação | cinza | 10 | ok | 0.18 |
| 1082 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1083 | MT | Especial | verde_videoprova_libras | 10 | ok | - |
| 1085 | CN | 1ª Aplicação | azul | 10 | ok | 0.20 |
| 1086 | CN | 1ª Aplicação | amarela | 10 | ok | 0.22 |
| 1087 | CN | 1ª Aplicação | cinza | 10 | ok | 0.19 |
| 1088 | CN | 1ª Aplicação | rosa | 10 | ok | 0.20 |
| 1092 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1093 | CN | Especial | verde_videoprova_libras | 10 | ok | - |
| 1135 | CH | Reaplicação | azul | 10 | ok | 0.04 |
| 1136 | CH | Reaplicação | amarela | 10 | ok | 0.05 |
| 1137 | CH | Reaplicação | branca | 10 | ok | 0.06 |
| 1138 | CH | Reaplicação | rosa | 10 | ok | 0.05 |
| 1145 | LC | Reaplicação | azul | 10 | ok | 0.09 |
| 1146 | LC | Reaplicação | amarela | 10 | ok | 0.09 |
| 1147 | LC | Reaplicação | rosa | 10 | ok | 0.09 |
| 1148 | LC | Reaplicação | branca | 10 | ok | 0.09 |
| 1155 | MT | Reaplicação | azul | 10 | ok | 0.13 |
| 1156 | MT | Reaplicação | amarela | 10 | ok | 0.05 |
| 1157 | MT | Reaplicação | rosa | 10 | ok | 0.08 |
| 1158 | MT | Reaplicação | cinza | 10 | ok | 0.14 |
| 1165 | CN | Reaplicação | azul | 10 | ok | 0.06 |
| 1166 | CN | Reaplicação | amarela | 10 | ok | 0.04 |
| 1167 | CN | Reaplicação | cinza | 10 | ok | 0.05 |
| 1168 | CN | Reaplicação | rosa | 10 | ok | 0.04 |
| 1175 | CH | Digital | azul | 10 | ok | 0.22 |
| 1176 | CH | Digital | amarela | 10 | ok | 0.23 |
| 1177 | CH | Digital | branca | 10 | ok | 0.25 |
| 1178 | CH | Digital | rosa | 10 | ok | 0.25 |
| 1179 | LC | Digital | azul | 10 | ok | 0.06 |
| 1180 | LC | Digital | amarela | 10 | ok | 0.07 |
| 1181 | LC | Digital | branca | 10 | ok | 0.07 |
| 1182 | LC | Digital | rosa | 10 | ok | 0.06 |
| 1183 | MT | Digital | azul | 10 | ok | 0.08 |
| 1184 | MT | Digital | amarela | 10 | ok | 0.09 |
| 1185 | MT | Digital | rosa | 10 | ok | 0.78 |
| 1186 | MT | Digital | cinza | 10 | ok | 0.10 |
| 1187 | CN | Digital | azul | 10 | ok | 0.17 |
| 1188 | CN | Digital | amarela | 10 | ok | 0.18 |
| 1189 | CN | Digital | rosa | 10 | ok | 0.18 |
| 1190 | CN | Digital | cinza | 10 | ok | 0.21 |

### 2023

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1191 | CH | 1ª Aplicação | azul | 10 | ok | 0.24 |
| 1192 | CH | 1ª Aplicação | amarela | 10 | ok | 0.24 |
| 1193 | CH | 1ª Aplicação | branca | 10 | ok | 0.22 |
| 1194 | CH | 1ª Aplicação | rosa | 10 | ok | 0.22 |
| 1195 | CH | Especial | rosa_ampliada | 10 | ok | - |
| 1196 | CH | Especial | rosa_superampliada | 10 | ok | - |
| 1197 | CH | Especial | laranja_braille | 10 | ok | - |
| 1198 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1199 | CH | Especial | verde_videoprova_libras | 10 | ok | - |
| 1201 | LC | 1ª Aplicação | azul | 10 | ok | 0.09 |
| 1202 | LC | 1ª Aplicação | amarela | 10 | ok | 0.10 |
| 1203 | LC | 1ª Aplicação | rosa | 10 | ok | 0.09 |
| 1204 | LC | 1ª Aplicação | branca | 10 | ok | 0.09 |
| 1205 | LC | Especial | rosa_ampliada | 10 | ok | - |
| 1206 | LC | Especial | rosa_superampliada | 10 | ok | - |
| 1207 | LC | Especial | laranja_braille | 10 | ok | - |
| 1208 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1209 | LC | Especial | verde_videoprova_libras | 10 | ok | - |
| 1211 | MT | 1ª Aplicação | azul | 10 | ok | 0.09 |
| 1212 | MT | 1ª Aplicação | amarela | 10 | ok | 0.22 |
| 1213 | MT | 1ª Aplicação | rosa | 10 | ok | 0.13 |
| 1214 | MT | 1ª Aplicação | cinza | 10 | ok | 0.23 |
| 1215 | MT | Especial | rosa_ampliada | 10 | erro_alto | - |
| 1216 | MT | Especial | rosa_superampliada | 10 | ok | - |
| 1217 | MT | Especial | laranja_braille | 10 | ok | - |
| 1218 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1219 | MT | Especial | verde_videoprova_libras | 10 | ok | - |
| 1221 | CN | 1ª Aplicação | azul | 10 | ok | 0.47 |
| 1222 | CN | 1ª Aplicação | amarela | 10 | ok | 0.44 |
| 1223 | CN | 1ª Aplicação | rosa | 10 | ok | 0.44 |
| 1224 | CN | 1ª Aplicação | cinza | 10 | ok | 0.49 |
| 1225 | CN | Especial | rosa_ampliada | 10 | erro_alto | - |
| 1226 | CN | Especial | rosa_superampliada | 10 | ok | - |
| 1227 | CN | Especial | laranja_braille | 10 | ok | - |
| 1228 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1229 | CN | Especial | verde_videoprova_libras | 10 | ok | - |
| 1271 | CH | Reaplicação | azul | 10 | erro_alto | 0.15 |
| 1272 | CH | Reaplicação | amarela | 10 | ok | 0.16 |
| 1273 | CH | Reaplicação | branca | 10 | ok | 0.15 |
| 1274 | CH | Reaplicação | rosa | 10 | ok | 0.19 |
| 1281 | LC | Reaplicação | azul | 10 | erro_alto | 0.12 |
| 1282 | LC | Reaplicação | amarela | 10 | ok | 0.53 |
| 1283 | LC | Reaplicação | rosa | 10 | ok | 0.12 |
| 1284 | LC | Reaplicação | branca | 10 | ok | 0.51 |
| 1291 | MT | Reaplicação | azul | 10 | ok | 0.06 |
| 1292 | MT | Reaplicação | amarela | 10 | ok | 0.07 |
| 1293 | MT | Reaplicação | rosa | 10 | ok | 0.06 |
| 1294 | MT | Reaplicação | cinza | 10 | ok | 0.07 |
| 1301 | CN | Reaplicação | azul | 10 | ok | 0.09 |
| 1302 | CN | Reaplicação | amarela | 10 | ok | 0.10 |
| 1303 | CN | Reaplicação | cinza | 10 | ok | 0.10 |
| 1304 | CN | Reaplicação | rosa | 10 | ok | 0.11 |

### 2024

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1363 | MT | Reaplicação | azul | 10 | ok | 0.14 |
| 1364 | MT | Reaplicação | amarela | 10 | ok | 0.10 |
| 1365 | MT | Reaplicação | verde | 10 | ok | 0.13 |
| 1366 | MT | Reaplicação | cinza | 10 | ok | 0.11 |
| 1373 | CN | Reaplicação | azul | 10 | ok | 0.08 |
| 1374 | CN | Reaplicação | amarela | 10 | ok | 0.07 |
| 1375 | CN | Reaplicação | cinza | 10 | ok | 0.05 |
| 1376 | CN | Reaplicação | verde | 10 | ok | 0.09 |
| 1383 | CH | 1ª Aplicação | azul | 10 | ok | 0.16 |
| 1384 | CH | 1ª Aplicação | amarela | 10 | ok | 0.21 |
| 1385 | CH | 1ª Aplicação | branca | 10 | ok | 0.18 |
| 1386 | CH | 1ª Aplicação | verde | 10 | ok | 0.18 |
| 1387 | CH | Especial | verde_ampliada | 10 | ok | - |
| 1388 | CH | Especial | verde_superampliada | 10 | ok | - |
| 1390 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1391 | CH | Especial | roxa_videoprova_libras | 10 | ok | - |
| 1395 | LC | 1ª Aplicação | azul | 10 | ok | 0.50 |
| 1396 | LC | 1ª Aplicação | amarela | 10 | ok | 0.52 |
| 1397 | LC | 1ª Aplicação | verde | 10 | ok | 0.55 |
| 1398 | LC | 1ª Aplicação | branca | 10 | ok | 0.59 |
| 1399 | LC | Especial | verde_ampliada | 10 | ok | - |
| 1400 | LC | Especial | verde_superampliada | 10 | ok | - |
| 1402 | LC | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1403 | LC | Especial | roxa_videoprova_libras | 10 | ok | - |
| 1407 | MT | 1ª Aplicação | azul | 10 | ok | 0.37 |
| 1408 | MT | 1ª Aplicação | amarela | 10 | ok | 0.27 |
| 1409 | MT | 1ª Aplicação | verde | 10 | ok | 0.23 |
| 1410 | MT | 1ª Aplicação | cinza | 10 | ok | 0.27 |
| 1411 | MT | Especial | verde_ampliada | 10 | ok | - |
| 1412 | MT | Especial | verde_superampliada | 10 | ok | - |
| 1414 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1415 | MT | Especial | roxa_videoprova_libras | 10 | ok | - |
| 1419 | CN | 1ª Aplicação | azul | 10 | ok | 0.19 |
| 1420 | CN | 1ª Aplicação | amarela | 10 | ok | 0.18 |
| 1421 | CN | 1ª Aplicação | verde | 10 | ok | 0.16 |
| 1422 | CN | 1ª Aplicação | cinza | 10 | ok | 0.17 |
| 1423 | CN | Especial | verde_ampliada | 10 | ok | - |
| 1424 | CN | Especial | verde_superampliada | 10 | ok | - |
| 1426 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1427 | CN | Especial | roxa_videoprova_libras | 10 | ok | - |

### 2025

| CO_PROVA | Área | Aplicação | Cor | N | Status | MAE |
|----------|------|-----------|-----|---|--------|-----|
| 1447 | CH | 1ª Aplicação | azul | 10 | ok | 0.16 |
| 1448 | CH | 1ª Aplicação | amarela | 10 | ok | 0.17 |
| 1449 | CH | 1ª Aplicação | branca | 10 | ok | 0.15 |
| 1450 | CH | 1ª Aplicação | verde | 10 | ok | 0.16 |
| 1451 | CH | Especial | laranja_ampliada | 10 | ok | - |
| 1452 | CH | Especial | laranja_superampliada | 10 | ok | - |
| 1454 | CH | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1455 | CH | Especial | roxa_videoprova_libras | 10 | ok | - |
| 1459 | LC | 1ª Aplicação | azul | 10 | ok | 0.47 |
| 1460 | LC | 1ª Aplicação | amarela | 10 | ok | 0.55 |
| 1461 | LC | 1ª Aplicação | verde | 10 | ok | 0.50 |
| 1462 | LC | 1ª Aplicação | branca | 10 | ok | 0.50 |
| 1463 | LC | Especial | laranja_ampliada | 10 | aviso_leve | - |
| 1464 | LC | Especial | laranja_superampliada | 10 | aviso_leve | - |
| 1466 | LC | Especial | laranja_adaptada_ledor | 10 | aviso_leve | - |
| 1467 | LC | Especial | roxa_videoprova_libras | 10 | aviso_leve | - |
| 1471 | MT | 1ª Aplicação | azul | 10 | ok | 0.14 |
| 1472 | MT | 1ª Aplicação | amarela | 10 | ok | 0.10 |
| 1473 | MT | 1ª Aplicação | verde | 10 | ok | 0.10 |
| 1474 | MT | 1ª Aplicação | cinza | 10 | ok | 0.05 |
| 1475 | MT | Especial | laranja_ampliada | 10 | ok | - |
| 1476 | MT | Especial | laranja_superampliada | 10 | ok | - |
| 1478 | MT | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1479 | MT | Especial | roxa_videoprova_libras | 10 | ok | - |
| 1483 | CN | 1ª Aplicação | azul | 10 | ok | 0.15 |
| 1484 | CN | 1ª Aplicação | amarela | 10 | ok | 0.16 |
| 1485 | CN | 1ª Aplicação | verde | 10 | ok | 0.16 |
| 1486 | CN | 1ª Aplicação | cinza | 10 | ok | 0.15 |
| 1487 | CN | Especial | laranja_ampliada | 10 | ok | - |
| 1488 | CN | Especial | laranja_superampliada | 10 | ok | - |
| 1490 | CN | Especial | laranja_adaptada_ledor | 10 | ok | - |
| 1491 | CN | Especial | roxa_videoprova_libras | 10 | ok | - |
| 1495 | CH | Especial | laranja_atendimento_especializado | 10 | ok | - |
| 1496 | LC | Especial | laranja_atendimento_especializado | 10 | aviso_leve | - |
| 1497 | MT | Especial | laranja_atendimento_especializado | 10 | ok | - |
| 1498 | CN | Especial | laranja_atendimento_especializado | 10 | ok | - |
| 1539 | CH | Reaplicação | azul | 10 | ok | 0.06 |
| 1541 | CH | Reaplicação | branca | 10 | ok | 0.06 |
| 1542 | CH | Reaplicação | verde | 10 | ok | 0.05 |
| 1549 | LC | Reaplicação | azul | 10 | aviso_forte | 4.54 |
| 1551 | LC | Reaplicação | verde | 10 | aviso_leve | 5.71 |
| 1552 | LC | Reaplicação | branca | 10 | aviso_leve | 5.10 |
| 1559 | MT | Reaplicação | azul | 10 | ok | 0.12 |
| 1560 | MT | Reaplicação | amarela | 10 | ok | 0.13 |
| 1561 | MT | Reaplicação | verde | 10 | ok | 0.14 |
| 1562 | MT | Reaplicação | cinza | 10 | ok | 0.13 |
| 1569 | CN | Reaplicação | azul | 10 | ok | 0.21 |
| 1570 | CN | Reaplicação | amarela | 10 | ok | 0.24 |
| 1571 | CN | Reaplicação | cinza | 10 | ok | 0.17 |
| 1572 | CN | Reaplicação | verde | 10 | ok | 0.24 |
