# 16-node grid/tree implementation and verification

Date: 16 November 2026. User authorized implementing 1 root + 15 sensors from the topology guides. This is scoped topology implementation and functional regression, not closure of Phase 4/5 or completion of Phase 6.

## Decisions and implementation

- `host/topologies.py` constructs exactly 16 native motes from the existing canonical template, preserving root/sensor type identity and assigning unique IDs 1–16. No upstream source changed.
- `--topology grid16`: 4×4 row-major grid, root in corner, 38 m spacing, existing UDGM 50 m transmission/100 m interference ranges. Radio-neighbour graph has 24 edges; the opposite corner has minimum six hops. Actual RPL routes are dynamic.
- `--topology tree16`: root (0,0), relay 2 (40,0), then three disjoint sensor chains of lengths 5, 5 and 4 along +x, +y and -y from relay. Existing UDGM produces exactly 15 edges; removing relay 2 disconnects root from downstream sensors. This realizes the guide's concentrated relay topology, not a perfect balanced binary tree. The architecture guide's 1+2+4+8=16 assertion is incorrect (sum is 15). Original guides/plans preserved.
- Existing default `legacy` preserves 3/9-node positions; existing two-sensor `--bottleneck` fixture remains intact. New layouts require 15 clients and reject conflicting `--bottleneck`.
- Provisioning count ceiling increased from 16 to 30 for 15 dual-profile senders. This bound itself allocates no RAM; existing context arrays remain dimensioned by configured clients. Actual protected runs exercise provisioning.
- New layouts currently support native Cooja only. Z1 is rejected explicitly before generated configuration/build writes because larger-root memory/stack qualification is pending. No heterogeneous target or hardware energy claim is made.
- Selected topology is in resolved configuration and therefore configuration identity; generated scenario and changed source files are covered by existing manifests/hashes.

## Executed checks

| Run/check | Result |
|---|---|
| Layout tests | 3 passed: legacy XML preservation, IDs/connectivity/edge counts, invalid combinations |
| Full unit suite in pinned container | 47 passed, including production-C policy tests |
| Native grid16, Phase 4 B2, seed 123456 | Passed; 360 generated, 347 authenticated deliveries; 0 captured fragment frames |
| Native tree16, Phase 4 B1, seed 123456 | Passed; 360 generated, 356 authenticated deliveries |
| Existing legacy root+2, Phase 3 B1 | Passed; 48/48 authenticated deliveries |
| Existing legacy root+8, Phase 4 B2 | Passed; see archived summary for delivery metrics |

Commands:

```bash
python3 -B -m unittest discover -s tests/unit -p 'test_topologies.py' -v
# Full suite executed inside pinned official container:
python3 -B -m unittest discover -s tests/unit -p 'test_*.py' -v
python3 host/run_experiment.py --phase 4 --mode B2 --clients 15 --topology grid16 --target cooja --warmup-ms 120000 --seed 123456
python3 host/run_experiment.py --phase 4 --mode B1 --clients 15 --topology tree16 --target cooja --warmup-ms 120000 --seed 123456
python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --seed 123456
python3 host/run_experiment.py --phase 4 --mode B2 --clients 8 --target cooja --seed 123456
```

Evidence index: `results/topology_16/evidence.json` records run paths, status, source and artifact hashes. Each run manifest retains resolved configuration, pinned dependencies, launch command, scenario and binary hashes. Logs: `results/topology_16/layout-tests.log`, `container-unit.log`, `host-unit-attempt.log`.

## Failures and limits

Initial grid attempt failed with `sg: setgid() failed: Invalid argument` inside the sandbox; preserved at `results/phase_04/20261116T114322493328Z-B2-15`. Authorized retry succeeded at `20261116T114332382532Z-B2-15`. Host full-unit attempt lacked dependencies (including numpy); preserved and rerun successfully in pinned container. No host packages installed.

Tree success: `results/phase_04/20261116T114409355764Z-B1-15`. Legacy successes: `results/phase_03/20261116T114447156129Z-B1-2` and `results/phase_04/20261116T114512206683Z-B2-8`.

Packet loss remains an observed outcome, not hidden by run PASS. These are single-seed functional checks, not matched grid-vs-tree performance comparisons (different cipher arms). No claimed lifetime improvement, adaptive-policy qualification, GUI verification, Z1 scaling or human sign-off. Required wider security/energy/phase matrices remain pending. Generated tracked settings were restored to their pre-task committed contents after serial runs; each run retains its own configuration archive.

Usage commands are also in `existing_toplogoyCode.md`. No original plan or historical evidence deleted or rewritten.
