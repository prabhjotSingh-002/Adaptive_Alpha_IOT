#!/usr/bin/env python3
"""
Phase 3: 4-Run Fast Diagnostic Gate for Plan C
Evaluates:
  Diag 1: Lossless (Rx=1.00, Tx=1.00, Seed 123456) Plan C (B1+D)
  Diag 2: Lossy Outlier (Rx=0.75, Tx=0.85, Seed 345678) Plan B + B1 (Hysteresis Only)
  Diag 3: Lossy Outlier (Rx=0.75, Tx=0.85, Seed 345678) Plan B + D (Leaf Sleep Only)
  Diag 4: Lossy Outlier (Rx=0.75, Tx=0.85, Seed 345678) Plan C (B1+D Combined)
"""

import os
import sys
import re
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Resolve workspace root (works inside Linux / WSL or Windows)
RUNNER_DIR = Path(__file__).resolve().parent
LEGACY_DIR = RUNNER_DIR.parent
ROOT = LEGACY_DIR.parent

SCENARIOS_DIR = LEGACY_DIR / "scenarios"
RESULTS_DIR = LEGACY_DIR / "results_plan_c"
DIAG_DIR = RESULTS_DIR / "diag"
DIAG_DIR.mkdir(parents=True, exist_ok=True)
GEN_SCENARIOS_DIR = LEGACY_DIR / "scenarios_dyn"
GEN_SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

CONTAINER = "contiker/contiki-ng:develop"
COOJA_BIN = "/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja"
CONTIKI_DIR = "/home/user/contiki-ng"

VOLTS = 3.0
I_CPU_A = 0.0042        # 4.2 mA active CPU
I_LPM_A = 0.0000533     # 53.3 uA LPM3
I_TX_A  = 0.0174        # 17.4 mA Radio TX
I_RX_A  = 0.0188        # 18.8 mA Radio RX
RTIMER_HZ = 32768.0
LPM_53UA_MW = 0.1600    # Model B baseline LPM (53.3 uA * 3.0V)

SENSOR_IDS_15 = list(range(2, 16))

def generate_scenario_file(base_csc: Path, seed: int, out_csc: Path):
    content = base_csc.read_text(errors="replace")
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
    per_sensor_seqs = {nid: set() for nid in sensor_ids}
    tx_packet_count = 0

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
            # Matches standard Plan B and Plan C with optional leaf_mode and sleep_cycles
            m = re.search(r'RSLAB,(\d+),DYN_STATS,alarm=(\d+),etx_cap=(\d+),cap4=(\d+),aoi=(\d+),end=(\d+),max_etx=(\d+),last_etx=(\d+)(?:,leaf_mode=(\d+),sleep_cycles=(\d+))?', l)
            if m:
                nid = int(m.group(1))
                leaf_m = int(m.group(9)) if m.group(9) is not None else 0
                sleep_c = int(m.group(10)) if m.group(10) is not None else 0
                dyn_stats[nid] = {
                    "alarm": int(m.group(2)),
                    "etx_cap": int(m.group(3)),
                    "cap4": int(m.group(4)),
                    "aoi": int(m.group(5)),
                    "end": int(m.group(6)),
                    "max_etx": int(m.group(7)),
                    "last_etx": int(m.group(8)),
                    "leaf_mode": leaf_m,
                    "sleep_cycles": sleep_c
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

    # Leaf vs relay separation
    leaf_nodes = [nid for nid, st in dyn_stats.items() if st.get("leaf_mode", 0) == 1]
    relay_nodes = [nid for nid in sensor_ids if nid not in leaf_nodes]

    leaf_powers = [node_powers[nid]["model_b_total_mw"] for nid in leaf_nodes if nid in node_powers]
    relay_powers = [node_powers[nid]["model_b_total_mw"] for nid in relay_nodes if nid in node_powers]
    leaf_rx_powers = [node_powers[nid]["rx_mw"] for nid in leaf_nodes if nid in node_powers]
    relay_rx_powers = [node_powers[nid]["rx_mw"] for nid in relay_nodes if nid in node_powers]

    mean_leaf_mw = round(sum(leaf_powers) / len(leaf_powers), 4) if leaf_powers else 0.0
    mean_relay_mw = round(sum(relay_powers) / len(relay_powers), 4) if relay_powers else 0.0
    mean_leaf_rx_mw = round(sum(leaf_rx_powers) / len(leaf_rx_powers), 4) if leaf_rx_powers else 0.0
    mean_relay_rx_mw = round(sum(relay_rx_powers) / len(relay_rx_powers), 4) if relay_rx_powers else 0.0

    # Key node powers
    node3_mw = node_powers.get(3, {}).get("model_b_total_mw", 0.0)
    node4_mw = node_powers.get(4, {}).get("model_b_total_mw", 0.0)
    node8_mw = node_powers.get(8, {}).get("model_b_total_mw", 0.0)

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
        "node3_model_b_mw": node3_mw,
        "node4_model_b_mw": node4_mw,
        "node8_model_b_mw": node8_mw,
        "leaf_nodes": leaf_nodes,
        "relay_nodes": relay_nodes,
        "mean_leaf_mw": mean_leaf_mw,
        "mean_relay_mw": mean_relay_mw,
        "mean_leaf_rx_mw": mean_leaf_rx_mw,
        "mean_relay_rx_mw": mean_relay_rx_mw,
        "dyn_stats": dyn_stats,
        "node_powers": node_powers
    }

def run_simulation(run_id: str, csc_path: Path, sensor_defines: str, root_defines: str, sensor_ids: list, force: bool = False):
    out_dir = DIAG_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "COOJA.testlog"
    json_file = out_dir / f"{run_id}.json"

    if not force and json_file.exists():
        try:
            with open(json_file) as f:
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
        f"make -j6 root.z1 TARGET=z1 DEFINES={root_defines} > /dev/null 2>&1; "
        f"rm -rf sensor.z1 sensor.co obj_z1/queuebuf.o contiki-z1.a; "
        f"make -j6 sensor.z1 TARGET=z1 DEFINES={sensor_defines} > /dev/null 2>&1; "
        f"{COOJA_BIN} --no-gui --contiki={CONTIKI_DIR} "
        f"--logdir=/workspace/legacy_stack/results_plan_c/diag/{run_id} "
        f"/workspace/{csc_path.relative_to(ROOT).as_posix()} > /dev/null 2>&1"
    )

    # Windows WSL or Linux host path
    wsl_root = "/mnt/c/Users/Yatin Singh/Documents/Btech Project - 1/Adaptive_Alpha_IOT_legacy"
    contiki_ng_path = "/home/yatin_04/adaptiveAlpha_IOT/external/contiki-ng"

    docker_cmd = [
        "docker", "run", "--rm",
        "--mount", f"type=bind,source={contiki_ng_path},destination=/home/user/contiki-ng",
        "-v", f"{wsl_root}:/workspace",
        CONTAINER,
        "bash", "-c", cmd
    ]

    t0 = time.time()
    res = subprocess.run(docker_cmd, capture_output=True, text=True)
    elapsed = round(time.time() - t0, 1)

    if res.returncode != 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR in {run_id}: exit={res.returncode}")
        print("STDERR:", res.stderr[-500:] if res.stderr else "")

    parsed = parse_run_log(log_file, sensor_ids)
    if parsed:
        parsed["run_id"] = run_id
        parsed["elapsed_wall_s"] = elapsed
        with open(json_file, "w") as f:
            json.dump(parsed, f, indent=2)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] DONE: {run_id} ({elapsed}s) -> PDR: {parsed['pdr']}%, Mean Power: {parsed['mean_model_b_mw']} mW, Alarm Lat: {parsed['mean_alarm_lat_ms']} ms")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] FAILED to parse log for {run_id}")
    return parsed

def main():
    print("================================================================================")
    print("PHASE 3: PLAN C 4-RUN FAST DIAGNOSTIC GATE")
    print("Target: Zolertia Z1 (15 Nodes, AES-128)")
    print("================================================================================")

    base_lossless = SCENARIOS_DIR / "test-15nodes.csc"
    base_lossy    = SCENARIOS_DIR / "test-15nodes-rx075-tx085.csc"

    csc_diag1 = GEN_SCENARIOS_DIR / "diag1_lossless_s123456.csc"
    csc_diag_lossy = GEN_SCENARIOS_DIR / "diag_lossy_s345678.csc"

    generate_scenario_file(base_lossless, 123456, csc_diag1)
    generate_scenario_file(base_lossy, 345678, csc_diag_lossy)

    results = {}

    # Common base defines for sensor & root
    base_sens = "LAB_PROFILE=1,LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12,LAB_ENABLE_AES=1,ENABLE_SPIKE_TRACE=1,ENABLE_DYN_BATCH=1"
    base_root = "LAB_PROFILE=1,LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12,LAB_ENABLE_AES=1,ENABLE_SPIKE_TRACE=1,IS_ROOT=1"

    # Diag 1: Lossless Plan C (B1+D)
    print("\n--- RUN 1/4: Diag 1 (Lossless Rx=1.00, Seed 123456, Plan C: B1+D) ---")
    d1_sens = f"{base_sens},ENABLE_MRHOF_HYST=1,ENABLE_LEAF_RDC_SLEEP=1"
    d1_root = f"{base_root},ENABLE_MRHOF_HYST=1"
    results["diag1"] = run_simulation("diag1_lossless_planc_aes_s123456", csc_diag1, d1_sens, d1_root, SENSOR_IDS_15, force=True)

    # Diag 2: Lossy Outlier Seed 345678 - Plan B + B1 (Hysteresis Only)
    print("\n--- RUN 2/4: Diag 2 (Lossy Rx=0.75/Tx=0.85, Seed 345678, Plan B + B1 Hysteresis Only) ---")
    d2_sens = f"{base_sens},ENABLE_MRHOF_HYST=1"
    d2_root = f"{base_root},ENABLE_MRHOF_HYST=1"
    results["diag2"] = run_simulation("diag2_lossy_planb_hyst_aes_s345678", csc_diag_lossy, d2_sens, d2_root, SENSOR_IDS_15, force=False)

    # Diag 3: Lossy Outlier Seed 345678 - Plan B + D (Leaf Sleep Only)
    print("\n--- RUN 3/4: Diag 3 (Lossy Rx=0.75/Tx=0.85, Seed 345678, Plan B + D Leaf Sleep Only) ---")
    d3_sens = f"{base_sens},ENABLE_LEAF_RDC_SLEEP=1"
    d3_root = f"{base_root}"
    results["diag3"] = run_simulation("diag3_lossy_planb_leaf_aes_s345678", csc_diag_lossy, d3_sens, d3_root, SENSOR_IDS_15, force=True)

    # Diag 4: Lossy Outlier Seed 345678 - Plan C (B1 + D Combined)
    print("\n--- RUN 4/4: Diag 4 (Lossy Rx=0.75/Tx=0.85, Seed 345678, Plan C: B1+D Combined) ---")
    d4_sens = f"{base_sens},ENABLE_MRHOF_HYST=1,ENABLE_LEAF_RDC_SLEEP=1"
    d4_root = f"{base_root},ENABLE_MRHOF_HYST=1"
    results["diag4"] = run_simulation("diag4_lossy_planc_combined_aes_s345678", csc_diag_lossy, d4_sens, d4_root, SENSOR_IDS_15, force=True)

    # Save summary
    summary_path = RESULTS_DIR / "diag_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    # Load Plan B baseline from dyn_b_summary.json
    plan_b_summary_path = LEGACY_DIR / "results_dyn_b" / "dyn_b_summary.json"
    with open(plan_b_summary_path) as f:
        pb_data = json.load(f)

    pb_s1_aes = pb_data["scenario_1_lossless"]["aes"]["dyn_b"]
    pb_s2_aes_s345 = pb_data["raw_runs"]["s2_lossy_aes_dyn_b_s345678"]

    print("\n" + "="*80)
    print("PHASE 3 DIAGNOSTIC AUDIT SCORECARD vs. LOCKED PLAN B BASELINE")
    print("="*80)

    # Diag 1 vs Plan B Lossless
    d1 = results["diag1"]
    print("\n1. DIAG 1: LOSSLESS (Rx=1.00, Tx=1.00, Seed 123456)")
    print(f"  Plan B Baseline:  PDR = {pb_s1_aes['pdr']}%, Mean Power = {pb_s1_aes['mean_model_b_mw']} mW, Alarm Lat = {pb_s1_aes['mean_alarm_lat_ms']} ms")
    print(f"  Plan C (B1+D):     PDR = {d1['pdr']}%, Mean Power = {d1['mean_model_b_mw']} mW, Alarm Lat = {d1['mean_alarm_lat_ms']} ms")
    pwr_delta = ((d1['mean_model_b_mw'] - pb_s1_aes['mean_model_b_mw']) / pb_s1_aes['mean_model_b_mw']) * 100.0
    print(f"  Network Power Delta: {pwr_delta:+.2f}%")
    print(f"  Leaf Nodes Detected: {d1['leaf_nodes']}")
    print(f"  Leaf Mean Power: {d1['mean_leaf_mw']} mW (Rx: {d1['mean_leaf_rx_mw']} mW)")
    print(f"  Relay Mean Power: {d1['mean_relay_mw']} mW (Rx: {d1['mean_relay_rx_mw']} mW)")

    # Diags 2, 3, 4 vs Plan B Lossy Outlier Seed 345678
    d2 = results["diag2"]
    d3 = results["diag3"]
    d4 = results["diag4"]
    print("\n2. LOSS-CHURN OUTLIER AUDIT (Rx=0.75, Tx=0.85, Seed 345678)")
    print(f"{'Metric':<25} | {'Plan B (Locked)':<15} | {'Diag 2 (Hyst)':<15} | {'Diag 3 (Leaf)':<15} | {'Diag 4 (Plan C)':<15}")
    print("-" * 95)
    print(f"{'PDR (%)':<25} | {pb_s2_aes_s345['pdr']:<15.2f} | {d2['pdr']:<15.2f} | {d3['pdr']:<15.2f} | {d4['pdr']:<15.2f}")
    print(f"{'Mean Power (mW)':<25} | {pb_s2_aes_s345['mean_model_b_mw']:<15.4f} | {d2['mean_model_b_mw']:<15.4f} | {d3['mean_model_b_mw']:<15.4f} | {d4['mean_model_b_mw']:<15.4f}")
    print(f"{'Energy (uJ/rdg)':<25} | {pb_s2_aes_s345['tot_energy_uj_reading']:<15.2f} | {d2['tot_energy_uj_reading']:<15.2f} | {d3['tot_energy_uj_reading']:<15.2f} | {d4['tot_energy_uj_reading']:<15.2f}")
    print(f"{'Node 3 Relay (mW)':<25} | {pb_s2_aes_s345['node3_model_b_mw']:<15.4f} | {d2['node3_model_b_mw']:<15.4f} | {d3['node3_model_b_mw']:<15.4f} | {d4['node3_model_b_mw']:<15.4f}")
    pb_node4 = pb_s2_aes_s345.get("node_powers", {}).get("4", {}).get("model_b_total_mw", 0.0)
    pb_node8 = pb_s2_aes_s345.get("node_powers", {}).get("8", {}).get("model_b_total_mw", 0.0)
    print(f"{'Node 4 Churn (mW)':<25} | {pb_node4:<15.4f} | {d2['node4_model_b_mw']:<15.4f} | {d3['node4_model_b_mw']:<15.4f} | {d4['node4_model_b_mw']:<15.4f}")
    print(f"{'Node 8 Churn (mW)':<25} | {pb_node8:<15.4f} | {d2['node8_model_b_mw']:<15.4f} | {d3['node8_model_b_mw']:<15.4f} | {d4['node8_model_b_mw']:<15.4f}")
    print(f"{'Leaf Nodes Sleeping':<25} | {'None':<15} | {'None':<15} | {str(d3['leaf_nodes']):<15} | {str(d4['leaf_nodes']):<15}")
    print("=" * 95)

if __name__ == "__main__":
    main()
