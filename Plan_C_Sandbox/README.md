# Plan C Cross-Layer Optimization Sandbox

This sandbox contains the complete implementation, simulation results, programmatic comparisons, and 300 DPI publication plots for **Plan C: Cross-Layer Extension (MRHOF Parent Hysteresis + RPL-Aware Leaf RDC Suppression)**.

---

## Sandbox Contents

```
Plan_C_Sandbox/
├── README.md                                 # This file: navigation & execution guide
├── MASTER_PROJECT_BENCHMARK_REPORT.md        # Comprehensive 4-generation cross-stack benchmark report
├── PLAN_C_ARCHITECTURE_AND_DIFF_GUIDE.md     # Code diffs, mathematical models, and rollback procedures
├── master_recalculated_comparison.json       # Master programmatic JSON dataset across all 4 generations
└── plots/                                    # 300 DPI publication-quality figures
    ├── fig7_master_evolution_vs_mustafa.png  # Subsystem power breakdown & Pareto FND lifetime
    ├── fig8_plan_c_lossy_ablation_and_churn.png # 2x2 grid: Energy, PDR, Outage Gap, Flapping resolution
    └── fig9_per_node_leaf_rdc_suppression.png # Per-node power profile showing -36% to -40% Rx reduction on leaves
```

---

## Summary of Key Results

| Metric | Mustafa et al. (Sensors 2025) | Static $k=1$ | Static $k=4$ | Plan B (Adaptive) | Plan C (Cross-Layer, AES) | Plan C (Cross-Layer, SPECK) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lossless Power** | 4.6311 mW (Table 6 AES) | 1.2006 mW | 0.8180 mW | 0.9751 mW | **0.8861 mW** | **0.8757 mW** |
| **Alarm Latency** | N/R | 890.1 ms | 26,235.5 ms | 885.5 ms | **1,078.5 ms** | **885.0 ms** |
| **Lossless PDR** | N/R | 100.00% | 97.62% | 98.81% | **92.86%** | **95.24%** |
| **FND Lifetime Ratio** | N/R | 1.00x (145.5 d) | 1.84x (267.9 d) | 1.46x (212.0 d) | **1.55x (225.4 d)** | **1.53x (227.0 d)** |
| **Lossy PDR (Scenario 2)** | N/R | N/A | 42.86% | 50.40% | **57.54% $\pm$ 0.91%** | **61.71% $\pm$ 9.82%** |
| **Lossy Energy per Reading** | N/R | N/A | 22,337 $\mu$J | 33,440 $\mu$J | **16,393 $\mu$J (-51.0%)**| **16,089 $\mu$J (-48.2%)**|
| **Lossy Alarm Latency** | N/R | N/A | 26,957 ms | 2,459 ms | **1,591.8 ms** | **1,782.5 ms** |
| **Outlier Churn (Node 4/8)** | N/R | N/A | N/A | 2.30 / 2.68 mW | **0.91 / 1.17 mW** | **0.91 / 1.17 mW (Flapping cured)** |

*Note*: Mustafa et al. (Sensors 2025, Vol. 25, 3457) Table 6 reports 15-node average power as 4.6311 mW for AES-128 and Table 10 reports 1.8690 mW for RPL Speck. Latency, packet delivery ratio, and bottleneck node power are Not Reported (N/R) in the paper.

---

## How to Reproduce

All commands are executed inside WSL Ubuntu from the repository root:

1. **Run the 16-Simulation Matrix**:
   ```bash
   python3 legacy_stack/runners/run_plan_c_matrix.py
   ```
2. **Recompute Master Programmatic Comparison**:
   ```bash
   python3 legacy_stack/runners/build_master_comparison.py
   ```
3. **Render 300 DPI Publication Plots**:
   ```bash
   docker run --rm -v "$(pwd):/workspace" contiker/contiki-ng:develop python3 /workspace/legacy_stack/runners/generate_plan_c_plots.py
   ```

---

## Strict Zero-Commit / Instant Revert Guarantee

All modifications made to `legacy_stack/contiki-2.7/core/net/rpl/rpl-mrhof.c` and `legacy_stack/firmware/sensor.c` are strictly uncommitted. All previous reports (`LEGACY_CONTIKI_BENCHMARK_REPORT.md`, `DYN_BATCH_PLAN_B_REPORT.md`, `fig1`–`fig6`, `Plan_B_Working_And_Results/`) remain 100% untouched.

To instantly revert the workspace back to clean commit `aff3cd8`:
```bash
git checkout -- . && git clean -fd
```
