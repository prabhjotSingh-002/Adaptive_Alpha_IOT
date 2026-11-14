# Phase 3 detailed implementation and verification report

**Status:** AES-CCM implementation and the requested automated engineering pilot were executed. Automated Cooja evidence supports the G2 roundtrip/failure scenarios and protected batching/size/deadline work for G3. Formal human review and the additional coverage listed below remain pending. This report does not claim independent reproduction, production security, hardware accuracy, an energy result or completion of later phases. Phase 4 has not started.

## Scope and prior phase connection

The original [master](../PLANS/MASTER_IMPLEMENTATION_PLAN.md) and [decision review](../PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md) remain unchanged. The preserved [temporary Phase 3 plan](tmp/phase_03_implementation_plan.md) guided the work. Phase 1's pinned official Cooja/Contiki/image and RPL topology were reused. Phase 2's generator, bounded reading serialization, queue, deadlines, source reading deduplication, host runner, parser and metric definitions were extended rather than replaced. N0 remains explicitly unprotected; no Phase 2 result was relabeled AES.

The original source and image pins are in [source-pins.json](../results/setup/source-pins.json). Final master and review SHA-256 are respectively 2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385 and 69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a. Tracked upstream Contiki and Cooja diffs were empty on the final audit. The project has no initial commit: final run manifests correctly record git_sha=null and actual source hashes. Create a reviewed commit before a frozen release.

## What changed and why

| Component | Implementation | Impact |
|---|---|---|
| firmware/crypto/aes_ccm.c | Bounded wrapper around the pinned Contiki CCM*/AES backend, 13-byte nonce and 16-byte tag; private decrypt scratch, full-tag comparison and wipe before return | A failed tag does not publish tentative plaintext; no new cryptographic primitive |
| firmware/crypto/secure_packet.c | AES wire envelope with exact v1 header as AAD; nonce derives from domain/profile/direction/sender/epoch/counter; per-sender 32-counter replay candidate committed only after valid authentication and decoded body | Rejects forged high counters without advancing state, and preserves the existing N0 reading codec |
| firmware/crypto/boot_gate.c | Initial locked context and one-use simulator mailbox | Controlled Cooja reset does not silently restart the same key/counter; not a production persistent-storage design |
| Sensor and root | Conditional AES profile 1, bounded 67-byte packet buffer, counter consumed before seal, root authentication then packet replay then reading dedup; separate RX_AUTH event | Both B1 and B4 share the Phase 2 queue/network path; root never uses N0 as secure fallback |
| configs/phase3.json and host runner | B1/B4 settings, fresh OS-random per-node/run test keys, simulator grant, shared existing lock, named container, copied binaries and status/hash manifests | Repeatable runs without parallel generated-config writers; normal reruns use fresh keys |
| Parser, metrics, plot | Profile-aware receive and wire lengths, 16-byte tag counted once, authenticated delivery separate from N0, pair/plot checks | Prevents marking legacy N0 events authenticated or charting a mismatched pair |
| Test-only sensor path | Dedicated --attack-test code sends isolated malicious packets and intentionally omits one packet before UDP submission | Exercises rejection and counter-gap recovery; disabled in normal pilot builds |
| Documentation | [Security contract](../docs/phase3-security-contract.md), [usage](../docs/phase3-usage.md), updated protocol, architecture and threat model | Makes wire, key, reset and limitations reviewable |

The secure wire has an 11-byte header, 10 bytes per reading and a 16-byte tag, for total sizes 37/47/57/67 bytes for counts 1/2/3/4. The body is encrypted and all 11 header bytes are AAD. N0's 16-byte reservation in Phase 2 was not a tag. Source IP checks are not authentication.

The host provides independent random 16-byte **test keys** per sender and run. These test fixtures and generated scenarios intentionally contain key bytes; they are public research inputs and must never be used as production secrets. No registry of every prior random key is implemented; uniqueness across runs relies on OS randomness. The one-use grant is held by the Cooja script outside mote RAM; snapshot rollback of both mote and script is outside the supported model.

## Download and dependencies

Downloaded only the official NIST CAVP CCM archive: 319267 bytes, [source](https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/mac/ccmtestvectors.zip), SHA-256 0e3c96761bd8f1a0b4dfe666146c32f7d367a49968375ff091b8da9ecaa673aa. It is stored under results/phase_03/vectors/. Reused the existing official image, source checkout, Docker, Java, GCC and container matplotlib. No additional host package or image was installed. NIST vector checks are informal correctness evidence, not CAVP certification.

## Actual tests and evidence

- [Production C sanitizer log](../results/phase_03/unit/crypto-tests-reviewed.log): official NIST VTT128 Count 60 (nonempty plaintext/AAD), VPT128 Count 0 (empty plaintext), VADT128 Count 0 (empty AAD), 16-byte tag, 13-byte nonce, plus wrong key/AAD/ciphertext/tag, caller-output isolation, secure packet replay, 31/32 replay-window edge and counter exhaustion. Empty payload markers in the NIST archive are interpreted using the section's zero length.
- [Python log](../results/phase_03/unit/python-tests-reviewed.log): 12 parser/metrics tests passed, including profile/authentication gating and tag accounting.
- [N0 shared C sanitizer log](../results/phase_03/unit/n0-core-tests.log): existing codec and aggregation boundaries passed.
- [On-mote NIST KAT](../results/phase_03/cooja_kat_01/COOJA.testlog): production adapter encrypted/decrypted official Count 60 and rejected a bad tag on actual native Cooja mote; TEST OK.
- [Boot reinitialization](../results/phase_03/cooja_boot_01/COOJA.testlog): initial grant, successful seal, application security-context reinitialization, no second grant and locked operation.
- [Fresh mote replacement](../results/phase_03/cooja_reset_01/COOJA.testlog): fresh native mote instance received no second grant and stayed locked for 16 checks.
- [Root replacement run](../results/phase_03/20261113T102318076649Z-B1-2/manifest.json): one authenticated receive before replacement; regrant refused; 47 subsequently incoming packets rejected while root remained locked. The intentionally low delivery is a security test, not a pilot.
- [Network tamper and gap run](../results/phase_03/20261113T103630420731Z-B1-2/manifest.json): seven injected packets rejected: replay, altered tag, altered header/counter, wrong key, altered ciphertext, profile-0 downgrade, unknown profile. Valid authenticated controls occurred before and after. One explicitly logged pre-submission drop created counter gap 2; 47/48 generated readings were delivered. This is not a radio loss measurement or a clean comparison run.
- Actual authenticated B4 boundary runs: [500ms / count 4](../results/phase_03/20261113T101818257792Z-B4-2/summary.json), [4000ms / deadline flush](../results/phase_03/20261113T101843424820Z-B4-2/summary.json), [47-byte budget / count 2](../results/phase_03/20261113T101907182564Z-B4-2/summary.json). All recorded 48/48 deliveries and zero observed fragment dispatches in those runs.
- N0 1+2 regression matched its generation traces; unchanged [Phase 1 smoke](../results/phase_01/smoke-20261113T102520721060Z/manifest.json) passed.
- [Expected timeout test](../results/phase_03/20261113T103314659067Z-B1-2/manifest.json): 1-second timeout produced a failed manifest, then the runner successfully stopped its own uniquely named container. This intentional failed run is preserved. Docker printed a deprecation notice for the stop --time option; cleanup still returned zero.
- [Native binary size](../results/phase_03/unit/native-size.log) measured the earlier corrected pair: root text/data/bss 270974/7768/111288 bytes, sensor 272362/7856/111128 bytes. These are native Cooja shared-library sizes, not embedded board RAM measurements.

## Clean B1/B4 engineering pilot

The [B1](../results/phase_03/20261113T103709606387Z-B1-8/manifest.json) and [B4](../results/phase_03/20261113T103749292302Z-B4-8/manifest.json) runs use one root, eight sensors and seed 123456. Their [paired comparison](../results/phase_03/20261113T103749292302Z-B4-8/paired-comparison.json) confirms all 192 generation tuples, including simulator-global timestamps, matched exactly.

| Actual metric | B1: AES single | B4: AES batch cap 4 |
|---|---:|---:|
| Generated / unique authenticated delivered | 192 / 192 | 192 / 192 |
| Application packets submitted | 192 | 64 |
| Application packet bytes including tags | 7104 | 3648 |
| p95 generation-to-root delay | 109.716 ms | 3079.706 ms |
| Maximum queue hold at flush initiation | 0 ms | 3000 ms |
| Observed batch counts | 1 | 3 |
| Captured fragment dispatches | 0 | 0 |

At 1 Hz, the 3-second oldest-reading deadline flushes before a fourth reading arrives; the 500ms boundary test demonstrates count 4 separately. Captures include control traffic; application bytes are not total on-air bytes. Fragment checks apply only to the captured supported MAC layouts/configurations. These are single-seed engineering observations, not statistical performance or energy/lifetime claims.

[Comparison chart](../results/phase_03/pilot-phase3.png) and [machine-readable evidence index](../results/phase_03/phase3-evidence.json) identify the exact sources, summaries, binaries and checksums.

## Problems, fixes and review notes

Detailed chronology and commands: [execution journal](phase_03_environment_and_implementation.md); download/environment detail: [problems and resolutions](phase_03_downloads_problems_and_resolutions.md).

- Read-only sandbox DNS and Docker group activation failed; authorized network/Docker execution succeeded. A Python test also could not create a temporary directory in the read-only sandbox; the authorized rerun passed.
- Pinned CCM returns a computed MIC and decrypts in place, so a project adapter had to compare the tag before releasing plaintext.
- A Cooja test binary was emitted under a generated mtype name, not crypto_kat.cooja; the actual binary and hash were retained.
- A provenance bug recorded literal HEAD as git_sha when there was no commit. Earlier Phase 3 manifests retain this error as historical evidence; the runner now checks git's return status and the selected final pair records null.
- Runner interruption could leave Docker work running; named-container timeout cleanup was added and verified by the preserved intentional failure. A hard OS kill is not covered.
- Independent keys generated across runs are random, but no persistent prior-key collision registry exists. A whole-simulation snapshot that restores both ledger and mote state is explicitly unsupported.

## Remaining validation and later phases

The automated tests establish the stated controlled cases, but do not claim every row of the temporary plan's larger security matrix. Explicit over-the-air reordering, deliberate radio-layer packet loss, authenticated malformed inner bodies and an end-to-end critical-event flush have not been separately demonstrated. The counter-gap test deliberately drops before UDP submission. Full review by another person, G0 two-student verification and independent clean-machine reproduction remain pending. The KAT covers one official nonempty vector on mote; empty/AAD edge vectors were host tests. These gaps must stay visible in any release and be closed before broader research/security claims.

Native Cooja timing and binary size do not establish physical device timing, memory limits, power or side-channel resistance. One seed cannot support confidence intervals or claims of general superiority. Future Phase 4 still owns Ascon and energy/lifetime, Phase 5 policy, and Phase 6 the research matrix/reproducibility work. Stop here and wait for user instruction before another phase.
