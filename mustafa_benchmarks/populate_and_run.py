#!/usr/bin/env python3
"""Populate existing valid results and run all remaining simulations."""
import json
import sys
from pathlib import Path

# Add benchmark directory to path
BENCHMARK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCHMARK_DIR))

from run_mustafa_experiments import execute_run, generate_reports, RESULTS_DIR, RAW_DIR

def get_latest_existing_records():
    by_key = {}
    for p in sorted(RAW_DIR.glob("*/metrics.json")):
        try:
            data = json.loads(p.read_text())
            pwr = data.get("power")
            if pwr and pwr.get("delivered_readings_count", 0) > 0:
                key = (data["nodes"], data["cipher"], data["batch_cap"])
                by_key[key] = data
        except Exception:
            pass
    return list(by_key.values())

def main():
    records = get_latest_existing_records()
    print(f"Loaded {len(records)} existing valid simulation records.")
    
    # Save baseline records and initial report
    generate_reports(records)

    # Remaining runs to execute
    remaining = [
        (5, "speck", 2),
        (5, "speck", 4),
        (5, "present", 2),
        (5, "present", 4),
        (10, "speck", 1),
        (10, "speck", 2),
        (10, "speck", 4),
        (10, "present", 1),
        (10, "present", 2),
        (10, "present", 4),
    ]

    for nodes, cipher, cap in remaining:
        print(f"\n==========================================")
        print(f"STARTING RUN: {nodes} Nodes | {cipher.upper()} | Cap k={cap}")
        print(f"==========================================")
        rec = execute_run(nodes, cipher, cap)
        
        # Replace or add
        records = [r for r in records if not (r["nodes"] == nodes and r["cipher"] == cipher and r["batch_cap"] == cap)]
        records.append(rec)
        generate_reports(records)
        
        p = rec.get("power", {})
        print(f"COMPLETED: Delivered: {p.get('delivered_readings_count')}/{nodes*12} | "
              f"Tx: {p.get('tx_mw')} mW | Duty Total: {p.get('duty_total_mw')} mW | "
              f"Tx Energy/Reading: {p.get('tx_energy_uj_reading')} uJ")

    print("\nALL SIMULATIONS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
