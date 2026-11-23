#!/usr/bin/env python3
"""
Gate 2 Diagnostic Runner for Plan B Adaptive Batching (15-Node AES-128-CCM).
Runs:
1. Run A (Lossless):  Rx = 1.00, Tx = 1.00 (test-15nodes.csc)
2. Run B (Rx loss):   Rx = 0.75, Tx = 1.00 (test-15nodes-rx075.csc)
3. Run C (Dual loss): Rx = 0.75, Tx = 0.85 (test-15nodes-rx075-tx085.csc)
4. (Optional Run D):  Rx = 0.60, Tx = 1.00 (test-15nodes-rx060.csc)

Parses:
- PDR (%)
- Mean Alarm Latency (ms) (seq 5, 10)
- Mean Normal Latency (ms)
- Model B Total Power (mW) (CPU + Tx + Rx + 0.1600 mW)
- Total ETX_Cap triggers across Nodes 2..15
- Count of nodes crossing ETX >= 192
- Per-node Max_ETX range (min..max) and per-node table
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

def parse_diagnostic_log(log_path: Path, sensor_ids: list, warmup_s: float = 100.0, measure_end_s: float = 220.0):
    if not log_path.exists():
        print(f"File not found: {log_path}")
        return None

    warmup_us = int(warmup_s * 1000000)
    measure_end_us = int(measure_end_s * 1000000)

    ticks_warmup = {}
    ticks_end = {}
    rx_readings = []
    dyn_stats = {}
    tx_packet_count = 0

    lines = log_path.read_text(errors="replace").splitlines()

    for l in lines:
        # Match ENERGY_RAW: time,node,RSLAB,node,ENERGY_RAW,cpu,lpm,0,tx,rx
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

        # Count TX packets
        if ",TX" in l:
            for nid in sensor_ids:
                if f",{nid},TX" in l or f",{nid},RSLAB,{nid},TX" in l:
                    tx_packet_count += 1
                    break

        # Match RX readings at root: time,1,RSLAB,1,RX,id,val,created_ms
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

        # Match DYN_STATS
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
    mean_cpu = sum(cpu_list) / n_nodes if n_nodes > 0 else 0.0
    mean_tx  = sum(tx_list)  / n_nodes if n_nodes > 0 else 0.0
    mean_rx  = sum(rx_list)  / n_nodes if n_nodes > 0 else 0.0
    mean_model_b = mean_cpu + mean_tx + mean_rx + LPM_53UA_MW

    # Readings and latencies
    total_expected = len(sensor_ids) * 12
    delivered = len(rx_readings)
    pdr = (delivered / float(total_expected) * 100.0) if total_expected > 0 else 0.0

    alarm_lats = [r["latency_ms"] for r in rx_readings if r["is_alarm"]]
    norm_lats = [r["latency_ms"] for r in rx_readings if not r["is_alarm"]]

    mean_alarm_lat = sum(alarm_lats) / len(alarm_lats) if alarm_lats else 0.0
    mean_norm_lat = sum(norm_lats) / len(norm_lats) if norm_lats else 0.0

    # ETX stats
    total_etx_cap = sum(st.get("etx_cap", 0) for st in dyn_stats.values())
    nodes_etx_ge_192 = [nid for nid, st in dyn_stats.items() if st.get("max_etx", 0) >= 192]
    max_etx_vals = [st.get("max_etx", 0) for st in dyn_stats.values()]
    min_max_etx = min(max_etx_vals) if max_etx_vals else 0
    max_max_etx = max(max_etx_vals) if max_etx_vals else 0

    return {
        "pdr": pdr,
        "delivered": delivered,
        "total_expected": total_expected,
        "mean_alarm_lat_ms": round(mean_alarm_lat, 1),
        "mean_norm_lat_ms": round(mean_norm_lat, 1),
        "mean_cpu_mw": round(mean_cpu, 4),
        "mean_tx_mw": round(mean_tx, 4),
        "mean_rx_mw": round(mean_rx, 4),
        "mean_model_b_mw": round(mean_model_b, 4),
        "total_etx_cap_triggers": total_etx_cap,
        "nodes_etx_ge_192_count": len(nodes_etx_ge_192),
        "nodes_etx_ge_192_list": nodes_etx_ge_192,
        "min_max_etx": min_max_etx,
        "max_max_etx": max_max_etx,
        "dyn_stats": dyn_stats,
        "node_powers": node_powers
    }

def main():
    sensor_ids_15 = list(range(2, 16))
    defines = "LAB_PROFILE=1,LAB_ENABLE_AES=1,ENABLE_DYN_BATCH=1,ENABLE_SPIKE_TRACE=1"

    runs = [
        ("Run A (Lossless Rx=1.0, Tx=1.0)", "diag_15nodes_aes_rx100", "/workspace/legacy_stack/scenarios/test-15nodes.csc"),
        ("Run B (Rx-only Rx=0.75, Tx=1.0)", "diag_15nodes_aes_rx075", "/workspace/legacy_stack/scenarios/test-15nodes-rx075.csc"),
        ("Run C (Dual-loss Rx=0.75, Tx=0.85)", "diag_15nodes_aes_rx075_tx085", "/workspace/legacy_stack/scenarios/test-15nodes-rx075-tx085.csc"),
    ]

    results = {}

    for label, run_id, csc in runs:
        success = run_cooja_sim(run_id, csc, defines)
        if not success:
            print(f"Simulation failed for {run_id}")
            continue
        log_path = RESULTS_DIR / run_id / "COOJA.testlog"
        data = parse_diagnostic_log(log_path, sensor_ids_15)
        results[run_id] = {
            "label": label,
            "data": data
        }

    # Save results to json
    summary_path = RESULTS_DIR / "gate2_diagnostic_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*85)
    print("GATE 2 DIAGNOSTIC SUMMARY (15-Node AES-128-CCM Plan B: 192/160 Thresholds)")
    print("="*85)
    print(f"{'Metric':<35} | {'Run A (Rx1.0/Tx1.0)':<16} | {'Run B (Rx0.75/Tx1.0)':<16} | {'Run C (Rx0.75/Tx0.85)':<16}")
    print("-" * 92)
    
    rA = results.get("diag_15nodes_aes_rx100", {}).get("data", {})
    rB = results.get("diag_15nodes_aes_rx075", {}).get("data", {})
    rC = results.get("diag_15nodes_aes_rx075_tx085", {}).get("data", {})

    print(f"{'Overall PDR (%)':<35} | {rA.get('pdr',0):.1f}% ({rA.get('delivered',0)}/{rA.get('total_expected',0)}) | {rB.get('pdr',0):.1f}% ({rB.get('delivered',0)}/{rB.get('total_expected',0)}) | {rC.get('pdr',0):.1f}% ({rC.get('delivered',0)}/{rC.get('total_expected',0)})")
    print(f"{'Mean Alarm Latency (ms)':<35} | {rA.get('mean_alarm_lat_ms',0):<16.1f} | {rB.get('mean_alarm_lat_ms',0):<16.1f} | {rC.get('mean_alarm_lat_ms',0):<16.1f}")
    print(f"{'Mean Normal Latency (ms)':<35} | {rA.get('mean_norm_lat_ms',0):<16.1f} | {rB.get('mean_norm_lat_ms',0):<16.1f} | {rC.get('mean_norm_lat_ms',0):<16.1f}")
    print(f"{'Model B Total Power (mW)':<35} | {rA.get('mean_model_b_mw',0):<16.4f} | {rB.get('mean_model_b_mw',0):<16.4f} | {rC.get('mean_model_b_mw',0):<16.4f}")
    print(f"{'  - CPU Power (mW)':<35} | {rA.get('mean_cpu_mw',0):<16.4f} | {rB.get('mean_cpu_mw',0):<16.4f} | {rC.get('mean_cpu_mw',0):<16.4f}")
    print(f"{'  - Radio Tx Power (mW)':<35} | {rA.get('mean_tx_mw',0):<16.4f} | {rB.get('mean_tx_mw',0):<16.4f} | {rC.get('mean_tx_mw',0):<16.4f}")
    print(f"{'  - Radio Rx Power (mW)':<35} | {rA.get('mean_rx_mw',0):<16.4f} | {rB.get('mean_rx_mw',0):<16.4f} | {rC.get('mean_rx_mw',0):<16.4f}")
    print(f"{'Total ETX_Cap Triggers':<35} | {rA.get('total_etx_cap_triggers',0):<16d} | {rB.get('total_etx_cap_triggers',0):<16d} | {rC.get('total_etx_cap_triggers',0):<16d}")
    print(f"{'Nodes with ETX >= 192':<35} | {rA.get('nodes_etx_ge_192_count',0):<16d} | {rB.get('nodes_etx_ge_192_count',0):<16d} | {rC.get('nodes_etx_ge_192_count',0):<16d}")
    print(f"{'Max_ETX Range (min..max)':<35} | {str(rA.get('min_max_etx',0))+'..'+str(rA.get('max_max_etx',0)):<16} | {str(rB.get('min_max_etx',0))+'..'+str(rB.get('max_max_etx',0)):<16} | {str(rC.get('min_max_etx',0))+'..'+str(rC.get('max_max_etx',0)):<16}")

    print("\n" + "="*85)
    print("PER-NODE ETX & FLUSH DETAILS")
    print("="*85)
    for run_name, rkey in [("Run A (Lossless)", "diag_15nodes_aes_rx100"), ("Run B (Rx=0.75)", "diag_15nodes_aes_rx075"), ("Run C (Rx=0.75, Tx=0.85)", "diag_15nodes_aes_rx075_tx085")]:
        d = results.get(rkey, {}).get("data", {})
        st_map = d.get("dyn_stats", {})
        print(f"\n--- {run_name} ---")
        print(" Node | Alarm | ETX_Cap | Cap4 | AoI | End | Max_ETX | Last_ETX")
        print("------|-------|---------|------|-----|-----|---------|---------")
        for nid in sensor_ids_15:
            st = st_map.get(nid, {})
            print(f" {nid:4d} | {st.get('alarm',0):5d} | {st.get('etx_cap',0):7d} | {st.get('cap4',0):4d} | {st.get('aoi',0):3d} | {st.get('end',0):3d} | {st.get('max_etx',0):7d} | {st.get('last_etx',0):8d}")

if __name__ == "__main__":
    main()
