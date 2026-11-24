#!/usr/bin/env python3
"""
16-Run Full Benchmark Matrix for Plan C (MRHOF Hysteresis + RPL-Aware Leaf RDC Suppression)
Topology: 15-node Zolertia Z1 on Contiki 2.7 (ContikiMAC @ 8 Hz, 240s envelope)
Hardware Constants: 3.0V, 4.2mA CPU, 17.4mA Tx, 18.8mA Rx, Model B LPM = 0.1600 mW

Scenarios:
- Scenario 1 (Lossless + Spikes, Rx=1.0, Tx=1.0, Seed=123456):
  Modes: Plan B + B1 (MRHOF Hysteresis Only), Plan C (Combined B1 + D Leaf Sleep)
  Ciphers: AES-128-CCM, SPECK-64/128
  (4 runs)

- Scenario 2 (Multi-Hop Dual-Loss + Spikes, Rx=0.75, Tx=0.85, Seeds: 123456, 234567, 345678):
  Modes: Plan B + B1 (Hysteresis), Plan C (Combined)
  Ciphers: AES-128-CCM, SPECK-64/128
  (12 runs: 2 modes x 2 ciphers x 3 seeds)

Total: 16 runs
"""

import os
import re
import sys
import json
import time
import math
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
LEGACY_DIR = ROOT / "legacy_stack"
SCENARIOS_DIR = LEGACY_DIR / "scenarios"
RESULTS_DIR = LEGACY_DIR / "results_plan_c"
RAW_RUNS_DIR = RESULTS_DIR / "raw_runs"
RAW_RUNS_DIR.mkdir(parents=True, exist_ok=True)
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

SENSOR_IDS_15 = list(range(2, 16))

CIPHER_PROFILES = {
    "aes":   {"profile": 1, "enable_flag": ",LAB_ENABLE_AES=1"},
    "speck": {"profile": 3, "enable_flag": ",LAB_ENABLE_SPECK=1"},
}

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
            m_c = re.search(r'RSLAB,(\d+),DYN_STATS,alarm=(\d+),etx_cap=(\d+),cap4=(\d+),aoi=(\d+),end=(\d+),max_etx=(\d+),last_etx=(\d+),leaf_mode=(\d+),sleep_cycles=(\d+)', l)
            if m_c:
                nid = int(m_c.group(1))
                dyn_stats[nid] = {
                    "alarm": int(m_c.group(2)),
                    "etx_cap": int(m_c.group(3)),
                    "cap4": int(m_c.group(4)),
                    "aoi": int(m_c.group(5)),
                    "end": int(m_c.group(6)),
                    "max_etx": int(m_c.group(7)),
                    "last_etx": int(m_c.group(8)),
                    "leaf_mode": int(m_c.group(9)),
                    "sleep_cycles": int(m_c.group(10))
                }
            else:
                m_b = re.search(r'RSLAB,(\d+),DYN_STATS,alarm=(\d+),etx_cap=(\d+),cap4=(\d+),aoi=(\d+),end=(\d+),max_etx=(\d+),last_etx=(\d+)', l)
                if m_b:
                    nid = int(m_b.group(1))
                    dyn_stats[nid] = {
                        "alarm": int(m_b.group(2)),
                        "etx_cap": int(m_b.group(3)),
                        "cap4": int(m_b.group(4)),
                        "aoi": int(m_b.group(5)),
                        "end": int(m_b.group(6)),
                        "max_etx": int(m_b.group(7)),
                        "last_etx": int(m_b.group(8)),
                        "leaf_mode": 0,
                        "sleep_cycles": 0
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
    node3_model_b = node_powers.get(3, {}).get("model_b_total_mw", 0.0)
    node4_model_b = node_powers.get(4, {}).get("model_b_total_mw", 0.0)
    node8_model_b = node_powers.get(8, {}).get("model_b_total_mw", 0.0)

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
        "node4_model_b_mw": round(node4_model_b, 4),
        "node8_model_b_mw": round(node8_model_b, 4),
        "leaf_nodes": leaf_nodes,
        "relay_nodes": relay_nodes,
        "mean_leaf_mw": mean_leaf_mw,
        "mean_relay_mw": mean_relay_mw,
        "mean_leaf_rx_mw": mean_leaf_rx_mw,
        "mean_relay_rx_mw": mean_relay_rx_mw,
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

def run_simulation(run_id: str, csc_path: Path, sensor_defines: str, root_defines: str, sensor_ids: list, force: bool = False):
    out_dir = RAW_RUNS_DIR / run_id
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
        f"--logdir=/workspace/legacy_stack/results_plan_c/raw_runs/{run_id} "
        f"/workspace/{csc_path.relative_to(ROOT).as_posix()} > /dev/null 2>&1"
    )

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

def compute_mean_sd(val_list):
    if not val_list:
        return 0.0, 0.0
    mean = sum(val_list) / len(val_list)
    if len(val_list) > 1:
        var = sum((x - mean) ** 2 for x in val_list) / (len(val_list) - 1)
        sd = math.sqrt(var)
    else:
        sd = 0.0
    return round(mean, 4), round(sd, 4)

def main():
    print("================================================================================")
    print("PLAN C FULL 16-RUN BENCHMARK MATRIX")
    print("Topology: 15-node Zolertia Z1 (Contiki 2.7, ContikiMAC @ 8 Hz, 240s envelope)")
    print("Evaluating: Plan B + B1 (MRHOF Hysteresis Only) vs. Plan C (Combined B1 + D Leaf Sleep)")
    print("Ciphers: AES-128-CCM, SPECK-64/128")
    print("================================================================================")

    base_csc_lossless = SCENARIOS_DIR / "test-15nodes.csc"
    base_csc_lossy    = SCENARIOS_DIR / "test-15nodes-rx075-tx085.csc"

    ciphers = ["aes", "speck"]
    modes = ["planb_hyst", "planc"]
    seeds = [123456, 234567, 345678]

    # Pre-populate from diagnostic runs if available
    diag_dir = RESULTS_DIR / "diag"
    diag_mapping = {
        "s2_lossy_aes_planb_hyst_s345678": diag_dir / "diag2_lossy_planb_hyst_aes_s345678",
        "s2_lossy_aes_planc_s345678": diag_dir / "diag4_lossy_planc_combined_aes_s345678",
    }
    for target_run, src_dir in diag_mapping.items():
        target_dir = RAW_RUNS_DIR / target_run
        target_json = target_dir / f"{target_run}.json"
        src_json = src_dir / f"{src_dir.name}.json"
        if not target_json.exists() and src_json.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_json, target_json)
                src_log = src_dir / "COOJA.testlog"
                if src_log.exists():
                    shutil.copy2(src_log, target_dir / "COOJA.testlog")
                print(f"Imported cached diagnostic run: {target_run} from {src_dir.name}")
            except Exception as e:
                print(f"Notice: could not copy diagnostic run {target_run}: {e}")

    raw_matrix_results = {}

    # -------------------------------------------------------------------------
    # Scenario 1: Lossless (Rx=1.00, Tx=1.00, Seed 123456, 4 runs)
    # -------------------------------------------------------------------------
    print("\n--- SCENARIO 1: LOSSLESS + INJECTED SPIKES (Rx=1.00, Tx=1.00, Seed 123456) ---")
    csc_s1 = GEN_SCENARIOS_DIR / "s1_lossless_s123456.csc"
    generate_scenario_file(base_csc_lossless, 123456, csc_s1)

    for cipher in ciphers:
        c_cfg = CIPHER_PROFILES[cipher]
        prof = c_cfg["profile"]
        c_flag = c_cfg["enable_flag"]

        for mode in modes:
            run_id = f"s1_lossless_{cipher}_{mode}_s123456"
            base_s = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,ENABLE_DYN_BATCH=1,ENABLE_MRHOF_HYST=1"
            base_r = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,IS_ROOT=1,ENABLE_MRHOF_HYST=1"

            if mode == "planc":
                s_def = f"{base_s},ENABLE_LEAF_RDC_SLEEP=1"
            else:
                s_def = base_s
            r_def = base_r

            res = run_simulation(run_id, csc_s1, s_def, r_def, SENSOR_IDS_15)
            raw_matrix_results[run_id] = res

    # -------------------------------------------------------------------------
    # Scenario 2: Multi-Hop Dual-Loss + Spikes (Rx=0.75, Tx=0.85, 3 Seeds, 12 runs)
    # -------------------------------------------------------------------------
    print("\n--- SCENARIO 2: MULTI-HOP DUAL-LOSS + INJECTED SPIKES (Rx=0.75, Tx=0.85, 3 Seeds) ---")
    for seed in seeds:
        csc_s2 = GEN_SCENARIOS_DIR / f"s2_lossy_seed{seed}.csc"
        generate_scenario_file(base_csc_lossy, seed, csc_s2)

        for cipher in ciphers:
            c_cfg = CIPHER_PROFILES[cipher]
            prof = c_cfg["profile"]
            c_flag = c_cfg["enable_flag"]

            for mode in modes:
                run_id = f"s2_lossy_{cipher}_{mode}_s{seed}"
                base_s = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,ENABLE_DYN_BATCH=1,ENABLE_MRHOF_HYST=1"
                base_r = f"LAB_PROFILE={prof},LAB_BATCH_CAP=4,LAB_WARMUP_S=100,LAB_TOTAL_READINGS=12{c_flag},ENABLE_SPIKE_TRACE=1,IS_ROOT=1,ENABLE_MRHOF_HYST=1"

                if mode == "planc":
                    s_def = f"{base_s},ENABLE_LEAF_RDC_SLEEP=1"
                else:
                    s_def = base_s
                r_def = base_r

                res = run_simulation(run_id, csc_s2, s_def, r_def, SENSOR_IDS_15)
                raw_matrix_results[run_id] = res

    # -------------------------------------------------------------------------
    # Aggregation & Summary Generation
    # -------------------------------------------------------------------------
    print("\n" + "="*85)
    print("AGGREGATING RESULTS & GENERATING MASTER PLAN C SUMMARY...")
    print("="*85)

    # Load Static k=1 reference from legacy_matrix_summary.json for FND lifetime calculation
    legacy_summary_path = ROOT / "legacy_stack" / "legacy_matrix_summary.json"
    k1_pwr_ref = {"aes": 2.1481, "speck": 2.1384} # Fallback to known ground truth
    if legacy_summary_path.exists():
        try:
            with open(legacy_summary_path) as f:
                leg_data = json.load(f)
            k1_pwr_ref["aes"] = leg_data["scenarios"]["scenario_1_lossless"]["aes"]["static_k1"]["node3_model_b_mw"]
            k1_pwr_ref["speck"] = leg_data["scenarios"]["scenario_1_lossless"]["speck"]["static_k1"]["node3_model_b_mw"]
        except Exception:
            pass

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
        for mode in modes:
            r = raw_matrix_results.get(f"s1_lossless_{cipher}_{mode}_s123456")
            if not r:
                continue
            n3_pwr = r.get("node3_model_b_mw", 0.0)
            ref_n3 = k1_pwr_ref.get(cipher, 2.1481)
            fnd_ratio = round(ref_n3 / n3_pwr, 2) if n3_pwr > 0 else 1.0

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
                "node4_model_b_mw": r.get("node4_model_b_mw", 0.0),
                "node8_model_b_mw": r.get("node8_model_b_mw", 0.0),
                "fnd_lifetime_ratio": fnd_ratio,
                "leaf_nodes": r.get("leaf_nodes", []),
                "mean_leaf_mw": r.get("mean_leaf_mw", 0.0),
                "mean_relay_mw": r.get("mean_relay_mw", 0.0),
                "mean_leaf_rx_mw": r.get("mean_leaf_rx_mw", 0.0),
                "mean_relay_rx_mw": r.get("mean_relay_rx_mw", 0.0),
                "total_alarm_flushes": r.get("total_alarm_flushes", sum(st.get("alarm", 0) for st in r.get("dyn_stats", {}).values())),
                "total_etx_cap_flushes": r.get("total_etx_cap_flushes", sum(st.get("etx_cap", 0) for st in r.get("dyn_stats", {}).values())),
                "total_cap4_flushes": r.get("total_cap4_flushes", sum(st.get("cap4", 0) for st in r.get("dyn_stats", {}).values())),
                "total_end_flushes": r.get("total_end_flushes", sum(st.get("end", 0) for st in r.get("dyn_stats", {}).values())),
            }

    # Aggregate Scenario 2 (Mean +- SD over 3 seeds)
    for cipher in ciphers:
        summary["scenario_2_lossy"][cipher] = {}
        for mode in modes:
            runs_mode = [raw_matrix_results.get(f"s2_lossy_{cipher}_{mode}_s{s}") for s in seeds]
            runs_mode = [r for r in runs_mode if r is not None]
            if not runs_mode:
                continue

            pdr_m, pdr_sd = compute_mean_sd([r.get("pdr", 0.0) for r in runs_mode])
            pwr_m, pwr_sd = compute_mean_sd([r.get("mean_model_b_mw", 0.0) for r in runs_mode])
            cpu_m, cpu_sd = compute_mean_sd([r.get("mean_cpu_mw", 0.0) for r in runs_mode])
            tx_m,  tx_sd  = compute_mean_sd([r.get("mean_tx_mw", 0.0) for r in runs_mode])
            rx_m,  rx_sd  = compute_mean_sd([r.get("mean_rx_mw", 0.0) for r in runs_mode])
            eng_m, eng_sd = compute_mean_sd([r.get("tot_energy_uj_reading", 0.0) for r in runs_mode])
            alat_m, alat_sd = compute_mean_sd([r.get("mean_alarm_lat_ms", 0.0) for r in runs_mode])
            nlat_m, nlat_sd = compute_mean_sd([r.get("mean_norm_lat_ms", 0.0) for r in runs_mode])
            outage_m, outage_sd = compute_mean_sd([r.get("max_consecutive_missing", 0) for r in runs_mode])
            n3_m, n3_sd = compute_mean_sd([r.get("node3_model_b_mw", 0.0) for r in runs_mode])
            n4_m, n4_sd = compute_mean_sd([r.get("node4_model_b_mw", 0.0) for r in runs_mode])
            n8_m, n8_sd = compute_mean_sd([r.get("node8_model_b_mw", 0.0) for r in runs_mode])
            leaf_m, leaf_sd = compute_mean_sd([r.get("mean_leaf_mw", 0.0) for r in runs_mode])
            relay_m, relay_sd = compute_mean_sd([r.get("mean_relay_mw", 0.0) for r in runs_mode])
            leafrx_m, leafrx_sd = compute_mean_sd([r.get("mean_leaf_rx_mw", 0.0) for r in runs_mode])
            relayrx_m, relayrx_sd = compute_mean_sd([r.get("mean_relay_rx_mw", 0.0) for r in runs_mode])

            summary["scenario_2_lossy"][cipher][mode] = {
                "pdr_mean": pdr_m, "pdr_sd": pdr_sd,
                "mean_model_b_mw_mean": pwr_m, "mean_model_b_mw_sd": pwr_sd,
                "mean_cpu_mw_mean": cpu_m, "mean_cpu_mw_sd": cpu_sd,
                "mean_tx_mw_mean": tx_m, "mean_tx_mw_sd": tx_sd,
                "mean_rx_mw_mean": rx_m, "mean_rx_mw_sd": rx_sd,
                "tot_energy_uj_reading_mean": eng_m, "tot_energy_uj_reading_sd": eng_sd,
                "mean_alarm_lat_ms_mean": alat_m, "mean_alarm_lat_ms_sd": alat_sd,
                "mean_norm_lat_ms_mean": nlat_m, "mean_norm_lat_ms_sd": nlat_sd,
                "max_consecutive_missing_mean": outage_m, "max_consecutive_missing_sd": outage_sd,
                "node3_model_b_mw_mean": n3_m, "node3_model_b_mw_sd": n3_sd,
                "node4_model_b_mw_mean": n4_m, "node4_model_b_mw_sd": n4_sd,
                "node8_model_b_mw_mean": n8_m, "node8_model_b_mw_sd": n8_sd,
                "mean_leaf_mw_mean": leaf_m, "mean_leaf_mw_sd": leaf_sd,
                "mean_relay_mw_mean": relay_m, "mean_relay_mw_sd": relay_sd,
                "mean_leaf_rx_mw_mean": leafrx_m, "mean_leaf_rx_mw_sd": leafrx_sd,
                "mean_relay_rx_mw_mean": relayrx_m, "mean_relay_rx_mw_sd": relayrx_sd,
            }

    summary_file = RESULTS_DIR / "plan_c_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OK] Master summary saved successfully to: {summary_file}")

if __name__ == "__main__":
    main()
