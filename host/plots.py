"""Plot validated comparison summaries; final metrics belong to metrics.py.

Supports 2, 4, and 7-arm group comparisons (B1/B2/B3/B4/B5/B6/P1).
Bootstrap 95% CI computed with numpy only — no scipy dependency.
Run via Docker wrapper (host/run_plots.py) when matplotlib unavailable on host.
"""
from comparison_guard import admit_group
import argparse
import json
import math
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


# Canonical display order and colours for all 7 research arms
ARM_ORDER  = ['N0-single', 'N0-batch', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'P1']
ARM_COLOUR = {
    'N0-single': '#aaaaaa', 'N0-batch': '#888888',
    'B1': '#1f77b4', 'B2': '#ff7f0e',
    'B3': '#9467bd',
    'B4': '#2ca02c', 'B5': '#d62728',
    'B6': '#8c564b', 'P1': '#e377c2',
}
VALID_GROUPS = {
    frozenset(['B1', 'B4']),
    frozenset(['N0-single', 'N0-batch']),
    frozenset(['B1', 'B2', 'B4', 'B5']),
    frozenset(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'P1']),
    # any subset accepted in multi-seed mode (validated below)
}


def _bootstrap_ci(values, n_boot=2000, ci=0.95, rng_seed=42):
    """Return (mean, lo, hi) using percentile bootstrap."""
    if not values:
        return None, None, None
    arr = np.array(values, dtype=float)
    if len(arr) == 1:
        return float(arr[0]), float(arr[0]), float(arr[0])
    rng = np.random.default_rng(rng_seed)
    boots = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    lo = float(np.percentile(boots, 100 * (1 - ci) / 2))
    hi = float(np.percentile(boots, 100 * (1 - (1 - ci) / 2)))
    return float(arr.mean()), lo, hi


def _load_run(run_dir: Path):
    """Load and validate a single run directory."""
    manifest = json.loads((run_dir / 'manifest.json').read_text())
    summary  = json.loads((run_dir / 'summary.json').read_text())
    mode   = manifest.get('mode') or summary.get('mode')
    status = manifest.get('status') or summary.get('status', 'unknown')
    if status != 'passed':
        raise ValueError(f"{run_dir.name}: status={status!r}, only passed runs allowed")
    if summary.get('security', '').endswith('security test'):
        raise ValueError(f"{run_dir.name}: security-test run excluded from comparison plots")
    cfg = manifest.get('config', {})
    if cfg.get('purpose') != 'functional' or cfg.get('lifetime'):
        raise ValueError('Only clean functional runs belong in these comparison plots')
    if cfg.get('phase') == 5 and not cfg.get('policy_repair_version'):
        raise ValueError('Historical uninitialized-policy run is not qualified')
    seed    = manifest.get('seed') or manifest.get('config', {}).get('seed')
    clients = manifest.get('clients', 0)
    return {
        'dir':     run_dir,
        'mode':    mode,
        'seed':    seed,
        'clients': clients,
        'summary': summary,
    }


def _group_by_mode(runs):
    """Return {mode: [run, ...]} preserving ARM_ORDER."""
    groups = {}
    for r in runs:
        groups.setdefault(r['mode'], []).append(r)
    return {m: groups[m] for m in ARM_ORDER if m in groups}


def _metric_values(runs_for_mode, key):
    return [r['summary'][key] for r in runs_for_mode if r['summary'].get(key) is not None]


def _plot_metric_group(ax, groups, key, ylabel, ylim=None, unit_scale=1.0,
                       show_ci=True, baseline_mode=None):
    """Bar chart with bootstrap CI error bars for one metric across all modes."""
    modes  = list(groups.keys())
    means, los, his, colours = [], [], [], []
    for m in modes:
        vals = [v * unit_scale for v in _metric_values(groups[m], key)]
        mn, lo, hi = _bootstrap_ci(vals)
        means.append(mn); los.append(lo); his.append(hi)
        colours.append(ARM_COLOUR.get(m, '#333333'))

    x = np.arange(len(modes))
    bars = ax.bar(x, [m if m is not None else 0 for m in means],
                  color=colours, width=0.6, zorder=3)

    if show_ci:
        for i, (mn, lo, hi) in enumerate(zip(means, los, his)):
            if None not in (mn, lo, hi) and hi > lo:
                ax.errorbar(i, mn, yerr=[[mn - lo], [hi - mn]],
                            fmt='none', color='black', capsize=4, linewidth=1.2)

    # Baseline dashed line
    if baseline_mode and baseline_mode in modes:
        idx = modes.index(baseline_mode)
        bv = means[idx]
        if bv is not None:
            ax.axhline(bv, color=colours[idx], linestyle='--',
                       linewidth=0.9, alpha=0.6, zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)
    if ylim:
        ax.set_ylim(*ylim)
    ax.yaxis.grid(True, linewidth=0.5, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Annotate n= per bar
    for i, m in enumerate(modes):
        n = len(_metric_values(groups[m], key))
        ax.text(i, 0, f'n={n}', ha='center', va='bottom',
                fontsize=6, color='#555555', transform=ax.get_xaxis_transform())


def _policy_summary_plot(ax, groups):
    """Stacked bar of profiles_used count for policy-aware modes."""
    policy_modes = [m for m in groups if any(
        r['summary'].get('policy') for r in groups[m])]
    if not policy_modes:
        ax.set_visible(False)
        return
    aes_counts, ascon_counts = [], []
    for m in policy_modes:
        a1 = sum(1 for r in groups[m]
                 if r['summary'].get('policy') and
                 1 in r['summary']['policy'].get('profiles_used', []))
        a2 = sum(1 for r in groups[m]
                 if r['summary'].get('policy') and
                 2 in r['summary']['policy'].get('profiles_used', []))
        aes_counts.append(a1); ascon_counts.append(a2)
    x = np.arange(len(policy_modes))
    ax.bar(x, aes_counts,  label='AES used',   color='#1f77b4', width=0.5)
    ax.bar(x, ascon_counts, bottom=aes_counts, label='Ascon used', color='#ff7f0e', width=0.5)
    ax.set_xticks(x); ax.set_xticklabels(policy_modes, fontsize=8)
    ax.set_ylabel('Runs using profile', fontsize=8)
    ax.set_title('Cipher profiles used (policy runs)', fontsize=9)
    ax.legend(fontsize=7)


def plot_comparison(run_dirs, output: Path, title_suffix=''):
    """Main entry point: load runs, produce multi-panel comparison figure."""
    lineage = admit_group(run_dirs)
    runs = [_load_run(Path(d)) for d in run_dirs]
    groups = _group_by_mode(runs)
    if not groups:
        raise ValueError("No valid runs to plot")

    n_arms = len(groups)
    has_energy  = any(_metric_values(groups[m], 'energy_per_delivered_reading_nj') for m in groups)
    has_policy  = any(any(r['summary'].get('policy') for r in groups[m]) for m in groups)

    # Build subplot layout
    metric_panels = ['reading_pdr', 'p95_delay_ms', 'packets_submitted']
    metric_labels = ['Unique reading PDR', 'p95 delay (ms)', 'UDP packets submitted']
    metric_ylims  = [(0, 1.05), None, None]
    if has_energy:
        metric_panels.append('energy_per_delivered_reading_nj')
        metric_labels.append('Energy / delivered reading (nJ)')
        metric_ylims.append(None)

    n_cols = len(metric_panels) + (1 if has_policy else 0)
    fig, axes = plt.subplots(1, n_cols, figsize=(4.2 * n_cols, 4.2))
    if n_cols == 1:
        axes = [axes]

    baseline = 'B1' if 'B1' in groups else None

    for ax, key, ylabel, ylim in zip(axes, metric_panels, metric_labels, metric_ylims):
        _plot_metric_group(ax, groups, key, ylabel,
                           ylim=ylim, baseline_mode=baseline)
        ax.set_title(ylabel, fontsize=9)

    if has_policy:
        _policy_summary_plot(axes[-1], groups)

    seeds  = sorted({r['seed'] for r in runs if r['seed']})
    n_runs = sum(len(v) for v in groups.values())
    suptitle = (f"Research pilot — {n_arms} arms, {n_runs} runs"
                f"{', seeds ' + '/'.join(str(s) for s in seeds) if seeds else ''}"
                f"{' — ' + title_suffix if title_suffix else ''}")
    fig.suptitle(suptitle, fontsize=10)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)

    # Save sources manifest alongside the figure
    sources = {
        'figure': str(output),
        'source_hashes': lineage,
        'arms': n_arms,
        'runs': n_runs,
        'seeds': seeds,
        'modes': list(groups.keys()),
        'run_dirs': [str(r['dir']) for r in runs],
        'metrics': metric_panels,
        'bootstrap_ci': '95% percentile, 2000 resamples, seed=42',
        'baseline': baseline,
    }
    output.with_suffix('.sources.json').write_text(
        json.dumps(sources, indent=2) + '\n')
    print(f"Saved: {output}  ({n_arms} arms, {n_runs} runs)", file=sys.stderr)
    return sources


def main():
    parser = argparse.ArgumentParser(
        description='Plot multi-arm comparison from run directories.')
    parser.add_argument('runs', nargs='+', type=Path,
                        help='Run directories (each must have manifest.json + summary.json)')
    parser.add_argument('--output', required=True, type=Path,
                        help='Output PNG path')
    parser.add_argument('--title', default='',
                        help='Optional title suffix')
    args = parser.parse_args()
    plot_comparison(args.runs, args.output, title_suffix=args.title)


if __name__ == '__main__':
    main()
