"""Score the frozen cap-one forecast against verified Z1 controls."""
from bisect import bisect_left, bisect_right
from collections import Counter
import json
from pathlib import Path
from statistics import median

from audit_battery_forecast import WINDOW_US, generation_times, trace
from run_experiment import digest

OUT = Path("results/phase_05/z1-affordability-v3")
TRAIN = OUT.parent / "z1-ranking-diagnosis-20261120/holdout-result.json"
OFFSETS = (-100000, -50000, -25000, 0, 25000, 50000, 100000)


def rate(a, b):
    return (b["total_nj"] - a["total_nj"]) * WINDOW_US / (b["sim_time_us"] - a["sim_time_us"])


def load_control(workload, mode, seed):
    receipt = json.loads((OUT / f"{workload}-{mode}.json").read_text())
    path = Path(receipt["directory"])
    if digest(path / "manifest.json") != receipt["manifest_sha256"]:
        raise ValueError(f"Manifest changed: {path}")
    manifest, events = trace(path)
    config = manifest["config"]
    if (manifest["mode"], manifest["effective_cap"], config["seed"]) != (mode, 1, seed):
        raise ValueError(f"Wrong control: {path}")
    expected = (500, 4000, 27, False) if workload == "changing" else (1000, None, 96, True)
    actual = (config["period_ms"], config.get("middle_period_ms"),
              config["readings_per_sensor"], config["lifetime"])
    if actual != expected or (config["lifetime"] and config["energy_budget_nj"] != 4097000000):
        raise ValueError(f"Wrong workload: {path}")
    cohort = (manifest["pins"], manifest["platform"], manifest["clients"], config["power_model"],
              config["energy_sample_ms"], {key: value for key, value in manifest["source_hashes"].items()
                                           if key != "firmware/generated-conf.h"})
    return cohort, events


def samples(events):
    energy = [event for event in events if event["event_type"] == "ENERGY_MODEL"]
    return energy, [event["sim_time_us"] for event in energy]


def changing_windows(events):
    energy, times = samples(events)
    generated = generation_times(events)
    rows = {}
    for ordinal, target in enumerate(range(generated[0], generated[-1], WINDOW_US)):
        start = bisect_left(times, target)
        if start == len(times):
            continue
        stop = bisect_left(times, times[start] + WINDOW_US)
        prior = bisect_right(times, times[start] - WINDOW_US) - 1
        if prior >= 0 and stop < len(times) and times[stop] <= generated[-1]:
            rows[ordinal] = (rate(energy[prior], energy[start]), rate(energy[start], energy[stop]))
    return rows


def finite_windows(events):
    energy, times = samples(events)
    deaths = [event["sim_time_us"] for event in events if event["event_type"] == "DEPLETED"]
    death, = deaths
    for start, time in enumerate(times):
        prior = bisect_right(times, time - WINDOW_US) - 1
        if prior < 0 or time >= death:
            continue
        remaining = energy[start]["remaining_nj"]
        forecast = rate(energy[prior], energy[start])
        yield dict(start_us=time, death_us=death, remaining_nj=remaining,
                   forecast_nj=forecast, predicted_affordable=forecast <= remaining,
                   observed_affordable=time + WINDOW_US < death)


def main():
    seed = json.loads((OUT / "protocol.json").read_text())["seed"]
    prior = json.loads(TRAIN.read_text())
    offsets = {
        node: median(row["rows"]["2"]["observed_nj"] - row["rows"]["1"]["observed_nj"]
                     for row in prior["comparisons"] if row["node"] == node)
        for node in (2, 3)
    }
    cohorts = []
    groups = {}
    for workload in ("changing", "finite"):
        for mode in ("B1", "B2"):
            cohort, groups[workload, mode] = load_control(workload, mode, seed)
            cohorts.append(cohort)
    if any(cohort != cohorts[0] for cohort in cohorts[1:]):
        raise ValueError("Incompatible controls")
    counts = Counter()
    changing = []
    finite = {}
    for node in (2, 3):
        aes = changing_windows(groups["changing", "B1"][node])
        ascon = changing_windows(groups["changing", "B2"][node])
        for ordinal in sorted(aes.keys() & ascon.keys()):
            anchor, actual_aes = aes[ordinal]
            forecast = [anchor, anchor + offsets[node]]
            observed = [actual_aes, ascon[ordinal][1]]
            counts["paired_windows"] += 1
            for offset in OFFSETS:
                budget = anchor + offset
                predicted = [cost <= budget for cost in forecast]
                actual = [cost <= budget for cost in observed]
                counts["grid_cases"] += 1
                counts["exact"] += predicted == actual
                if sum(actual) == 1:
                    counts["one_action"] += 1
                    counts["one_action_exact"] += predicted == actual
                changing.append(dict(node=node, ordinal=ordinal, budget_nj=budget,
                                     forecast_nj=forecast, observed_nj=observed,
                                     predicted=predicted, actual=actual))
        for mode in ("B1", "B2"):
            finite[f"{mode}/{node}"] = list(finite_windows(groups["finite", mode][node]))
    crossings = {key: [row for row in rows if not row["observed_affordable"]]
                 for key, rows in finite.items()}
    changing_pass = (
        counts["paired_windows"] >= 20 and 10 * counts["exact"] >= 9 * counts["grid_cases"]
        and counts["one_action"] >= 10
        and 5 * counts["one_action_exact"] >= 4 * counts["one_action"]
    )
    finite_pass = all(rows and not any(row["predicted_affordable"] for row in rows)
                      for rows in crossings.values())
    report = dict(seed=seed, calibration_sha256=digest(TRAIN), offsets_nj=offsets,
                  counts=counts, changing_pass=changing_pass, finite_pass=finite_pass,
                  joint_policy_qualified=False, changing=changing, finite=finite)
    (OUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(dict(counts), "changing pass:", changing_pass, "finite pass:", finite_pass)
    print("Finite crossings and false-affordable counts:",
          {key: (len(rows), sum(row["predicted_affordable"] for row in rows))
           for key, rows in crossings.items()})


if __name__ == "__main__":
    main()
