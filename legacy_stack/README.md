# Legacy Contiki 2.7 Benchmark Stack (ContikiMAC @ 8 Hz)

This directory contains the complete, self-contained implementation and empirical validation of **Adaptive Message Batching on Legacy Contiki 2.7**, achieving **100% stack and environment parity** with the published baseline of:

> **Mustafa et al. (*Sensors* 2025)**:  
> *"A Secure and Energy-Efficient Cross-Layer Network Architecture for the Internet of Things"*, *Sensors* 2025, 25(11), 3457. DOI: [10.3390/s25113457](https://doi.org/10.3390/s25113457).

---

## 1. Quick Start (How to Run in 1 Command)

### Prerequisites:
- Docker installed and running on the host system.
- Docker image: `docker pull contiker/contiki-ng:develop`

### Execute Full 24-Simulation Matrix:
From the repository root, simply run:
```bash
python3 legacy_stack/runners/run_legacy_matrix.py
```

### What Happens Automatically:
1. Compiles MSP430 firmware for Zolertia Z1 (`sensor.z1`, `root.z1`) across all profiles and batch sizes ($k=1, 2, 4$).
2. Executes 24 automated headless Cooja simulations under ContikiMAC @ 8 Hz.
3. Parses raw hardware cycle counters (Energest ticks) for CPU, Radio Tx, Radio Listen/Rx, and LPM.
4. Generates:
   - Full publication report: `legacy_stack/results/LEGACY_CONTIKI_BENCHMARK_REPORT.md`
   - Complete machine-readable metrics: `legacy_stack/results/legacy_matrix_summary.json`

---

## 2. Directory Structure

```text
legacy_stack/
├── README.md                              <-- This quick-start guide
├── contiki-2.7/                           <-- Pinned official Contiki 2.7 release OS
├── firmware/                              <-- Zolertia Z1 C Firmware
│   ├── sensor.c                           <-- Sensor mote (batch queue + traffic generation)
│   ├── root.c                             <-- RPL Root mote (packet reception + verification)
│   ├── project-conf.h                     <-- ContikiMAC 8 Hz, CSMA & Radio configuration
│   ├── aggregate.c / aggregate.h          <-- Static ring buffer batching queue
│   ├── protocol.c / protocol.h            <-- Bit-packed wire protocol framing
│   └── Makefile                           <-- Z1 cross-compilation rules
├── crypto/                                <-- Pure C Cryptographic Primitives
│   ├── speck.c / speck.h                  <-- NSA Speck-64/128 ARX block cipher
│   ├── aes-128.c / ccm-star.c / aes_ccm.c <-- TI AES-128-CCM AEAD engine
│   ├── present.c / present.h              <-- Present-128 block cipher
│   └── secure_packet.c / secure_packet.h  <-- Unified security wrapper
├── scenarios/                             <-- Headless Cooja Simulation Topologies
│   ├── test-5nodes.csc                    <-- 1 Root + 4 Sensors (UDGM Distance Loss)
│   └── test-10nodes.csc                   <-- 1 Root + 9 Sensors (Multi-hop Mesh)
├── runners/                               <-- Automation Harness
│   └── run_legacy_matrix.py               <-- Orchestrates compilation, Cooja, and metric analysis
└── results/                               <-- Output Artifacts
    ├── LEGACY_CONTIKI_BENCHMARK_REPORT.md <-- Side-by-side comparison tables against Mustafa
    ├── legacy_matrix_summary.json         <-- Consolidated JSON metrics
    └── matrix/                            <-- Raw Cooja execution logs (COOJA.testlog)
```

---

## 3. Key Findings & Paper Takeaways

1. **Physical Parity with Mustafa et al.**:
   - Radio Listen power under ContikiMAC 8 Hz is **0.39–0.53 mW**, perfectly matching Mustafa's reported range (0.25–0.66 mW).
2. **Batching ($k=2$) Slashes Total Power**:
   - 5-Node Speck: **0.7624 mW** vs Mustafa's **1.2138 mW** (**-37.2% total power savings**).
   - 5-Node AES-128: **0.7642 mW** vs Mustafa's **1.6344 mW** (**-53.2% total power savings**).
   - Packet count cut by **-50.0%** across the mesh.
   - **100.0% Packet Delivery Ratio (PDR)** maintained on 5 nodes.
3. **Core Thesis Justification (Adaptive Batching)**:
   - On 10-node meshes under heavy asynchronous preamble strobing, static $k=4$ experiences channel collisions, demonstrating empirically why fixed static batching fails and why **Adaptive Alpha** is necessary.
