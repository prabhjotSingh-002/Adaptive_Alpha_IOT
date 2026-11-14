# Phase 1 Linux setup

See phase_jouney/phase_01_environment.md for decisions and actual status.

Ubuntu 26.04 is supported by the official Docker Engine Ubuntu installation instructions: https://docs.docker.com/engine/install/ubuntu/ . The project installer follows the official apt repository method and records output; it does not remove conflicting installations or add users to privileged groups.

Run in your own interactive terminal from this project:

```bash
bash scripts/install_docker.sh
```

The sudo password is entered locally in the terminal. The script installs Docker Engine/CLI, containerd, Buildx and Compose, starts the service and runs hello-world. Logs are under results/setup/docker-install-*.log. Only a successful execution establishes installation. Java, C/ARM/MSP430 toolchains are supplied by the official Contiki image later; no duplicate host installation is required at this step.

Subsequent steps: validate Docker access, pull the source-matched official Contiki image, record its digest, verify Java/compiler versions inside it, build Cooja, and run the unchanged official 9-node RPL scenario. Commands for these steps will be added after validation. G0 requires real simulation output and the master's human verification.

## Validated Phase 1 environment and rerun

Docker 29.9.3 daemon and hello-world verified. The account is in docker group; the inherited agent session uses sg docker to activate that authorized membership. Source pins and actual image digest are in results/setup/source-pins.json. The requested source-hash image tag was absent; the official develop image was pulled, pinned by digest and validated for Java 25/Cooja compatibility.

After source/image/build preparation already completed on this machine, rerun from project root:

```bash
bash scripts/smoke.sh
```

Each run writes results/phase_01/smoke-<UTC>/manifest.json, console.log and COOJA.testlog. It must pass with responses at nodes 2–9. This is the official unprotected tutorial, not the research application.

Initial build/run command executed successfully (requires Docker access):

```bash
sg docker -c 'docker run --rm --name adaptivealpha-phase1 --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT/external/contiki-ng,destination=/home/user/contiki-ng --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT,destination=/workspace contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609 bash /workspace/scripts/phase1_container.sh'
```

Build output: results/phase_01/cooja-build.log. Toolchain output: toolchain.log. Initial run: cooja-run.log and COOJA.testlog. The smoke command uses the built distribution; full rebuild can download Gradle dependencies again because the initial build container cache was ephemeral. Paths in the initial command are this machine's paths; adjust bind mount sources for another checkout.

To restore source on another machine: clone official contiki-ng, checkout the recorded Contiki commit, initialize tools/cooja recursively and verify its recorded SHA, pull the recorded image digest, run python3 scripts/prepare_phase1.py, then build/run using the command above with corrected host paths. Other hardware-platform submodules were not required for native Cooja and remain uninitialized.

Formal G0 still needs two students' manual verification per the master. Headless automated evidence is complete; GUI display and independent clean-machine reproduction are not yet validated.
