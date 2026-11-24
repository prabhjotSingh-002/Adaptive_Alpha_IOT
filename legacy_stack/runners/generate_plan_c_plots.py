#!/usr/bin/env python3
"""
Publication-Quality Figure Generation for Plan C (Cross-Layer Adaptation).
Generates:
  1. fig7_master_evolution_vs_mustafa.png (2-panel: Subsystem Power Breakdown & Pareto FND Lifetime vs. Alarm Latency)
  2. fig8_plan_c_lossy_ablation_and_churn.png (2x2 grid: Energy, PDR, Outage Window, Seed 345678 Churn)
  3. fig9_per_node_leaf_rdc_suppression.png (Per-Node Relay vs. Leaf Rx Power Profile)

Strict publication criteria: 300 DPI, tight_layout, zero text clipping, accessible color palettes.
Saves to both legacy_stack/plots_plan_c/ and Plan_C_Sandbox/plots/.
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[2]
LEGACY_DIR = ROOT / "legacy_stack"
PLOTS_DIR = LEGACY_DIR / "plots_plan_c"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
SANDBOX_PLOTS_DIR = ROOT / "Plan_C_Sandbox" / "plots"
SANDBOX_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

MASTER_JSON = ROOT / "Plan_C_Sandbox" / "master_recalculated_comparison.json"
PLAN_C_SUMMARY = LEGACY_DIR / "results_plan_c" / "plan_c_summary.json"
PLAN_B_SUMMARY = LEGACY_DIR / "results_dyn_b" / "dyn_b_summary.json"

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9.0,
    'figure.titlesize': 13,
    'figure.dpi': 300,
    'savefig.dpi': 300
})

def save_dual(fig, filename):
    p1 = PLOTS_DIR / filename
    p2 = SANDBOX_PLOTS_DIR / filename
    fig.savefig(p1, bbox_inches='tight', dpi=300)
    fig.savefig(p2, bbox_inches='tight', dpi=300)
    print(f"[OK] Saved: {filename} to both plots_plan_c/ and Plan_C_Sandbox/plots/")

def plot_fig7(master_data):
    """
    Fig 7: Master Evolution vs. Mustafa et al. (2025)
    Panel (a): Stacked Subsystem Power (CPU, Tx, Rx, LPM) across Generations
    Panel (b): Pareto Alarm Latency vs. FND Battery Lifetime
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.2))

    # Panel (a): Subsystem Power Breakdown across 5 evaluated systems
    gens = [
        "Static k=1\n(Baseline)",
        "Static k=4\n(Energy Bound)",
        "Plan B\n(Dyn Batch)",
        "Plan B + B1\n(Hysteresis)",
        "Plan C\n(B1 + Leaf Sleep)"
    ]

    # Exact measured data for AES (Scenario 1 Lossless)
    # Static k1: CPU 0.2588, TX 0.2252, RX 0.5566, LPM 0.1600 -> 1.2006 mW
    # Static k4: CPU 0.1524, TX 0.0915, RX 0.4140, LPM 0.1600 -> 0.8180 mW
    # Plan B:    CPU 0.1982, TX 0.1448, RX 0.4721, LPM 0.1600 -> 0.9751 mW
    # Plan B+B1: CPU 0.1866, TX 0.1382, RX 0.4602, LPM 0.1600 -> 0.9449 mW
    # Plan C:    CPU 0.1819, TX 0.1305, RX 0.4138, LPM 0.1600 -> 0.8861 mW

    cpu_vals = [0.2588, 0.1524, 0.1982, 0.1866, 0.1819]
    tx_vals  = [0.2252, 0.0915, 0.1448, 0.1382, 0.1305]
    rx_vals  = [0.5566, 0.4140, 0.4721, 0.4602, 0.4138]
    lpm_vals = [0.1600, 0.1600, 0.1600, 0.1600, 0.1600]

    x = np.arange(len(gens))
    width = 0.52

    c_lpm = '#95a5a6'
    c_cpu = '#3498db'
    c_tx  = '#e67e22'
    c_rx  = '#e74c3c'

    p1 = ax1.bar(x, lpm_vals, width, label='LPM (53.3 µA baseline)', color=c_lpm, edgecolor='black', linewidth=0.6)
    p2 = ax1.bar(x, cpu_vals, width, bottom=lpm_vals, label='CPU Active (4.2 mA)', color=c_cpu, edgecolor='black', linewidth=0.6)
    p3 = ax1.bar(x, tx_vals, width, bottom=np.array(lpm_vals)+np.array(cpu_vals), label='Radio TX (17.4 mA)', color=c_tx, edgecolor='black', linewidth=0.6)
    p4 = ax1.bar(x, rx_vals, width, bottom=np.array(lpm_vals)+np.array(cpu_vals)+np.array(tx_vals), label='Radio RX/Listen (18.8 mA)', color=c_rx, edgecolor='black', linewidth=0.6)

    # In-bar total labels
    totals = [sum(vals) for vals in zip(lpm_vals, cpu_vals, tx_vals, rx_vals)]
    for i, tot in enumerate(totals):
        ax1.text(x[i], tot + 0.02, f"{tot:.3f} mW", ha='center', va='bottom', fontweight='bold', fontsize=9)

    # Informative annotation showing honest Mustafa 2025 Table 6 baseline
    ax1.text(0.04, 0.95,
             "Mustafa et al. (Sensors 2025, Table 6 AES-128 Baseline):\n"
             "Total Avg Power = 4.6311 mW (Off-chart, 3.86x vs Static k=1)\n"
             "Breakdown: CPU 0.432, Listen 1.968, TX 2.080, LPM 0.151 mW",
             transform=ax1.transAxes, fontsize=8.2, va='top', ha='left',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#fcf3cf', edgecolor='#d4ac0d', lw=1.0))

    ax1.set_ylabel('Mean Network Power (mW, Model B 3.0V)')
    ax1.set_title('(a) Subsystem Power Breakdown Evolution (Scenario 1 Lossless)', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(gens, rotation=12, ha='right')
    ax1.set_ylim(0, 1.45)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    ax1.legend(loc='upper right', framealpha=0.95)

    # Panel (b): Pareto Frontier: Alarm Latency vs. FND Lifetime
    # Data points: (Alarm Latency ms, FND Lifetime Days, Label, Marker, Color)
    points = [
        (890.1,   145.5, "Static k=1 (Baseline)", '^', '#e74c3c'),
        (26235.5, 267.9, "Static k=4 (Energy Bound)", 'v', '#7f8c8d'),
        (885.5,   212.0, "Plan B (Adaptive Batch)", 'D', '#2980b9'),
        (925.7,   218.5, "Plan B + B1 (MRHOF Hyst)", 'p', '#d35400'),
        (1078.5,  225.4, "Plan C (B1 + Leaf Sleep)", '*', '#27ae60')
    ]

    for lat, days, label, marker, col in points:
        size = 190 if marker == '*' else 120
        ax2.scatter(lat, days, s=size, color=col, marker=marker, edgecolors='black', linewidth=1.0, zorder=5, label=label)

    # Custom annotations carefully placed to avoid collisions
    # Static k1
    ax2.annotate("Static k=1 (Baseline)\n0.89s (145.5 d)",
                 xy=(890.1, 145.5), xytext=(530, 152),
                 fontsize=8.5, fontweight='bold', color='#c0392b', ha='left',
                 arrowprops=dict(arrowstyle="->", color='#c0392b', lw=0.9))

    # Plan B
    ax2.annotate("Plan B\n0.89s (212.0 d, 1.46x)",
                 xy=(885.5, 212.0), xytext=(530, 195),
                 fontsize=8.5, fontweight='bold', color='#2980b9', ha='left',
                 arrowprops=dict(arrowstyle="->", color='#2980b9', lw=0.9))

    # Plan B + B1
    ax2.annotate("Plan B + B1\n0.93s (218.5 d, 1.50x)",
                 xy=(925.7, 218.5), xytext=(530, 242),
                 fontsize=8.5, fontweight='bold', color='#d35400', ha='left',
                 arrowprops=dict(arrowstyle="->", color='#d35400', lw=0.9))

    # Plan C
    ax2.annotate("Plan C (Combined)\n1.08s (225.4 d, 1.55x)",
                 xy=(1078.5, 225.4), xytext=(1700, 222),
                 fontsize=8.5, fontweight='bold', color='#1e8449', ha='left',
                 arrowprops=dict(arrowstyle="->", color='#1e8449', lw=0.9))

    # Static k=4
    ax2.annotate("Static k=4 (Energy Bound)\n26.2s delay (267.9 d)",
                 xy=(26235.5, 267.9), xytext=(15500, 255),
                 fontsize=8.5, fontweight='bold', color='#7f8c8d', ha='right',
                 arrowprops=dict(arrowstyle="->", color='#7f8c8d', lw=0.9))

    # Reference horizontal line for Static k=1 (1.0x FND)
    ax2.axhline(145.5, color='#e74c3c', linestyle=':', alpha=0.6, label='Static k=1 Baseline Lifetime (145.5 d)')
    # Reference vertical line for Sub-second Alarm Gate (1000 ms)
    ax2.axvline(1000.0, color='#27ae60', linestyle='--', alpha=0.5, label='Sub-second Alarm Bound (1,000 ms)')

    # Honest footnote regarding Mustafa 2025 Table 6
    ax2.text(0.04, 0.94,
             "Note: Mustafa et al. (Sensors 2025, Table 6) reported 4.6311 mW network power;\n"
             "alarm latency and per-node lifetime were not reported (N/R).",
             transform=ax2.transAxes, fontsize=8.0, va='top', ha='left',
             bbox=dict(boxstyle='square,pad=0.4', facecolor='#f8f9f9', edgecolor='#bdc3c7', lw=0.8))

    ax2.set_xscale('log')
    ax2.set_xlabel('Mean Alarm Delivery Latency (ms, log scale)')
    ax2.set_ylabel('First Node Die (FND) Battery Lifetime (Days, 2x AA)')
    ax2.set_title('(b) Multi-Metric Pareto Frontier: Alarm Latency vs. FND Lifetime', fontweight='bold')
    ax2.set_xlim(480, 35000)
    ax2.set_ylim(130, 290)
    ax2.grid(True, which='both', linestyle='--', alpha=0.4)
    # Legend safely placed in lower-right with zero overlap
    ax2.legend(loc='lower right', framealpha=0.95, fontsize=8.2)

    plt.tight_layout()
    save_dual(fig, "fig7_master_evolution_vs_mustafa.png")
    plt.close(fig)

def plot_fig8(master_data, raw_pc_data):
    """
    Fig 8: Plan C Lossy Ablation & Flapping Churn Resolution (2x2 Grid)
    (a) Delivery-Adjusted Energy per Reading (µJ/rdg) across modes (whisker-collision free)
    (b) Packet Delivery Ratio (%) with 3-seed error bars (whisker-collision free)
    (c) Maximum Consecutive Missing Reading Outage Window
    (d) Outlier Seed 345678 Bottleneck & Churn Power (Node 3, 4, 8) with clean upper-left legend
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    ((ax1, ax2), (ax3, ax4)) = axes

    modes = ["Static k=4", "VoI-Only", "Plan B", "Plan B+B1", "Plan C"]
    x = np.arange(len(modes))

    aes_lossy = master_data["scenario_2_lossy_ablation_aes"]
    speck_lossy = master_data["scenario_2_lossy_ablation_speck"]

    w_half = 0.35

    # -------------------------------------------------------------
    # (a) Energy per Reading (µJ)
    # -------------------------------------------------------------
    eng_aes = [r["energy_uj_mean"] for r in aes_lossy]
    eng_aes_sd = [r["energy_uj_sd"] for r in aes_lossy]
    eng_speck = [r["energy_uj_mean"] for r in speck_lossy]
    eng_speck_sd = [r["energy_uj_sd"] for r in speck_lossy]

    b1 = ax1.bar(x - w_half/2, eng_aes, w_half, yerr=eng_aes_sd, capsize=4, label='AES-128-CCM', color='#2980b9', edgecolor='black', linewidth=0.6)
    b2 = ax1.bar(x + w_half/2, eng_speck, w_half, yerr=eng_speck_sd, capsize=4, label='SPECK-64/128', color='#27ae60', edgecolor='black', linewidth=0.6)

    # In-bar labels placed safely inside the bars (at 45% height) to prevent collision with top error whiskers!
    for rect in b1:
        h = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2, h * 0.45, f"{h:.0f}\nµJ", ha='center', va='center', fontsize=8.0, fontweight='bold', color='white')
    for rect in b2:
        h = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2, h * 0.45, f"{h:.0f}\nµJ", ha='center', va='center', fontsize=8.0, fontweight='bold', color='white')

    ax1.set_ylabel('Total Energy (µJ / Delivered Reading)')
    ax1.set_title('(a) Delivery-Adjusted Energy per Reading (Scenario 2 Lossy)', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(modes, rotation=12)
    ax1.set_ylim(0, 58000)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    ax1.legend(loc='upper right', framealpha=0.95)

    # -------------------------------------------------------------
    # (b) Packet Delivery Ratio (%)
    # -------------------------------------------------------------
    pdr_aes = [r["pdr_mean"] for r in aes_lossy]
    pdr_aes_sd = [r["pdr_sd"] for r in aes_lossy]
    pdr_speck = [r["pdr_mean"] for r in speck_lossy]
    pdr_speck_sd = [r["pdr_sd"] for r in speck_lossy]

    b3 = ax2.bar(x - w_half/2, pdr_aes, w_half, yerr=pdr_aes_sd, capsize=4, label='AES-128-CCM', color='#2980b9', edgecolor='black', linewidth=0.6)
    b4 = ax2.bar(x + w_half/2, pdr_speck, w_half, yerr=pdr_speck_sd, capsize=4, label='SPECK-64/128', color='#27ae60', edgecolor='black', linewidth=0.6)

    # In-bar labels placed at 45% height to prevent whisker overlap
    for rect in b3:
        h = rect.get_height()
        ax2.text(rect.get_x() + rect.get_width()/2, h * 0.45, f"{h:.1f}%", ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')
    for rect in b4:
        h = rect.get_height()
        ax2.text(rect.get_x() + rect.get_width()/2, h * 0.45, f"{h:.1f}%", ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')

    ax2.set_ylabel('Packet Delivery Ratio (PDR, %)')
    ax2.set_title('(b) End-to-End Delivery Reliability (Scenario 2 Lossy)', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(modes, rotation=12)
    ax2.set_ylim(0, 85)
    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    ax2.legend(loc='lower right', framealpha=0.95)

    # -------------------------------------------------------------
    # (c) Max Consecutive Missing Outage Gap (Readings)
    # -------------------------------------------------------------
    out_aes = [r["outage_gap_mean"] for r in aes_lossy]
    out_speck = [r["outage_gap_mean"] for r in speck_lossy]

    b5 = ax3.bar(x - w_half/2, out_aes, w_half, label='AES-128-CCM', color='#e67e22', edgecolor='black', linewidth=0.6)
    b6 = ax3.bar(x + w_half/2, out_speck, w_half, label='SPECK-64/128', color='#9b59b6', edgecolor='black', linewidth=0.6)

    for i, rect in enumerate(b5):
        h = rect.get_height()
        offset_x = -0.08 if i == 0 else 0
        ax3.text(rect.get_x() + rect.get_width()/2 + offset_x, h + 0.35, f"{h:.1f} rdg\n({h*10:.0f}s)", ha='center', va='bottom', fontsize=7.0, fontweight='bold', color='#ba4a00')
    for i, rect in enumerate(b6):
        h = rect.get_height()
        offset_x = 0.08 if i == 0 else 0
        ax3.text(rect.get_x() + rect.get_width()/2 + offset_x, h + 0.35, f"{h:.1f} rdg\n({h*10:.0f}s)", ha='center', va='bottom', fontsize=7.0, fontweight='bold', color='#6c3483')

    ax3.set_ylabel('Max Consecutive Outage Gap (Readings / 10s Window)')
    ax3.set_title('(c) Channel Outage Duration Gap (Shorter is Better)', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(modes, rotation=12)
    ax3.set_ylim(0, 16)
    ax3.grid(axis='y', linestyle='--', alpha=0.4)
    ax3.legend(loc='upper right', framealpha=0.95)

    # -------------------------------------------------------------
    # (d) Outlier Seed 345678 Churn Power (Node 3, 4, 8)
    # Legend moved to upper-left to prevent covering Node 8's red bar!
    # -------------------------------------------------------------
    nodes_churn = ["Node 3 (Relay)", "Node 4 (Flapping)", "Node 8 (Flapping)"]
    x_nodes = np.arange(len(nodes_churn))
    w_node = 0.25

    # Locked values on Seed 345678:
    pb_n3, pb_n4, pb_n8 = 1.9151, 2.3032, 2.6805
    hyst_n3, hyst_n4, hyst_n8 = 1.9692, 0.9134, 1.1706
    planc_n3, planc_n4, planc_n8 = 2.0418, 1.2587, 1.4464

    b7 = ax4.bar(x_nodes - w_node, [pb_n3, pb_n4, pb_n8], w_node, label='Plan B (Flapping Churn)', color='#e74c3c', edgecolor='black', linewidth=0.6)
    b8 = ax4.bar(x_nodes, [hyst_n3, hyst_n4, hyst_n8], w_node, label='Plan B + B1 (Hysteresis Solved)', color='#2980b9', edgecolor='black', linewidth=0.6)
    b9 = ax4.bar(x_nodes + w_node, [planc_n3, planc_n4, planc_n8], w_node, label='Plan C (Hyst + Leaf Sleep)', color='#27ae60', edgecolor='black', linewidth=0.6)

    for rect in b7:
        h = rect.get_height()
        ax4.text(rect.get_x() + rect.get_width()/2, h + 0.05, f"{h:.2f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#922b21')
    for rect in b8:
        h = rect.get_height()
        ax4.text(rect.get_x() + rect.get_width()/2, h + 0.05, f"{h:.2f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1f618d')
    for rect in b9:
        h = rect.get_height()
        ax4.text(rect.get_x() + rect.get_width()/2, h + 0.05, f"{h:.2f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1e8449')

    ax4.set_ylabel('Node Power Consumption (mW, Model B 3.0V)')
    ax4.set_title('(d) Outlier Seed 345678: Churn Flapping Resolution', fontweight='bold')
    ax4.set_xticks(x_nodes)
    ax4.set_xticklabels(nodes_churn)
    ax4.set_ylim(0, 3.5)
    ax4.grid(axis='y', linestyle='--', alpha=0.4)
    # Legend safely placed in UPPER LEFT (zero collision with Node 8 on the right)
    ax4.legend(loc='upper left', framealpha=0.95)

    plt.tight_layout()
    save_dual(fig, "fig8_plan_c_lossy_ablation_and_churn.png")
    plt.close(fig)

def plot_fig9(plan_c_raw):
    """
    Fig 9: Per-Node Relay vs. Leaf RDC Suppression Profile
    Compares Node 2..15 Power:
      - Relays (Nodes 2, 3, 4, 6, 7, 8, 9, 10, 11, 13)
      - Leaves (Nodes 5, 12, 14, 15)
    Uses true Plan B baseline from dyn_b_summary.json.
    """
    fig, ax = plt.subplots(figsize=(13.5, 6))

    # Pull per-node powers from Plan C and Plan B baselines
    run_planc = plan_c_raw["raw_runs"]["s1_lossless_aes_planc_s123456"]

    with open(PLAN_B_SUMMARY) as f:
        dyn_b = json.load(f)
    run_planb = dyn_b["raw_runs"]["s1_lossless_aes_dyn_b_s123456"]

    sensor_ids = list(range(2, 16))
    leaf_ids = [5, 12, 14, 15]

    pb_powers = [run_planb["node_powers"][str(nid)]["model_b_total_mw"] for nid in sensor_ids]
    pc_powers = [run_planc["node_powers"][str(nid)]["model_b_total_mw"] for nid in sensor_ids]
    pb_rx_powers = [run_planb["node_powers"][str(nid)]["rx_mw"] for nid in sensor_ids]
    pc_rx_powers = [run_planc["node_powers"][str(nid)]["rx_mw"] for nid in sensor_ids]

    x = np.arange(len(sensor_ids))
    width = 0.38

    # Color coded bars: Green for Leaf, Blue for Relay
    colors_pc = ['#2980b9' if nid not in leaf_ids else '#27ae60' for nid in sensor_ids]

    b1 = ax.bar(x - width/2, pb_powers, width, label='Plan B Baseline (Always Active 8Hz ContikiMAC)', color='#bdc3c7', edgecolor='black', linewidth=0.6)
    b2 = ax.bar(x + width/2, pc_powers, width, label='Plan C (RPL-Aware Leaf RDC Sleep Enabled)', color=colors_pc, edgecolor='black', linewidth=0.6)

    # Highlight leaf nodes with annotations
    for i, nid in enumerate(sensor_ids):
        if nid in leaf_ids:
            pwr_drop = ((pc_powers[i] - pb_powers[i]) / pb_powers[i]) * 100.0
            rx_drop  = ((pc_rx_powers[i] - pb_rx_powers[i]) / pb_rx_powers[i]) * 100.0
            ax.text(x[i] + width/2, pc_powers[i] + 0.03, f"LEAF\n{pwr_drop:.1f}%\n(Rx {rx_drop:.0f}%)",
                    ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#196f3d')

    ax.set_xlabel('Sensor Node ID in Multi-Hop Topology')
    ax.set_ylabel('Total Node Power (mW, Model B 3.0V)')
    ax.set_title('Fig 9: Per-Node Power Profile (Relay vs. Sleeping Leaf Nodes in Scenario 1 Lossless)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Node {nid}\n({'LEAF' if nid in leaf_ids else 'Relay'})" for nid in sensor_ids], fontsize=8.8)
    ax.set_ylim(0, 1.65)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    # Custom legend for Leaf vs Relay
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#bdc3c7', edgecolor='black', label='Plan B Baseline (Always Active ContikiMAC)'),
        Patch(facecolor='#2980b9', edgecolor='black', label='Plan C Relay Node (Active Duty Cycle)'),
        Patch(facecolor='#27ae60', edgecolor='black', label='Plan C Leaf Node (RDC Sleeping, -38% Rx vs Plan B Leaf)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', framealpha=0.95)

    plt.tight_layout()
    save_dual(fig, "fig9_per_node_leaf_rdc_suppression.png")
    plt.close(fig)

def main():
    print("=" * 80)
    print("GENERATING UPGRADED PUBLICATION-QUALITY PLOTS FOR PLAN C (FIG 7, 8, 9)")
    print("=" * 80)

    with open(MASTER_JSON) as f:
        master_data = json.load(f)

    with open(PLAN_C_SUMMARY) as f:
        pc_raw = json.load(f)

    plot_fig7(master_data)
    plot_fig8(master_data, pc_raw)
    plot_fig9(pc_raw)

    print("\n[OK] All 3 publication figures generated successfully at 300 DPI!")

if __name__ == "__main__":
    main()
