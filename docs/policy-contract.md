# Policy and queue contract — items 4–5 repair, 17 November 2026

## Scope and residual energy

P1 is a cost-aware cipher/cap ranker with measured own-generation traffic. Its current scenario-level network nJ/authenticated-delivery table is not a validated local battery-demand forecast. Residual-aware P1 ranking remains unresolved; the residual field in telemetry does not establish that capability. B3 uses the actual residual-budget threshold and is validated separately. No energy/lifetime gain follows from a successful mechanism test.

## Safety and feasible actions

The shared production policy C is compiled for host tests and motes. An initialized profile outside {1,2} or cap outside {1,2,4} returns protected AES/cap1 fallback and resets initialization before any cost lookup. Cost entries of zero are unavailable. UINT64_MAX is a bounded representable cost; arithmetic compares differences only after ordering checks. Dwell uses unsigned elapsed time and never retains an infeasible action. Protected fallback does not mean N0, nor does it mean a depleted node may transmit; the terminal energy path stops the application and radio.

Packet capacity uses shared LAB_HEADER and LAB_READING_BYTES constants. Profiles retain distinct security contexts/counters; choosing another profile does not reset its counter or key context.

## Measured rate

Each sensor observes actual created_ms values for its own generated readings. An eight-interval bounded window estimates floor(100000 * interval_count / sum_ms), in Hz×100. Rate is unavailable (zero) until two readings are observed. Equal timestamps do not invent an interval; a discontinuity >INT32_MAX reinitializes the window. Unsigned subtraction handles one bounded clock wrap. Rate saturates at UINT16_MAX.

Freshness expires when age > max(1000 ms, 2×mean observed interval). FEATURE records are emitted when sample count or estimated/stale rate changes. Raw-event verification reconstructs the window from GEN, checks sample count/rate and bounds feature age against the same node's simulator timestamp. Constant-rate Z1 runs establish measurement operation; changing-arrival host tests are fixtures, not research evidence of dynamic workload adaptation.

## Deadline and cap reduction

The old queue is serviced before a newly due reading is offered. Full-cap fill prediction therefore requires (cap−1)*period < effective flush deadline; equality does not promise full occupancy. Effective flush time subtracts the configured lead. Static and adaptive Z1 runs use the same 125-ms flush lead; native uses zero. This is a queue scheduling contract, not an E2E delivery guarantee.

A reduced cap chunks an existing backlog: lab_build_batch returns min(queue_count,current_cap), and commit removes only that submitted chunk. The sensor emits the new POLICY action first, then drains at most LAB_CAPACITY chunks, stopping if submission cannot progress. Pending readings remain subject to explicit deadline/drop accounting. No packet may exceed the current logged cap. Shared-C tests verify order, retained readings and commits after shrink; these fixtures are not measured network results.

## Evidence and timing

POLICY records the decision; TX2 reads actual sealed header profile/epoch/counter; RX2 is emitted only after successful root authentication/body/replay acceptance. Canonical raw-event checks join these identities and reading ranges. Logged profile/cap changes, startup assignments and actual wire-profile changes are reported separately. A policy change after traffic ends need not create a wire transition.

POLICY_TIME covers the existing timed selection/application region, not all feature collection, instrumentation, chunk flushing or cryptography. Zero timer ticks can mean below resolution. Complete component-model energy includes actual on-mote work; do not add a second crypto-energy term. Configured transition cost is an assumption with per-reading amortization over the dwell horizon; it is not a measured isolated switching-energy result.

## Reset and depletion

A replaced root does not receive a second simulation boot grant. Acceptance requires two real boot requests, authenticated pre-reset traffic, positive post-reset captured-packet probes, locked-context rejections and zero post-reset accepted packets/readings/reactivation. This proves fail-closed behavior, not recovery/availability or replay-window restoration after reboot.

For finite-budget runs, preserve the prospective schedule after death. Require final exhausted energy sample/zero remaining budget, exact production-C reconciliation, terminal REMOVED and no later node RF/application events. A targeted bottleneck fixture must show the actual parent path and downstream traffic before removal. Root power and bounded versus unbounded sensor budgets are explicit. FND/HND/service crossing/confirmation and censored events remain separate metrics.

## Reproducibility

Use host/run_experiment.py serially. --preflight-only checks fully resolved runtime and calibration compatibility without building/simulating. Capture contract initial_log_event_included_v2 processes the first message because pinned Cooja ScriptParser already waits once before executing user script. The generic OS MAIN log is disabled uniformly to fit Z1 ROM; all structured RSLAB events remain required. Earlier ROM and missing-timer failures are preserved.

Any source change invalidates current-source admission of older tables; historical runs remain valid for their captured source cohort. Refresh only the required small calibration set, preserve previous versions, and do not silently transfer 3-node tables to 9-node evaluation.
