# Network Topologies & Experiment Architectures
## AdaptiveAlpha IoT — Research Matrix & Scaling Guide

Is document mein project ke saare **Current aur Planned Network Topologies**, unke **Research Questions**, **Technical Limits**, aur unhe **Run karne ke Exact Commands** detail mein diye gaye hain.

---

## 1. Quick Overview: The 6-Network Strategy

Sirf nodes badhane se research nahi banti. Har network ka ek specific maqsad hota hai:

| # | Network Topology | Size (Nodes) | Status | Main Research Question |
|---|---|:---:|:---:|---|
| **1** | **Small Direct Network** | Root + 2 Sensors (3 nodes) | ✅ Ready Now | Encryption correctness, policy switching, zero-routing loss debugging |
| **2** | **Existing Continuity Network** | Root + 8 Sensors (9 nodes) | ✅ Ready Now | Static baselines vs Adaptive policies standard regression & benchmarking |
| **3** | **Multihop Grid Network** | 10 & 20 Nodes (4×5 Grid) | 🔄 Phase 6 | Scaling, distributed forwarding load, multi-hop latency vs energy |
| **4** | **Bottleneck Tree Network** | 10 & 20 Nodes (Tree) | 🔄 Phase 6 | Concentrated relay traffic & forwarder battery depletion (Lifetime killer) |
| **5** | **Alternate-Path Network** | 5 Nodes (Diamond) | 🔄 Phase 6 | Relay node death ke baad dynamic RPL route recovery & self-healing |
| **6** | **Uneven-Link / Stress Network** | 9–20 Nodes (Lossy) | 🔄 Phase 6 | Lossy wireless links, bursty traffic aur unequal battery budgets |

---

## 2. Detailed Topology Breakdown & Diagrams

### Topology 1: Small Direct Network (Root + 2 Sensors)
```
Sensor 2 ───┐ (Direct 1-Hop)
            ├───> [ Root Node 1 ]
Sensor 3 ───┘ (Direct 1-Hop)
```
- **Kyun Chahiye:** Root aur dono sensors ek doosre ke radio range (50m) ke andar hote hain. Koi multi-hop routing drop nahi hota.
- **Kya Test Karta Hai:** 
  - Cryptographic verification (AES vs Ascon tags match ho rahe hain ya nahi).
  - B3/P1 policy context switching.
  - Zero routing noise ke sath payload & protocol debugging.
- **Run Command:**
  ```bash
  python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --seed 123456 --gui
  ```

---

### Topology 2: Existing Continuity Network (Root + 8 Sensors)
```
         [S4]       [S7]
           \         /
  [S2] ───> [ Root 1 ] <─── [S5]
           /    |    \
        [S3]   [S6]   [S8]
                |
              [S9] (Partial 2-hop)
```
- **Kyun Chahiye:** Ye project ka standard 9-node baseline hai jispe Phase 1 se Phase 5 tak ke 170+ historical runs record hue hain.
- **Kya Test Karta Hai:**
  - 7 Arms comparison (N0, B1, B2, B4, B5, B3, B6, P1).
  - PDR (Packet Delivery Ratio) ~96–98% par benchmark stability.
- **Run Command:**
  ```bash
  python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 123456 --power-model --target z1
  ```

---

### Topology 3: Multi-Hop Grid Network (10 & 20 Nodes)
```
[Root 1] ──── [ S2 ] ──── [ S3 ] ──── [ S4 ] ──── [ S5 ]
   │            │            │            │            │
 [ S6 ] ──── [ S7 ] ──── [ S8 ] ──── [ S9 ] ──── [S10 ]
   │            │            │            │            │
 [S11 ] ──── [S12 ] ──── [S13 ] ──── [S14 ] ──── [S15 ]
   │            │            │            │            │
 [S16 ] ──── [S17 ] ──── [S18 ] ──── [S19 ] ──── [S20 ]
```
- **Kyun Chahiye:** Real-world smart metering / mesh sensor deployment jaisa 4×5 grid.
- **Radio Setup:** Spacing = 40m, Radio range = 50m. Is wajah se corner wale nodes Root tak 3 se 4 hops ke baad pahunchte hain.
- **Kya Test Karta Hai:**
  - Forwarding overhead: Root ke paas wale nodes (S2, S6) par deep nodes ke mukable kitna extra load aata hai.
  - Batching (B4/B5) ka impact: Kya multi-hop mein batching karne se intermediate node ka queue bhar jata hai ya energy bachti hai?

---

### Topology 4: Bottleneck Tree (Relay Concentration & Depletion)
```
                     [ Node 1 : Root ]
                            ▲
                            │ (Single Relay Link)
                     [ Node 2 : RELAY ]  <─── (CRITICAL BOTTLENECK)
                     /      |       \
                [Branch] [Branch] [Branch]
                 /    \   /    \   /    \
               [S]    [S] [S]  [S] [S]  [S]  (Downstream Sensors)
```
- **Kyun Chahiye:** Research paper ka sabse bada selling point! Yahan ek hi forwarder node par poore network ka load hota hai.
- **Kya Test Karta Hai:**
  - **Relay Energy Depletion:** Fixed AES (B1) chalane par Relay Node 2 sabse pehle mar jata hai, jisse poora network andha ho jata hai.
  - **Adaptive Policy Ka Faida:** P1/B3 policy Relay par activate hokar use Ascon + Batching par shift kar deti hai, jisse Relay 40% zyada der zinda rehta hai.
- **Current Available 3-Node Chain Command:**
  ```bash
  python3 host/run_experiment.py --phase 5 --mode B3 --clients 2 --bottleneck --gui
  ```
  *(Isme Node 1 at x=0m, Node 2 at x=40m, Node 3 at x=80m. Node 3 seedha Node 1 tak nahi pahunch sakta, Node 2 ke through hop karta hai).*

---

### Topology 5: Alternate-Path Resilience Network (Route Recovery)
```
                 [ Root 1 ]
                /          \
        [ Relay A (N2) ]   [ Relay B (N3) ]
                \          /
             [ Sensor C (N4) ]
                    │
             [ Sensor D (N5) ]
```
- **Kyun Chahiye:** Network resilience aur self-healing prove karne ke liye.
- **Kya Test Karta Hai:**
  1. Pehle normal traffic Relay A se chalega.
  2. Relay A ko artificially kill (`DEPLETED`) kiya jayega.
  3. RPL protocol live detect karega aur traffic automatically **Relay B** par reroute karega.
  4. Metrics measure honge:
     - Route recovery time (seconds).
     - Lost readings count.
     - Recovery ka additional energy cost.

---

### Topology 6: Uneven-Link / Stress Network (Weak Radio & Bursty Traffic)
- **Kyun Chahiye:** Ideal simulator world se hatkar real-world RF noise mimic karna.
- **Test Variations:**
  1. **Weak Links:** Kuch intermediate links ka UDGM RX success ratio 1.0 se ghata kar 0.7 kar dena (30% packet loss).
  2. **Bursty Generation:** Har 1 second ke bajaye achanak 10 readings ka burst aana.
  3. **Unequal Initial Battery:** Kisi node ko 10J battery aur forwarder ko sirf 2J battery dena.

---

## 3. Current Technical Limits & Safe Scaling Rules

Abhi hum direct 20 nodes kyun nahi chala rahe? Technical limits samajhna zaroori hai:

| Component | Current Limit | 20-Node Scaling Ke Liye Kya Chahiye? |
|---|:---:|---|
| **Runner Clients Flag** | Max 8 (`--clients 8`) | Argument parser aur loops ko 20 tak allow karna |
| **Cooja XML Scenario** | 9 Motes hardcoded | Naya XML scenario template (e.g. `phase6-grid-20.csc`) |
| **Cryptographic Contexts** | 16 Contexts Max (8 nodes × 2 ciphers) | Root memory allocation ko 38 contexts tak expand karna |
| **TI Z1 Mote Static RAM** | 8192 Bytes total (~696B free) | Z1 par extra contexts daalne se pehle stack safety audit zaroori hai |
| **Host System Memory** | ~4 GB RAM constraint | Serial single-run execution maintain rakhna hoga |

---

## 4. Phase-Wise Execution Roadmap (Bina Kuch Tode)

1. **Step 1 (Done):** Root + 2 Debugging (`--clients 2`) aur Root + 8 Baseline (`--clients 8`).
2. **Step 2 (Phase 6 Early):** Small 5-Node Alternate-Path Network implement karke resilience verify karna.
3. **Step 3 (Phase 6 Mid):** 10-Node Grid aur 10-Node Bottleneck Tree add karna (Z1 RAM verify karte hue).
4. **Step 4 (Phase 6 Late):** 20-Node Grid scaling aur final comparison matrix generate karna.
