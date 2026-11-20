# AdaptiveAlpha IoT: Deadline-Constrained Energy-Aware Secure Data Delivery in RPL Networks

[![Contiki-NG](https://img.shields.io/badge/Contiki--NG-develop-blue.svg)](https://github.com/contiki-ng/contiki-ng)
[![Simulator](https://img.shields.io/badge/Cooja-Z1%20MSP430%20%2B%20CC2420-orange.svg)]()
[![Security](https://img.shields.io/badge/Security-AES--128--CCM%20%7C%20Ascon--AEAD128-green.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Docker%20Pinned%20Container-purple.svg)]()

**AdaptiveAlpha IoT** is an end-to-end research framework and production-C implementation for joint cryptographic suite adaptation and dynamic packet aggregation in low-power wireless IoT networks running the Routing Protocol for Low-Power and Lossy Networks (RPL).

The framework implements and evaluates **Policy P1** — an intelligent, measurement-driven joint adaptation strategy that coordinates cipher profiles (AES-128-CCM vs. Ascon-AEAD128) and batch capacities (Cap 1, 2, 4) against dynamic traffic rates, transmission deadlines, and remaining battery levels ($E_{\text{residual}}$).

---

## 📌 Key Architectural Pillars

1. **Dual Authenticated Cryptography Profiles:**
   - **Profile 1:** Hardware-assisted / reference software **AES-128-CCM** (16-byte authentication tag).
   - **Profile 2:** Lightweight NIST LWC winner **Ascon-AEAD128** (16-byte authentication tag).
2. **Deadline-Aware Dynamic Batch Aggregation:**
   - Dynamic batching (caps 1, 2, and 4 readings per frame) constrained by delivery deadlines ($T_{\text{deadline}} = 3000\text{ ms}$) and MTU bounds ($67\text{ bytes}$ payload budget).
3. **Residual Battery Affordability Forecaster (New Revised P1):**
   - Mote-level dynamic demand forecaster:
     $$E_{\text{demand}} = (\text{fill\_time} \times P_{\text{listen}}) + E_{\text{tx}}$$
   - Prevents terminal depletion queue traps: If $E_{\text{demand}} > E_{\text{residual}}$, the policy commits Reason Code 11 (`LAB_POL_P1_BATTERY`), flushing pending readings immediately under Cap 1 to prevent reading loss upon node death.
4. **Reproducible Hardware Energy Modeling:**
   - TI MSP430F2617 MCU (8 MHz, 3V) and CC2420 IEEE 802.15.4 radio component model validated with Contiki-NG Energest accounting and exact terminal cutoff accounting.

---

## 📊 Experimental Results (9-Node Z1 Finite-Battery Lifetime Evaluation)

Evaluated on an **official 9-node legacy topology (1 Root + 8 Sensors)**, **Seed 123456**, with a finite energy budget of **4.097 Joules / sensor** and 102-second horizon:

| Arm | Description | Authenticated / 192 | Scheduled PDR | Generated PDR | Energy / Rdg | p95 Latency | First Node Death (s) | Service Failure Crossing (s) |
|---|---|---|---|---|---|---|---|---|
| **B1** | Fixed AES-128-CCM (Cap 1) | 90 / 192 | 46.9% | 93.8% | 364.5 mJ | 121.6 ms | 72.57 s | 75.0 s |
| **B2** | Fixed Ascon-AEAD128 (Cap 1) | 90 / 192 | 46.9% | 93.8% | 364.5 mJ | 122.8 ms | 72.57 s | 75.0 s |
| **B3** | Crude Threshold Cipher Switch | 82 / 192 | 42.7% | 93.2% | 400.0 mJ | 148.9 ms | 71.20 s | 75.0 s |
| **B4** | Fixed AES-128-CCM (Cap 4) | 75 / 192 | 39.1% | 78.1% | 437.5 mJ | 2977.3 ms | 72.67 s | 75.0 s |
| **B5** | Fixed Ascon-AEAD128 (Cap 4) | 75 / 192 | 39.1% | 78.1% | 437.5 mJ | 2989.4 ms | 72.67 s | 75.0 s |
| **B6** | Blind Batch Adaptation | 76 / 192 | 39.6% | 86.4% | 431.7 mJ | 1149.0 ms | 71.30 s | 75.0 s |
| **Original P1** | Static Cost-Only P1 | 76 / 192 | 39.6% | 86.4% | 431.8 mJ | 1140.9 ms | 71.30 s | 75.0 s |
| **Revised P1** | **Demand-Aware Dynamic P1** | **83 / 192** | **43.2%** | **94.3%** | **395.3 mJ** | **1140.5 ms** | **71.30 s** | **77.0 s** |

### 🚀 Key Empirical Achievements:
- **Delivery Rescue:** Revised P1 delivered **83 authenticated readings** (+7 readings gain, **+9.2%** over Original P1).
- **Energy Savings:** Model energy dropped from 431.80 mJ to **395.25 mJ / reading** (**8.5% energy reduction**).
- **Service Extension:** Network-wide service SLA crossing extended from **75.0 s to 77.0 s** (+2.0 seconds).
- **Zero Violations:** 0 post-death RF frames or application deliveries; 100% authenticated packets match sealed transmissions.

---

## 📁 Repository Structure

```
├── firmware/                  # Embedded Contiki-NG C firmware
│   ├── aggregate/             # Dynamic reading aggregation & batch framing
│   ├── common/                # Network protocol packet headers & event contracts
│   ├── crypto/                # AES-128-CCM and Ascon-AEAD128 cipher implementations
│   ├── energy/                # Energest telemetry sampling and energy model
│   ├── policy/                # P1 adaptive policy engine & rate estimator
│   ├── root/                  # RPL Dag Root sink node firmware
│   └── sensor/                # Battery-powered RPL sensor node firmware
├── host/                      # Python orchestration, calibration, and analysis harness
│   ├── run_experiment.py      # Serial experiment coordinator (Dockerized Cooja)
│   ├── calibrate.py           # Multi-action decoupled energy calibration engine
│   ├── calibration_contract.py# Provenance and source hash verification guard
│   ├── dashboard.py           # Web dashboard (Historical, Campaign, and Latest views)
│   ├── metrics.py             # Event log parser, delay calculator, and PDR verifier
│   └── topologies.py          # 9-node legacy, 16-node grid, and 16-node tree layout generators
├── configs/                   # Hardware power models & experiment configurations
├── phase_jouney/              # Phase-by-phase chronological engineering journals (Phases 1-5)
├── results/                   # Calibration matrices, SHA-256 evidence ledgers, and logs
└── tests/                     # Unit tests for policy, crypto, calibration, and topology
```

---

## ⚙️ Quick Start & Reproduction

### Prerequisites
- Docker Engine with user permissions (`sg docker` or `sudo`)
- Official Pinned Contiki-NG Docker image:
  ```bash
  docker pull contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609
  ```

### 1. Run Unit Tests (Inside Container)
```bash
docker run --rm -v $(pwd):/home/user/adaptiveAlpha_IOT -w /home/user/adaptiveAlpha_IOT \
  -e PYTHONPATH=host:tests/unit:. \
  contiker/contiki-ng:develop \
  python3 -m unittest tests/unit/test_policy.py tests/unit/test_action_demand_calibration.py
```

### 2. Compile Mote Binaries (MSP430 Target)
```bash
docker run --rm -v $(pwd):/workspace -w /workspace/firmware/sensor \
  contiker/contiki-ng:develop make TARGET=z1 clean && make TARGET=z1

docker run --rm -v $(pwd):/workspace -w /workspace/firmware/root \
  contiker/contiki-ng:develop make TARGET=z1 clean && make TARGET=z1
```

### 3. Launch the 9-Node Finite-Battery Experiment
```bash
python3 -B host/run_experiment.py \
  --phase 5 \
  --mode P1 \
  --clients 8 \
  --target z1 \
  --power-model \
  --seed 123456 \
  --policy-cost-table results/phase_05/z1-revised-calibration/cost-table-revised.json \
  --require-qualified-policy \
  --energy-budget-nj 4097000000
```

### 4. Start the Research Dashboard
```bash
python3 -B host/run_dashboard.py --port 5051
```
Open **[http://localhost:5051/](http://localhost:5051/)** in your browser to view live results:
- `/` — Latest verified P1 energy curves, depletion timing, and delivery metrics.
- `/historical` — Complete archive of all historical runs and validation logs.
- `/campaign` — Side-by-side mode comparisons (B1..B6 vs P1).

---

## 📜 Provenance & Verification
Every simulation run automatically generates:
- Full serial `console.log` and raw `events.jsonl` traces.
- Exact SHA-256 hashes of all sources, binaries, Makefiles, and configuration files.
- Production-C energy reconciliation matching Energest hardware counters.

Historical baselines remain anchored to git tag **`project_base`**.
