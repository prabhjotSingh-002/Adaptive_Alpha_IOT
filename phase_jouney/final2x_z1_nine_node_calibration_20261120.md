# 20 November 2026 — 9-node Z1 calibration and P1 preflight

The nine-mote legacy Z1 scenario used one root and eight sensors with the pinned official Contiki-NG/Cooja container. Each static cell used seed 223457, 60 s warmup, 24 readings per sensor at 1 s intervals, a 3 s deadline, 125 ms flush lead, and 15 s drain. The horizon was 102 s. Energy costs use the Z1 MCU/radio component model across the entire run window.

| Cipher | Configured cap | Authenticated / generated | p95 delay (ms) | Model cost (nJ / authenticated reading) | TX batch distribution | Run manifest |
|---|---:|---:|---:|---:|---|---|
| AES-CCM | 1 | 186/192 | 158.26 | 247378091 | {'1': 186} | [20261119T191047113613Z-B1-8](../results/phase_04/20261119T191047113613Z-B1-8/manifest.json) |
| AES-CCM | 2 | 186/192 | 1143.52 | 247107863 | {'2': 93} | [20261119T191238765737Z-B1-8](../results/phase_04/20261119T191238765737Z-B1-8/manifest.json) |
| AES-CCM | 4 | 186/192 | 2990.33 | 247009829 | {'3': 62} | [20261119T191434910853Z-B1-8](../results/phase_04/20261119T191434910853Z-B1-8/manifest.json) |
| Ascon-AEAD128 | 1 | 186/192 | 158.00 | 247386588 | {'1': 186} | [20261119T191622767325Z-B2-8](../results/phase_04/20261119T191622767325Z-B2-8/manifest.json) |
| Ascon-AEAD128 | 2 | 186/192 | 1143.91 | 247103499 | {'2': 93} | [20261119T191812314950Z-B2-8](../results/phase_04/20261119T191812314950Z-B2-8/manifest.json) |
| Ascon-AEAD128 | 4 | 186/192 | 3001.10 | 247002285 | {'3': 62} | [20261119T192008597849Z-B2-8](../results/phase_04/20261119T192008597849Z-B2-8/manifest.json) |

All six static cells qualified against the existing 95% delivery and 5,000 ms p95 limits. All 72 artifact and binary checks matched. The cap-4 measurements use observed batch occupancy under this workload, whose 1 s period and 125 ms flush lead yield batches of three. Single-seed model costs describe this scenario.

## Builds and P1 admission

Both firmware roles linked in all six static cells. GNU msp430-size measured a maximum of **54,929 bytes text+data** and **6,932 bytes data+bss** across the 12 archived Z1 binaries. Minimum observed stack headroom was **344 bytes** in the static runs. These figures cover the exercised static paths. [Binary size evidence](../results/phase_05/z1-nine-node-20261120/binary-size-evidence.json)

The Phase 5 CLI returned `preflight_passed` and `calibration_status: qualified` for the matching nine-node runtime context with independent evaluation seed 123456. Admission checked source, dependencies, scenario template, workload, power model and calibration artifact lineage. The cost table SHA-256 is `fb59e718b95d7de2c7b271b15109a186694a5d73e8fe25e23f7b653382e34878`. [Cost table](../results/phase_05/z1-nine-node-20261120/cost-table-v1.json) · [P1 preflight](../results/phase_05/z1-nine-node-20261120/p1-preflight.log)

## Execution record

The first AES cap-1 attempt failed at `sg: setgid() failed: Invalid argument` inside the sandbox. After approval, the canonical runner completed the retry in the pinned Docker image. The five remaining runs used the same runner serially and the repository runner lock guarded generated configuration and build directories. The canonical runner regenerated `firmware/generated-conf.h` for each cell. [Failed console](../results/phase_04/20261119T191035058671Z-B1-8/console.log) · [Commands](../results/phase_05/z1-nine-node-20261120/calibration-commands.json) · [Table build](../results/phase_05/z1-nine-node-20261120/table-build.log) · [Toolchain size log](../results/phase_05/z1-nine-node-20261120/msp430-size.log)

This checkpoint ends at P1 preflight. The nine-node P1 build and functional and finite-budget simulations are pending, along with comparison and human review gates.
