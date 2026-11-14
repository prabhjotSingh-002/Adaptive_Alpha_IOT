# Phase 2 build, tests and diagnostic experiments

Read PLANS/MASTER_IMPLEMENTATION_PLAN.md, docs/protocol.md and docs/architecture.md. This implementation supports N0 only, with no application authentication/encryption.

Prerequisites: Phase 1 pinned source, built Cooja distribution and locally available official digest-pinned image. Source/image pins: results/setup/source-pins.json. Docker account membership must be available; commands activate it via sg docker. No new host installs are needed.

From the project root:

```bash
python3 host/run_experiment.py --clients 2 --mode both
python3 host/run_experiment.py --clients 8 --mode both
python3 host/run_experiment.py --clients 2 --mode N0-batch --period-ms 500
python3 host/run_experiment.py --clients 2 --mode N0-batch --period-ms 4000
python3 host/run_experiment.py --clients 2 --mode N0-batch --payload-budget 47
```

Runner inputs come from configs/phase2.json plus explicit CLI overrides. JSON is used with the Python standard library; YAML-specific tooling is not needed for this pilot. It generates firmware/generated-conf.h and saves resolved values in each manifest. A lock prevents concurrent builds modifying shared settings. Runtime READY events validate effective settings. Output goes into a new results/phase_02/<UTC>-<mode>-<clients>/ directory: manifest.json, scenario.csc, console.log, COOJA.testlog, events.jsonl and summary.json. Failed runs retain available artifacts/status; a passed run means valid instrumentation/accounting, not proof of statistical improvement. Paired invocations also require exact generation trace equality.

The period/deadline must be multiples of the 125ms scheduler tick. The pilot is finite: 60s warmup, 24 readings per node, configured period, 3s deadline and 15s drain after conservative generation horizon. No battery deaths or traffic changes occur. Lower byte budgets can lower the effective cap; reserve=16 accounts for future tag space only and does not add encryption.

Run C and Python tests in the existing toolchain image:

```bash
sg docker -c 'docker run --rm --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT,destination=/workspace contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609 bash /workspace/scripts/test_phase2.sh'
```

Adjust the bind-mount source for another checkout. C sources are shared between mote firmware and host ASan/UBSan tests; ten Python fixture tests cover parser/metric failures and known answers. The source tree has no initial project commit yet; run manifests record git_sha=null and actual source hashes instead of fabricating a commit SHA. Create/review a proper versioned release before frozen research experiments.

The chart in results/phase_02/pilot-comparison.png comes only from the validated primary pair summaries. host/plots.py uses matplotlib already present in the official image. host/metrics.py alone defines metrics. Radio raw captures support the zero-fragment observation for these actual N0 scenarios; encrypted/MAC-security variants require new verification. A local submission is not an acknowledgement or successful delivery. Local queue hold at submission initiation is separate from end-to-end delay.

Known boundary: the runner uses a 900s host process timeout and records a failure; if the Docker client is externally interrupted, inspect docker ps and stop the corresponding run container before resuming. No claim of automatic orphan-container cleanup is made.
