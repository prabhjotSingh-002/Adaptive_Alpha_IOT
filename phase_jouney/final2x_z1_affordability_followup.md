# Phase 5 affordability and joint transition follow-up

The seed 123459 diagnostic reconciled the modeled component totals in 42 paired windows. All 42 pairs covered matching traffic phases and 40 included identical generated-reading IDs. The median absolute skew was 268 µs at the start and 277 µs at the end. The existing forecast correctly ordered the actions in 24/42 windows. The median absolute observed gap was 9.28 µJ and the median absolute gap error was 26.92 µJ. For the 30 windows fully within the slow phase, the median absolute CPU difference was 8.70 µJ and the listen difference was 0.70 µJ. This motivates calibrating packet work by traffic and packet size. The two reading-mismatched windows are retained in the CSV. [Window data](../results/phase_05/z1-affordability-v3/window-diagnosis.csv)

The pinned radio-off Z1 benchmark passed 128 matched switch/hold samples. Both arms begin with the same profile and cap. Across 32 samples each, AES cap 1 to Ascon cap 4 added a median 7.066 µJ of modeled CPU energy (range 7.042–7.090 µJ). Ascon cap 4 to AES cap 1 added 6.945 µJ (range 6.921–6.969 µJ). The two cap-one regression medians were 7.066 and 6.969 µJ. The timed interval exercises policy selection and local application of the action fields. Radio send and queued cap-shrink work require separate measurements. The original sandbox launch failed at Docker group setup and the approved retry passed. [Passed run manifest](../results/phase_05/z1-joint-transition-v1-retry/manifest.json) · [Failed run manifest](../results/phase_05/z1-joint-transition-v1/manifest.json)

The offline queue projection and energy bounds passed nine host assertions for backlog drain, holds, cap-triggered flushes, deadlines, missing calibration and exact depletion boundaries. The projection assumes successful submissions and continuous event timing. It takes caller-supplied energy bounds, so qualification needs calibrated background, packet and transition inputs plus paired traces with decision-time queue state. The host assertions establish implementation behavior. [Projection](../host/forecast_action_demand.py) · [Checks and hashes](../results/phase_05/z1-affordability-v3/followup.sha256)

```bash
python3 -B host/diagnose_affordability.py
python3 -B host/run_transition_benchmark.py results/phase_05/z1-joint-transition-v1-retry
sha256sum -c results/phase_05/z1-affordability-v3/followup.sha256
```

The benchmark runner requires a fresh output directory on subsequent runs. Radio-enabled matched queued shrink, calibrated development replay and fresh joint affordability qualification remain pending. R04 is open and the revised nine-node run remains gated.
