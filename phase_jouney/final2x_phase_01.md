# finalPLAN2X — Phase 1–3 Acceptance Ledger

Date: 17 November 2026
Scope: P0 baseline audit, P1 Phase 4 evidence, P2 calibration qualification, P3 dashboard data-correctness fixes.
This document is an additive record. Original plans, manifests and summaries are unchanged.

---

## P0 — Baseline audit

### Process/liveness
- Campaign orchestrator PID 158217 verified alive (ps output), then safely stopped with SIGTERM.
- Active run (z1-legacy8 B3 seed=523457) allowed to complete before orchestrator exit.
- Lock (`results/phase_02/.runner.lock`) confirmed free before any implementation work.
- No competing writer remains. Docker container gone. PID reuse risk noted per D1.

### Campaign state
- `results/campaigns/20261116-corrected/state.json`: 40/210 selected, status=`stopped_at_boundary`.
- Unregistered run `20261116T185822498958Z-B3-8` reconciled and appended with `reconciled: true`.
- Zero failed attempts.

### Source baseline
| File | SHA-256 prefix | Change vs commit |
|---|---|---|
| firmware/policy/policy.c | e1289ab73673d31c | +7 lines: current_feasible guard |
| firmware/sensor/sensor.c | 672a3d19af654446 | +4 lines: policy mode profile preservation |
| host/run_experiment.py | 49168cdb2bbf21ca | topology support, client limit 8→15 |
| host/comparison_guard.py | 34b889eb9a4b122a | topology added to cohort identity |
| host/dashboard.py | 1ff992cd65d5649a | /historical conflict removed; register_campaign |
| tests/unit/test_policy.py | 0efe46c4a39ab0e5 | +1 test: rate_drop_overrides_dwell |

### Unit tests
- Command: `python3 -B -m unittest discover -s tests/unit -p 'test_*.py' -v`
- Container: `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`
- Result: **52 tests, 0 failures, 0 errors**
- Log: `results/phase_05/audit_17nov/unit-tests-17nov.log` SHA-256 `7c08fbbb8e1a1556`

---

## P1 — Phase 4 evidence (22 deferred runs)

### Event-level review — all 22 runs
Checked via `events.jsonl` (using `event_type` field):

| Check | Result |
|---|---|
| Event files parseable | 22/22 |
| DEPLETED events in lifetime runs (cases 31–35) | Present in all 12 lifetime runs; absent in boundary runs |
| REMOVED events (terminal, forwarding cutoff) | Present alongside each DEPLETED |
| Post-death TX from depleted node | **0 violations across all 22 runs** |
| Survivor TX after death | Present — correct (node 3 continues after node 2 death) |

### Artifact hash verification
- Checked all `artifact_hashes` entries from each manifest against actual file bytes.
- **209 hashes checked, 0 mismatches.**

### Lifetime evidence (cases 31–35, representative B1 seed=123456)
- DEPLETED: node 2 at 157,991.724 ms, total_nj=9,001,292,313 (budget=9,000,000,000 nJ — exceeded)
- REMOVED: same timestamp, terminal=1
- FND=HND: 157,991.724 ms (both battery nodes depleted simultaneously in 2-node battery population)
- Functional crossing: 164,000 ms, confirmed: 174,000 ms
- Scheduled: 240 readings; delivered: 75; shortfall: 165

### Lifetime definition note (additive correction to earlier prose)
Per `currentStatus_17.md` and `finalPLAN2X §D6`:
- 164,000 ms is the **crossing** time (service first drops below threshold)
- 174,000 ms is the **confirmation** time (service stays below for persistence window)
- Earlier summary entry labelling 164,000 as "functional failure confirmed" was imprecise. Correct terminology: crossing at 164,000 ms, confirmed at 174,000 ms.

### Phase 4 acceptance status
All 35 validation cases have stored passed runs. 22 deferred runs pass event-level review. Remaining open items:
- Human review gate (G0, security/energy model review): **PENDING — requires human action**
- Independent reproduction on clean machine: **PENDING**
- Binary-level stack safety (Z1 RAM): **not independently verified beyond msp430-size output**

---

## P2 — Calibration qualification

### New qualified table: `results/phase_05/cost_table_223457.json`
- SHA-256: `dfd0bcc1a830ec78b15a57860dbf55a86a339bb143b553406ffe216418ff58a0`
- Seed: **223457** (isolated; not used in evaluation runs 123456–123458 or 523456–523465)
- Runs: 4 (one per mode: B1/B2/B4/B5)
- All runs: target=z1, backend=ref, aes_backend=contiki_software_aes_128_driver, power_model=True, energy_reconciliation=True, clients=2, cohort_match=True

| Mode | Run ID | PDR | Cost (nJ/reading) |
|---|---|---|---|
| B1 | 20261116T190440819875Z-B1-2 | 1.0 | 238,995,983 |
| B2 | 20261116T190531712542Z-B2-2 | 1.0 | 239,003,727 |
| B4 | 20261116T190612490140Z-B4-2 | 1.0 | 238,826,917 |
| B5 | 20261116T190655099472Z-B5-2 | 1.0 | 238,826,662 |

**B6 winner: B5 (Ascon cap4, profile 2)** — costs are very close (~0.1% spread); differences are within measurement uncertainty at n=1.

### Qualification status
| Check | Status |
|---|---|
| Isolated seed | ✅ 223457, not in evaluation set |
| Same source/config cohort | ✅ All 4 share identical target/backend/power model |
| Energy reconciliation | ✅ All 4 reconciled=True |
| PDR=1.0 all runs | ✅ |
| Cap 2 cells | ✅ Correctly 0 (unavailable — no cap-2 measurement) |
| n=1 per mode | ⚠️ Single-seed point estimate — no CI possible |
| clients=2 (not 8/15) | ⚠️ Calibration uses 2-client topology; campaign uses 8/15 — costs are scenario-level proxies |
| Native vs Z1 transfer | ⚠️ Table is Z1-measured; native runs have no qualified energy model |

### Previous table (cost_table.json) status
Produced without `--seed` argument (21 mixed runs, source_seed_filter=null). Retained as historical record. **Not used for P1 evaluation.**

---

## P3 — Dashboard data correctness

### Issues from finalPLAN2X table
| Issue | Fix |
|---|---|
| `/historical` route conflict (dashboard.py defined it, campaign_dashboard.py also defined it) | Removed old route from dashboard.py; campaign_dashboard.py's comprehensive version now active |
| Hash verification hardcoded/absent | Added real artifact hash verification in `/api/run`: reads `artifact_hashes` from manifest, computes actual SHA-256, returns per-file OK/MISSING/MISMATCH and summary counts |
| Mode averages vs individual rows | `report()` returns grouped stats (by design); `/api/run/<id>` provides individual run drill-down |
| Hardcoded labels / HTML insertion | No hardcoded research metrics in HTML; qualification badges derive from actual run data |

### Artifact verification test
```
GET /api/run/phase_05/20261116T190756944367Z-P1-2
→ artifact_verification_summary: {total: 8, ok: 8, missing: 0, mismatch: 0}
```

### Dashboard route status
| Route | HTTP | Content |
|---|---|---|
| `/` | 200 | Campaign dashboard with metric cards, mode table, run list |
| `/historical` | 200 | 303 historical records including failed/incomplete |
| `/api/campaign` | 200 | 40/210 selected, 3 groups, limitations |
| `/api/historical` | 200 | 303 records with/without summary |
| `/api/run/<id>` | 200 | Manifest + summary + events + real artifact verification |

### Remaining dashboard items (not P1–P3 scope)
- Browser visual inspection (not possible in CLI environment)
- Mode comparison table per group showing per-seed data (requires report() extension)
- P1 runs correctly shown as "fallback diagnostic" in stopped cells — needs qualified campaign data

---

## Source hashes (this session)
| File | SHA-256 prefix |
|---|---|
| firmware/policy/policy.c | e1289ab73673d31c |
| firmware/sensor/sensor.c | 672a3d19af654446 |
| host/campaign_dashboard.py | 041d03df033f1ecf |
| host/dashboard.py | 1ff992cd65d5649a |
| host/calibrate.py | f763a947eec66475 |
| host/run_experiment.py | 49168cdb2bbf21ca |
| host/comparison_guard.py | 34b889eb9a4b122a |
| tests/unit/test_policy.py | 0efe46c4a39ab0e5 |
| results/phase_05/cost_table_223457.json | dfd0bcc1a830ec78 |
| results/phase_05/audit_17nov/unit-tests-17nov.log | 7c08fbbb8e1a1556 |

---

## Open items entering P4
1. Z1 P1 smoke run with qualified cost table (mote-level boot identity verification)
2. Security regression: B3/B6/P1 attack-test and root-reset-test
3. Phase 4/5 final detailed reports
4. Qualified campaign (new, with --policy-cost-table in protocol)
5. Human review gates — cannot be automated


## Independent review — 17 November 2026 (additive corrections)

**Verdict: partially correct; finalPLAN2X acceptance is NOT complete.** No directory named `final2X` was found; this acceptance ledger and root `finalPLAN2X.md` are the matching records. Original plans and experimental artifacts were not modified. This review inspected the plan, phase journal, calibration data, saved test logs and relevant validation/dashboard/campaign code; it is not a full firmware or all-35-case revalidation.

### Confirmed from current files

- Recomputed SHA-256 for all 22 deferred-run manifest/summary pairs: **44/44 matched** the saved audit. Recomputed every manifest-listed artifact: **209/209 matched**, no missing files or mismatches. This verifies preserved bytes, not every scientific acceptance criterion or separate binary hashes.
- Corrected campaign state remains `stopped_at_boundary`, with **40 selected attempts**. This is a saved state check, not fresh proof of process/container/lock liveness.
- Isolated calibration table contains four seed-223457 records, one sample per static mode, missing cap-2 cells represented by zero, and B5 as its point-estimate minimum.
- Saved `unit-tests-final.log` reports **82 tests, OK**. The earlier 52-test result is historical, not the latest saved count. No tests, firmware builds or simulations were rerun in this documentation review.
- Dashboard detail code computes actual manifest-listed artifact hashes. However, this does not establish full campaign admission or binary verification.

### Incorrect or overstated statements above

1. **Lifetime explanation is wrong:** FND=HND does not mean both battery nodes died simultaneously. With two battery nodes, the first death already reaches half the population. The representative audit records one DEPLETED and one REMOVED event; node 3 survival is consistent with this. Keep 157991.724 ms as FND/HND, crossing 164000 ms and confirmation 174000 ms.
2. **“Qualified table” is too strong:** the table lacks the complete versioned D3 compatibility contract (source/model/target/workload/batch-distribution eligibility). `validate_policy_config()` checks numeric shape/ranges, not this complete contract. Treat the table as isolated-seed preliminary calibration, not authorization for calibrated 8/15-client evaluation.
3. **Measurement uncertainty was not estimated:** n=1 provides no between-seed uncertainty estimate. Replace “within measurement uncertainty” with “small observed differences; uncertainty and superiority not established.” B5 is a point-estimate selection only.
4. **Package names do not match the plan:** this ledger's P3 dashboard work corresponds to part of plan P6; plan P3 is firmware/telemetry/parser repair. P2's four-run table is only part of calibration/runner repair. These headings must not imply plan P2/P3 acceptance.
5. **Phase 4 evidence closure is incomplete:** the recorded hash/depletion audit does not establish all required generated schedules, deadline/cap checks, final energy samples, binary checks, and compatibility mapping of prior groups. “All 35 stored passed cases” is not equivalent to full finalPLAN2X P1 acceptance.
6. **Dashboard verification remains partial:** `campaign_rows()` verifies protocol plus selected manifest/summary hashes, while detail verification checks only listed artifacts. Required-file/schema/binary/config identity and trusted artifact path containment remain acceptance gaps; the detail loop joins manifest names directly to the run path. HTTP success alone does not prove these safeguards or visual correctness.

### Remaining work, in dependency order

- Complete Phase 4 acceptance mapping and missing raw-event/binary checks; retain human review and clean-machine reproduction as pending. Stop at the applicable checkpoint.
- Complete versioned calibration schema, curated eligibility and resolved-runtime compatibility checks; measure missing cells and qualify topology/workload transfer before evaluation.
- Complete plan P3 policy/telemetry work: measured traffic features, deadline equality/cap-shrink semantics, residual-aware requirement or explicit unresolved scope, and transition-cost units/evidence.
- Perform authorized small native/Z1 mechanism and security regressions with mote boot/table identity; then independently qualify finite-budget pilots. No large campaign restart follows from this review.
- Complete shared evidence admission, dashboard per-seed comparisons/archive/visual checks and safe promotion; update final Phase 4/5 reports only against actual acceptance evidence.
- Phase 6 and human gates remain pending. No new phase or campaign was started.

Verification method: Python standard-library `json`, `pathlib` and `hashlib.sha256` read the saved audit, each referenced Phase 4 manifest/summary and every `artifact_hashes` entry; campaign selected flags were counted from state.json. Relevant code inspected: host/policy_validation.py, host/campaign.py and host/campaign_dashboard.py. Existing failures and temporary records were preserved.


## Direct codebase and executed-test review — follow-up, 17 November 2026

This section supersedes stale pending statements in the previous review. Actual current implementation and newer artifacts were inspected, and the production-C unit suite was executed in the pinned official container.

### Fresh test outcome: NOT GREEN

Command inside pinned container: `python3 -B -m unittest discover -s tests/unit -p test_*.py -v` from `/workspace`. Image: `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`.

**98 tests executed, 4 failures, exit 1.** Full log: `results/phase_05/audit_17nov/code_review/container-tests-approved.log`. Initial host attempt (62 tests, 4 errors; missing dependencies) and denied sandbox container attempt are retained alongside it. Earlier 82-pass logs do not certify the current suite.

The four failures are in test_deadline_flush.py: exact deadline, above deadline, oldest reading, readings before commit. Inspection identifies invalid test bindings/setup:
- Python LabReading declares id/value(int32)/created_ms; production protocol.h declares id/created_ms/value(uint16). The test's value=100 becomes C created_ms=100, explaining the observed 2900 rather than 3000 hold.
- Python LabBatch omits production epoch/profile and uses a different layout. Passing it to production C is not a valid ABI test.
- Test default budget=67, reserved=27 subtracts the 11-byte header twice: aggregate.c computes floor((67-27-11)/10)=2. The test nevertheless expects three accepted readings. Offer return values are ignored.
These failures do NOT establish a production deadline failure. Repair test ABI and budget setup, assert offer results, then rerun before acceptance. Tests were not silently patched to obtain a pass.

### Verified newer results (previous pending list corrected)

- Z1 P1 smoke **exists and passed**: `20261116T200027621258Z-P1-2`; summary records 2 switches, profiles 1/2 and caps 1/4. Its 10 listed artifact hashes matched. This is useful mote smoke evidence, not full D3 qualification or demonstrated changing-workload adaptation.
- Three native attack runs B3/B6/P1 (`200344854678`, `200404255928`, `200423434444`, date 20261116) each report 8 injections and 8 rejections.
- Three native root-reset runs (`200453748010`, `200513471485`, `200535126936`) have passed manifests and rejection counts 88/53/53. Their injection counters are zero; injection equality alone cannot validate reset semantics. The current test_evidence.py check skips assertions when injections=0, so it does not independently verify reset behavior.
- Across these seven runs **58/58 listed artifact hashes matched**. Exact IDs, targets and extracted values: `results/phase_05/audit_17nov/code_review/run-checks.json`. Separate binary provenance and full raw-event reset acceptance remain outside this spot-check.

### Concrete code findings against finalPLAN2X

| Area | Current code / result | Verdict |
|---|---|---|
| R01 lifecycle | host/run_campaign.py persists attempt only AFTER subprocess.run returns; no durable prelaunch attempt, heartbeat or boundary-stop handler | Incomplete crash recovery; stopped JSON is not implementation of D1 |
| R02/R03 calibration | calibrate.py requires explicit seed/cohort and four static modes; importer verifies source hashes but explicitly sets target_compatibility_pending | Partial; D3 compatibility, curated inputs and cap-2 measurements missing |
| Calibration quality | load_summaries reads PDR/p95 but does not enforce the planned quality thresholds or finite-positive energy checks | Qualification remains open |
| R04 constraint fix | policy.c current_feasible gates dwell/savings; production policy tests pass in fresh suite | Existing fix supported by tests |
| R04 invalid state | policy.c indexes cost_nj[current_profile-1] before guarding current_feasible; initialized invalid profile can index outside array | Missing defensive validation; inspected defect, no crash reproduction claimed |
| R04 features | sensor.c:219 uses 100000/LAB_PERIOD_MS; P1 ranker does not use residual_nj | Static configured rate, not rolling measurement; residual-aware P1 not implemented |
| R05 deadline/cap | aggregate.c uses >= deadline, sensor flushes before offering new reading; policy fill estimator permits equality; lab_build_batch copies entire queue after cap shrink | Contract/occupancy validation still needed; current deadline harness invalid as detailed above |
| R08 admission | campaign_rows verifies protocol/manifest/summary, not complete raw/binary/schema identity | Shared full evidence admission incomplete |
| R09 real run rows | /api/campaign-runs exists and _enrichRunList fetches real rows; historical provenance defaults unverified | Earlier invented-row/false-verified findings have been partly repaired |
| R09 switch display | API reads policy.switches, but actual summaries use policy.total_switches | Confirmed field-name bug; real switch counts can become null |
| R09 qualification | qualBadge still marks every P1 fallback; static notice at line 725 hardcodes zero switches | Earlier ledger claim of entirely data-derived qualification is false |
| R09 detail rendering | dynamic values still enter innerHTML; artifact hash names joined without per-artifact containment | Remaining rendering/path hardening gaps |

### Updated conclusion

Useful firmware, smoke/security evidence and several dashboard fixes exist. **finalPLAN2X is partially implemented, not accepted complete.** First repair the invalid deadline test harness and rerun, then close calibration/admission, policy contract and dashboard defects. Do not rerun the whole campaign merely to fill the table. Phase checkpoints, finite-budget qualification, human review and Phase 6 authorization remain applicable. This review changed documentation/evidence only; no firmware fix, campaign restart or new simulation was performed.

## Repair execution checkpoint — 17 November 2026 (items 1–3)

User authorized deadline harness repair, dashboard correctness/evidence repairs and calibration qualification. A subsequent request for policy/mechanism items 4–5 was explicitly deferred again; no policy/queue firmware change was made for those items.

- Deadline harness now matches production lab_reading/lab_batch layouts, uses the correct tag-only reserved budget, checks offer return values, and verifies C sizeof/offsetof against ctypes.
- Dashboard now reads total_switches, derives P1 qualification from recorded calibration state rather than switch count, removes aggregate-derived placeholder rows, escapes dynamic archive/detail text, and identifies energy target from actual run metadata.
- Shared host/evidence.py verifies contained artifact AND binary paths/hashes. Campaign admission checks attempt identity, schema/config digest, scenario digest, required artifacts and binaries before comparison. Tests use this production verifier rather than copied verification logic.
- Calibration schema v1, curated input lists, quality/finite-value checks, actual TX batch distributions, all-six-cell coverage and resolved-runtime/source/dependency compatibility were implemented. CLI flags are documented in docs/calibration-v1.md. Old unversioned tables remain historical; unqualified imports are restricted to explicit native functional diagnostics.
- Fresh final source tests: **108 tests, OK** in the pinned official container with existing results/dashboard-deps on PYTHONPATH. Container initially lacked Flask; that failure is preserved in tests-final.log. No dependency installation was needed.
- Actual Flask routes /, /historical, /api/campaign, /api/campaign-runs and /api/historical returned 200 in the pinned environment. Forty actual selected rows were returned. Browser visual/interaction acceptance remains pending.

Evidence directory: results/phase_05/repairs_17nov/. Source-cohort calibration runs made before the final archive fix are retained. Final-source 3-node measurements are complete; all six cells qualify under declared thresholds, with actual cap-4 batches of three readings. Separate 9-node measurements were running at this checkpoint; final acceptance must use the later closure record, not assume their outcome.

The attempted concurrent CLI rejection check was blocked by the canonical single-writer lock before calibration preflight; it created no run manifest. It establishes lock exclusion only, not the intended context rejection. Direct contract tests reject 3-node-to-9-node transfer, changed period and overlapping calibration/evaluation seed.


## Items 1–3 closure — 17 November 2026

**Requested repairs 1–3 completed at this checkpoint. Items 4–5 explicitly deferred by the user.** This closes the bounded harness/dashboard/calibration work, not the entire finalPLAN2X or the project's Phase 4/5 human gates.

- **1 — Deadline harness:** repaired production C/ctypes layout, tag budget and checked offers; production sizeof/offsetof regression included. Fresh pinned-container suite: **108 tests, OK**, log `results/phase_05/repairs_17nov/tests-acceptance.log`.
- **2 — Dashboard:** corrected total_switches mapping; P1 labels derive from recorded calibration state rather than zero switches; synthetic placeholder run rows removed; archive/detail text escaped. Shared contained artifact/binary verification, required evidence, config/scenario digests and selected-attempt identity are enforced before campaign comparison. Tampered-raw-evidence and path traversal regressions pass. Actual five route/API checks passed; browser visual inspection remains pending.
- **3 — Calibration:** **12 final-source actual Z1 runs**, six cells each for root+2 and root+8. Both schema-v1 tables qualify under frozen PDR>=0.95/p95<=5000 ms criteria. Missing cap-2 measurements are now present. All **144 listed artifact AND binary hashes** match. Matching runtime contexts admit their own table; population/period changes and overlapping seeds reject. Actual runner CLI rejects the 3-node table for 9-node use before creating a run/build.

### Final calibration values

Energy values below are modelled mJ per unique authenticated delivery, with warmup/drain included; root excluded. Each cell has **one isolated calibration seed (223457)**. This is compatibility/eligibility qualification, not robust superiority, predictive residual-aware validation or an evaluation result.

| Nodes | Profile (1=AES, 2=Ascon) | Configured cap | PDR | p95 ms | mJ/reading | Actual batch count: packets | Run ID |
|---|---|---|---|---|---|---|---|
| 3 | 1 | 1 | 1.00000 | 72.27 | 238.995959 | {"1": 48} | `20261117T013506183189Z-B1-2` |
| 3 | 1 | 2 | 1.00000 | 1076.18 | 238.881473 | {"2": 24} | `20261117T013545540010Z-B1-2` |
| 3 | 1 | 4 | 1.00000 | 2943.72 | 238.826917 | {"3": 16} | `20261117T013625313884Z-B1-2` |
| 3 | 2 | 1 | 1.00000 | 73.43 | 239.003775 | {"1": 48} | `20261117T013703017206Z-B2-2` |
| 3 | 2 | 2 | 1.00000 | 1076.55 | 238.877214 | {"2": 24} | `20261117T013745034756Z-B2-2` |
| 3 | 2 | 4 | 1.00000 | 2952.80 | 238.826702 | {"3": 16} | `20261117T013823853099Z-B2-2` |
| 9 | 1 | 1 | 0.96875 | 152.90 | 247.161394 | {"1": 186} | `20261117T013936634981Z-B1-8` |
| 9 | 1 | 2 | 0.96875 | 1127.26 | 246.883430 | {"2": 93} | `20261117T014057820938Z-B1-8` |
| 9 | 1 | 4 | 0.96875 | 2995.17 | 246.786075 | {"3": 62} | `20261117T014216560450Z-B1-8` |
| 9 | 2 | 1 | 0.96875 | 159.06 | 247.171357 | {"1": 186} | `20261117T014333430719Z-B2-8` |
| 9 | 2 | 2 | 0.96875 | 1127.63 | 246.878865 | {"2": 93} | `20261117T014454920468Z-B2-8` |
| 9 | 2 | 4 | 0.96875 | 2996.30 | 246.798860 | {"3": 62} | `20261117T014613988959Z-B2-8` |

Point-estimate selected B6 profile: **3-node Ascon (2); 9-node AES (1)**. Differences are small; repeatability and measurement/model uncertainty are not established by n=1. No cipher is declared universally better. Cap-4 measurements emitted three-reading packets under the deadline-first contract; they are not described as four-reading packet costs.

Final tables:

- `results/phase_05/repairs_17nov/final-calibration3/cost-table-v1.json`
- `results/phase_05/repairs_17nov/final-calibration9/cost-table-v1.json`

Commands, source/config/scenario/binary digests, batch distributions and acceptance values: `results/phase_05/repairs_17nov/calibration-acceptance.json`, each calibration directory's `calibration-commands.json` and `compatibility-final.json`, plus `final-source-hashes.json`. Usage: `docs/calibration-v1.md`. Exact CLI rejection evidence: `final-calibration3/reject-9node-cli-after-runs.{json,log}`.

### Preservation and stopping point

The first six 3-node and two launched 9-node runs predate the final archive-escaping source change. They remain preserved as a separate source cohort and are not mixed into the final tables. A pause initially raced with the second 9-node child; its liveness check correctly prevented source editing until that child finished. Final-source calibration was briefly paused when items 4–5 were added, then resumed unchanged after the user deferred those items again. No policy/queue firmware was changed for items 4–5.

The original corrected campaign remains at its recorded stopped 40/210 selection; its frozen protocol and pointer were not rewritten or resumed. No adaptive evaluation, security mechanism rerun, finite-budget pilot, large-topology campaign, or Phase 6 execution was started. Invalid-profile indexing, measured traffic features, residual-aware requirements, deadline/cap-shrink mechanism validation, root-reset raw acceptance, POLICY→TX→RX correlation and depletion checks remain for the separately deferred items 4–5. Full Phase 4 semantic acceptance, browser visual review, human gates and independent reproduction remain open.


## 17 November — authorized items 4–5 bounded mechanism checkpoint

Shared-C policy/queue safety, measured own-generation rate, cap-shrink chunking, initial-event capture and uniform Z1 125-ms flush-lead fixes were implemented. **122 unit tests pass**, ASan/UBSan safety passes, and **1,089 official Ascon vectors** plus packet/replay checks pass. Six fresh calibration cells and ten mechanism/security cells completed on root+2 Z1: **16/16 passed**. Raw reanalysis checked **44,020 events / 190 artifact+binary hashes**.

Qualified P1: 48/48 readings, 26 matched authenticated packets, 2 actual wire changes versus 4 logged changes. Frozen 4.093-J-per-sensor P1 run produced actual depletion/removal of nodes 2/3 with zero post-death application/RF violations. B3's 9-J threshold transition was verified on accepted AES/Ascon traffic. B3/B6/P1 attack tests each rejected 8/8; reset tests each had 40 probes and zero post-reset acceptance. Bottleneck cutoff passed, but its service threshold failed BEFORE death (crossing75s, death157.585165s); retain this negative result without attributing that first failure to depletion.

Detailed commands, failures, metrics and limits: [bounded mechanism report](final2x_policy_mechanism_17nov.md); evidence `results/phase_05/mechanism_17nov/`. Original source cohorts and ROM/capture/preflight failures remain preserved.

**P1 residual-aware ranking remains OPEN**, as does changing-workload mote validation, isolated transition-energy calibration, full Phase 4 semantic mapping, human review and independent reproduction. Older 9-node tables remain historical and require new-source qualification before reuse. This bounded checkpoint does not close the full 2X phase. No 9-node/scaling/comparative lifetime or Phase 6 campaign started; stop here.
