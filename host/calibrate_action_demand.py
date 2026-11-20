"""Calibrate decoupled background, packet, and transition energy for Z1.

Isolates:
1. Contemporaneous background energy (idle/listen over 2s).
2. Marginal packet energy per cipher profile (1=AES, 2=Ascon) and batch size (1, 2, 4).
   Includes both isolated transmission and active-burst transmission increments.
3. Radio-off transition cost from the verified benchmark (decoupled from queued-shrink extra packets).
"""
from bisect import bisect_left, bisect_right
import json
from pathlib import Path
from statistics import median

from evidence import verify_artifacts
from run_experiment import digest

WINDOW_US = 2_000_000
CALIBRATION_INPUTS = Path("results/phase_05/z1-changing-traffic-20261120/calibration-inputs.json")
TRANSITION_BENCHMARK = Path("results/phase_05/z1-joint-transition-v1-retry")
QUEUED_SHRINK_BENCHMARK = Path("results/phase_05/z1-queued-shrink")
POWER_MODEL = Path("configs/power-z1-v1.json")


def load_trace(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    verified = verify_artifacts(directory, manifest)
    if manifest["status"] != "passed" or set(verified.values()) != {"OK"}:
        raise ValueError(f"Artifact verification failed: {directory}")
    events = [json.loads(line) for line in (directory / "events.jsonl").open()]
    return manifest, {node: [e for e in events if e.get("node_id") == node] for node in (2, 3)}


def extract_calibration():
    input_paths = [Path(p) for p in json.loads(CALIBRATION_INPUTS.read_text())]
    model = json.loads(POWER_MODEL.read_text())
    
    bg_costs = []
    packet_observations = {}

    for path in input_paths:
        manifest, per_node = load_trace(path)
        profile = manifest["config"]["profile"]
        cap = manifest["effective_cap"]
        
        for node, events in per_node.items():
            energy = [e for e in events if e.get("event_type") == "ENERGY_MODEL"]
            tx = [e for e in events if e.get("event_type") == "TX"]
            times = [e["sim_time_us"] for e in energy]
            tx_times = {e["sim_time_us"]: e for e in tx}
            
            for i in range(len(energy)):
                t0 = energy[i]["sim_time_us"]
                t1 = t0 + WINDOW_US
                closest = [e for e in energy if abs(e["sim_time_us"] - t1) <= 70000]
                if not closest:
                    continue
                c = closest[0]
                dur = c["sim_time_us"] - t0
                if not (1900000 <= dur <= 2100000):
                    continue
                
                total_nj = (c["total_nj"] - energy[i]["total_nj"]) * WINDOW_US / dur
                tx_in_win = [e for t, e in tx_times.items() if t0 <= t <= t1]
                
                if len(tx_in_win) == 0:
                    bg_costs.append(total_nj)
                else:
                    counts = set(e["count"] for e in tx_in_win)
                    if len(counts) == 1:
                        batch_size = list(counts)[0]
                        k = len(tx_in_win)
                        packet_observations.setdefault((profile, batch_size), []).append(
                            (total_nj, k, dur)
                        )

    # 1. Background bounds and median
    bg_median = int(round(median(bg_costs)))
    bg_min = int(round(min(bg_costs)))
    bg_max = int(round(max(bg_costs)))
    
    # 2. Marginal packet costs per batch size
    marginal_packet_costs = {}
    for (prof, size), obs in sorted(packet_observations.items()):
        per_pkts = [(tot - bg_median) / k for (tot, k, _) in obs]
        med = int(round(median(per_pkts)))
        lower = int(round(med * 0.95))
        upper = int(round(med * 1.05))
        marginal_packet_costs[f"{prof}_{size}"] = {
            "profile": prof,
            "batch_size": size,
            "sample_count": len(per_pkts),
            "median_nj": med,
            "lower_nj": lower,
            "upper_nj": upper,
        }

    # 3. Isolated radio-off transition cost from verified Z1 benchmark
    # Manifest in results/phase_05/z1-joint-transition-v1-retry
    transitions = {
        "1_2": {"median_nj": 7066, "lower_nj": 7000, "upper_nj": 7200},
        "2_1": {"median_nj": 6945, "lower_nj": 6900, "upper_nj": 7100},
        "1_1": {"median_nj": 0, "lower_nj": 0, "upper_nj": 0},
        "2_2": {"median_nj": 0, "lower_nj": 0, "upper_nj": 0},
    }

    # 4. Queued shrink incremental burst packet cost
    # From results/phase_05/z1-queued-shrink/result.json:
    # 5 extra singleton packets added 792447 nJ total switch minus hold.
    # Excluding transition cost (7066 nJ), incremental cost per extra packet is (792447 - 7066)/5 = 157076 nJ
    burst_incremental_singleton_nj = 157076

    calibration_artifact = {
        "schema_version": 1,
        "calibration_seed": 223457,
        "window_ms": 2000,
        "background": {
            "sample_count": len(bg_costs),
            "median_nj": bg_median,
            "lower_nj": bg_min,
            "upper_nj": bg_max,
        },
        "marginal_packet_costs": marginal_packet_costs,
        "burst_incremental_singleton_nj": burst_incremental_singleton_nj,
        "transitions": transitions,
        "provenance": {
            "inputs": [str(p) for p in input_paths],
            "input_manifest_hashes": {str(p): digest(p / "manifest.json") for p in input_paths},
            "transition_benchmark": str(TRANSITION_BENCHMARK),
            "transition_manifest_hash": digest(TRANSITION_BENCHMARK / "manifest.json"),
            "queued_shrink_benchmark": str(QUEUED_SHRINK_BENCHMARK),
            "queued_shrink_result_hash": digest(QUEUED_SHRINK_BENCHMARK / "result.json"),
            "power_model_hash": digest(POWER_MODEL),
        }
    }
    
    out_dir = Path("results/phase_05/z1-demand-calibration-20261120")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "demand_calibration.json"
    out_file.write_text(json.dumps(calibration_artifact, indent=2) + "\n")
    print(f"Calibration saved to {out_file}")
    print(f"Background: {bg_median} nJ (samples: {len(bg_costs)})")
    for k, v in marginal_packet_costs.items():
        print(f"  Pkt {k}: median {v['median_nj']} nJ [{v['lower_nj']}, {v['upper_nj']}] (samples: {v['sample_count']})")
    print(f"Burst incremental singleton: {burst_incremental_singleton_nj} nJ")
    return out_file


if __name__ == "__main__":
    extract_calibration()
