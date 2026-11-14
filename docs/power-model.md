# Phase 4 MCU/radio power model and accounting

Model: `configs/power-z1-v1.json`, ID1, nominal3V, Z1/MSP430F2617 at8MHz, 25°C. This is a software simulation component estimate, not whole-board power or a physical battery measurement. Actual validation status and failures are indexed in `results/phase_04/phase4-evidence.json` and the Phase4 journal.

## Sources and parameters

The archived TI SLAS541M datasheet Figure8-2 gives approximately4.2mA MCU active current at3V/8MHz. The model records ±0.2mA curve-reading sensitivity, rather than scaling the unrelated1MHz headline current. Table8.6 gives typical LPM3 crystal-clock current1.1µA at3V/25°C. Sources:

- [TI MSP430F2617 SLAS541M](https://www.ti.com/lit/ds/symlink/msp430f2617.pdf), archived as `results/phase_04/msp430f2617-SLAS541M.pdf`.
- [TI CC2420 SWRS041C](https://www.ti.com/lit/ds/symlink/cc2420.pdf), archived as `results/phase_04/cc2420-SWRS041C.pdf`. The component model uses oscillator-on idle426µA, TX17.4mA at0dBm and listen18.8mA; the pinned driver turns RF off with SRFOFF and retains the oscillator.

CPU/LPM timelines include the idle radio baseline once; radio TX/listen coefficients are increments above it. Coefficients in nanoamps are CPU4626000, LPM427100, deep0, TX16974000, listen18374000. Thus an active/listening interval charges MCU plus full radio listen current, without adding a board baseline twice. Root has the same model but is mains-powered/excluded from primary battery-node sums. Other regulators, LEDs, external sensors and board leakage are outside this component scope. Boot uses an oscillator-on baseline conservatively; transitions and pre-Energest-init hardware activity are not measured.

The pinned platform records LPM1/LPM3 under one Energest LPM counter. The selected Z1 build has UART RX DMA disabled; inspected F2xxx call sites request LPM1 only in that disabled DMA branch. Runtime accounting additionally rejects a nonzero `msp430_dco_required` or any deep-LPM ticks. This qualifies LPM3 for this configuration only. A different peripheral/clock configuration must revalidate the model rather than inherit the coefficients.

## Measurement and arithmetic

Official Energest provides CPU/LPM/deep/TX/listen cumulative counters. Z1 reports32768Hz with16-bit underlying time (2s wrap). Sampling is125ms by default;250/500ms are explicit validation options. Counters are flushed/copied in a short interrupt-masked snapshot, then interrupts are restored before arithmetic/logging. Raw snapshots are logged once per second and at terminal depletion; gaps at/above an underlying wrap fail validation. This does not replace the official OS state tracker.

Shared production `firmware/energy/energy.c` computes per-state nanojoules as `delta_ticks * millivolts * nanoamps / (1000 * frequency)`, with checked products/sums and retained remainders. Invalid regression/overflow invalidates the run without a partial sample commit. Budget exhaustion is terminal. One explicit final close accounts shutdown deltas after queue disposition and MAC/radio-off; close cannot reactivate the state or be repeated. Final serial reporting/removal occurs after that counter snapshot and is a bounded observation boundary, not secretly included energy.

The runner compiles `host/energy_reconcile.c` against that same C implementation for each model run. Host analysis compares every logged total/residual against recomputation, checks component conservation and stores per-state contributions. It also evaluates ±0.2mA CPU-current sensitivity on the same observed trace with an uncapped budget. Those bounds are parameter sensitivity, not a counterfactual network-lifetime prediction or confidence interval.

Budget accounting starts from OS Energest initialization, including warm-up. Phase4 engineering figures declare the boot-to-horizon observation window, including warm-up/drain, with dead nodes ending at their final snapshot. Primary energy is the battery-node sum divided by unique authenticated deliveries; no deliveries gives undefined energy per reading. Mains root totals remain separately reported. Later main research must freeze its own measurement start/end cohort; it cannot silently substitute these windows.

## Depletion and evidence

At exhaustion, firmware locks contexts, stops generation, accounts queued DROP70 readings and switches MAC/radio off. Cooja then removes the whole mote on its DEPLETED event and records REMOVED, preventing timer-driven resurrection. Counter snapshots and detection/removal timestamps remain in raw evidence. The parser requires verified terminal events, survivor final samples and no post-removal radio activity; crashes/timeouts are failures. The bottleneck fixture requires parent-path and authenticated downstream receive proof before removing the forwarder.

Portable sanitizer tests cover fractional precision, conservation, regression, overflow, terminal budgets and one-time close. Actual model/network runs, controlled idle/CPU-load cases, sample-period sensitivity and final matrices must be checked in the evidence ledger; code or this document alone does not close G4. Stack observations use the pinned official stack-fill checker with a128-byte minimum remaining guard. Its documented limitation is that merely reserved, unwritten stack space may be missed; this is observed workload qualification, not a proof against arbitrary future workloads.

## AES target qualification

The pinned MSPSim CC2420 strobe dispatcher does not implement SAES. Its default hardware AES path accepted a wrong-key fixture and is excluded from protected comparisons. Application and mote-KAT builds now explicitly select vetted Contiki `aes_128_driver` through `firmware/crypto/aes-backend.mk`. New results identify the software backend; old Z1 application runs without that selection retain their artifacts but cannot serve as secure baseline qualification. Native software AES and direct Ascon KAT evidence have their original, narrower scopes.
