# Phase 3: AES-CCM engineering pilot

Read the unchanged PLANS/ documents, phase_jouney/tmp/phase_03_implementation_plan.md and phase_jouney/phase_03_detailed_report.md. Use the pinned Contiki source and official image in results/setup/source-pins.json. The existing Docker group may require sg docker; the runner uses it.

From the project root:

    python3 host/run_experiment.py --phase 3 --mode both --clients 2
    python3 host/run_experiment.py --phase 3 --mode both --clients 8
    python3 host/run_experiment.py --phase 3 --mode B4 --clients 2 --period-ms 500
    python3 host/run_experiment.py --phase 3 --mode B4 --clients 2 --period-ms 4000
    python3 host/run_experiment.py --phase 3 --mode B4 --clients 2 --payload-budget 47
    python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --attack-test
    python3 host/run_experiment.py --phase 3 --mode B1 --clients 2 --root-reset-test

The last two commands are dedicated security tests; never use their performance summaries as clean baseline results. --timeout-seconds can intentionally produce a failed run for cleanup testing. --phase defaults to 2 for existing N0 calls. Phase 2 and 3 share the same nonblocking runner lock and build/config directories.

Each Phase 3 run receives independent OS-random test-only keys. Its test-keys.json and generated scenario contain those keys in cleartext for reproducibility: they are public simulation fixtures, not credentials or production provisioning. A simulation boot gate requires a one-use Cooja grant. A reset locks the context until a new experiment with fresh keys; snapshot rollback and real power-failure persistence are not supported. See the threat model.

Run portable production-code checks (the same AES/CCM sources are linked on motes):

    sg docker -c 'docker run --rm --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT,destination=/workspace contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609 bash /workspace/scripts/test_phase3_crypto.sh'
    python3 -B -m unittest discover -s tests/unit -p 'test_*.py' -v

Adjust the bind source for a different checkout. A run manifest contains resolved config, pins, commands, source and binary hashes, and outcome; per-run binaries are copied under binaries/. Raw simulator serial/radio output and normalized events are retained. The pair file checks exact simulator-global GEN tuples. Named containers are stopped on caught timeout/keyboard interruption; a hard kill of the runner or OS still requires checking for leftovers.

Evidence index: results/phase_03/phase3-evidence.json. Earlier Phase 3 manifests generated before the git provenance fix may say git_sha=HEAD even though no commit existed; this is not a SHA. Final indexed primary runs correctly record null and source hashes.
