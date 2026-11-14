# Phase 3 execution journal

Status: automated implementation and engineering pilot executed; additional security coverage and human review remain pending. Original plans and phase_jouney/tmp are preserved.

## Initial inspection

Read AGENTS.md, master plan, decision review, phase index and temporary Phase 3 plan. The existing implementation is N0 only; Phase 3 requires authenticated CCM, reset and replay safety, and actual simulation evidence. No Phase 3 security gate has passed yet.

## Backend preparation
- Existing pinned Contiki and Cooja commits and original master/companion SHA-256 values match the Phase 3 plan.
- Sandbox DNS resolution failed for csrc.nist.gov; a network-enabled HEAD request succeeded (HTTP 200). Docker group activation failed in sandbox; elevated Docker info reported server 29.9.3.
- Downloaded official NIST CAVP CCM archive to results/phase_03/vectors/ccmtestvectors.zip (319267 bytes), SHA-256 0e3c96761bd8f1a0b4dfe666146c32f7d367a49968375ff091b8da9ecaa673aa. Source https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/mac/ccmtestvectors.zip. No host package or Docker image installed.
- Implemented the first portable bounded AES-CCM adapter using pinned Contiki CCM/AES, plus a host shim, NIST VTT128 [Tlen=16] Count 60 test and negative authentication tests. This is not yet integrated into firmware and is not G2 evidence.
- Ran the pinned container against scripts/test_phase3_crypto.sh: NIST VTT128 Count 60, altered tag/AAD/ciphertext and wrong-key checks passed under ASan/UBSan. This was a host test, not a Cooja result.
- Added an initial production secure-packet/nonce/replay module reusing Phase 2's shared serializer; its activation API requires a separately validated one-use provisioning mechanism. This API alone does not demonstrate reset safety.
- After adding shared packet code, reran the pinned host test command: official vector, bad tag/AAD/ciphertext/wrong key, packet replay and lock checks all passed under ASan/UBSan. These do not establish reset safety.
- Prepared a dedicated Cooja mote self-test using the same production adapter and NIST Count 60; actual simulator execution follows.

## On-mote vector proof and startup gate work
- Cooja one-mote NIST test passed: results/phase_03/cooja_kat_01/COOJA.testlog contains PHASE3_KAT_PASS and TEST OK. Actual simulation time 382000us. Build and raw logs retained.
- Initial attempt to hash crypto_kat.cooja by that name failed because Cooja renamed the built library mtype946284594.cooja; record the actual path/hash in the evidence manifest instead.
- Added boot_gate with a zero-initialized one-use mailbox, plus a Cooja harness/test for locked initial state and application security-context reinitialization. Full mote reset and root replay persistence still require separate proof.
- Actual Cooja mailbox proof results/phase_03/cooja_boot_01/COOJA.testlog: one initial grant, valid seal, application security-context reinitialization, refused regrant, and eight locked checks passed (TEST OK). This does not establish full-mote reset behavior.
- Added a separate fresh-mote replacement scenario to investigate native Cooja reset behavior without modifying upstream; it will be reported separately.
- The fresh native Cooja mote replacement test results/phase_03/cooja_reset_01/COOJA.testlog recorded one granted seal, a new mote instance, refused regrant and sixteen locked checks (TEST OK). It does not yet prove root reset behavior or arbitrary simulator snapshot rollback.
- Started integrating the shared secure packet and boot gate into existing sensor/root processes under compile-time profile 1; N0 remains profile 0. Network builds and delivery are not yet verified.
- Extended the existing runner for Phase 3 B1/B4 using fresh OS-random simulation-only keys, Cooja mailbox provisioning, and the existing Phase 2 lock. Extended parser/metrics for protected wire lengths and authenticated RX events. These are implementation changes awaiting real network builds, negative tests and review; no pilot result is claimed.
- B1/B4 protected 1+2 and 1+8 runs passed accounting and exact paired generation checks. 1+8 raw summaries and frame captures are saved in results/phase_03/20261113T101722604824Z-B1-8 and results/phase_03/20261113T101741421306Z-B4-8. This remains one-seed engineering evidence, subject to negative-security and release review.
- B4 boundary runs at 500ms period, 4000ms period and 47-byte budget passed; see run IDs 20261113T101818257792Z-B4-2, 20261113T101843424820Z-B4-2 and 20261113T101907182564Z-B4-2.
- Read-only sandbox could not create Python test temporary files; reran with permission and all ten legacy unit tests passed. Added a separately identified test-only packet injection path for real root rejection evidence; it is disabled in normal pilots.
- Security injection run 20261113T102042016664Z-B1-2 passed: root rejected one replay, one modified tag, one modified header and one wrong-key packet, with valid authenticated controls before/after. This is an isolated test build.
- N0 1+2 paired regression passed (20261113T102118635213Z-N0-single-2 and 20261113T102135883286Z-N0-batch-2), with matching generated traces.
- Improved runner to preserve per-run binary copies and finalize pair metadata hashes, and changed plot labels/validation to distinguish N0 and AES. Earlier runs retain their original manifests and do not contain saved binary copies; rerun final candidate after this improvement.
- Prepared a dedicated root replacement test; outcome is not yet known.
- Actual root replacement security run 20261113T102318076649Z-B1-2 passed its dedicated checks: one valid authenticated receive before replacement, refused regrant, no post-reset acceptance and 47 incoming packets rejected. This is a controlled simulator test, not production persistent storage or snapshot rollback protection.
- Added explicit host tests for packet replay window offsets 31/32, counter exhaustion, nonce sender separation, authenticated metric gating and avoiding double-counting the 16-byte tag.
- Review found that git rev-parse HEAD printed literal HEAD on stdout despite a nonzero return code in this no-commit repository; earlier new manifests incorrectly recorded that string as git_sha. Fixed runner to use git rev-parse --verify HEAD and check the return code; old manifests remain preserved and must not be interpreted as a commit. A final pair must be rerun to prove null SHA.
- Review expanded isolated injection tests to include altered ciphertext, profile-0 downgrade and unknown profile in addition to replay/tag/header/wrong-key cases. Earlier four-case result remains preserved; the seven-case result requires a fresh actual run.
- Added exact-parameter NIST VPT128 empty-plaintext and VADT128 empty-AAD vectors to complement the VTT128 nonempty vector. The NIST files encode an empty payload/AAD as a placeholder 00; the test uses the section length of zero.
- Seven-case actual network injection run 20261113T102810541246Z-B1-2 passed with seven root rejections and valid controls around them.
- Final current-firmware B1/B4 pair: 20261113T102840621052Z-B1-8 and 20261113T102859484540Z-B4-8. Both recorded git_sha=null, retained root/sensor binaries and valid paired comparison hash; generated traces match exactly.
- Unchanged Phase 1 smoke regression passed at results/phase_01/smoke-20261113T102520721060Z. Shared N0 C sanitizer checks and 12 Python tests passed; chart at results/phase_03/pilot-verified.png uses actual pair summaries.
- Runner now names each container uniquely and attempts to stop only that container on host timeout/keyboard interrupt, recording the cleanup result. This path still requires an actual interruption test before claiming cleanup is verified.
- Expanded the dedicated injection build with a documented intentional pre-submission drop of sensor 2 packet counter 2. This exercises delivery after a counter gap, not a measured radio/link-loss event; the clean pilot build is unaffected. A fresh negative test must verify this change.

## Final audit and handoff

## Pending-check continuation
- Added a production-code host test for an authenticated malformed reading: the tag is valid, the reading ID is invalid, replay state remains unchanged, and a valid packet with the same counter is subsequently accepted. The pinned container sanitizer suite passed; see results/phase_03/unit/crypto-malformed-body.log. The first sandboxed attempt failed because the filesystem was read-only; the authorized rerun passed. This is host evidence, not an end-to-end Cooja result.
- Over-the-air reordering, deliberate radio-layer loss, end-to-end malformed-body rejection and critical-event flush remain pending. Human G0 and independent review remain pending. Phase 4 has not started.
- Current-source primary pair 20261113T103709606387Z-B1-8 and 20261113T103749292302Z-B4-8 passed with exact paired generation, retained binaries, null git SHA and hashed artifacts. Chart results/phase_03/pilot-phase3.png.
- Final seven-case injection plus intentional pre-submission counter gap run 20261113T103630420731Z-B1-2 passed. The gap is not radio-layer loss.
- NIST exact-variant host tests, 12 Python tests, N0 core sanitizer tests and Phase 1 smoke passed. Expected timeout failure and scoped container cleanup were preserved.
- Wrote detailed report, download/problem report, usage/security contract and machine-readable index. Additional on-wire reorder, deliberate radio loss, authenticated invalid inner body, end-to-end critical flush, two-student G0 and independent human reproduction remain pending. No Phase 4 work started.
