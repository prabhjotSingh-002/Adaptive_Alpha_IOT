# Existing topologies aur run commands

Checked: 16 November 2026. Source/scenario inspection aur `python3 host/run_experiment.py --help` successful. Is documentation task mein simulation/build execute nahi kiya; neeche commands available code paths hain, fresh PASS claims nahi.

## 1. Actually kya available hai?

Repository mein ek canonical saved scenario hai: `simulations/scenarios/phase1-rpl-9.csc`. Runner isi se smaller networks aur bottleneck fixture generate karta hai. Historical results ke generated `scenario.csc` independent maintained topology templates nahi hain.

| Available layout | Nodes | Implementation | Purpose |
|---|---|---|---|
| Original RPL demo / full irregular layout | Root 1 + sensors 2–9 = 9 | Saved `.csc`; original demo uses upstream rpl-udp | Environment smoke, continuity network |
| Small direct-neighbour layout | Root 1 + sensors 2–3 = 3 | Runner keeps first 3 motes using `--clients 2` | Quick functional/security checks |
| Full custom-application layout | Root 1 + sensors 2–9 = 9 | Same saved coordinates, custom firmware, `--clients 8` | Static/policy pilots |
| Bottleneck chain | Root 1 + sensors 2–3 = 3 | `--clients 2 --bottleneck` repositions motes | Relay/depletion experiments |

Original demo aur full custom application ki geometry same hai; firmware alag hai. Cipher modes B1/B2/B3/B4/B5/B6/P1 topologies nahi hain. `--target cooja` / `--target z1` execution targets hain, layouts nahi.

### Geometry and radio

UDGM radio: transmitting range 50 m, interference range 100 m, configured TX/RX success ratios 1.0. Ye settings collision-free delivery ya 100% application PDR guarantee nahi karti.

| Node | Role | Original x (m) | Original y (m) |
|---|---|---:|---:|
| 1 | Root | 43.29 | 7.17 |
| 2 | Sensor | 41.01 | 42.16 |
| 3 | Sensor | 62.15 | 33.48 |
| 4 | Sensor | 82.83 | 21.69 |
| 5 | Sensor | 93.06 | 4.90 |
| 6 | Sensor | 60.03 | 64.80 |
| 7 | Sensor | 91.52 | 49.57 |
| 8 | Sensor | 115.16 | 27.56 |
| 9 | Sensor | 79.77 | 89.88 |

Small layout mein sensors 2/3 root ke direct radio range mein hain. Full layout irregular multi-hop-capable network hai, regular grid ya fixed star nahi. Actual RPL parents/routes runtime evidence se verify karne hain.

Bottleneck positions:

```text
Root 1 (0,0) <--40 m--> Sensor/relay 2 (40,0) <--40 m--> Sensor 3 (80,0)
```

Root–sensor 3 distance 80 m hai, configured transmission range se bahar. Sensor 2 intended relay hai; actual forwarding aur depletion cutoff logs/radio capture se qualify hote hain. Runner bottleneck ke liye exactly two clients require karta hai.

## 2. Setup

```bash
cd /home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT
python3 host/run_experiment.py --help
```

Docker running, docker-group access, pinned upstream checkouts aur built Cooja required hain. Existing runner pinned official container use karta hai. Ek time par ek experiment chalao; generated config/build directories shared hain. Original smoke ko bhi custom runs ke saath parallel mat chalao.

## 3. Original 9-node upstream demo

```bash
bash scripts/smoke.sh
```

Ye unchanged official RPL demo path hai; project AEAD/policy validation nahi. Outputs `results/phase_01/smoke-*/` mein.

## 4. Small direct network: root + 2 sensors

Unprotected N0 single/batch pair:

```bash
python3 host/run_experiment.py --phase 2 --mode both --clients 2 --seed 123456
```

AES-CCM functional run:

```bash
python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --seed 123456
```

Ascon on emulated Z1:

```bash
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --seed 123456
```

## 5. Full existing network: root + 8 sensors

AES-CCM baseline:

```bash
python3 host/run_experiment.py --phase 4 --mode B1 --clients 8 --target z1 --seed 123456
```

Four static arms B1/B2/B4/B5, serial execution with modelled energy:

```bash
python3 host/run_experiment.py --phase 4 --mode all --clients 8 --target z1 --power-model --seed 123456
```

Policy code path example (repaired integration still needs network qualification):

```bash
python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --target z1 --power-model --seed 123456
```

Same topology par `--mode B6` or `--mode P1` select kar sakte ho. Missing qualified P1 costs can lead to fallback; a successful run alone does not establish adaptation or savings. Historical Phase 5 results have audit qualifications in `lastAstra check.md`.

## 6. Bottleneck chain: root → relay → distant sensor

Functional chain run, without forcing energy-budget depletion:

```bash
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --bottleneck --warmup-ms 120000 --seed 123456
```

Existing depletion-sensitivity fixture command:

```bash
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --power-model --bottleneck --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --energy-sample-ms 125 --seed 223456
```

`--energy-sample-ms 250` selects the other recorded sensitivity case. These command paths exist in `host/validate_phase4.py`; outstanding qualification remains pending. Specifying a budget does not itself prove a death event occurred during observation. FND/HND/censoring and relay shutdown require actual valid evidence.

## 7. GUI mein topology dekho

Small network:

```bash
python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --seed 123456 --gui
```

Full network:

```bash
python3 host/run_experiment.py --phase 3 --mode B1 --clients 8 --seed 123456 --gui
```

Bottleneck:

```bash
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --bottleneck --warmup-ms 120000 --seed 123456 --gui
```

GUI needs working desktop/display forwarding. Previous blank-window issue is not yet verified resolved. GUI is visual inspection, not the normal headless results pipeline. Research evidence ke liye `--gui` remove karke headless run use karo.

## 8. Output aur important parameters

Custom headless runs: `results/phase_0N/<run-id>/`. Successful processing produces `manifest.json`, generated `scenario.csc`, logs/events and `summary.json`; failed runs may lack summaries. Manifest status/error inspect karo. Original raw evidence preserve karo.

| Flag | Meaning |
|---|---|
| `--clients 2` / `8` | Sensors only; total nodes = clients + root |
| `--bottleneck` | Three-node linear geometry; only with two clients |
| `--target cooja` | Native functional target; not faithful hardware crypto energy |
| `--target z1` | Emulated Z1 target |
| `--power-model` | Modelled energy; supported here with Phase 4/5 Z1 |
| `--seed` | Simulation random seed; does not reposition saved nodes |
| `--period-ms` | Generation period; does not change topology |
| `--gui` | Visual inspection mode |

## 9. Newly implemented 16-node layouts (16 November 2026)

Native Cooja supports `grid16` (4×4, 38 m spacing) and `tree16` (single root-facing relay with three chains of 5, 5 and 4 sensors). Both have exactly 1 root + 15 sensors. The tree is a bottleneck tree, not a perfect balanced binary tree: 1+2+4+8 is 15, not 16.

```bash
python3 host/run_experiment.py --phase 4 --mode B2 --clients 15 --topology grid16 --target cooja --warmup-ms 120000 --seed 123456
python3 host/run_experiment.py --phase 4 --mode B1 --clients 15 --topology tree16 --target cooja --warmup-ms 120000 --seed 123456
```

Append `--gui` for visual inspection. Existing default remains `--topology legacy`; old `--bottleneck --clients 2` still works. New layouts reject `--bottleneck`, non-15 client counts and Z1 until memory/stack qualification. Native runs do not establish hardware energy or lifetime gains. Actual run evidence: [16-node report](phase_jouney/topology_16_implementation.md).

## 10. Planned, not currently runnable as ready topology selections

10/20-node grid, larger bottleneck tree, dedicated alternate-path resilience network, heterogeneous/uneven-link topology are discussed in planning/guides. Current canonical template has only 9 motes; increasing `--clients` alone cannot create extra motes. The implemented options are `--topology grid16/tree16`; arbitrary-size grid/tree generation is not implemented.

`--radio-loss-test` is a controlled test hook, not a separate maintained weak-link topology. Larger layouts require scenario generation, provisioning/memory/routing changes and validation before claiming support.

## 11. Sources and verification scope

- `simulations/scenarios/phase1-rpl-9.csc`: exact mote positions/radio configuration.
- `host/run_experiment.py`: scenario slicing, bottleneck positioning, CLI and validation.
- `host/scenario_target.py`: Z1 adaptation.
- `scripts/smoke.sh`, `scripts/smoke.py`: original official-network smoke.
- `host/validate_phase4.py`: existing depletion/lifetime fixture commands.
- `lastAstra check.md`: current qualification limits.

No original plan changed. The initial inventory did not execute simulations. The later 16-node implementation and regression evidence are recorded in the linked report.
