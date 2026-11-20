# Phase 5 radio-enabled queued shrink and forecast replay

## Matched control

Seed 123460 used three Z1 motes and 12 readings per sensor at 500 ms. Both arms began at Ascon cap 4. On the first policy tick with two queued readings, the hold arm retained that action and the switch arm selected AES cap 1. The fixture controls action selection. Firmware applied it through the normal sensor action and backlog drain path, with production aggregation, sealing and radio submission.

Both runs delivered 24/24 authenticated readings. On each sensor, the two queued readings went out as separate AES singleton packets after the switch. The hold arm submitted six packets over the run, compared with 24 in the switch arm. Per sensor, the two seconds after the anchor captured one frame under hold and six under switch, with one queued reading at the hold endpoint and zero at the switch endpoint.

| Sensor | CPU change, µJ | Low-power change, µJ | TX change, µJ | Listen change, µJ | Total change, µJ |
|---|---:|---:|---:|---:|---:|
| 2 | +946.34 | −88.07 | +394.61 | −460.43 | +792.45 |
| 3 | +947.84 | −88.17 | +393.60 | −463.62 | +789.64 |

The comparison uses reconciled energy counters bracketing each two-second observation window and normalizes their duration. It includes the sustained effect of the smaller batch cap during the window. The isolated radio-off action application cost was measured separately in the preceding checkpoint. The two sensors share one seed and simulation, and the result is descriptive. The sandbox Docker failure and compiler failure from the unused fixture policy state are preserved. [Protocol](../results/phase_05/z1-queued-shrink/protocol.json) · [Paired results and manifests](../results/phase_05/z1-queued-shrink/result.json)

## Development forecast replay

A rate-conditioned candidate used archived seed 223457 controls and only generation intervals available at the AES decision timestamp. It was scored on the existing seed 123459 windows and unchanged budgets.

| Candidate | Exact set | Exactly one action fits | False-affordable action calls | Abstained budget cases |
|---|---:|---:|---:|---:|
| Recent-rate baseline | 135/294 | 4/20 | 112 | 0 |
| Rate-conditioned | 106/294 | 0/20 | 135 | 98 |

Abstentions count in the denominators. The candidate uses absolute per-action calibration windows. Packet-level calibration for the queue-aware model remains to be collected, including the packet occupancy and contemporaneous background demand. The radio fixture measured the total impact of holding a new cap after transition. That total cannot be added to a forecast that already projects the additional packets. R04 remains open. A new held-out ranking evaluation and revised nine-node P1 run remain gated. [Development replay](../results/phase_05/z1-queued-shrink/development-replay.json)

Commands and hashes are indexed with the evidence. Reproduction uses a fresh log directory for collection. The audit and replay below consume the saved runs.

```bash
PYTHONPATH=host python3 -B results/phase_05/z1-queued-shrink/audit.txt
PYTHONPATH=host python3 -B results/phase_05/z1-queued-shrink/replay.txt
```

## Changing traffic with a finite budget

The runner, telemetry checks and lifetime metrics now use the same prospective demand schedule. Four lifetime unit tests passed, including the two traffic segment boundaries. The pinned three-node AES cap-1 smoke on development seed 123461 and 4.5 J per sensor passed. Both sensors entered the 4,000 ms interval and depleted. Root authenticated 24/24 generated readings out of 54 scheduled. First depletion occurred at 80.483 s. Audit verified all 13 indexed artifacts. This validates the changing-traffic finite-budget harness for this smoke workload. [Run audit](../results/phase_05/z1-queued-shrink/finite-changing-result.json)
