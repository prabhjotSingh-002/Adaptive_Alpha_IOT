"""Explain the saved cap-one comparison without changing its scoring windows."""
from bisect import bisect_left, bisect_right
import csv
import json
from pathlib import Path
from statistics import median

from evaluate_affordability import OUT, WINDOW_US, load_control, samples

COMPONENTS = ("cpu", "lpm", "deep", "tx", "listen")


def details(events, ordinal, model):
    energy, times = samples(events)
    generated = [row for row in events if row["event_type"] == "GEN"]
    origin = generated[0]["sim_time_us"]
    start = bisect_left(times, origin + ordinal * WINDOW_US)
    stop = bisect_left(times, times[start] + WINDOW_US)
    prior = bisect_right(times, times[start] - WINDOW_US) - 1
    begin, end = times[start], times[stop]
    reading_times = [row["sim_time_us"] for row in generated]
    first, last = (bisect_right(reading_times, time) for time in (begin, end))
    raw = [row for row in events if row["event_type"] == "ENERGY_RAW"]
    raw_times = [row["sim_time_us"] for row in raw]
    a, b = (raw[bisect_right(raw_times, time) - 1] for time in (begin, end))
    duration = end - begin
    result = dict(prior_us=times[prior] - origin, start_us=begin - origin,
                  end_us=end - origin, past_duration_us=begin - times[prior],
                  future_duration_us=duration, phase_start=(first - 1) // 9,
                  phase_end=(last - 1) // 9,
                  readings=" ".join(str(row["reading_id"]) for row in generated[first:last]),
                  packets=sum(row["event_type"] == "TX" and begin < row["sim_time_us"] <= end
                              for row in events))
    denominator = 1000 * model["frequency"]
    for component, current in zip(COMPONENTS, model["nanoamps"]):
        coefficient = current * model["millivolts"]
        delta = b[component] * coefficient // denominator - a[component] * coefficient // denominator
        result[f"{component}_nj"] = delta * WINDOW_US / duration
    return result


def main():
    report = json.loads((OUT / "result.json").read_text())
    model = json.loads(Path("configs/power-z1-v1.json").read_text())
    controls = [load_control("changing", mode, report["seed"])[1] for mode in ("B1", "B2")]
    windows = {(row["node"], row["ordinal"]): row for row in report["changing"]}
    rows = []
    for (node, ordinal), window in sorted(windows.items()):
        aes, ascon = [details(control[node], ordinal, model) for control in controls]
        observed = window["observed_nj"]
        forecasts = window["forecast_nj"]
        for arm, total in zip((aes, ascon), observed):
            if abs(sum(arm[f"{key}_nj"] for key in COMPONENTS) - total) > 2:
                raise ValueError(f"Energy reconciliation failed for {node}/{ordinal}")
        row = dict(node=node, ordinal=ordinal, same_readings=aes["readings"] == ascon["readings"],
                   same_phase=all(aes[key] == ascon[key] for key in ("phase_start", "phase_end")),
                   start_skew_us=ascon["start_us"] - aes["start_us"],
                   end_skew_us=ascon["end_us"] - aes["end_us"],
                   observed_gap_nj=observed[1] - observed[0],
                   forecast_gap_nj=forecasts[1] - forecasts[0])
        for name, arm in (("aes", aes), ("ascon", ascon)):
            row.update({f"{name}_{key}": value for key, value in arm.items()})
        rows.append(row)
    with (OUT / "window-diagnosis.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print("windows", len(rows), "same readings", sum(row["same_readings"] for row in rows),
          "same phase", sum(row["same_phase"] for row in rows))
    for key in ("start_skew_us", "end_skew_us"):
        print(key, "median abs", median(abs(row[key]) for row in rows))


if __name__ == "__main__":
    main()
