#!/usr/bin/env python3
"""Build Phase 5 cost table from Phase 4 static run summaries.

Reads all passed Phase 4 run summaries whose purpose is 'functional' or
'lifetime=false' and whose mode is B1/B2/B4/B5.  Computes mean
energy_nj_per_delivered_reading per mode and selects B6 winner.

Outputs results/phase_05/cost_table.json (hashed, frozen before evaluation).

Usage:
    python3 host/calibrate.py [--seed SEED] [--out PATH]
"""
import argparse, hashlib, json, statistics
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

CAP_INDEX = {1: 0, 2: 1, 4: 2}
MODE_PROFILE = {"B1": 1, "B2": 2, "B4": 1, "B5": 2}
MODE_CAP     = {"B1": 1, "B2": 1, "B4": 4, "B5": 4}

def load_summaries(results_dir: Path, seed=None):
    """Return list of (mode, summary_dict) for valid Phase 4 static runs."""
    rows = []
    seen = set()
    cohort = None
    if seed is None: raise ValueError("Explicit isolated calibration seed required")
    for d in sorted(results_dir.iterdir()):
        manifest_path = d / "manifest.json"
        summary_path  = d / "summary.json"
        if not manifest_path.exists() or not summary_path.exists():
            continue
        try:
            m = json.loads(manifest_path.read_text())
            s = json.loads(summary_path.read_text())
        except Exception:
            continue
        if m.get("status") != "passed":
            continue
        cfg = m.get("config", {})
        if cfg.get("phase") != 4:
            continue
        if cfg.get("purpose") != "functional" or cfg.get("lifetime") or not cfg.get("power_model"):
            continue
        if cfg.get("aes_backend") != "contiki_software_aes_128_driver" or not m.get("energy_reconciliation"):
            continue
        mode = m.get("mode")
        if mode not in MODE_PROFILE:
            continue
        if seed is not None and cfg.get("seed") != seed:
            continue
        enj = s.get("energy_per_delivered_reading_nj")
        pdr = s.get("reading_pdr")
        p95 = s.get("p95_delay_ms")
        delivered = s.get("unique_authenticated_delivered", 0)
        if enj is None or pdr is None or delivered == 0:
            continue
        # Only explicit seed, identical source/measurement cohort, no repeated cells.
        identity = json.dumps({k:cfg.get(k) for k in ("target","backend","warmup_ms","period_ms","readings_per_sensor","deadline_ms","drain_ms","payload_budget","power_model","energy_sample_ms")},sort_keys=True)
        sources = {k:v for k,v in m.get("source_hashes",{}).items() if k != "firmware/generated-conf.h"}
        signature = (identity, json.dumps(sources,sort_keys=True), m.get("clients"))
        if cohort is None: cohort = signature
        if signature != cohort: raise ValueError("Mixed calibration cohort; select compatible source/config runs")
        cell = (mode, cfg.get("seed"))
        if cell in seen: raise ValueError("Duplicate calibration cell; explicitly curate attempts")
        seen.add(cell)
        rows.append({
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "run_id": m.get("run_id"),
            "mode": mode,
            "seed": cfg.get("seed"),
            "clients": m.get("clients"),
            "energy_nj_per_delivered_reading": enj,
            "reading_pdr": pdr,
            "p95_delay_ms": p95,
            "unique_authenticated_delivered": delivered,
        })
    return rows


def build_cost_table(rows):
    """Return cost table dict keyed by mode."""
    per_mode = {}
    for r in rows:
        per_mode.setdefault(r["mode"], []).append(r["energy_nj_per_delivered_reading"])

    table = {}
    for mode, vals in per_mode.items():
        table[mode] = {
            "mean_nj_per_delivered_reading": statistics.mean(vals),
            "samples": len(vals),
            "profile": MODE_PROFILE[mode],
            "cap": MODE_CAP[mode],
        }
    return table


def select_b6_winner(table):
    """B6 winner: mode with lowest mean energy among B1/B2/B4/B5."""
    candidates = {m: v for m, v in table.items() if m in MODE_PROFILE}
    if not candidates:
        return None, None
    winner = min(candidates, key=lambda m: candidates[m]["mean_nj_per_delivered_reading"])
    return winner, MODE_PROFILE[winner]


def build_p1_cost_array(table):
    """P1 cost_nj[profile-1][cap_index] array from table.
    Missing cells are 0 (unavailable — policy falls back for those)."""
    arr = [[0, 0, 0], [0, 0, 0]]
    for mode, v in table.items():
        pi = MODE_PROFILE[mode] - 1
        ci = CAP_INDEX[MODE_CAP[mode]]
        arr[pi][ci] = int(v["mean_nj_per_delivered_reading"])
    return arr


def main():
    parser = argparse.ArgumentParser(description="Build Phase 5 cost table from Phase 4 summaries")
    parser.add_argument("--seed", type=int, required=True,
                        help="Filter to runs with this seed (default: all seeds)")
    parser.add_argument("--out", default=str(ROOT / "results/phase_05/cost_table.json"),
                        help="Output path for cost table JSON")
    args = parser.parse_args()

    results_dir = ROOT / "results/phase_04"
    rows = load_summaries(results_dir, seed=args.seed)

    if not rows:
        print(f"No valid Phase 4 runs found in {results_dir} (seed={args.seed})")
        return 1

    table = build_cost_table(rows)
    if set(table) != set(MODE_PROFILE):
        raise ValueError("Calibration requires all four static controls")
    b6_winner_mode, b6_profile = select_b6_winner(table)
    p1_arr = build_p1_cost_array(table)

    out = {
        "produced_utc": datetime.now(timezone.utc).isoformat(),
        "source_runs": len(rows),
        "source_records": rows,
        "source_seed_filter": args.seed,
        "per_mode": table,
        "b6_winner_mode": b6_winner_mode,
        "b6_profile": b6_profile,
        "p1_cost_nj": p1_arr,
        "note": "cost_nj[profile-1][cap_index] where cap_index 0=cap1 1=cap2 2=cap4; 0 means no data"
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()

    print(f"Cost table written: {out_path}")
    print(f"SHA-256: {sha}")
    print(f"B6 winner: {b6_winner_mode} (profile {b6_profile})")
    print(f"P1 cost array: {p1_arr}")
    print(f"Runs included: {len(rows)}")
    for mode, v in sorted(table.items()):
        print(f"  {mode}: {v['mean_nj_per_delivered_reading']:.0f} nJ/reading "
              f"(n={v['samples']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
