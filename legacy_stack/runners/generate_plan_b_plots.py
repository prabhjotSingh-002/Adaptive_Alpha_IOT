#!/usr/bin/env python3
"""
Publication Plot Generator for Plan B Adaptive Batching (300 DPI).
Outputs:
1. plots_dyn_b/fig5_dyn_b_power_vs_alarm_latency.png:
   - Panel (a): Mean Network Power & Bottleneck Node 3 Power (Static k=1 vs k=4 vs Plan B).
     Headroom raised to ylim(0, 3.15), legend at upper left with zero overlap with Node 3 (2.15 mW).
   - Panel (b): Alarm Latency vs Normal Telemetry Latency (Pareto breakthrough).
     Unified cipher markers (solid AES, open SPECK), clean legend at upper left,
     xlim(0, 18.0), ylim(-0.5, 34.0), non-colliding callout boxes.
2. plots_dyn_b/fig6_lossy_channel_resilience.png:
   - Publication-grade 2x2 layout with a SINGLE shared horizontal legend at the top:
     Panel (a): Delivery-Adjusted Total Energy per Reading (uJ/rdg) with ylim(0, 62000).
     Panel (b): Overall PDR (%) with ylim(0, 78).
     Panel (c): Mean Critical Alarm Latency (s) with ylim(0, 34).
     Panel (d): Peak Consecutive Outage Duration (s) with ylim(0, 148).
   - Zero title clipping, labels positioned cleanly above error caps, in-bar callouts with zero overlap.
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

# Also sync to conversation brain artifacts and Plan B working directory
ARTIFACT_PLOTS_DIR = Path("C:/Users/Yatin Singh/.gemini/antigravity/brain/f9125195-a215-418a-9bf6-5f1466ae491f/plots_dyn_b")
ARTIFACT_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
PLAN_B_WORKING_PLOTS = Path("C:/Users/Yatin Singh/Documents/Btech Project - 1/Plan_B_Working_And_Results/plots_dyn_b")
PLAN_B_WORKING_PLOTS.mkdir(parents=True, exist_ok=True)

# Publication styling matching IEEE / ACM standard
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 12.5,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Color palette
C_STATIC_K1 = "#7f8c8d"   # Gray baseline
C_STATIC_K4 = "#2980b9"   # Primary Blue
C_VOI_ONLY  = "#e67e22"   # Orange
C_PLAN_B    = "#27ae60"   # Forest Green (Winner)
C_NODE3     = "#c0392b"   # Red (Bottleneck Node 3)

def plot_fig5(summary: dict):
    """Figure 5: Power Consumption and Latency Pareto Breakthrough (Lossless Scenario 1)."""
    s1 = summary["scenario_1_lossless"]
    ciphers = ["aes", "speck"]
    cipher_labels = ["AES-128-CCM", "SPECK-64/128"]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8))
    
    # ---------------- Panel (a): Power Consumption & Bottleneck Relay ----------------
    x = np.arange(len(ciphers))
    width = 0.22
    
    pwr_k1_mean = [s1[c]["static_k1"]["mean_model_b_mw"] for c in ciphers]
    pwr_k4_mean = [s1[c]["static_k4"]["mean_model_b_mw"] for c in ciphers]
    pwr_pb_mean = [s1[c]["dyn_b"]["mean_model_b_mw"] for c in ciphers]
    
    n3_k1 = [s1[c]["static_k1"]["node3_model_b_mw"] for c in ciphers]
    n3_k4 = [s1[c]["static_k4"]["node3_model_b_mw"] for c in ciphers]
    n3_pb = [s1[c]["dyn_b"]["node3_model_b_mw"] for c in ciphers]
    
    # Bars for Mean Network Power
    b1 = ax1.bar(x - width, pwr_k1_mean, width, label="Static $k=1$ (Network Mean)", color=C_STATIC_K1, alpha=0.85, edgecolor="black", linewidth=1.1)
    b2 = ax1.bar(x,         pwr_k4_mean, width, label="Static $k=4$ (Network Mean)", color=C_STATIC_K4, alpha=0.85, edgecolor="black", linewidth=1.1)
    b3 = ax1.bar(x + width, pwr_pb_mean, width, label="Plan B (Network Mean)",     color=C_PLAN_B,    alpha=0.90, edgecolor="black", linewidth=1.2)
    
    # Markers for Node 3 Bottleneck Relay Power
    ax1.plot(x - width, n3_k1, marker="D", markersize=7.5, color=C_NODE3, linestyle="None", label="Bottleneck Node 3 Relay", zorder=5)
    ax1.plot(x,         n3_k4, marker="D", markersize=7.5, color=C_NODE3, linestyle="None", zorder=5)
    ax1.plot(x + width, n3_pb, marker="D", markersize=7.5, color=C_NODE3, linestyle="None", zorder=5)
    
    # Annotate Node 3 exact numbers cleanly above the markers
    for i in range(len(ciphers)):
        ax1.text(x[i] - width, n3_k1[i] + 0.08, f"{n3_k1[i]:.2f}", ha="center", va="bottom", fontsize=8.5, color=C_NODE3, fontweight="bold")
        ax1.text(x[i],         n3_k4[i] + 0.08, f"{n3_k4[i]:.2f}", ha="center", va="bottom", fontsize=8.5, color=C_NODE3, fontweight="bold")
        ax1.text(x[i] + width, n3_pb[i] + 0.08, f"{n3_pb[i]:.2f}", ha="center", va="bottom", fontsize=8.5, color=C_NODE3, fontweight="bold")
        
        # Annotate savings inside the Plan B bar with compact font
        saving_pct = ((pwr_k1_mean[i] - pwr_pb_mean[i]) / pwr_k1_mean[i]) * 100.0
        fnd_ratio = s1[ciphers[i]]["dyn_b"]["fnd_lifetime_ratio"]
        ax1.text(x[i] + width, pwr_pb_mean[i] / 2.0, f"-{saving_pct:.1f}%\n({fnd_ratio:.2f}× FND)",
                 ha="center", va="center", fontsize=7.8, fontweight="bold", color="white")
    
    ax1.set_ylabel("Power Consumption (mW)")
    ax1.set_title("(a) Power Consumption & Relay Stress (15 Nodes, Lossless)", pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cipher_labels, fontweight="bold")
    ax1.set_ylim(0, 3.20)  # Raised limit ensures 1.05 mW clearance above Node 3 (2.15 mW)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", framealpha=0.92, ncol=2)
    
    # ---------------- Panel (b): Latency Pareto Trade-off Breakthrough ----------------
    modes_cfg = [
        ("Static $k=1$", C_STATIC_K1, "o", 85),
        ("Static $k=4$", C_STATIC_K4, "s", 95),
        ("Plan B (Dynamic)", C_PLAN_B, "*", 190),
    ]
    
    # Plot trajectories
    for c_idx, c in enumerate(ciphers):
        c_name = "AES" if c == "aes" else "SPECK"
        line_style = "-" if c == "aes" else "--"
        line_alpha = 0.55 if c == "aes" else 0.45
        
        l_norm = [s1[c]["static_k1"]["mean_norm_lat_ms"] / 1000.0,
                  s1[c]["static_k4"]["mean_norm_lat_ms"] / 1000.0,
                  s1[c]["dyn_b"]["mean_norm_lat_ms"] / 1000.0]
        l_alarm = [s1[c]["static_k1"]["mean_alarm_lat_ms"] / 1000.0,
                   s1[c]["static_k4"]["mean_alarm_lat_ms"] / 1000.0,
                   s1[c]["dyn_b"]["mean_alarm_lat_ms"] / 1000.0]
        
        ax2.plot(l_norm, l_alarm, color="#555555", linestyle=line_style, linewidth=1.5, alpha=line_alpha, zorder=2)
        
        # Plot points: Solid fill for AES, hollow white fill for SPECK
        for m_idx, (m_label, m_col, m_shape, m_size) in enumerate(modes_cfg):
            face_col = m_col if c == "aes" else "white"
            edge_w = 1.2 if c == "aes" else 2.0
            ax2.scatter(l_norm[m_idx], l_alarm[m_idx], facecolor=face_col, edgecolor=m_col,
                        marker=m_shape, s=m_size, linewidth=edge_w, zorder=4)

    # Clean non-overlapping callout boxes positioned with ample margins
    # Cluster 1: Static k=1 (near x=1.0, y=0.9)
    ax2.annotate("Static $k=1$\nAES: 0.89s | SPECK: 0.90s", xy=(1.02, 0.90),
                 xytext=(1.8, 4.2), textcoords="data",
                 fontsize=8.8, ha="left",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=C_STATIC_K1, alpha=0.92),
                 arrowprops=dict(arrowstyle="->", color=C_STATIC_K1, lw=1.2))

    # Cluster 2: Static k=4 (near x=14.0, y=26.1) - Placed at x=10.2, y=29.2 to avoid legend
    ax2.annotate("Static $k=4$ (Batching Delay)\nAES: 26.24s | SPECK: 25.96s", xy=(14.06, 26.10),
                 xytext=(9.0, 29.5), textcoords="data",
                 fontsize=8.8, ha="left",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#f8f9fa", ec=C_STATIC_K4, alpha=0.92),
                 arrowprops=dict(arrowstyle="->", color=C_STATIC_K4, lw=1.2))

    # Cluster 3: Plan B Dynamic (near x=14.3, y=0.94)
    ax2.annotate("Plan B (VoI Early Flush)\nAES: 0.89s | SPECK: 0.99s\n(-96% Alarm Latency vs $k=4$)", xy=(14.33, 0.94),
                 xytext=(9.2, 7.5), textcoords="data",
                 fontsize=8.8, ha="left", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.35", fc="#eafaf1", ec=C_PLAN_B, lw=1.4, alpha=0.95),
                 arrowprops=dict(arrowstyle="->", color=C_PLAN_B, lw=1.4))

    # Sub-Second VoI Zone (Shifted to x=3.2 to avoid overlap with Static k=1 marker at x=1.0)
    ax2.axhspan(0, 1.0, color="#d5f5e3", alpha=0.45, zorder=1)
    ax2.text(3.2, 0.35, "Sub-Second VoI Zone (< 1.0s)", fontsize=9, color="#145a32", fontweight="bold")
    
    # Legend construction: Clean separate mode entries and cipher indicators
    leg_handles = [
        matplotlib.lines.Line2D([0], [0], marker="o", color=C_STATIC_K1, label="Static $k=1$", markersize=7, linestyle="None"),
        matplotlib.lines.Line2D([0], [0], marker="s", color=C_STATIC_K4, label="Static $k=4$", markersize=7, linestyle="None"),
        matplotlib.lines.Line2D([0], [0], marker="*", color=C_PLAN_B, label="Plan B (Dynamic)", markersize=11, linestyle="None"),
        matplotlib.lines.Line2D([0], [0], marker="o", markerfacecolor="#333333", markeredgecolor="#333333", color="#333333", linestyle="-", label="AES-128-CCM (Solid)"),
        matplotlib.lines.Line2D([0], [0], marker="o", markerfacecolor="white", markeredgecolor="#333333", color="#333333", linestyle="--", label="SPECK-64/128 (Hollow)"),
    ]
    ax2.legend(handles=leg_handles, loc="upper left", framealpha=0.92, fontsize=8.8)

    ax2.set_xlabel("Mean Normal Telemetry Latency (s)")
    ax2.set_ylabel("Mean Critical Alarm Latency (s)")
    ax2.set_title("(b) Breaking the Static Pareto Trade-Off", pad=12)
    ax2.set_xlim(0, 18.0)
    ax2.set_ylim(-0.5, 34.0)
    ax2.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    for dest in [PLOTS_DIR, ARTIFACT_PLOTS_DIR, PLAN_B_WORKING_PLOTS]:
        plt.savefig(dest / "fig5_dyn_b_power_vs_alarm_latency.png")
    plt.close()
    print("Generated Publication Figure 5 successfully.")

def plot_fig6(summary: dict):
    """Figure 6: Multi-Hop Lossy Channel Resilience (Scenario 2: Rx=0.75, Tx=0.85, 3-Seed Mean +- SD)."""
    s2 = summary["scenario_2_lossy"]
    ciphers = ["aes", "speck"]
    cipher_labels = ["AES-128-CCM", "SPECK-64/128"]
    
    # 2x2 grid for clean 4-panel presentation
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13.5, 10.0))
    
    x = np.arange(len(ciphers))
    width = 0.25
    
    modes = ["static_k4", "voi_only", "dyn_b"]
    labels = ["Static $k=4$", "VoI-Only (No ETX Cap)", "Plan B (Dynamic)"]
    colors = [C_STATIC_K4, C_VOI_ONLY, C_PLAN_B]
    
    # ---------------- Panel (a): Delivery-Adjusted Energy (uJ / Rdg) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        means = [s2[c][m]["tot_energy_uj_reading"]["mean"] for c in ciphers]
        stds  = [s2[c][m]["tot_energy_uj_reading"]["std"] for c in ciphers]
        rects = ax1.bar(x + (idx - 1)*width, means, width, yerr=stds, capsize=4.5,
                        label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        for r, val, std in zip(rects, means, stds):
            y_pos = val + std + 1400
            ax1.text(r.get_x() + r.get_width()/2.0, y_pos, f"{val:.0f}",
                     ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    # Net saving callout vs VoI-Only on SPECK (Arrow target adjusted to avoid 25247 label)
    speck_voi_e = s2["speck"]["voi_only"]["tot_energy_uj_reading"]["mean"]
    speck_pb_e  = s2["speck"]["dyn_b"]["tot_energy_uj_reading"]["mean"]
    saving = ((speck_voi_e - speck_pb_e) / speck_voi_e) * 100.0
    ax1.annotate(f"-{saving:.1f}% Energy", xy=(x[1] + width + 0.08, speck_pb_e + s2["speck"]["dyn_b"]["tot_energy_uj_reading"]["std"] + 2400),
                 xytext=(x[1] + width + 0.22, 47000),
                 ha="center", fontsize=9.2, fontweight="bold", color="#145a32",
                 bbox=dict(boxstyle="round,pad=0.25", fc="#eafaf1", ec=C_PLAN_B, lw=1.2),
                 arrowprops=dict(arrowstyle="->", color=C_PLAN_B, lw=1.3))

    ax1.set_ylabel(r"Energy / Delivered Rdg ($\mu\text{J}$)")
    ax1.set_title("(a) Delivery-Adjusted Energy under Loss", pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(cipher_labels, fontweight="bold")
    ax1.set_ylim(0, 62000)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # ---------------- Panel (b): Overall Packet Delivery Ratio (PDR %) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        pdr_means = [s2[c][m]["pdr"]["mean"] for c in ciphers]
        pdr_stds  = [s2[c][m]["pdr"]["std"] for c in ciphers]
        rects = ax2.bar(x + (idx - 1)*width, pdr_means, width, yerr=pdr_stds, capsize=4.5,
                        label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        for r, val, std in zip(rects, pdr_means, pdr_stds):
            y_pos = val + std + 1.8
            ax2.text(r.get_x() + r.get_width()/2.0, y_pos, f"{val:.1f}%",
                     ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    # PDR gain callout inside Plan B bar on SPECK
    speck_voi_pdr = s2["speck"]["voi_only"]["pdr"]["mean"]
    speck_pb_pdr  = s2["speck"]["dyn_b"]["pdr"]["mean"]
    pdr_gain = speck_pb_pdr - speck_voi_pdr
    ax2.text(x[1] + width, speck_pb_pdr / 2.0, f"+{pdr_gain:.1f}%\nPDR",
             ha="center", va="center", fontsize=8.8, fontweight="bold", color="white")

    ax2.set_ylabel("Overall Packet Delivery Ratio (%)")
    ax2.set_title("(b) End-to-End PDR under Loss", pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(cipher_labels, fontweight="bold")
    ax2.set_ylim(0, 78)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # ---------------- Panel (c): Mean Critical Alarm Latency (s) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        lat_means = [s2[c][m]["mean_alarm_lat_ms"]["mean"] / 1000.0 for c in ciphers]
        lat_stds  = [s2[c][m]["mean_alarm_lat_ms"]["std"] / 1000.0 for c in ciphers]
        rects = ax3.bar(x + (idx - 1)*width, lat_means, width, yerr=lat_stds, capsize=4.5,
                        label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        for r, val, std in zip(rects, lat_means, lat_stds):
            y_pos = val + std + 0.8
            ax3.text(r.get_x() + r.get_width()/2.0, y_pos, f"{val:.1f}s",
                     ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax3.set_ylabel("Mean Critical Alarm Latency (s)")
    ax3.set_title("(c) Critical Alarm Responsiveness under Loss", pad=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(cipher_labels, fontweight="bold")
    ax3.set_ylim(0, 34)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    # ---------------- Panel (d): Peak Consecutive Outage Duration (s) ----------------
    for idx, (m, lbl, col) in enumerate(zip(modes, labels, colors)):
        gap_means = [s2[c][m]["max_consecutive_missing_s"]["mean"] for c in ciphers]
        gap_stds  = [s2[c][m]["max_consecutive_missing_s"]["std"] for c in ciphers]
        rects = ax4.bar(x + (idx - 1)*width, gap_means, width, yerr=gap_stds, capsize=4.5,
                        label=lbl, color=col, alpha=0.88, edgecolor="black", linewidth=1.1)
        
        for r, val, std in zip(rects, gap_means, gap_stds):
            y_pos = val + std + 3.5
            ax4.text(r.get_x() + r.get_width()/2.0, y_pos, f"{val:.0f}s",
                     ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    # Outage gap reduction inside the Plan B bars to eliminate any collision with error caps
    for i, c in enumerate(ciphers):
        gap_k4 = s2[c]["static_k4"]["max_consecutive_missing_s"]["mean"]
        gap_pb = s2[c]["dyn_b"]["max_consecutive_missing_s"]["mean"]
        gap_red = ((gap_k4 - gap_pb) / gap_k4) * 100.0
        ax4.text(x[i] + width, gap_pb / 2.0, f"-{gap_red:.0f}%\nGap",
                 ha="center", va="center", fontsize=8.8, fontweight="bold", color="white")

    ax4.set_ylabel("Peak Consecutive Outage Duration (s)")
    ax4.set_title("(d) Bounding Loss Burst Outages", pad=10)
    ax4.set_xticks(x)
    ax4.set_xticklabels(cipher_labels, fontweight="bold")
    ax4.set_ylim(0, 148)
    ax4.grid(axis="y", linestyle="--", alpha=0.5)

    # ---------------- SINGLE SHARED HORIZONTAL LEGEND ----------------
    shared_handles = [
        matplotlib.patches.Patch(facecolor=C_STATIC_K4, edgecolor="black", label="Static $k=4$ Baseline"),
        matplotlib.patches.Patch(facecolor=C_VOI_ONLY,  edgecolor="black", label="VoI-Only (No ETX Cap)"),
        matplotlib.patches.Patch(facecolor=C_PLAN_B,    edgecolor="black", label="Plan B (Dynamic Dual-Threshold)"),
    ]
    fig.legend(handles=shared_handles, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 0.985), framealpha=0.95, fontsize=11.5)

    plt.subplots_adjust(top=0.92, bottom=0.07, left=0.08, right=0.97, hspace=0.32, wspace=0.24)

    for dest in [PLOTS_DIR, ARTIFACT_PLOTS_DIR, PLAN_B_WORKING_PLOTS]:
        plt.savefig(dest / "fig6_lossy_channel_resilience.png")
    plt.close()
    print("Generated Publication Figure 6 successfully.")

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
