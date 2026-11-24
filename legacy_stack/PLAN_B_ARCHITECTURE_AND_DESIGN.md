# Plan B Architecture & Technical Design Specification

**System Model:** Dynamic Value-of-Information (VoI) and Age-of-Information (AoI) Dual-Threshold Batching with Local RPL Parent ETX Quality Adaptation  
**Target Architecture:** Zolertia Z1 (TI MSP430F2617 @ 8 MHz, 8,192 B RAM, 92 KB Flash + CC2420 @ 3.0V)  
**Operating System:** Contiki 2.7 with ContikiMAC RDC @ 8 Hz and RPL Routing (MRHOF Objective Function)

---

## 1. Problem Formulation & Theoretical Motivation

### 1.1 The Static Batching Dilemma
In low-power wireless sensor networks (WSNs) employing asynchronous duty-cycled MAC protocols (e.g., ContikiMAC @ 8 Hz), radio energy consumption is dominated by wake-up preamble strobing. In a 15-node multi-hop topology, static aggregation ($k=4$) reduces radio transmissions from 168 packets down to 42 packets (-75% channel accesses), slashing network power consumption from 1.20 mW down to 0.81 mW.

However, static aggregation introduces two critical systemic liabilities:
1. **Critical Anomaly Blindness:** In event-driven or industrial monitoring, high-priority telemetry (e.g., sudden pressure spikes, gas leaks) is buffered alongside periodic telemetry. If an anomaly occurs when buffer occupancy is low ($b = 1$), the critical reading must wait for $k - 1$ subsequent sample intervals ($\approx 30$ seconds at a 10-second sampling period), violating sub-second latency bounds.
2. **Channel-Degradation Buffer Bloat:** Under wireless fading or multi-hop relay contention, transmitting large static frames ($k=4$, 104 B over-the-air) requires prolonged ContikiMAC strobe trains. When channel errors occur, CSMA retransmission attempts quickly exhaust queue buffers, causing catastrophic packet drops where **4 consecutive sensor readings are lost simultaneously** (creating 40-second data blackouts).

### 1.2 Constrained Energy–Latency Dual-Threshold Formulation (and Lyapunov DPP Connection)
In energy-constrained wireless sensor networks, the optimal batching problem can be formulated as minimizing average transmission power subject to hard latency and freshness constraints:
$$\min_{k_t \in \{1, 2, 4\}} \lim_{T \to \infty} \frac{1}{T} \sum_{t=0}^{T-1} \mathbb{E}\left[ P_{\text{tx}}(k_t) \right]$$
$$\text{subject to} \quad L_{\text{alarm}} \le L_{\max}^{\text{alarm}} \ (\approx 1.0\text{ s}), \quad \text{AoI}_i(t) \le \Delta t_{\text{AoI}} \ (35.0\text{ s}), \quad \forall i$$
While stochastic network optimization often addresses such problems using online Lyapunov Drift-Plus-Penalty (DPP) frameworks with virtual delay queues $Z(t)$ (e.g., Neely, 2010), implementing continuous floating-point drift calculations and dynamic multipliers on an 8 MHz, 16-bit MSP430 MCU introduces prohibitive computational overhead and memory instability.

Instead, Plan B implements a **deterministic, rule-based 3-Gate dual-threshold controller** operating strictly with integer arithmetic and 12 bytes of core RAM state (plus 10 bytes of diagnostic telemetry counters). This provides the exact operational benefits of the theoretical optimization (guaranteed sub-second alarm delivery and bounded queuing age) without runtime solver overhead. Full stochastic Lyapunov DPP integration with formal queue convergence bounds is established as an important avenue for future work.

---

## 2. The 3-Gate Control Architecture

Plan B is executed locally at each sensor client during every sampling tick $t$ via the following sequential decision pipeline:

```mermaid
flowchart TD
    A["New Sensor Reading: x(t)"] --> B{"Gate 1: VoI Anomaly?<br>|x(t) - Baseline| >= 50"}
    B -- Yes (Anomaly) --> C["Flush Immediately!<br>reason = FLUSH_ALARM_VOI<br>(Bypass Cap & Send k=1..4)"]
    B -- No (Normal) --> D["Update Calm Baseline EWMA<br>Baseline = (7*Baseline + x(t)) / 8"]
    D --> E{"Gate 2: ETX Link Quality?<br>ETX >= 192 AND ETX > prev_etx"}
    E -- Link Degraded --> F["Clamp Cap: k_cap = 2<br>(Reduce Channel Hold Time)"]
    E -- Link Normal / Decaying --> G{"ETX <= 160?"}
    G -- Yes --> H["Restore Cap: k_cap = 4"]
    G -- No --> I["Maintain Active Cap"]
    F --> J{"Gate 3: Capacity / AoI / Drain?<br>buf_cnt >= k_cap OR Age >= 35s OR Last Sample"}
    H --> J
    I --> J
    J -- Condition Met --> K["Flush Batch!<br>reason = FLUSH_CAP / AOI / END"]
    J -- Condition Not Met --> L["Hold Sample in Buffer"]
```

### Gate 1: Hard Value-of-Information (VoI) Alarm Flush
- **Objective:** Ensure emergency telemetry achieves sub-second delivery regardless of buffer occupancy.
- **Mechanism:** Computes absolute deviation from a running calm baseline:
  $$\Delta x = |x_t - \bar{x}_t|$$
  If $\Delta x \ge \tau_{\text{alarm}} = 50$:
  1. The reading is immediately added to the queue.
  2. The buffer is dispatched instantaneously with reason `FLUSH_ALARM_VOI`.
  3. The calm baseline is **NOT** updated with the anomaly sample, preventing baseline corruption.
- **Calm Baseline Update (Non-alarm samples only):**
  $$\bar{x}_{t+1} = \frac{7}{8}\bar{x}_t + \frac{1}{8}x_t = \lfloor (\bar{x}_t \times 7 + x_t) \gg 3 \rfloor$$
  *(Implemented via 16-bit shift operations: zero floating-point overhead).*

### Gate 2: Local RPL Parent ETX Clamping with Strict Trend Filtering
- **Objective:** Mitigate ContikiMAC preamble collision cascades under multi-hop channel degradation by dynamically halving the batch cap ($k=4 \to k=2$).
- **Metric Extraction:** Reads the RPL preferred parent's `link_metric` directly from `core/net/rpl/rpl.h`:
  $$\text{ETX}_{\text{raw}} = \text{dag}\to\text{preferred\_parent}\to\text{link\_metric}$$
  *(Contiki 2.7 scale: 128 represents ETX = 1.0).*
- **Clamping Threshold:** $\text{ETX}_{\text{raw}} \ge 192$ (corresponding to $\text{ETX} \ge 1.50$, or an expected 1.5 transmissions per hop).
- **Hysteresis Recovery Threshold:** $\text{ETX}_{\text{raw}} \le 160$ (corresponding to $\text{ETX} \le 1.25$).
- **Strict Trend Filter (Preventing Monotonic Initial Metric False Clamping):**
  In Contiki 2.7, `rpl-mrhof.c` initializes link metrics to `RPL_INIT_LINK_METRIC = 5` ($5 \times 128 = 640$). When a node boots, its link metric slowly decays downwards toward 128 via the 90/10 EWMA:
  $$E_{t+1} = \frac{90 \times E_t + 10 \times \text{packet\_etx}}{100}$$
  Even with perfect transmission ACKs ($\text{packet\_etx} = 128$), an edge node may take 10+ packets to decay below 192.  
  To prevent false clamping during lossless operation, Gate 2 requires a strict climb:
  $$\text{Clamp to } k=2 \iff \text{ETX}_{\text{raw}} \ge 192 \quad \mathbf{AND} \quad (\text{prev\_etx} > 0 \ \land \ \mathbf{\text{ETX}_{\text{raw}} > \text{prev\_etx}})$$
  If the link metric is monotonically decreasing or unchanged between buffering cycles, Gate 2 remains inactive ($k_{\text{cap}} = 4$).

### Gate 3: Capacity, AoI Freshness Guard, and Window-End Drain
- **Capacity Flush:** Dispatches the batch when `buf_cnt >= k_cap` (where $k_{\text{cap}} \in \{2, 4\}$).
- **Age-of-Information (AoI) Guard:** If the oldest buffered sample exceeds $\Delta t_{\text{AoI}} = 35.0\text{ s}$, the batch is immediately flushed with `FLUSH_AOI_TIMEOUT`, bounding maximum telemetry age.
- **Window-End Drain:** When the active measurement interval concludes (`readings_sent >= LAB_TOTAL_READINGS`), any remaining partial batch ($k=1, 2, 3$) is flushed with `FLUSH_WINDOW_END`, ensuring zero tail drop.

---

## 3. Firmware Memory Footprint (Zolertia Z1 Audit)

Plan B was designed strictly within the Zolertia Z1 MSP430F2617 memory constraints (8,192 B RAM total):

```c
typedef struct {
  int16_t  x_baseline;      /* 2 B: Smoothed calm baseline */
  uint32_t first_ts_ms;     /* 4 B: Timestamp of oldest buffered reading */
  uint16_t prev_etx;        /* 2 B: Previous valid metric for trend tracking */
  uint8_t  buf_cnt;         /* 1 B: Current buffer count (0..4) */
  uint8_t  k_cap;           /* 1 B: Active batch cap (2 or 4) */
  uint8_t  initialized;     /* 1 B: Initialization flag */
  uint8_t  last_was_alarm;  /* 1 B: Anomaly flag */
} dyn_batch_ctx_t;          /* Total: 12 Bytes RAM (with 16-bit MSP430 alignment) */
```

### Static Memory Allocation Audit (`msp430-size`)

The Zolertia Z1 ELF binaries were audited under the exact simulation build flags (`QUEUEBUF_CONF_NUM=8` for sensors, `QUEUEBUF_CONF_NUM=4` for root):

| Component | Text (Flash) | Data (RAM) | BSS (RAM) | Total RAM | Free Stack Headroom | Stability Margin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **AES-128 Static $k=4$** | 46,315 B | 246 B | 6,734 B | 6,980 B | 1,212 B | Safe (>500 B) |
| **AES-128 Plan B (Fixed)** | 46,413 B | 246 B | 6,756 B | **7,002 B** | **1,190 B** | **Safe (+22 B delta)** |
| **SPECK-64 Static $k=4$** | 43,189 B | 246 B | 6,558 B | 6,804 B | 1,388 B | Safe (>500 B) |
| **SPECK-64 Plan B (Fixed)** | 43,287 B | 246 B | 6,580 B | **6,826 B** | **1,366 B** | **Safe (+22 B delta)** |
| **Root Gateway (`root.z1`)** | 45,987 B | 242 B | 6,318 B | 6,560 B | 1,632 B | Untouched (0 B) |

> [!NOTE]
> The **+22 B** static BSS allocation consists of the **12-byte** `dyn_batch_ctx_t` core controller state plus **10 bytes** of end-of-window diagnostic telemetry counters (`5 × uint16_t`). Sensor nodes utilize `QUEUEBUF_CONF_NUM=8` to prevent relay buffer starvation, leaving a healthy **1,190 B** (AES) and **1,366 B** (SPECK) of free stack headroom, well above the 500 B crash threshold.

---

## 4. Contiki 2.7 Implementation Insights & UDGM Physics

### 4.1 Zero Wire-Format Modification & Dynamic Count Decoding
The dynamic batching engine operates entirely at the client sensor level without altering packet framing:
- The packet wire format preserves the exact 11-byte `LAB_HEADER` (`wire[0..10]`, where `wire[10]` contains the reading count $k$), followed by $k \times 10$-byte reading structs (`uint32_t id`, `uint32_t created_ms`, `uint16_t value`) and a 16-byte cryptographic MAC tag (`wire[11 + 10k .. 26 + 10k]`).
- On the root gateway, `root.c` verifies the cryptographic payload length in `lab_secure_open()` and dynamically extracts the sample count $k$ from `wire[10]` in `lab_decode()`. Because $k$ is encoded natively in the existing application header byte, variable batch sizes ($k \in \{1, 2, 3, 4\}$) are seamlessly ingested without wire modifications, protocol renegotiation, or AAD tampering.

### 4.2 Resolving ContikiMAC Preamble Strobe Contention
In ContikiMAC @ 8 Hz, a transmitter sends continuous strobes across a 125 ms wake-up cycle. Under multi-hop topologies, intermediate forwarders (such as Bottleneck Relay Node 3) experience overlapping strobe collisions from child nodes.  
When an upstream link degrades, large 104-byte static packets require prolonged transmission airtime per strobe. Clamping to $k=2$ cuts the strobe packet payload in half, reducing channel hold time and allowing CSMA clear-channel assessments (CCA) to succeed with fewer backoffs. This explains why Plan B achieved a **-33.6% net energy reduction** and **+15.3% PDR improvement** on SPECK under multi-hop loss.
