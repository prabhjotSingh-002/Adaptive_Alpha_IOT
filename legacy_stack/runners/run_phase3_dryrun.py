#!/usr/bin/env python3
"""
Phase 3 Sanity Dry Run for Plan B Adaptive Batching (5-Node AES).
Runs:
1. 5-node Lossless (Rx = 1.0)
2. 5-node Lossy (Rx = 0.75)
Parses logs and reports PDR, flush reasons, ETX stats, and alarm vs normal latencies.
"""

import os
import re
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results_dyn_b"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

COOJA_BIN = "/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja"
CONTIKI_DIR = "/home/user/contiki-ng"

def run_cooja_sim(run_id: str, csc_path: str, defines: str):
    out_dir = RESULTS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_file = out_dir / "COOJA.testlog"
    
    print(f"\n=======================================================")
    print(f"Starting Run: {run_id}")
    print(f"Scenario: {csc_path}")
    print(f"Defines: {defines}")
    print(f"=======================================================")

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
    if res.returncode != 0:
        print(f"Error running simulation: {res.stderr}")
        return False
    print(f"Completed: {run_id} (Log size: {log_file.stat().st_size if log_file.exists() else 0} bytes)")
    return True

def parse_phase3_log(log_path: Path, sensor_ids: list):
    if not log_path.exists():
        print(f"File not found: {log_path}")
        return None

    lines = log_path.read_text(errors="replace").splitlines()
    
    rx_readings = []
    dyn_stats = {}
    tick_samples = {nid: [] for nid in sensor_ids}

    for l in lines:
        parts = l.split(",")
        if len(parts) >= 6 and parts[2] == "RSLAB" and parts[4] == "RX":
            # Format: time_us, 1, RSLAB, 1, RX, id, value, created_ms
            t_ms = float(parts[0]) / 1000.0
            rid = int(parts[5])
            val = int(parts[6])
            c_ms = float(parts[7])
            nid = rid >> 16
            seq = rid & 0xFFFF
            latency = t_ms - c_ms
            is_alarm = (seq in (5, 10))
            rx_readings.append({
                "rx_time_ms": t_ms,
                "reading_id": rid,
                "node_id": nid,
                "seq": seq,
                "value": val,
                "created_ms": c_ms,
                "latency_ms": latency,
                "is_alarm": is_alarm
            })
        elif "DYN_STATS" in l:
            # Format: RSLAB,<nid>,DYN_STATS,alarm=...,etx_cap=...,cap4=...,aoi=...,end=...,max_etx=...,last_etx=...
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
        elif "TICK" in l:
            # Format: RSLAB,<nid>,TICK,rd=...,val=...,etx=...,cap=...,reason=...
            m = re.search(r'RSLAB,(\d+),TICK,rd=(\d+),val=(\d+),etx=(\d+),cap=(\d+),reason=(\d+)', l)
            if m:
                nid = int(m.group(1))
                if nid in tick_samples:
                    tick_samples[nid].append({
                        "rd": int(m.group(2)),
                        "val": int(m.group(3)),
                        "etx": int(m.group(4)),
                        "cap": int(m.group(5)),
                        "reason": int(m.group(6))
                    })

    expected = len(sensor_ids) * 12
    delivered = len(rx_readings)
    pdr = (delivered / expected * 100.0) if expected else 0.0

    alarm_latencies = [r["latency_ms"] for r in rx_readings if r["is_alarm"]]
    norm_latencies = [r["latency_ms"] for r in rx_readings if not r["is_alarm"]]

    mean_alarm_lat = sum(alarm_latencies) / len(alarm_latencies) if alarm_latencies else 0.0
    mean_norm_lat = sum(norm_latencies) / len(norm_latencies) if norm_latencies else 0.0

    return {
        "expected": expected,
        "delivered": delivered,
        "pdr": pdr,
        "dyn_stats": dyn_stats,
        "tick_samples": tick_samples,
        "mean_alarm_lat": mean_alarm_lat,
        "mean_norm_lat": mean_norm_lat,
        "rx_readings": rx_readings
    }

def main():
    sensor_ids_5 = [2, 3, 4, 5]
    defines_dyn = "LAB_PROFILE=1,LAB_ENABLE_AES=1,ENABLE_DYN_BATCH=1,ENABLE_SPIKE_TRACE=1"

    # Run 1: Lossless (Rx = 1.0)
    id_rx10 = "sanity_5nodes_aes_rx10"
    csc_rx10 = "/workspace/legacy_stack/scenarios/test-5nodes.csc"
    run_cooja_sim(id_rx10, csc_rx10, defines_dyn)
    res_rx10 = parse_phase3_log(RESULTS_DIR / id_rx10 / "COOJA.testlog", sensor_ids_5)

    # Run 2: Lossy (Rx = 0.75)
    id_rx075 = "sanity_5nodes_aes_rx075"
    csc_rx075 = "/workspace/legacy_stack/scenarios/test-5nodes-rx075.csc"
    run_cooja_sim(id_rx075, csc_rx075, defines_dyn)
    res_rx075 = parse_phase3_log(RESULTS_DIR / id_rx075 / "COOJA.testlog", sensor_ids_5)

    print("\n" + "="*70)
    print("PHASE 3 VERIFICATION SUMMARY TABLE")
    print("="*70)
    for name, res in [("Lossless (Rx = 1.0)", res_rx10), ("Lossy (Rx = 0.75)", res_rx075)]:
        if not res:
            print(f"[{name}] FAILED TO PARSE")
            continue
        print(f"\n--- {name} ---")
        print(f"PDR: {res['pdr']:.2f}% ({res['delivered']}/{res['expected']} readings delivered)")
        print(f"Mean Alarm Latency (seq 5, 10): {res['mean_alarm_lat']:.1f} ms")
        print(f"Mean Normal Latency:           {res['mean_norm_lat']:.1f} ms")
        print("\nPer-Sensor Flush Stats & ETX:")
        print(" Node | Alarm | ETX_Cap | Cap4 | AoI | End | Max_ETX | Last_ETX")
        print("------|-------|---------|------|-----|-----|---------|---------")
        for nid in sensor_ids_5:
            st = res['dyn_stats'].get(nid, {})
            print(f" {nid:4d} | {st.get('alarm',0):5d} | {st.get('etx_cap',0):7d} | {st.get('cap4',0):4d} | {st.get('aoi',0):3d} | {st.get('end',0):3d} | {st.get('max_etx',0):7d} | {st.get('last_etx',0):8d}")

if __name__ == "__main__":
    main()
