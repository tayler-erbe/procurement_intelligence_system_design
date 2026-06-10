#!/usr/bin/env python3
"""
BTAA Procurement RAG — Evaluation Runner
Tests all 30 queries in btaa_eval_set.json against the live API.

Usage:
    python btaa_eval_runner.py
    python btaa_eval_runner.py --api http://localhost:8080
    python btaa_eval_runner.py --category exact
    python btaa_eval_runner.py --out analysis_output/57_eval_results.txt
"""

import json
import time
import argparse
import sys
import requests
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_API  = "http://localhost:8080"
EVAL_FILE    = Path(__file__).parent / "btaa_eval_set.json"
TIMEOUT      = 60   # seconds per query

# ── Grading helpers ───────────────────────────────────────────────────────────
def grade_query(q: dict, result: dict) -> tuple[bool, list[str]]:
    """
    Returns (passed: bool, failures: list[str])
    Checks tier, price range, and minimum alternatives.
    """
    failures = []

    # 1. Tier check
    expected_tier = q.get("expected_tier")
    actual_tier   = result.get("tier", "")
    if expected_tier and actual_tier != expected_tier:
        failures.append(f"tier: expected '{expected_tier}', got '{actual_tier}'")

    # 2. Price range check — best price must be in expected range
    best = result.get("best") or result.get("cheapest")
    price_min = q.get("expected_price_min")
    price_max = q.get("expected_price_max")
    if best and price_min is not None and price_max is not None:
        price = float(best.get("price", 0) or 0)
        if price < price_min or price > price_max:
            failures.append(
                f"price: ${price:.2f} outside expected range "
                f"[${price_min}–${price_max}]"
            )
    elif price_min is not None and not best:
        failures.append("price: no result returned")

    # 3. Minimum alternatives check
    min_alts = q.get("expected_min_alternatives", 0)
    if min_alts > 0:
        n_exact = result.get("n_exact", 0)
        n_llm   = result.get("n_llm",   0)
        n_alts  = len(result.get("alternatives", [])) + n_exact + n_llm
        if n_alts < min_alts:
            failures.append(
                f"alternatives: got {n_alts}, expected >= {min_alts}"
            )

    # 4. Expected distributor check (when specified)
    exp_dist = q.get("expected_distributor")
    if exp_dist and best:
        actual_dist = best.get("distributor", "")
        if actual_dist != exp_dist:
            failures.append(
                f"distributor: expected '{exp_dist}', got '{actual_dist}'"
            )

    return len(failures) == 0, failures


def run_query(api: str, q: dict) -> tuple[dict, float]:
    """Call /candidates then /compare for a full pipeline result."""
    t0 = time.time()

    # Step 1: get candidates
    params = {"query": q["query"]}
    if q.get("manufacturer"):  params["manufacturer"]  = q["manufacturer"]
    if q.get("part_number"):   params["part_number"]   = q["part_number"]

    r = requests.get(f"{api}/candidates", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    cand_data = r.json()

    candidates = cand_data.get("candidates", [])
    tier       = cand_data.get("tier", "unknown")

    if not candidates:
        return {"tier": tier, "candidates_n": 0, "best": None,
                "cheapest": None, "n_exact": 0, "n_llm": 0,
                "alternatives": []}, time.time()-t0

    # Step 2: compare using first candidate as baseline
    best_cand = candidates[0]
    baseline  = {
        "distributor": best_cand.get("distributor",""),
        "manufacturer":best_cand.get("manufacturer",""),
        "description": best_cand.get("description",""),
        "price":       float(best_cand.get("price", 0) or 0),
        "catalog_num": best_cand.get("catalog_num",""),
    }

    r2 = requests.post(f"{api}/compare",
                       json={"baseline": baseline, "query": q["query"]},
                       timeout=TIMEOUT)
    r2.raise_for_status()
    compare_data = r2.json()

    # Merge tier from candidates
    compare_data["tier"] = tier
    compare_data["best"] = baseline  # first candidate is "best" from retrieval

    return compare_data, time.time()-t0


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="BTAA eval runner")
    parser.add_argument("--api",      default=DEFAULT_API,
                        help="API base URL")
    parser.add_argument("--category", default=None,
                        help="Filter by category (e.g. 'exact', 'semantic', 'pipettes')")
    parser.add_argument("--out",      default=None,
                        help="Output file path")
    args = parser.parse_args()

    # Load eval set
    if not EVAL_FILE.exists():
        print(f"ERROR: {EVAL_FILE} not found", file=sys.stderr)
        sys.exit(1)

    with open(EVAL_FILE) as f:
        eval_data = json.load(f)
    queries = eval_data["queries"]

    # Filter by category if specified
    if args.category:
        queries = [q for q in queries
                   if args.category.lower() in q.get("category","").lower()
                   or args.category.lower() in q.get("expected_tier","").lower()]
        print(f"Filtered to {len(queries)} queries matching '{args.category}'")

    # Check API health
    try:
        h = requests.get(f"{args.api}/health", timeout=5)
        hd = h.json()
        llm_online = bool(hd.get("llm_endpoint"))
        print(f"API: {args.api}")
        print(f"Index: {hd.get('index_vectors',0):,} vectors")
        print(f"LLM:  {'ONLINE — ' + hd['llm_endpoint'] if llm_online else 'OFFLINE (exact-match tests only)'}")
    except Exception as e:
        print(f"ERROR: Cannot reach API at {args.api}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nRunning {len(queries)} queries...\n")
    print("─" * 80)

    results    = []
    passed     = 0
    failed     = 0
    errors     = 0
    total_time = 0.0

    for i, q in enumerate(queries, 1):
        label = f"[{q['id']}] {q['label']}"
        print(f"{i:2d}/{len(queries)}  {label[:55]:<57}", end="", flush=True)

        try:
            result, elapsed = run_query(args.api, q)
            total_time += elapsed
            ok, failures = grade_query(q, result)

            status = "✓ PASS" if ok else "✗ FAIL"
            print(f"  {status}  {elapsed:.1f}s")
            if failures:
                for f in failures:
                    print(f"          → {f}")

            results.append({
                "id":       q["id"],
                "label":    q["label"],
                "category": q.get("category",""),
                "passed":   ok,
                "failures": failures,
                "elapsed":  round(elapsed, 2),
                "tier":     result.get("tier",""),
                "n_candidates": result.get("candidates_n", 0),
                "n_exact":  result.get("n_exact", 0),
                "n_llm":    result.get("n_llm", 0),
            })
            if ok: passed += 1
            else:  failed += 1

        except Exception as e:
            print(f"  ERROR  {str(e)[:60]}")
            results.append({
                "id": q["id"], "label": q["label"],
                "passed": False, "failures": [f"exception: {e}"],
                "elapsed": 0, "tier": "error",
            })
            errors += 1
            failed += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    total   = len(queries)
    pct     = 100 * passed / total if total else 0
    avg_t   = total_time / max(total - errors, 1)

    print("\n" + "─" * 80)
    print(f"RESULTS: {passed}/{total} passed ({pct:.0f}%)")
    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Errors:  {errors}")
    print(f"  Avg latency: {avg_t:.1f}s per query")
    print(f"  Total time:  {total_time:.0f}s")

    # By category
    cats = {}
    for r in results:
        c = r.get("category", "unknown")
        if c not in cats: cats[c] = {"pass":0,"total":0}
        cats[c]["total"] += 1
        if r["passed"]: cats[c]["pass"] += 1

    if len(cats) > 1:
        print("\nBy category:")
        for cat, v in sorted(cats.items()):
            bar = "█" * v["pass"] + "░" * (v["total"]-v["pass"])
            print(f"  {cat:<30} {v['pass']}/{v['total']}  {bar}")

    # Known weaknesses summary
    weaknesses = eval_data.get("known_weaknesses_to_watch", [])
    if weaknesses and failed > 0:
        print("\nKnown acceptable failures:")
        failed_ids = {r["id"] for r in results if not r["passed"]}
        for w in weaknesses:
            wid = w if isinstance(w, str) else w.get("id","")
            if wid in failed_ids:
                note = "" if isinstance(w, str) else f" — {w.get('note','')}"
                print(f"  {wid}{note}")

    # ── Write output file ──────────────────────────────────────────────────────
    outpath = args.out or f"analysis_output/57_eval_results_{datetime.now():%Y%m%d_%H%M%S}.txt"
    Path(outpath).parent.mkdir(exist_ok=True)

    with open(outpath, "w", encoding="utf-8") as f:
        f.write(f"BTAA Procurement Eval — {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"API: {args.api}\n")
        f.write(f"LLM: {'online' if llm_online else 'offline'}\n")
        f.write(f"Queries: {total}  Passed: {passed}  Failed: {failed}  "
                f"Pass rate: {pct:.0f}%\n\n")
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            f.write(f"[{r['id']}] {status}  {r['label']}\n")
            if r["failures"]:
                for fail in r["failures"]:
                    f.write(f"  → {fail}\n")
        f.write(f"\nTotal time: {total_time:.0f}s  Avg: {avg_t:.1f}s/query\n")

    print(f"\nResults saved to: {outpath}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
