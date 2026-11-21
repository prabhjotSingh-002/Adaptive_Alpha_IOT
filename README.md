# AdaptiveAlpha IoT: Adaptive Payload Batching and Lightweight Cryptographic Co-Design in RPL Networks

[![Contiki-NG](https://img.shields.io/badge/Contiki--NG-v4.9-blue.svg)](https://github.com/contiki-ng/contiki-ng)
[![Target](https://img.shields.io/badge/Hardware-Zolertia%20Z1%20(MSP430%20%2B%20CC2420)-orange.svg)]()
[![Ciphers](https://img.shields.io/badge/Security-Speck--64%2F128%20%7C%20AES--128--CCM%20%7C%20Present--128-green.svg)]()
[![Platform](https://img.shields.io/badge/Emulation-Docker%20%2F%20Cooja-purple.svg)]()

**AdaptiveAlpha IoT** is an embedded research framework and C firmware implementation for **Application-Layer Adaptive Payload Batching ($k \in \{1, 2, 4\}$)** co-designed with lightweight authenticated cryptography (Speck-64/128, AES-128-CCM, and Present-128) on ultra-constrained Wireless Sensor Network (WSN) motes running Contiki-NG and RPL (Routing Protocol for Low-Power and Lossy Networks).

The primary benchmark target is a direct, rigorous comparative evaluation against the published baselines of **Mustafa et al. (*Sensors* 2025 Tables 6 & 10)** on the identical **Zolertia Z1 platform** (TI MSP430F2617 16-bit RISC MCU + CC2420 transceiver @ 3.0V, 8 KB RAM, 92 KB Flash).

---

## 📌 Key Empirical Findings (Pure Unnormalized Cooja Energest Ground Truth)

All evaluations are based on authentic, unnormalized hardware Energest cycle counters on Zolertia Z1 motes emulated in Cooja over a 10-second periodic traffic schedule:

1. **Active CPU Power Outperforms Mustafa Baseline**:
   - By eliminating 1-second 64-bit integer (`PRIu64`) serial logging division on the 16-bit MSP430, active CPU power dropped by **>70%**.
   - 5-Node Speck $k=4$: **0.0877 mW** vs. Mustafa's **0.1288 mW** (**-31.9% CPU power reduction**).
   - 10-Node Speck $k=4$: **0.1386 mW** vs. Mustafa's **0.1745 mW** (**-20.6% CPU power reduction**).
   - 10-Node AES-128 $k=4$: **0.1406 mW** vs. Mustafa's **0.2536 mW** (**-44.6% CPU power reduction**).
2. **Network Packets Slashed by 50% to 75%**:
   - Under $k=2$, network packet count is cut in half (**-50.0%**).
   - Under $k=4$, network packet count is cut by three-quarters (**-75.0%**).
3. **Radio Transmission Energy Slashed by Up to 44.4%**:
   - By amortizing the 6LoWPAN IPHC header (7B), IEEE 802.15.4 MAC header (23B), and AEAD authentication tag (16B) across 4 readings:
   - 5-Node Speck Tx energy drops from **221.60 $\mu$J** ($k=1$) $\to$ **135.96 $\mu$J** ($k=4$, **-38.6%**).
   - 10-Node Speck Tx energy drops from **345.19 $\mu$J** ($k=1$) $\to$ **193.03 $\mu$J** ($k=4$, **-44.1%**).
4. **100.0% Delivery Guarantee**:
   - Zero packet drops (100.0% PDR: 32/32 on 5 nodes, 72/72 on 10 nodes) across all batch sizes for Speck, AES-128, and Plaintext.
5. **Cryptographic Co-Design Insight**:
   - **Speck-64/128** is optimal for 16-bit RISC: pure ARX operations (Addition, Rotation, XOR) require zero lookup tables and zero permutations, yielding CPU power virtually identical to plaintext (0.0877 mW vs 0.0872 mW).
   - **Present-128** collapses in multi-hop networks (PDR drops to 47.2%–54.2%) due to software bit-shuffling bottlenecks on the MSP430.

---

## 📊 Summary of Ground-Truth Experimental Results

### 5-Node Star/Mesh Topology (32 Total Readings Scheduled)
| Cipher Mode | Batch ($k$) | Packets Sent | CPU (mW) | Radio Tx (mW) | Radio Listen (mW) | Tx Energy/Rdg ($\mu$J) | PDR (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Speck-64/128** | $k=1$ | 32 | 0.1075 | 0.0217 | 53.7127 | 221.60 | **100.0%** |
| **Speck-64/128** | $k=2$ | 16 (-50%) | 0.0946 | 0.0162 | 53.7164 | 165.61 (-25.3%) | **100.0%** |
| **Speck-64/128** | $k=4$ | 8 (-75%) | **0.0877** | **0.0133** | 53.7183 | **135.96 (-38.6%)** | **100.0%** |
| **AES-128-CCM** | $k=4$ | 8 (-75%) | **0.0896** | **0.0133** | 53.7183 | **135.86 (-38.7%)** | **100.0%** |
| **None (Plaintext)**| $k=4$ | 8 (-75%) | 0.0872 | 0.0128 | 53.7194 | 131.15 (-33.5%) | **100.0%** |

### 10-Node Multi-Hop Mesh Topology (72 Total Readings Scheduled)
| Cipher Mode | Batch ($k$) | Packets Sent | CPU (mW) | Radio Tx (mW) | Radio Listen (mW) | Tx Energy/Rdg ($\mu$J) | PDR (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Speck-64/128** | $k=1$ | 72 | 0.1801 | 0.0337 | 54.3015 | 345.19 | **100.0%** |
| **Speck-64/128** | $k=2$ | 36 (-50%) | 0.1528 | 0.0238 | 54.3083 | 243.18 (-29.5%) | **100.0%** |
| **Speck-64/128** | $k=4$ | 18 (-75%) | **0.1386** | **0.0189** | 54.3116 | **193.03 (-44.1%)** | **100.0%** |
| **AES-128-CCM** | $k=4$ | 18 (-75%) | **0.1406** | **0.0189** | 54.3116 | **193.01 (-44.4%)** | **100.0%** |
| **None (Plaintext)**| $k=4$ | 18 (-75%) | 0.1378 | 0.0179 | 54.3136 | 183.65 (-39.9%) | **100.0%** |

---

## 📁 Repository Structure

```
├── DEFENDABLE_PAPER_RESULTS.md               # Definitive publication tables & scientific defense
├── PROJECT_COMPLETE_PROGRESS_AND_ARCHITECTURE.md # Full architectural specification & design details
├── README.md                                 # Main project documentation & reproduction guide
├── mustafa_benchmarks/                       # Benchmark suite targeting Mustafa et al. (2025)
│   ├── crypto/                               # C89 cipher implementations (Speck, Present, AES, KAT suite)
│   ├── firmware/                             # Z1 sensor and root firmware with batching ring queue
│   ├── scenarios/                            # Cooja .csc simulation models (5-node and 10-node RPL)
│   ├── results/                              # Definitive JSON metrics and comparative markdown reports
│   ├── run_option_a_all.py                   # Automated 24-run test coordinator
│   └── run_mustafa_experiments.py            # Single-run experiment runner
├── docs/                                     # Documentation and archived planning logs
│   └── archive/legacy_plans/                 # Archived preliminary planning & scratch documents
└── firmware/                                 # Base firmware codebase
```

---

## ⚙️ Quick Start & Reproduction

### Prerequisites
- Docker Engine with user permissions
- Pinned Contiki-NG Docker image: `contiker/contiki-ng:develop`

### 1. Cryptographic Known-Answer-Test (KAT) Verification
```bash
docker run --rm -v $(pwd):/workspace -w /workspace/mustafa_benchmarks/crypto \
  contiker/contiki-ng:develop bash -c "gcc -O2 -Wall test_all_ciphers.c speck.c present.c -o test_ciphers && ./test_ciphers"
```

### 2. Run the Full 24-Run Definitive Benchmark Matrix
```bash
python3 mustafa_benchmarks/run_option_a_all.py
```

### 3. Key Reference Documents
- **Publication Ground Truth:** [DEFENDABLE_PAPER_RESULTS.md](file:///C:/Users/Yatin%20Singh/Documents/Btech%20Project%20-%201/Adaptive_Alpha_IOT/DEFENDABLE_PAPER_RESULTS.md)
- **Architecture & Progress:** [PROJECT_COMPLETE_PROGRESS_AND_ARCHITECTURE.md](file:///C:/Users/Yatin%20Singh/Documents/Btech%20Project%20-%201/Adaptive_Alpha_IOT/PROJECT_COMPLETE_PROGRESS_AND_ARCHITECTURE.md)
- **Benchmark Analysis:** [mustafa_benchmarks/MUSTAFA_BENCHMARK_ANALYSIS.md](file:///C:/Users/Yatin%20Singh/Documents/Btech%20Project%20-%201/Adaptive_Alpha_IOT/mustafa_benchmarks/MUSTAFA_BENCHMARK_ANALYSIS.md)
