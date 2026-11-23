#!/usr/bin/env python3
"""
Finalized 24-Run Phase 4 Benchmark Matrix for Plan B Adaptive Batching.
Topology: 15-node Zolertia Z1 on Contiki 2.7 (ContikiMAC @ 8 Hz, 240s envelope)
Hardware Constants: 3.0V, 4.2mA CPU, 17.4mA Tx, 18.8mA Rx, Model B LPM = 0.1600 mW

Scenarios:
- Scenario 1 (Lossless + Spikes, Rx=1.0, Tx=1.0, Seed=123456):
  Modes: Static k=1, Static k=4, Plan B
  Ciphers: AES-128-CCM, SPECK-64/128
  (6 runs)

- Scenario 2 (Multi-Hop Dual-Loss + Spikes, Rx=0.75, Tx=0.85, Seeds: 123456, 234567, 345678):
  Modes: Static k=4, VoI-Only, Plan B
  Ciphers: AES-128-CCM, SPECK-64/128
  (18 runs: 3 modes x 2 ciphers x 3 seeds)

Total: 24 runs
"""

import os
import re
import sys
import json
import time
import math
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
LEGACY_DIR = ROOT / "legacy_stack"
SCENARIOS_DIR = LEGACY_DIR / "scenarios"
RESULTS_DIR = LEGACY_DIR / "results_dyn_b"
MATRIX_DIR = RESULTS_DIR / "matrix"
MATRIX_DIR.mkdir(parents=True, exist_ok=True)
GEN_SCENARIOS_DIR = LEGACY_DIR / "scenarios_dyn"
GEN_SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

CONTAINER = "contiker/contiki-ng:develop"
COOJA_BIN = "/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja"
CONTIKI_DIR = "/home/user/contiki-ng"

VOLTS = 3.0
I_CPU_A = 0.0042        # 4.2 mA active CPU
I_LPM_A = 0.0000011     # 1.1 uA LPM3
I_TX_A  = 0.0174        # 17.4 mA Radio TX
I_RX_A  = 0.0188        # 18.8 mA Radio RX
RTIMER_HZ = 32768.0
LPM_53UA_MW = 0.1600    # Model B baseline LPM (53.3 uA * 3.0V)

CIPHER_PROFILES = {
    "aes":   {"profile": 1, "enable_flag": ",LAB_ENABLE_AES=1"},
    "speck": {"profile": 3, "enable_flag": ",LAB_ENABLE_SPECK=1"},
}

def generate_scenario_file(base_csc: Path, seed: int, out_csc: Path):
    """Generate scenario CSC file with explicit randomseed."""
    content = base_csc.read_text(errors="replace")
    # Replace randomseed
    content = re.sub(r'<randomseed>.*?</randomseed>', f'<randomseed>{seed}</randomseed>', content)
    out_csc.write_text(content)
    return out_csc

def parse_run_log(log_path: Path, sensor_ids: list, warmup_s: float = 100.0, measure_end_s: float = 220.0):
    if not log_path.exists():
        return None

    warmup_us = int(warmup_s * 1000000)
    measure_end_us = int(measure_end_s * 1000000)

    ticks_warmup = {}
    ticks_end = {}
    rx_readings = []
    dyn_stats = {}
    tx_packet_count = 0
    per_sensor_seqs = {nid: set() for nid in sensor_ids}

    lines = log_path.read_text(errors="replace").splitlines()

    for l in lines:
        m_eng = re.match(r"^(\d+),(\d+),RSLAB,\2,ENERGY_RAW,(\d+),(\d+),0,(\d+),(\d+)", l)
        if m_eng:
            t_us = int(m_eng.group(1))
            nid = int(m_eng.group(2))
            c = int(m_eng.group(3))
            l_val = int(m_eng.group(4))
            tx = int(m_eng.group(5))
            rx = int(m_eng.group(6))
            if nid in sensor_ids:
                if t_us <= warmup_us:
                    ticks_warmup[nid] = (t_us, c, l_val, tx, rx)
                if t_us <= measure_end_us:
                    ticks_end[nid] = (t_us, c, l_val, tx, rx)

        if ",TX" in l:
            for nid in sensor_ids:
                if f",{nid},TX" in l or f",{nid},RSLAB,{nid},TX" in l:
                    tx_packet_count += 1
                    break

        parts = l.split(",")
        if len(parts) >= 8 and parts[2] == "RSLAB" and parts[4] == "RX":
            t_ms = float(parts[0]) / 1000.0
            rid = int(parts[5])
            val = int(parts[6])
            c_ms = float(parts[7])
            nid = rid >> 16
            seq = rid & 0xFFFF
            lat = max(0.0, t_ms - c_ms)
            is_alarm = (seq in (5, 10))
            if nid in per_sensor_seqs:
                per_sensor_seqs[nid].add(seq)
            rx_readings.append({
                "rx_time_ms": t_ms,
                "reading_id": rid,
                "node_id": nid,
                "seq": seq,
                "value": val,
                "created_ms": c_ms,
                "latency_ms": lat,
                "is_alarm": is_alarm
            })

        if "DYN_STATS" in l:
            m = re.search(r'RSLAB,(\d+),DYN_STATS,alarm=(\d+),etx_cap=(\d+),cap4=(\d+),aoi=(\d+),end=(\d+),max_etx=(\d+),last_etx=(\d+)', l)
            if m:
                nid = int(m.group(1))
                dyn_stats[nid] = {
                    "alarm": int(m.group(2)),
                    "etx_cap": int(m.group(3)),
                    "cap4": int(m.group(4)),
                    "aoi": int(m.group(5)),
                    "end": int(m.group(6)),
                    "max_etx": int(m.group(7)),
                    "last_etx": int(m.group(8))
                }

    # Energest calculation
    cpu_list, lpm_list, tx_list, rx_list, total_list = [], [], [], [], []
    node_powers = {}
    for nid in sensor_ids:
        if nid not in ticks_warmup or nid not in ticks_end:
            continue
        t0, c0, l0, tx0, rx0 = ticks_warmup[nid]
        t1, c1, l1, tx1, rx1 = ticks_end[nid]
        dt_s = (t1 - t0) / 1000000.0
        dticks = dt_s * RTIMER_HZ
        if dticks <= 0:
            continue

        cpu_mw = ((c1 - c0) / dticks) * (VOLTS * I_CPU_A * 1000.0)
        lpm_mw = ((l1 - l0) / dticks) * (VOLTS * I_LPM_A * 1000.0)
        tx_mw  = ((tx1 - tx0)  / dticks) * (VOLTS * I_TX_A * 1000.0)
        rx_mw  = ((rx1 - rx0)  / dticks) * (VOLTS * I_RX_A * 1000.0)
        tot_mw = cpu_mw + lpm_mw + tx_mw + rx_mw

        cpu_list.append(cpu_mw)
        lpm_list.append(lpm_mw)
        tx_list.append(tx_mw)
        rx_list.append(rx_mw)
        total_list.append(tot_mw)

        node_powers[nid] = {
            "cpu_mw": round(cpu_mw, 4),
            "tx_mw": round(tx_mw, 4),
            "rx_mw": round(rx_mw, 4),
            "lpm_mw": round(lpm_mw, 4),
            "total_mw": round(tot_mw, 4),
            "model_b_total_mw": round(cpu_mw + tx_mw + rx_mw + LPM_53UA_MW, 4)
        }

    n_nodes = len(cpu_list)
    if n_nodes == 0:
        return None

    mean_cpu = sum(cpu_list) / n_nodes
    mean_tx  = sum(tx_list)  / n_nodes
    mean_rx  = sum(rx_list)  / n_nodes
    mean_model_b = mean_cpu + mean_tx + mean_rx + LPM_53UA_MW

    total_expected = len(sensor_ids) * 12
    delivered = len(rx_readings)
    pdr = (delivered / float(total_expected) * 100.0) if total_expected > 0 else 0.0

    active_duration_s = measure_end_s - warmup_s  # 120s
    delivered_per_sensor = delivered / float(n_nodes) if n_nodes > 0 else 0.0
    tot_energy_uj_reading = (mean_model_b * active_duration_s * 1000.0) / delivered_per_sensor if delivered_per_sensor > 0 else 0.0

    alarm_lats = [r["latency_ms"] for r in rx_readings if r["is_alarm"]]
    norm_lats = [r["latency_ms"] for r in rx_readings if not r["is_alarm"]]

    mean_alarm_lat = sum(alarm_lats) / len(alarm_lats) if alarm_lats else 0.0
    mean_norm_lat = sum(norm_lats) / len(norm_lats) if norm_lats else 0.0

    # Clean Outage Burst Metrics
    all_outage_burst_lens = []
    max_consec_drops_overall = 0

    for nid in sensor_ids:
        delivered_seqs = per_sensor_seqs[nid]
        consec = 0
        for s in range(1, 13):
            if s not in delivered_seqs:
                consec += 1
            else:
                if consec > 0:
                    all_outage_burst_lens.append(consec)
                    if consec > max_consec_drops_overall:
                        max_consec_drops_overall = consec
                    consec = 0
        if consec > 0:
            all_outage_burst_lens.append(consec)
            if consec > max_consec_drops_overall:
                max_consec_drops_overall = consec

    mean_outage_burst_len = (sum(all_outage_burst_lens) / len(all_outage_burst_lens)) if all_outage_burst_lens else 0.0

    # ETX flush stats
    total_alarm_flushes = sum(st.get("alarm", 0) for st in dyn_stats.values())
    total_etx_cap_flushes = sum(st.get("etx_cap", 0) for st in dyn_stats.values())
    total_cap4_flushes = sum(st.get("cap4", 0) for st in dyn_stats.values())
    total_aoi_flushes = sum(st.get("aoi", 0) for st in dyn_stats.values())
    total_end_flushes = sum(st.get("end", 0) for st in dyn_stats.values())
    nodes_etx_ge_192 = [nid for nid, st in dyn_stats.items() if st.get("max_etx", 0) >= 192]
    max_etx_vals = [st.get("max_etx", 0) for st in dyn_stats.values()]
    min_max_etx = min(max_etx_vals) if max_etx_vals else 0
    max_max_etx = max(max_etx_vals) if max_etx_vals else 0

    # Node 3 Bottleneck Relay stats
    node3_model_b = node_powers.get(3, {}).get("model_b_total_mw", 0.0)

    return {
        "pdr": round(pdr, 2),
        "delivered": delivered,
        "total_expected": total_expected,
        "tx_packet_count": tx_packet_count,
        "mean_model_b_mw": round(mean_model_b, 4),
        "mean_cpu_mw": round(mean_cpu, 4),
        "mean_tx_mw": round(mean_tx, 4),
        "mean_rx_mw": round(mean_rx, 4),
        "tot_energy_uj_reading": round(tot_energy_uj_reading, 2),
        "mean_alarm_lat_ms": round(mean_alarm_lat, 1),
        "mean_norm_lat_ms": round(mean_norm_lat, 1),
        "max_consecutive_missing": max_consec_drops_overall,
        "max_consecutive_missing_s": max_consec_drops_overall * 10,
        "mean_outage_burst_len": round(mean_outage_burst_len, 2),
        "node3_model_b_mw": round(node3_model_b, 4),
        "total_alarm_flushes": total_alarm_flushes,
        "total_etx_cap_flushes": total_etx_cap_flushes,
        "total_cap4_flushes": total_cap4_flushes,
        "total_aoi_flushes": total_aoi_flushes,
        "total_end_flushes": total_end_flushes,
        "nodes_etx_ge_192_count": len(nodes_etx_ge_192),
        "min_max_etx": min_max_etx,
        "max_max_etx": max_max_etx,
        "dyn_stats": dyn_stats,
        "node_powers": node_powers
    }

def run_simulation(run_id: str, csc_path: Path, defines: str, sensor_ids: list, force: bool = False):
    out_dir = MATRIX_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "COOJA.testlog"
    json_path = out_dir / "result.json"

    if not force and json_path.exists():
        try:
            with open(json_path) as f:
                cached = json.load(f)
            if cached.get("pdr", 0) > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] SKIP: {run_id} (Cached PDR: {cached['pdr']}%, Model B: {cached['mean_model_b_mw']} mW)")
                return cached
        except Exception:
            pass

    cmd = (
        f"set -eu; "
        f"cd /workspace/legacy_stack/firmware; "
        f"rm -rf obj_z1 *.z1 *.co contiki-z1.a; "
        f"make root.z1 TARGET=z1 DEFINES={defines},IS_ROOT=1 > /dev/null 2>&1; "
        f"rm -rf sensor.z1 sensor.co obj_z1/queuebuf.o contiki-z1.a; "
        f"make sensor.z1 TARGET=z1 DEFINES={defines} > /dev/null 2>&1; "
        f"{COOJA_BIN} --no-gui --contiki={CONTIKI_DIR} "
        f"--logdir=/workspace/legacy_stack/results_dyn_b/matrix/{run_id} "
        f"/workspace/{csc_path.relative_to(ROOT).as_posix()} > /dev/null 2>&1"
    )

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{ROOT}/external/contiki-ng:/home/user/contiki-ng:ro",
        "-v", f"{ROOT}:/workspace",
        CONTAINER,
        "bash", "-c", cmd
    ]

    t0 = time.time()
    res = subprocess.run(docker_cmd, capture_output=True, text=True)
    elapsed = round(time.time() - t0, 1)

    if res.returncode != 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR {run_id}: returncode {res.returncode}")
        print(f"STDERR: {res.stderr}")
        return None

    data = parse_run_log(log_file, sensor_ids)
    if data is None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR {run_id}: Failed to parse log {log_file}")
        return None

    data["run_id"] = run_id
    data["elapsed_s"] = elapsed

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] DONE: {run_id} ({elapsed}s) | PDR: {data['pdr']}% ({data['delivered']}/{data['total_expected']}) | Model B: {data['mean_model_b_mw']} mW | Alm Lat: {data['mean_alarm_lat_ms']} ms | Norm Lat: {data['mean_norm_lat_ms']} ms | Peak Gap: {data['max_consecutive_missing_s']}s | ETX Clamps: {data['total_etx_cap_flushes']}")
    return data

def compute_mean_std(values: list):
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    std = math.sqrt(variance)
    return round(mean, 4), round(std, 4)

def main():
    sensor_ids_15 = list(range(2, 16))
    base_csc_lossless = SCENARIOS_DIR / "test-15nodes.csc"
    base_csc_lossy = SCENARIOS_DIR / "test-15nodes-rx075-tx085.csc"

    raw_matrix_results = {}

    print("\n" + "="*85)
    print("STARTING 24-RUN BENCHMARK MATRIX (15 NODES, CONTIKI 2.7 CONTIKIMAC 8 HZ)")
    print("="*85)

    # -------------------------------------------------------------
    # Scenario 1: Lossless + Injected Spikes (Rx=1.0, Tx=1.0, Seed=123456)
    # Modes: static_k1, static_k4, dyn_b | Ciphers: aes, speck
    # -------------------------------------------------------------
    print("\n--- SCENARIO 1: LOSSLESS + INJECTED SPIKES (Rx=1.00, Tx=1.00, Seed=123456) ---")
    csc_s1 = GEN_SCENARIOS_DIR / "s1_lossless_seed123456.csc"
    generate_scenario_file(base_csc_lossless, 123456, csc_s1)

    s1_modes = ["static_k1", "static_k4", "dyn_b"]
    ciphers = ["aes", "speck"]

    for cipher in ciphers:
        c_cfg = CIPHER_PROFILES[cipher]
        prof = c_cfg["profile"]
        c_flag = c_cfg["enable_flag"]

        for mode in s1_modes:
            run_id = f"s1_lossless_{cipher}_{mode}_s123456"
            if mode == "static_k1":
                defines = f"LAB_PROFILE={prof},LAB_BATCH_CAP=1,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1"
            elif mode == "static_k4":
                defines = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1"
            elif mode == "dyn_b":
                defines = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,ENABLE_DYN_BATCH=1"

            res = run_simulation(run_id, csc_s1, defines, sensor_ids_15)
            raw_matrix_results[run_id] = res

    # -------------------------------------------------------------
    # Scenario 2: Dual-Loss + Injected Spikes (Rx=0.75, Tx=0.85, Seeds: 123456, 234567, 345678)
    # Modes: static_k4, voi_only, dyn_b | Ciphers: aes, speck
    # -------------------------------------------------------------
    print("\n--- SCENARIO 2: MULTI-HOP DUAL-LOSS + INJECTED SPIKES (Rx=0.75, Tx=0.85, 3 Seeds) ---")
    seeds = [123456, 234567, 345678]
    s2_modes = ["static_k4", "voi_only", "dyn_b"]

    for seed in seeds:
        csc_s2 = GEN_SCENARIOS_DIR / f"s2_lossy_seed{seed}.csc"
        generate_scenario_file(base_csc_lossy, seed, csc_s2)

        for cipher in ciphers:
            c_cfg = CIPHER_PROFILES[cipher]
            prof = c_cfg["profile"]
            c_flag = c_cfg["enable_flag"]

            for mode in s2_modes:
                run_id = f"s2_lossy_{cipher}_{mode}_s{seed}"
                if mode == "static_k4":
                    defines = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1"
                elif mode == "voi_only":
                    defines = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,ENABLE_DYN_BATCH=1,DISABLE_ETX_CLAMP=1"
                elif mode == "dyn_b":
                    defines = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,ENABLE_DYN_BATCH=1"

                res = run_simulation(run_id, csc_s2, defines, sensor_ids_15)
                raw_matrix_results[run_id] = res

    # -------------------------------------------------------------
    # Aggregation & Summary Generation (Mean +- SD)
    # -------------------------------------------------------------
    print("\n" + "="*85)
    print("AGGREGATING RESULTS & GENERATING SUMMARY...")
    print("="*85)

    summary = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "nodes": 15,
            "total_sensors": 14,
            "total_expected_readings_per_run": 168,
            "lossless_seed": 123456,
            "lossy_seeds": seeds,
        },
        "scenario_1_lossless": {},
        "scenario_2_lossy": {},
        "raw_runs": raw_matrix_results
    }

    # Aggregate Scenario 1
    for cipher in ciphers:
        summary["scenario_1_lossless"][cipher] = {}
        # Reference Node 3 power on Static k=1 for FND lifetime extension
        ref_k1_run = raw_matrix_results.get(f"s1_lossless_{cipher}_static_k1_s123456")
        ref_node3_pwr = ref_k1_run.get("node3_model_b_mw", 1.0) if ref_k1_run else 1.0

        for mode in s1_modes:
            r = raw_matrix_results.get(f"s1_lossless_{cipher}_{mode}_s123456")
            if not r:
                continue
            n3_pwr = r.get("node3_model_b_mw", 0.0)
            fnd_ratio = round(ref_node3_pwr / n3_pwr, 2) if n3_pwr > 0 else 1.0
            summary["scenario_1_lossless"][cipher][mode] = {
                "pdr": r["pdr"],
                "delivered": r["delivered"],
                "total_expected": r["total_expected"],
                "tx_packet_count": r["tx_packet_count"],
                "mean_model_b_mw": r["mean_model_b_mw"],
                "mean_cpu_mw": r["mean_cpu_mw"],
                "mean_tx_mw": r["mean_tx_mw"],
                "mean_rx_mw": r["mean_rx_mw"],
                "tot_energy_uj_reading": r["tot_energy_uj_reading"],
                "mean_alarm_lat_ms": r["mean_alarm_lat_ms"],
                "mean_norm_lat_ms": r["mean_norm_lat_ms"],
                "node3_model_b_mw": n3_pwr,
                "fnd_lifetime_ratio": fnd_ratio,
                "total_alarm_flushes": r["total_alarm_flushes"],
                "total_etx_cap_flushes": r["total_etx_cap_flushes"],
                "total_cap4_flushes": r["total_cap4_flushes"],
                "total_end_flushes": r["total_end_flushes"],
            }

    # Aggregate Scenario 2 (Mean +- SD across 3 seeds)
    for cipher in ciphers:
        summary["scenario_2_lossy"][cipher] = {}
        for mode in s2_modes:
            seed_runs = [raw_matrix_results.get(f"s2_lossy_{cipher}_{mode}_s{s}") for s in seeds]
            seed_runs = [r for r in seed_runs if r is not None]

            pdr_mean, pdr_std = compute_mean_std([r["pdr"] for r in seed_runs])
            del_mean, del_std = compute_mean_std([r["delivered"] for r in seed_runs])
            pwr_mean, pwr_std = compute_mean_std([r["mean_model_b_mw"] for r in seed_runs])
            uj_mean, uj_std = compute_mean_std([r["tot_energy_uj_reading"] for r in seed_runs])
            alm_mean, alm_std = compute_mean_std([r["mean_alarm_lat_ms"] for r in seed_runs])
            norm_mean, norm_std = compute_mean_std([r["mean_norm_lat_ms"] for r in seed_runs])
            gap_mean, gap_std = compute_mean_std([r["max_consecutive_missing_s"] for r in seed_runs])
            burst_mean, burst_std = compute_mean_std([r["mean_outage_burst_len"] for r in seed_runs])
            n3_mean, n3_std = compute_mean_std([r["node3_model_b_mw"] for r in seed_runs])
            etx_mean, etx_std = compute_mean_std([r["total_etx_cap_flushes"] for r in seed_runs])

            summary["scenario_2_lossy"][cipher][mode] = {
                "pdr": {"mean": pdr_mean, "std": pdr_std},
                "delivered": {"mean": del_mean, "std": del_std},
                "mean_model_b_mw": {"mean": pwr_mean, "std": pwr_std},
                "tot_energy_uj_reading": {"mean": uj_mean, "std": uj_std},
                "mean_alarm_lat_ms": {"mean": alm_mean, "std": alm_std},
                "mean_norm_lat_ms": {"mean": norm_mean, "std": norm_std},
                "max_consecutive_missing_s": {"mean": gap_mean, "std": gap_std},
                "mean_outage_burst_len": {"mean": burst_mean, "std": burst_std},
                "node3_model_b_mw": {"mean": n3_mean, "std": n3_std},
                "total_etx_cap_flushes": {"mean": etx_mean, "std": etx_std},
                "per_seed_runs": seed_runs
            }

    summary_file = RESULTS_DIR / "dyn_b_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved complete summary to: {summary_file}")
    print("\n" + "="*85)
    print("PHASE 4 BENCHMARK MATRIX COMPLETED SUCCESSFULLY!")
    print("="*85)

if __name__ == "__main__":
    main()
