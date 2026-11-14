# Phase 1: downloads, installation, problems and resolutions

This report consolidates the actual Phase 1 journal and saved evidence. It explains what happened and why; it does not replace the master plan or the chronological journal.

**Status:** automated environment/network work completed; two students must still perform the master G0 manual verification. No later phase has started.

## 1. Purpose and starting condition

Phase 1 established a working environment for an unchanged official RPL network: one root and eight clients. Validating the network before custom application code makes later failures easier to locate: toolchain/simulator issues can be distinguished from protocol, aggregation or security bugs.

Initial laptop inspection found Ubuntu 26.04.1, Git 2.53.0, Python 3.14.4, curl, wget and unzip. Java, javac, GCC, Make, Docker, Ant and Gradle were absent from PATH. Existing tools were reused; no reinstall was needed for Git/Python/download utilities.

Available RAM affected worker count and headless execution only. The full master scope was retained. No memory exhaustion failure was observed or established during Phase 1.

## 2. What was downloaded or installed, and why

| Item | Actual action / version | Why needed | Where it lives |
|---|---|---|---|
| Contiki-NG source | Official repository cloned; commit a304687372e2917d325d4d71cf68610fe9a6279b recorded | Existing IoT OS, RPL Lite, IPv6/6LoWPAN, MAC and official UDP examples | Project external/contiki-ng/ |
| Cooja source | Upstream submodule initialized recursively; commit fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4 | Execute Contiki firmware in simulated networks without buying hardware | Project external/contiki-ng/tools/cooja/ |
| Docker apt signing key and source definition | Downloaded official signing key; configured Ubuntu Resolute stable repository | Allow apt to authenticate and retrieve official Docker packages | /etc/apt/keyrings/docker.asc and /etc/apt/sources.list.d/docker.sources; copies under results/setup/ |
| Docker Engine / CLI | Installed system-wide; verified 29.9.3 | Run a consistent official build/simulation environment | Ubuntu system packages; daemon is a system service |
| containerd.io | Installed as Docker dependency | Container runtime management used by Docker | Ubuntu system packages |
| Docker Buildx | Installed; verified 0.39.0 | Standard Docker image-build tooling; available for future container reproducibility | System Docker CLI plugin; not exercised by the demo |
| Docker Compose | Installed; verified 5.7.1 | Standard official Docker tooling installed by reviewed package set | System Docker CLI plugin; not required/exercised by this single-container demo |
| ca-certificates and curl | Included in installer prerequisite command; curl was already present | HTTPS certificate verification and signing-key download | Host packages; the command alone does not establish whether apt newly installed or retained each package |
| hello-world image | Downloaded and run successfully | Verify the Docker daemon can pull and execute a container | Docker-managed image storage |
| Official Contiki toolchain image | Downloaded contiker/contiki-ng:develop, then pinned by immutable digest | Supply compatible Java, C and embedded toolchains without separate host installs | Docker-managed storage, root directory /var/lib/docker |
| Gradle distribution | Wrapper downloaded Gradle 9.6.1 | Build the selected Cooja revision with its specified build system | Initial build container's Gradle cache |
| Cooja build dependencies | Resolved by Gradle during successful installDist build | Supply libraries/plugins required by upstream Cooja | Initial container cache and built distribution/artifacts under project source tree |

The toolchain image contains more upstream tools than the demo needs. Downloading that image brings its packaged contents together; those are not individual host installations. The following tools were actually checked by commands inside the image:

| Tool | Observed version | Purpose in this project |
|---|---|---|
| Java / GraalVM | 25.0.3 | Matches pinned Cooja build requirement Java 25 |
| GCC | 11.4.0 | Compiles native Cooja mote firmware |
| GNU Make | 4.3 | Runs Contiki firmware builds |
| MSP430 GCC | 4.7.4 | Available for later compatible MSP430/Sky emulation; not used for this native run |
| ARM GCC | 10.3.1 | Available for compatible later targets; not used for this native run |

No separate host Java/GCC/Make installation was performed by this phase. No Ascon library, Python analysis environment or hardware SDK submodules were separately installed for future phases. Required future dependencies will be selected and logged in their corresponding phase. Ant was not needed: the selected Cooja revision uses Gradle.

A full list of transitive apt/Gradle package versions was not captured as a separate lockfile. The retained installer log, upstream revisions, actual toolchain output and immutable image digest are the existing provenance evidence; this report does not invent a more complete inventory or download-size total.

## 3. Exact selected image and source provenance

Requested source-derived image tag:

```text
contiker/contiki-ng:1a8be2d47fc7ef835f45461dbf014155d59be3e8a58e8779149d7645a7b1266c
```

That tag was not found. The actual successful image was official develop, recorded and executed as:

```text
contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609
```

The digest identifies the actual image, even if develop changes later. It does not imply the unavailable source-derived tag became available. Compatibility was verified by checking tools, building Cooja, compiling the official firmware and running the network.

The source commits and selected image are recorded in [source-pins.json](../results/setup/source-pins.json). The master plan SHA256 stayed 2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385.

## 4. Problems encountered and how they were resolved

| Problem / symptom | Observed cause | Action taken | Outcome and impact |
|---|---|---|---|
| First bootstrap did not proceed | User interrupted approval before execution | Inspected workspace for partial files/downloads before resuming | Confirmed no partial bootstrap; resumed cleanly |
| Sandbox could not modify files/download normally | Read-only filesystem and restricted execution/network policy | Used approved execution for required writes, downloads and Docker operations | Journals, sources and scripts could be created without changing sandbox policy |
| Sandboxed sudo failed with no-new-privileges | Sandbox restriction | Checked approved host execution separately | Distinguished sandbox restriction from actual host authentication |
| Host sudo reported interactive authentication required | Agent had no interactive sudo authentication | Created reviewable scripts/install_docker.sh; user ran it locally and entered password in terminal | Official Docker packages installed; hello-world passed; password was not requested in chat |
| docker info returned permission denied | User was initially not in docker group | User added account to docker group | Authorized account membership existed; no socket permission broadening used |
| Permission denied persisted after group change | Existing agent process retained old supplementary groups | Compared id with account group database; used sg docker -c to start a process with authorized group | Docker daemon access succeeded without waiting for agent logout/restart |
| Source-derived Docker image tag not found | Registry did not contain that requested tag | Pulled official develop; recorded immutable digest; validated runtime/build | Working compatible toolchain selected; fallback explicitly recorded |
| Gradle distribution download timed out three times | Wrapper reported 10,000 ms network timeouts; exact network cause not established | Allowed built-in retries; host curl redirect/connectivity check succeeded | Fourth attempt downloaded Gradle 9.6.1; Cooja build succeeded |
| Upstream saved scenario had 16 motes rather than tutorial target of 9 | Saved example topology differed from required one-root/eight-client demonstration | Derived first nine nodes in a separate project scenario | Required node count achieved without editing official client/server source |
| Saved GUI scenario had no project-specific headless acceptance check | Automated run needs termination and observable success conditions | Added ScriptRunner timeout and checks for root requests plus responses at every client | Missing required delivery would fail; actual run passed |

Group membership is a persistent host access change. Docker remained a system service; project scripts used it to run a container. No privileged container mode, hardware USB passthrough, custom networking stack or physical-device setup was needed for this demo.

## 5. What was created locally rather than downloaded

| Artifact | Why it was created | How it helps later phases |
|---|---|---|
| Git initialization and .gitignore | Establish project tracking and exclude downloaded source/runtime noise | Prepare controlled future changes; this does not mean an initial commit was created |
| scripts/install_docker.sh | Repeat official apt setup with conflict checks and logs | Explain host changes and reproduce installation |
| scripts/prepare_phase1.py | Derive required node count/headless script from official example | Keep scenario preparation reproducible |
| simulations/scenarios/phase1-rpl-9.csc | Saved one-root/eight-client headless scenario | Stable working network reference |
| scripts/phase1_container.sh | Capture toolchain versions, build Cooja and run official firmware | Reproducible initial build/run sequence |
| scripts/smoke.py and scripts/smoke.sh | Check source pins, rerun built distribution, validate response set, save status/hashes | Detect environment/network regressions before custom firmware changes |
| results/setup/source-pins.json | Record selected source/image identity | Trace dependency provenance |
| results/phase_01/evidence.json | Index hashes, counts, node IDs and limitations | Make success auditable from actual artifacts |
| docs/setup-linux.md and phase journals | Record commands, rationale and outcomes | Transfer knowledge between team members |

Builds also generated Cooja Java artifacts and native mote libraries under external/contiki-ng. Those compiled files are outputs, not modifications to upstream source. Upstream Contiki/Cooja tracked diffs were empty when checked.

The original saved scenario's first nine nodes were retained, compilation made serial, GUI-only plugins replaced with the headless test plugin, and a 600,000 ms simulated timeout added. Sensor and root application sources remained official and unchanged.

## 6. Actual verification results

- Docker installer completed and hello-world ran successfully; daemon active.
- Toolchain version checks succeeded inside the digest-pinned image.
- Cooja installDist succeeded: seven executed tasks, build log reports about two minutes.
- Initial network run exited successfully with TEST OK.
- Root ID 1 received 18 request events; clients 2–9 all received responses.
- First test ended at simulation time 48,496,368 microseconds = 48.496368 seconds.
- A second executed smoke run also passed and recorded a separate manifest.

| Client | Response events in initial run |
|---|---:|
| 2 | 3 |
| 3 | 3 |
| 4 | 3 |
| 5 | 4 |
| 6 | 1 |
| 7 | 1 |
| 8 | 2 |
| 9 | 1 |

The run terminates once all required clients demonstrate roundtrip delivery. These counts establish functionality; they do not form a fixed-duration performance or energy comparison. Simulated time is distinct from build time and real wall-clock execution time.

## 7. Evidence and repeat command

- [Docker installer log](../results/setup/docker-install-20261113T085620Z.log): host package installation and hello-world.
- [Toolchain log](../results/phase_01/toolchain.log): observed tool versions.
- [Cooja build log](../results/phase_01/cooja-build.log): download retries and successful build.
- [Initial execution log](../results/phase_01/cooja-run.log): native build and simulator status.
- [Raw simulation events](../results/phase_01/COOJA.testlog): node startup, requests and responses.
- [Evidence index](../results/phase_01/evidence.json): pins and artifact hashes.
- [Second-run manifest](../results/phase_01/smoke-20261113T090550305726Z/manifest.json): repeat execution and acceptance outcome.
- [Chronological journal](phase_01_environment.md): original progression and decisions.

From project root, using the already built distribution:

```bash
bash scripts/smoke.sh
```

Each execution creates a separate timestamped directory. Full rebuild instructions are in [setup-linux.md](../docs/setup-linux.md).

## 8. Remaining Phase 1 checks and future impact

No current installation or automated network blocker remains. Formal G0 still needs the master's two-student manual verification; GUI display and independent clean-machine reproduction were not validated by these runs. Record actual reviewer names/date/outcomes after review, rather than marking them done automatically.

Phase 1 supplies a verified environment and baseline network. It does not yet implement custom sensor readings, aggregation, application AEAD, adaptive policy or energy/lifetime experiments. Those remain in their planned phases.

The first build container was ephemeral, so its Gradle cache is not guaranteed to survive. Built distribution and logs persist through bind mounts. A full rebuild may re-download Gradle/dependencies; the existing smoke run uses the persisted built distribution.

## 9. Remaining phases by relative workload

This is an engineering estimate based on dependencies, correctness risks and evidence work. It adds no deadlines and changes no master scope. A completed phase is logged and work stops before the next phase, following the user's instruction.

| Phase | Relative size | Main work | Why this size |
|---|---|---|---|
| 2 | Medium; relatively smallest remaining | Custom reading IDs/generator, wire protocol, transport integration, bounded batching and tests | Working network exists, but queue/deadline/MTU/data-accounting correctness still needs real integration |
| 3 | Large | AES-CCM adapter, nonce/replay handling, failure tests, secure batching, runner/parser and secure pilot | Security correctness and end-to-end experiment evidence have several dependent checks |
| 4 | Very large | Ascon integration, static controls, Energest/power conversion, residual budgets and node-death/lifetime behaviour | Combines a second security backend with a validated measurement/depletion model |
| 5 | Very large | Calibration, battery-threshold and joint policy, feasible action selection, switching cost/hysteresis and ablations | Central research method; relies on trustworthy earlier cost/security/energy data |
| 6 | Large; experiment-heavy | Frozen experiment matrix, paired seeds, uncertainty, independent rerun and release/manuscript evidence | Runtime, data validation and reproducibility can dominate even if code changes are smaller |

Of five remaining phases: **four large (including two very large), one medium, zero truly small**. If using only large/small labels, Phase 2 is the one comparatively smaller phase; it should not be mistaken for a trivial task. The existing six-phase sequence remains in place.
