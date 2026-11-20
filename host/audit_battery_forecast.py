"""Evaluate an offline two-second node energy forecast on curated Z1 traces."""
import argparse
from bisect import bisect_left
from collections import defaultdict
import json
from pathlib import Path
from statistics import median

from evidence import verify_artifacts
from run_experiment import digest

WINDOW_US = 2_000_000
CHANGING = Path("results/phase_05/z1-changing-traffic-20261120")
CLOSURE = Path("results/phase_05/z1-closure-20261120")
FINITE = Path("results/phase_05/20261117T024127105801Z-P1-2")


def trace(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    verified = verify_artifacts(directory, manifest)
    if manifest["status"] != "passed" or set(verified.values()) != {"OK"}:
        raise ValueError(directory)
    events = [json.loads(line) for line in (directory / "events.jsonl").open()]
    return manifest, {node: [e for e in events if e["node_id"] == node]
                      for node in (2, 3)}


def windows(events, start, stop):
    energy = [e for e in events if e["event_type"] == "ENERGY_MODEL"]
    times = [e["sim_time_us"] for e in energy]
    for target in range(start, stop - WINDOW_US + 1, WINDOW_US):
        index = bisect_left(times, target)
        if index >= len(times):
            continue
        end = bisect_left(times, times[index] + WINDOW_US)
        if end >= len(times) or times[end] > stop:
            continue
        a, b = energy[index], energy[end]
        duration = b["sim_time_us"] - a["sim_time_us"]
        cost = (b["total_nj"] - a["total_nj"]) * WINDOW_US / duration
        yield a, b, cost


def generation_times(events):
    return [e["sim_time_us"] for e in events if e["event_type"] == "GEN"]


def calibration(directories):
    table = {}
    for path in directories:
        manifest, per_node = trace(path)
        config = manifest["config"]
        if config["seed"] != 223457:
            raise ValueError("Unexpected calibration seed")
        for node, events in per_node.items():
            generation = generation_times(events)
            if len(generation) != 27:
                raise ValueError("Unexpected calibration workload")
            segments = {200: [(generation[0], generation[8]), (generation[18], generation[26])],
                        25: [(generation[9], generation[17])]}
            for rate, spans in segments.items():
                observed = [cost for start, stop in spans for _, _, cost in windows(events, start, stop)]
                key = (node, config["profile"], manifest["effective_cap"], rate)
                if key in table or not observed:
                    raise ValueError(key)
                table[key] = median(observed)
    if len(table) != 24:
        raise ValueError("Incomplete calibration")
    return table


def predict(table, node, profile, cap, rate):
    if not 25 <= rate <= 200:
        return None
    low, high = (table[node, profile, cap, r] for r in (25, 200))
    return low + (high - low) * (rate - 25) / 175


def validate(table, path, adaptive):
    manifest, per_node = trace(path)
    config = manifest["config"]
    if config["seed"] == 223457:
        raise ValueError("Evaluation seed overlaps calibration")
    records = []
    for node, events in per_node.items():
        generation = generation_times(events)
        if len(generation) < 2:
            continue
        policies = [e for e in events if e["event_type"] == "POLICY"]
        features = [e for e in events if e["event_type"] == "FEATURE"]
        for index, (a, b, actual) in enumerate(windows(events, generation[0], generation[-1])):
            start, end = a["sim_time_us"], b["sim_time_us"]
            if adaptive:
                known = [e for e in policies if e["sim_time_us"] <= start]
                rates = [e for e in features if e["sim_time_us"] <= start]
                if not known or not rates:
                    continue
                profile, cap = known[-1]["profile"], known[-1]["cap"]
                rate = rates[-1]["rate_hz_x100"]
                stable = all((e["profile"], e["cap"]) == (profile, cap)
                             for e in policies if start < e["sim_time_us"] <= end)
                stable &= all(e["rate_hz_x100"] == rate for e in features
                              if start < e["sim_time_us"] <= end)
                if not stable:
                    continue
            else:
                profile, cap = config["profile"], manifest["effective_cap"]
                rate = 100000 // config["period_ms"]
            forecast = predict(table, node, profile, cap, rate)
            if forecast is None:
                continue
            remaining = a["remaining_nj"] if config.get("lifetime") else None
            records.append(dict(run=path.name, node=node, profile=profile, cap=cap,
                                rate_hz_x100=rate, window=index, start_us=start, end_us=end,
                                predicted_nj=forecast, observed_nj=actual,
                                relative_error=abs(forecast-actual)/actual,
                                remaining_nj=remaining,
                                predicted_affordable=(forecast <= remaining) if remaining is not None else None,
                                observed_affordable=(actual <= remaining) if remaining is not None else None))
    return records



def rank_cap_one(records):
    """Replay affordability at the midpoint of the two predicted demands."""
    groups = defaultdict(dict)
    for record in records:
        if record["cap"] == 1:
            groups[record["node"], record["window"]][record["profile"]] = record
    comparisons = []
    for (node, window), profiles in sorted(groups.items()):
        if set(profiles) != {1, 2}:
            continue
        left, right = profiles[1], profiles[2]
        budget = (left["predicted_nj"] + right["predicted_nj"]) / 2
        predicted = [p for p, row in profiles.items() if row["predicted_nj"] <= budget]
        observed = [p for p, row in profiles.items() if row["observed_nj"] <= budget]
        comparisons.append(dict(node=node, window=window, hypothetical_residual_nj=budget,
                                predicted_affordable=sorted(predicted), observed_affordable=sorted(observed)))
    return dict(windows=len(comparisons),
                matching=sum(row["predicted_affordable"] == row["observed_affordable"] for row in comparisons),
                comparisons=comparisons,
                scope="hypothetical residuals on paired static cap-one traces")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    calibration_inputs = [Path(path) for path in json.loads((CHANGING / "calibration-inputs.json").read_text())]
    table = calibration(calibration_inputs)
    changing_run = Path(json.loads((CHANGING / "mote-attempts.json").read_text())[-1]["directory"])
    current_controls = [Path("results/phase_04") / r["run_id"] for r in
                        json.loads((CLOSURE / "phase4-audit.json").read_text())["current_static"]]
    suites = {"changing_p1": [changing_run], "finite_p1_historical_source": [FINITE],
              "stationary_static": current_controls}
    report = dict(scope="offline forecast, no firmware ranking validation",
                  horizon_us=WINDOW_US, calibration={"|".join(map(str, k)): v for k, v in table.items()},
                  inputs={str(path): digest(path / "manifest.json") for path in
                          [*calibration_inputs, *(path for paths in suites.values() for path in paths)]},
                  script_sha256=digest(Path(__file__)), validation={})
    for name, paths in suites.items():
        records = [r for path in paths for r in validate(table, path, name != "stationary_static")]
        errors = [r["relative_error"] for r in records]
        checks = [r for r in records if r["remaining_nj"] is not None]
        report["validation"][name] = dict(
            windows=len(records), median_absolute_relative_error=median(errors) if errors else None,
            max_absolute_relative_error=max(errors, default=None),
            affordability_correct=sum(r["predicted_affordable"] == r["observed_affordable"] for r in checks),
            affordability_checks=len(checks),
            observed_unaffordable=sum(not r["observed_affordable"] for r in checks), records=records)
        print(name, len(records), "median/max absolute relative error",
              median(errors) if errors else None, max(errors, default=None),
              "observed unaffordable", sum(not r["observed_affordable"] for r in checks))
    ranks = rank_cap_one(report["validation"]["stationary_static"]["records"])
    report["cap_one_ranking_diagnostic"] = ranks
    print("hypothetical cap-one affordable set matches", ranks["matching"], "/", ranks["windows"])
    args.out.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
