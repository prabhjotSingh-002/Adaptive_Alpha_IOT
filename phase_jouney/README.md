# Phase journey

This folder records **what happened in each phase**: implementation, commands, tests, errors, fixes and reports. For **what to implement next**, use the separate [planning index](../PLANS/README.md). The master plan owns scope, deadlines, deliverables and gates.

| Phase | Scope | Status |
|---|---|---|
| 1 | Environment + unchanged official RPL demo (G0) | Automated work complete; stopped; two-student G0 review pending |
| 2 | Reading protocol, transport and aggregation | Automated work complete; N0 pilot verified; stopped before Phase 3 |
| 3 | AES-CCM + reproducible secure pilot | Automated implementation/pilot complete; human review and expanded validation pending |
| 4 | Ascon + energy and lifetime model | Started; implementation and gates pending |
| 5 | Adaptive policy and controls | Pending |
| 6 | Full experiments, reproducibility and release | Pending |

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

- [Execution journal](phase_04_environment_and_implementation.md)

The final Phase 4 report has not yet been produced. Current planning is maintained at [PLANS/PHASE_04_IMPLEMENTATION_PLAN.md](../PLANS/PHASE_04_IMPLEMENTATION_PLAN.md).

## Preserved historical records

The root `tmp/` directory contains preserved planning snapshots. They are indexed and labelled in [PLANS/README.md](../PLANS/README.md); future maintained plans belong in PLANS, while execution history stays here.
