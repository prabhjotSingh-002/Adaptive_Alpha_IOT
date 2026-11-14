## Follow-up repair implementation

- Dynamic-cap validation now follows per-node POLICY state, checks profile consistency and retains static limits. Protected two-reading POLICY→TX fixture passes; lowering the policy cap rejects it. 19 metrics host tests pass; log: results/priority_repairs/followup/metrics.log. An initial fixture failed because its RX profile identity did not match TX; corrected the fixture to protected AES with explicit context/authentication events.
- Added pre-generation policy integer/range/threshold/cost-shape validation; imported calibration run IDs, manifest/summary hashes, status and seed are checked. Full target/model compatibility of imported tables still needs completion; current status explicitly says compatibility pending.
- Missing costs/default calibration are explicitly qualified in resolved config. Existing safe fallback remains. No new calibration run performed.
- Shared comparison guard rejects mixed source/config cohorts and repeated mode/seed cells for analysis/plots. Figure/analysis source hashes and missing-pair counts recorded. Dedicated negative fixtures for the new shared guard remain needed.
- Added POLICY_TIME rtimer telemetry around decision and application; parser/summary expose time/sample count. It is not an energy measurement and does not separately isolate switching cost. Timing has not been built/validated on the mote; short rtimer interval/wrap assumptions remain to verify when phase validation is authorized.
- GUI desktop inspection: Wayland/KWin, no open Cooja window. Added software-rendering JVM flags and propagate nonzero GUI exit. Blank-window resolution remains unverified; no GUI/simulation launched.
- No Phase 4/5 validation or Phase 6 work executed. Remaining nondeferred closure includes calibration target/model compatibility, guard tests, firmware compile/timing checks and actual GUI verification.

# Last Astra check — current issues and Phase 6 execution priorities

Date: 14 November 2026
Scope: code/evidence audit and work ordering. This document does not certify a phase as complete or authorize starting the next phase. This update changes documentation only; no new simulation or test was executed.

## Follow-up inspection — unresolved integration gaps

Rechecked all ten source hashes against results/priority_repairs/repair-evidence.json: all match. Existing recorded 19 C-policy + 3 host checks remain the same-source host evidence; no new phase validation or simulation ran.

**New P0 finding:** host/metrics.py TX validation still enforces `count <= cap`, while configs/phase5.json starts B6/P1 at cap 1 and host/run_experiment.py passes that effective cap to summarize(). Firmware now changes queue.cap dynamically. A real two/four-reading policy batch will therefore fail the static count check. Repair must validate against actual per-node policy state and payload bounds, while preserving strict static-mode checks. Add a shared integration fixture covering POLICY → TX; the existing 22 tests do not cover this.

Other remaining code work: validate policy numeric types/ranges and threshold ordering before generated writes; verify imported calibration source hashes/config/model compatibility rather than only nonempty lineage; explicitly handle/label unavailable P1 costs and uncalibrated B6 defaults; finish cohort controls across descriptive statistics and plots (currently grouped by mode, potentially pooling incompatible cohorts), record missing pairs and exact figure lineage. Actual overhead instrumentation and GUI diagnosis/verification remain open.

Firmware initialization, uint64 thresholds, first-action switch exclusion, production-C test dispatch and paired-difference bootstrap repairs are present. Their presence does not qualify the whole application. Phase 4/5 validation remains deferred by user; Phase 6 remains unstarted.

## Repair checkpoint — host fixes, validation deferred by user

Current instruction: resolve priority code errors; do not run Phase 4/5 validation or start Phase 6.

- R01: initialized sensor policy configuration; thresholds widened to uint64_t (6e9 exceeds uint32_t); optional `--policy-cost-table` loads isolated calibration data and records its hash. No historical unqualified table injected; absent costs retain safe P1 fallback.
- R02: replaced Python mirrors with ctypes calls to production policy.c. 19 targeted C host tests passed in the pinned container.
- R03: B6 selects target cap before enqueue; B6/P1 filter batching against configured rate/deadline, P1 amortizes transition cost over declared dwell horizon without overflowing cost addition. First policy assignment is excluded from switch counts. Actual network behaviour remains unvalidated.
- R04: explicit calibration seed required; duplicate/mixed cohorts fail; software AES/accounting evidence required; source manifest/summary hashes retained. New valid calibration remains deferred.
- R05: analysis joins seed/cohort identities and resamples paired differences; rejects duplicate cells and unqualified historical policy runs. Plot loader rejects old uninitialized-policy and nonfunctional runs. Broader plot cohort/figure provenance work remains open.
- R06: historical completion claims superseded by this checkpoint. Raw results/evidence were preserved.
- R07/R08: Phase 4/5 validation explicitly deferred. No Cooja run launched.
- R09: actual decision/switch overhead measurement remains open; no measured value claimed.
- R10: GUI issue remains open; display verification not performed.
- Phase 6 remains unstarted. Runtime policy identity/overhead telemetry and comprehensive calibration/config/plot guards still require further work; this is not full audit closure.

Host initially lacked GCC; direct policy test failed before running tests. Pinned container was used successfully. No host packages installed.

## Authority and reading order

1. [Project rules](AGENTS.md).
2. [Original master](PLANS/MASTER_IMPLEMENTATION_PLAN.md) and [decision review](PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md). These remain authoritative and unchanged.
3. [Consolidated Phase 4/5/6 roadmap](agentGuidance/phase_4_5_6.md), especially F4/F5 acceptance requirements, F6.1–F6.7 and the master-coverage audit.
4. [Phase 4 plan](PLANS/PHASE_04_IMPLEMENTATION_PLAN.md), [repair plan](PLANS/PHASE_04_PROBLEM_RESOLUTION_PLAN.md), [Phase 5 plan](PLANS/PHASE_05_IMPLEMENTATION_PLAN.md).
5. [Journey index](phase_jouney/README.md), current journals, actual source and per-run evidence.
6. This audit, then historical context files. Resolve contradictory completion statements against requirements, code and actual logs.

The user moved guidance documents into `agentGuidance/`. Historical relative links may now be stale. Preserve original plans, all root `tmp/` records and failures. A newer Markdown filename does not override the master or establish a passing gate.

## Main conclusion

Phase 6 still requires implementation, qualification, research experiments and release work. Earlier claims in PHASE6_CONTEXT.md that no firmware changes are needed and all policy logic is complete are contradicted by the inspected code. Phase 5 integration repairs and inherited Phase 4 qualification must precede final research runs. Successful transport/security pilots do not prove that intended adaptive decisions actually ran.

## 1. Priority table — repairs and inherited prerequisites

P0 blocks trustworthy adaptive/comparative conclusions. P1 blocks required qualification or experiment readiness. P2 blocks final reproducibility/release. All required rows remain required regardless of priority.

| Order / priority | ID | Work | Files / evidence | Completion criterion |
|---|---|---|---|---|
| 1 / P0 | R01 | Initialize policy state from resolved configuration and validated cost table | firmware/sensor/sensor.c; firmware/policy/policy.h; host/run_experiment.py | Thresholds, B6 profile, deadline, payload, dwell, margins and costs reach actual C state; runtime identities match; real expected actions observed |
| 2 / P0 | R02 | Replace Python-mirror-only policy verification with shared production C tests | tests/unit/test_policy.py; firmware/policy/policy.c | Tests compile/call actual policy.c; boundaries, fallback, integer limits and switching exercised; integration catches omitted initialization |
| 3 / P0 | R03 | Complete B6/P1 decision semantics and accurate switch accounting | policy.c; sensor.c; host/metrics.py | B6 can accumulate and batch in actual traffic; P1 respects declared traffic/deadline constraints and saving horizon; initialization is not counted as a cipher transition |
| 4 / P0 | R04 | Repair calibration eligibility, seed separation and firmware cost loading | host/calibrate.py; results/phase_05/cost_table.json | Compatible qualified runs only; unique experimental units; separate calibration seeds; source IDs/hashes retained; table loaded and identified at runtime |
| 5 / P0 | R05 | Correct analysis pairing and comparison eligibility | host/analysis.py; host/plots.py; analysis wrappers | Same seed/scenario pairs joined explicitly; paired bootstrap over differences; duplicate/missing/incompatible runs handled; statistical fixtures pass |
| 6 / P0 | R06 | Correct unsupported completion and causal explanations | agentGuidance context/status files; Phase 5 report/evidence | Reports distinguish actual fallback from working adaptation; historical raw evidence preserved; affected claims marked unqualified |
| 7 / P1 | R07 | Close seven recorded Phase 4 validation groups | phase_jouney/phase_04_leftover.md; host/validate_phase4.py | 4000 ms and 47-byte boundaries, 125/250 ms depletion sensitivity and three four-arm lifetime seed groups have qualified evidence or explicit failures |
| 8 / P1 | R08 | Revalidate repaired Phase 5 policies and shared paths | Phase 5 config, firmware and run evidence | Actual profile/cap changes, security/reset continuity, resources and matched pilots verified; root+9 research pilot requirement accounted for |
| 9 / P1 | R09 | Measure policy decision and transition overhead | policy/sensor telemetry; parser/metrics | Actual timing/cost evidence, valid local features and logging overhead available; no assumed zero overhead |
| 10 / P1 | R10 | Resolve white Cooja GUI and verify presentation | GUI runner; COOJA_GUI_PRESENTATION_GUIDE.md | Visible controls/network and usable live procedure verified on the user's display; headless success alone does not close this |
| 11 / P2 | R11 | Synchronize documentation navigation after folder move | agentGuidance/, PLANS/README.md, journey/docs indexes | One clear current entry point; links resolve; historical snapshots labelled; original master/tmp records preserved |

R05 tooling can progress while R01–R04 are repaired. Required regressions and calibration must be repeated after changes that invalidate their source/config cohort. Avoid rerunning unrelated matrices without a dependency reason.

## 2. Confirmed findings and evidence limits

### R01 — configuration never reaches policy state

`firmware/sensor/sensor.c` declares `static lab_policy_state policy_state;` and passes it to B3/B6/P1. The inspected source has no initialization of its configuration/cost fields. Static storage begins zeroed. Generated configuration macros alone do not populate a C struct.

Selected saved runs corroborate the resulting behaviour:

| Mode | Run under results/phase_05/ | Observed policy | Interpretation |
|---|---|---|---|
| B3 | 20261114T120117290160Z-B3-8 | Profile 1 / cap 1; first reason 2 | AES selected; this does not validate configured nonzero thresholds |
| B6 | 20261114T121756262964Z-B6-8 | Profile 1 / cap 1; first reason 1 | Fallback, despite configured intended Ascon profile 2 |
| P1 | 20261114T122031479887Z-P1-8 | Profile 1 / cap 1; first reason 9 | No feasible costed action; missing loaded costs, not demonstrated excessive switching cost |

Evidence inspected: each run's `summary.json` policy fields and first POLICY event in `events.jsonl`. This is a selected-run audit, not a hash certification of every historical artifact. B3/P1 summaries count eight switches; the current first-assignment comparison against zero previous values can count startup assignments as switches.

### R02 — tests do not execute production policy C

`tests/unit/test_policy.py` contains a C build helper, but `setUpClass` sets `cls.lib = None` and explicitly uses a Python mirror. Passing those 17 tests does not establish actual policy.c or sensor integration correctness. Keep useful fixtures, but execute the shared production C and actual application paths.

### R03 — decision logic requires integration work

B6 begins with cap 1 and requires at least two queued readings before increasing cap. Immediate cap-1 flushing may prevent reaching that condition; validate the full generator/queue/service ordering and repair it. This is an integration concern to demonstrate, not a claim that every possible workload fails.

P1 currently filters chiefly by payload fit and nonzero cost cells. Complete declared traffic/deadline feasibility, valid local-feature handling, prediction horizon and transition-cost units/overflow checks. `rate_hz_x100` is hardcoded to 100 in the sensor. Measure decision CPU time and transition overhead; security must remain active for all choices and fallbacks.

### R04 — calibration is not independently qualified

`host/calibrate.py` broadly collects passed Phase 4 energy summaries without complete source/backend/scenario qualification or unique-seed control. Saved `cost_table.json` contains `source_seed_filter: null`, 21 source samples, and unequal per-mode counts. A calibration seed mentioned in another document does not establish that those samples use it. The table does not retain the complete source-run lineage needed to audit selection.

Rebuild calibration from explicitly eligible, compatible, separately seeded runs. Record selected/rejected attempts and hashes. Unknown cost cells stay unavailable. Do not choose a favourable cipher from mixed exploratory/test populations.

### R05 — paired statistics label is incorrect

`host/analysis.py::_paired_diff` independently resamples both arms regardless of equal sample lengths, then can label equal-sized pilots as paired. It does not join observations by seed/scenario. Fix pairing before interpreting comparative confidence intervals.

Analysis/plot loaders group broad passed-run collections; duplicates, model/backend/source changes and experimental purposes need explicit eligibility controls. Current percentage differences across Phase 4/5 are not final qualified adaptive-policy conclusions. Preserve negative results once validity is established; low PDR alone is an outcome, not automatic grounds to discard a valid run.

### R07 — inherited qualification remains open

Recorded deferred groups: two boundary groups, two sampling/depletion groups and three four-arm lifetime groups. Verify current manifests before executing to avoid duplicate work. Prove terminal radio/forwarding cutoff, final accounting, survivor evidence, FND/HND and functional-lifetime censoring. The 47-byte protected budget fits two 10-byte readings: 47 - 11 header - 16 tag = 20 bytes. Historical text calling this a one-reading budget is incorrect.

## 3. Separate table — Phase 6 implementation and acceptance

| Package / priority | Implement or execute | Existing foundation | Remaining acceptance / output |
|---|---|---|---|
| F6.1 / P1 | Network/scenario scaling | Nine-mote saved scenario; runner slices it; maximum eight clients | Generate grid/bottleneck 10/20-total-node scenarios; root+9/root+19 provisioning, routing, replay/state dimensions; RAM/stack and traffic validation |
| F6.2 / P0 before main runs | Freeze research protocol and matrix | Master and Phase 4 protocol | docs/experiment-protocol.md, configs/phase6.json, seed registry; frozen endpoints, thresholds, budgets, rates, exclusions, comparator, censoring and analysis |
| F6.3 / P1 | Resumable serial matrix execution | Canonical runner, attempt records, shared lock and manifests | Phase 6 support; thin scheduler or canonical extension; identity/hash-verified reuse, interruption recovery, immutable failures, matrix completeness |
| F6.4 / P1 | Final comparative, lifetime, stress and ablation runs | Static/adaptive scaffolding and exploratory pilots | Qualified seven-mode paired matrix; loss/bursts/heterogeneous budgets/reboot/route recovery; cipher/batching/hysteresis/transition-cost/deadline ablations with security preserved |
| F6.5 / P0 correctness, P1 completion | Correct statistics and research figures | Descriptive statistics, bootstrap and basic multi-arm charts | Genuine paired inference; missing-pair policy; survival/RMST with censoring; energy–latency, service, component/node energy, overhead, ablation/sensitivity figures and exact source hashes |
| F6.6 / P2 | Reproducibility tooling and independent check | Pinned official dependencies and saved evidence | Locked analysis environment, dependency restore, CI/shared-C checks, archive verification, documented real second-person clean reproduction |
| F6.7 / P2 | Final release and claims audit | Existing technical docs and partial phase reports | Root README, quickstart/demo, methods/manuscript draft, limitations, complete Phase 6 journal/report/problem record and results/phase_06/phase6-evidence.json |

### Scaling requirements

10 total nodes means root + 9 sensors: 18 dual-profile sender contexts. 20 total nodes means root + 19 sensors: 38 contexts. Increasing the current 16-context ceiling to 32 is insufficient for 20 total nodes. A constant-only edit is not acceptance: storage dimensions, stack, radio buffers, routing capacity, key provisioning and actual delivery must fit and work. If Z1 cannot support the required target, retain the failure and resolve target/model implications explicitly.

### Frozen experiment scope

Proposed full matrix: 7 modes × 2 topologies × 2 sizes × 2 rates × 10 paired seeds = 560 runs for one declared purpose. A separate full lifetime matrix adds cost. Measure throughput/storage before freezing the actual scope. Any reduction must be explicit and justified before viewing main outcomes; an eight-client subset does not silently satisfy the full master scope.

Proposed held-out seeds in the consolidated roadmap are 423456–423465. Verify they remain unused before freezing. Calibration, development and evaluation must stay separate. Preserve valid negative results, undefined energy when delivery is zero, failed instrumentation and missing pairs with their correct classifications.

### Tooling absent at this audit

- docs/experiment-protocol.md
- configs/phase6.json
- host/run_matrix.py (a canonical-runner extension is an acceptable implementation alternative)
- host/requirements.lock
- .github/workflows/ci.yml
- README.md
- docs/policy.md
- docs/reproducibility.md
- results/phase_06/ directory/evidence ledger

Current runner accepts phases 2–5. Merely writing phase6.json does not implement Phase 6 execution. Survival analysis needs a validated method and tests; installing scipy alone is neither necessary proof nor completion.

## 4. Documentation corrections to make during implementation

| Existing claim | Correct interpretation |
|---|---|
| PHASE6_CONTEXT.md: no new firmware work | Firmware integration/scaling work is required by observed gaps and the consolidated roadmap |
| Policies complete; tests validate actual C | Mirror tests and fallback pilots do not close shared-C/integration acceptance |
| P1 did not switch because overhead exceeded savings | Selected observed run reports no feasible action; costs are not loaded into policy state |
| B6 used calibrated Ascon | Selected observed run used AES fallback |
| 32 contexts support proposed scaling | Root+19 sensors with two profiles requires 38 contexts |
| Equal sample counts imply paired statistics | Seed/scenario identity must be joined; current bootstrap is independent |
| Phase 4 complete with seven cases deferred | Required deferred acceptance remains open; preserve exact scope and reasons |
| Poor PDR results can simply be excluded | Distinguish genuine performance failure from invalid instrumentation; predefine handling and retain valid negative results |
| Decide full matrix after looking at minimum-matrix results | Freeze research scope independently of favourable outcomes; separately labelled development pilots may inform feasibility |

Do not overwrite original raw logs/manifests to manufacture passing evidence. Add qualification/exclusion records and corrected summaries with provenance. Synchronize historical-navigation links without deleting preserved records.

## 5. Execution order and stop conditions

Policy integration + production-C tests → valid isolated calibration → affected Phase 4/5 regressions and qualification → network scaling → protocol/matrix freeze → resumable runner validation → frozen experiments → statistics/figures → reproducibility/release.

Statistics correctness and documentation navigation can proceed independently before final runs. Close and report each phase, respecting the project rule to stop at phase boundaries for user instruction. Human reviews, GUI verification and independent reproduction remain pending until actually performed. No performance gain, publication, full phase completion or human sign-off is promised by this plan.

## 6. Audit provenance

This document records the preceding code/evidence inspection requested by the user. On creation, rechecked the new agentGuidance location and unchanged presence of the policy-state, Python-mirror and independent-bootstrap issues. Source and results can change; verify drift before implementing. No fresh build/test/simulation was run for this documentation task. Existing recorded runs retain their original source/config scopes.
