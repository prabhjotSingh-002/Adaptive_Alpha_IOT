# Version 1 scenario calibration

Calibration is a single-seed scenario-level energy-per-authenticated-reading proxy. Qualification means complete measured cells, artifact integrity and exact runtime compatibility, not statistically established cipher superiority or a validated residual-energy forecast.

## Measure static cells

Use the canonical runner serially, with the same workload/model/target and isolated seed. Repeat for B1 (AES) and B2 (Ascon), caps 1, 2 and 4:

```bash
python3 -B host/run_experiment.py --phase 4 --mode B1 --clients 2 --target z1 --power-model --seed 223457 --calibration-cap 2
```

`--calibration-cap` is restricted to Phase 4 static B1/B2 Z1 power-model runs. It cannot combine with security/lifetime fixtures. Purpose is recorded as calibration; configured and actual cap are retained. Existing B1/B2 control mappings remain unchanged without this flag. A cap-4 measurement may send three-reading packets under deadline-first scheduling; the table records the actual TX batch distribution.

Build from a JSON list of exact run directories, relative to the repository root:

```bash
python3 -B host/calibrate.py --seed 223457 --calibration-inputs results/phase_05/repairs_17nov/final-calibration3/calibration-inputs.json --out results/phase_05/repairs_17nov/final-calibration3/cost-table-v1.json
```

Freeze the output before evaluation. All six profile/cap cells are required; missing cells remain zero/unavailable and qualification is incomplete. Accepted and rejected input records retain reasons. Preregistered eligibility here is reading PDR >=0.95, p95 <=5000 ms, positive finite energy and positive authenticated deliveries; no threshold-based rejection applies to subsequent evaluation outcomes. Required artifacts and binaries must match recorded hashes, and source/config/model/dependency/client/topology context must agree. Calibration includes warmup and drain energy and excludes the root via the canonical metric.

## Consume after resolving CLI settings

```bash
python3 -B host/run_experiment.py --phase 5 --mode P1 --clients 2 --target z1 --power-model --seed 123456 --policy-cost-table results/phase_05/repairs_17nov/final-calibration3/cost-table-v1.json --require-qualified-policy
```

This command is an evaluation example, not a record that a P1 pilot was executed. Check phase authorization before running. A 3-node table is rejected for `--clients 8`; use an independently measured compatible 9-node table. Period/payload CLI overrides are checked before build against the fully resolved runtime context. Source or dependency drift also rejects the table. Calibration and evaluation seeds cannot overlap.

Old unversioned tables are retained as historical data. They cannot satisfy qualified preflight. Explicit `--allow-unqualified-policy` permits only native functional diagnostics; it cannot bypass compatibility for power-model/lifetime results. Do not manually edit generated-conf.h.

## Evidence from this repair

See `results/phase_05/repairs_17nov/` for full test logs, Flask route checks, commands and measured calibration artifacts. Earlier source-cohort runs remain preserved; final source measurements are kept under `final-calibration3/` and `final-calibration9/`. Human review, browser visual acceptance, dynamic-policy validation and comparative lifetime research remain separate gates.
