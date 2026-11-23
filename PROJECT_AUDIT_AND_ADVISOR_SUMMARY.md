# Project Audit, Empirical Benchmark Data, and Diagnostic Findings

> **Purpose of this Document:**  
> This document provides an exhaustive, transparent technical summary of our research project comparing **Adaptive Payload Batching** against the published baseline of **Mustafa et al. (*Sensors* 2025)** on the **legacy Contiki 2.7 / ContikiMAC @ 8 Hz** stack.  
> It is structured so that any independent expert or external AI model (Claude, ChatGPT, etc.) can review our empirical data, evaluate our diagnostic findings, and provide concrete feedback on the methodology, paper defense, and next technical steps under tight deadlines.

---

## 1. Experimental Setup & Target Baseline

### Target Paper Baseline
- **Reference:** Mustafa et al., *"Performance Evaluation of Lightweight Cryptographic Algorithms for Secure Communication in IoT Networks"*, *Sensors* 2025, 25(11), 3457.
- **Published Metrics Evaluated:** 5, 10, 15, and 20 nodes; Table 3 (workload/network config), Table 6 (component-wise power in mW: CPU, Tx, Rx, LPM, Total), Table 10 (cipher comparisons).

### Strict Parity Implementation Environment
- **Operating System:** Official Contiki 2.7 Release (Legacy Stack).
- **Radio Duty Cycling (RDC):** ContikiMAC @ 8 Hz Channel Check Rate (`NETSTACK_CONF_RDC = contikimac_driver`).
- **MAC Layer:** IEEE 802.15.4 CSMA (`csma_driver`).
- **Hardware Platform:** Zolertia Z1 (TI MSP430F2617 16-bit RISC MCU @ 8 MHz, CC2420 2.4 GHz Transceiver @ 3.0V).
- **Physical Memory Limits:** 8 KB RAM, 92 KB ROM (Flash).
- **Radio Medium:** Cooja UDGM (Tx range 50m, Interference 100m, 100% Tx/Rx success ratio).
- **Topology:** 1 RPL Root (Node 1) + $N-1$ Sensors ($N \in \{5, 10, 15\}$), multi-hop mesh.
- **Workload Profile:** 10-second periodic reading generation; 8 readings/sensor generated post-warmup window (60s for 5/10 nodes; 100s for 15 nodes).
- **Measurement Method:** Direct hardware Energest cycle counters on MSP430 MCU and CC2420 transceiver (unnormalized physical emulation).
- **Ciphers Evaluated:** Plaintext (NONE), Speck-64/128, AES-128-CCM, Present-128.
- **Batching Scheme:** $k \in \{1, 2, 4\}$ readings aggregated into single sealed 802.15.4 frames.

---

## 2. Full Empirical Benchmark Results (Legacy Contiki 2.7)

### A. 15-Node Topology (1 RPL Root + 14 Sensors, 112 Total Expected Readings)

| Cipher Profile | Batch Cap ($k$) | Pkts Sent | CPU (mW) | Radio Tx (mW) | Radio Rx (mW) | Total (Model B: $53.3\mu\text{A}$) | **Mustafa Baseline** | **Power Saving vs. Mustafa** | Delivered / Expected | PDR (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mustafa Baseline (AES)** | $k=1$ | - | 0.4323 | 2.0801 | 1.9682 | **4.6311 mW** | **4.6311 mW** | *Baseline* | - | - |
| **Our Implementation (AES)** | $k=1$ | 112 | 0.2450 | 0.2154 | 0.5338 | **1.1542 mW** | 4.6311 mW | **-75.1%** | 105 / 112 | **93.8%** |
| **Our Implementation (AES)** | $k=2$ | 56 | 0.1987 | 0.1522 | 0.4742 | **0.9851 mW** | 4.6311 mW | **-78.7%** | 80 / 112 | **71.4%** |
| **Our Implementation (AES)** | $k=4$ | 28 | 0.1719 | 0.1252 | 0.4278 | **0.8849 mW** | 4.6311 mW | **-80.9%** | 88 / 112 | **78.6%** |
| | | | | | | | | | | |
| **Mustafa Baseline (SPECK)** | $k=1$ | - | 0.2194 | 0.4868 | 1.0060 | **1.8690 mW** | **1.8690 mW** | *Baseline* | - | - |
| **Our Implementation (SPECK)** | $k=1$ | 112 | 0.2497 | 0.2235 | 0.5426 | **1.1758 mW** | 1.8690 mW | **-37.1%** | 104 / 112 | **92.9%** |
| **Our Implementation (SPECK)** | $k=2$ | 56 | 0.1893 | 0.1446 | 0.4688 | **0.9628 mW** | 1.8690 mW | **-48.5%** | 74 / 112 | **66.1%** |
| **Our Implementation (SPECK)** | $k=4$ | 28 | 0.1705 | 0.1272 | 0.4328 | **0.8905 mW** | 1.8690 mW | **-52.4%** | 68 / 112 | **60.7%** |
| | | | | | | | | | | |
| **Mustafa Baseline (PRESENT)**| $k=1$ | - | 0.3088 | 1.3425 | 1.4993 | **3.3049 mW** | **3.3049 mW** | *Baseline* | - | - |
| **Our Implementation (PRESENT)**| $k=1$ | 112 | 0.4956 | 0.3139 | 0.6347 | **1.6042 mW** | 3.3049 mW | **-51.5%** | 66 / 112 | **58.9%** |
| **Our Implementation (PRESENT)**| $k=2$ | 56 | 0.3347 | 0.1645 | 0.5019 | **1.1610 mW** | 3.3049 mW | **-64.9%** | 72 / 112 | **64.3%** |
| **Our Implementation (PRESENT)**| $k=4$ | 28 | 0.2641 | 0.1204 | 0.4683 | **1.0128 mW** | 3.3049 mW | **-69.4%** | 72 / 112 | **64.3%** |
| | | | | | | | | | | |
| **Mustafa Baseline (NONE)** | $k=1$ | - | 0.0989 | 0.1780 | 0.3695 | **0.8068 mW** | **0.8068 mW** | *Baseline* | - | - |
| **Our Implementation (NONE)** | $k=1$ | 112 | 0.2472 | 0.2261 | 0.5661 | **1.1994 mW** | 0.8068 mW | - | 107 / 112 | **95.5%** |
| **Our Implementation (NONE)** | $k=2$ | 56 | 0.1923 | 0.1581 | 0.4710 | **0.9814 mW** | 0.8068 mW | - | 106 / 112 | **94.6%** |
| **Our Implementation (NONE)** | $k=4$ | 28 | 0.1692 | 0.1272 | 0.4357 | **0.8921 mW** | 0.8068 mW | - | 76 / 112 | **67.9%** |

---

### B. 10-Node Topology (1 RPL Root + 9 Sensors, 72 Total Expected Readings)

| Cipher Profile | Batch Cap ($k$) | Pkts Sent | CPU (mW) | Radio Tx (mW) | Radio Rx (mW) | Total (Model B) | **Mustafa Baseline** | **Power Saving vs. Mustafa** | Delivered / Expected | PDR (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mustafa Baseline (AES)** | $k=1$ | - | 0.2536 | 1.0291 | 1.0933 | **2.5317 mW** | **2.5317 mW** | *Baseline* | - | - |
| **Our Implementation (AES)** | $k=1$ | 72 | 0.2724 | 0.2594 | 0.5284 | **1.2153 mW** | 2.5317 mW | **-52.0%** | 68 / 72 | **94.4%** |
| **Our Implementation (AES)** | $k=2$ | 36 | 0.2246 | 0.2098 | 0.4708 | **1.0603 mW** | 2.5317 mW | **-58.1%** | 36 / 72 | **50.0%** |
| **Our Implementation (AES)** | $k=4$ | 18 | 0.2000 | 0.1718 | 0.4443 | **0.9712 mW** | 2.5317 mW | **-61.6%** | 48 / 72 | **66.7%** |
| | | | | | | | | | | |
| **Mustafa Baseline (SPECK)** | $k=1$ | - | 0.1745 | 0.4326 | 0.7603 | **1.5254 mW** | **1.5254 mW** | *Baseline* | - | - |
| **Our Implementation (SPECK)** | $k=1$ | 72 | 0.2624 | 0.2599 | 0.5328 | **1.2102 mW** | 1.5254 mW | **-20.7%** | 69 / 72 | **95.8%** |
| **Our Implementation (SPECK)** | $k=2$ | 36 | 0.2199 | 0.1968 | 0.4751 | **1.0469 mW** | 1.5254 mW | **-31.4%** | 46 / 72 | **63.9%** |
| **Our Implementation (SPECK)** | $k=4$ | 18 | 0.1923 | 0.1667 | 0.4360 | **0.9501 mW** | 1.5254 mW | **-37.7%** | 28 / 72 | **38.9%** |
| | | | | | | | | | | |
| **Mustafa Baseline (PRESENT)**| $k=1$ | - | 0.1943 | 0.7050 | 0.8841 | **1.9409 mW** | **1.9409 mW** | *Baseline* | - | - |
| **Our Implementation (PRESENT)**| $k=1$ | 72 | 0.5194 | 0.3381 | 0.6349 | **1.6475 mW** | 1.9409 mW | **-15.1%** | 44 / 72 | **61.1%** |
| **Our Implementation (PRESENT)**| $k=2$ | 36 | 0.3675 | 0.2189 | 0.5270 | **1.2685 mW** | 1.9409 mW | **-34.6%** | 24 / 72 | **33.3%** |
| **Our Implementation (PRESENT)**| $k=4$ | 18 | 0.3022 | 0.1776 | 0.4882 | **1.1231 mW** | 1.9409 mW | **-42.1%** | 28 / 72 | **38.9%** |
| | | | | | | | | | | |
| **Mustafa Baseline (NONE)** | $k=1$ | - | 0.0766 | 0.1641 | 0.3054 | **0.7072 mW** | **0.7072 mW** | *Baseline* | - | - |
| **Our Implementation (NONE)** | $k=1$ | 72 | 0.2555 | 0.2420 | 0.5339 | **1.1865 mW** | 0.7072 mW | - | 71 / 72 | **98.6%** |
| **Our Implementation (NONE)** | $k=2$ | 36 | 0.2108 | 0.1889 | 0.4625 | **1.0173 mW** | 0.7072 mW | - | 72 / 72 | **100.0%** |
| **Our Implementation (NONE)** | $k=4$ | 18 | 0.1915 | 0.1696 | 0.4367 | **0.9529 mW** | 0.7072 mW | - | 44 / 72 | **61.1%** |

---

### C. 5-Node Topology (1 RPL Root + 4 Sensors, 32 Total Expected Readings)

| Cipher Profile | Batch Cap ($k$) | Pkts Sent | CPU (mW) | Radio Tx (mW) | Radio Rx (mW) | Total (Model B) | **Mustafa Baseline** | **Power Saving vs. Mustafa** | Delivered / Expected | PDR (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mustafa Baseline (AES)** | $k=1$ | - | 0.1814 | 0.6324 | 0.6624 | **1.6344 mW** | **1.6344 mW** | *Baseline* | - | - |
| **Our Implementation (AES)** | $k=1$ | 32 | 0.2050 | 0.2049 | 0.4353 | **1.0003 mW** | 1.6344 mW | **-38.8%** | 32 / 32 | **100.0%** |
| **Our Implementation (AES)** | $k=2$ | 16 | 0.1750 | 0.1710 | 0.4150 | **0.9209 mW** | 1.6344 mW | **-43.7%** | 32 / 32 | **100.0%** |
| **Our Implementation (AES)** | $k=4$ | 8 | 0.1591 | 0.1504 | 0.3983 | **0.8677 mW** | 1.6344 mW | **-46.9%** | 24 / 32 | **75.0%** |
| | | | | | | | | | | |
| **Mustafa Baseline (SPECK)** | $k=1$ | - | 0.1288 | 0.3812 | 0.5440 | **1.2138 mW** | **1.2138 mW** | *Baseline* | - | - |
| **Our Implementation (SPECK)** | $k=1$ | 32 | 0.2041 | 0.2079 | 0.4368 | **1.0039 mW** | 1.2138 mW | **-17.3%** | 32 / 32 | **100.0%** |
| **Our Implementation (SPECK)** | $k=2$ | 16 | 0.1726 | 0.1702 | 0.4164 | **0.9191 mW** | 1.2138 mW | **-24.3%** | 32 / 32 | **100.0%** |
| **Our Implementation (SPECK)** | $k=4$ | 8 | 0.1608 | 0.1574 | 0.3992 | **0.8773 mW** | 1.2138 mW | **-27.7%** | 24 / 32 | **75.0%** |
| | | | | | | | | | | |
| **Mustafa Baseline (PRESENT)**| $k=1$ | - | 0.1484 | 0.4042 | 0.5588 | **1.2704 mW** | **1.2704 mW** | *Baseline* | - | - |
| **Our Implementation (PRESENT)**| $k=1$ | 32 | 0.4436 | 0.2440 | 0.5789 | **1.4216 mW** | 1.2704 mW | - | 29 / 32 | **90.6%** |
| **Our Implementation (PRESENT)**| $k=2$ | 16 | 0.3199 | 0.1785 | 0.4553 | **1.1088 mW** | 1.2704 mW | **-12.7%** | 18 / 32 | **56.2%** |
| **Our Implementation (PRESENT)**| $k=4$ | 8 | 0.2699 | 0.1669 | 0.4352 | **1.0271 mW** | 1.2704 mW | **-19.2%** | 20 / 32 | **62.5%** |
| | | | | | | | | | | |
| **Mustafa Baseline (NONE)** | $k=1$ | - | 0.0602 | 0.1234 | 0.2582 | **0.6036 mW** | **0.6036 mW** | *Baseline* | - | - |
| **Our Implementation (NONE)** | $k=1$ | 32 | 0.1968 | 0.1962 | 0.4332 | **0.9813 mW** | 0.6036 mW | - | 32 / 32 | **100.0%** |
| **Our Implementation (NONE)** | $k=2$ | 16 | 0.1660 | 0.1641 | 0.3994 | **0.8894 mW** | 0.6036 mW | - | 32 / 32 | **100.0%** |
| **Our Implementation (NONE)** | $k=4$ | 8 | 0.1523 | 0.1489 | 0.3900 | **0.8511 mW** | 0.6036 mW | - | 32 / 32 | **100.0%** |

---

## 3. The Advisor / Independent Audit (Key Critiques)

An independent rigorous audit was conducted on our benchmark tables, pointing out four major concerns:

1. **Flaw 1: PDR Collapse on $k=4$ and Effective Energy Illusion**
   - At $k=4$, PDR collapsed to 38.9%–78.6% across 10-node and 15-node topologies.
   - When packets are dropped in a multi-hop mesh, intermediate relays never forward them. Hence, Radio Tx, Rx, and CPU power appear artificially depressed.
   - The real evaluation metric must be **Energy per Delivered Reading ($\mu\text{J}/\text{reading}$)**. If PDR drops by 40%, the effective energy per delivered reading increases drastically.
2. **Flaw 2: Misleading Attribution of the -80.9% AES Power Drop**
   - In 15-node AES, our $k=4$ is 0.8849 mW vs Mustafa's 4.6311 mW (-80.9%).
   - However, our $k=1$ (single reading, zero batching) was already 1.1542 mW (-75.1% drop vs Mustafa).
   - The pure gain from batching ($k=1 \to k=4$) is only $-23.3\%$ (1.1542 $\to$ 0.8849 mW). Crediting the entire -80.9% drop to "batching" conflates stack/firmware differences with payload aggregation.
3. **Flaw 3: Plaintext Baseline Discrepancy & Minor Cipher Variance**
   - Our Plaintext NONE is 0.98–1.20 mW (Model B), whereas Mustafa's Plaintext is 0.60–0.81 mW.
   - On 15-node $k=1$, AES (1.1542 mW) and Speck (1.1758 mW) are slightly lower than Plaintext NONE (1.1994 mW) by ~3-4%, which physically should not happen under identical seeds without explanation of ContikiMAC sleep phase variance.
4. **Flaw 4: Markdown Document Text Inconsistencies**
   - Text summary claimed "100% Packet Delivery Reliability" despite tables showing 38.9%–78.6%.
   - Table headers used positive signs for savings (`+75.1%` instead of `-75.1%`).

---

## 4. In-Depth Log Analysis & Diagnostic Discoveries

To investigate the root cause of the packet drops at $k=4$ (and encrypted $k=2$), we conducted a trace-level analysis of `COOJA.testlog` files.

### A. Testing the 6LoWPAN Fragmentation Hypothesis
- **Hypothesis:** Did large payloads (4 readings + 16B auth tag = 67B application payload) exceed the 127-byte IEEE 802.15.4 MTU and trigger 6LoWPAN fragmentation?
- **Log Verification:** We extracted all 4,914 over-the-air radio transmission events (`RADIO,...`) logged by the Cooja UDGM radio medium across the entire 15-node simulation (`15nodes_speck_k4`).
- **Empirical Result:**
  - Total radio frames logged: 4,914.
  - Min frame length: 5 bytes (ACKs).
  - **Max frame length: 104 bytes.**
  - **Verdict:** **NO 6LoWPAN fragmentation occurred.** The maximum physical frame size (104 bytes) was well below the 127-byte limit. All packets were transmitted as intact single frames.

### B. Batch 1 vs. Batch 2 Delivery Breakdown
- **Hypothesis:** Did packets drop because the 195s simulation cutoff killed in-flight packets of Batch 2 (generated at $t = 170\text{s}$)?
- **Log Verification:** In `15nodes_speck_k4`, we checked delivery separated by batch generation window:
  - **Batch 1 (generated at $t \approx 132\text{s}$):** Only **28 / 56 readings delivered (50.0%)**.
  - **Batch 2 (generated at $t \approx 172\text{s}$):** **40 / 56 readings delivered (71.4%)**.
  - **Verdict:** Batch 1 was transmitted **63 seconds before simulation termination**, yet half of the Batch 1 packets were lost! Thus, simulation cutoff is NOT the primary cause.

### C. Hop-by-Hop Trace: The Intermediate Relay Queue Starvation
We traced the exact packet lifecycle of Node 14 (located at $x=155.0, y=45.0$, ~118m from Root, 3-4 hops away):
1. **$t = 132.28\text{s}$:** Node 14 generates Batch 1, strobes ContikiMAC, and transmits a 104-byte frame to Node 11.
2. **$t = 132.38\text{s}$:** Node 11 receives the frame and returns an 802.15.4 ACK (`02000b...`).
3. **$t = 135.64\text{s}$:** Node 11 forwards the frame to Node 8.
4. **$t = 135.70\text{s}$:** Node 8 receives the frame, ACKs Node 11, and forwards to Node 7 (bottleneck router).
5. **$t = 135.72\text{s}$:** Node 7 receives and ACKs the frame (`02001ddc7e`).
6. **$t = 135.85\text{s}$ – End:** Node 7 transmits its OWN local readings to Node 3, but **NEVER forwards the packet received from Node 8/14!**

### D. Root Cause Identified: Contiki 2.7 Default Buffer Configuration
In Contiki 2.7 `platform/z1/contiki-conf.h`:
```c
#define QUEUEBUF_CONF_NUM 4   /* Default IPv6 queue buffers is ONLY 4! */
```
- In multi-hop mesh routing, bottleneck nodes (e.g., Node 7, Node 3) act as transit relays for 4–6 downstream sensors while also generating their own packets.
- Because ContikiMAC operates at 8 Hz, every outbound frame requires up to 125 ms of active preamble strobing.
- When multiple children transmit 104-byte frames into a relay during a strobe window, **all 4 queue buffers are instantly exhausted**.
- In Contiki 2.7, when `queuebuf_alloc()` returns NULL, incoming routed frames are **silently dropped without buffering**.
- Furthermore, `CSMA_CONF_MAX_MAC_TRANSMISSIONS` defaults to only 3. If a collision or busy channel occurs during strobing, the packet is discarded (`MAC_TX_NOACK`).

### E. Hardware Memory Feasibility on Zolertia Z1
- **MCU Specs:** TI MSP430F2617 with **8,192 bytes (8 KB) RAM**.
- Current firmware RAM consumption (`sensor.z1`):
  - `.data`: 246 bytes
  - `.bss`: 5,702 bytes
  - **Total RAM Used: 5,948 bytes (72.6%)**
  - **Available Free RAM: 2,244 bytes.**
- Memory required to increase `QUEUEBUF_CONF_NUM` from 4 to 16:
  - 12 additional queue buffers $\times$ ~140 bytes $\approx$ **1,680 bytes**.
  - **$2,244 - 1,680 = 564$ bytes free stack headroom.**
  - **Verdict:** Increasing `QUEUEBUF_CONF_NUM` to 14–16 is physically feasible and fits within the 8 KB RAM boundary.

---

## 5. Technical Questions for External Reviewers

We would appreciate advice from external AI models / advisors on the following strategic and technical decisions:

1. **Queue Buffer vs. Channel Check Rate:**  
   Will increasing `QUEUEBUF_CONF_NUM` from 4 to 14/16 and `CSMA_CONF_MAX_MAC_TRANSMISSIONS` from 3 to 5 be sufficient to restore multi-hop PDR to $\ge 90\%-95\%$ under ContikiMAC 8 Hz, or is an adaptive CSMA backoff delay also required to prevent relay congestion?
2. **Attribution & Paper Framing:**  
   How should we structure the paper's comparison against Mustafa et al.?  
   - *Component A:* Demonstrating that our phase-staggered ContikiMAC implementation avoids Mustafa's massive radio retransmission storm ($k=1$ baseline consumes 1.15 mW vs Mustafa's 4.63 mW on AES).  
   - *Component B:* Demonstrating that Adaptive Batching ($k=1 \to k=4$) provides an additional 23%–35% genuine energy reduction by amortizing ContikiMAC preamble strobes.  
   Is this two-tier attribution compelling and scientifically bulletproof for peer review?
3. **Metric Standard:**  
   Should we formally report **Total Energy per Delivered Reading ($\mu\text{J}/\text{reading}$)** alongside average node power (mW) to definitively prove that batching is energy-efficient even if PDR varies slightly?
4. **Deadline Strategy:**  
   Is running a single diagnostic scenario (10-node Speck $k=4$ with 220s timeout and expanded queue buffers) the optimal low-risk first step before executing any large matrix runs?
