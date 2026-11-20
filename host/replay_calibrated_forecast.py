"""Replay and qualify the calibrated queue/demand forecast on seed 123459."""
from bisect import bisect_left, bisect_right
from collections import Counter
import json
from pathlib import Path
from statistics import median

from audit_battery_forecast import generation_times
from diagnose_affordability import details
from evaluate_affordability import OUT, load_control, WINDOW_US, rate
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


def evaluate_replay():
    bg_bounds, bg_median, packet_costs, transitions = load_calibration()
    old = json.loads((OUT / "result.json").read_text())
    seed = old["seed"]
    
    # Load controls
    controls = {}
    for workload in ("changing", "finite"):
        for mode in ("B1", "B2"):
            controls[workload, mode] = load_control(workload, mode, seed)[1]
            
    model = json.loads(POWER_MODEL.read_text())
    
    # 1. Changing traffic replay
    # In cap-1 controls (B1, B2), current action is AES cap 1 (profile 1) or Ascon cap 1 (profile 2)
    changing_scores = Counter()
    changing_records = []
    
    for row in old["changing"]:
        node, ordinal = row["node"], row["ordinal"]
        budget = row["budget_nj"]
        observed = row["observed_nj"]
        actual = row["actual"]
        
        # Decision state from B1 events
        events = controls["changing", "B1"][node]
        generation = generation_times(events)
        d = details(events, ordinal, model)
        start_us = generation[0] + d["start_us"]
        
        # Readings generated before start_us
        past_gen = [t for t in generation if t <= start_us]
        future_gen = [t for t in generation if t > start_us]
        
        # In cap 1, previous readings were drained on send.
        # Check if an un-transmitted reading is pending at start_us
        tx_events = [e["sim_time_us"] for e in events if e.get("event_type") == "TX" and e.get("node_id") == node]
        past_tx = [t for t in tx_events if t <= start_us]
        unacked = len(past_gen) - len(past_tx)
        queued_ages_ms = tuple([max(0, int((start_us - past_gen[-i]) / 1000)) for i in range(1, unacked + 1)]) if unacked > 0 else ()
        
        next_arrival_ms = int(round((future_gen[0] - start_us) / 1000.0)) if future_gen else None
        
        # Measured rate interval from recent arrivals
        if len(past_gen) >= 2:
            recent_intervals = [b - a for a, b in zip(past_gen[-5:-1], past_gen[-4:])]
            interval_ms = int(round(median(recent_intervals) / 1000.0)) if recent_intervals else 500
            if interval_ms <= 0:
                interval_ms = 500
        else:
            interval_ms = 500
            
        forecast_medians = []
        forecast_bounds = []
        for candidate_prof in (1, 2):
            batches = expected_batches(
                queued_ages_ms=queued_ages_ms,
                next_arrival_ms=next_arrival_ms,
                arrival_interval_ms=interval_ms,
                cap=1,
                deadline_ms=3000,
                horizon_ms=2000
            )
            # Bounds
            bounds = forecast_bounds_nj(
                background=bg_bounds,
                batches=batches,
                packet_costs=packet_costs,
                current=1,
                candidate=candidate_prof,
                transitions=transitions
            )
            forecast_bounds.append(bounds)
            # Point estimate for median
            pt_pkt = sum(packet_costs[(candidate_prof, s)][0] * 0.5 + packet_costs[(candidate_prof, s)][1] * 0.5 for s in batches)
            pt_trans = transitions[(1, candidate_prof)][0] * 0.5 + transitions[(1, candidate_prof)][1] * 0.5
            forecast_medians.append(bg_median + pt_pkt + pt_trans)
            
        predicted = [cost <= budget for cost in forecast_medians]
        
        changing_scores["cases"] += 1
        changing_scores["exact"] += (predicted == actual)
        if sum(actual) == 1:
            changing_scores["one_fit_cases"] += 1
            changing_scores["one_fit_exact"] += (predicted == actual)
        changing_scores["false_affordable_actions"] += sum(p is True and not a for p, a in zip(predicted, actual))
        
        changing_records.append({
            "node": node,
            "ordinal": ordinal,
            "budget_nj": budget,
            "observed_nj": observed,
            "forecast_nj": forecast_medians,
            "predicted": predicted,
            "actual": actual,
        })
        
    # 2. Finite budget survival check
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
                # 2s demand forecast for static cap 1 under 1000ms traffic (2 packets in 2s)
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
            
    # Evaluation checks against frozen acceptance thresholds
    total_cases = changing_scores["cases"]
    exact_cases = changing_scores["exact"]
    one_fit_cases = changing_scores["one_fit_cases"]
    one_fit_exact = changing_scores["one_fit_exact"]
    
    exact_pct = exact_cases * 100.0 / total_cases if total_cases else 0
    one_fit_pct = one_fit_exact * 100.0 / one_fit_cases if one_fit_cases else 0
    
    # Check finite crossing false-affordable
    finite_false_count = sum(sum(r["predicted_affordable"] for r in rows) for rows in finite_crossings.values())
    
    changing_pass = (exact_pct >= 90.0 and one_fit_cases >= 10 and one_fit_pct >= 80.0)
    finite_pass = (finite_false_count == 0 and all(len(rows) > 0 for rows in finite_crossings.values()))
    
    result = {
        "status": "passed" if (changing_pass and finite_pass) else "failed",
        "changing_pass": changing_pass,
        "finite_pass": finite_pass,
        "scores": dict(changing_scores),
        "exact_percentage": exact_pct,
        "one_fit_percentage": one_fit_pct,
        "finite_false_affordable": finite_false_count,
        "finite_crossings_count": {k: len(v) for k, v in finite_crossings.items()},
        "calibration_sha256": digest(CALIB_FILE),
    }
    
    out_dir = Path("results/phase_05/z1-affordability-qualified")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "replay_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    evaluate_replay()
