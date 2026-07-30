# ENEM Score Recalculation

The library estimates ENEM scores with the published item parameters and
validates each exam booklet against official participant scores.

## Versioned item data

The 17 `ITENS_PROVA_<year>.csv` files are stored once, under
`src/tri_enem/data/itens/<year>/`. They are:

- produced from the official releases by `tools/gerar_dados_itens.py`;
- schema-checked and recorded in `data/itens/manifest.json`, including source
  and normalized SHA-256 hashes;
- included in wheels by the package-data rule in `pyproject.toml`;
- loaded through `importlib.resources` when no external item path is supplied.

Regenerate the package data with:

```bash
python tools/gerar_dados_itens.py \
  --microdados-dir /path/to/MICRODADOS_ENEM
```

The generator accepts the extracted official `microdados_enem_<year>/DADOS`
layout (including the lowercase 2016 filename), normalizes all files
atomically, and fails if any year or required column is missing.

## Ability calculation

The response model is the three-parameter logistic model:

```text
P(correct | θ) = c + (1 - c) / (1 + exp(-a · (θ - b)))
```

Ability is estimated by EAP with an `N(0, 1)` prior and 80-point
Gauss-Hermite quadrature. Scalar and vectorized implementations are tested for
numerical equivalence. Abandoned items do not enter the likelihood.

LC item selection is language-strict. In particular, the 2020 digital
booklets 691–694 contain two complete 45-item versions under each proof code;
the version matching the participant language is selected before positions
are paired with responses.

The adapted 2013 booklets 187–190 also contain two distinct item collections
under each code, but neither the item file nor the participant file exposes a
version discriminator. They remain calculable through a deterministic choice
of the first collection in the normalized official file. Their holdout status,
sample size, MAE, and maximum observed error are always presented with the
score, so this unresolved ambiguity is not hidden from users.

## Score transformation

`coeficientes_data.json` uses schema v3. Each mapped proof has one entry with:

- an affine baseline (`slope`, `intercept`);
- either a linear transformation or monotonic piecewise-linear knots;
- calibration and model-selection sample sizes;
- untouched holdout metrics;
- status and reason.

Candidate models are linear and monotonic piecewise-linear transformations with
5, 9, 17, or 33 requested knots. Knot scores are fitted with weighted isotonic
regression. Selection minimizes, in order, validation errors above two points,
maximum error, MAE, and model complexity.

## Real-data sampling and validation

Run:

```bash
python tools/recalibrar_validacao.py \
  --microdados-dir /path/to/MICRODADOS_ENEM \
  --workers 3
```

For every mapped proof, and separately by language in LC, valid participant
records are stratified into:

```text
(0,400], (400,500], (500,600], (600,700], (700,800],
(800,900], (900,1000], (1000,+∞)
```

Up to 160 deterministic cases are retained per stratum: 100 calibration,
30 model selection, and 30 final holdout cases. Official zeros, absent
participants, missing responses, unmapped proofs, and proofs without item
parameters cannot enter calibration. Minimum and maximum official scores are
reserved for holdout whenever possible.

The generator publishes atomically:

- `src/tri_enem/coeficientes_data.json`;
- `tests/fixtures/validation_holdout.jsonl.gz`;
- `tests/fixtures/validation_manifest.json`;
- `docs/VALIDATION_REPORT.md`.

The manifest records source hashes, sampling parameters, coverage, source
commit, and status counts. No participant identifier is stored.

## Status contract

Status uses the maximum absolute holdout error, not training MAE:

| Status | Maximum holdout error |
|---|---:|
| `ok` | ≤ 2 points |
| `aviso_leve` | > 2 and ≤ 5 |
| `aviso_forte` | > 5 and ≤ 15 |
| `erro_alto` | > 15 |

Fewer than 30 holdout records, fewer than two populated score bands, or
incomplete band coverage results in `nao_calibrado`. Only `ok` is exposed as
`confiavel=True`; every other calculable result is explicitly an estimate.

The user-facing message has a separate presentation profile. An `ok` proof
receives a positive confirmation. A proof whose typical holdout errors are
low but whose strict status is caused by a small number of exceptions receives
an intermediate message. This profile never changes the strict status or
promotes the proof to `confiavel=True`.

Current generated results are in [VALIDATION_REPORT.md](VALIDATION_REPORT.md).
The report includes plain-language guidance, statistics by year and area,
human-readable booklet names, status/profile lists, and exact per-proof
metrics.
CI recomputes the committed holdout with:

```bash
python tests/validar_holdout.py
```
