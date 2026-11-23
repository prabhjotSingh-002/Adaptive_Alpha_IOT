#!/usr/bin/env python3
"""Generate publication-grade figures for paper/thesis from legacy benchmark data.

Produces:
1. Fig 1: Grouped bar chart of Total Power (mW) across 5, 10, 15 nodes comparing Mustafa Baseline vs k=1, k=2, k=4
2. Fig 2: Stacked power component breakdown (CPU, Tx, Rx, LPM) for 15-node topology
3. Fig 3: Energy-Latency Pareto Frontier (Mean Latency vs Total Energy per Reading)
4. Fig 4: Dual-Stack Consistency comparison (Contiki 2.7 ContikiMAC vs Contiki-NG CSMA)
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
SUMMARY_PATH = RESULTS_DIR / "legacy_matrix_summary.json"
PLOTS_DIR = RESULTS_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

with open(SUMMARY_PATH) as f:
    data = json.load(f)

# Mustafa Table 6 Baselines
MUSTAFA_TABLE_6 = {
    5: {
        "none":    {"cpu_mw": 0.0602, "rx_mw": 0.2582, "tx_mw": 0.1234, "lpm_mw": 0.1618, "total_mw": 0.6036},
        "aes":     {"cpu_mw": 0.1814, "rx_mw": 0.6624, "tx_mw": 0.6324, "lpm_mw": 0.1582, "total_mw": 1.6344},
        "speck":   {"cpu_mw": 0.1288, "rx_mw": 0.5440, "tx_mw": 0.3812, "lpm_mw": 0.1598, "total_mw": 1.2138},
        "present": {"cpu_mw": 0.1484, "rx_mw": 0.5588, "tx_mw": 0.4042, "lpm_mw": 0.1590, "total_mw": 1.2704},
    },
    10: {
        "none":    {"cpu_mw": 0.0766, "rx_mw": 0.3054, "tx_mw": 0.1641, "lpm_mw": 0.1611, "total_mw": 0.7072},
        "aes":     {"cpu_mw": 0.2536, "rx_mw": 1.0933, "tx_mw": 1.0291, "lpm_mw": 0.1557, "total_mw": 2.5317},
        "speck":   {"cpu_mw": 0.1745, "rx_mw": 0.7603, "tx_mw": 0.4326, "lpm_mw": 0.1580, "total_mw": 1.5254},
        "present": {"cpu_mw": 0.1943, "rx_mw": 0.8841, "tx_mw": 0.7050, "lpm_mw": 0.1575, "total_mw": 1.9409},
    },
    15: {
        "none":    {"cpu_mw": 0.0989, "rx_mw": 0.3695, "tx_mw": 0.1780, "lpm_mw": 0.1604, "total_mw": 0.8068},
        "aes":     {"cpu_mw": 0.4323, "rx_mw": 1.9682, "tx_mw": 2.0801, "lpm_mw": 0.1505, "total_mw": 4.6311},
        "speck":   {"cpu_mw": 0.2194, "rx_mw": 1.0060, "tx_mw": 0.4868, "lpm_mw": 0.1568, "total_mw": 1.8690},
        "present": {"cpu_mw": 0.3088, "rx_mw": 1.4993, "tx_mw": 1.3425, "lpm_mw": 0.1543, "total_mw": 3.3049},
    }
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "axes.grid": True,
    "grid.alpha": 0.3,
})

# ==============================================================================
# FIGURE 1: Grouped Bar Chart of Total Power (mW) across Topologies
# ==============================================================================
def plot_fig1():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), sharey=True)
    ciphers = ["speck", "aes", "present"]
    cipher_labels = ["SPECK-64/128", "AES-128-CCM", "PRESENT-128"]
    
    x = np.arange(len(ciphers))
    width = 0.20

    for idx, nodes in enumerate([5, 10, 15]):
        ax = axes[idx]
        mustafa_vals = [MUSTAFA_TABLE_6[nodes][c]["total_mw"] for c in ciphers]
        k1_vals = [data[f"{nodes}nodes_{c}_k1"]["mean_total_53uA_mw"] for c in ciphers]
        k2_vals = [data[f"{nodes}nodes_{c}_k2"]["mean_total_53uA_mw"] for c in ciphers]
        k4_vals = [data[f"{nodes}nodes_{c}_k4"]["mean_total_53uA_mw"] for c in ciphers]

        r1 = ax.bar(x - 1.5 * width, mustafa_vals, width, label="Mustafa Baseline (k=1)", color="#d95f02", alpha=0.85, edgecolor="black", hatch="//")
        r2 = ax.bar(x - 0.5 * width, k1_vals, width, label="Our k=1 (Tier 1 Stack)", color="#7570b3", alpha=0.85, edgecolor="black")
        r3 = ax.bar(x + 0.5 * width, k2_vals, width, label="Our k=2 (Batching)", color="#386cb0", alpha=0.85, edgecolor="black")
        r4 = ax.bar(x + 1.5 * width, k4_vals, width, label="Our k=4 (Max Batching)", color="#1b9e77", alpha=0.90, edgecolor="black")

        ax.set_title(f"{nodes}-Node Topology ({nodes-1} Sensors)", fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(cipher_labels, rotation=10, fontsize=11)
        ax.set_xlabel("Cryptographic Algorithm", fontsize=12)
        if idx == 0:
            ax.set_ylabel("Mean Total Power (mW)", fontsize=12)
            ax.legend(loc="upper left", framealpha=0.95)

        # Highlight savings on 15 nodes AES and SPECK with 2-line label and white background box
        if nodes == 15:
            ax.annotate("-82.3%\nvs. Mustafa", xy=(1 + 1.5 * width, k4_vals[1]), xytext=(1 - 0.45 * width, 2.5),
                        arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#1b9e77", alpha=0.95),
                        fontsize=9.5, fontweight="bold", color="#1b9e77", ha="center")
            ax.annotate("-56.8%\nvs. Mustafa", xy=(0 + 1.5 * width, k4_vals[0]), xytext=(0 - 0.45 * width, 2.0),
                        arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#1b9e77", alpha=0.95),
                        fontsize=9.5, fontweight="bold", color="#1b9e77", ha="center")

    plt.suptitle("Total Node Power Comparison: Mustafa et al. Baseline vs. Adaptive Batching (ContikiMAC 8 Hz)", y=0.98, fontweight="bold")
    plt.tight_layout()
    p = PLOTS_DIR / "fig1_total_power_grouped.png"
    plt.savefig(p, dpi=300)
    plt.close()
    print(f"Saved: {p}")


# ==============================================================================
# FIGURE 2: Stacked Power Component Breakdown (15-Node Topology)
# ==============================================================================
def plot_fig2():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    groups = []
    
    cpu_vals = []
    tx_vals = []
    rx_vals = []
    lpm_vals = []

    for c in ["none", "speck", "aes", "present"]:
        for cap in [1, 2, 4]:
            k = f"15nodes_{c}_k{cap}"
            res = data[k]
            groups.append(f"{c.upper()}\nk={cap}")
            cpu_vals.append(res["mean_cpu_mw"])
            tx_vals.append(res["mean_tx_mw"])
            rx_vals.append(res["mean_rx_mw"])
            lpm_vals.append(res["mean_lpm_53uA_mw"])

    x = np.arange(len(groups))
    width = 0.65

    p1 = ax.bar(x, lpm_vals, width, label="LPM Standby (53.3 µA)", color="#bdbdbd", edgecolor="black")
    p2 = ax.bar(x, rx_vals, width, bottom=lpm_vals, label="Radio Rx / Listen", color="#6baed6", edgecolor="black")
    p3 = ax.bar(x, tx_vals, width, bottom=np.array(lpm_vals) + np.array(rx_vals), label="Radio Tx", color="#fd8d3c", edgecolor="black")
    p4 = ax.bar(x, cpu_vals, width, bottom=np.array(lpm_vals) + np.array(rx_vals) + np.array(tx_vals), label="Active CPU", color="#74c476", edgecolor="black")

    ax.set_ylabel("Power Breakdown (mW)", fontsize=12)
    ax.set_title("15-Node Physical Power Breakdown by Hardware Subsystem (ContikiMAC 8 Hz)", pad=30, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=9.5)
    ax.set_xlabel("Cryptographic Profile & Batch Capacity (k)", fontsize=12)
    
    # Place horizontal legend cleanly above the plot area to prevent overlap
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=4, framealpha=0.95, fontsize=10.5)
    ax.set_ylim(0, 1.75)

    # Vertical group dividers
    for div in [2.5, 5.5, 8.5]:
        ax.axvline(div, color="grey", linestyle="--", alpha=0.5)

    plt.tight_layout()
    p = PLOTS_DIR / "fig2_power_breakdown_15nodes.png"
    plt.savefig(p, dpi=300)
    plt.close()
    print(f"Saved: {p}")


# ==============================================================================
# FIGURE 3: Energy-Latency Pareto Frontier (15-Node Topology)
# ==============================================================================
def plot_fig3():
    fig, ax = plt.subplots(figsize=(10, 6.4))

    ciphers = {
        "none":    {"label": "Plaintext (NONE)", "color": "#252525", "marker": "o"},
        "speck":   {"label": "SPECK-64/128", "color": "#1b9e77", "marker": "s"},
        "aes":     {"label": "AES-128-CCM", "color": "#386cb0", "marker": "^"},
        "present": {"label": "PRESENT-128", "color": "#d95f02", "marker": "D"},
    }

    # Plot curves
    for c, meta in ciphers.items():
        lats = []
        energies = []
        for cap in [1, 2, 4]:
            res = data[f"15nodes_{c}_k{cap}"]
            lat_s = res["mean_latency_ms"] / 1000.0
            tot_uj = res["tot_energy_uj_reading"]
            lats.append(lat_s)
            energies.append(tot_uj)

        ax.plot(lats, energies, linestyle="-", marker=meta["marker"], markersize=8,
                color=meta["color"], label=meta["label"], linewidth=2)
        
        # Individual marker labels for PRESENT (higher curve)
        if c == "present":
            for i, cap in enumerate([1, 2, 4]):
                ax.annotate(f"PRESENT k={cap}", xy=(lats[i], energies[i]), xytext=(lats[i] + 0.3, energies[i] + 250),
                            fontsize=9, color=meta["color"], fontweight="bold")

    # Clean cluster labels for lower lines (NONE, SPECK, AES) to avoid label clutter
    ax.annotate("k=1 (Unbatched)\n[~0.9s delay]", xy=(0.95, 11800), xytext=(1.8, 12600),
                arrowprops=dict(facecolor="#252525", shrink=0.08, width=0.8, headwidth=4),
                fontsize=9.5, fontweight="bold", color="#252525")

    ax.annotate("k=2 (Batched)\n[~6.0s delay]", xy=(6.0, 9600), xytext=(7.2, 10600),
                arrowprops=dict(facecolor="#386cb0", shrink=0.08, width=0.8, headwidth=4),
                fontsize=9.5, fontweight="bold", color="#386cb0")

    ax.annotate("k=4 (Max Batching)\n[~16.1s delay, -30% Energy]", xy=(16.1, 8100), xytext=(11.5, 9200),
                arrowprops=dict(facecolor="#1b9e77", shrink=0.08, width=0.8, headwidth=4),
                fontsize=9.5, fontweight="bold", color="#1b9e77")

    ax.set_xlabel("Mean End-to-End Delivery Latency (Seconds)", fontsize=12)
    ax.set_ylabel(r"Total Energy per Delivered Reading ($\mu$J)", fontsize=12)
    ax.set_title("Energy–Latency Pareto Trade-off Frontier (15 Nodes, ContikiMAC 8 Hz)", pad=32, fontweight="bold")
    
    # Place horizontal legend at top center
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=4, framealpha=0.95, fontsize=10)
    ax.set_xlim(-0.5, 20.5)
    ax.set_ylim(7000, 18000)

    # Highlight operational regimes with shaded spans
    ax.axvspan(-0.5, 2.8, alpha=0.08, color="green")
    ax.axvspan(4.2, 8.2, alpha=0.08, color="blue")
    ax.axvspan(14.0, 19.8, alpha=0.08, color="purple")

    # Clean banner texts in upper margin (shortened to prevent border clipping)
    ax.text(1.15, 16900, "Regime 1: Delay-Critical\n(<2s, Alarm / Real-time)", fontsize=9.5, color="darkgreen", fontweight="bold", ha="center")
    ax.text(6.2, 16900, "Regime 2: Balanced\n(~6s, Regular Telemetry)", fontsize=9.5, color="darkblue", fontweight="bold", ha="center")
    ax.text(16.9, 16900, "Regime 3: High Efficiency\n(~16s, Delay-Tolerant)", fontsize=9.5, color="purple", fontweight="bold", ha="center")

    plt.tight_layout()
    p = PLOTS_DIR / "fig3_pareto_energy_latency.png"
    plt.savefig(p, dpi=300)
    plt.close()
    print(f"Saved: {p}")


# ==============================================================================
# FIGURE 4: Dual-Stack Consistency (Contiki 2.7 ContikiMAC vs Contiki-NG CSMA)
# ==============================================================================
def plot_fig4():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.6))

    # Left: Contiki 2.7 ContikiMAC 8 Hz (Total Node Power mW) across all 4 ciphers
    ciphers_left = ["none", "speck", "aes", "present"]
    labels_left = ["NONE", "SPECK-64/128", "AES-128-CCM", "PRESENT-128"]
    x_left = np.arange(len(ciphers_left))
    width = 0.25

    k1_legacy = [data[f"15nodes_{c}_k1"]["mean_total_53uA_mw"] for c in ciphers_left]
    k2_legacy = [data[f"15nodes_{c}_k2"]["mean_total_53uA_mw"] for c in ciphers_left]
    k4_legacy = [data[f"15nodes_{c}_k4"]["mean_total_53uA_mw"] for c in ciphers_left]

    ax1.bar(x_left - width, k1_legacy, width, label="k=1 (Unbatched)", color="#7570b3", edgecolor="black")
    ax1.bar(x_left, k2_legacy, width, label="k=2 (Batched)", color="#386cb0", edgecolor="black")
    ax1.bar(x_left + width, k4_legacy, width, label="k=4 (Max Batch)", color="#1b9e77", edgecolor="black")

    ax1.set_title("Contiki 2.7 (ContikiMAC @ 8 Hz)\nTotal Node Power (mW)", fontweight="bold", fontsize=12, pad=38)
    ax1.set_xticks(x_left)
    ax1.set_xticklabels(labels_left, fontsize=10.5)
    ax1.set_ylabel("Mean Total Power (mW)", fontsize=12)
    ax1.set_xlabel("Cryptographic Algorithm", fontsize=12)
    ax1.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, framealpha=0.95, fontsize=10)
    ax1.set_ylim(0, 1.75)

    # Right: Contiki-NG 4.9 CSMA (Radio Tx Energy per Delivered Reading µJ)
    # Exact verified Contiki-NG 15-node 100s-warmup dataset:
    # NONE: 338.72 / 238.15 / 176.22 (-48.0%)
    # SPECK: 451.32 / 274.19 / 192.50 (-57.4%)
    # AES: 434.59 / 278.56 / 212.68 (-51.1%)
    # Note: PRESENT omitted due to 23%-34% PDR collapse in Contiki-NG (2,066-11,399 uJ/rdg)
    ciphers_right = ["none", "speck", "aes"]
    labels_right = ["NONE", "SPECK-64/128", "AES-128-CCM"]
    x_right = np.arange(len(ciphers_right))

    k1_ng_tx = [338.72, 451.32, 434.59]
    k2_ng_tx = [238.15, 274.19, 278.56]
    k4_ng_tx = [176.22, 192.50, 212.68]

    ax2.bar(x_right - width, k1_ng_tx, width, label="k=1 (Unbatched)", color="#7570b3", edgecolor="black")
    ax2.bar(x_right, k2_ng_tx, width, label="k=2 (Batched)", color="#386cb0", edgecolor="black")
    ax2.bar(x_right + width, k4_ng_tx, width, label="k=4 (Max Batch)", color="#1b9e77", edgecolor="black")

    ax2.set_title("Contiki-NG 4.9 (CSMA NullRDC)\nRadio Tx Energy per Delivered Reading (µJ)*", fontweight="bold", fontsize=12, pad=38)
    ax2.set_xticks(x_right)
    ax2.set_xticklabels(labels_right, fontsize=10.5)
    ax2.set_ylabel(r"Tx Energy per Reading ($\mu$J)", fontsize=12)
    ax2.set_xlabel("Cryptographic Algorithm", fontsize=12)
    ax2.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, framealpha=0.95, fontsize=10)
    ax2.set_ylim(0, 560)

    # Annotate saving on Contiki-NG
    ax2.annotate("-57.4%", xy=(1 + width, k4_ng_tx[1]), xytext=(1 + 0.1 * width, 320),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                 fontsize=10, fontweight="bold", color="#1b9e77", ha="center")
    ax2.annotate("-51.1%", xy=(2 + width, k4_ng_tx[2]), xytext=(2 + 0.1 * width, 320),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                 fontsize=10, fontweight="bold", color="#1b9e77", ha="center")

    plt.suptitle("Cross-Stack Consistency: Monotonic Batching Gains in ContikiMAC Total Power & Contiki-NG Tx Energy", y=0.985, fontweight="bold", fontsize=13)
    plt.figtext(0.55, 0.01, "*Note: PRESENT-128 omitted on Contiki-NG panel due to 23%–34% PDR collapse (2,066–11,399 µJ/rdg).", fontsize=8.5, style="italic")
    plt.tight_layout(rect=[0, 0.04, 1, 0.94])
    p = PLOTS_DIR / "fig4_dual_stack_comparison.png"
    plt.savefig(p, dpi=300)
    plt.close()
    print(f"Saved: {p}")


if __name__ == "__main__":
    print("Generating refined publication figures...")
    plot_fig1()
    plot_fig2()
    plot_fig3()
    plot_fig4()
    print("All figures successfully generated in:", PLOTS_DIR)
