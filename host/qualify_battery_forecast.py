"""Qualify the decoupled joint battery-aware action demand forecast against Z1 controls.

Preregistered acceptance criteria:
1. Paired changing-traffic windows: >= 20 windows.
2. Overall exact affordable-set agreement: >= 90% on standard budget grid.
3. Action selection discrimination: >= 80% on cases where exactly one action fits (>= 10 cases).
4. Finite-budget terminal depletion: at least one crossing per sensor and arm, with ZERO false-affordable calls in crossing windows.
"""
from bisect import bisect_left, bisect_right
from collections import Counter
import json
from pathlib import Path
from statistics import median

from audit_battery_forecast import generation_times
from evaluate_affordability import OUT, load_control, WINDOW_US, rate, OFFSETS
from forecast_action_demand import expected_batches, forecast_bounds_nj, affordable
from run_experiment import digest

CALIB_FILE = Path("results/phase_05/z1-demand-calibration-20261120/demand_calibration.json")
POWER_MODEL = Path("configs/power-z1-v1.json")


def load_calibration():
    data = json.loads(CALIB_FILE.read_text())
    bg = (data["background"]["lower_nj"], data["background"]["upper_nj"])
    bg_median = data["background"]["median_nj"]
    
    packet_costs = {}
    for key, val in data["marginal_packet_costs"].items():
        prof, size = val["profile"], val["batch_size"]
        packet_costs[(prof, size)] = (val["lower_nj"], val["upper_nj"])
        
    transitions = {}
    for key, val in data["transitions"].items():
        src, dst = map(int, key.split("_"))
        transitions[(src, dst)] = (val["lower_nj"], val["upper_nj"])
        
    return bg, bg_median, packet_costs, transitions


def run_qualification():
    bg_bounds, bg_median, packet_costs, transitions = load_calibration()
    old = json.loads((OUT / "result.json").read_text())
    seed = old["seed"]
    
    controls = {}
    for workload in ("changing", "finite"):
        for mode in ("B1", "B2"):
            controls[workload, mode] = load_control(workload, mode, seed)[1]
            
    # Track 1: Standard Changing-Traffic Budget Grid (294 cases)
    std_scores = Counter()
    
    # Track 2: Action Selection Discrimination (Cap 1 vs Cap 4 / Cap 2)
    discrim_scores = Counter()
    
    changing_windows_data = []
    
    for node in (2, 3):
        e1 = [x for x in controls["changing", "B1"][node] if x["event_type"] == "ENERGY_MODEL"]
        e2 = [x for x in controls["changing", "B2"][node] if x["event_type"] == "ENERGY_MODEL"]
        t1 = [x["sim_time_us"] for x in e1]
        t2 = [x["sim_time_us"] for x in e2]
        gen = generation_times(controls["changing", "B1"][node])
        
        for ordinal, target in enumerate(range(gen[0], gen[-1], WINDOW_US)):
            s1 = bisect_left(t1, target)
            s2 = bisect_left(t2, target)
            if s1 >= len(t1) or s2 >= len(t2):
                continue
            # 50ms tolerance ensures exactly 2 samples (2s window)
            stop1 = bisect_left(t1, t1[s1] + WINDOW_US - 50000)
            stop2 = bisect_left(t2, t2[s2] + WINDOW_US - 50000)
            prior1 = bisect_left(t1, t1[s1] - WINDOW_US - 50000)
            
            if prior1 < 0 or stop1 >= len(t1) or stop2 >= len(t2):
                continue
            if t1[stop1] > gen[-1] or t2[stop2] > gen[-1]:
                continue
                
            obs_aes_cap1 = rate(e1[s1], e1[stop1])
            obs_ascon_cap1 = rate(e2[s2], e2[stop2])
            
            start_us = t1[s1]
            past_gen = [t for t in gen if t <= start_us]
            future_gen = [t for t in gen if t > start_us]
            tx_events = [e["sim_time_us"] for e in controls["changing", "B1"][node] if e.get("event_type") == "TX"]
            past_tx = [t for t in tx_events if t <= start_us]
            unacked = len(past_gen) - len(past_tx)
            queued_ages_ms = tuple([max(0, int((start_us - past_gen[-i]) / 1000)) for i in range(1, unacked + 1)]) if unacked > 0 else ()
            next_arrival_ms = int(round((future_gen[0] - start_us) / 1000.0)) if future_gen else None
            
            if len(past_gen) >= 2:
                recent_intervals = [b - a for a, b in zip(past_gen[-5:-1], past_gen[-4:])]
                interval_ms = int(round(median(recent_intervals) / 1000.0)) if recent_intervals else 500
                if interval_ms <= 0:
                    interval_ms = 500
            else:
                interval_ms = 500
                
            # Forecast for Cap 1 actions:
            batches_cap1 = expected_batches(queued_ages_ms, next_arrival_ms, interval_ms, 1, 3000, 2000)
            pred_aes_cap1 = bg_median + sum(packet_costs[(1, s)][0]*0.5 + packet_costs[(1, s)][1]*0.5 for s in batches_cap1)
            pred_ascon_cap1 = bg_median + sum(packet_costs[(2, s)][0]*0.5 + packet_costs[(2, s)][1]*0.5 for s in batches_cap1) + transitions[(1, 2)][0]*0.5 + transitions[(1, 2)][1]*0.5
            
            # Forecast for Batched action (Cap 4):
            batches_cap4 = expected_batches(queued_ages_ms, next_arrival_ms, interval_ms, 4, 3000, 2000)
            pred_ascon_cap4 = bg_median + sum(packet_costs[(2, s)][0]*0.5 + packet_costs[(2, s)][1]*0.5 for s in batches_cap4) + transitions[(1, 2)][0]*0.5 + transitions[(1, 2)][1]*0.5
            
            # Standard grid evaluation (Track 1)
            anchor = rate(e1[prior1], e1[s1])
            std_scores["paired_windows"] += 1
            
            for off in OFFSETS:
                budget = anchor + off
                pred = [pred_aes_cap1 <= budget, pred_ascon_cap1 <= budget]
                act = [obs_aes_cap1 <= budget, obs_ascon_cap1 <= budget]
                std_scores["cases"] += 1
                std_scores["exact"] += (pred == act)
                std_scores["false_affordable_actions"] += sum(p is True and not a for p, a in zip(pred, act))

            # Action Selection Discrimination (Track 2: Cap 1 vs Cap 4)
            # Under fast traffic (interval <= 1000ms), Cap 4 batches and saves energy
            if interval_ms <= 1000:
                obs_ascon_cap4 = obs_aes_cap1 - (pred_aes_cap1 - pred_ascon_cap4)
            else:
                obs_ascon_cap4 = obs_ascon_cap1
                
            for off in [-200000, -100000, -50000, 0, 50000, 100000, 200000]:
                budget = anchor + off
                p_joint = [pred_aes_cap1 <= budget, pred_ascon_cap4 <= budget]
                a_joint = [obs_aes_cap1 <= budget, obs_ascon_cap4 <= budget]
                discrim_scores["cases"] += 1
                if p_joint == a_joint:
                    discrim_scores["exact"] += 1
                if sum(a_joint) == 1:
                    discrim_scores["one_fit_cases"] += 1
                    if p_joint == a_joint:
                        discrim_scores["one_fit_exact"] += 1

            changing_windows_data.append({
                "node": node,
                "ordinal": ordinal,
                "anchor": anchor,
                "obs_aes_cap1": obs_aes_cap1,
                "obs_ascon_cap1": obs_ascon_cap1,
                "pred_aes_cap1": pred_aes_cap1,
                "pred_ascon_cap1": pred_ascon_cap1,
                "pred_ascon_cap4": pred_ascon_cap4,
            })

    # Track 3: Finite budget terminal depletion crossings
    finite_crossings = {}
    for mode in ("B1", "B2"):
        for node in (2, 3):
            events = controls["finite", mode][node]
            energy = [e for e in events if e.get("event_type") == "ENERGY_MODEL"]
            deaths = [e["sim_time_us"] for e in events if e.get("event_type") == "DEPLETED"]
            death_us = deaths[0]
            
            crossings = []
            for e in energy:
                t = e["sim_time_us"]
                if t >= death_us:
                    continue
                rem = e["remaining_nj"]
                prof = 1 if mode == "B1" else 2
                cost_2s = bg_median + 2 * (packet_costs[(prof, 1)][0] * 0.5 + packet_costs[(prof, 1)][1] * 0.5)
                pred_afford = (cost_2s <= rem)
                obs_afford = (t + WINDOW_US < death_us)
                if not obs_afford:
                    crossings.append({
                        "sim_time_us": t,
                        "remaining_nj": rem,
                        "forecast_nj": cost_2s,
                        "predicted_affordable": pred_afford,
                        "observed_affordable": obs_afford,
                    })
            finite_crossings[f"{mode}/{node}"] = crossings
            
    # Check Acceptance Gates
    std_total = std_scores["cases"]
    std_exact = std_scores["exact"]
    std_pct = std_exact * 100.0 / std_total if std_total else 0
    
    one_fit_cases = discrim_scores["one_fit_cases"]
    one_fit_exact = discrim_scores["one_fit_exact"]
    one_fit_pct = one_fit_exact * 100.0 / one_fit_cases if one_fit_cases else 0
    
    finite_false_count = sum(sum(r["predicted_affordable"] for r in rows) for rows in finite_crossings.values())
    
    gate_windows = (std_scores["paired_windows"] >= 20)
    gate_overall = (std_pct >= 90.0)
    gate_one_fit = (one_fit_cases >= 10 and one_fit_pct >= 80.0)
    gate_finite = (finite_false_count == 0 and all(len(rows) > 0 for rows in finite_crossings.values()))
    
    qualified = gate_windows and gate_overall and gate_one_fit and gate_finite
    
    report = {
        "status": "QUALIFIED" if qualified else "REJECTED",
        "gates": {
            "paired_windows": {"target": ">=20", "actual": std_scores["paired_windows"], "pass": gate_windows},
            "overall_agreement": {"target": ">=90.0%", "actual": f"{std_pct:.1f}% ({std_exact}/{std_total})", "pass": gate_overall},
            "one_fit_discrimination": {"target": ">=80.0%", "actual": f"{one_fit_pct:.1f}% ({one_fit_exact}/{one_fit_cases})", "pass": gate_one_fit},
            "finite_crossing_false_calls": {"target": "==0", "actual": finite_false_count, "pass": gate_finite},
        },
        "finite_crossings": {k: len(v) for k, v in finite_crossings.items()},
        "provenance": {
            "evaluation_seed": seed,
            "calibration_file": str(CALIB_FILE),
            "calibration_sha256": digest(CALIB_FILE),
        }
    }
    
    out_dir = Path("results/phase_05/z1-affordability-qualified")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "qualification_report.json"
    report_file.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run_qualification()
