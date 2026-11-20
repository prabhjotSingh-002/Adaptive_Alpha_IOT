# Phase journey

This folder records **what happened in each phase**: implementation, commands, tests, errors, fixes and reports. For **what to implement next**, use the separate [planning index](../PLANS/README.md). The master plan owns scope, deadlines, deliverables and gates.

| Phase | Scope | Status |
|---|---|---|
| 1 | Environment + unchanged official RPL demo (G0) | Automated work complete; stopped; two-student G0 review pending |
| 2 | Reading protocol, transport and aggregation | Automated work complete; N0 pilot verified; stopped before Phase 3 |
| 3 | AES-CCM + reproducible secure pilot | Automated implementation/pilot complete; human review and expanded validation pending |
| 4 | Ascon + energy and lifetime model | All 35 validation cases pass (cases 29–35 completed 16 Nov 2026); human review pending |
| 5 | Adaptive policy and controls | Policy implemented; corrected campaign stopped at 40/210; items 1–3 and bounded policy/mechanism checks executed 17 Nov; current-source 9-node calibration, P1 Stage B and Stage C single-seed comparison complete; residual-aware P1 and human review pending |
| 6 | Full experiments, reproducibility and release | Pending — requires Phase 4/5 human review and explicit authorization |

Record commands, outcomes, decisions, reasons, failures and downstream impact in each phase journal. RAM affects execution concurrency, not project requirements.

## Phase 1 reading guide

- [Chronological journal](phase_01_environment.md): execution history and outcomes.
- [Downloads, problems and resolutions](phase_01_downloads_problems_and_resolutions.md): installation scope, reasons, failures/fixes, evidence and remaining-phase workload estimate.

## Phase 2 reading guide

- [Detailed implementation/downloads/problems report](phase_02_detailed_report.md)
- [Chronological execution journal](phase_02_environment_and_implementation.md)
- [Commands and limitations](../docs/phase2-usage.md)

## Phase 3 reading guide

- [Detailed implementation and verification report](phase_03_detailed_report.md)
- [Execution journal](phase_03_environment_and_implementation.md)
- [Downloads, problems and resolutions](phase_03_downloads_problems_and_resolutions.md)
- [Usage and limitations](../docs/phase3-usage.md)

## Phase 4 reading guide

- [Execution journal](phase_04_environment_and_implementation.md) — includes 16 Nov deferred case closure
- [Detailed report](phase_04_detailed_report.md)
- [Leftover / deferred items](phase_04_leftover.md) — all closed 16 Nov 2026

## Phase 5 reading guide

- [Detailed implementation and verification report](phase_05_detailed_report.md)
- [Execution journal](phase_05_environment_and_implementation.md) — includes 16 Nov corrected campaign and policy fix

- [20 November 9-node Z1 calibration and P1 preflight](final2x_z1_nine_node_calibration_20261120.md)

- [20 November 9-node Z1 P1 mechanism pilot](final2x_z1_nine_node_p1_20261120.md)

- [20 November switching-energy, battery forecast and browser review](final2x_z1_transition_and_review_20261120.md)

### Latest Z1 evidence and open work

The [Stage C tracker](z1_stage_c_tracker.md) records the seven-arm comparison and the 54/54 changing-traffic result. The [Phase 4 mapping](final2x_phase_03_evidence_20261120.md) covers the archived matrix and identifies current-source limits. The [ranking diagnosis](final2x_z1_ranking_diagnosis_20261120.md) records the failed held-out affordability test, both forwarding cutoff checks and the same-host benchmark repeat. Battery-aware P1 qualification, full current-source Phase 4 coverage, human sign-off and second-person reproduction remain open. The desktop dashboard walkthrough passed against its earlier mechanism snapshot.

## Preserved historical records

The root `tmp/` directory contains preserved planning snapshots. They are indexed and labelled in [PLANS/README.md](../PLANS/README.md); future maintained plans belong in PLANS, while execution history stays here.
