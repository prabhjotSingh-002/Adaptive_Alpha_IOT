# AdaptiveAlpha IoT — Resolution and Verification Plan

Date: 16 November 2026

**Status: PLAN ONLY. Implementation, builds, tests, simulations, dashboard changes and campaign promotion are not authorized by this document. Ask the user before execution, as explicitly requested.**

## 1. Authority and scope

Follow `AGENTS.md`, `PLANS/MASTER_IMPLEMENTATION_PLAN.md`, `PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md`, `PLANS/PHASE_05_IMPLEMENTATION_PLAN.md` and the phase journals. Original plans remain unchanged. This document sequences investigation and proposed repairs; it does not close any gate or authorize Phase 6. Complete the approved Phase 4/5 closure work, write detailed journal/report updates, then stop for the next instruction.

Current-session deliverable: this file only. Existing workspace changes belong to earlier work and must be preserved. No new execution result or verified research metric is claimed here.

## 2. Findings from read-only inspection

These are source/configuration observations, not a completed runtime audit. Historical report claims must be checked against original artifacts before reuse.

| Observation | Evidence inspected | Implication / remaining verification |
|---|---|---|
| P1 skips every zero-valued cost cell and returns `LAB_POL_NO_FEASIBLE` when no candidate survives. | `firmware/policy/policy.c`, `lab_policy_p1` | An all-zero table explains the fallback mechanism. Audit each actual run's config and POLICY reasons to establish its cause. |
| Current generated header contains an all-zero `LAB_P1_COSTS`; its selected policy mode is B6. | `firmware/generated-conf.h` | This is mutable last-build state, not proof of any prior P1 binary's settings. |
| Cost import is optional; missing import is explicitly labelled unavailable. Import verifies source manifest/summary hashes but labels target compatibility pending. | `host/run_experiment.py` | Qualification must extend beyond file existence and an optional CLI argument. |
| The inspected fresh protocol supplies no `--policy-cost-table` and no finite budget; its limitations explicitly describe P1 fallback and lifetime exclusion. | `results/campaigns/20261116-fresh/protocol.json` | Existing fresh results cannot simply be renamed validated adaptation results. |
| Sensor state already initializes `.cost_nj = LAB_P1_COSTS`; current integration already includes policy application and switch telemetry. | `firmware/sensor/sensor.c` | Recheck existing repairs rather than blindly reimplementing historical fixes. |
| Calibration scans Phase 4 runs, maps B1/B2 to cap 1 and B4/B5 to cap 4, leaving cap 2 unmeasured. It collects PDR/p95 but does not enforce quality thresholds before ranking. | `host/calibrate.py` | Validate actual configured caps, all required cells, measurement eligibility and cohort compatibility. Do not interpolate cap 2 without evidence. |
| P1 uses a static cost matrix and rate/deadline feasibility; residual energy is not used in its ranking. | `firmware/policy/policy.c` | Loading costs alone does not demonstrate residual-energy-sensitive optimization or repeated profile adaptation. |
| Runner sets the default model budget to `2**64-1`; lifetime depends on an explicit finite-budget argument. | `host/run_experiment.py` | No depletion in a functional campaign is expected, not sufficient evidence of broken depletion logic. |
| Lifetime code already represents FND/HND censoring and has a separate service-failure definition. | `host/lifetime.py` | Audit time origin, denominator, observation horizon and service thresholds before reporting lifetime. |
| Old dashboard structure remains in `host/dashboard.py`; `/historical` currently strips its mode comparison section. | `host/dashboard.py`, `host/campaign_dashboard.py` | Restore comprehensive presentation while preventing invalid pooled comparisons. |
| Phase index and detailed reports contain different historical status statements and later corrections. | `phase_jouney/README.md`, Phase 5 reports, `fresh_statistics_20261116.md` | Reconcile statuses in new execution reports; never treat old completion prose as acceptance evidence. |

## 3. Work package A — Preserve evidence and establish the audit baseline

1. Record current git status/diff, exact dependency pins and container identity. Do not reset unrelated edits or touch upstream sources.
2. Inventory all `results/phase_01/` through `results/phase_05/`, prior campaigns, failed attempts, inventories and source snapshots. Preserve everything in place; never delete `phase_jouney/tmp` or any of its contents.
3. Create a new uniquely named audit/campaign directory after authorization. Record original paths, sizes and SHA-256 digests in a new inventory. Never overwrite old manifests, summaries, inventories or protocols.
4. Trace representative native and Z1 P1 runs end to end: command → resolved config → calibration digest → generated header snapshot → binary → boot/config identity → raw POLICY/SWITCH/TX/RX logs → parsed events → summary → dashboard selection.
5. Distinguish missing calibration, incompatible calibration, no feasible action, valid best-action hold, dwell hold, insufficient saving, inactive context and depleted state. Report actual reason counts only after log verification.
6. Independently verify referenced artifact hashes, not just manifest status. Missing evidence remains visible as unverified; preserve failed/tampered artifacts and exclude them from validated aggregates.

Acceptance: a reproducible per-run evidence chain and explicit confirmed/provisional findings. A newly calculated hash anchors present bytes; it cannot retroactively prove historical authenticity where original hashes are absent.

## 4. Work package B — Repair calibration and configuration delivery

1. Define a versioned calibration contract: exact target/backend, power model, topology/client count, timing, payload, profile/cap, source/dependency hashes, metric units, seed, completeness and quality eligibility.
2. Identify compatible existing evidence first. Generate new static calibration runs only where qualification is missing. Keep calibration and evaluation seeds disjoint; never choose a winner from evaluation outcomes.
3. Cover both profiles and caps 1/2/4 with actual configured actions. If the runner cannot express a required static cell, add an explicit validated calibration control. Unmeasured cells remain unavailable, never fabricated or copied from neighbouring caps.
4. Reject duplicate cells, mixed cohorts, invalid summaries, nonfinite/negative costs, missing authenticated delivery, hash mismatches and incomplete runs. Freeze PDR/deadline eligibility thresholds before calibration selection; preserve valid poor outcomes without using them as eligible winners.
5. Verify costs against raw-log-derived metrics and energy reconciliation. Keep scope consistent: network-average cost is not automatically a measured local marginal action cost. Document the estimator and its limits.
6. Select B6's fixed cipher using the frozen calibration rule. Record its evidence rather than a hard-coded Ascon claim.
7. Require an explicitly qualified table for validated P1/B6 campaign tracks. Keep no-table fallback available only as a clearly labelled diagnostic. Enforce target/model/cohort compatibility and propagate table digest through campaign arguments, resolved config and manifest.
8. Validate numeric ranges, array shape, C constants and stale-build detection. The canonical runner remains the sole writer of generated configuration/build directories; do not hand-edit `generated-conf.h` as a fix.

Acceptance: a qualified table reaches the compiled mote and observed boot/run identity, malformed or incompatible imports fail before execution, and an absent-table diagnostic still exercises secure fallback. Native results remain functional/network evidence unless a valid measurement model is established; never silently reuse Z1 energy calibration as native energy evidence.

## 5. Work package C — Verify and repair genuine policy behavior

1. Compile the shared production policy C code for tests. Inspect initialization, timer wrap, rate estimation, queue ordering, oldest-reading age, payload accounting, arithmetic width and feature freshness.
2. Recheck the current sensor profile-preservation repair across selection, flush, encryption and TX; do not undo it. Check batch boundaries, queue cap reductions and deadline flushing.
3. Test zero/partial costs, inactive contexts, unavailable profiles, MTU/deadline rejection, dwell/hysteresis boundaries and transition-cost units. A held current action must remain feasible when conditions change; dwell must not excuse a constraint violation.
4. Determine whether measured cost rankings and changing feasible sets can produce the intended adaptation. If the existing static matrix cannot represent the intended energy/latency dependence, document the gap and specify the smallest measurable estimator extension consistent with the master. Do not invent battery multipliers, PDR feedback or transition energies.
5. Use separately labelled mechanism scenarios with predeclared traffic changes and validated costs. Keep the traffic schedule identical across compared arms. Verify both profile and cap decisions when measured conditions support them.
6. Distinguish startup selection, profile changes and cap changes in telemetry. Record candidates/constraint reasons sufficiently to explain choices, while accounting for added logging overhead across controls.
7. Validate timing telemetry on each target; `POLICY_TIME` is timing, not measured decision energy. Verify security invariants during transitions: no N0 downgrade, no nonce reuse, no unauthenticated acceptance and correct replay handling.

Acceptance: decisions match qualified costs and constraints in real Cooja logs; expected fallback tests pass; TX/RX agree with applied policy. Zero switches can be correct in stationary conditions. Never force oscillation, reverse cost rankings or lower margins merely to obtain attractive plots. If evidence does not support a profile crossover or energy improvement, report that limitation.

## 6. Work package D — Dedicated finite-budget/depletion track

Keep functional performance and lifetime experiments separate.

1. First validate Phase 4 energy prerequisites using the pinned Z1 model: Energest counter deltas/wrap, tick frequency, component accounting, overflow, monotonic consumption and host/firmware reconciliation.
2. Derive a finite budget and horizon from independent pilot consumption. Freeze them before comparative evaluation; use the same budget, workload, topology, observation rules and seed pairing for all arms.
3. Define battery-node population, root power assumption, warmup charging, time origin, sample resolution, demand schedule, drain interval and censoring rules. Preserve prospective demand after death so survivor-only PDR cannot hide lost service.
4. Run a controlled single-node depletion case, then a forwarding/bottleneck case. Confirm one terminal `ACTIVE → DEPLETED` transition, stopped generation/crypto/TX and disabled radio/forwarding as required by the model.
5. Separate routing recovery by surviving nodes from resurrection of a depleted battery. Do not add recharge/reboot recovery without an explicitly approved model and nonce-state design.
6. Only after correctness passes, run the dedicated comparative lifetime track. Report FND, HND and functional service failure separately, with event/censor flags and uncertainty appropriate to the sample count.
7. Audit the existing 5-second service bound against the policy's configured deadline; label these distinct definitions or obtain approval for a prospective protocol change. Do not reinterpret old results.

Acceptance: actual terminal depletion and forwarding effects are evidenced; no-death observations are right-censored, never zero lifetime or an invented death time. Native functional runs do not become battery-lifetime evidence.

## 7. Work package E — Fresh campaign and statistical validity

1. Use a new campaign ID and immutable protocol; never resume an old campaign with changed sources/configuration. Maintain separate calibration, mechanism, functional evaluation and lifetime tracks.
2. Freeze mode set B1/B2/B3/B4/B5/B6/P1, groups, seeds, run count, stopping/retry policy and eligibility before execution. Treat N0 only as explicitly unprotected diagnostics.
3. Begin with small native functional and Z1 instrumented smoke runs, then security/aggregation regressions, then approved paired evaluation. Build serially through the canonical runner in the pinned official container.
4. Record every exact command, exit code, stdout/stderr, source/config/scenario/binary/log hash and validation result, including failures. Select attempts using a predetermined technical rule; never discard low PDR or unfavorable valid results.
5. Verify matched scheduled traffic, not just matching seeds. Keep source/config/target/model/topology cohorts separate; prevent duplicate attempts from increasing independent sample counts.
6. Calculate metrics through the canonical parser/metrics pipeline. Report sample counts, missing pairs and paired effects; avoid significance or publication-scale claims from a small pilot.

Acceptance: every selected result is traceable and reproducible, with no historical pooling. Promotion requires integrity and behavioral qualification, not a promised positive result.

## 8. Work package F — Restore and polish the comprehensive dashboard

Use the existing local Flask dashboard. This task does not require migration to an external website service.

### Layout shared by fresh and archive views

1. Header with explicit Fresh validated / Historical archive navigation, campaign selector, provenance status and last verification time.
2. Metric cards with units, sample count, scope and missing-data states.
3. Rich mode-comparison table: delivery, latency, TX/batching, modelled energy where qualified, profiles/caps, separate profile/cap transitions and fallback reasons. Add lifetime columns only for the lifetime track.
4. Filterable, sortable runs table with mode, seed, target, topology, campaign, status, purpose, calibration state and evidence links.
5. Run details: raw logs, manifest, resolved parameters, calibration/power model, SHA-256 verification, selected-attempt lineage and failure reasons.
6. Detailed policy/energy/lifetime views only where supporting telemetry exists. Export the displayed cohort with source IDs, filters and integrity metadata.

### Presentation

Restore the old information hierarchy from the existing template/history. Improve readable typography, spacing, restrained colors, contrast, status/profile/cap badges, table borders, sticky headers and horizontal overflow. Use consistent units and precision, keyboard-visible focus and responsive cards. Preserve dense useful content rather than replacing tables with a sparse summary.

### Data safeguards

- Main view admits only explicitly selected, hash-verified new runs; until available it shows an honest empty/pending state. Existing fallback results remain accessible with their qualification.
- Historical view includes all phases and earlier campaigns, including failures and manifest-less early evidence. Missing provenance is labelled unverified, not hidden or fabricated.
- Restore historical mode comparisons only within a selected compatible cohort. Never reinstate the previous broad pooled statistics.
- Separate calibration, diagnostic, security, functional and lifetime data. Distinguish missing metric from measured zero; avoid misleading zero-height charts.
- Validate data and evidence routes, not just the page/API status. Scope caches to campaign and selection; surface integrity failures without silently falling back to stale data.
- Keep prior `historical.json` files unchanged. A new catalogue may reference them and additional preserved artifacts.

Acceptance: both routes retain comprehensive tables and drill-downs; cohort filters prevent invalid pooling; visible metrics reconcile with validated summaries/logs; old evidence remains reachable.

## 9. Verification and execution environment

Required container:

`contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`

Reuse pinned Contiki-NG/Cooja/Ascon checkouts. No upstream edits. Custom implementation stays in `firmware/` and `host/`; focused tests, new configs and reports use established project locations.

| Layer | Required evidence before acceptance |
|---|---|
| Production C | Policy, aggregation, energy arithmetic and crypto boundary regressions; actual compiler output |
| Host pipeline | Calibration provenance/compatibility, missing/tampered artifacts, seed isolation, censoring and paired-cohort checks |
| Builds | Native and Z1 build logs, resource fit and generated-config/binary hashes |
| Cooja | Qualified calibration, policy mechanism, security regression, depletion/forwarding and approved evaluation logs |
| Dashboard | API/data-route checks, filter isolation, missing/censored metrics, archive coverage and evidence links |
| Visual review | Desktop/narrow viewport inspection, contrast, keyboard navigation and rich-table readability |
| Preservation | Before/after inventory comparison of historical artifacts and untouched original plans |

Exact commands will be derived from inspected runner/test interfaces and recorded before execution. Commands involving new features must not be presented as already supported. No test, simulation or browser inspection was executed while writing this plan.

## 10. Order, stopping conditions and deliverables

Execution order: A audit → B calibration contract/repairs → C policy verification → D energy prerequisites and depletion correctness → Phase 5 pilot/report checkpoint. Obtain the required next instruction before Phase 6/full comparative expansion. Dashboard implementation can accompany the approved phase, with pending states until qualified results exist.

Stop a track on pin/source drift, manifest mismatch, unqualified calibration, crypto regression, infeasible action application, energy reconciliation failure or incomplete simulation. Preserve all failure evidence and create a new attempt after correction. A poor but valid result is not an infrastructure failure.

Expected deliverables after authorization:

- Audited issue/evidence matrix and new immutable preservation inventory.
- Minimal reviewed firmware/host repairs and focused regression evidence.
- Qualified frozen calibration tables and explicit compatibility metadata.
- New separate campaign records, raw logs, manifests and reproducible metrics.
- Comprehensive polished fresh/archive UI with verified evidence drill-down.
- Detailed phase journal/report updates, unresolved limitations and pending human gates.

## 11. User decisions before execution

1. Approve or revise this plan and authorize the first Phase 4/5 audit/repair stage. This is required by the user's explicit “no implementation; ask me” instruction.
2. Confirm whether the retained old layout in `host/dashboard.py` is the preferred design reference; otherwise identify the preferred prior revision. Proposed default: use that comprehensive layout with modern styling.
3. Before a large comparative/lifetime matrix, agree on runtime budget, target coverage and the frozen experimental protocol using the small pilot evidence. No arbitrary lifetime budget, seed count or guaranteed improvement is promised now.

**Current completion boundary: the plan is written; all implementation and runtime validation remain pending.**
