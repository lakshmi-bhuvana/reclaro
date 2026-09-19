#!/usr/bin/env python3
"""
reclaro_benchmark.py
====================
Reproducible benchmark comparing a naive exact-string matching baseline against
Reclaro's deterministic/hybrid matching pipeline.

Runs fully locally - no AWS credentials, no Bedrock calls, no live FDA API.
Uses the actual Reclaro matching code from the backend package.

Usage:
    py -3.14 benchmarks/reclaro_benchmark.py

Requirements:
    pip install pydantic   (already in requirements.txt)

Metric Definitions
------------------
Two distinct measurement sets are reported:

STRICT CONFIRMATION METRICS
  A prediction is only "correct" for an AFFECTED item when Reclaro returns CONFIRMED.
  NEEDS_REVIEW on an AFFECTED item is treated as a failure to confirm (i.e. counted
  as a false negative under strict confirmation semantics), not as a true positive.

  TP  = CONFIRMED  on AFFECTED ground truth
  FP  = CONFIRMED  on NOT_AFFECTED ground truth
  FN  = NEEDS_REVIEW or NOT_AFFECTED on AFFECTED ground truth
  TN  = NOT_AFFECTED on NOT_AFFECTED ground truth
  Precision        = TP / (TP + FP)
  Recall (strict)  = TP / (TP + FN)   [denominator = total AFFECTED]

SCREENING / ESCALATION METRIC
  Separately: how many AFFECTED items were surfaced (CONFIRMED OR NEEDS_REVIEW).
  This is NOT called recall to avoid conflating confirmation with escalation.
  Screened Detection Coverage = (TP + NEEDS_REVIEW on AFFECTED) / total AFFECTED
"""

import csv
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so backend package imports work.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.models.schemas import (
    InventoryItem,
    NormalizedRecall,
)
from backend.services.evidence.evidence_builder import EvidenceBuilder


# ===========================================================================
# BENCHMARK RECALL SCOPE
# ===========================================================================
# A synthetic (but internally self-consistent) FDA-style recall scope.
# Not pulled from the live openFDA API — deterministic and reproducible.
#
# Recall profile:
#   Firm:    Cardio Systems Inc.
#   Product: Spectrum IQ Infusion Pump
#   Catalog: 74021210 through 74021229  (20 catalog numbers)
#   Model:   Spectrum IQ
#   Lot:     ALL_LOTS (unrestricted lot scope)
#   Serial:  ALL_SERIALS (unrestricted serial scope)
# ===========================================================================

def build_benchmark_recall() -> NormalizedRecall:
    """Build the fixed synthetic NormalizedRecall used for all benchmark cases."""
    catalog_range = [str(n) for n in range(74021210, 74021230)]  # 74021210..74021229

    return NormalizedRecall(
        recall_id="BM-CARDIO-2024-001",
        manufacturer="cardio systems",          # normalizer output (no suffix, lowercase)
        product_families=[
            "Spectrum IQ Infusion Pump",
            "Infusion Pump",
        ],
        models=["SPECTRUM IQ"],
        catalog_numbers=catalog_range,          # already normalized (digits only)
        udi_di=[],
        lot_ranges=["ALL_LOTS"],                # unrestricted
        serial_ranges=["ALL_SERIALS"],          # unrestricted
        action="Remove from service and contact Cardio Systems Inc. for replacement.",
        risk_class="Class II",
    )


BENCHMARK_RECALL = build_benchmark_recall()
GROUND_TRUTH_CSV = Path(__file__).parent / "ground_truth.csv"


# ===========================================================================
# GROUND TRUTH LOADER
# ===========================================================================

def load_ground_truth() -> List[Dict[str, str]]:
    """Load the CSV benchmark dataset."""
    rows = []
    with open(GROUND_TRUTH_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def row_to_inventory_item(row: Dict[str, str]) -> InventoryItem:
    """Convert a ground_truth.csv row into an InventoryItem."""
    return InventoryItem(
        inventory_id=row["case_id"],
        manufacturer=row["manufacturer"] or "Unknown",
        product_name=row["product_name"] or "Unknown Device",
        model=row["model"] or None,
        catalog_number=row["catalog_number"] or None,
        lot_number=row["lot_number"] or None,
        serial_number=row["serial_number"] or None,
    )


# ===========================================================================
# BASELINE: Naive exact-string matching
# ===========================================================================
# Rules:
#   1. Lowercase-strip manufacturer; exact substring match against the
#      normalized recall manufacturer string (no suffix stripping).
#   2. Exact string catalog match — no hyphen or space removal at all.
#   3. Exact case-insensitive model match.
#   4. Verdict: CONFIRMED if mfr AND (catalog OR model) match. Otherwise
#      NOT_AFFECTED. The baseline never emits NEEDS_REVIEW.
#
# This models a naive inventory-audit spreadsheet search: copy-paste the
# recall catalog list into VLOOKUP with no pre-processing.
# ===========================================================================

def baseline_predict(item: InventoryItem, recall: NormalizedRecall) -> tuple[str, List[str]]:
    """
    Naive exact-string baseline.
    Returns (status_str, signals_list).
    Status is one of: 'CONFIRMED', 'NOT_AFFECTED'.
    """
    signals = []

    # Manufacturer: lowercase strip + substring check; no suffix normalization
    item_mfr_raw = (item.manufacturer or "").lower().strip()
    recall_mfr_raw = (recall.manufacturer or "").lower().strip()
    mfr_match = (
        item_mfr_raw == recall_mfr_raw
        or item_mfr_raw in recall_mfr_raw
        or recall_mfr_raw in item_mfr_raw
    )
    if mfr_match:
        signals.append("BASELINE_MFR_MATCH")

    # Catalog: exact raw-string comparison only (no normalization at all)
    cat_match = False
    item_cat_raw = (item.catalog_number or "").strip()
    if item_cat_raw:
        for r_cat in recall.catalog_numbers:
            if item_cat_raw == r_cat:
                cat_match = True
                signals.append("BASELINE_EXACT_CATALOG")
                break

    # Model: exact case-insensitive comparison only
    model_match = False
    item_model_raw = (item.model or "").upper().strip()
    if item_model_raw:
        for r_model in recall.models:
            if item_model_raw == r_model.upper().strip():
                model_match = True
                signals.append("BASELINE_EXACT_MODEL")
                break

    if mfr_match and (cat_match or model_match):
        return "CONFIRMED", signals
    return "NOT_AFFECTED", signals


# ===========================================================================
# RECLARO PIPELINE
# ===========================================================================

def reclaro_predict(item: InventoryItem, recall: NormalizedRecall) -> tuple[str, List[str]]:
    """
    Run the actual Reclaro deterministic pipeline (no AI/Bedrock).
    Returns (status_str, signals_list).
    """
    # ai_signals=None ensures no Bedrock dependency
    match_result = EvidenceBuilder.build_match_result(item, recall, ai_signals=None)
    return match_result.status.value, match_result.signals


# ===========================================================================
# EVALUATION
# ===========================================================================

def evaluate(
    predictions: List[str],
    ground_truths: List[str],
) -> Dict[str, Any]:
    """
    Compute metrics under STRICT CONFIRMATION semantics.

    STRICT CONFIRMATION:
      NEEDS_REVIEW on an AFFECTED case is NOT a true positive.
      It is counted as a confirmation failure (contributes to FN_strict).

      TP           = CONFIRMED on AFFECTED
      FP           = CONFIRMED on NOT_AFFECTED
      FN_strict    = (NEEDS_REVIEW + NOT_AFFECTED) on AFFECTED
      TN           = NOT_AFFECTED on NOT_AFFECTED
      NR_on_neg    = NEEDS_REVIEW on NOT_AFFECTED (tracked separately)

    Precision (strict) = TP / (TP + FP)
    Recall    (strict) = TP / (TP + FN_strict)   [denominator = total AFFECTED]

    SCREENING / ESCALATION (reported separately):
      screened_positives = TP + NEEDS_REVIEW on AFFECTED
      screened_coverage  = screened_positives / total AFFECTED
      (NOT labelled 'recall' — labelled 'Screened Detection Coverage')
    """
    tp = fp = tn = nr_on_pos = nr_on_neg = not_affected_on_pos = 0

    for pred, gt in zip(predictions, ground_truths):
        is_affected = (gt == "AFFECTED")
        if is_affected:
            if pred == "CONFIRMED":
                tp += 1
            elif pred == "NEEDS_REVIEW":
                nr_on_pos += 1          # escalated but NOT confirmed
            else:                        # NOT_AFFECTED on AFFECTED
                not_affected_on_pos += 1
        else:
            if pred == "CONFIRMED":
                fp += 1
            elif pred == "NEEDS_REVIEW":
                nr_on_neg += 1           # false escalation
            else:
                tn += 1

    fn_strict = nr_on_pos + not_affected_on_pos   # all non-CONFIRMED on AFFECTED

    total = len(predictions)
    affected = sum(1 for g in ground_truths if g == "AFFECTED")
    not_affected = total - affected

    # --- STRICT metrics ---
    precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
    recall_strict = tp / (tp + fn_strict) if (tp + fn_strict) > 0 else float("nan")
    # Note: tp + fn_strict == affected (all AFFECTED cases)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else float("nan")

    # --- SCREENING metric (separate) ---
    screened_positives = tp + nr_on_pos
    screened_coverage = screened_positives / affected if affected > 0 else float("nan")

    review_count = nr_on_pos + nr_on_neg
    review_rate = review_count / total if total > 0 else float("nan")

    return {
        "total": total,
        "affected": affected,
        "not_affected": not_affected,
        # Strict confirmation counts
        "tp": tp,
        "fp": fp,
        "fn_strict": fn_strict,
        "fn_nr": nr_on_pos,              # subset of FN: those that were NEEDS_REVIEW
        "fn_missed": not_affected_on_pos, # subset of FN: those that were NOT_AFFECTED
        "tn": tn,
        "nr_on_neg": nr_on_neg,
        # Strict metrics
        "precision": precision,
        "recall_strict": recall_strict,
        "fpr": fpr,
        # Screening metric
        "screened_positives": screened_positives,
        "screened_coverage": screened_coverage,
        # Review
        "nr_on_pos": nr_on_pos,
        "nr_on_neg": nr_on_neg,
        "review_count": review_count,
        "review_rate": review_rate,
    }


def fmt(val) -> str:
    """Format a float metric for display."""
    if isinstance(val, float):
        if val != val:  # NaN
            return "N/A"
        return f"{val:.3f}"
    return str(val)


# ===========================================================================
# CASE-LEVEL STATUS TAG
# ===========================================================================

def case_ok_tag(pred: str, expected: str) -> str:
    """
    Returns a clear single-character tag for the case-level table.

    C = CONFIRMED on AFFECTED (strict TP)
    N = NOT_AFFECTED on NOT_AFFECTED (TN)
    R = NEEDS_REVIEW on AFFECTED (escalated, NOT a strict TP)
    F = prediction wrong (FP or FN)
    """
    if pred == "CONFIRMED" and expected == "AFFECTED":
        return "C"   # Strict TP
    if pred == "NOT_AFFECTED" and expected == "NOT_AFFECTED":
        return "N"   # TN
    if pred == "NEEDS_REVIEW" and expected == "AFFECTED":
        return "R"   # Escalated — NOT counted as TP in strict metrics
    return "F"       # Wrong (FP or hard FN)


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    rows = load_ground_truth()

    if not rows:
        print("ERROR: No rows loaded from ground_truth.csv")
        sys.exit(1)

    # Verify all 30 cases are present exactly once
    case_ids = [r["case_id"].strip() for r in rows]
    if len(case_ids) != len(set(case_ids)):
        duplicates = [c for c in case_ids if case_ids.count(c) > 1]
        print(f"ERROR: Duplicate case IDs detected: {set(duplicates)}")
        sys.exit(1)

    recall = BENCHMARK_RECALL

    case_results = []
    baseline_preds = []
    reclaro_preds = []
    ground_truths_list = []
    baseline_times = []
    reclaro_times = []

    for row in rows:
        item = row_to_inventory_item(row)
        expected = row["expected_status"].strip()

        # --- BASELINE ---
        t0 = time.perf_counter()
        b_pred, b_signals = baseline_predict(item, recall)
        t1 = time.perf_counter()

        # --- RECLARO ---
        t2 = time.perf_counter()
        r_pred, r_signals = reclaro_predict(item, recall)
        t3 = time.perf_counter()

        case_results.append({
            "case_id": row["case_id"],
            "case_type": row["case_type"],
            "expected": expected,
            "baseline_pred": b_pred,
            "reclaro_pred": r_pred,
            "baseline_signals": b_signals,
            "reclaro_signals": r_signals,
            "b_tag": case_ok_tag(b_pred, expected),
            "r_tag": case_ok_tag(r_pred, expected),
            "baseline_time_ms": (t1 - t0) * 1000,
            "reclaro_time_ms": (t3 - t2) * 1000,
            "notes": row.get("notes", ""),
        })

        baseline_preds.append(b_pred)
        reclaro_preds.append(r_pred)
        ground_truths_list.append(expected)
        baseline_times.append((t1 - t0) * 1000)
        reclaro_times.append((t3 - t2) * 1000)

    # Compute metrics
    b_m = evaluate(baseline_preds, ground_truths_list)
    r_m = evaluate(reclaro_preds, ground_truths_list)

    avg_b_time = sum(baseline_times) / len(baseline_times)
    avg_r_time = sum(reclaro_times) / len(reclaro_times)

    sep = "=" * 65

    # ===========================================================================
    # REPORT
    # ===========================================================================

    print()
    print(sep)
    print("RECLARO BENCHMARK")
    print(sep)
    print()

    # --- Dataset summary ---
    print("Dataset")
    print("-" * 45)
    print(f"  Total cases          : {b_m['total']}")
    print(f"  Cases AFFECTED  (GT) : {b_m['affected']}")
    print(f"  Cases NOT_AFFECTED(GT): {b_m['not_affected']}")
    print(f"  Unique case IDs      : {len(set(case_ids))}  (no duplicates)")
    print(f"  CSV                  : {GROUND_TRUTH_CSV.name}")
    print(f"  Recall ID            : {recall.recall_id}")
    print(f"  Recall firm          : Cardio Systems Inc.")
    print(f"  Recall mfr (norm)    : '{recall.manufacturer}'")
    print(f"  Catalog range        : 74021210-74021229  ({len(recall.catalog_numbers)} numbers)")
    print()

    # --- NEEDS_REVIEW on AFFECTED — detailed audit ---
    nr_on_affected = [r for r in case_results
                      if r["reclaro_pred"] == "NEEDS_REVIEW" and r["expected"] == "AFFECTED"]

    print("NEEDS_REVIEW AUDIT (Reclaro, GT=AFFECTED)")
    print("-" * 45)
    if nr_on_affected:
        for r in nr_on_affected:
            print(f"  Case     : {r['case_id']}")
            print(f"  Expected : {r['expected']}")
            print(f"  Reclaro  : {r['reclaro_pred']}")
            print(f"  Signals  : {r['reclaro_signals']}")
            print(f"  Reason   : Manufacturer and product-family evidence present but")
            print(f"             NO exact catalog, NO model identifier matched the recall")
            print(f"             scope. Verifier Rule 1 (CONFIRMED) requires a deterministic")
            print(f"             identifier (UDI, catalog, or model). Rule 2 fires instead.")
            print(f"  Strict   : Counts as FN under strict confirmation semantics.")
            print(f"             NEEDS_REVIEW is NOT a confirmed positive.")
            print(f"  Screening: Item was surfaced for review (not silently dropped).")
            print(f"             Counted in Screened Detection Coverage metric.")
            print()
    else:
        print("  None.")
        print()

    # --- Helper to print one pipeline's metrics ---
    def print_pipeline(label: str, m: Dict, avg_time: float):
        print(label)
        print("-" * 45)
        print()
        print("  [STRICT CONFIRMATION METRICS]")
        print(f"  NEEDS_REVIEW treated as: confirmation failure (not TP)")
        print()
        print(f"    TP  (CONFIRMED on AFFECTED)     : {m['tp']}")
        print(f"    FP  (CONFIRMED on NOT_AFFECTED) : {m['fp']}")
        print(f"    FN  (not-confirmed on AFFECTED) : {m['fn_strict']}")
        print(f"        of which NEEDS_REVIEW       : {m['fn_nr']}")
        print(f"        of which NOT_AFFECTED       : {m['fn_missed']}")
        print(f"    TN  (NOT_AFFECTED on NOT_AFFECTED): {m['tn']}")
        print()
        print(f"    Precision (strict)              : {fmt(m['precision'])}")
        print(f"      = TP / (TP + FP) = {m['tp']} / {m['tp'] + m['fp']}")
        print(f"    Recall    (strict)              : {fmt(m['recall_strict'])}")
        print(f"      = TP / (TP + FN) = {m['tp']} / {m['tp'] + m['fn_strict']}")
        print(f"    False Positive Rate             : {fmt(m['fpr'])}")
        print(f"      = FP / (FP + TN) = {m['fp']} / {m['fp'] + m['tn']}")
        print()
        print("  [SCREENING / ESCALATION METRIC]")
        print(f"  (Separate from strict recall. Do not conflate.)")
        print()
        print(f"    CONFIRMED on AFFECTED           : {m['tp']}")
        print(f"    NEEDS_REVIEW on AFFECTED        : {m['nr_on_pos']}")
        print(f"    Screened positives              : {m['screened_positives']}")
        print(f"    Total AFFECTED                  : {m['affected']}")
        print(f"    Screened Detection Coverage     : {fmt(m['screened_coverage'])}")
        print(f"      = (TP + NR_on_pos) / total_AFFECTED")
        print(f"      = {m['screened_positives']} / {m['affected']}")
        print(f"      (This is NOT recall. It measures how many AFFECTED items")
        print(f"       were surfaced by any signal, not deterministically confirmed.)")
        print()
        print("  [REVIEW METRICS]")
        print(f"    NEEDS_REVIEW on AFFECTED (FN)   : {m['nr_on_pos']}")
        print(f"    NEEDS_REVIEW on NOT_AFFECTED    : {m['nr_on_neg']}")
        print(f"    Total NEEDS_REVIEW              : {m['review_count']}")
        print(f"    Review Rate (of all cases)      : {fmt(m['review_rate'])}")
        print()
        print(f"  Avg processing time               : {avg_time:.3f} ms/item")

    print_pipeline("BASELINE (naive exact-string)", b_m, avg_b_time)
    print()
    print_pipeline("RECLARO (deterministic + normalization)", r_m, avg_r_time)

    # --- Comparison table ---
    print()
    print("COMPARISON SUMMARY")
    print("-" * 45)
    print(f"  {'Metric':<36} {'Baseline':>9} {'Reclaro':>9}")
    print(f"  {'-'*36} {'-'*9} {'-'*9}")
    rows_cmp = [
        ("tp",                "TP (strict confirmed)"),
        ("fp",                "FP (false positives)"),
        ("fn_strict",         "FN strict (not confirmed)"),
        ("fn_nr",             "  of which NEEDS_REVIEW"),
        ("fn_missed",         "  of which NOT_AFFECTED"),
        ("tn",                "TN"),
        ("precision",         "Precision (strict)"),
        ("recall_strict",     "Recall (strict)"),
        ("screened_coverage", "Screened Detection Coverage"),
        ("review_rate",       "Review Rate"),
    ]
    for key, label in rows_cmp:
        bv = b_m[key]
        rv = r_m[key]
        print(f"  {label:<36} {fmt(bv):>9} {fmt(rv):>9}")
    print()
    print("  Tag legend in case table below:")
    print("    C = Correct CONFIRMED (strict TP)")
    print("    N = Correct NOT_AFFECTED (TN)")
    print("    R = NEEDS_REVIEW on AFFECTED (escalated; NOT a strict TP)")
    print("    F = Wrong prediction (FP or hard FN)")
    print()

    # --- Case-level table ---
    print("CASE-LEVEL RESULTS")
    print("-" * 45)
    hdr = f"  {'ID':<5} {'GT':<14} {'Baseline':<14} {'Reclaro':<14} {'B':<3} {'R':<3} Type"
    print(hdr)
    print("  " + "-" * 85)
    for r in case_results:
        print(
            f"  {r['case_id']:<5} "
            f"{r['expected']:<14} "
            f"{r['baseline_pred']:<14} "
            f"{r['reclaro_pred']:<14} "
            f"{r['b_tag']:<3} {r['r_tag']:<3} "
            f"{r['case_type']}"
        )

    print()
    print("  Tag explanation for this run:")
    for r in case_results:
        if r["r_tag"] == "R":
            print(f"    {r['case_id']} R -> NEEDS_REVIEW on AFFECTED: escalated, not confirmed (counts as FN)")
        elif r["r_tag"] == "F":
            print(f"    {r['case_id']} F -> Wrong: pred={r['reclaro_pred']} expected={r['expected']}")
        if r["b_tag"] == "F":
            print(f"    {r['case_id']} B=F -> Baseline wrong: pred={r['baseline_pred']} expected={r['expected']}")

    print()
    print("NOTE: This is an engineering benchmark on a synthetic dataset.")
    print("      It evaluates matching behaviour, not clinical safety.")
    print("      See benchmarks/README.md for methodology and limitations.")
    print()
    print(sep)
    print("BENCHMARK COMPLETE")
    print(sep)
    print()


if __name__ == "__main__":
    main()
