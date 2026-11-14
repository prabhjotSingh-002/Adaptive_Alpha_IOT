# Phase 4 implemented commands and evidence limits

Run from project root with the pinned official dependencies/image and Docker access. All build writers share `results/phase_02/.runner.lock`.

```
python3 host/run_experiment.py --phase 4 --mode B1 --clients 2 --switch-test --target z1 --timeout-seconds 300
python3 host/run_experiment.py --phase 4 --mode B1 --clients 2 --switch-test --target z1 --energy-telemetry --timeout-seconds 300
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --timeout-seconds 300
```

Phase 4 now provisions two independent 16-byte keys per sender, one per permitted profile. Both contexts activate in one validated metadata transaction; no header-triggered context allocation exists. Root lookup is bounded by sender/profile; reading dedup remains shared per sender. Static B1/B2/B4/B5 select their configured cipher. `--switch-test` is a dedicated security-purpose controlled AES→Ascon→AES exercise; it is not an adaptive policy. The first three submissions must retain counters 1/1/2 in their respective contexts. The application packet ordinal is separate from the nonce counter.

New Phase 4 runs use schema 2: META2 carries resolved config identity/selected profile/context count/test flag; TX2 uses actual sealed header profile/epoch/counter; RX2 uses verified output identity; PACKET2 occurs once per authenticated packet before reading dedup. Host packet keys include sender/profile/epoch/counter. Packet PDR uses authenticated accepted data packets over local UDP submissions, separate from reading PDR, MAC frames/retries and attack injections. Exact `PHASE4_SCHEMA2_COMPLETE` and `TEST OK` terminal lines are required. Legacy logs retain schema 1; select the recorded producer schema when reparsing historical evidence.

`--energy-telemetry` currently permits only Z1 Phase 4 and emits official raw counters, timer frequency and width. It does not select a validated power model, report joules or shut down forwarding. See [power accounting status](power-model.md).

Known failing evidence: Z1 root+8 controlled-return runs at 60s and 180s warm-up have node 9 with no submissions; matching context counters were observed for the other seven senders. They are failed integration runs, not successful target qualification. Longer warm-up alone did not resolve the route symptom. Preserve topology and diagnose routing/memory before interpreting lifetime or scaling outcomes.

KATs, provisioning negatives/reset matrix, target resource/stack/energy qualification and final pilot requirements remain governed by the consolidated plan and Phase 4 journal. Source presence or this usage document does not close those gates.
