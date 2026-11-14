"""AdaptiveAlpha IoT — experiment dashboard.

Serves a live web UI at http://localhost:5000 showing all experiment results,
per-mode statistics, comparison charts and run-level detail.

Run via Docker wrapper (always):
    python3 host/run_dashboard.py

Or directly if Flask + matplotlib + numpy are installed:
    cd <project_root>
    python3 host/dashboard.py
"""
import glob
import hashlib
import io
import json
import math
import os
import statistics
import subprocess
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

try:
    from flask import Flask, jsonify, render_template_string, request, send_file, abort
except ImportError:
    sys.exit("Flask not found. Run via: python3 host/run_dashboard.py")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

PROJECT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT / "results"
app = Flask(__name__)

# ── ARM metadata ────────────────────────────────────────────────────────────
ARM_ORDER  = ["N0-single", "N0-batch", "B1", "B2", "B3", "B4", "B5", "B6", "P1"]
ARM_COLOR  = {
    "N0-single": "#aaaaaa", "N0-batch": "#888888",
    "B1": "#1f77b4", "B2": "#ff7f0e", "B3": "#9467bd",
    "B4": "#2ca02c", "B5": "#d62728", "B6": "#8c564b", "P1": "#e377c2",
}
ARM_DESC = {
    "N0-single": "No AEAD, 1 reading/packet",
    "N0-batch":  "No AEAD, batched",
    "B1": "AES-CCM, cap=1 (baseline)",
    "B2": "Ascon-128, cap=1",
    "B3": "Battery-threshold: AES↔Ascon",
    "B4": "AES-CCM, cap=4",
    "B5": "Ascon-128, cap=4",
    "B6": "Fixed Ascon + adaptive batching",
    "P1": "Joint cost-aware policy",
}

# ── Data loading ─────────────────────────────────────────────────────────────
_cache = {"runs": [], "ts": 0.0}
_lock  = threading.Lock()

def _load_runs(force=False):
    with _lock:
        if not force and time.time() - _cache["ts"] < 10:
            return _cache["runs"]
        runs = []
        for f in sorted(glob.glob(str(RESULTS / "phase_0*/*/summary.json"))):
            try:
                s = json.loads(Path(f).read_text())
                m = json.loads(Path(f).with_name("manifest.json").read_text())
                status  = s.get("status") or m.get("status", "?")
                mode    = m.get("mode", "?")
                clients = m.get("clients", 0)
                seed    = m.get("config", {}).get("seed")
                target  = m.get("platform", "cooja")
                sec     = "security test" in s.get("security", "")
                phase_s = Path(f).parts[-3]          # e.g. "phase_04"
                phase   = int(phase_s.split("_")[1])
                runs.append({
                    "run_id":  Path(f).parent.name,
                    "phase":   phase,
                    "mode":    mode,
                    "status":  status,
                    "clients": clients,
                    "seed":    seed,
                    "target":  target,
                    "sec":     sec,
                    "energy":  s.get("energy_per_delivered_reading_nj"),
                    "pdr":     s.get("reading_pdr"),
                    "p95":     s.get("p95_delay_ms"),
                    "packets": s.get("packets_submitted"),
                    "app_bytes": s.get("application_packet_bytes"),
                    "policy":  s.get("policy"),
                    "radio":   s.get("radio", {}),
                    "security_label": s.get("security", ""),
                    "path":    str(Path(f).parent),
                })
            except Exception:
                pass
        _cache["runs"] = runs
        _cache["ts"]   = time.time()
        return runs

# ── Bootstrap CI (numpy) ──────────────────────────────────────────────────────
def _ci(vals, n_boot=2000, seed=42):
    if not vals:
        return None, None, None
    arr = np.array(vals, dtype=float)
    if len(arr) == 1:
        v = float(arr[0])
        return v, v, v
    rng   = np.random.default_rng(seed)
    boots = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    return float(arr.mean()), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))

def _stats(runs, key):
    vals = [r[key] for r in runs if r.get(key) is not None]
    if not vals:
        return {"n": 0, "mean": None, "ci_lo": None, "ci_hi": None, "min": None, "max": None}
    mn, lo, hi = _ci(vals)
    return {"n": len(vals), "mean": mn, "ci_lo": lo, "ci_hi": hi,
            "min": min(vals), "max": max(vals)}

# ── API endpoints ─────────────────────────────────────────────────────────────

@app.route("/api/runs")
def api_runs():
    phase  = request.args.get("phase", type=int)
    mode   = request.args.get("mode")
    status = request.args.get("status", "passed")
    runs   = _load_runs()
    if phase:
        runs = [r for r in runs if r["phase"] == phase]
    if mode:
        runs = [r for r in runs if r["mode"] == mode]
    if status != "all":
        runs = [r for r in runs if r["status"] == status]
    return jsonify(runs)


@app.route("/api/summary")
def api_summary():
    runs      = _load_runs()
    passed    = [r for r in runs if r["status"] == "passed"]
    pilot     = [r for r in passed if r["clients"] == 8 and not r["sec"]]
    by_mode   = defaultdict(list)
    for r in pilot:
        by_mode[r["mode"]].append(r)

    result = {}
    for mode in ARM_ORDER:
        if mode not in by_mode:
            continue
        mrs = by_mode[mode]
        result[mode] = {
            "n_runs":      len(mrs),
            "description": ARM_DESC.get(mode, ""),
            "color":       ARM_COLOR.get(mode, "#333"),
            "energy":      _stats(mrs, "energy"),
            "pdr":         _stats(mrs, "pdr"),
            "p95":         _stats(mrs, "p95"),
            "policy_runs": sum(1 for r in mrs if r["policy"]),
            "mean_switches": (
                statistics.mean(r["policy"]["total_switches"] for r in mrs if r["policy"])
                if any(r["policy"] for r in mrs) else None
            ),
        }
    return jsonify(result)


@app.route("/api/phases")
def api_phases():
    runs = _load_runs()
    phases = {}
    for r in runs:
        ph = r["phase"]
        if ph not in phases:
            phases[ph] = {"total": 0, "passed": 0, "modes": set(), "targets": set()}
        phases[ph]["total"] += 1
        if r["status"] == "passed":
            phases[ph]["passed"] += 1
        phases[ph]["modes"].add(r["mode"])
        phases[ph]["targets"].add(r["target"])
    # sets not JSON serialisable
    return jsonify({k: {**v, "modes": sorted(v["modes"]), "targets": sorted(v["targets"])}
                    for k, v in sorted(phases.items())})


@app.route("/api/run/<run_id>")
def api_run_detail(run_id):
    for phase_dir in RESULTS.glob("phase_0*"):
        run_path = phase_dir / run_id
        if run_path.exists():
            detail = {}
            for fname in ("summary.json", "manifest.json"):
                fp = run_path / fname
                if fp.exists():
                    detail[fname.replace(".json", "")] = json.loads(fp.read_text())
            events_path = run_path / "events.jsonl"
            if events_path.exists():
                lines = events_path.read_text().splitlines()
                detail["event_count"] = len(lines)
                # last 10 events
                detail["recent_events"] = [json.loads(l) for l in lines[-10:]]
            return jsonify(detail)
    abort(404)


@app.route("/api/chart/energy")
def api_chart_energy():
    if not HAS_PLOT:
        abort(503, "matplotlib not available")
    runs   = _load_runs()
    pilot  = [r for r in runs if r["status"] == "passed"
              and r["clients"] == 8 and not r["sec"]]
    by_mode = defaultdict(list)
    for r in pilot:
        by_mode[r["mode"]].append(r)

    modes  = [m for m in ARM_ORDER if m in by_mode]
    means, lo_errs, hi_errs, colors = [], [], [], []
    for m in modes:
        vals = [r["energy"] for r in by_mode[m] if r["energy"]]
        if vals:
            mn, lo, hi = _ci(vals)
            means.append(mn / 1e6)        # nJ → mJ
            lo_errs.append((mn - lo) / 1e6)
            hi_errs.append((hi - mn) / 1e6)
        else:
            means.append(0); lo_errs.append(0); hi_errs.append(0)
        colors.append(ARM_COLOR.get(m, "#333"))

    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(modes))
    bars = ax.bar(x, means, color=colors, width=0.6, zorder=3)
    ax.errorbar(x, means, yerr=[lo_errs, hi_errs],
                fmt="none", color="black", capsize=5, linewidth=1.5, zorder=4)
    # B1 baseline dashed line
    if "B1" in modes:
        b1_val = means[modes.index("B1")]
        ax.axhline(b1_val, color=ARM_COLOR["B1"], linestyle="--",
                   linewidth=1.0, alpha=0.6, label="B1 baseline")
        ax.legend(fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(modes, fontsize=10)
    ax.set_ylabel("Energy per delivered reading (mJ)", fontsize=10)
    ax.set_title("Network energy per unique authenticated delivered reading\n"
                 "(8-client Z1 pilot, 95% bootstrap CI)", fontsize=11)
    ax.yaxis.grid(True, linewidth=0.5, alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    for i, (m, v) in enumerate(zip(modes, means)):
        n = len([r for r in by_mode[m] if r["energy"]])
        ax.text(i, 0.01, f"n={n}", ha="center", va="bottom",
                fontsize=7, color="#555", transform=ax.get_xaxis_transform())
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=130); buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype="image/png")


@app.route("/api/chart/pdr")
def api_chart_pdr():
    if not HAS_PLOT:
        abort(503)
    runs   = _load_runs()
    pilot  = [r for r in runs if r["status"] == "passed"
              and r["clients"] == 8 and not r["sec"]]
    by_mode = defaultdict(list)
    for r in pilot:
        by_mode[r["mode"]].append(r)

    modes = [m for m in ARM_ORDER if m in by_mode]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    for ax, key, ylabel, ylim, scale in [
        (axes[0], "pdr",  "Reading PDR",          (0.90, 1.01), 1),
        (axes[1], "p95",  "p95 delay (ms)",        None,         1),
    ]:
        means, lo_errs, hi_errs, colors = [], [], [], []
        for m in modes:
            vals = [r[key] for r in by_mode[m] if r.get(key) is not None]
            if vals:
                mn, lo, hi = _ci(vals)
                means.append(mn * scale)
                lo_errs.append((mn - lo) * scale)
                hi_errs.append((hi - mn) * scale)
            else:
                means.append(0); lo_errs.append(0); hi_errs.append(0)
            colors.append(ARM_COLOR.get(m, "#333"))
        x = np.arange(len(modes))
        ax.bar(x, means, color=colors, width=0.6, zorder=3)
        ax.errorbar(x, means, yerr=[lo_errs, hi_errs],
                    fmt="none", color="black", capsize=4, linewidth=1.2, zorder=4)
        ax.set_xticks(x); ax.set_xticklabels(modes, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(ylabel, fontsize=10)
        if ylim:
            ax.set_ylim(*ylim)
        ax.yaxis.grid(True, linewidth=0.5, alpha=0.4, zorder=0)
        ax.set_axisbelow(True)

    fig.suptitle("PDR and latency (8-client pilot, 95% bootstrap CI)", fontsize=11)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=130); buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype="image/png")


@app.route("/api/chart/policy")
def api_chart_policy():
    if not HAS_PLOT:
        abort(503)
    runs   = _load_runs()
    policy_runs = [r for r in runs if r["policy"] and r["status"] == "passed"
                   and r["clients"] == 8 and not r["sec"]]
    if not policy_runs:
        abort(404, "No policy runs found")
    by_mode = defaultdict(list)
    for r in policy_runs:
        by_mode[r["mode"]].append(r)
    modes = [m for m in ARM_ORDER if m in by_mode]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Switches per run
    ax = axes[0]
    switch_means = []
    for m in modes:
        sw = [r["policy"]["total_switches"] for r in by_mode[m] if r["policy"]]
        switch_means.append(statistics.mean(sw) if sw else 0)
    x = np.arange(len(modes))
    ax.bar(x, switch_means, color=[ARM_COLOR.get(m, "#333") for m in modes], width=0.6)
    ax.set_xticks(x); ax.set_xticklabels(modes, fontsize=9)
    ax.set_ylabel("Mean policy switches per run", fontsize=9)
    ax.set_title("Policy switches", fontsize=10)
    ax.yaxis.grid(True, linewidth=0.5, alpha=0.4)
    ax.set_axisbelow(True)

    # Profiles used
    ax = axes[1]
    aes_counts   = [sum(1 for r in by_mode[m] if r["policy"] and 1 in r["policy"].get("profiles_used", [])) for m in modes]
    ascon_counts = [sum(1 for r in by_mode[m] if r["policy"] and 2 in r["policy"].get("profiles_used", [])) for m in modes]
    x = np.arange(len(modes))
    ax.bar(x, aes_counts,   label="AES used",   color="#1f77b4", width=0.5)
    ax.bar(x, ascon_counts, label="Ascon used", color="#ff7f0e", width=0.5,
           bottom=aes_counts)
    ax.set_xticks(x); ax.set_xticklabels(modes, fontsize=9)
    ax.set_ylabel("Run count", fontsize=9)
    ax.set_title("Cipher profiles used", fontsize=10)
    ax.legend(fontsize=8)
    ax.yaxis.grid(True, linewidth=0.5, alpha=0.4)
    ax.set_axisbelow(True)

    fig.suptitle("Policy behaviour (8-client pilot)", fontsize=11)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=130); buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype="image/png")


@app.route("/api/refresh")
def api_refresh():
    _load_runs(force=True)
    return jsonify({"status": "ok", "runs": len(_cache["runs"]),
                    "ts": _cache["ts"]})

# ── HTML UI ───────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AdaptiveAlpha IoT — Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
header{background:#1a1d2e;border-bottom:1px solid #2d3748;padding:14px 24px;display:flex;align-items:center;gap:16px}
header h1{font-size:1.2rem;font-weight:600;color:#e2e8f0}
header span{font-size:.8rem;color:#718096;background:#2d3748;padding:3px 10px;border-radius:12px}
.refresh-btn{margin-left:auto;background:#3182ce;color:#fff;border:none;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:.85rem}
.refresh-btn:hover{background:#2b6cb0}
.container{max-width:1400px;margin:0 auto;padding:20px 24px}
.section{margin-bottom:32px}
.section-title{font-size:.9rem;font-weight:600;color:#a0aec0;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;border-bottom:1px solid #2d3748;padding-bottom:6px}
/* Phase cards */
.phase-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.phase-card{background:#1a1d2e;border:1px solid #2d3748;border-radius:8px;padding:14px}
.phase-card h3{font-size:1rem;color:#63b3ed;margin-bottom:8px}
.phase-card .stat{font-size:.8rem;color:#a0aec0;margin:2px 0}
.phase-card .stat span{color:#e2e8f0;font-weight:500}
/* Mode table */
.mode-table{width:100%;border-collapse:collapse;font-size:.82rem}
.mode-table th{text-align:left;padding:8px 12px;background:#1a1d2e;color:#a0aec0;border-bottom:2px solid #2d3748;white-space:nowrap}
.mode-table td{padding:7px 12px;border-bottom:1px solid #2d3748;vertical-align:middle}
.mode-table tr:hover td{background:#1e2235}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.75rem;font-weight:600}
.bar-cell{display:flex;align-items:center;gap:8px}
.bar-bg{flex:1;background:#2d3748;border-radius:4px;height:8px;min-width:80px}
.bar-fill{height:8px;border-radius:4px;transition:width .4s}
.ci{font-size:.72rem;color:#718096}
/* Charts */
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chart-card{background:#1a1d2e;border:1px solid #2d3748;border-radius:8px;overflow:hidden}
.chart-card .chart-title{padding:10px 14px;font-size:.85rem;color:#a0aec0;border-bottom:1px solid #2d3748}
.chart-card img{width:100%;display:block}
.chart-loading{padding:40px;text-align:center;color:#4a5568;font-size:.85rem}
/* Runs table */
.runs-table{width:100%;border-collapse:collapse;font-size:.8rem}
.runs-table th{padding:7px 10px;background:#1a1d2e;color:#a0aec0;border-bottom:2px solid #2d3748;text-align:left;white-space:nowrap}
.runs-table td{padding:6px 10px;border-bottom:1px solid #1e2235;font-family:monospace}
.runs-table tr:hover td{background:#1e2235;cursor:pointer}
.tag{display:inline-block;padding:1px 6px;border-radius:4px;font-size:.72rem}
.tag-pass{background:#1a3a2a;color:#48bb78}
.tag-fail{background:#3a1a1a;color:#fc8181}
.tag-sec{background:#2a2a1a;color:#f6e05e}
/* Run detail modal */
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:100;overflow-y:auto}
.modal-bg.open{display:flex;align-items:flex-start;justify-content:center;padding:40px 20px}
.modal{background:#1a1d2e;border:1px solid #2d3748;border-radius:10px;max-width:860px;width:100%;padding:24px;position:relative}
.modal-close{position:absolute;top:14px;right:16px;background:none;border:none;color:#a0aec0;font-size:1.3rem;cursor:pointer}
.modal h2{color:#63b3ed;margin-bottom:16px;font-size:1rem}
.kv-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;font-size:.8rem;margin-bottom:16px}
.kv-grid .k{color:#718096} .kv-grid .v{color:#e2e8f0;font-family:monospace}
.events-box{background:#0f1117;border:1px solid #2d3748;border-radius:6px;padding:10px;font-family:monospace;font-size:.72rem;color:#a0aec0;max-height:220px;overflow-y:auto;white-space:pre-wrap}
/* Toast */
.toast{position:fixed;bottom:20px;right:20px;background:#2d3748;color:#e2e8f0;padding:10px 18px;border-radius:8px;font-size:.85rem;opacity:0;transition:opacity .3s;z-index:200}
.toast.show{opacity:1}
@media(max-width:900px){.chart-grid{grid-template-columns:1fr}.kv-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>🔬 AdaptiveAlpha IoT Dashboard</h1>
  <span id="run-count">loading…</span>
  <span id="last-refresh"></span>
  <button class="refresh-btn" onclick="refreshAll()">↻ Refresh</button>
</header>

<div class="container">
  <!-- Phase overview -->
  <div class="section">
    <div class="section-title">Phase Overview</div>
    <div class="phase-grid" id="phase-grid">
      <div style="color:#4a5568;font-size:.85rem">Loading…</div>
    </div>
  </div>

  <!-- Mode comparison table -->
  <div class="section">
    <div class="section-title">Mode Comparison — 8-client pilot (passed, non-security)</div>
    <div style="overflow-x:auto">
      <table class="mode-table" id="mode-table">
        <thead>
          <tr>
            <th>Mode</th><th>Description</th><th>Runs</th>
            <th>Energy / reading</th><th>PDR</th><th>p95 delay (ms)</th><th>Policy switches</th>
          </tr>
        </thead>
        <tbody id="mode-tbody">
          <tr><td colspan="7" style="color:#4a5568;padding:20px">Loading…</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Charts -->
  <div class="section">
    <div class="section-title">Charts (live from results)</div>
    <div class="chart-grid">
      <div class="chart-card">
        <div class="chart-title">Energy per delivered reading (nJ) — 95% bootstrap CI</div>
        <img id="chart-energy" src="/api/chart/energy" alt="energy chart"
             onerror="this.parentElement.innerHTML='<div class=chart-loading>Chart unavailable</div>'">
      </div>
      <div class="chart-card">
        <div class="chart-title">PDR and p95 delay</div>
        <img id="chart-pdr" src="/api/chart/pdr" alt="pdr chart"
             onerror="this.parentElement.innerHTML='<div class=chart-loading>Chart unavailable</div>'">
      </div>
      <div class="chart-card">
        <div class="chart-title">Policy behaviour (B3 / B6 / P1)</div>
        <img id="chart-policy" src="/api/chart/policy" alt="policy chart"
             onerror="this.parentElement.innerHTML='<div class=chart-loading>No policy runs yet</div>'">
      </div>
    </div>
  </div>

  <!-- All runs table -->
  <div class="section">
    <div class="section-title">
      All Runs
      <span style="font-weight:400;font-size:.8rem;margin-left:12px">
        Filter:
        <select id="filter-phase" onchange="renderRuns()" style="background:#2d3748;color:#e2e8f0;border:1px solid #4a5568;padding:2px 6px;border-radius:4px;font-size:.8rem">
          <option value="">All phases</option>
          <option value="2">Phase 2</option><option value="3">Phase 3</option>
          <option value="4">Phase 4</option><option value="5">Phase 5</option>
        </select>
        <select id="filter-mode" onchange="renderRuns()" style="background:#2d3748;color:#e2e8f0;border:1px solid #4a5568;padding:2px 6px;border-radius:4px;font-size:.8rem;margin-left:6px">
          <option value="">All modes</option>
        </select>
      </span>
    </div>
    <div style="overflow-x:auto;max-height:420px;overflow-y:auto">
      <table class="runs-table">
        <thead style="position:sticky;top:0">
          <tr>
            <th>Run ID</th><th>Phase</th><th>Mode</th><th>Target</th>
            <th>Clients</th><th>Seed</th><th>Status</th>
            <th>Energy (nJ)</th><th>PDR</th><th>p95 (ms)</th><th>Type</th>
          </tr>
        </thead>
        <tbody id="runs-tbody">
          <tr><td colspan="11" style="color:#4a5568;padding:20px">Loading…</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- Run detail modal -->
<div class="modal-bg" id="modal-bg" onclick="if(event.target===this)closeModal()">
  <div class="modal" id="modal">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <h2 id="modal-title">Run detail</h2>
    <div class="kv-grid" id="modal-kv"></div>
    <div class="section-title" style="margin-top:12px">Recent events (last 10)</div>
    <div class="events-box" id="modal-events"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let allRuns = [];

function fmt(v, dec=2) {
  if (v == null) return '—';
  if (typeof v === 'number') return v.toFixed(dec);
  return v;
}
function fmtEnergy(v) {
  if (v == null) return '—';
  return (v/1e6).toFixed(1) + ' mJ';
}
function fmtEnergyNJ(v) {
  if (v == null) return '—';
  return Math.round(v).toLocaleString() + ' nJ';
}

async function fetchPhases() {
  const res = await fetch('/api/phases');
  const data = await res.json();
  const grid = document.getElementById('phase-grid');
  grid.innerHTML = '';
  for (const [ph, d] of Object.entries(data).sort()) {
    const pct = d.total ? Math.round(d.passed/d.total*100) : 0;
    grid.innerHTML += `
      <div class="phase-card">
        <h3>Phase ${ph}</h3>
        <div class="stat">Total: <span>${d.total}</span></div>
        <div class="stat">Passed: <span>${d.passed} (${pct}%)</span></div>
        <div class="stat">Modes: <span>${d.modes.join(', ')}</span></div>
        <div class="stat">Targets: <span>${d.targets.join(', ')}</span></div>
      </div>`;
  }
}

async function fetchSummary() {
  const res = await fetch('/api/summary');
  const data = await res.json();
  const tbody = document.getElementById('mode-tbody');

  // Find max energy for bar scaling
  const maxE = Math.max(...Object.values(data).map(d => d.energy.mean || 0));
  const b1E  = data['B1'] ? data['B1'].energy.mean : null;

  tbody.innerHTML = '';
  const ARM_ORDER = ['N0-single','N0-batch','B1','B2','B3','B4','B5','B6','P1'];
  for (const m of ARM_ORDER) {
    if (!data[m]) continue;
    const d = data[m];
    const e = d.energy;
    const pdr = d.pdr;
    const p95 = d.p95;
    const pct = e.mean && maxE ? (e.mean/maxE*100).toFixed(0) : 0;
    const vsB1 = (b1E && e.mean) ? ((e.mean - b1E)/b1E*100).toFixed(1) : null;
    const vsB1html = vsB1 != null
      ? `<span style="color:${parseFloat(vsB1)>0?'#fc8181':'#48bb78'};font-size:.75rem"> ${parseFloat(vsB1)>0?'+':''}${vsB1}%</span>`
      : '';
    tbody.innerHTML += `
      <tr>
        <td><span class="badge" style="background:${d.color}22;color:${d.color}">${m}</span></td>
        <td style="color:#a0aec0">${d.description}</td>
        <td>${d.n_runs}</td>
        <td>
          <div class="bar-cell">
            <div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${d.color}"></div></div>
            <span>${fmtEnergy(e.mean)}</span>${vsB1html}
          </div>
          <div class="ci">${e.ci_lo!=null ? `[${fmtEnergy(e.ci_lo)} – ${fmtEnergy(e.ci_hi)}]` : ''}</div>
        </td>
        <td>${fmt(pdr.mean,4)} <div class="ci">${pdr.ci_lo!=null?`[${fmt(pdr.ci_lo,4)} – ${fmt(pdr.ci_hi,4)}]`:''}</div></td>
        <td>${fmt(p95.mean,1)} ms <div class="ci">${p95.ci_lo!=null?`[${fmt(p95.ci_lo,1)} – ${fmt(p95.ci_hi,1)}]`:''}</div></td>
        <td>${d.mean_switches != null ? d.mean_switches.toFixed(1) : '—'}</td>
      </tr>`;
  }
}

async function fetchRuns() {
  const res = await fetch('/api/runs?status=all');
  allRuns = await res.json();
  document.getElementById('run-count').textContent = `${allRuns.length} runs`;

  // Populate mode filter
  const modeSelect = document.getElementById('filter-mode');
  const modes = [...new Set(allRuns.map(r => r.mode))].sort();
  modeSelect.innerHTML = '<option value="">All modes</option>' +
    modes.map(m => `<option value="${m}">${m}</option>`).join('');

  renderRuns();
}

function renderRuns() {
  const phase = document.getElementById('filter-phase').value;
  const mode  = document.getElementById('filter-mode').value;
  let runs = allRuns;
  if (phase) runs = runs.filter(r => r.phase == phase);
  if (mode)  runs = runs.filter(r => r.mode === mode);

  const tbody = document.getElementById('runs-tbody');
  if (!runs.length) { tbody.innerHTML = '<tr><td colspan="11" style="color:#4a5568;padding:16px">No runs match filter</td></tr>'; return; }

  const ARM_COLOR = {"N0-single":"#aaa","N0-batch":"#888","B1":"#1f77b4","B2":"#ff7f0e","B3":"#9467bd","B4":"#2ca02c","B5":"#d62728","B6":"#8c564b","P1":"#e377c2"};
  tbody.innerHTML = runs.slice().reverse().map(r => {
    const statusTag = r.status === 'passed'
      ? `<span class="tag tag-pass">passed</span>`
      : `<span class="tag tag-fail">${r.status}</span>`;
    const typeTag = r.sec ? `<span class="tag tag-sec">security</span>` : '';
    const c = ARM_COLOR[r.mode] || '#888';
    return `<tr onclick="openRun('${r.run_id}')">
      <td style="color:#a0aec0;font-size:.75rem">${r.run_id}</td>
      <td>${r.phase}</td>
      <td><span style="color:${c};font-weight:600">${r.mode}</span></td>
      <td>${r.target}</td>
      <td>${r.clients}</td>
      <td>${r.seed ?? '—'}</td>
      <td>${statusTag}</td>
      <td>${r.energy ? Math.round(r.energy).toLocaleString() : '—'}</td>
      <td>${r.pdr != null ? r.pdr.toFixed(4) : '—'}</td>
      <td>${r.p95 != null ? r.p95.toFixed(1) : '—'}</td>
      <td>${typeTag}</td>
    </tr>`;
  }).join('');
}

async function openRun(run_id) {
  const res = await fetch(`/api/run/${run_id}`);
  if (!res.ok) { showToast('Run detail not found'); return; }
  const data = await res.json();
  document.getElementById('modal-title').textContent = run_id;
  const s = data.summary || {};
  const m = data.manifest || {};
  const cfg = m.config || {};
  const kv = [
    ['Phase', m.phase || cfg.phase || '—'],
    ['Mode', m.mode || '—'],
    ['Target', m.platform || '—'],
    ['Clients', m.clients || '—'],
    ['Seed', cfg.seed ?? '—'],
    ['Status', m.status || '—'],
    ['Security', s.security || '—'],
    ['PDR', s.reading_pdr != null ? s.reading_pdr.toFixed(4) : '—'],
    ['p95 delay', s.p95_delay_ms != null ? s.p95_delay_ms.toFixed(1)+' ms' : '—'],
    ['Energy/reading', s.energy_per_delivered_reading_nj != null ? Math.round(s.energy_per_delivered_reading_nj).toLocaleString()+' nJ' : '—'],
    ['Generated', s.generated ?? '—'],
    ['Delivered', s.unique_authenticated_delivered ?? s.unique_delivered ?? '—'],
    ['Injections', s.security_test_injections ?? '—'],
    ['Rejections', s.security_test_rejections ?? '—'],
    ['Events', data.event_count ?? '—'],
    ['Warmup', cfg.warmup_ms ? cfg.warmup_ms/1000+'s' : '—'],
  ];
  document.getElementById('modal-kv').innerHTML =
    kv.map(([k,v]) => `<div class="k">${k}</div><div class="v">${v}</div>`).join('');
  const ev = data.recent_events || [];
  document.getElementById('modal-events').textContent =
    ev.map(e => JSON.stringify(e)).join('\n') || '(no events)';
  document.getElementById('modal-bg').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-bg').classList.remove('open');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function reloadCharts() {
  const ts = Date.now();
  ['chart-energy','chart-pdr','chart-policy'].forEach(id => {
    const img = document.getElementById(id);
    if (img) {
      const base = img.src.split('?')[0];
      img.src = base + '?t=' + ts;
    }
  });
}

async function refreshAll() {
  await fetch('/api/refresh');
  document.getElementById('last-refresh').textContent =
    'Refreshed ' + new Date().toLocaleTimeString();
  showToast('Data refreshed');
  await Promise.all([fetchPhases(), fetchSummary(), fetchRuns()]);
  reloadCharts();
}

document.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('last-refresh').textContent =
    'Loaded ' + new Date().toLocaleTimeString();
  await Promise.all([fetchPhases(), fetchSummary(), fetchRuns()]);
});

// Auto-refresh every 30s
setInterval(refreshAll, 30000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", 5000))
    host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    print(f"[dashboard] Starting on http://{host}:{port}", flush=True)
    print(f"[dashboard] Open http://localhost:{port} in your browser", flush=True)
    app.run(host=host, port=port, debug=False, threaded=True)
