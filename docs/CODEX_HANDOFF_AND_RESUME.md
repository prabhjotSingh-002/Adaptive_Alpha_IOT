# Codex handoff and resume guide

> Newer resume prompt: [NEXT_AI_IDE_RESUME_PROMPT.md](../NEXT_AI_IDE_RESUME_PROMPT.md) records the later Phase 4 implementation, excluded Z1 AES backend, deadline fix and interrupted matrices. Read that prompt with the latest journal before relying on this historical snapshot.

> Planning navigation update: use [the current Phase 4 plan](../PLANS/PHASE_04_IMPLEMENTATION_PLAN.md) and [planning index](../PLANS/README.md). Phase-by-phase executed work is indexed separately in [the journey](../phase_jouney/README.md). The snapshot below retains historical implementation details; check the latest journal before acting.

Snapshot date: 14 November 2026, Asia/Kolkata.
Workspace: `/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT`.
Purpose: give another Codex window the recorded project history, reading order, actual implementation state and continuation instructions. This is a handoff snapshot; inspect newer journal entries and source changes before acting.

## 1. Start in another window

Open this same project directory and give the new session the resume prompt in Section 12. Ask it to read this document and the linked project records before editing.

Use the files below as the durable record. This guide summarizes the decisions and recorded execution; it is not a verbatim transcript of every chat message. Test assertions must be verified from raw evidence or rerun when evidence is missing.

Only one window should own implementation at a time. Stop editing/running experiments in the old window before the new window becomes the writer. A read-only review can happen separately. The runner lock protects generated builds; it does not coordinate simultaneous source edits by two sessions.

The user has already authorized completing Phase 4 according to its saved plan. No new design approval is needed for routine work in that scope. The current user request that created this guide is documentation-only; start implementation in the new session when given the resume prompt. Environment approval prompts may still be required for restricted filesystem, Docker or network operations.

## 2. User preferences and permanent constraints

- Follow the authoritative master and companion decisions; do not rewrite them without an explicit user instruction.
- Proceed phase by phase. Complete the current phase's required work, write detailed logs/reports, then stop before the next phase.
- Never delete `tmp/` or its contents, even during cleanup. Its temporary plans are permanent records.
- Use the spelling `phase_jouney` because that is the actual repository directory.
- Reuse official networking, simulator, toolchain and vetted cryptography. Keep implementation DRY and maintainable for later policy work.
- Explain actual downloads and problems in simple Hinglish. Record what changed, why, how, tests, failures/resolution and downstream impact.
- Approximately 4GB RAM affects concurrency, not required deliverables. Use serial firmware builds and simulations.
- The user repeatedly requested full Phase 4 completion. Previous turns stopped after small increments; do not interpret those partial handoffs as completion or as a requirement to ask for permission after every increment.
- Never manufacture logs, benchmarks, reviewer sign-off, security guarantees or energy gains. Human gates remain pending until performed.
- N0 is unprotected. Host fixtures and host crypto tests are validation inputs, not network research results.

Read the actual [AGENTS.md](../AGENTS.md); it governs project collaboration.

## 3. Required reading order

Read the following before continuing implementation:

1. [AGENTS.md](../AGENTS.md).
2. [MASTER_IMPLEMENTATION_PLAN.md](../PLANS/MASTER_IMPLEMENTATION_PLAN.md), especially security, energy, telemetry, experiments, validation gates and calendar.
3. [IMPLEMENTATION_AND_DECISION_REVIEW.md](../PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md), especially W6/W7 and reuse decisions.
4. [Phase index](../phase_jouney/README.md).
5. [Current Phase 4 implementation plan](../PLANS/PHASE_04_IMPLEMENTATION_PLAN.md), then its linked preserved original plan, all sections.
6. [Current Phase 4 execution journal](../phase_jouney/phase_04_environment_and_implementation.md), including its latest entries.
7. [Phase 3 report](../phase_jouney/phase_03_detailed_report.md), [journal](../phase_jouney/phase_03_environment_and_implementation.md), [download/problem report](../phase_jouney/phase_03_downloads_problems_and_resolutions.md) and [preserved plan](../tmp/phase_03_implementation_plan.md).
8. [Phase 2 report](../phase_jouney/phase_02_detailed_report.md), [journal](../phase_jouney/phase_02_environment_and_implementation.md) and [preserved plan](../tmp/phase_02_implementation_plan.md).
9. [Phase 1 journal](../phase_jouney/phase_01_environment.md) and [downloads/problems](../phase_jouney/phase_01_downloads_problems_and_resolutions.md).
10. [Architecture](architecture.md), [protocol](protocol.md), [security contract](phase3-security-contract.md), [threat model](threat-model.md), [Phase 3 usage](phase3-usage.md) and [Linux setup](setup-linux.md).

Read the authoritative documents themselves. Do not substitute this summary for their scope and gates. Some early documents describe the state at their original creation; later journals contain subsequent progress.

## 4. Phase history and current status

| Phase | Recorded work | Remaining limits |
|---|---|---|
| 1 | Official pinned Contiki/Cooja environment; unchanged RPL root and eight clients; repeated headless smoke | Two-student G0 manual review still pending |
| 2 | Shared bounded reading codec, aggregation, UDP application, deterministic generator, runner/parser/metrics and N0 pilot | Results are explicitly unprotected; human/reproduction checks not inferred |
| 3 | Vetted AES-CCM wrapper, authenticated envelope, packet replay, simulator boot grant, secure B1/B4 pilot and controlled rejection/reset tests | Expanded end-to-end tests and independent review remain pending |
| 4 | Official Ascon source downloaded; bounded adapter; 1,089 official host vectors; initial profile-aware secure packet integration and host regressions | Application/runner/Cooja integration, energy/depletion/lifetime, broader validation and final reports unfinished |
| 5 | Adaptive policy and controls | Not started |
| 6 | Full research matrix, statistics, reproducibility and release | Not started |

At this snapshot the phase index still labels Phase 4 `Pending`. The Phase 4 journal and actual code establish that it has started. Correct that index as part of the next implementation/documentation update; do not conclude that Phase 4 is either untouched or completed.

The original master retains its midterm dates and later research scope. This handoff does not reschedule the project.

## 5. Existing implementation that must be reused

- `firmware/common/protocol.c/.h`: explicit serialization, 11-byte header, 10-byte reading, bounded capacity 4, strict decoding and reading-ID window.
- `firmware/aggregate/`: bounded ring, byte/count constraints, oldest-reading deadline, separate build/commit operations. No heap-based replacement needed.
- `firmware/sensor/sensor.c` and `firmware/root/root.c`: existing processes using official networking. Extend these instead of creating separate baseline apps.
- `firmware/crypto/aes_ccm.c/.h`: pinned Contiki CCM/AES adapter; 13-byte nonce, 16-byte tag, private authentication scratch.
- `firmware/crypto/secure_packet.c/.h`: common envelope and replay lifecycle; now partially generalized for Ascon.
- `firmware/crypto/boot_gate.c/.h`: default-locked contexts and one-use Cooja mailbox grant outside mote RAM.
- `host/run_experiment.py`, `parse_logs.py`, `metrics.py`, `plots.py`: one execution/analysis pipeline.

Critical behavioral details:

- Sensor GEN happens before crypto/network work. Preserve deterministic identities, values and traffic schedule across controls.
- Global simulator timestamps determine end-to-end delay. Source-local timestamps do not replace them.
- At 1Hz, a 3-second oldest-reading deadline flushes a count-3 batch before the fourth reading is offered. Cap 4 is separately exercised with faster traffic.
- Protected sizes are 37/47/57/67 bytes for one through four readings. Count the 16-byte tag once; N0's reserved space is not an actual tag.
- Local UDP submission is not proof of root delivery. Root authenticated receive events determine secure delivery.
- Packet replay and source-reading deduplication are separate concerns. Future profile switching must preserve independent packet contexts and shared reading identity.
- Do not modify upstream Contiki/Cooja core or implement cryptographic primitives yourself.

## 6. Exact partial Phase 4 work

New files already present:

- `firmware/crypto/ascon_aead.c/.h`.
- `tests/security/test_ascon_aead.c`.
- `tests/security/test_ascon_vectors.c`.
- `tests/security/test_ascon_packet.c`.
- `scripts/test_phase4_ascon.sh`.
- `phase_jouney/phase_04_environment_and_implementation.md`.

Existing files changed: `firmware/crypto/secure_packet.c/.h`.

The Ascon wrapper enforces bounded lengths, uses separate upstream input/output buffers, and only copies plaintext to the caller after successful authentication. It wraps the official reference backend; it does not implement a new primitive.

The secure context now has a profile field and `lab_security_init_profile`. Legacy `lab_security_init` still selects AES profile 1. `LAB_ENABLE_ASCON` enables profile 2 dispatch. Unsupported profiles initialize invalid. AES retains its original nonce; Ascon uses the planned 16-byte context nonce with three trailing zero bytes.

This is partial host integration. `firmware/Makefile` has not yet wired the Ascon backend into application builds. The sensor/root and provisioning still assume AES in key locations. The runner and parser still contain profile-1 assumptions. There is no `configs/phase4.json` or completed production energy module at this snapshot.

Recorded actual host test outcomes, both processes exited 0:

| Script | Reported outcome |
|---|---|
| `scripts/test_phase4_ascon.sh` | Empty official vector and bounds/isolation; 1,089 official vectors for seal/open; Ascon packet dispatch/profile mismatch/replay checks passed under ASan/UBSan |
| `scripts/test_phase3_crypto.sh` | AES NIST vectors and negative adapter checks; existing secure-packet authentication/replay/lock tests passed after profile changes |

The Phase 4 unit directory currently contains compiled test executables. The test scripts print output but do not yet preserve a complete Phase 4 raw log/provenance manifest. The journal records the observed output. During continuation, capture fresh logs and source/config/binary hashes; do not invent historical raw logs from journal summaries.

## 7. Dependencies, pins and environment

Use [source-pins.json](../results/setup/source-pins.json) and verify against actual checkouts:

| Dependency | Pin |
|---|---|
| Contiki-NG | `a304687372e2917d325d4d71cf68610fe9a6279b` |
| Cooja | `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4` |
| Official image | `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609` |
| ascon-c checkout | `446347f21b209f3921c65ece70027c366cbe1693` |

Ascon lives under `external/ascon-c`; checkout size was approximately 25 MB. The reference directory is `crypto_aead/asconaead128/ref`, implementation file `aead.c`. It is the standardized variant, not an old Ascon-128/128a vector set.

The matching corpus is `external/ascon-c/crypto_aead/asconaead128/LWC_AEAD_KAT_128_128.txt`, SHA-256 `bbbc34692fe05e5fda0a3b025585622ab3e3747495e5e3655b29aae8c2a4bd33`.

Upstream LICENSE SHA-256 is `5537d4d10b76b81b6e8dfd8b644480a4b1efa332fbb0cdb61126c5be781ef7b4`. Preserve the actual license and record complete provenance before release.

The existing container has `/usr/bin/gcc`, `/usr/local/bin/msp430-gcc` and `/usr/local/bin/arm-none-eabi-gcc`. No additional compiler was installed for Phase 4 host tests. Finding no host GCC did not mean a toolchain download was needed. Target support and timing fidelity still require actual builds.

Typical mounts are project → `/workspace` and upstream Contiki → `/home/user/contiki-ng`. The built Cooja launcher inside the container is `/home/user/contiki-ng/tools/cooja/build/install/cooja/bin/cooja`.

The workspace sandbox has been read-only. Docker-group access failed inside it with `sg: setgid() failed: Invalid argument`; authorized execution succeeded. Use the environment's normal approval mechanism for required writes/Docker/network. Do not disable security, change Docker socket permissions or reinstall Docker as a workaround.

## 8. Commands and evidence discipline

Inspect before writing:

```bash
pwd
git status --short
git -C external/ascon-c rev-parse HEAD
git -C external/ascon-c status --short
sha256sum PLANS/MASTER_IMPLEMENTATION_PLAN.md PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md
```

Existing host test invocation, run from the workspace with required environment approval:

```bash
sg docker -c 'docker run --rm --mount type=bind,source=/home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT,destination=/workspace contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609 bash /workspace/scripts/test_phase4_ascon.sh'
```

The AES regression uses the same command with `/workspace/scripts/test_phase3_crypto.sh`. Capture exit status and raw output to a new named evidence file when rerunning. Preserve failures and earlier artifacts; do not overwrite the only copy of historical evidence.

All generated config/build work must share the runner's existing `results/phase_02/.runner.lock`. Do not introduce a Phase 4-only lock while other phases use the original lock. Standalone host tests must also avoid concurrent writes to identical output binaries.

The project has no initial project commit at this snapshot and many files are untracked. Do not use reset/clean or treat untracked files as disposable. `.gitignore` ignores `external/`, so a simple Git diff/commit does not preserve downloaded dependencies. Record pins and licenses. A transfer to another machine requires dependency recovery and separate evidence backup.

Run manifests must use an actual revision or null if no commit exists. An earlier runner incorrectly stored literal `HEAD`; later Phase 3 runs corrected this. Preserve historical manifests and use source hashes as authority.

Authoritative hashes to preserve:

- Master: `2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385`.
- Decision review: `69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a`.

## 9. Phase 3 evidence and inherited debt

Use the [Phase 3 evidence index](../results/phase_03/phase3-evidence.json) and [detailed report](../phase_jouney/phase_03_detailed_report.md) for exact artifacts.

The current primary pair is `results/phase_03/20261113T103709606387Z-B1-8` and `results/phase_03/20261113T103749292302Z-B4-8`. Both delivered 192 of 192 authenticated readings with exactly matching generation tuples; application submissions were 192 versus 64. These are engineering pilot results with one seed.

Keep these pending checks visible:

- Deliberate over-the-air reordering.
- Deliberate radio-layer loss. The earlier counter gap was a pre-UDP omission, not radio loss.
- End-to-end authenticated malformed-body rejection. A later production-code host test passed; Cooja evidence is pending.
- End-to-end critical-event flush. A shared aggregation unit test is not the complete integration test.
- Two-student G0 verification and independent human/reproduction review.

Native Cooja functionality and native shared-library sizes do not establish hardware timing, embedded RAM use or physical energy. No current Ascon network or energy result exists.

## 10. Continue Phase 4 in this order

Follow the [current Phase 4 implementation plan](../PLANS/PHASE_04_IMPLEMENTATION_PLAN.md) together with its linked preserved original requirements. Its work packages are the completion contract:

1. P4.0: verify baseline/pins, record current state and inherited checks; retain old evidence.
2. P4.1: finish adapter provenance and adversarial validation; preserve complete host test logs/hashes.
3. P4.2: integrate both protected profiles through provisioning, boot gate, sensor/root, build files, runner/parser/metrics; run actual mote vectors and B2/B5 root+2 smoke; retain AES/N0 regressions.
4. P4.3: validate a supported emulated target and timing source early. Compiler presence alone does not prove stack compatibility or energy fidelity.
5. P4.4: use official Energest counters and a sourced component power model; implement/test shared production energy arithmetic and reconcile telemetry.
6. P4.5: implement terminal simulated depletion, including forwarding/radio shutdown; validate an actual multi-hop forwarder and lifetime-aware completion/accounting.
7. P4.6: actual four-arm static pilots B1/B2/B4/B5 with matched conditions, required seeds/boundaries and inherited automated checks.
8. P4.7: complete detailed reports, evidence index and honest gate ledger, then stop before Phase 5.

Specific integration traps already identified:

- Runner currently derives phase from profile 1 vs everything else; profile 2 would be misrouted without explicit phase handling.
- Profile-1 assumptions occur in sensor/root, parser, metrics, key provisioning and labels. Unknown nonzero profiles must never be assumed authenticated.
- Root contexts must be bounded and keyed by allowed sender/profile/epoch. Packet replay must remain transactional on invalid tags or malformed bodies.
- Returning AES → Ascon → AES must retain per-profile counter/replay state. Do not reinitialize on every selection.
- Current metrics require every scheduled reading and DONE from all clients. Depletion needs verified terminal events, actual generation accounting and separate scheduled-demand shortfall.
- Lifetime runs can have different realized generation after death. Keep identical prospective demand and verify alive intervals; retain strict trace matching for non-depletion controls.
- G4 requires stopping forwarding/radio, not merely the sensor generator. Verify no timer reactivation and document in-flight boundaries.
- Energest totals can be 64-bit while the underlying timer is narrower; validate wrap-safe sampling. CPU and radio timelines overlap; use component currents without double-counting whole-board power.
- Native host wall time is not mote crypto energy. Keep full energy claims pending until the model/timing path is validated.
- No observed FND/HND/functional-failure event means censored data, not a fabricated death at the horizon. Freeze budget/window/threshold rules before comparative runs.

## 11. Documentation required at Phase 4 completion

Continue the existing execution journal and create the plan's final documents when actual work supports them:

- `phase_jouney/phase_04_detailed_report.md`.
- `phase_jouney/phase_04_downloads_problems_and_resolutions.md`.
- `docs/phase4-usage.md`.
- `results/phase_04/phase4-evidence.json` with actual artifacts/hashes and gate mapping.
- Updated phase index with accurate automated/human gate status.

Record each change's purpose, implementation, commands, actual output/errors, fixes, dependency/download scope, limitations and future impact. Never retroactively label the existing host corpus pass as an on-mote or research result. Stop after Phase 4 and wait for the user's Phase 5 instruction.

## 12. Ready-to-paste prompt for the new session

```text
Workspace: /home/vanitas_archiviste/myDEV_linux/adaptiveAlpha_IOT

Resume this existing project and complete Phase 4 according to
PLANS/PHASE_04_IMPLEMENTATION_PLAN.md.

First read docs/CODEX_HANDOFF_AND_RESUME.md and follow its required reading
order: AGENTS.md, both original PLANS documents, current Phase 4 plan/journal,
Phase 1–3 reports and relevant actual code/evidence. Verify current workspace
state before editing; this handoff may be older than the latest journal.

Phase 4 is partially implemented: Ascon adapter, 1,089 official host vectors,
initial profile-aware secure packet dispatch and AES host regressions exist.
Sensor/root/runner/Cooja integration and energy/depletion/lifetime remain
pending at the handoff snapshot. Do not restart from scratch or claim Phase 4
complete based on those host tests.

Proceed through the remaining authorized Phase 4 work, tests and evidence.
Use the pinned official environment and upstream cryptographic source. Keep
one writer for shared config/builds. Explain actual problems/downloads and
ask only when essential information or environment approval is required.
Record detailed work continuously in phase_jouney. Preserve all failures.

Never delete phase_jouney/tmp or its contents. Do not change the original
plans without my explicit instruction. Human gates stay pending until done.
Complete Phase 4 reports and stop before Phase 5. Keep me updated in Hinglish.
```

Before handing control over, ensure the old window is no longer editing or running experiments. The new session should begin with source/journal inspection and an accurate short status update, then continue the remaining implementation.
