# 2X Phase 3 evidence checkpoint — 20 November 2026

The execution order follows Sections 12–13 of [finalPLAN2X](../finalPLAN2X.md). Existing 3-node and 9-node calibration tables remain tied to their measured source and workload cohorts. The separate changing-traffic table qualified on six new 3-node cells. [Nine-node calibration](final2x_z1_nine_node_calibration_20261120.md) · [Changing-traffic tracker](z1_stage_c_tracker.md#changing-traffic-z1-checkpoint)

## Phase 4 mapping and fresh controls

- Mapped 35 archived validation cases to 62 accepted runs. Verified 685 indexed artifact and binary hashes. The original failed static case for seed 123458 remains indexed alongside the passing rerun.
- Replayed 83,467 structured events and 15,153 frames with the current parser and summary logic. The seven compared summary fields matched in every run. All 22 deferred runs were included. Energy-model runs replayed through their preserved reconciliation binaries. Lifetime runs also passed the current terminal-depletion checks.
- Built and ran four fresh static modes in the pinned Z1 environment at root + 2 sensors and seed 123456. B1, B2, B4 and B5 each authenticated 48/48 readings. The runner recorded its 125 ms service-bound pairing marker. All 49 indexed hashes matched. Each captured generated header matched that run's manifest. The first audit compared the generated source entry against the active global header and rejected the first three arms. The amended audit compares that entry against the run-local copy.
- Archived cases have historical source fingerprints. The ledger records drift per run. Fresh controls cover the four ordinary static modes in one seed and topology. Full current-source matrix coverage and human review remain open. The shared runner lock was available after the fresh controls completed.

Run the following from the repository root:

```bash
python3 -B host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model --seed 123456 --timeout-seconds 300
PYTHONPATH=host python3 -B results/phase_05/z1-closure-20261120/phase4-audit.txt
```

The audit reads the saved control log. The first command above is the recorded simulation invocation and produces new run IDs when repeated. [Machine-readable ledger](../results/phase_05/z1-closure-20261120/phase4-audit.json) · [Fresh run log](../results/phase_05/z1-closure-20261120/phase4-current-static.log) · [Replay log](../results/phase_05/z1-closure-20261120/phase4-audit-expanded.log) · [First audit failure](../results/phase_05/z1-closure-20261120/phase4-audit-first.log)

## Work carried forward

The earlier browser attempt saved Firefox screenshots of the latest, archive and campaign pages. The campaign screenshot was taken during data loading. The interactive walkthrough remains pending. Isolated switching energy, battery-aware P1 validation, human sign-off and independent reproduction remain open. Existing Stage A–C results stay recorded with their original scope. [Browser capture log](../results/phase_05/z1-closure-20261120/walkthrough.log) · [Stage C tracker](z1_stage_c_tracker.md)
