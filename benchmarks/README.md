# Reclaro Benchmark

## Purpose

This benchmark evaluates and compares two matching approaches against a synthetic hospital-inventory dataset:

1. **Baseline** — naive exact-string matching (no normalization, no fuzzy logic, no AI)
2. **Reclaro** — the existing deterministic + normalization pipeline

The goal is to demonstrate, on a controlled dataset, the kinds of real-world inventory formatting problems that exact-string matching fails on, and to show how Reclaro's normalization layer handles them.

---

## Files

| File | Description |
|---|---|
| `ground_truth.csv` | 30 synthetic inventory cases with expected affected/not-affected classification |
| `reclaro_benchmark.py` | Standalone benchmark script using the actual Reclaro backend code |
| `README.md` | This document |

---

## What the Synthetic Dataset Represents

The dataset models a hospital inventory audit against a single synthetic FDA-style recall:

- **Recalling firm**: Cardio Systems Inc.
- **Product**: Spectrum IQ Infusion Pump
- **Model**: Spectrum IQ
- **Catalog numbers**: 74021210 through 74021229 (20 numbers)
- **Lot scope**: ALL_LOTS (unrestricted)
- **Serial scope**: ALL_SERIALS (unrestricted)

The 30 cases represent realistic inventory record variations commonly encountered in hospital biomedical engineering databases:

| Category | Cases | What it tests |
|---|---|---|
| Exact positives | B01–B04 | Clean match - both pipelines should confirm |
| Catalog formatting differences | B06, B07, B13, B21, B29 | Hyphens and spaces in catalog numbers |
| Manufacturer alias/suffix | B05, B09, B11, B25 | Inc. / Corp / LLC / Medical suffixes |
| Missing catalog, model match | B12, B20 | Partial identifier coverage |
| Wrong manufacturer | B08, B14, B16, B23 | Manufacturer gate effectiveness |
| Wrong product / catalog collision | B15 | Catalog match with unrelated product |
| Lot/serial scope | B17, B18 | ALL_LOTS / ALL_SERIALS unrestricted scope |
| Model confirms when catalog absent/wrong | B22, B24 | Model match as primary signal |
| All-lowercase input | B27 | Case normalization |
| Ambiguous (no strong identifiers) | B10, B30 | Product family overlap only |
| Unrelated devices | B19, B26 | True negatives |

---

## Why Exact-String Matching is a Reasonable Baseline

Many hospital inventory systems perform recall matching by exporting a spreadsheet and running exact text comparisons. This is the operational baseline that Reclaro is designed to improve upon.

The naive baseline:
- Lowercases and strip-matches the manufacturer name (substring check)
- Compares the catalog number as a raw string — no hyphen or space removal
- Compares the model number as an exact case-insensitive string
- Emits CONFIRMED if manufacturer matches AND (catalog OR model) matches
- Never emits NEEDS_REVIEW — it has only two outputs: match or no match

---

## What Reclaro Adds

Reclaro applies several normalization and matching improvements over the baseline:

1. **Catalog normalization**: removes hyphens, spaces, and punctuation before comparing catalog numbers (`74021-212` → `74021212`). The naive baseline fails on any formatting variant.

2. **Manufacturer suffix normalization**: strips legal entity suffixes (Inc., Corp., LLC, Medical, Systems, Healthcare, etc.) so `Cardio Systems Corporation` and `Cardio Systems Inc.` and `Cardio Systems Medical` all resolve to the same normalized token `cardio systems`.

3. **Token overlap matching**: decomposes manufacturer names into tokens, allowing partial overlap matching for alias detection.

4. **Product family matching**: extracts product family names from the recall description and checks for token subset overlap with the inventory product name. This enables evidence generation even when catalog and model are unavailable.

5. **NEEDS_REVIEW tier**: when evidence is present but proof is incomplete (e.g. product family match with no catalog/model identifier), Reclaro flags the item for manual inspection rather than silently dropping it to NOT_AFFECTED. The naive baseline has no review tier — uncertain cases are lost as false negatives.

6. **Recall scope awareness**: interprets ALL_LOTS and ALL_SERIALS markers in the recall scope correctly, so lot/serial restrictions do not block confirmation when the scope is unrestricted.

---

## Benchmark Methodology

1. Load the 30-case `ground_truth.csv` dataset.
2. Construct a fixed `NormalizedRecall` object representing the synthetic recall (no live API calls).
3. For each case, run the naive baseline and then the Reclaro pipeline independently.
4. Record predictions, signals, and processing time per case.
5. Compute aggregate metrics.

The benchmark is:
- **Local** — no network access, no AWS credentials required
- **Deterministic** — identical output on every run
- **Reproducible** — the synthetic recall and ground truth are fixed
- **Bedrock-free** — the core benchmark passes `ai_signals=None`; no Bedrock calls are made

---

## Definition of AFFECTED vs NOT_AFFECTED

**AFFECTED**: The inventory item is within the scope of the recall and requires action.
This is defined by the ground truth in `ground_truth.csv`.

**NOT_AFFECTED**: The item is not within the recall scope and requires no action.

### Treatment of NEEDS_REVIEW

The Reclaro pipeline can emit three statuses: CONFIRMED, NEEDS_REVIEW, NOT_AFFECTED.

In the benchmark evaluation:

| Reclaro status | Ground truth = AFFECTED | Ground truth = NOT_AFFECTED |
|---|---|---|
| CONFIRMED | ✓ True Positive | ✗ False Positive |
| NEEDS_REVIEW | Counted as `review_on_positive` — not TP, but also not FN | Counted as `review_on_negative` |
| NOT_AFFECTED | ✗ False Negative | ✓ True Negative |

**NEEDS_REVIEW is not silently counted as correct.** It is tracked separately. In recall-sensitivity calculations, items flagged NEEDS_REVIEW on an AFFECTED case are excluded from both TP and FN — they represent correctly escalated uncertainty.

For the purposes of `r_correct` in the case-level output, NEEDS_REVIEW on an AFFECTED case is marked Y (partial credit) because the pipeline avoided a false negative and flagged the item for review.

---

## Metrics Reported

| Metric | Definition |
|---|---|
| TP | True Positives — CONFIRMED on an AFFECTED ground truth |
| FP | False Positives — CONFIRMED on a NOT_AFFECTED ground truth |
| FN | False Negatives — NOT_AFFECTED on an AFFECTED ground truth |
| TN | True Negatives — NOT_AFFECTED on a NOT_AFFECTED ground truth |
| Precision | TP / (TP + FP) |
| Recall (Sensitivity) | TP / (TP + FN + NEEDS_REVIEW_on_positive) |
| False Positive Rate | FP / (FP + TN) |
| Review Rate | Total NEEDS_REVIEW / Total cases |
| Avg Processing Time | Mean per-item wall time in milliseconds |

---

## Limitations

> **This is an engineering benchmark, not a medical validation study.**

The following limitations apply:

1. **Synthetic dataset**: All 30 cases are artificially constructed. They represent plausible real-world formatting problems but are not derived from actual hospital inventory records.

2. **Ground truth is manually defined**: The AFFECTED/NOT_AFFECTED labels were assigned by the benchmark designer, not by a clinician or FDA expert. They reflect the matching engineering problem, not clinical risk assessment.

3. **Single recall scope**: The benchmark uses one fixed synthetic recall. Performance may differ substantially across different recall types (e.g., lot-restricted recalls, UDI-DI recalls, serial-range recalls).

4. **Catalog collision is a known limitation**: When a catalog number appears in a recall scope but belongs to a completely different product from the same manufacturer (e.g. B15 — Cardiac Monitor with catalog 74021217), neither the baseline nor Reclaro can distinguish this without additional product-level data. This is a data quality problem, not a matching algorithm problem.

5. **openFDA data quality**: Real recall notices may have incomplete, ambiguous, or inconsistent code_info fields. Recall parser extraction quality directly affects matching quality.

6. **No Bedrock evaluation**: This benchmark does not evaluate the Bedrock AI normalization layer. AI-enhanced results may improve NEEDS_REVIEW conversion rates on noisy records but are excluded here for reproducibility.

7. **Benchmark results depend on case selection**: The performance gap between baseline and Reclaro is a direct function of how many catalog-formatting cases are included. The 30 cases were designed to be representative, not exhaustive.

8. **Not a safety determination**: A CONFIRMED result from Reclaro indicates a deterministic match against structured recall scope data. It does not constitute a clinical safety assessment. All recall management decisions must follow applicable regulatory and institutional procedures.

---

## Running the Benchmark

```bash
# From the project root
py -3.14 benchmarks/reclaro_benchmark.py
```

No AWS credentials, no Bedrock credentials, no network access required.

---

## Running the Backend Test Suite

```bash
py -3.14 -m pytest backend/tests -v
```
