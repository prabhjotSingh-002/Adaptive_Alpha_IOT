# Phase 3 downloads, problems and resolutions

## Download and installation scope

- NIST CAVP AES-CCM test vector archive, 319267 bytes, downloaded to results/phase_03/vectors/ccmtestvectors.zip. Source: https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/mac/ccmtestvectors.zip. SHA-256: 0e3c96761bd8f1a0b4dfe666146c32f7d367a49968375ff091b8da9ecaa673aa. Reason: independently published exact AES-128/13-byte nonce/16-byte tag known answers.
- Reused existing pinned Contiki and Cooja source, the official digest-pinned image, Docker 29.9.3, Cooja Java/toolchain and matplotlib. No host package and no new image installed. Test binaries and generated results are inside the project workspace.
- NIST vector use is a correctness check, not certification. Pinned source files retain their upstream license notices.

## Observed problems and resolutions

| Problem | Evidence / cause | Resolution and impact |
|---|---|---|
| NIST hostname unavailable in sandbox | curl exit 6, DNS restriction | Authorized network request returned HTTP 200 and downloaded archive; hash recorded |
| Docker group activation denied in sandbox | sg: setgid failed | Authorized Docker info reported 29.9.3; runs use sg docker with appropriate permissions |
| Python fixture could not create temporary directory | Read-only sandbox denied /tmp and workspace writes | Authorized rerun succeeded; all 12 current Python tests passed |
| Backend CCM API did not verify incoming tag | Pinned source returns void, decrypts in-place and generates MIC | Bounded project wrapper compares 16 bytes and releases no failed plaintext; host and Cooja checks passed |
| Reset could reuse a counter with the same key | Fresh context originally starts at counter 1 | Default-locked simulator mailbox and one-use external grant; context, fresh mote and actual root replacement tests recorded |
| Unexpected Cooja output filename | Build output library named mtype*.cooja, not crypto_kat.cooja | Identified, copied and hashed actual test binary; no result invented |
| Git provenance incorrectly showed HEAD | git rev-parse printed HEAD despite failure/no initial commit | Use --verify and return code; selected final manifests say null; earlier manifests preserved with known limitation |
| Timed-out Docker client could leave container running | Runner had no owned-container cleanup | Named container and scoped stop added; deliberate timeout test exit 0 for stop. Docker warns --time is deprecated |
| Sample packet loss vs observed radio loss | Test must prove counter gap without inventing network loss | Test-only sender explicitly drops one reading before UDP, logs DROP, then receiver accepts later counters. No radio-loss claim |
| Prior paired metadata hash recorded too early | Pair file written after run manifest artifact hashes | Runner finalizes pair metadata and hashes for both current runs; old artifacts preserved |
| Phase 2 versus Phase 3 plot labels | Plot title was hardcoded N0 | Now checks pair identity/profile and labels AES separately |

The [Phase 3 evidence index](../results/phase_03/phase3-evidence.json) and [detailed report](phase_03_detailed_report.md) provide actual commands, results, boundaries and remaining checks. No phase_jouney/tmp files were deleted.
