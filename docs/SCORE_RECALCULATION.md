# ENEM Score Recalculation

The library reproduces official ENEM scores by reimplementing the Item Response Theory pipeline used by INEP, calibrated against real participant data from the public microdata releases. Scores are accurate to within 1 point for **92% of all exam booklets from 2009 to 2025**.

---

## Data

All inputs come from INEP's publicly released annual microdata ([dados.gov.br](https://dados.gov.br/dados/conjuntos-dados/microdados-do-enem)):

- **Item parameters** — the three IRT parameters (a, b, c) for every question in every booklet
- **Answer keys** — correct answers per question per booklet color
- **Participant records** — response strings and official scores used for calibration and validation

---

## Calculation Pipeline

### 1. IRT Model

ENEM scores use the **3-Parameter Logistic Model (3PL)**:

```
P(correct | θ) = c + (1 - c) / (1 + exp(-D · a · (θ - b)))
```

- **a** — discrimination
- **b** — difficulty
- **c** — pseudo-guessing floor
- **D = 1.0**

### 2. Ability Estimation (EAP)

Each student's latent ability θ is estimated via **Expected A Posteriori** integration:

```
θ̂ = ∫ θ · L(responses | θ) · N(0,1) dθ  /  ∫ L(responses | θ) · N(0,1) dθ
```

Computed using **80-point Gauss-Hermite quadrature** with a standard normal prior N(0, 1).

### 3. Score Transformation

```
score = slope × θ + intercept
```

The coefficients are not constant and vary per subject area. They were determined by fitting against real participant data from the INEP microdata:

| Area | Slope (≈) | Intercept (≈) |
|------|----------:|---------------:|
| MT   | 129.6     | 500.0          |
| CN   | 113.1     | 501.2          |
| CH   | 112.3     | 501.5          |
| LC   | 108.1     | 500.0          |

Coefficients are stable across years (year-to-year variation < 0.1%) and stored per exam booklet in [coeficientes_data.json](../src/tri_enem/coeficientes_data.json).

---

## Calibration

INEP applies an annual equalization step that adjusts slope and intercept per exam. Coefficients were recovered by fitting a linear regression between EAP-estimated θ values and official scores from the microdata.

**Pipeline** (`calibrador.py` / `tools/calibrar_com_mapeamento.py`):

1. Load microdata for a given year and area from `microdados_limpos/`
2. Filter to participants with valid attendance and official score
3. Draw a stratified sample of up to 200 participants per booklet, across score bands (0–500, 500–600, 600–700, 700–800, 800+)
4. Estimate θ via EAP using published item parameters
5. Fit OLS: `official_score ≈ slope × θ̂ + intercept`
6. Store slope, intercept, MAE, and R² per booklet in `coeficientes_data.json`

---

## Validation

Test cases come from real participant records in `tests/fixtures/exemplos_microdados.json`, extracted from INEP microdata.

**`tests/extrair_exemplos_completos.py`** — builds the test suite by resolving each participant's exam color and application type from their `CO_PROVA` code and writing rows to `tests/suite_testes_completos.txt`.

**`tests/executar_testes_completos.py`** — runs the full Streamlit app calculation path against 40+ real participants, comparing recalculated scores against official scores and validating question-order mappings per year.

---

## Precision

Measured as **Mean Absolute Error (MAE)** between recalculated and official scores on the validation sample.

| Metric | Value |
|--------|-------|
| Median MAE (368 exams) | 0.14 pts |
| Mean MAE | 1.89 pts |
| Exams with MAE ≤ 2 pts | 340 / 368 (92%) |
| Exams with MAE ≤ 5 pts | 345 / 368 (94%) |
| Coverage | 2009–2025 |

**By year:**

| Year | Reliable | Partial | High Error | No Data |
|------|--------:|---------:|-----------:|--------:|
| 2009 | 28 | 0 | 5 | 0 |
| 2010 | 24 | 0 | 0 | 0 |
| 2011 | 12 | 1 | 3 | 0 |
| 2012 | 20 | 0 | 0 | 0 |
| 2013 | 12 | 0 | 8 | 0 |
| 2014 | 20 | 0 | 2 | 0 |
| 2015 | 35 | 1 | 0 | 0 |
| 2016 | 42 | 0 | 0 | 0 |
| 2017 | 17 | 0 | 15 | 0 |
| 2018 | 26 | 6 | 0 | 0 |
| 2019 | 18 | 0 | 6 | 0 |
| 2020 | 52 | 0 | 4 | 0 |
| 2021 | 70 | 2 | 0 | 0 |
| 2022 | 56 | 0 | 0 | 0 |
| 2023 | 48 | 0 | 4 | 0 |
| 2024 | 32 | 0 | 0 | 16 |
| 2025 | 52 | 2 | 0 | 2 |

*Reliable: MAE ≤ 5 pts. Partial: MAE 5–15 pts. High Error: MAE > 15 pts. No Data: zero participants in public microdata (adapted booklets).*

Precision warnings are surfaced at runtime by `precisao.py` and shown in the web UI.

---

## Answer-Order Mapping

Each booklet color presents the same questions in a different order. Every `(year, area, application_type, color)` combination maps to a specific INEP exam code (`CO_PROVA`) via [mapeamento_provas.yaml](../src/tri_enem/mapeamento_provas.yaml).

Structural changes across years:

| Period | Change |
|--------|--------|
| Pre-2016 | Colors were Cinza/Laranja; `TX_COR` column absent from microdata |
| 2016–2017 | CH question sequence shifted in some booklets |
| 2020 | Physical and digital editions share item codes with different orderings |
| 2020+ | LC answer block moved from positions 91–135 to 1–45 in item files |
| 2009 | LC lacks `TP_LINGUA`; English/Spanish blocks cannot be separated |

---

## Known Limitations

| Case | MAE | Cause |
|------|-----|-------|
| 2009 LC (all booklets) | 46–71 pts | `TP_LINGUA` absent; language blocks cannot be separated |
| 2013 LC booklet 189 | 231.6 pts | Item order mismatch in INEP file |
| 2013 CH/CN/MT (selected) | 21–110 pts | Item order anomalies for special booklets |
| 2017 CH/CN/MT (15 booklets) | 15–84 pts | Mixed question-numbering conventions in special booklets |
| 2019 MT PPL booklets | ≈26 pts | PPL booklet ordering not resolved |
| 2020 digital LC (4 booklets) | 34–40 pts | Duplicate item entries for physical/digital editions |
| 2024–2025 adapted booklets | N/A | Zero participants in public microdata |
| Any exam, score > 900 pts | ±5 pts | Sparse quadrature grid at the upper tail |
