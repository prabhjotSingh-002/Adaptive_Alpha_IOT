#!/usr/bin/env python3
"""
Pre-Phase 4 Verification Script:
1. Re-run Run A (Lossless Rx=1.0, Tx=1.0) with dyn_batch trend-filter fix:
   Verify Node 12 false clamp is eliminated (ETX_Cap == 0 network-wide, 100% PDR).
2. Run C A/B Comparison (Dual-Loss Rx=0.75, Tx=0.85):
   VoI-Only (DISABLE_ETX_CLAMP=1) vs Plan B (Full Gate 1+2+3).
   Compute PDR, Power, Latencies, Max Consecutive Missing Readings, and 4-Reading Outages.
"""

import os
import re
import sys
import json
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results_dyn_b"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

COOJA_BIN = "/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja"
CONTIKI_DIR = "/home/user/contiki-ng"

VOLTS = 3.0
I_CPU_A = 0.0042        # 4.2 mA
I_LPM_A = 0.0000011     # 1.1 uA
I_TX_A  = 0.0174        # 17.4 mA
I_RX_A  = 0.0188        # 18.8 mA
RTIMER_HZ = 32768.0
LPM_53UA_MW = 0.1600    # Model B baseline LPM

def run_cooja_sim(run_id: str, csc_path: str, defines: str):
    out_dir = RESULTS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "COOJA.testlog"
    
    print(f"\n=======================================================")
    print(f"Starting Run: {run_id}")
    print(f"Scenario: {csc_path}")
    print(f"Defines: {defines}")
    print(f"=======================================================")

    t0 = time.time()
    cmd = (
        f"cd /workspace/legacy_stack/firmware; "
        f"rm -rf obj_z1 *.z1 *.co contiki-z1.a; "
        f"make root.z1 TARGET=z1 DEFINES={defines},IS_ROOT=1 > /dev/null 2>&1; "
        f"rm -rf sensor.z1 sensor.co obj_z1/queuebuf.o contiki-z1.a; "
        f"make sensor.z1 TARGET=z1 DEFINES={defines} > /dev/null 2>&1; "
        f"{COOJA_BIN} --no-gui --contiki={CONTIKI_DIR} "
        f"--logdir=/workspace/legacy_stack/results_dyn_b/{run_id} "
        f"{csc_path} > /dev/null 2>&1"
    )

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{BASE_DIR.parent}/external/contiki-ng:/home/user/contiki-ng:ro",
        "-v", f"{BASE_DIR.parent}:/workspace",
        "contiker/contiki-ng:develop",
        "bash", "-c", cmd
    ]

    res = subprocess.run(docker_cmd, capture_output=True, text=True)
    elapsed = round(time.time() - t0, 1)
    if res.returncode != 0:
        print(f"Error running simulation ({run_id}): returncode {res.returncode}")
        print(f"STDOUT:\n{res.stdout}")
        print(f"STDERR:\n{res.stderr}")
        return False
    size = log_file.stat().st_size if log_file.exists() else 0
    print(f"Completed {run_id} in {elapsed}s (Log: {size} bytes)")
    return True

def parse_full_metrics(log_path: Path, sensor_ids: list, warmup_s: float = 100.0, measure_end_s: float = 220.0):
    if not log_path.exists():
        print(f"File not found: {log_path}")
        return None

    warmup_us = int(warmup_s * 1000000)
    measure_end_us = int(measure_end_s * 1000000)

    ticks_warmup = {}
    ticks_end = {}
    rx_readings = []
    dyn_stats = {}
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

    # Energest
    cpu_list, lpm_list, tx_list, rx_list, total_list = [], [], [], [], []
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

    n_nodes = len(cpu_list)
    mean_cpu = sum(cpu_list) / n_nodes if n_nodes > 0 else 0.0
    mean_tx  = sum(tx_list)  / n_nodes if n_nodes > 0 else 0.0
    mean_rx  = sum(rx_list)  / n_nodes if n_nodes > 0 else 0.0
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

    total_etx_cap = sum(st.get("etx_cap", 0) for st in dyn_stats.values())
    nodes_etx_ge_192 = [nid for nid, st in dyn_stats.items() if st.get("max_etx", 0) >= 192]
    max_etx_vals = [st.get("max_etx", 0) for st in dyn_stats.values()]
    min_max_etx = min(max_etx_vals) if max_etx_vals else 0
    max_max_etx = max(max_etx_vals) if max_etx_vals else 0

    # Burst Outage Analysis per sensor (1..12 sequence)
    burst_stats = {}
    total_4reading_drops = 0
    max_consec_drops_overall = 0

    for nid in sensor_ids:
        delivered_seqs = per_sensor_seqs[nid]
        # Track consecutive missing
        consec = 0
        max_consec = 0
        drops_4_count = 0
        missing_list = []
        for s in range(1, 13):
            if s not in delivered_seqs:
                consec += 1
                missing_list.append(s)
                if consec > max_consec:
                    max_consec = consec
            else:
                if consec >= 4:
                    drops_4_count += 1
                consec = 0
        if consec >= 4:
            drops_4_count += 1

        total_4reading_drops += drops_4_count
        if max_consec > max_consec_drops_overall:
            max_consec_drops_overall = max_consec

        burst_stats[nid] = {
            "delivered_count": len(delivered_seqs),
            "missing_count": 12 - len(delivered_seqs),
            "max_consecutive_missing": max_consec,
            "drops_of_4_count": drops_4_count,
            "missing_seqs": missing_list
        }

    return {
        "pdr": pdr,
        "delivered": delivered,
        "total_expected": total_expected,
        "tot_energy_uj_reading": round(tot_energy_uj_reading, 2),
        "mean_alarm_lat_ms": round(mean_alarm_lat, 1),
        "mean_norm_lat_ms": round(mean_norm_lat, 1),
        "mean_cpu_mw": round(mean_cpu, 4),
        "mean_tx_mw": round(mean_tx, 4),
        "mean_rx_mw": round(mean_rx, 4),
        "mean_model_b_mw": round(mean_model_b, 4),
        "total_etx_cap_triggers": total_etx_cap,
        "nodes_etx_ge_192_count": len(nodes_etx_ge_192),
        "min_max_etx": min_max_etx,
        "max_max_etx": max_max_etx,
        "dyn_stats": dyn_stats,
        "burst_stats": burst_stats,
        "total_4reading_drops": total_4reading_drops,
        "max_consec_drops_overall": max_consec_drops_overall
    }

def main():
    sensor_ids_15 = list(range(2, 16))

    # 1. Re-run Run A (Lossless) with fixed dyn_batch.h
    print("\n>>> STEP 1: Re-running Run A (Lossless Rx=1.0, Tx=1.0) with Trend Filter Fix...")
    defines_dyn = "LAB_PROFILE=1,LAB_ENABLE_AES=1,ENABLE_DYN_BATCH=1,ENABLE_SPIKE_TRACE=1"
    run_cooja_sim("verify_runA_lossless_fixed", "/workspace/legacy_stack/scenarios/test-15nodes.csc", defines_dyn)
    res_A = parse_full_metrics(RESULTS_DIR / "verify_runA_lossless_fixed" / "COOJA.testlog", sensor_ids_15)

    # 2. Run C: VoI-Only (DISABLE_ETX_CLAMP=1) on Rx=0.75, Tx=0.85
    print("\n>>> STEP 2: Running Run C (Dual-Loss) with VoI-Only (DISABLE_ETX_CLAMP=1)...")
    defines_voi_only = "LAB_PROFILE=1,LAB_ENABLE_AES=1,ENABLE_DYN_BATCH=1,ENABLE_SPIKE_TRACE=1,DISABLE_ETX_CLAMP=1"
    run_cooja_sim("ab_runC_voi_only", "/workspace/legacy_stack/scenarios/test-15nodes-rx075-tx085.csc", defines_voi_only)
    res_C_voi = parse_full_metrics(RESULTS_DIR / "ab_runC_voi_only" / "COOJA.testlog", sensor_ids_15)

    # 3. Run C: Plan B (Fixed Gate 1+2+3) on Rx=0.75, Tx=0.85
    print("\n>>> STEP 3: Running Run C (Dual-Loss) with Plan B (Fixed Gate 1+2+3)...")
    run_cooja_sim("ab_runC_plan_b_fixed", "/workspace/legacy_stack/scenarios/test-15nodes-rx075-tx085.csc", defines_dyn)
    res_C_dyn = parse_full_metrics(RESULTS_DIR / "ab_runC_plan_b_fixed" / "COOJA.testlog", sensor_ids_15)

    # Print Verification Summary for Run A
    print("\n" + "="*80)
    print("STEP 1 VERIFICATION: RUN A (LOSSLESS RX=1.0, TX=1.0) AFTER TREND FILTER FIX")
    print("="*80)
    if res_A:
        print(f"PDR: {res_A['pdr']:.1f}% ({res_A['delivered']}/{res_A['total_expected']} readings)")
        print(f"Mean Alarm Latency: {res_A['mean_alarm_lat_ms']:.1f} ms")
        print(f"Mean Normal Latency: {res_A['mean_norm_lat_ms']:.1f} ms")
        print(f"Model B Total Power: {res_A['mean_model_b_mw']:.4f} mW")
        print(f"Total ETX_Cap Triggers across ALL sensors: {res_A['total_etx_cap_triggers']}")
        print(f"Nodes with ETX >= 192: {res_A['nodes_etx_ge_192_count']}")
        print(f"Max_ETX Range: {res_A['min_max_etx']}..{res_A['max_max_etx']}")
        print("\nPer-Node Detail (Run A):")
        print(" Node | Alarm | ETX_Cap | Cap4 | AoI | End | Max_ETX | Last_ETX")
        print("------|-------|---------|------|-----|-----|---------|---------")
        for nid in sensor_ids_15:
            st = res_A['dyn_stats'].get(nid, {})
            print(f" {nid:4d} | {st.get('alarm',0):5d} | {st.get('etx_cap',0):7d} | {st.get('cap4',0):4d} | {st.get('aoi',0):3d} | {st.get('end',0):3d} | {st.get('max_etx',0):7d} | {st.get('last_etx',0):8d}")

    # Print A/B Comparison Table for Run C
    print("\n" + "="*85)
    print("STEP 2: RUN C A/B COMPARISON (Rx=0.75, Tx=0.85): VoI-Only vs Plan B")
    print("="*85)
    print(f"{'Metric':<40} | {'VoI-Only (k=4)':<18} | {'Plan B (Dynamic)':<18} | {'Delta / Benefit':<18}")
    print("-" * 100)

    pdr_voi = res_C_voi['pdr'] if res_C_voi else 0.0
    pdr_dyn = res_C_dyn['pdr'] if res_C_dyn else 0.0
    pdr_delta = pdr_dyn - pdr_voi

    del_voi = res_C_voi['delivered'] if res_C_voi else 0
    del_dyn = res_C_dyn['delivered'] if res_C_dyn else 0

    pwr_voi = res_C_voi['mean_model_b_mw'] if res_C_voi else 0.0
    pwr_dyn = res_C_dyn['mean_model_b_mw'] if res_C_dyn else 0.0

    uj_voi = res_C_voi['tot_energy_uj_reading'] if res_C_voi else 0.0
    uj_dyn = res_C_dyn['tot_energy_uj_reading'] if res_C_dyn else 0.0

    alm_voi = res_C_voi['mean_alarm_lat_ms'] if res_C_voi else 0.0
    alm_dyn = res_C_dyn['mean_alarm_lat_ms'] if res_C_dyn else 0.0

    norm_voi = res_C_voi['mean_norm_lat_ms'] if res_C_voi else 0.0
    norm_dyn = res_C_dyn['mean_norm_lat_ms'] if res_C_dyn else 0.0

    drops4_voi = res_C_voi['total_4reading_drops'] if res_C_voi else 0
    drops4_dyn = res_C_dyn['total_4reading_drops'] if res_C_dyn else 0

    max_gap_voi = res_C_voi['max_consec_drops_overall'] if res_C_voi else 0
    max_gap_dyn = res_C_dyn['max_consec_drops_overall'] if res_C_dyn else 0

    etx_trig_dyn = res_C_dyn['total_etx_cap_triggers'] if res_C_dyn else 0

    print(f"{'Overall PDR (%)':<40} | {pdr_voi:.1f}% ({del_voi}/168)    | {pdr_dyn:.1f}% ({del_dyn}/168)    | {pdr_delta:+.1f}%")
    print(f"{'Model B Total Power (mW)':<40} | {pwr_voi:<18.4f} | {pwr_dyn:<18.4f} | {pwr_dyn - pwr_voi:+.4f} mW")
    print(f"{'Total Energy / Delivered Rdg (uJ)':<40} | {uj_voi:<18.1f} | {uj_dyn:<18.1f} | {uj_dyn - uj_voi:+.1f} uJ")
    print(f"{'Mean Alarm Latency (ms)':<40} | {alm_voi:<18.1f} | {alm_dyn:<18.1f} | {alm_dyn - alm_voi:+.1f} ms")
    print(f"{'Mean Normal Latency (ms)':<40} | {norm_voi:<18.1f} | {norm_dyn:<18.1f} | {norm_dyn - norm_voi:+.1f} ms")
    print(f"{'Total 4-Reading Outages (Count)':<40} | {drops4_voi:<18d} | {drops4_dyn:<18d} | {drops4_dyn - drops4_voi:+d}")
    print(f"{'Max Consecutive Missing Rdgs (Gap)':<40} | {max_gap_voi} readings ({max_gap_voi*10}s) | {max_gap_dyn} readings ({max_gap_dyn*10}s) | {max_gap_dyn - max_gap_voi:+d} rdgs")
    print(f"{'Total ETX_Cap Triggers':<40} | {'0 (Disabled)':<18} | {etx_trig_dyn:<18d} | +{etx_trig_dyn}")

    # Save to json
    out_summary = {
        "runA_fixed": res_A,
        "runC_voi_only": res_C_voi,
        "runC_plan_b_fixed": res_C_dyn
    }
    with open(RESULTS_DIR / "pre_phase4_verification_summary.json", "w") as f:
        json.dump(out_summary, f, indent=2)

if __name__ == "__main__":
    main()
