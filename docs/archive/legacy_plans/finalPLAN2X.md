# finalPLAN2X — Evidence-driven resolution and closure plan

Date: 17 November 2026. Status: proposed execution specification; this document does not claim that the listed repairs or experiments have been completed.

This request produces this plan only. Earlier execution authorization remains context, but no implementation, campaign restart/stop or dashboard promotion is performed while writing it. Original PLANS documents remain authoritative and unchanged. Preserve finalPLAN_execute.md and currentStatus_17.md as historical planning/audit records. Phase boundaries and actual human review gates remain mandatory.

## 1. What must be achieved

Deliver a calibrated, explainable policy; verified batching/depletion behavior; scientifically separated and reproducible results; and the original comprehensive dashboard structure with polished fresh/archive views. Every issue below must end with evidence-backed acceptance or an explicitly recorded unresolved blocker. “All resolved” is prohibited while any required acceptance is missing. Positive energy gains, repeated profile switches and uncensored deaths in every comparative run are not guaranteed outcomes.

Known checkpoint from currentStatus_17.md: 22 deferred Phase 4 runs and 20 selected corrected-campaign runs; 381 manifest-listed artifact hashes matched. These are the previous audit snapshot, not a live count. They do not establish full raw-event reanalysis, binary verification, all 35 Phase 4 groups, runner liveness or calibrated P1 behavior.

## 2. Issue ledger: what, why, where and expected closure

| ID | Problem and why it matters | Implementation/review locations | Required outcome |
|---|---|---|---|
| R01 | JSON running state may outlive the process; interrupted attempts can be lost from selection | host/run_campaign.py, host/run_experiment.py | Recoverable lifecycle, unique attempt identity, reliable liveness evidence and no competing writer |
| R02 | Missing P1 calibration causes safe fallback | host/calibrate.py, host/policy_validation.py, host/run_experiment.py | Qualified table required for adaptive validation; explicit fallback diagnostics remain possible |
| R03 | Imported tables lack full compatibility; cap 2 absent; configured cap may differ from transmitted count | Same files, firmware/aggregate/aggregate.c, host/metrics.py | Measured cells with exact context, actual batch distributions and complete provenance |
| R04 | Dwell/savings can retain infeasible actions; static features/costs do not establish full adaptation | firmware/policy/policy.c/.h, firmware/sensor/sensor.c | Constraints take priority; decisions explained by available measured features and costs |
| R05 | Deadline equality and flush ordering differ from naive fill prediction | firmware/aggregate/aggregate.c, firmware/sensor/sensor.c, host/policy_validation.py | One documented scheduling contract shared by candidate prediction and actual batching |
| R06 | Functional unbounded budgets cannot demonstrate lifetime or B3 threshold behavior | firmware/energy/*, host/lifetime.py, host/run_experiment.py | Separate finite-budget mechanism and comparative tracks, terminal depletion and proper censoring |
| R07 | Phase 4 completion wording exceeds checks performed in latest audit | host/validate_phase4.py, phase_jouney/*, new evidence ledger | Every required group linked to compatible executed evidence; targeted reruns for gaps |
| R08 | Campaign readers check only part of evidence and compatibility | host/campaign.py, host/comparison_guard.py, host/analysis.py, host/plots.py | Full artifact/binary validation, schema-aware cohort admission and reproducible paired statistics |
| R09 | Dashboard points to old campaign and archive misses incomplete/early records | host/dashboard.py, host/campaign_dashboard.py, host/run_dashboard.py | Comprehensive polished UI, explicit campaign selection, inclusive archive and safe promotion |
| R10 | Source freeze includes UI; edits can interrupt active campaigns | host/campaign.py, host/run_campaign.py | No editing active frozen sources; versioned future separation of experiment and presentation provenance |
| R11 | Large topologies need honest measurement qualification | host/topologies.py, host/scenario_target.py, host/run_experiment.py | Grid16/tree16 functional validation separated from qualified Z1 energy conclusions |
| R12 | Historical integrity and reporting corrections | new audit output, phase_jouney reports | Original artifacts retained; corrections/reanalysis additive; no false completion or improvement claims |

All ledger statuses start OPEN, except existing evidence may be accepted after verification. The earlier feasibility patch is implemented/host-tested, not yet fully mote-qualified.

## 3. System design decisions

### D1 — One experiment owner and immutable attempts

The canonical runner owns generated config and build directories. Serial builds/runs remain required. Before work, inspect host-visible process identity, start time, command, container identity, locks and log progression. A PID alone can be reused; a JSON status alone is staleable. If host visibility requires permission, use the normal escalation mechanism.

If a campaign is active, preserve its current attempt and arrange a graceful stop at a run boundary before modifying frozen sources. Do not kill unrelated processes or rewrite a live protocol. If already interrupted, reconcile any unregistered directory using run identity/config/command and artifact validation before deciding selection. Never adopt a run merely because its timestamp is recent.

Future lifecycle: queued → running → passed/failed/interrupted, with attempt record persisted before child launch; heartbeat, process/container identity, terminal exit and evidence paths. Parent interruption must not leave an uncontrolled child writing the shared build tree. Add a stop request handled between runs. Crash recovery and stale locks need tests.

The existing corrected campaign is functional/fallback evidence. Completing all 210 cells is optional for that purpose and is not a prerequisite for repairing P1. Do not spend more runs expecting calibration to appear automatically.

### D2 — Distinct qualification levels

Use explicit run purposes and qualification states: calibration, functional diagnostic, mechanism validation, functional comparison, lifetime comparison and security fixture. A transport/parser pass is different from calibrated-policy qualification. No-table P1 must be visibly diagnostic, and validated campaign preflight must reject it.

Native Cooja provides functional/network evidence. Z1 component-model energy remains modelled energy, not physical battery measurement. Never transfer a Z1 cost table to native and call it target-calibrated. Native execution of a Z1 policy may be permitted only as an explicitly labelled portability/mechanism test with separate admission rules; otherwise omit its calibrated-energy claims. Never fill native energy cards with Z1 numbers.

### D3 — Versioned calibration contract

Table schema must include units, estimator definition, target/backend, dependency pins, power-model hash, source fingerprint, topology/client count, traffic schedule, warmup/drain, payload/tag/deadline semantics, calibration seeds, eligible run IDs and hashes, actual profile/cap/batch distribution, quality thresholds and eligibility decisions.

Use profile × configured cap cells for both profiles and caps 1/2/4. Costs correspond to the measured behavior of that cap under its workload; a cap-4 run sending three-reading packets must not be described as a measured four-reading packet cost. Missing cells stay unavailable. Do not interpolate, extrapolate or copy cost entries without an independently validated model.

Read raw logs through canonical parsing/metrics and verify energy reconciliation. Reject malformed ranges, booleans masquerading as integers, NaN/Infinity, unsupported schema, stale/mismatched source/model/target, duplicated cells and evaluation-seed contamination. Validate the table against the fully resolved runtime config AFTER CLI overrides, not the initial base config.

Use explicit curated input paths instead of an uncontrolled scan of all Phase 4 directories. Preserve accepted and rejected records with reasons. Calibration quality eligibility is predeclared; poor valid evaluation results must never be discarded for failing those thresholds.

B6 cipher selection uses a frozen calibration rule. Network energy per delivered reading is initially a scenario-level empirical proxy, not automatically marginal local action energy. Establish its predictive validity on held-out calibration validation before stronger claims. Keep boot/warmup/drain inclusion explicit.

### D4 — Constraint-first policy and realistic features

Retain the current current_feasible guard and verify missing-cost/startup, invalid profile/cap state, arithmetic overflow, timer wrap, payload/deadline changes and depleted contexts. Never index the cost array with unchecked runtime profile values. Dwell and savings may hold only a still-valid action. Authentication remains mandatory.

Audit current feature implementation: the inspected sensor derives rate from LAB_PERIOD_MS, not observed rolling arrivals. If time-varying traffic is used, add a bounded measured interarrival estimator with initialization/staleness semantics, and a deterministic schedule shared across arms. Do not claim online traffic learning from a compile-time constant.

Static costs plus a stationary feasible set can correctly stay on one action. To establish mechanism changes, use predeclared traffic regimes with measured corresponding costs; transitions must follow real rankings and constraint changes. Both ciphers need not alternate if evidence always favors one.

Residual energy currently does not affect P1 ranking. Multiplying every candidate by the same battery weight does not change the argmin. Before claiming residual-aware adaptation, define an explicit objective/constraint that changes action selection and calibrate its parameters: e.g. a measured forecast of energy demand over a fixed service horizon versus residual budget, while preserving deadline/security requirements. Specify forecast error and infeasibility behavior. This is a design proposal requiring validation, not an existing feature or guaranteed benefit. If no defensible estimator can be implemented, mark the residual-aware requirement unresolved and report the implemented cost-aware scope honestly.

Transition cost and margin must have consistent nJ versus nJ/reading units and a defined prediction horizon. Measure transition overhead where possible; otherwise label conservative assumptions and perform sensitivity tests. POLICY_TIME measures timer ticks, not energy; zero ticks can mean below resolution. Count profile changes and cap changes separately; distinguish startup selection and fallback entry/exit.

### D5 — Batching/deadline contract

Keep per-node aggregation; routers forward rather than merge other nodes' plaintext. Payload capacity is floor((budget − header − tag)/reading_bytes). Current protected constants give floor((47−11−16)/10)=2. Source constants should be shared rather than duplicated magic numbers.

Keep the existing rule that an old deadline is serviced before a newly due reading is offered, unless a separately reviewed design change is necessary. Fill-time estimate (cap−1)×period must account for this equality ordering and actual service/flush lead timing. Test below/equal/above deadline boundaries; do not promise full cap occupancy when equality flushes earlier.

Batch hold deadline bounds local waiting, not end-to-end arrival. Report both. If an application delivery deadline is required, allocate a measured forwarding allowance and validate deadline misses; no unmeasured per-hop constants. When cap decreases below existing queue occupancy, define flush/chunk/drop semantics explicitly so TX never contradicts logged active cap and no reading is silently lost.

### D6 — Lifetime is a separate measurement track

Finite budget, battery population, root power assumption, charging start, workload, time origin and observation horizon must be frozen. First use the existing depletion cases to verify terminal radio/forwarding cutoff and counter accounting. A single targeted deplete-node bottleneck experiment is mechanism evidence, not automatically a whole-network battery-life comparison.

Prospective demand remains scheduled after a node dies. Show delivered/generated PDR and delivered/scheduled service ratio with clear denominators. FND, HND and functional failure are separate events; HND may equal FND in a two-node battery population. No-event runs are right-censored. Retain original crossing versus confirmation times: the inspected representative summary crosses at 164000 ms and confirms at 174000 ms; earlier prose calling 164000 the confirmation time needs an additive correction.

Do not resurrect depleted nodes. Surviving-network route recovery is distinct from battery recharge/reboot. Preserve nonce safety on any separately approved restart model. Keep existing 5-second functional-service bound visibly distinct from a 3-second batching deadline.

### D7 — Provenance and presentation

Raw logs, binaries, generated config, manifests and original inventories remain immutable. New reanalysis outputs name parser/metrics versions and link original artifacts; never overwrite the original summary to make it pass. Historical source drift means another cohort, not automatic invalidity of preserved past results.

Future source provenance may separate experiment-affecting code from presentation code, with versioned rules and both fingerprints retained. Never exclude parser/metrics/runner code merely to bypass a source-drift failure. Do not retrofit new identity rules into old frozen campaigns.

## 4. Ordered implementation packages

### P0 — Establish safe baseline and finish the file audit

Read all applicable instructions, authoritative plans and phase journals. Re-read every changed implementation/test file in full, inspect git diffs, new files and the prior audit baseline. Record ownership uncertainty: git diff alone cannot attribute another agent's work to this session. Inventory all historical artifacts, dependencies, current source/config hashes and errors.

Resolve runner liveness as D1 describes. Record a new reconciliation report; do not silently change prior state. Expected output: exact current attempts, no competing writer, verified preserved baseline and an issue ledger tied to source lines/evidence.

### P1 — Close Phase 4 evidence accurately

Review all 22 newly stored deferred runs at raw-event level: expected config, completion markers, generated schedule, deadline/cap behavior, terminal depletion, final energy sample, forbidden post-death activity, survivor evidence and censoring. Verify binary hashes in addition to artifact hashes. Link the prior 28 groups by scenario/source compatibility and identify which affected cases need rerunning.

Create a new machine-readable acceptance ledger and additive journal corrections. Do not regenerate all 35 groups automatically; rerun gaps or cases invalidated by changed measurement/firmware behavior. Required failures stay archived. Update the detailed report and stop at the Phase 4 checkpoint for the next phase instruction per project rules.

### P2 — Calibration and runner repairs

After Phase 5 continuation: extend host/calibrate.py with curated inputs, schema/quality rules and explicit profile/cap metadata; extend policy_validation.py with semantic compatibility and qualification; extend run_experiment.py with calibration-only static cap selection and resolved-config validation. Proposed new CLI options must be implemented/tested before use: --calibration-inputs, --calibration-cap, --require-qualified-policy, --traffic-schedule. Final names can follow repository conventions and must be documented with --help.

Add measured calibration sets for missing cells, isolated from evaluation. Freeze immutable table before evaluation. Log table hash/config identity at boot and verify against manifest/generated header/binary. Do not manually edit generated-conf.h.

### P3 — Firmware, telemetry and parser repairs

Change firmware/policy/{policy.c,policy.h}, sensor/sensor.c and only necessary aggregate/common event files to implement D4/D5. Extend host/parse_logs.py and metrics.py for qualified decisions, fallback reason counts, separate transitions, actual batch occupancy and timing validity. Keep shared production C in host tests. Protect wire-format compatibility or version schemas explicitly.

Add focused tests to tests/unit/test_policy.py, test_metrics.py, test_core.c and new calibration/runner tests as needed. Tests use synthetic values only as unit fixtures and must never feed research dashboards.

### P4 — Small mechanism verification before scaling

Run native functional smoke and Z1 calibrated smoke at root+2; then deadline/payload boundaries and secure profile transitions. Use a no-cost diagnostic to prove explicit fallback remains safe, and a qualified-cost run to prove costs reach the mote. Expected result is explainable action selection, not a minimum arbitrary switch count.

Run B3 threshold crossing with a finite budget and verified thresholds; run B6 adaptive batching under changing feasible rates; run P1 under calibrated workload regimes. Where dynamic schedule support is not yet implemented, separate constant-rate runs establish configuration sensitivity only, not runtime adaptation.

### P5 — Separate finite-budget pilot

Choose budget/horizon from independent consumption pilots and freeze them before comparing arms. First verify one-node and bottleneck depletion. Then a small matched seven-arm Z1 pilot when all modes are qualified. Security fixture hooks must not contaminate energy measurement runs. Evaluate uncertainty and sampling sensitivity; do not call differences smaller than measurement uncertainty established gains.

### P6 — Dashboard rebuild and safe promotion

Reuse the existing Flask application and old rich layout. Implement metric cards; mode comparison tables; filterable/sortable run table; run details; manifest/raw log/config/table/binary evidence links; policy reasons; separate lifetime views; export of exact selected cohorts. Add consistent typography, spacing, badges, borders, sticky headers, contrast, keyboard focus and mobile table overflow.

Archive catalogue must include phases 1–5, prior campaigns, failures, incomplete runs and records without summaries. Missing provenance stays visible as unverified. Comparison eligibility is stricter than archive visibility. Historical comparisons require compatible selected cohorts; never pool unlike modes/purposes/models/sources.

Add shared artifact verification in host/campaign.py or a focused host/evidence module: protocol/manifest/summary/raw/binary hashes, required files, schema, resolved-config identity, attempt-mode/seed/group correspondence and trusted path containment. Update comparison_guard.py with explicit functional versus lifetime rules, calibration digest and policy version. Current guard rejects lifetime, so do not bypass it to plot lifetime together with functional runs.

Finish UI changes before freezing new experiment source snapshots unless provenance separation is already implemented and tested. Atomically promote current.json only after acceptance and archive route verification. An unqualified campaign must not appear as “validated adaptive results.” Maintain rollback pointer/history without rewriting original campaign inventories.

### P7 — Phase 5 closure, then Phase 6 expansion

Write full Phase 5 report with commands, hashes, failures, limitations and remaining human review. Stop for the next instruction before Phase 6. Do not execute a large matrix merely because a launcher can run it.

For later approved expansion, explicitly include grid16 and tree16 (1 root+15 sensors) as native functional groups and legacy Z1 root+8 as qualified modelled-energy group. Perform small topology smoke first. Use the same scheduled readings per paired arm and keep groups separate. Topology changes can invalidate scenario-level cost tables; recalibrate or validate transfer explicitly.

20/50-node scaling requires separate footprint/runtime/radio/topology feasibility and a new approved protocol. It is not supported or certified simply by changing the client count. No large native topology energy claim without a qualified model.

## 5. Tests and runs: what, why and acceptance

| Layer | Tests/runs | Why | Pass evidence |
|---|---|---|---|
| Calibration | Missing/partial/tampered table, cap mapping, NaN/ranges, wrong target/model/source, duplicate cells, seed overlap, quality eligibility | Prevent plausible but scientifically invalid costs | Explicit rejection reasons and valid complete cohort acceptance |
| Policy C | No costs, partial costs, rate drop during dwell, no-saving hold, changed payload/deadline, invalid state, uint64 bounds, timer wrap, context inactive | Avoid unsafe hold/indexing and preserve secure fallback | Production C compiled and exercised; failing-before/fixed-after regression where feasible |
| Aggregation | Cap 1/2/4, budget 47/67, periods 500/1000/4000 ms, exact deadline, queue already above new cap, route loss, critical flush | Match prediction, occupancy and actual send/drop behavior | Every reading accounted, no expired TX, no oversized packet |
| Security | Existing AES/Ascon KAT, bad tag/AAD/key, replay/reset and profile-transition acceptance | Policy changes must preserve authenticated delivery and nonce rules | Host and actual mote evidence, no plaintext fallback |
| Energy | Existing arithmetic/sampler tests, counter wrap, overflow, final accounting, idle/load, 125/250 ms depletion sensitivity | Validate model and terminal behavior | Reconciliation succeeds and post-death forbidden activity absent |
| Lifetime | FND/HND order, no-death censoring, scheduled demand, crossing vs confirmation, survivor routing | Avoid inflated lifetime/PDR claims | Raw events reproduce stored definitions and independent checks |
| Campaign | Persist-before-launch, interrupted child, stale state, duplicate attempt, drift, wrong group/seed, stop/resume | Safe resumability and no mixed cohorts | Failure artifacts retained; exactly one eligible selected attempt per cell |
| Dashboard | Tampered artifact, missing metric, censored lifetime, incomplete historical record, cohort isolation, evidence path traversal, missing inventory | Prevent misleading displays or inaccessible history | API/route tests plus real browser inspection |
| Comparison | Seed pairing, duplicate/missing pairs, one-seed CI unavailable, null energy, different power/table/source | Valid statistical unit and scope | Canonical metrics, reproducible analysis with lineage |

Zero switch count and a poor PDR are not automatic implementation failures. A decision inconsistent with qualified inputs, invalid artifact, mismatched TX profile or silently missing demand is a failure.

## 6. Execution commands and logging contract

Use only the pinned official image:

`contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`

Existing test commands to execute inside that image with the workspace mounted at /workspace and working directory /workspace:

```bash
python3 -B -m unittest discover -s tests/unit -p 'test_*.py' -v
bash scripts/test_phase2.sh
bash scripts/test_phase3_crypto.sh
bash scripts/test_phase4_ascon.sh
bash scripts/test_phase4_energy.sh
```

Inspect each script before execution for build-directory ownership and output locations. Run serially. For every invocation, write command, UTC start/end, exit status, stdout/stderr, source/config hashes and container identity to a NEW audit directory; preserve failures and rerun as a new attempt. Do not merely record a paraphrased command or reconstruct missing stdout afterward.

Canonical run examples below use existing options; run on the established runner host, which manages its own pinned build/simulator container. Do not blindly nest Docker inside the test container. These are illustrative cells, not authorization to reuse calibration/evaluation seeds or overwrite existing artifacts:

```bash
# Existing Phase 4 boundary interfaces; execute only if evidence review requires rerun.
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --period-ms 4000 --timeout-seconds 900
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --payload-budget 47 --timeout-seconds 900

# Existing depletion mechanism interface; original case budget, not a newly derived comparative budget.
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --power-model --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 223456 --energy-sample-ms 125 --timeout-seconds 900
```

Qualified P1 invocation template after compatibility repair and table freeze:

```text
python3 host/run_experiment.py --phase 5 --mode P1 --clients <matching-client-count> --target z1 --power-model --seed <unused-evaluation-seed> --policy-cost-table <new-qualified-table-path> [all matching scenario options]
```

This template is not copy-paste runnable until placeholders are resolved. Existing --policy-cost-table alone currently does NOT certify compatibility. New static-cap/dynamic-traffic/strict-qualification flags require implementation first. Never supply fabricated costs just to make this command pass.

Future campaign launcher, only after preflight:

```text
python3 host/run_campaign.py results/campaigns/<new-immutable-campaign-id>
```

Choose run count after small-pilot runtime measurements; keep calibration/validation/evaluation seeds disjoint. Ten seeds are not automatically statistically adequate. Freeze paired matrix and retry/selection rule before evaluation, retain unfavorable valid results and show missing pairs.

## 7. What not to do

- No overwriting/deleting original results, historical inventories, original plans or phase_jouney/tmp contents.
- No upstream Contiki-NG/Cooja core changes or invented crypto primitives.
- No manual generated-config patch as a substitute for runner repair.
- No continued large fallback campaign presented as adaptive verification.
- No invented costs, copied target energy, synthetic dashboard metrics or forced profile oscillation.
- No automatic restart on the same shared build tree without proving prior owner termination.
- No changed protocol/source/table inside a frozen campaign; make a new campaign.
- No silent redefinition of lifetime denominator, energy window or deadline to improve results.
- No treating matching hashes as proof of correct scientific interpretation.
- No claim that every historical group was revalidated because the last seven groups passed.
- No human gate marked complete by an automated agent.

## 8. Definition of done and final handover

Each R01–R12 entry must link: diagnosis → code diff/design decision → executed test command/log → source/config/scenario/binary/artifact hashes → observed acceptance → remaining limitation. Resolve discovered issues iteratively; unknown new bugs cannot be guaranteed absent by this plan.

Deliver an additive audit/acceptance ledger, qualified calibration tables, mechanism and finite-budget pilot evidence, preserved raw results, a comprehensive fresh/archive dashboard and detailed Phase 4/5 reports. Keep code-ready, host-tested, mote-validated, comparative-evaluated and human-reviewed states separate.

The work is complete only when the agreed Phase 4/5 acceptance criteria are evidenced and the dashboard exposes the correct qualifications. If the intended residual-aware policy or any required gate remains unsupported, report the exact blocker and leave that requirement OPEN. Phase 6 expansion remains a separately instructed stage.

## 9. Kiro handoff decision — avoid further unqualified bulk execution

**Recommended decision: stop scheduling new cells in the corrected campaign, let the active run finish if safely possible, preserve all existing results, then prioritize calibration and small qualified validation. Do not wait for 210 fallback-oriented runs to resolve P1.** This is an execution recommendation, not a record that a process was stopped by this document edit.

The supplied Kiro process listing establishes activity at its capture time, not permanent liveness or scientific validity. Recheck the actual host before acting. Do not reuse PID 158217 without verifying identity/start time. No failure in process output does not mean the experimental objective is satisfied.

Important corrections to the proposed advice:

- P1 fallback runs are useful diagnostics, not meaningless; they cannot substantiate adaptive benefit.
- B3 under unbounded energy does not validate threshold adaptation. B6 without qualified selection is a configured-cipher batching result, not a calibrated-winner ablation. Static controls remain useful within their exact cohort.
- Infinite battery is NOT the direct reason current P1 cannot switch. Inspected lab_policy_p1 does not rank by residual energy; costs, feasibility, dwell and savings determine selection. Missing qualified costs are the immediate problem.
- Do not blindly add `results/phase_05/cost_table.json`: verify its seed isolation, provenance, units, target/model/source/workload compatibility and actual cells first. Existing importer explicitly leaves compatibility pending.
- Do not simply repoint current.json: corrected campaign currently lacks historical.json in the inspected directory listing, while the archive loader requires it. A one-line pointer change can break archive access and still show unqualified P1.

### Safe operational handoff

1. Inspect exact parent/child/container identities, active output directory and locks. Snapshot current protocol/state/log references in a NEW audit record.
2. Check whether the current orchestrator has a tested boundary-stop facility. The inspected version does not: `--limit` is only a launch-time argument, not a control for an already running process. Do not invent a stop-file command or patch its source while active.
3. Use the owning agent's controlled process management to prevent the parent scheduling another cell while allowing the current child to finish; verify behavior before signaling. If a boundary cannot be safely coordinated, terminate only the identified campaign process tree/container in a controlled manner and preserve the interrupted attempt. Do not issue blanket pkill/killall, kill the Docker daemon, or assume stopping the parent stops its children.
4. Verify no remaining writer owns the generated/build paths. Reconcile the completed or interrupted active attempt from manifest/logs before any restart. Preserve original state as evidence and record reconciliation separately.
5. Implement/test future boundary-stop and crash-recovery support while idle. Begin repairs and small calibration runs in a NEW campaign. Keep existing corrected/fresh campaigns accessible under their original qualifications.

Copyable instruction to Kiro:

> Follow finalPLAN2X.md. First verify live process/container identity. Stop scheduling additional corrected-campaign cells at a safe boundary; preserve the active run if possible and all completed/failed artifacts. Do not edit frozen source/protocol or point the dashboard to corrected yet. Reconcile any interrupted attempt and prove the shared writer is idle. Then implement qualified calibration/config propagation, run small production-C and actual Cooja validations, and complete the comprehensive dashboard/archive changes. Do not claim P1 adaptation from fallback results or reuse an unqualified old cost table. Report exact evidence and follow phase checkpoints.

## 10. Concrete coding implementation blueprint

These are proposed functions/contracts and edits, not code already implemented. Implement and test them in dependency order; retain existing CLI compatibility where safe and version new manifests/tables.

### 10.1 Shared verification and calibration

Add a focused `host/evidence.py` module (proposed) with:

```python
verify_run(directory, required_artifacts, expected_identity) -> VerifiedRun
# Validate path containment, manifest schema/status, required raw logs/config,
# each artifact_hashes entry and binary_hashes entry, and identity correspondence.
# Return evidence/qualification; raise explicit errors, never substitute empty data.
```

`host/calibrate.py`: replace implicit mode-to-cap-only inference with explicit resolved profile/cap plus observed batch histogram. Add curated input manifest handling, schema output, selected/rejected lineage and quality rules. Retain unavailable cells explicitly; export the firmware's zero sentinel only at the validated conversion boundary.

`host/policy_validation.py`: add `validate_calibration(table, resolved_config, evaluation_seed)` and `require_policy_qualification(mode, purpose, qualification)`. Compatibility must include dependencies, model and workload fingerprint, not merely matching SHA strings for source manifest/summary files.

`host/run_experiment.py`: reorder main flow:

```text
parse options → resolve ALL configuration/target/model overrides
→ validate inputs and purpose → verify calibration against resolved config
→ attach costs/B6 winner/table digest → policy numeric/semantic validation
→ acquire canonical writer lock → create unique run record
→ generate config → build → simulate → verify/reconcile → write final manifest
```

Reject unqualified adaptive comparison before touching generated config. Record explicit diagnostic qualification when missing calibration is intentionally tested. Freeze table bytes alongside run metadata or reference an immutable verified artifact. Extend boot identity so observed config/table can be traced to the compiled binary.

### 10.2 Policy and sensor

`firmware/policy/policy.c`: factor candidate feasibility into a shared internal helper used for both current action and candidate selection. Validate current profile/cap before array indexing; the existing feasibility guard does not itself protect the subsequent unconditional current-cost indexing against corrupt profile state. Define fallback synchronization so persistent state, applied action and telemetry agree after fallback/recovery. Preserve current_feasible regression behavior.

`firmware/policy/policy.h`: document allowed ranges and units, feature validity and decision reasons. Add fields only with matching ctypes/test schema changes and firmware initialization updates.

`firmware/sensor/sensor.c`: calculate features from the declared schedule/observed arrivals as appropriate; preserve oldest creation time; apply cap reductions with an explicit safe queue policy; apply profile at a batch boundary; emit actual applied action. Keep schedule identical across modes. Do not duplicate policy ranking logic here.

`firmware/aggregate/aggregate.c`: retain shared queue implementation. Add helper(s) for exact encoded capacity and deadline semantics if needed, with production-C tests at equality and cap reduction. Record every drop rather than silently clearing a queue.

`firmware/common/events.h`, `host/parse_logs.py`, `host/metrics.py`: version added telemetry fields together. Produce fallback counts by reason, separate profile/cap changes, startup selection, decision timer resolution and batch occupancy. Reconcile decisions with actual TX/RX. Do not infer zero fallback from zero SWITCH events.

### 10.3 Campaign control and statistical admission

`host/run_campaign.py`: add persisted active-attempt record before spawn; record child/container identity; atomic state transitions; boundary stop request; interrupted-run reconciliation; fail-closed qualification preflight. Handle signals with a tested child-lifecycle policy rather than leaving the child untracked.

`host/campaign.py`: use shared verify_run for selected records; check protocol group/mode/seed/config against each actual run; include qualification in reports. Keep presentation fingerprints distinct only after versioned source-freeze design is tested.

`host/comparison_guard.py`: define explicit purpose-specific compatibility. Lifetime groups need matching budget/population/time/service definitions; adaptive comparisons need matching table/policy contracts. Keep duplicate attempt rejection and seed pairing. Do not loosen functional checks globally to admit lifetime records.

`host/lifetime.py`: verify time origin, prospective demand, censoring and crossing/confirmation names; change implementation only for evidenced bugs. Add metric schema/version if definitions change; keep historical summaries intact.

### 10.4 Dashboard coding deliverables — mandatory

`host/dashboard.py`:

- Replace summary-only archive discovery with an additive catalogue of directories/artifacts, including failed/incomplete/early records.
- Keep `/historical` comprehensive; cohort selection gates comparison tables.
- Add safe read-only run detail/evidence endpoints with path containment and integrity status.
- Show active filter, selected cohort, missing metrics and qualification visibly.

`host/campaign_dashboard.py`:

- Rebuild main HTML/CSS around the retained rich dashboard structure.
- Add campaign/group/purpose/mode/status selectors, metric cards, full mode table, sortable run table, run drill-down and parameter lineage.
- Display fallback/profile/cap reasons and lifetime event/censor state only when present.
- Distinguish qualified adaptive results, functional diagnostics and archival records. No fabricated placeholders that resemble measurements.
- Use shared style tokens for typography, spacing, badges, borders, sticky headers, mobile overflow and keyboard focus across both views.

`host/campaign.py`: extend response with verified per-run rows, qualification and evidence links; keep metric computation in canonical host modules rather than JavaScript.

`host/run_dashboard.py`: preserve localhost/read-only serving and pinned dependencies. Ensure catalogue availability and clear error reporting without launching simulations.

Proposed tests: `tests/unit/test_calibration.py`, `test_evidence.py`, `test_campaign_lifecycle.py`, `test_dashboard.py`; extend existing policy/metrics/lifetime/campaign/topology tests. Add only behavior-focused regressions, not tests that merely duplicate implementation constants.

Before promotion, verify `/`, `/api/campaign`, `/historical`, archive data routes, run details and evidence downloads against actual files; test missing inventory, tampered raw log/binary, empty campaign, failed run, unsupported schema and incompatible cohort. Perform desktop/narrow-screen visual inspection. Preserve current.json's old value in a promotion record and atomically update only after both fresh and archive acceptance.

### 10.5 Completion report required from implementer

For every changed file, report purpose, actual diff, test/run evidence, remaining limitations and relationship to R01–R12. Separate proposed function names above from delivered APIs. Include before/after screenshots for dashboard structure, exact campaign pointer, archive coverage counts and reproducible evidence links. An implementation claim without executed validation remains pending.

## 11. Verified review of Kiro checkpoint — 17 November 2026

This section updates the earlier baseline without rewriting historical findings. Current task scope: review and update THIS PLAN ONLY. No implementation fix, campaign action or pointer change was made during this review. File inspection, SHA-256 checks and Flask test-client requests were executed; no simulation or browser session was launched.

### 11.1 Verified progress and qualification

- Corrected campaign state now records `stopped_at_boundary`, 40 attempts, 40 selected. This verifies recorded state, not independently the asserted signal history, absence of every host writer or complete historical preservation.
- Four new calibration runs exist: `20261116T190440819875Z-B1-2`, `20261116T190531712542Z-B2-2`, `20261116T190612490140Z-B4-2`, `20261116T190655099472Z-B5-2`. Their manifests identify Z1, seed 223457, two clients and passed status.
- `results/phase_05/cost_table_223457.json` contains those four cells, one sample each. B5 is the numeric minimum in this small dataset. Both cap-2 entries remain zero/unavailable. Do NOT label the entire calibration requirement closed or the winner robustly established.
- The inspected importer still sets `source_hashes_verified_target_compatibility_pending`; its full compatibility repair has NOT been delivered.
- Smoke `results/phase_05/20261116T190756944367Z-P1-2` is **native cooja**, seed 123456, using the Z1-derived table. Its table digest is `dfd0bcc1a830ec78b15a57860dbf55a86a339bb143b553406ffe216418ff58a0`. Thus it establishes imported-cost functional behavior, not target-qualified native energy or Z1 mote validation.
- Raw parsed SWITCH events show node 2 at 2486 ms and node 3 at 3149 ms, each changing profile 1→2 and cap 1→4, reason 6. Two switches means one early selection change per sensor, not repeated adaptation within a sensor or a demonstrated response to changing conditions. Keep this useful smoke evidence with that qualification.
- Checked **58 manifest-listed artifact and binary hashes** across those four calibration runs and the smoke run; all matched. This verifies stored bytes against those manifests, not independent energy accuracy or complete calibration provenance validation.
- Promotion record exists and current dashboard selection was changed to corrected. Dashboard source rewrite exists. Do not count it as accepted: defects below remain.
- A search of results `*.log` and `*.txt` for `Ran 51 tests` found no matching saved log. The reported 51-test result is not independently verified by this review. Locate the exact command/container/source/log evidence; if unavailable, rerun appropriately and retain actual output rather than reconstruct it.

### 11.2 Critical dashboard defects — fix before presentation

**U1 — Mode aggregates are presented as individual-run measurements.** In `host/campaign_dashboard.py::_enrichRunList`, rows are synthesized from mode seeds, assigned invented IDs `group-mode-seed...`, given mode-mean PDR/delay/energy, hardcoded zero switches, passed status and null directory. The optional `/api/campaign-runs` enrichment is not implemented in the inspected dashboard modules. Therefore this is not a valid run-history table and its details cannot reliably identify real runs.

Required fix: implement a mandatory verified per-run response from exact selected attempt directories; use each actual manifest/summary for identity/status/metrics/switches. Remove aggregate-to-run fallback entirely. Missing endpoint/data must show unavailable/error, never fabricated rows. Test two same-mode runs with deliberately different fixture metrics and verify distinct rows plus actual IDs and working detail links. Fixtures remain tests only.

**U2 — Duplicate `/historical` route hides the rebuilt archive.** `host/dashboard.py` registers its old `index` route before `register_campaign()` adds the new archive route. Flask URL matching executed in this review returns `('index', {})`. GET `/historical` returns 200 but does not contain the new `All historical run records` heading. Route registration/syntax success is insufficient acceptance.

Required fix: give `/historical` exactly one owner; retire/redirect the old route deliberately. Test actual endpoint resolution and rendered content as well as API responses. Verify early/failed/incomplete record visibility and drill-down after the route fix.

**U3 — False verified provenance.** `_load_historical` initializes provenance to verified and retains it when a manifest is present, without comparing artifact/binary hashes. Run detail computes current hashes but does not compare them to trusted recorded values. A newly calculated SHA is not proof of verified history.

Required fix: derive provenance from shared evidence verification; use manifest-present/unverified, verified, missing and mismatch states. Validate resolved historical directory containment before opening files. Include a tampered-artifact regression and never silently turn a bad record into an empty list.

**U4 — Hardcoded scientific qualifications.** `qualBadge` marks every P1 fallback; another notice infers fallback from zero switches. Static metadata assumes B6 is always Ascon. These will mislabel future qualified or stationary-optimal runs.

Required fix: compute qualification from manifest calibration state and actual policy reasons; neither mode name nor zero switches alone establishes fallback. Resolve B6 profile from its recorded config/table. Include qualified-zero-switch and fallback fixtures.

**U5 — Unsafe HTML insertion.** Dynamic manifest/event/path values are interpolated into `innerHTML` in run detail and archive rows. Use DOM textContent or correct context-specific escaping, not direct insertion of log content. Test special characters/HTML-like artifact text. Preserve keyboard navigation and detail-panel focus management.

**U6 — Incomplete evidence access and archive functionality.** Detail returns a console-log path string rather than downloadable raw evidence; new archive markup lacks the required run drill-down and compatible-cohort comparison. Finish those requirements after U1/U2. Do not infer full archive coverage from an inventory count alone; compare catalogue against filesystem and prior inventories.

### 11.3 Executed route check and environment limitation

Executed using installed local Flask dependencies, without starting a listening socket:

```bash
PYTHONPATH=host:results/dashboard-deps python3 -B -
```

The script imported dashboard, used app.test_client() for `/`, `/historical`, `/api/historical`, `/api/campaign`, and inspected url_map matching for `/historical`.

Observed: `/` 200; `/historical` 200 but OLD endpoint; `/api/historical` 200; `/api/campaign` 500 with `ModuleNotFoundError: No module named 'numpy'` through host/analysis.py. This is a failure of this host test environment; it does not prove the pinned Docker dashboard environment also lacks numpy. Verify API behavior in the actual intended serving environment and preserve the log. Browser visual/interaction validation remains pending. A sandbox listening-socket restriction does not prevent Flask test-client checks.

### 11.4 Corrections to checkpoint prose

- Do not say all 170 remaining cells would be P1: 170 refers to all remaining mode/group/seed cells. Static and diagnostic runs may be useful, but further bulk execution was not the highest priority.
- Do not describe the new table as fully qualified while cap-2 coverage, compatibility and measurement uncertainty remain open.
- Do not claim two aggregate switches prove repeated dynamic or residual-aware adaptation.
- Do not call a source-changed older cohort invalid solely because a newer code revision exists.
- Promotion record says fresh/archive routes were verified; current route-level evidence shows the rebuilt archive is not actually served. Add a corrective record later rather than overwrite the original promotion record.

### 11.5 Updated next-action order

1. Preserve and reuse the four measured calibration runs and functional smoke; do not repeat them without a specific reason.
2. Fix U1/U2/U3 first so the dashboard cannot show synthetic run metrics or misleading verification. Complete actual-serving-environment API tests; do not start another large campaign for a UI fix.
3. Complete calibration schema/compatibility and required cap coverage. Assess the very small B4/B5 difference against repeatability/model/timing uncertainty before making a strong winner claim.
4. Run a small **matching Z1** qualified P1 smoke if energy-policy validation remains in approved scope. If Z1 is deferred for time, keep that acceptance OPEN and label the native smoke functional portability evidence.
5. Validate meaningful mechanism scenarios and security/queue boundaries; then finish dashboard drill-down/archive and visual checks.
6. Recover or reproduce the claimed test evidence; update Phase 4/5 detailed reports with exact qualification. Respect phase checkpoints. No new 210-run campaign is required to close these defects.

This review recognizes real progress but leaves R02–R05, R08–R09 and relevant validation/reporting items open. Only plan documentation was changed by this review.


## 12. Execution phases — current controlling sequence

These are **2X phases**, not a renumbering of the project's original phases. This table organizes the full document; all relevant earlier requirements still apply.

| 2X phase | Scope | Exit / status |
|---|---|---|
| 1 | Implement reproducible read-only baseline and selected-run integrity audit; preserve source/status/process snapshot and historical inventory | Implemented and executed; see phase_jouney/final2x_phase_01.md. Host liveness and full semantic reanalysis remain explicitly unverified. |
| 2 | Repair dashboard U1/U2/U3/U4/U5: actual per-run data, unique archive route, truthful provenance and safe rendering | Verified API/route regressions and real evidence drill-down; no invented run rows |
| 3 | Complete calibration qualification/cap coverage for 3-node Z1 and establish separate 9-node compatibility; review Phase 4 evidence | Pending; reuse compatible evidence, no automatic small-to-large cost transfer |
| 4 | Policy/batching/security repairs; 3-node Z1 mechanism checks, then 9-node Z1 P1 finite-budget pilot | Pending; actual terminal depletion, policy decisions and censoring verified; see Section 13 |
| 5 | Finish comprehensive fresh/archive presentation and visual checks, reports and release qualification | Honest demo and detailed closure ledger; human gates pending until performed |
| 6 | Separately instructed comparative lifetime/scaling expansion | New frozen protocol; no automatic 210-run launch |

Stop after each 2X phase and report. Existing project Phase 4/5 boundaries also apply. Phase 1 completion means this bounded audit implementation is delivered, NOT that every P0 review requirement or host-liveness check is complete. Remaining baseline uncertainties are carried explicitly into Phase 2 preflight.


## 13. User-selected network scope — 3-node then 9-node Z1

This scope clarification supersedes earlier optional Z1 deferral and suggestions to run grid16/tree16 now. **Retain Z1 energy/depletion validation; defer new 16-node grid/tree and larger scaling runs.** Preserve all existing large-network evidence and archive access. This update changes planning only; no simulation is launched by writing it.

| Stage | Network | Purpose | Required acceptance |
|---|---|---|---|
| A | 1 root + 2 sensors = 3 nodes, Z1 | Fast calibration qualification, shared policy/queue checks, controlled depletion and bottleneck mechanism | Verified costs/config identity; secure decisions; terminal cutoff and accounting; reuse compatible Phase 4 evidence |
| B | 1 root + 8 sensors = 9 nodes, Z1 legacy | Qualified P1 operation with a finite budget and actual depletion evaluation | Compatible 9-node cost qualification; recorded finite budget; actual death evidence in mechanism pilot; correct FND/HND/service/censor metrics |
| C | Same 9-node Z1 layout, small paired pilot | Compare P1 with qualified static controls and ablations under equal demand/budget | Start with one paired seed after preflight; expand only if time permits and protocol authorizes it; preliminary claims only |
| Deferred | 16-node grid/tree and larger networks | Scaling/topology sensitivity | No new runs now; future separately instructed scope |

### Execution requirements

1. In 2X Phase 3 qualify the measured 3-node calibration, fill needed cap cells and verify source/model/traffic compatibility. Do not transplant scenario-level 3-node energy costs into 9-node evaluation without independent transfer validation or a new 9-node calibration cohort. Keep calibration and evaluation seeds separate.
2. In 2X Phase 4 first validate the 3-node Z1 mechanism. Then run a small 9-node P1 functional check and a separately labelled finite-budget pilot. Freeze budget and horizon using independent pilot consumption before comparative outcomes are inspected. Do not blindly reuse the historical 9 J budget; account for warmup and ensure the intended active observation window exists.
3. Current CLI uses `--clients 2` for 3 nodes and `--clients 8` for 9 nodes, with `--target z1 --power-model`. A finite `--energy-budget-nj` enables lifetime evaluation. The qualified `--policy-cost-table` and matching scenario settings must be explicit.
4. **Do not pass `--bottleneck` with 8 clients:** current runner supports that fixture only with two sensors. The 9-node legacy topology is not automatically proven to contain a critical forwarder. If forwarding-node death is claimed there, verify routes and choose the intended test node from evidence; otherwise retain the established 3-node bottleneck test for that mechanism.
5. Distinguish targeted single-node depletion from a network-wide finite-battery comparison. Verify how `deplete_node` applies budgets before choosing the population; document root power and each sensor's budget. Apply identical rules across compared modes.
6. Demand must continue prospectively after death. Report generated-based PDR separately from scheduled-demand service. Retain censored cases; do not force every comparative arm to die or count node death itself as a P1 improvement.
7. The 9-node P1 pilot must demonstrate valid cost-driven decisions AND correct depletion accounting. Death alone does not prove adaptation; switching alone does not prove energy savings. Static best-action behavior remains a possible legitimate outcome.
8. Before any comparison, run only the smallest needed diagnostic/mechanism cells. A full seven-mode × one-seed comparison is seven evaluation runs, excluding calibration, security and mechanism work. Do not restart 210 cells. More seeds improve assessment but require time and a frozen extension plan.
9. Present 3-node and 9-node results in separate dashboard cohorts, with target/model/budget/calibration identifiers and evidence links. Keep older unlimited-budget P1 runs labelled fallback/functional diagnostics.

Section 12 Phase 4 now explicitly owns this small finite-budget pilot; it is not silently deferred to Phase 6. Phase 6 remains broader statistical/scaling expansion. Existing project/2X phase checkpoints still apply. If time prevents Stage B completion, report 9-node energy/depletion validation pending rather than declaring full resolution.


## 14. Review of supplied Kiro completion table — 17 November 2026

This additive review supersedes conflicting completion labels in the supplied chat table. Scope: source/document inspection and calibration manifest/summary hash checks only; no new simulations, build, test rerun, campaign launch or human acceptance. Sections 12–13 remain the controlling execution sequence.

### Corrections supported by current files

| Item | Corrected status and reason |
|---|---|
| R01 | PARTIAL. state.json records stopped_at_boundary; this is not proof of crash recovery, heartbeat or absence of active writers. Lifecycle acceptance remains open. |
| R02 / R03 | PARTIAL, not qualified closure. All eight manifest/summary hashes for the four seed-223457 source runs matched in this review. However run_experiment.py explicitly records source_hashes_verified_target_compatibility_pending. policy_validation.py validates integer widths/array shape, not full runtime calibration compatibility. The table lacks the full D3 schema; cap 2 remains unavailable. Documenting the gap does not satisfy required coverage. |
| R04 | Feasibility fix present; test_policy.py contains 20 test methods, not 52. The saved 82-test log covers several modules. Ordinary P1 Z1 smoke does not itself prove on-mote rate-drop/dwell regression, residual-aware ranking or dynamic adaptation. Keep these acceptance items open. |
| R05 | OPEN. flush_lead_ms cohort equality is not a tested scheduling contract. Below/equal/above deadline and queue-cap reduction behavior still need dedicated acceptance evidence. |
| R06 | PARTIAL. comparison_guard.admit_group rejects lifetime runs outright. This prevents mixing but does not implement or qualify lifetime comparison admission/statistics. |
| R07 | PARTIAL. Existing audit JSON reports 22 runs, 209 artifact checks and no post-death TX violations. This review did not independently replay that audit. Those fields do not establish all 35 groups, separate binary verification, final energy accounting, forwarding cutoff and every D6 acceptance condition. Human gates remain pending. |
| R08 | PARTIAL. campaign_rows verifies protocol, manifest and summary hashes only. Detail-view artifact checks are useful but do not enforce complete artifact/binary verification before comparison admission. |
| R09 / R10 | Reported pointer/archive and safe-stop progress do not close all U1–U6 presentation, visual acceptance or future source-freeze requirements. Revalidate actual endpoints and live writer status at the next implementation preflight. |
| R11 | Labels are appropriate qualification, not validation of energy portability or large-topology measurement. New 16-node work remains deferred by Section 13. |
| R12 | Preservation remains mandatory. No historical artifacts were modified by this review. A universal claim that all original files remain intact needs a full inventory comparison; it is not established merely by this table. |

### Package labels and launch decision

The chat table renumbers original packages incorrectly: Section 4 P3 is firmware/telemetry/parser repair; P6 is dashboard rebuild and safe promotion, not a qualified campaign. Use Section 12's explicitly named **2X phases** for the current sequence and retain the original P0–P7 meanings.

The matching Z1 smoke and six security runs reported in phase_05_detailed_report.md are useful progress, but do not close every P4 mechanism requirement: its B3 functional smoke has unlimited budget and zero threshold switches. Two aggregate P1 switches do not prove repeated dynamic adaptation.

**Do not start the proposed 4.5-hour bulk campaign on the strength of this completion table.** The 72-minute/4.5-hour estimates are unverified scheduling estimates, not measured guarantees. Complete compatibility/admission and required boundary checks first. Follow Section 13: qualified 3-node mechanism evidence, independently qualified 9-node costs, frozen finite budget/horizon/population, then a small 9-node P1 pilot. Start comparison with one paired seed only after preflight; three seeds are not the automatic next step. No 210-cell or new grid16/tree16 launch is authorized by this review.

Before launching, record exact command, resolved config, calibration digest and compatibility decision, source/model/scenario hashes, single-writer evidence and expected acceptance checks. Preserve failures. Stop at each applicable 2X/project checkpoint. Phase 6 and human gates remain pending.

Review evidence: inspected host/calibrate.py, host/policy_validation.py, calibration importer in host/run_experiment.py, host/comparison_guard.py, host/campaign.py and detail verification in host/campaign_dashboard.py; counted 20 policy test methods; read saved unit-tests-final.log (82 tests, OK; historical execution, not rerun); executed Python SHA-256 comparison of all four calibration manifest/summary pairs (8/8 matched); read campaign state (stopped_at_boundary). No claim of a full repository or raw-event audit is made.

## 15. Direct code/results verification and fresh test outcome — 17 November 2026

**Status: finalPLAN2X is partially implemented, not accepted complete.** This additive update records the subsequent direct codebase review and executed tests. It supersedes stale pending statements where newer evidence is identified below; earlier history remains preserved. This documentation update starts no implementation phase or campaign.

### Executed tests and diagnosed failures

The production-C unit suite was run in the pinned official container `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`, from `/workspace`:

```bash
python3 -B -m unittest discover -s tests/unit -p test_*.py -v
```

**98 tests ran; 4 failed; process exit 1.** The historical 82-pass result does not certify the current suite. [Fresh container log](results/phase_05/audit_17nov/code_review/container-tests-approved.log); initial host dependency errors and sandbox execution failure are preserved in the same directory.

All four failures are in `tests/unit/test_deadline_flush.py`: exact deadline, above deadline, oldest-reading hold, and readings retained before commit. Code inspection found invalid test bindings/setup:

- Python `LabReading` declares id/value(int32)/created_ms, while production `protocol.h` declares id/created_ms/value(uint16). Test value 100 becomes C created_ms 100, explaining the observed 2900-ms hold instead of 3000 ms.
- Python `LabBatch` omits production epoch/profile and has the wrong layout.
- Budget 67 and reserved 27 double-count the 11-byte header: production capacity is floor((67−27−11)/10)=2, while the test expects three readings. Offer return values are ignored.

These failures do **not** prove a production firmware deadline bug. Correct the test ABI and budget setup, assert offer results, and rerun before accepting the deadline contract. No test or firmware fix was made during this review.

### Newer run evidence confirmed

- Z1 P1 smoke `20261116T200027621258Z-P1-2` exists with passed status, two aggregate switches, profiles 1/2 and caps 1/4. It is no longer merely pending; full calibration compatibility and changing-workload adaptation remain unproven.
- Native B3/B6/P1 attack runs `20261116T200344854678Z-B3-2`, `20261116T200404255928Z-B6-2`, and `20261116T200423434444Z-P1-2` each report 8 injections and 8 rejections.
- Native root-reset runs `20261116T200453748010Z-B3-2`, `20261116T200513471485Z-B6-2`, and `20261116T200535126936Z-P1-2` have passed manifests and rejection counts 88/53/53. Their injection counters are zero; the test's conditional injection-equality check therefore does not independently validate reset semantics.
- Across these seven runs, **58/58 manifest-listed artifact hashes matched**. This is stored-artifact integrity evidence, not full raw-event/binary or scientific qualification.

Exact extracted results: [run checks](results/phase_05/audit_17nov/code_review/run-checks.json). Reviewed implementation/test fingerprints: [source hashes](results/phase_05/audit_17nov/code_review/source-hashes.json).

### Remaining code defects and acceptance gaps

| Area | Direct code finding | Required follow-up |
|---|---|---|
| Calibration | Importer explicitly records `source_hashes_verified_target_compatibility_pending`; complete D3 schema/runtime compatibility and cap-2 measurements are absent. Calibration reads PDR/p95 without enforcing planned quality thresholds. | Complete qualification before claiming calibrated evaluation. |
| Dashboard switch counts | `/api/campaign-runs` reads `policy.switches`, while actual summaries contain `policy.total_switches`. | Correct the field mapping and verify real per-run counts. |
| Dashboard qualification | `qualBadge` still marks every P1 as fallback; a notice hardcodes zero switches. | Derive labels from actual calibration state and policy reasons. |
| Dashboard progress | Real `/api/campaign-runs` and real-row fetching now exist; historical provenance defaults to unverified. | Preserve these fixes; do not repeat older invented-row findings as current facts. Remaining dynamic HTML/path checks and visual acceptance are open. |
| Campaign recovery | `run_campaign.py` persists attempts only after the child returns; durable prelaunch attempt, heartbeat and boundary-stop handler are absent. | Implement/test crash recovery; saved stopped state is not liveness proof. |
| Policy safety | `current_feasible` correctly gates dwell/savings and policy tests pass, but cost lookup indexes `current_profile-1` before guarding invalid initialized profile state. | Validate runtime profile before indexing; targeted regression required. No crash reproduction claimed. |
| Policy features | Sensor uses `100000 / LAB_PERIOD_MS`; P1 ranking does not use residual energy. | Do not claim measured rolling-rate or residual-aware P1 adaptation. |
| Deadline/cap behavior | Production uses deadline equality and flush-before-offer; prediction permits equality and batch construction copies the entire queue after cap shrink. | Repair the harness and validate prediction/occupancy contracts. |
| Evidence admission | Campaign reader verifies protocol/manifest/summary but not complete raw/binary/schema/config identity. | Finish shared evidence admission before campaign acceptance. |

Next steps remain within the existing phase/checkpoint sequence: repair and rerun the invalid tests, close calibration/admission and policy/dashboard defects, then perform the authorized qualified mechanism and finite-budget work. No bulk campaign restart is justified by these results. Human gates and Phase 6 authorization remain pending.

Detailed companion record: [direct codebase review in the acceptance ledger](phase_jouney/final2x_phase_01.md). This update modifies documentation only; existing logs, failed tests, original artifacts and historical findings remain preserved.

## 16. Items 1–3 repair execution checkpoint — 17 November 2026

This supersedes the corresponding unfixed-code statements in Section 15: deadline test ABI/budget repair and dashboard switch/qualification/rendering/shared verification repairs are implemented; **108 tests pass** in the pinned container. Actual dashboard/archive route checks pass using existing Flask dependencies. Versioned six-cell calibration with curated inputs, quality gates, actual batch occupancy and resolved-runtime/source/dependency checks is implemented. Final-source 3-node calibration qualifies; independent 9-node measurements were in progress at this checkpoint. Do not infer their acceptance until the closure record is added.

Detailed execution: phase_jouney/final2x_phase_01.md; evidence: results/phase_05/repairs_17nov/; usage: docs/calibration-v1.md. Original manifests, tables, failed checks and earlier source cohorts are retained. User explicitly deferred items 4–5 again; invalid-profile/traffic/queue mechanism work and Z1 policy/depletion validation remain pending. Browser visual acceptance, human gates and Phase 6 are not closed by this repair.


### Section 16 closure — items 1–3 completed

Final-source acceptance now supersedes the in-progress calibration checkpoint: **108 tests pass; 12 actual calibration runs qualify (six cells each for 3-node and 9-node Z1); 144 artifact/binary hashes match.** Separate versioned tables contain measured cap-2 cells and actual batch occupancy. Matching runtime contexts validate; topology/client/period/seed incompatibility rejects, including an actual 3-node-to-9-node CLI rejection before build. Point-estimate B6 profile is Ascon for 3 nodes and AES for 9 nodes; single-seed data does not establish robust superiority.

Dashboard total_switches, hardcoded qualifications, unsafe dynamic text and placeholder rows are repaired; shared campaign evidence admission includes config/scenario identity and artifact/binary verification. Browser visual acceptance remains pending. Commands, digests, metrics and limitations are in `results/phase_05/repairs_17nov/calibration-acceptance.json` and the closure section of `phase_jouney/final2x_phase_01.md`; usage is in `docs/calibration-v1.md`.

**Stop here: user explicitly deferred items 4–5.** Policy invalid-state/traffic/queue and residual-aware acceptance, small Z1 security/wire/depletion mechanisms, full Phase 4 semantic mapping, human gates and independent reproduction remain open. This does not close every original 2X phase requirement. Original campaign/protocol/pointer and all earlier artifacts remain retained; no Phase 6 or bulk evaluation was launched.


## 17. Items 4–5 bounded execution and remaining residual-aware requirement — 17 November 2026

User authorized policy/queue repairs and small Z1 mechanism validation after the items 1–3 checkpoint. Bounded checks are now executed: **122 unit tests**, ASan/UBSan safety, **1,089 official Ascon vectors**, and **16 final-source root+2 Z1 calibration/mechanism/security runs** pass. Independent reparse checks **44,020 events and 190 artifact/binary hashes**.

Invalid runtime profile/cap indexing is guarded; full-cap prediction respects deadline-first equality; cap reduction uses committed bounded chunks; rate comes from eight observed generation intervals with staleness/startup semantics. Canonical capture processes the initial log event. Static/adaptive Z1 flush lead is uniformly125ms and actual `--preflight-only` table admission is tested before build. Generic OS MAIN startup INFO is suppressed via project config for ROM fit; structured research logs remain required. Old ROM/capture/default-mismatch failures and source cohorts remain preserved.

Qualified P1 functional proof: 48/48 readings and 26/26 packet joins, both AEAD profiles on authenticated wire traffic, 4 logged versus 2 actual wire profile changes. Independently frozen 4.093-J sensor budgets produced terminal depletion/removal with zero post-death activity. B3's finite-budget threshold transition is verified separately. All three attack fixtures rejected 8/8 injections; all three reset fixtures had40 post-reset probes and zero acceptance. The bottleneck control's cutoff is verified, but service failed before death; no causal lifetime benefit is claimed.

**R04 residual-aware P1 remains OPEN.** Scenario-level network costs are not a validated local battery forecast; do not claim residual-aware P1 or energy/lifetime superiority. Changing-workload on-mote validation, isolated transition-energy calibration, full Phase 4 semantic acceptance, human review and independent reproduction remain pending. Existing 9-node tables are historical and need new-source qualification before future use. No 9-node/scaling/comparative or Phase6 campaign was launched.

Details: [policy/mechanism report](phase_jouney/final2x_policy_mechanism_17nov.md), [policy contract](docs/policy-contract.md), and `results/phase_05/mechanism_17nov/mechanism-acceptance.json`. Stop at this bounded checkpoint; the complete original 2X phase is not declared finished.
