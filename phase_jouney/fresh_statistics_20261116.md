# Fresh implementation statistics and dashboard

Date: 16 November 2026. User requested preserving old statistics separately and producing fresh implementation-based statistics with an updated dashboard. This authorizes the scoped campaign below; it does not manufacture prior human gate approval or close the entire research plan.

## Frozen scope

`results/campaigns/20261116-current/protocol.json` specifies 10 previously unused seeds 523456–523465 and 210 protected-mode cells: seven modes B1/B2/B4/B5/B3/B6/P1 for grid16 native, tree16 native and legacy root+8 Z1 with the component power model. Warmup is 120 s; 24 readings/sensor at 1 Hz, 3 s deadline, 15 s drain, 67-byte payload budget. Each group is analysed separately. N0 diagnostics, other small layouts, lifetime and full master-matrix stress/ablation coverage are outside this scoped campaign.

Native runs establish network metrics only. B3 receives unbounded residual energy in native functional runs and the Z1 functional runs have effectively unlimited budgets; threshold adaptation is not exercised. P1 currently has no qualified loaded cost table and remains a fallback diagnostic. B6 uses configured Ascon, not a newly qualified calibration winner. These are explicit current-implementation limitations, not evidence of adaptive energy gains. Neither ten seeds nor completion of this campaign automatically certifies research adequacy.

## Historical preservation

The historical inventory contains 228 pre-campaign run directories. No raw run moved, deleted or rewritten. Fresh selection names exact attempts and hashes; old data is not admitted to campaign statistics. Failed new attempts remain visible in state and logs. First successful attempt per cell is selected; valid low-PDR outcomes are retained. Duplicate attempts are not additional independent samples.

## Implementation

- `host/run_campaign.py`: serial canonical-runner orchestration, source/protocol freeze, per-attempt logs, resumable selection and failure stop.
- `host/campaign.py`: hash-verified selected runs, shared compatibility guard, run-level descriptive statistics and seed-matched differences against B1. Null energy stays missing, never zero; fewer than two samples produce no confidence interval.
- `host/comparison_guard.py`: topology now participates in compatibility identity.
- `host/campaign_dashboard.py`: fresh campaign/group/metric selectors, means/medians/CIs, paired comparisons, observed policy profiles/caps, progress, limitations, lineage and JSON export.
- `host/dashboard.py`: historical archive route with pooled-comparison UI removed. New dashboard is root route.
- `host/run_dashboard.py`: localhost binding, read-only project mount, persistent local Flask dependencies instead of an unpinned installation at every launch.

## Checks and execution evidence

50 unit tests passed in pinned official container; log `results/campaigns/20261116-current/unit-tests.log`. New tests reject protocol tampering, duplicate cells and mixed topologies. Flask test-client checks returned HTTP 200 for `/`, `/historical`, `/api/campaign`. Running HTTP API was also checked on localhost:5000 after sandbox socket restriction required authorized retry.

Pinned container initially lacked Flask. Installed Flask 3.0.3 with resolved dependencies into `results/dashboard-deps`; exact installed versions recorded in campaign `dashboard-requirements.lock`. No host system package installed. An intermediate dashboard syntax error from quoting was corrected before source freeze and tests.

Campaign command:

```bash
python3 host/run_campaign.py results/campaigns/20261116-current
```

Dashboard command:

```bash
python3 host/run_dashboard.py --port 5000
```

`state.json` is the live execution record; each selected original phase run retains canonical command, source/config/scenario/binary hashes and logs. Campaign has its own source snapshot and protocol SHA-256. The original generated configuration was saved to `pre-run-generated-conf.h` before execution.

## Current acceptance

Implementation/unit/API checks passed. 

Bug fix and fresh campaign execution (`results/campaigns/20261116-fresh`):
- `firmware/sensor/sensor.c` was patched to preserve selected cipher profile under `LAB_POLICY_MODE` during `flush()`, eliminating the `TX profile differs from policy` mismatch.
- Historical runs catalogued: 237 previous run directories strictly preserved and isolated in `historical.json`.
- Fresh campaign executed 21 runs (Seed 523456 across all 3 groups: grid16, tree16, z1-legacy8 for modes B1, B2, B4, B5, B3, B6, P1).
- 100% of these 21 runs passed (21/21) with zero errors.
- Updated Dashboard running live on `http://localhost:5000` via `host/run_dashboard.py`. Accessible at root `/` for fresh results and `/historical` for preserved legacy data.
