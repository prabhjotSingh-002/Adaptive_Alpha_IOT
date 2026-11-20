# Phase 5 Z1 battery affordability replay

The held-out cap-one forecast failed the changing-traffic gate. The finite-budget survival check passed for both static actions. R04 remains open and the revised nine-node P1 run did not enter the run queue.

## Forecast and evaluation

The previous diagnostic found that listening dominated node energy and that absolute forecast bias exceeded the difference between actions. This replay forecasts the next two seconds from each node's preceding measured rate. For changing traffic, the AES forecast anchors both actions and a per-node median Ascon-minus-AES offset comes from the already examined seed 123458. For the finite-budget test, each arm uses its own prior rate and actual remaining energy. The changing-traffic controls use seven synthetic decision budgets per paired window. The finite controls classify survival to the two-second horizon from actual depletion timestamps.

The protocol froze held-out seed 123459 and the thresholds before scoring. The changing-traffic gate required 90% exact affordable-set agreement overall and 80% when exactly one action fit, with minimum counts for both checks. The finite gate required a crossing for each sensor and arm and zero false-affordable calls in those crossings. [Frozen protocol](../results/phase_05/z1-affordability-v3/protocol.json) · [Frozen inputs and code](../results/phase_05/z1-affordability-v3/frozen-evaluation.sha256)

## Observed outcomes

| Check | Held-out result | Gate |
|---|---:|---|
| Changing traffic, exact affordable set | 135/294 (45.9%) over 42 paired windows | Fail |
| Changing traffic, exactly one observed affordable action | 4/20 (20%) | Fail |
| Finite budget, false-affordable crossing predictions | 0/12, three crossing windows per sensor and arm | Pass |

Both changing-traffic controls authenticated 54/54 generated readings. Both finite controls at 4.097 J per sensor authenticated 24/24 generated readings out of 192 scheduled per arm. The survival labels matched on all 280 scored finite windows. Nearby windows at a crossing share the same depletion event. The changing-traffic median absolute demand errors were 262.5 µJ for AES and 273.3 µJ for Ascon. This result measures an offline cap-one forecast on three motes with one held-out seed. Firmware P1 ranking still uses calibrated costs and feasibility. [Per-window results](../results/phase_05/z1-affordability-v3/result.json) · [Evaluation log](../results/phase_05/z1-affordability-v3/evaluation.log)

## Reproduction and provenance

```bash
python3 -B host/run_affordability_controls.py
python3 -B host/evaluate_affordability.py
sha256sum -c results/phase_05/z1-affordability-v3/evidence.sha256
```

The collection command expects empty receipt and log paths. Preserve the existing cohort before collecting another. Each receipt records the resolved command, exit status, log hash and manifest hash. The four manifests contain source, config, scenario and binary provenance. Replay verified 50 indexed artifact hashes across the four runs. The first attempt failed source consistency when the offline evaluator was added during collection. The complete four-run cohort was collected after both scripts were finalized. [Evidence hashes](../results/phase_05/z1-affordability-v3/evidence.sha256) · [First attempt failure](../results/phase_05/z1-affordability-v3/attempt-1/changing-B2.log)

Reliable action-specific forecasts under changing traffic, qualification across batch caps and transition conditions, and the gated nine-node run remain open.
