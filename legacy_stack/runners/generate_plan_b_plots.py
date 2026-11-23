#!/usr/bin/env python3
"""
Publication Plot Generator for Plan B Adaptive Batching (300 DPI).
Outputs:
1. plots_dyn_b/fig5_dyn_b_power_vs_alarm_latency.png:
   - Panel A: Mean Network Power & Bottleneck Node 3 Power (Static k=1 vs k=4 vs Plan B).
   - Panel B: Alarm Latency vs Normal Telemetry Latency (Pareto breakthrough).
2. plots_dyn_b/fig6_lossy_channel_resilience.png:
   - Panel A: Delivery-Adjusted Total Energy per Reading (uJ) with 3-seed Mean +- SD error bars.
   - Panel B: Mean Alarm Latency (s) & Overall PDR (%).
   - Panel C: Peak Consecutive Outage Gap (s).
"""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
SUMMARY_FILE = BASE_DIR / "results_dyn_b" / "dyn_b_summary.json"
PLOTS_DIR = BASE_DIR / "plots_dyn_b"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Also sync to conversation brain artifacts
ARTIFACT_PLOTS_DIR = Path("C:/Users/Yatin Singh/.gemini/antigravity/brain/f9125195-a215-418a-9bf6-5f1466ae491f/plots_dyn_b")
ARTIFACT_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Styling standards matching fig1..fig4
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Palette
C_STATIC_K1 = "#7f8c8d"   # Gray baseline
C_STATIC_K4 = "#2980b9"   # Primary Blue
C_VOI_ONLY  = "#e67e22"   # Orange
C_PLAN_B    = "#27ae60"   # Forest Green (Winner)
C_NODE3     = "#c0392b"   # Red (Bottleneck)

def plot_fig5(summary: dict):
    """Figure 5: Power Consumption and Latency Pareto Breakthrough (Lossless Scenario 1)."""
    s1 = summary["scenario_1_lossless"]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8))
    
    # ---------------- Panel A: Power Consumption & Bottleneck Relay ----------------
    ciphers = ["aes", "speck"]
    cipher_labels = ["AES-128-CCM", "SPECK-64/128"]
    
    x = np.arange(len(ciphers))
    width = 0.22
    
    # Data extraction
    pwr_k1_mean = [s1[c]["static_k1"]["mean_model_b_mw"] for c in ciphers]
    pwr_k4_mean = [s1[c]["static_k4"]["mean_model_b_mw"] for c in ciphers]
    pwr_pb_mean = [s1[c]["dyn_b"]["mean_model_b_mw"] for c in ciphers]
    
    n3_k1 = [s1[c]["static_k1"]["node3_model_b_mw"] for c in ciphers]
    n3_k4 = [s1[c]["static_k4"]["node3_model_b_mw"] for c in ciphers]
    n3_pb = [s1[c]["dyn_b"]["node3_model_b_mw"] for c in ciphers]
    
    # Bars for Mean Network Power
    b1 = ax1.bar(x - width, pwr_k1_mean, width, label="Static $k=1$ (Network Mean)", color=C_STATIC_K1, alpha=0.85, edgecolor="black", linewidth=1)
    b2 = ax1.bar(x,         pwr_k4_mean, width, label="Static $k=4$ (Network Mean)", color=C_STATIC_K4, alpha=0.85, edgecolor="black", linewidth=1)
    b3 = ax1.bar(x + width, pwr_pb_mean, width, label="Plan B (Network Mean)",     color=C_PLAN_B,    alpha=0.90, edgecolor="black", linewidth=1.2)
    
    # Overlay lines/markers for Node 3 Bottleneck Relay Power
    ax1.plot(x - width, n3_k1, marker="D", markersize=7, color=C_NODE3, linestyle="None", label="Bottleneck Node 3 Power")
    ax1.plot(x,         n3_k4, marker="D", markersize=7, color=C_NODE3, linestyle="None")
    ax1.plot(x + width, n3_pb, marker="D", markersize=7, color=C_NODE3, linestyle="None")
    
    # Annotate savings
    for i, c in enumerate(ciphers):
        saving_pct = ((pwr_k1_mean[i] - pwr_pb_mean[i]) / pwr_k1_mean[i]) * 100.0
        fnd_ratio = s1[c]["dyn_b"]["fnd_lifetime_ratio"]
        ax1.text(x[i] + width, pwr_pb_mean[i] + 0.03, f"-{saving_pct:.1f}%\n({fnd_ratio:.2f}× FND)", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#196f3d")
    
    ax1.set_ylabel("Power Consumption (mW)")
    ax1.set_title("(a) Power Consumption & Relay Stress (15 Nodes, Lossless)", pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cipher_labels, fontweight="bold")
    ax1.set_ylim(0, max(max(n3_k1), max(pwr_k1_mean)) * 1.25)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", framealpha=0.92)
    
    # ---------------- Panel B: Latency Pareto Trade-off Breakthrough ----------------
    # Plot Alarm Latency vs Normal Latency
    modes_cfg = [
        ("Static $k=1$", C_STATIC_K1, "o", 90),
        ("Static $k=4$", C_STATIC_K4, "s", 100),
        ("Plan B (Dynamic)", C_PLAN_B, "*", 180),
    ]
    
    for c_idx, c in enumerate(ciphers):
        c_name = "AES" if c == "aes" else "SPECK"
        marker_style = "-" if c == "aes" else "--"
        
        l_norm = [s1[c]["static_k1"]["mean_norm_lat_ms"] / 1000.0,
                  s1[c]["static_k4"]["mean_norm_lat_ms"] / 1000.0,
                  s1[c]["dyn_b"]["mean_norm_lat_ms"] / 1000.0]
        l_alarm = [s1[c]["static_k1"]["mean_alarm_lat_ms"] / 1000.0,
                   s1[c]["static_k4"]["mean_alarm_lat_ms"] / 1000.0,
                   s1[c]["dyn_b"]["mean_alarm_lat_ms"] / 1000.0]
        
        ax2.plot(l_norm, l_alarm, color="gray", linestyle=marker_style, alpha=0.6, zorder=1)
        
        # Plot points
        for m_idx, (m_label, m_col, m_shape, m_size) in enumerate(modes_cfg):
            pt_label = f"{m_label} ({c_name})" if c == "aes" else None
            ax2.scatter(l_norm[m_idx], l_alarm[m_idx], color=m_col, marker=m_shape, s=m_size, edgecolor="black", linewidth=1.2, zorder=3, label=pt_label)
            
            # Text callout
            offset_y = 1.0 if m_idx == 1 else -0.8
            offset_x = 0.4 if m_idx == 2 else 0.2
            ax2.annotate(f"{c_name}: {l_alarm[m_idx]:.2f}s", (l_norm[m_idx], l_alarm[m_idx]),
                         textcoords="offset points", xytext=(offset_x*10, offset_y*12),
                         fontsize=9, fontweight="bold" if m_idx == 2 else "normal",
                         bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=m_col, alpha=0.85))
    
    # Draw Sub-Second VoI Zone
    ax2.axhspan(0, 1.0, color="#d5f5e3", alpha=0.45, label="Sub-Second VoI Safety Zone (<1.0s)", zorder=0)
    
    ax2.set_xlabel("Mean Normal Telemetry Latency (s)")
    ax2.set_ylabel("Mean Critical Alarm Latency (s)")
    ax2.set_title("(b) Breaking the Static Pareto Trade-Off", pad=12)
    ax2.set_xlim(0, max(l_norm) * 1.25)
    ax2.set_ylim(-0.2, max(l_alarm) * 1.35)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", framealpha=0.92)
    
    plt.tight_layout()
    out1 = PLOTS_DIR / "fig5_dyn_b_power_vs_alarm_latency.png"
    out2 = ARTIFACT_PLOTS_DIR / "fig5_dyn_b_power_vs_alarm_latency.png"
    plt.savefig(out1)
    plt.savefig(out2)
    plt.close()
    print(f"Generated Figure 5: {out1}")

def plot_fig6(summary: dict):
    """Figure 6: Multi-Hop Lossy Channel Resilience (Scenario 2: Rx=0.75, Tx=0.85, 3-Seed Mean +- SD)."""
    s2 = summary["scenario_2_lossy"]
    ciphers = ["aes", "speck"]
    cipher_labels = ["AES-128-CCM", "SPECK-64/128"]
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(17, 5.4))
    
    x = np.arange(len(ciphers))
    width = 0.26
    
    # Modes in Scenario 2: static_k4, voi_only, dyn_b
    modes = ["static_k4", "voi_only", "dyn_b"]
    labels = ["Static $k=4$", "VoI-Only (No ETX Cap)", "Plan B (Dynamic)"]
    colors = [C_STATIC_K4, C_VOI_ONLY, C_PLAN_B]
    
    # ---------------- Panel A: Delivery-Adjusted Energy (uJ / Rdg) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        means = [s2[c][m]["tot_energy_uj_reading"]["mean"] for c in ciphers]
        stds  = [s2[c][m]["tot_energy_uj_reading"]["std"] for c in ciphers]
        rects = ax1.bar(x + (idx - 1)*width, means, width, yerr=stds, capsize=5, label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        # Label values on top of bars
        for r, val in zip(rects, means):
            ax1.text(r.get_x() + r.get_width()/2.0, r.get_height() + 1200, f"{val:.0f}", ha="center", va="bottom", fontsize=8.5, rotation=0)

    # Net saving callout vs VoI-Only
    for i, c in enumerate(ciphers):
        saving = ((s2[c]["voi_only"]["tot_energy_uj_reading"]["mean"] - s2[c]["dyn_b"]["tot_energy_uj_reading"]["mean"]) / s2[c]["voi_only"]["tot_energy_uj_reading"]["mean"]) * 100.0
        ax1.annotate(f"-{saving:.1f}% Energy", xy=(x[i] + width, s2[c]["dyn_b"]["tot_energy_uj_reading"]["mean"]),
                     xytext=(x[i] + width, s2[c]["dyn_b"]["tot_energy_uj_reading"]["mean"] * 0.65),
                     ha="center", fontsize=9.5, fontweight="bold", color="#145a32",
                     arrowprops=dict(arrowstyle="->", color="#145a32", lw=1.2))

    ax1.set_ylabel(r"Total Energy / Delivered Reading ($\mu\text{J}$)")
    ax1.set_title("(a) Delivery-Adjusted Energy under Loss", pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cipher_labels, fontweight="bold")
    ax1.set_ylim(0, max([s2[c]["static_k4"]["tot_energy_uj_reading"]["mean"] for c in ciphers]) * 1.35)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", framealpha=0.92)

    # ---------------- Panel B: Mean Alarm Latency (s) & PDR (%) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        lat_means = [s2[c][m]["mean_alarm_lat_ms"]["mean"] / 1000.0 for c in ciphers]
        lat_stds  = [s2[c][m]["mean_alarm_lat_ms"]["std"] / 1000.0 for c in ciphers]
        rects = ax2.bar(x + (idx - 1)*width, lat_means, width, yerr=lat_stds, capsize=5, label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        for r, val in zip(rects, lat_means):
            ax2.text(r.get_x() + r.get_width()/2.0, r.get_height() + 0.5, f"{val:.1f}s", ha="center", va="bottom", fontsize=8.5)

    ax2.set_ylabel("Mean Critical Alarm Latency (s)")
    ax2.set_title("(b) Critical Alarm Responsiveness under Loss", pad=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(cipher_labels, fontweight="bold")
    ax2.set_ylim(0, max([s2[c]["static_k4"]["mean_alarm_lat_ms"]["mean"]/1000.0 for c in ciphers]) * 1.35)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", framealpha=0.92)

    # ---------------- Panel C: Peak Consecutive Outage Duration (s) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        gap_means = [s2[c][m]["max_consecutive_missing_s"]["mean"] for c in ciphers]
        gap_stds  = [s2[c][m]["max_consecutive_missing_s"]["std"] for c in ciphers]
        rects = ax3.bar(x + (idx - 1)*width, gap_means, width, yerr=gap_stds, capsize=5, label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        for r, val in zip(rects, gap_means):
            ax3.text(r.get_x() + r.get_width()/2.0, r.get_height() + 2.0, f"{val:.0f}s", ha="center", va="bottom", fontsize=8.5)

    # Outage reduction callout
    for i, c in enumerate(ciphers):
        gap_red = ((s2[c]["static_k4"]["max_consecutive_missing_s"]["mean"] - s2[c]["dyn_b"]["max_consecutive_missing_s"]["mean"]) / s2[c]["static_k4"]["max_consecutive_missing_s"]["mean"]) * 100.0
        ax3.annotate(f"-{gap_red:.0f}% Gap", xy=(x[i] + width, s2[c]["dyn_b"]["max_consecutive_missing_s"]["mean"]),
                     xytext=(x[i] + width, s2[c]["dyn_b"]["max_consecutive_missing_s"]["mean"] * 0.65),
                     ha="center", fontsize=9.5, fontweight="bold", color="#145a32",
                     arrowprops=dict(arrowstyle="->", color="#145a32", lw=1.2))

    ax3.set_ylabel("Peak Consecutive Outage Duration (s)")
    ax3.set_title("(c) Bounding Loss Burst Outages", pad=12)
    ax3.set_xticks(x)
    ax3.set_xticklabels(cipher_labels, fontweight="bold")
    ax3.set_ylim(0, 110)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right", framealpha=0.92)

    plt.tight_layout()
    out1 = PLOTS_DIR / "fig6_lossy_channel_resilience.png"
    out2 = ARTIFACT_PLOTS_DIR / "fig6_lossy_channel_resilience.png"
    plt.savefig(out1)
    plt.savefig(out2)
    plt.close()
    print(f"Generated Figure 6: {out1}")

def main():
    if not SUMMARY_FILE.exists():
        print(f"Summary file not found: {SUMMARY_FILE}")
        return
    with open(SUMMARY_FILE) as f:
        summary = json.load(f)
    plot_fig5(summary)
    plot_fig6(summary)
    print("All publication plots successfully generated!")

if __name__ == "__main__":
    main()
