"""Statistical analysis of multi-arm experiment results.

Computes per-mode descriptive stats, pairwise comparisons vs B1 baseline,
95% bootstrap CIs, and a plain-text summary table.  Runs inside the pinned
Docker container (via run_analysis.py) where numpy is available, or on any
host that has numpy installed.

Usage (direct, if numpy available):
    python3 host/analysis.py --phase 4
    python3 host/analysis.py --phase 4 --phase 5 --output results/analysis.json

Output:
    JSON file with per-mode stats + pairwise table
    Plain-text summary printed to stdout
"""
from comparison_guard import admit_group
import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

WORKSPACE   = Path(__file__).resolve().parents[1]
ARM_ORDER   = ['N0-single', 'N0-batch', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'P1']
MIN_CLIENTS = 8
N_BOOT      = 4000
CI          = 0.95
RNG_SEED    = 42

METRICS = [
    ('reading_pdr',                    'Reading PDR',                 None,    1.0),
    ('p95_delay_ms',                   'p95 delay (ms)',              None,    1.0),
    ('energy_per_delivered_reading_nj','Energy/reading (nJ)',         None,    1.0),
    ('packets_submitted',              'UDP packets submitted',       None,    1.0),
    ('application_packet_bytes',       'App packet bytes',            None,    1.0),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_runs(phases, min_clients=MIN_CLIENTS):
    runs = []
    for phase in phases:
        pattern = str(WORKSPACE / f"results/phase_0{phase}/*/summary.json")
        for f in sorted(glob.glob(pattern)):
            try:
                s = json.loads(Path(f).read_text())
                m = json.loads(Path(f).with_name('manifest.json').read_text())
                status  = s.get('status') or m.get('status', 'unknown')
                clients = m.get('clients', 0)
                sec     = s.get('security', '')
                mode    = m.get('mode') or s.get('mode')
                seed    = m.get('seed') or m.get('config', {}).get('seed')
                if (status == 'passed' and clients >= min_clients
                        and 'security test' not in sec and mode):
                    cfg = m.get('config',{})
                    if cfg.get('purpose') != 'functional' or cfg.get('lifetime'): continue
                    if cfg.get('phase') == 5 and not cfg.get('policy_repair_version'): continue
                    sources = {k:v for k,v in m.get('source_hashes',{}).items() if k != 'firmware/generated-conf.h'}
                    cohort = json.dumps({'sources':sources, 'clients':clients,
                        'config':{k:cfg.get(k) for k in ('target','backend','warmup_ms','period_ms','readings_per_sensor','deadline_ms','drain_ms','payload_budget','power_model','energy_sample_ms','aes_backend')}},sort_keys=True)
                    pair_key = (seed,cohort)
                    if any(r['mode']==mode and r['pair_key']==pair_key for r in runs):
                        raise ValueError('Duplicate analysis cell; curate attempts explicitly')
                    runs.append({
                        'pair_key': pair_key,
                        'phase':   phase,
                        'mode':    mode,
                        'seed':    seed,
                        'clients': clients,
                        'dir':     str(Path(f).parent),
                        'summary': s,
                    })
            except (OSError, json.JSONDecodeError):
                continue
    return runs


def _group_by_mode(runs):
    groups = {}
    for r in runs:
        groups.setdefault(r['mode'], []).append(r)
    return {m: groups[m] for m in ARM_ORDER if m in groups}


# ---------------------------------------------------------------------------
# Bootstrap statistics
# ---------------------------------------------------------------------------

def _bootstrap_ci(arr, n_boot=N_BOOT, ci=CI, seed=RNG_SEED):
    arr = np.array(arr, dtype=float)
    if len(arr) == 0:
        return dict(n=0, mean=None, median=None, std=None, ci_lo=None, ci_hi=None,
                    min=None, max=None)
    rng   = np.random.default_rng(seed)
    boots = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    alpha = (1 - ci) / 2
    return dict(
        n      = int(len(arr)),
        mean   = float(arr.mean()),
        median = float(np.median(arr)),
        std    = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        ci_lo  = float(np.percentile(boots, 100 * alpha)),
        ci_hi  = float(np.percentile(boots, 100 * (1 - alpha))),
        min    = float(arr.min()),
        max    = float(arr.max()),
    )


def _paired_diff(vals_a, vals_b):
    """Mean difference (b - a) with bootstrap CI.  Uses unpaired bootstrap
    when sample sizes differ (common with partial pilots)."""
    a = np.array(vals_a, dtype=float)
    b = np.array(vals_b, dtype=float)
    if len(a) == 0 or len(b) == 0:
        return dict(mean_diff=None, ci_lo=None, ci_hi=None,
                    pct_change=None, note='insufficient_data')
    if len(a) != len(b):
        raise ValueError("Paired statistics require matched seed/scenario observations")
    rng = np.random.default_rng(RNG_SEED)
    n = len(a)
    differences = b - a
    boot_diffs = rng.choice(differences, size=(N_BOOT,n), replace=True).mean(axis=1)
    alpha = (1 - CI) / 2
    mean_diff = float(b.mean() - a.mean())
    pct       = 100 * mean_diff / a.mean() if a.mean() != 0 else None
    note = ('pilot_estimate_unpaired' if len(a) != len(b)
            else 'pilot_estimate_paired' if min(len(a), len(b)) < 5
            else 'adequate')
    return dict(
        mean_diff  = mean_diff,
        ci_lo      = float(np.percentile(boot_diffs, 100 * alpha)),
        ci_hi      = float(np.percentile(boot_diffs, 100 * (1 - alpha))),
        pct_change = round(pct, 2) if pct is not None else None,
        note       = note,
    )


# ---------------------------------------------------------------------------
# Policy summary
# ---------------------------------------------------------------------------

def _policy_stats(runs_for_mode):
    ticks_all, switches_all, profiles_all, caps_all = [], [], [], []
    for r in runs_for_mode:
        p = r['summary'].get('policy')
        if not p:
            continue
        ticks_all.append(p.get('total_policy_ticks', 0))
        switches_all.append(p.get('total_switches', 0))
        for prof in p.get('profiles_used', []):
            profiles_all.append(prof)
        for cap in p.get('caps_used', []):
            caps_all.append(cap)
    if not ticks_all:
        return None
    return {
        'mean_ticks':    float(np.mean(ticks_all)),
        'mean_switches': float(np.mean(switches_all)),
        'profiles_seen': sorted(set(profiles_all)),
        'caps_seen':     sorted(set(caps_all)),
        'runs_with_policy': len(ticks_all),
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_analysis(phases, min_clients=MIN_CLIENTS, output_path=None):
    runs   = _load_runs(phases, min_clients)
    lineage = admit_group([r["dir"] for r in runs])
    groups = _group_by_mode(runs)

    if not groups:
        print("[analysis] No qualifying runs found.", file=sys.stderr)
        return {}

    # Per-mode stats
    per_mode = {}
    for mode, mode_runs in groups.items():
        entry = {'n_runs': len(mode_runs), 'seeds': sorted({r['seed'] for r in mode_runs})}
        for key, label, _, _ in METRICS:
            vals = [r['summary'][key] for r in mode_runs if r['summary'].get(key) is not None]
            entry[key] = _bootstrap_ci(vals)
        entry['policy'] = _policy_stats(mode_runs)
        per_mode[mode] = entry

    # Pairwise vs B1 baseline
    baseline = 'B1'
    pairwise = {}
    if baseline in groups:
        for mode in groups:
            if mode == baseline:
                continue
            pw = {}
            for key, _, _, _ in METRICS:
                left = {r['pair_key']: r for r in groups[baseline]}
                right = {r['pair_key']: r for r in groups[mode]}
                pairs = sorted(left.keys() & right.keys())
                pairs = [p for p in pairs if left[p]['summary'].get(key) is not None and right[p]['summary'].get(key) is not None]
                base_vals = [left[p]['summary'][key] for p in pairs]
                cmp_vals = [right[p]['summary'][key] for p in pairs]
                pw[key] = _paired_diff(base_vals, cmp_vals)
                pw[key]['matched_pairs'] = len(pairs)
                pw[key]['missing_left'] = len(right.keys()-left.keys())
                pw[key]['missing_right'] = len(left.keys()-right.keys())
            pairwise[mode] = pw

    result = {
        'phases':       phases,
        'source_hashes': lineage,
        'min_clients':  min_clients,
        'total_runs':   len(runs),
        'modes':        list(groups.keys()),
        'baseline':     baseline,
        'bootstrap_ci': f'{int(CI*100)}% percentile, n_boot={N_BOOT}, seed={RNG_SEED}',
        'per_mode':     per_mode,
        'pairwise_vs_baseline': pairwise,
    }

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(result, indent=2) + '\n')
        print(f"[analysis] Saved → {output_path}", file=sys.stderr)

    _print_table(result)
    return result


# ---------------------------------------------------------------------------
# Plain-text summary table
# ---------------------------------------------------------------------------

def _fmt(val, decimals=2):
    if val is None:
        return '   —   '
    if isinstance(val, float):
        return f"{val:.{decimals}f}"
    return str(val)


def _print_table(result):
    modes    = result['modes']
    per_mode = result['per_mode']
    pairwise = result.get('pairwise_vs_baseline', {})
    baseline = result.get('baseline', 'B1')

    sep = '─' * 110
    print(f"\n{'='*110}")
    print(f"  ANALYSIS SUMMARY   phases={result['phases']}   "
          f"runs={result['total_runs']}   baseline={baseline}")
    print(f"  Bootstrap {result['bootstrap_ci']}")
    print(f"{'='*110}\n")

    # Energy table
    print("  ENERGY PER DELIVERED READING (nJ)")
    print(sep)
    print(f"  {'Mode':<8}  {'n':>4}  {'Mean':>14}  {'Median':>14}  "
          f"{'95% CI':>22}  {'vs B1 Δ%':>10}  {'Note'}")
    print(sep)
    for m in modes:
        s = per_mode[m].get('energy_per_delivered_reading_nj', {})
        if s.get('n', 0) == 0:
            print(f"  {m:<8}  {'—':>4}  {'no energy data':>50}")
            continue
        ci_str = f"[{_fmt(s['ci_lo'],0)} – {_fmt(s['ci_hi'],0)}]"
        pw     = pairwise.get(m, {}).get('energy_per_delivered_reading_nj', {})
        pct    = f"{pw.get('pct_change',0):+.1f}%" if pw.get('pct_change') is not None else '  —  '
        note   = pw.get('note', '')
        print(f"  {m:<8}  {s['n']:>4}  {_fmt(s['mean'],0):>14}  "
              f"{_fmt(s['median'],0):>14}  {ci_str:>22}  {pct:>10}  {note}")
    print(sep)

    # PDR table
    print("\n  READING PDR")
    print(sep)
    print(f"  {'Mode':<8}  {'n':>4}  {'Mean':>8}  {'95% CI':>22}  {'vs B1 Δ':>12}")
    print(sep)
    for m in modes:
        s  = per_mode[m].get('reading_pdr', {})
        pw = pairwise.get(m, {}).get('reading_pdr', {})
        ci_str = (f"[{_fmt(s['ci_lo'],4)} – {_fmt(s['ci_hi'],4)}]"
                  if s.get('n', 0) > 0 else '—')
        d_str  = (f"{pw['mean_diff']:+.4f}" if pw.get('mean_diff') is not None else '—')
        print(f"  {m:<8}  {s.get('n',0):>4}  {_fmt(s.get('mean'),4):>8}  "
              f"{ci_str:>22}  {d_str:>12}")
    print(sep)

    # p95 delay
    print("\n  p95 READING DELAY (ms)")
    print(sep)
    print(f"  {'Mode':<8}  {'n':>4}  {'Mean':>10}  {'95% CI':>22}  {'vs B1 Δ ms':>12}")
    print(sep)
    for m in modes:
        s  = per_mode[m].get('p95_delay_ms', {})
        pw = pairwise.get(m, {}).get('p95_delay_ms', {})
        ci_str = (f"[{_fmt(s['ci_lo'],1)} – {_fmt(s['ci_hi'],1)}]"
                  if s.get('n', 0) > 0 else '—')
        d_str  = (f"{pw['mean_diff']:+.1f}" if pw.get('mean_diff') is not None else '—')
        print(f"  {m:<8}  {s.get('n',0):>4}  {_fmt(s.get('mean'),1):>10}  "
              f"{ci_str:>22}  {d_str:>12}")
    print(sep)

    # Policy runs
    policy_modes = [m for m in modes if per_mode[m].get('policy')]
    if policy_modes:
        print("\n  POLICY RUNS (B3 / B6 / P1)")
        print(sep)
        print(f"  {'Mode':<8}  {'runs':>6}  {'mean ticks':>12}  "
              f"{'mean switches':>15}  {'profiles seen':>15}  {'caps seen'}")
        print(sep)
        for m in policy_modes:
            p = per_mode[m]['policy']
            print(f"  {m:<8}  {p['runs_with_policy']:>6}  "
                  f"{p['mean_ticks']:>12.0f}  {p['mean_switches']:>15.1f}  "
                  f"{str(p['profiles_seen']):>15}  {p['caps_seen']}")
        print(sep)

    print(f"\n  NOTE: Results labelled 'pilot_estimate_*' have <5 paired runs.")
    print(f"  Do not make statistical inferences until ≥5 seeds per arm.\n")


def main():
    parser = argparse.ArgumentParser(description='Statistical analysis of experiment results.')
    parser.add_argument('--phase', type=int, action='append', dest='phases',
                        default=[], choices=[2, 3, 4, 5],
                        help='Phase(s) to include (repeatable: --phase 4 --phase 5)')
    parser.add_argument('--output', type=str, default=None,
                        help='Optional JSON output path')
    parser.add_argument('--min-clients', type=int, default=MIN_CLIENTS,
                        help=f'Min clients filter (default {MIN_CLIENTS})')
    args = parser.parse_args()
    phases = args.phases if args.phases else [4]
    run_analysis(phases, min_clients=args.min_clients, output_path=args.output)


if __name__ == '__main__':
    main()
