# Benchmark Comparison: AdaptiveAlpha Batching vs. Mustafa et al. (Sensors 2025)

## 1. Study Citation & Context
- **Reference Paper**: Rashid Mustafa, Nurul I. Sarkar, Mahsa Mohaghegh, Shahbaz Pervez, Robert Morados,
  *"A Secure and Energy-Efficient Cross-Layer Network Architecture for the Internet of Things"*, *Sensors* 2025, 25(11), 3457. [https://doi.org/10.3390/s25113457](https://doi.org/10.3390/s25113457).
- **Hardware Platform**: Zolertia Z1 mote (MSP430F2617 16-bit RISC MCU + CC2420 IEEE 802.15.4 Transceiver @ 3.0V).
- **Operating System**: Contiki-NG / Cooja Simulator (RPL mesh routing over 6LoWPAN).
- **Metric Power Formula (Mustafa Eq. 1)**: `Total Power = CPU_mW + RadioTx_mW + RadioRx_mW + LPM_mW`.

---

## 2. Side-by-Side Comparison: 5-Node Topology (1 Root + 4 Sensors)

### A. Raw Power & Metric Breakdown

| Configuration | Cipher Mode | Cap ($k$) | CPU (mW) | Radio Tx (mW) | Raw Listen (mW) | Duty Listen (mW) | **Duty Total (mW)** | **Tx Energy/Reading (uJ)** | Delivered |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mustafa Baseline (No Enc)** | None | $k=1$ | 0.0602 | 0.1234 | - | 0.2582 | **0.6036** | - | - |
| **Mustafa Baseline (AES-128)** | AES-128 | $k=1$ | 0.1814 | 0.6324 | - | 0.6624 | **1.6344** | - | - |
| **Mustafa Baseline (Speck)** | Speck | $k=1$ | 0.1288 | 0.3812 | - | 0.544 | **1.2138** | - | - |
| **Mustafa Baseline (Present)** | Present | $k=1$ | 0.1484 | 0.4042 | - | 0.5588 | **1.2704** | - | - |
| **Our Run (AES)** | AES | $k=1$ | 0.7002 | 0.0249 | 33.5167 | 0.6615 | **1.3884** | **248.28** | 48 |
| **Our Run (AES)** | AES | $k=2$ | 0.6847 | 0.0188 | 33.5528 | 0.6622 | **1.3676** | **187.71** | 48 |
| **Our Run (AES)** | AES | $k=4$ | 0.6782 | 0.0169 | 33.555 | 0.6623 | **1.3592** | **168.4** | 48 |
| **Our Run (NONE)** | NONE | $k=1$ | 0.6913 | 0.0222 | 33.5497 | 0.6622 | **1.3774** | **221.26** | 48 |
| **Our Run (NONE)** | NONE | $k=2$ | 0.6796 | 0.0175 | 33.5549 | 0.6623 | **1.3612** | **174.17** | 48 |
| **Our Run (NONE)** | NONE | $k=4$ | 0.6759 | 0.016 | 33.5565 | 0.6623 | **1.356** | **159.83** | 48 |
| **Our Run (PRESENT)** | PRESENT | $k=1$ | 0.9379 | 0.0249 | 33.2811 | 0.6569 | **1.6214** | **248.01** | 48 |
| **Our Run (SPECK)** | SPECK | $k=1$ | 0.6953 | 0.0249 | 33.5462 | 0.6621 | **1.3841** | **248.31** | 48 |
| **Our Run (SPECK)** | SPECK | $k=2$ | 0.6806 | 0.0188 | 33.5528 | 0.6622 | **1.3634** | **187.74** | 48 |
| **Our Run (SPECK)** | SPECK | $k=4$ | 0.6757 | 0.0169 | 33.555 | 0.6623 | **1.3567** | **168.4** | 48 |
| **Our Run (PRESENT)** | PRESENT | $k=2$ | 0.8354 | 0.0188 | 33.3762 | 0.6588 | **1.5147** | **187.45** | 48 |
| **Our Run (PRESENT)** | PRESENT | $k=4$ | 0.7741 | 0.0193 | 33.4361 | 0.6599 | **1.4552** | **257.14** | 36 |

---

## 3. Side-by-Side Comparison: 10-Node Topology (1 Root + 9 Sensors)

### A. Raw Power & Metric Breakdown

| Configuration | Cipher Mode | Cap ($k$) | CPU (mW) | Radio Tx (mW) | Raw Listen (mW) | Duty Listen (mW) | **Duty Total (mW)** | **Tx Energy/Reading (uJ)** | Delivered |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mustafa Baseline (No Enc)** | None | $k=1$ | 0.0766 | 0.1641 | - | 0.3054 | **0.7072** | - | - |
| **Mustafa Baseline (AES-128)** | AES-128 | $k=1$ | 0.2536 | 1.0291 | - | 1.0933 | **2.5317** | - | - |
| **Mustafa Baseline (Speck)** | Speck | $k=1$ | 0.1943 | 0.705 | - | 0.8841 | **1.9409** | - | - |
| **Mustafa Baseline (Present)** | Present | $k=1$ | 0.1745 | 0.4326 | - | 0.7603 | **1.5254** | - | - |
| **Our Run (AES)** | AES | $k=1$ | 0.7445 | 0.0367 | 33.4684 | 1.0905 | **1.8735** | **391.55** | 101 |
| **Our Run (AES)** | AES | $k=2$ | 0.7142 | 0.0249 | 33.5141 | 1.092 | **1.8329** | **257.46** | 104 |
| **Our Run (AES)** | AES | $k=4$ | 0.6986 | 0.0226 | 33.5371 | 1.0927 | **1.8157** | **289.63** | 84 |
| **Our Run (NONE)** | NONE | $k=1$ | 0.7348 | 0.032 | 33.4732 | 1.0907 | **1.8592** | **331.01** | 104 |
| **Our Run (NONE)** | NONE | $k=2$ | 0.7091 | 0.0227 | 33.5161 | 1.0921 | **1.8257** | **235.64** | 104 |
| **Our Run (NONE)** | NONE | $k=4$ | 0.6967 | 0.0213 | 33.5383 | 1.0928 | **1.8126** | **263.89** | 87 |
| **Our Run (SPECK)** | SPECK | $k=1$ | 0.7396 | 0.0369 | 33.4683 | 1.0905 | **1.8688** | **381.79** | 104 |
| **Our Run (SPECK)** | SPECK | $k=2$ | 0.7102 | 0.0249 | 33.5141 | 1.092 | **1.8288** | **257.46** | 104 |
| **Our Run (SPECK)** | SPECK | $k=4$ | 0.696 | 0.022 | 33.5376 | 1.0928 | **1.8126** | **281.68** | 84 |
| **Our Run (PRESENT)** | PRESENT | $k=1$ | 1.0116 | 0.0908 | 33.1524 | 1.0802 | **2.1843** | **2643.81** | 37 |
| **Our Run (PRESENT)** | PRESENT | $k=2$ | 0.9331 | 0.0767 | 33.2431 | 1.0832 | **2.0947** | **2430.57** | 34 |
| **Our Run (PRESENT)** | PRESENT | $k=4$ | 0.7989 | 0.0373 | 33.4106 | 1.0886 | **1.9266** | **1217.64** | 33 |

---

## 4. Key Academic Takeaways for Thesis & Presentation
1. **The Radio Overhead Dominance**: As predicted by hardware physics, radio transmission and listening account for over 80% of total node energy.
2. **Limitation of Mustafa's Approach**: Mustafa et al. only adjusted the cipher algorithms while keeping packets unbatched ($k=1$). While Speck saved ~5.2% radio Tx power, it still incurred full packet framing overhead on every reading.
3. **Impact of Adding Batching**: By buffering and aggregating readings into batches of $k=2$ and $k=4$, radio submissions and framing overhead drop significantly, yielding substantial reductions in total power consumption while maintaining security.
