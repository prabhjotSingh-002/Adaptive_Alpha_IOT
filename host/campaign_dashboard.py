"""Comprehensive campaign dashboard UI.

Historical raw evidence stays separately accessible via /historical.
Fresh campaign comparison data is served from /api/campaign (uses report()).
"""
import hashlib
import json
from pathlib import Path

from flask import abort, jsonify, render_template_string, request

from campaign import ROOT, report, campaign_rows
from evidence import verify_artifacts, policy_qualification

# ── ARM metadata (kept in sync with dashboard.py constants) ─────────────────
ARM_ORDER = ["N0-single", "N0-batch", "B1", "B2", "B3", "B4", "B5", "B6", "P1"]
ARM_COLOR = {
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
    "B6": "Recorded fixed profile + adaptive batching",
    "P1": "Joint cost-aware policy",
}

RESULTS = ROOT / "results"


def _sha256_file(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _current_campaign_dir():
    """Return the Path of the current campaign directory, or None."""
    pointer = ROOT / "results/campaigns/current.json"
    if not pointer.exists():
        return None
    try:
        rel = json.loads(pointer.read_text())["directory"]
        d = (ROOT / rel).resolve()
        d.relative_to(ROOT / "results/campaigns")  # containment check
        return d
    except (KeyError, ValueError, OSError):
        return None


def _load_historical(campaign_dir):
    """Return list of dicts for every historical directory."""
    hist_file = campaign_dir / "historical.json"
    dirs = set(json.loads(hist_file.read_text()).get("directories", [])) if hist_file.exists() else set()
    # The frozen campaign inventory is historical, not a filter on newer evidence.
    for phase in RESULTS.glob('phase_*'):
        if not phase.is_dir(): continue
        for candidate in [phase, *phase.iterdir()]:
            if candidate.is_dir() and any((candidate/name).exists() for name in ('manifest.json','summary.json','COOJA.testlog')):
                dirs.add(str(candidate.relative_to(ROOT)))
    dirs = sorted(dirs)
    records = []
    for rel in dirs:
        run_path = (ROOT / rel).resolve()
        try:
            run_path.relative_to(RESULTS.resolve())
        except ValueError:
            continue
        # Derive run_id from final path component
        run_id = run_path.name
        # Phase from second path component (e.g. results/phase_02/...)
        parts = Path(rel).parts
        phase_str = ""
        for part in parts:
            if part.startswith("phase_"):
                try:
                    phase_str = "Phase " + str(int(part.split("_")[1]))
                except (IndexError, ValueError):
                    phase_str = part
                break

        manifest = None
        summary = None
        has_events = (run_path / "events.jsonl").exists()

        if (run_path / "manifest.json").exists():
            try:
                manifest = json.loads((run_path / "manifest.json").read_text())
            except (OSError, json.JSONDecodeError):
                manifest = {}

        if (run_path / "summary.json").exists():
            try:
                summary = json.loads((run_path / "summary.json").read_text())
            except (OSError, json.JSONDecodeError):
                summary = {}

        mode = "—"
        status = "—"
        target = "—"
        seed = None
        pdr = None
        purpose = "—"
        provenance = "unverified"

        if manifest:
            mode = manifest.get("mode") or "—"
            status = manifest.get("status") or "—"
            target = manifest.get("platform") or manifest.get("config", {}).get("target") or "—"
            if isinstance(manifest.get("config"), dict):
                seed = manifest["config"].get("seed")
                purpose = manifest["config"].get("purpose") or "—"
        else:
            provenance = "unverified"

        if summary:
            pdr = summary.get("reading_pdr")

        records.append({
            "run_id": run_id,
            "directory": rel,
            "phase": phase_str,
            "mode": mode,
            "status": status,
            "target": target,
            "seed": seed,
            "pdr": pdr,
            "purpose": purpose,
            "has_manifest": manifest is not None,
            "has_summary": summary is not None,
            "has_events": has_events,
            "provenance": provenance,
        })
    return records


def register_campaign(app):

    # ── Existing routes (kept working) ──────────────────────────────────────

    @app.route("/api/campaign-runs")
    def api_campaign_runs():
        directory = _current_campaign_dir()
        if directory is None:
            return jsonify(runs=[])
        try:
            _, _, rows = campaign_rows(directory)
            runs = []
            for row in rows:
                m, summary = row['manifest'], row['summary']
                config = m.get('config', {})
                runs.append(dict(run_id=m['run_id'], group=row['group'],
                    mode=row['mode'], seed=row['seed'],
                    directory=str(Path(row['directory']).relative_to(ROOT)),
                    target=config.get('target'), status=m.get('status'),
                    pdr=summary.get('reading_pdr'), p95=summary.get('p95_delay_ms'),
                    energy=summary.get('energy_per_delivered_reading_nj'),
                    switches=(summary.get('policy') or {}).get('total_switches'),
                    qualification=policy_qualification(m, summary),
                    calibration=config.get('policy_calibration_status', 'unverified')))
            return jsonify(runs=runs)
        except (ValueError, OSError, KeyError) as exc:
            return jsonify(runs=[], error=str(exc)), 409

    @app.route("/api/campaign")
    def api_campaign():
        pointer = ROOT / "results/campaigns/current.json"
        if not pointer.exists():
            return jsonify({
                "status": "not_started",
                "groups": {},
                "limitations": ["No fresh campaign selected."],
            })
        try:
            directory = (ROOT / json.loads(pointer.read_text())["directory"]).resolve()
            directory.relative_to(ROOT / "results/campaigns")
            result = report(directory)
            result["historical_inventory"] = str(directory / "historical.json")
            return jsonify(result)
        except (ValueError, OSError, KeyError) as exc:
            return jsonify({
                "status": "evidence_error",
                "groups": {},
                "limitations": [str(exc)],
            }), 409

    @app.route("/campaign")
    def campaign_index():
        # Inject ARM metadata as JSON for the template
        arm_colors_json = json.dumps(ARM_COLOR)
        arm_desc_json = json.dumps(ARM_DESC)
        arm_order_json = json.dumps(ARM_ORDER)
        return render_template_string(
            INDEX_HTML,
            arm_colors=arm_colors_json,
            arm_descs=arm_desc_json,
            arm_order=arm_order_json,
        )

    # ── New routes ───────────────────────────────────────────────────────────

    @app.route("/historical")
    def historical_index():
        return render_template_string(HISTORICAL_HTML)

    @app.route("/api/historical")
    def api_historical():
        campaign_dir = _current_campaign_dir()
        if campaign_dir is None:
            return jsonify({"error": "No current campaign", "records": []}), 404
        records = _load_historical(campaign_dir)
        return jsonify({"records": records, "total": len(records)})

    @app.route("/api/run/<path:run_id>")
    def api_run(run_id):
        # Reject path traversal characters early
        if ".." in run_id or run_id.startswith("/"):
            abort(400)

        # Locate the run directory; it must live under ROOT/results
        candidate = (RESULTS / run_id).resolve()
        try:
            candidate.relative_to(RESULTS)
        except ValueError:
            abort(403)

        if not candidate.is_dir():
            abort(404)

        result = {"run_id": run_id, "directory": str(candidate)}

        # Manifest
        manifest_path = candidate / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                result["manifest"] = manifest
                result["manifest_sha256"] = _sha256_file(manifest_path)
            except (OSError, json.JSONDecodeError) as exc:
                result["manifest_error"] = str(exc)
        else:
            result["manifest"] = None

        # Summary
        summary_path = candidate / "summary.json"
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text())
                result["summary"] = summary
                result["summary_sha256"] = _sha256_file(summary_path)
            except (OSError, json.JSONDecodeError) as exc:
                result["summary_error"] = str(exc)
        else:
            result["summary"] = None

        # Events (first 20 + last 20)
        events_path = candidate / "events.jsonl"
        if events_path.exists():
            try:
                raw_lines = events_path.read_text().splitlines()
                total = len(raw_lines)
                first20 = []
                last20 = []
                for line in raw_lines[:20]:
                    line = line.strip()
                    if line:
                        try:
                            first20.append(json.loads(line))
                        except json.JSONDecodeError:
                            first20.append({"raw": line})
                if total > 20:
                    for line in raw_lines[max(20, total - 20):]:
                        line = line.strip()
                        if line:
                            try:
                                last20.append(json.loads(line))
                            except json.JSONDecodeError:
                                last20.append({"raw": line})
                result["events"] = {
                    "total_lines": total,
                    "first_20": first20,
                    "last_20": last20,
                }
            except OSError as exc:
                result["events_error"] = str(exc)
        else:
            result["events"] = None

        # Artifact hash verification against manifest-listed hashes
        if result.get("manifest"):
            artifact_hashes = result["manifest"].get("artifact_hashes", {})
            verification = verify_artifacts(candidate, result["manifest"])
            result["artifact_verification"] = verification
            result["artifact_verification_summary"] = {
                "total": len(verification),
                "ok": sum(1 for v in verification.values() if v == "OK"),
                "missing": sum(1 for v in verification.values() if v == "MISSING"),
                "mismatch": sum(1 for v in verification.values() if v not in ("OK", "MISSING")),
            }

        # Log path hint (not served, just the path string)
        log_path = candidate / "console.log"
        result["log_path"] = str(log_path) if log_path.exists() else None

        return jsonify(result)


# ════════════════════════════════════════════════════════════════════════════
# Main campaign index page
# ════════════════════════════════════════════════════════════════════════════

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AdaptiveAlpha IoT · Research Results</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0f1117;
  --surface: #1a1d2e;
  --border: #2d3748;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --passed: #4ade80;
  --failed: #f87171;
  --interrupted: #fb923c;
  --warn-bg: #2d2510;
  --warn-border: #d97706;
  --info-bg: #0f1f33;
  --info-border: #0ea5e9;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); font-size: 15px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
*:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* ── Layout ── */
header { background: var(--surface); border-bottom: 1px solid var(--border); }
.hinner { max-width: 1400px; margin: auto; padding: 14px 24px; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
h1 { font-size: 20px; margin: 0; white-space: nowrap; }
h1 span { color: var(--muted); font-weight: 400; }
.spacer { flex: 1; }
.hinner a { font-size: 14px; white-space: nowrap; }
#last-updated { font-size: 13px; color: var(--muted); white-space: nowrap; }
button.btn { font: inherit; color: var(--text); background: #253449; border: 1px solid #64748b; border-radius: 6px; padding: 7px 14px; cursor: pointer; }
button.btn:hover { background: #2e3f5a; }

main { max-width: 1400px; margin: auto; padding: 24px; }

/* Readable overview on desktop and mobile. */
header { position: sticky; top: 0; z-index: 10; box-shadow: 0 4px 24px #0003; }
.card { box-shadow: 0 8px 24px #0002; border-top: 3px solid var(--accent); }
.card-value { font-variant-numeric: tabular-nums; }
tbody tr:nth-child(even) { background: #ffffff03; }
.table-wrap { max-height: 65vh; }
@media(max-width: 640px) { main { padding: 14px; } .hinner { padding: 14px; } .card { min-width: 130px; } }
/* ── Cards ── */
.cards { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; flex: 1; min-width: 160px; }
.card-label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 6px; }
.card-value { font-size: 28px; font-weight: 650; line-height: 1; }

/* ── Notices ── */
.notice { border-left: 3px solid var(--warn-border); background: var(--warn-bg); padding: 12px 16px; border-radius: 0 6px 6px 0; margin-bottom: 20px; font-size: 14px; line-height: 1.6; }
.notice li { margin: 2px 0; }
.info { border-left: 3px solid var(--info-border); background: var(--info-bg); }
.error-banner { border-left: 3px solid var(--failed); background: #2d1010; color: var(--failed); padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 16px; font-size: 14px; display: none; }

/* ── Section ── */
h2 { font-size: 16px; margin: 28px 0 12px; color: var(--text); }
.section-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
select { font: inherit; color: var(--text); background: #1e293b; border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px; }
label { font-size: 13px; color: var(--muted); display: flex; align-items: center; gap: 6px; }

/* ── Tables ── */
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
thead { position: sticky; top: 0; z-index: 2; }
th { background: #1e2535; color: var(--muted); text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); white-space: nowrap; font-weight: 500; }
td { padding: 9px 12px; border-bottom: 1px solid #1e2535; vertical-align: top; white-space: nowrap; }
tr:last-child td { border-bottom: none; }
tr.clickable { cursor: pointer; }
tr.clickable:hover td { background: #1e2d42; }

/* ── Badges ── */
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.badge-passed { background: #052e16; color: var(--passed); border: 1px solid #15803d; }
.badge-failed { background: #2d0a0a; color: var(--failed); border: 1px solid #991b1b; }
.badge-interrupted { background: #2d1700; color: var(--interrupted); border: 1px solid #c2410c; }
.badge-other { background: #1e293b; color: var(--muted); border: 1px solid var(--border); }
.badge-functional { background: #0c1f38; color: #60a5fa; border: 1px solid #1d4ed8; }
.badge-fallback { background: #2d2510; color: #fbbf24; border: 1px solid #92400e; }
.badge-lifetime { background: #1a0a2e; color: #c084fc; border: 1px solid #7c3aed; }
.mode-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }

/* ── Run detail modal ── */
#detail-backdrop { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.55); z-index: 100; }
#detail-backdrop.open { display: block; }
#detail-panel { position: fixed; top: 0; right: 0; height: 100vh; width: min(640px, 100vw); background: #131726; border-left: 1px solid var(--border); overflow-y: auto; z-index: 101; transform: translateX(100%); transition: transform .22s ease; }
#detail-panel.open { transform: translateX(0); }
.dp-header { display: flex; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); gap: 12px; }
.dp-header h3 { margin: 0; font-size: 15px; flex: 1; word-break: break-all; }
.dp-close { background: none; border: 1px solid var(--border); color: var(--muted); border-radius: 6px; padding: 4px 10px; cursor: pointer; font: inherit; }
.dp-body { padding: 20px; }
.dp-section { margin-bottom: 20px; }
.dp-section h4 { font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin: 0 0 10px; }
.kv-grid { display: grid; grid-template-columns: auto 1fr; gap: 4px 16px; font-size: 13px; }
.kv-key { color: var(--muted); white-space: nowrap; }
.kv-val { word-break: break-all; font-family: ui-monospace, monospace; }
.events-box { background: #0a0d14; border: 1px solid var(--border); border-radius: 6px; padding: 10px; font-family: ui-monospace, monospace; font-size: 11px; overflow-x: auto; max-height: 240px; overflow-y: auto; white-space: pre; color: #a0bcd8; }
.dp-loading { color: var(--muted); font-size: 13px; padding: 20px; text-align: center; }

/* ── Responsive ── */
@media (max-width: 650px) {
  .hinner { gap: 10px; }
  h1 { font-size: 16px; }
  main { padding: 14px; }
  .card-value { font-size: 22px; }
}
</style>

<header>
  <div class="hinner">
    <h1>AdaptiveAlpha IoT <span>· Research Results</span></h1>
    <div class="spacer"></div>
    <span id="last-updated"></span>
    <a href="/historical">Historical archive →</a>
    <button class="btn" id="refresh-btn">Refresh</button>
  </div>
</header>

<main>
  <div id="error-banner" class="error-banner" role="alert"></div>

  <!-- Summary cards -->
  <div class="cards">
    <div class="card">
      <div class="card-label">Campaign</div>
      <div class="card-value" id="card-campaign" style="font-size:17px">—</div>
    </div>
    <div class="card">
      <div class="card-label">Status</div>
      <div class="card-value" id="card-status" style="font-size:17px">—</div>
    </div>
    <div class="card">
      <div class="card-label">Selected / Planned</div>
      <div class="card-value" id="card-count">—</div>
    </div>
    <div class="card">
      <div class="card-label">Attempts total</div>
      <div class="card-value" id="card-attempts">—</div>
    </div>
    <div class="card">
      <div class="card-label">Groups</div>
      <div class="card-value" id="card-groups">—</div>
    </div>
  </div>

  <!-- Limitations notice -->
  <div id="limitations-box" class="notice" style="display:none">
    <strong>Protocol limitations</strong>
    <ul id="limitations-list"></ul>
  </div>

  <!-- Mode comparison -->
  <h2>Mode comparison</h2>
  <div class="section-bar">
    <label>Group <select id="group-select"></select></label>
    <label>Metric
      <select id="metric-select">
        <option value="reading_pdr">Reading delivery ratio (PDR)</option>
        <option value="p95_delay_ms">p95 delivery delay (ms)</option>
        <option value="packets_submitted">Packets submitted</option>
        <option value="application_packet_bytes">Application bytes</option>
        <option value="energy_per_delivered_reading_nj">Modelled energy / delivered reading</option>
      </select>
    </label>
  </div>
  <p id="group-desc" style="color:var(--muted);font-size:13px;margin:0 0 10px"></p>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Mode</th>
          <th>Description</th>
          <th>Runs</th>
          <th>PDR mean [95% CI]</th>
          <th>p95 delay ms [CI]</th>
          <th>Energy / reading</th>
          <th>Switches</th>
          <th>Profiles</th>
          <th>Caps</th>
          <th>Qualification</th>
        </tr>
      </thead>
      <tbody id="mode-rows"></tbody>
    </table>
  </div>
  <p id="stats-note" class="notice info" style="font-size:12px;margin-top:10px;display:none"></p>

  <!-- Selected runs -->
  <h2>Selected runs</h2>
  <div class="section-bar">
    <label>Group <select id="filter-group"><option value="">All</option></select></label>
    <label>Mode <select id="filter-mode"><option value="">All</option></select></label>
    <label>Status <select id="filter-status"><option value="">All</option></select></label>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Group</th>
          <th>Mode</th>
          <th>Seed</th>
          <th>Target</th>
          <th>PDR</th>
          <th>p95 ms</th>
          <th>Energy nJ/reading</th>
          <th>Switches</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody id="runs-rows"></tbody>
    </table>
  </div>
  <p id="runs-count" style="font-size:12px;color:var(--muted);margin-top:8px"></p>

  <button class="btn" id="download-btn" style="margin-top:16px">Download statistics JSON</button>
  <details style="margin-top:20px">
    <summary style="cursor:pointer;font-size:14px;color:var(--muted)">Evidence lineage (current group)</summary>
    <pre id="lineage-pre" style="overflow:auto;font-size:11px;background:#0a0d14;padding:12px;border-radius:6px;border:1px solid var(--border);color:#94a3b8"></pre>
  </details>
</main>

<!-- Run detail panel -->
<div id="detail-backdrop" onclick="closeDetail()"></div>
<div id="detail-panel" role="dialog" aria-modal="true" aria-label="Run detail">
  <div class="dp-header">
    <h3 id="dp-title">Run detail</h3>
    <button class="dp-close" onclick="closeDetail()">✕ Close</button>
  </div>
  <div class="dp-body" id="dp-body">
    <p class="dp-loading">Loading…</p>
  </div>
</div>

<script>
const ARM_COLOR = {{ arm_colors | safe }};
const ARM_DESC  = {{ arm_descs  | safe }};
const ARM_ORDER = {{ arm_order  | safe }};

let _data = { groups: {}, campaign: '', status: '', selected: 0, expected: 0, attempts: 0, limitations: [] };
let _allRuns = [];  // flat list of selected runs with group/mode metadata

function $(id) { return document.getElementById(id); }

/* ── Formatting ── */
function fmt(v, digits=4) {
  if (v == null) return '—';
  return Number(v).toLocaleString(undefined, { maximumFractionDigits: digits });
}
function fmtPdr(v) { return v == null ? '—' : (v * 100).toFixed(2) + '%'; }
function fmtNj(v) { return v == null ? '—' : fmt(v / 1e6, 3) + ' mJ'; }
function ci(s, transform) {
  if (!s || s.mean == null) return '—';
  const m = transform ? transform(s.mean) : fmt(s.mean);
  if (s.ci_lo == null) return m + ' (no CI)';
  const lo = transform ? transform(s.ci_lo) : fmt(s.ci_lo);
  const hi = transform ? transform(s.ci_hi) : fmt(s.ci_hi);
  return m + ' [' + lo + ', ' + hi + ']';
}
function modeBadge(mode) {
  const color = ARM_COLOR[mode] || '#888';
  return `<span class="mode-dot" style="background:${color}"></span>${esc(mode)}`;
}
function statusBadge(st) {
  const cls = st === 'passed' ? 'badge-passed' : st === 'failed' ? 'badge-failed' : st === 'interrupted' ? 'badge-interrupted' : 'badge-other';
  return `<span class="badge ${cls}">${esc(st || '—')}</span>`;
}
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function qualBadge(mode, group) {
  const labels = [...new Set(_allRuns.filter(r => r.group === group && r.mode === mode).map(r => r.qualification))];
  return '<span class="badge badge-functional">' + esc(labels.join(', ') || 'unverified') + '</span>';
}

/* ── Render mode comparison table ── */
function drawModeTable() {
  const gid = $('group-select').value;
  const g = _data.groups[gid];
  const tbody = $('mode-rows');
  tbody.replaceChildren();
  $('lineage-pre').textContent = '';
  if (!g) return;
  $('group-desc').textContent = g.description || '';
  $('lineage-pre').textContent = JSON.stringify(g.lineage, null, 2);

  for (const mode of ARM_ORDER) {
    const m = g.modes[mode];
    if (!m) continue;
    const tr = document.createElement('tr');
    const mk = m.metrics;
    const switches = mk.reading_pdr ? (g.modes[mode].caps || []) : [];
    const totalSwitches = _allRuns
      .filter(r => r.group === gid && r.mode === mode)
      .reduce((acc, r) => acc + (r.switches || 0), 0);

    // Energy: show "—" for cooja groups (not z1)
    const energyStat = mk.energy_per_delivered_reading_nj;
    const groupRuns = _allRuns.filter(r => r.group === gid);
    const isZ1 = groupRuns.length > 0 && groupRuns.every(r => r.target === 'z1');
    const energyCell = isZ1 ? ci(energyStat, v => fmtNj(v)) : '—';

    tr.innerHTML = `
      <td>${modeBadge(mode)}</td>
      <td style="color:var(--muted);max-width:220px;white-space:normal">${esc(ARM_DESC[mode] || '')}</td>
      <td>${esc(m.n)}</td>
      <td style="font-family:ui-monospace,monospace;font-size:12px">${ci(mk.reading_pdr, v => fmtPdr(v))}</td>
      <td style="font-family:ui-monospace,monospace;font-size:12px">${ci(mk.p95_delay_ms)}</td>
      <td style="font-family:ui-monospace,monospace;font-size:12px">${energyCell}</td>
      <td>${esc(totalSwitches)}</td>
      <td>${esc((m.profiles || []).join(', ') || '—')}</td>
      <td>${esc((m.caps || []).join(', ') || '—')}</td>
      <td>${qualBadge(mode, gid)}</td>
    `;
    tbody.append(tr);
  }
  const stats = _data.statistics || '';
  if (stats) { $('stats-note').textContent = stats; $('stats-note').style.display = ''; }
}

/* ── Render runs table ── */
function drawRunsTable() {
  const fg = $('filter-group').value;
  const fm = $('filter-mode').value;
  const fs = $('filter-status').value;
  const tbody = $('runs-rows');
  tbody.replaceChildren();
  let count = 0;
  for (const r of _allRuns) {
    if (fg && r.group !== fg) continue;
    if (fm && r.mode !== fm) continue;
    if (fs && r.status !== fs) continue;
    count++;
    const tr = document.createElement('tr');
    tr.className = 'clickable';
    tr.dataset.runid = r.run_id;
    tr.dataset.dir = r.directory;
    tr.onclick = () => openDetail(r.run_id, r.directory);
    tr.innerHTML = `
      <td style="font-family:ui-monospace,monospace;font-size:11px;max-width:260px;overflow:hidden;text-overflow:ellipsis">${esc(r.run_id)}</td>
      <td>${esc(r.group)}</td>
      <td>${modeBadge(r.mode)}</td>
      <td>${esc(r.seed ?? '—')}</td>
      <td>${esc(r.target || '—')}</td>
      <td>${fmtPdr(r.pdr)}</td>
      <td>${r.p95 != null ? fmt(r.p95, 1) : '—'}</td>
      <td>${r.target === 'z1' && r.energy != null ? fmtNj(r.energy) : '—'}</td>
      <td>${esc(r.switches ?? '—')}</td>
      <td>${statusBadge(r.status)}</td>
    `;
    tbody.append(tr);
  }
  $('runs-count').textContent = `Showing ${count} of ${_allRuns.length} selected runs`;
}

/* ── Populate filter dropdowns ── */
function populateFilters() {
  const groups = Object.keys(_data.groups);
  const modes = new Set(_allRuns.map(r => r.mode));
  const statuses = new Set(_allRuns.map(r => r.status));

  const fg = $('filter-group');
  fg.replaceChildren();
  fg.append(Object.assign(document.createElement('option'), { value: '', textContent: 'All groups' }));
  groups.forEach(g => fg.append(Object.assign(document.createElement('option'), { value: g, textContent: g })));

  const fm = $('filter-mode');
  fm.replaceChildren();
  fm.append(Object.assign(document.createElement('option'), { value: '', textContent: 'All modes' }));
  ARM_ORDER.filter(m => modes.has(m)).forEach(m => fm.append(Object.assign(document.createElement('option'), { value: m, textContent: m })));

  const fst = $('filter-status');
  fst.replaceChildren();
  fst.append(Object.assign(document.createElement('option'), { value: '', textContent: 'All statuses' }));
  [...statuses].sort().forEach(s => fst.append(Object.assign(document.createElement('option'), { value: s, textContent: s })));
}

/* ── Main data refresh ── */
async function refresh() {
  try {
    const resp = await fetch('/api/campaign');
    const data = await resp.json();
    _data = data;

    // Cards
    $('card-campaign').textContent = data.campaign || '—';
    $('card-status').textContent = data.status || '—';
    $('card-count').textContent = (data.selected ?? '—') + ' / ' + (data.expected ?? '—');
    $('card-attempts').textContent = data.attempts ?? '—';
    $('card-groups').textContent = Object.keys(data.groups || {}).length;
    $('last-updated').textContent = 'Updated ' + new Date().toLocaleTimeString();

    // Limitations
    const lims = data.limitations || [];
    if (lims.length) {
      const ul = $('limitations-list');
      ul.replaceChildren();
      lims.forEach(l => {
        const li = document.createElement('li');
        li.textContent = l;
        ul.append(li);
      });
      $('limitations-box').style.display = '';
    }

    // Error state
    const eb = $('error-banner');
    if (!resp.ok) {
      eb.textContent = 'Evidence validation failed — comparison withheld. ' + (lims[0] || '');
      eb.style.display = '';
    } else {
      eb.style.display = 'none';
    }

    // Build flat runs list from groups
    // Exact selected attempts are mandatory; no aggregate-to-run placeholders.
    await _enrichRunList();

    // Group selector
    const gs = $('group-select');
    const prevGroup = gs.value;
    gs.replaceChildren();
    for (const [id, g] of Object.entries(data.groups || {})) {
      gs.append(Object.assign(document.createElement('option'), { value: id, textContent: g.description || id }));
    }
    if (data.groups[prevGroup]) gs.value = prevGroup;

    populateFilters();
    drawModeTable();
    drawRunsTable();
  } catch(e) {
    const eb = $('error-banner');
    eb.textContent = 'Could not load campaign data: ' + e.message;
    eb.style.display = '';
  }
}

/* ── Enrich run list with per-run data from /api/historical or state ── */
async function _enrichRunList() {
  _allRuns = [];
  const response = await fetch('/api/campaign-runs');
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || 'Run evidence unavailable');
  _allRuns = payload.runs;

}

/* ── Run detail panel ── */
async function openDetail(runId, dir) {
  $('dp-title').textContent = runId;
  $('dp-body').innerHTML = '<p class="dp-loading">Loading…</p>';
  $('detail-panel').classList.add('open');
  $('detail-backdrop').classList.add('open');
  document.body.style.overflow = 'hidden';

  // Use the directory path as the identifier for the API
  const apiId = dir ? dir.replace(/^results\//, '') : runId;
  try {
    const resp = await fetch('/api/run/' + encodeURIComponent(apiId));
    if (!resp.ok) {
      $('dp-body').innerHTML = `<p style="color:var(--failed)">Could not load run: HTTP ${resp.status}</p>`;
      return;
    }
    const d = await resp.json();
    renderDetail(d);
  } catch(e) {
    $('dp-body').innerHTML = `<p style="color:var(--failed)">Error: ${esc(e.message)}</p>`;
  }
}

function closeDetail() {
  $('detail-panel').classList.remove('open');
  $('detail-backdrop').classList.remove('open');
  document.body.style.overflow = '';
}

function renderDetail(d) {
  const m = d.manifest || {};
  const s = d.summary || {};
  const cfg = m.config || {};
  const policy = s.policy || {};

  let html = '';

  // Manifest key fields
  html += '<div class="dp-section"><h4>Run identity</h4><div class="kv-grid">';
  html += kv('Run ID', m.run_id || d.run_id);
  html += kv('Mode', m.mode || '—');
  html += kv('Status', m.status || '—');
  html += kv('Target / backend', (m.platform || '—') + ' / ' + (m.backend || '—'));
  html += kv('Seed', cfg.seed ?? '—');
  html += kv('Purpose', cfg.purpose || '—');
  html += kv('Clients', m.clients ?? '—');
  html += kv('Phase', cfg.phase ?? '—');
  html += kv('Source files', Object.keys(m.source_hashes || {}).length || '—');
  html += '</div></div>';

  if (d.manifest_sha256) {
    html += '<div class="dp-section"><h4>Integrity</h4><div class="kv-grid">';
    html += kv('manifest.json SHA-256', d.manifest_sha256);
    html += kv('summary.json SHA-256', d.summary_sha256 || '—');
    html += '</div></div>';
  }

  // Summary metrics
  if (d.summary) {
    html += '<div class="dp-section"><h4>Metrics</h4><div class="kv-grid">';
    html += kv('Reading PDR', s.reading_pdr != null ? (s.reading_pdr*100).toFixed(3)+'%' : '—');
    html += kv('p95 delay', s.p95_delay_ms != null ? s.p95_delay_ms.toFixed(2)+' ms' : '—');
    html += kv('Packets submitted', s.packets_submitted ?? '—');
    html += kv('Application bytes', s.application_packet_bytes ?? '—');
    const eng = s.energy_per_delivered_reading_nj;
    html += kv('Energy / reading', eng != null ? (eng/1e6).toFixed(4)+' mJ (modelled, z1 only)' : '— (not measured on cooja)');
    html += '</div></div>';
  }

  // Policy summary
  if (Object.keys(policy).length) {
    html += '<div class="dp-section"><h4>Policy</h4><div class="kv-grid">';
    html += kv('Profiles used', (policy.profiles_used || []).join(', ') || '—');
    html += kv('Caps used', (policy.caps_used || []).join(', ') || '—');
    html += kv('Total switches', policy.total_switches ?? 0);
    const reasons = policy.switch_reasons || {};
    html += kv('Switch reasons', Object.keys(reasons).length ? JSON.stringify(reasons) : 'none');
    html += kv('Policy ticks', policy.total_policy_ticks ?? '—');
    html += '</div></div>';

  }

  // Events
  if (d.events) {
    const ev = d.events;
    html += `<div class="dp-section"><h4>Events (${ev.total_lines} total — first/last 10)</h4>`;
    const display = [...(ev.first_20 || []).slice(0, 10), ...(ev.last_20 || []).slice(-10)];
    html += `<div class="events-box">${esc(display.map(e => JSON.stringify(e)).join('\n'))}</div></div>`;
  }

  // Log path
  if (d.log_path) {
    html += `<div class="dp-section"><h4>Log file</h4><code style="font-size:12px;color:var(--muted)">${esc(d.log_path)}</code></div>`;
  }

  $('dp-body').innerHTML = html;
}

function kv(k, v) {
  return `<span class="kv-key">${esc(k)}</span><span class="kv-val">${esc(v)}</span>`;
}

/* ── Event listeners ── */
$('group-select').onchange = drawModeTable;
$('filter-group').onchange = drawRunsTable;
$('filter-mode').onchange = drawRunsTable;
$('filter-status').onchange = drawRunsTable;
$('refresh-btn').onclick = refresh;
$('download-btn').onclick = () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(_data, null, 2)], {type: 'application/json'}));
  const a = Object.assign(document.createElement('a'), { href: url, download: 'adaptivealpha-statistics.json' });
  a.click();
  URL.revokeObjectURL(url);
};
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDetail(); });

refresh();
setInterval(refresh, 30000);
</script>
</html>
"""


# ════════════════════════════════════════════════════════════════════════════
# Historical archive page
# ════════════════════════════════════════════════════════════════════════════

HISTORICAL_HTML = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AdaptiveAlpha IoT · Historical Archive</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0f1117;
  --surface: #1a1d2e;
  --border: #2d3748;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #38bdf8;
  --passed: #4ade80;
  --failed: #f87171;
  --interrupted: #fb923c;
  --warn-bg: #2d2510;
  --warn-border: #d97706;
  --info-bg: #0f1f33;
  --info-border: #0ea5e9;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); font-size: 15px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
*:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

header { background: var(--surface); border-bottom: 1px solid var(--border); }
.hinner { max-width: 1400px; margin: auto; padding: 14px 24px; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
h1 { font-size: 20px; margin: 0; white-space: nowrap; }
h1 span { color: var(--muted); font-weight: 400; }
.spacer { flex: 1; }

main { max-width: 1400px; margin: auto; padding: 24px; }

.notice { border-left: 3px solid var(--warn-border); background: var(--warn-bg); padding: 12px 16px; border-radius: 0 6px 6px 0; margin-bottom: 20px; font-size: 14px; line-height: 1.6; }
.info { border-left: 3px solid var(--info-border); background: var(--info-bg); }

h2 { font-size: 16px; margin: 0 0 14px; }

.section-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
select { font: inherit; color: var(--text); background: #1e293b; border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px; }
label { font-size: 13px; color: var(--muted); display: flex; align-items: center; gap: 6px; }

.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
thead { position: sticky; top: 0; z-index: 2; }
th { background: #1e2535; color: var(--muted); text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); white-space: nowrap; font-weight: 500; cursor: pointer; user-select: none; }
th:hover { color: var(--text); }
th .sort-arrow { margin-left: 4px; opacity: .4; }
th.sorted .sort-arrow { opacity: 1; }
td { padding: 9px 12px; border-bottom: 1px solid #1e2535; vertical-align: middle; white-space: nowrap; }
tr:last-child td { border-bottom: none; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.badge-passed { background: #052e16; color: var(--passed); border: 1px solid #15803d; }
.badge-failed { background: #2d0a0a; color: var(--failed); border: 1px solid #991b1b; }
.badge-interrupted { background: #2d1700; color: var(--interrupted); border: 1px solid #c2410c; }
.badge-other { background: #1e293b; color: var(--muted); border: 1px solid var(--border); }
.badge-yes { background: #0c1f38; color: #60a5fa; border: 1px solid #1d4ed8; }
.badge-no { background: #1a1d2e; color: var(--muted); border: 1px solid var(--border); }
.badge-unverified { background: #2d2510; color: #fbbf24; border: 1px solid #92400e; }

.mode-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }
.no-summary { color: var(--muted); font-style: italic; }
.error-msg { color: var(--failed); font-size: 13px; padding: 20px; }

#count-label { font-size: 13px; color: var(--muted); margin-top: 8px; }

@media (max-width: 650px) {
  .hinner { gap: 10px; }
  h1 { font-size: 16px; }
  main { padding: 14px; }
}
</style>

<header>
  <div class="hinner">
    <h1>AdaptiveAlpha IoT <span>· Historical Archive</span></h1>
    <div class="spacer"></div>
    <a href="/">← Fresh results</a>
  </div>
</header>

<main>
  <div class="notice info">
    <strong>Archive records are visible for reference.</strong>
    Eligibility for comparison requires compatible source, config, target, model and purpose.
    Records without manifest provenance are shown as "unverified" and are not hidden.
  </div>

  <h2>All historical run records</h2>

  <div class="section-bar">
    <label>Phase <select id="filter-phase"><option value="">All phases</option></select></label>
    <label>Status <select id="filter-status"><option value="">All statuses</option></select></label>
    <label>Mode <select id="filter-mode"><option value="">All modes</option></select></label>
    <label>Has summary <select id="filter-summary">
      <option value="">Any</option>
      <option value="yes">With summary</option>
      <option value="no">No summary</option>
    </select></label>
  </div>

  <div id="error-msg" class="error-msg" style="display:none"></div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th data-col="run_id">Run ID <span class="sort-arrow">↕</span></th>
          <th data-col="phase">Phase <span class="sort-arrow">↕</span></th>
          <th data-col="mode">Mode <span class="sort-arrow">↕</span></th>
          <th data-col="status">Status <span class="sort-arrow">↕</span></th>
          <th data-col="target">Target <span class="sort-arrow">↕</span></th>
          <th data-col="seed">Seed <span class="sort-arrow">↕</span></th>
          <th data-col="pdr">PDR <span class="sort-arrow">↕</span></th>
          <th data-col="purpose">Purpose <span class="sort-arrow">↕</span></th>
          <th data-col="has_summary">Summary <span class="sort-arrow">↕</span></th>
          <th data-col="has_events">Events <span class="sort-arrow">↕</span></th>
          <th data-col="provenance">Provenance <span class="sort-arrow">↕</span></th>
        </tr>
      </thead>
      <tbody id="hist-rows"></tbody>
    </table>
  </div>
  <p id="count-label">Loading…</p>
</main>

<script>
const ARM_COLOR = {
  "N0-single":"#aaaaaa","N0-batch":"#888888",
  "B1":"#1f77b4","B2":"#ff7f0e","B3":"#9467bd",
  "B4":"#2ca02c","B5":"#d62728","B6":"#8c564b","P1":"#e377c2"
};

let _records = [];
let _sortCol = 'run_id';
let _sortDir = 1;

function $(id) { return document.getElementById(id); }

function statusBadge(st) {
  if (!st || st === '—') return '<span class="no-summary">—</span>';
  const cls = st === 'passed' ? 'badge-passed' : st === 'failed' ? 'badge-failed' : st === 'interrupted' ? 'badge-interrupted' : 'badge-other';
  return `<span class="badge ${cls}">${esc(st)}</span>`;
}
function yesNo(v) {
  return v ? '<span class="badge badge-yes">yes</span>' : '<span class="badge badge-no">no</span>';
}
function modeBadge(mode) {
  if (!mode || mode === '—') return '<span class="no-summary">—</span>';
  const color = ARM_COLOR[mode] || '#888';
  return `<span class="mode-dot" style="background:${color}"></span>${esc(mode)}`;
}
function fmtPdr(v) { return v == null ? '<span class="no-summary">no summary</span>' : (v*100).toFixed(2)+'%'; }

function populateFilters() {
  const phases = new Set(_records.map(r => r.phase).filter(Boolean));
  const statuses = new Set(_records.map(r => r.status).filter(Boolean));
  const modes = new Set(_records.map(r => r.mode).filter(v => v && v !== '—'));

  const fp = $('filter-phase');
  fp.replaceChildren();
  fp.append(Object.assign(document.createElement('option'), { value: '', textContent: 'All phases' }));
  [...phases].sort().forEach(p => fp.append(Object.assign(document.createElement('option'), { value: p, textContent: p })));

  const fs = $('filter-status');
  fs.replaceChildren();
  fs.append(Object.assign(document.createElement('option'), { value: '', textContent: 'All statuses' }));
  [...statuses].sort().forEach(s => fs.append(Object.assign(document.createElement('option'), { value: s, textContent: s })));

  const fm = $('filter-mode');
  fm.replaceChildren();
  fm.append(Object.assign(document.createElement('option'), { value: '', textContent: 'All modes' }));
  [...modes].sort().forEach(m => fm.append(Object.assign(document.createElement('option'), { value: m, textContent: m })));
}

function getFiltered() {
  const fp = $('filter-phase').value;
  const fs = $('filter-status').value;
  const fm = $('filter-mode').value;
  const fsum = $('filter-summary').value;
  return _records.filter(r => {
    if (fp && r.phase !== fp) return false;
    if (fs && r.status !== fs) return false;
    if (fm && r.mode !== fm) return false;
    if (fsum === 'yes' && !r.has_summary) return false;
    if (fsum === 'no' && r.has_summary) return false;
    return true;
  });
}

function sortRecords(list) {
  return [...list].sort((a, b) => {
    let av = a[_sortCol], bv = b[_sortCol];
    if (av == null) av = '';
    if (bv == null) bv = '';
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * _sortDir;
    return String(av).localeCompare(String(bv)) * _sortDir;
  });
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function draw() {
  const filtered = sortRecords(getFiltered());
  const tbody = $('hist-rows');
  tbody.replaceChildren();
  for (const r of filtered) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family:ui-monospace,monospace;font-size:11px;max-width:280px;overflow:hidden;text-overflow:ellipsis" title="${esc(r.run_id)}">${esc(r.run_id)}</td>
      <td>${esc(r.phase || '—')}</td>
      <td>${modeBadge(r.mode)}</td>
      <td>${statusBadge(r.status)}</td>
      <td>${esc(r.target || '—')}</td>
      <td>${esc(r.seed ?? '—')}</td>
      <td>${fmtPdr(r.pdr)}</td>
      <td style="max-width:140px;overflow:hidden;text-overflow:ellipsis;color:var(--muted)" title="${esc(r.purpose || '')}">${esc(r.purpose || '—')}</td>
      <td>${yesNo(r.has_summary)}</td>
      <td>${yesNo(r.has_events)}</td>
      <td>${r.provenance === 'unverified' ? '<span class="badge badge-unverified">unverified</span>' : '<span class="badge badge-other">verified</span>'}</td>
    `;
    tbody.append(tr);
  }
  $('count-label').textContent = `Showing ${filtered.length} of ${_records.length} records`;
}

// Sortable column headers
document.querySelectorAll('th[data-col]').forEach(th => {
  th.onclick = () => {
    const col = th.dataset.col;
    if (_sortCol === col) {
      _sortDir = -_sortDir;
    } else {
      _sortCol = col;
      _sortDir = 1;
    }
    document.querySelectorAll('th[data-col]').forEach(h => h.classList.remove('sorted'));
    th.classList.add('sorted');
    th.querySelector('.sort-arrow').textContent = _sortDir === 1 ? '↑' : '↓';
    draw();
  };
});

$('filter-phase').onchange = draw;
$('filter-status').onchange = draw;
$('filter-mode').onchange = draw;
$('filter-summary').onchange = draw;

async function load() {
  try {
    const resp = await fetch('/api/historical');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    _records = data.records || [];
    populateFilters();
    draw();
  } catch(e) {
    $('error-msg').textContent = 'Could not load historical records: ' + e.message;
    $('error-msg').style.display = '';
    $('count-label').textContent = '';
  }
}

load();
</script>
</html>
"""
