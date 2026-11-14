# Phase 4 — Downloads, Problems and Resolutions

**Date:** 14 November 2026

---

## Downloads / New Dependencies

No new packages downloaded in Phase 4. All work used:

- Pinned Contiki-NG commit `a304687372e2917d325d4d71cf68610fe9a6279b`
- Pinned Cooja commit `fabff3ee41eeeb6f3de7bd11f7c9cdf0a7d7dfc4`
- Pinned Ascon-C commit `446347f21b209f3921c65ece70027c366cbe1693`
- Official container `contiker/contiki-ng@sha256:b14d5afb0a2a852d9e72bbed607ead03f6ccc5f4d4dee44f0799110be2f4b609`
- TI datasheet PDFs archived at `results/phase_04/msp430f2617-SLAS541M.pdf` and `cc2420-SWRS041C.pdf`

---

## Problems and Resolutions

### P1 — Z1 CC2420 hardware AES accepted wrong key

**Discovered:** `validation-20261114T061839506081Z` — wrong-key fixture was accepted (root read counter 6, reading 2147483647) under default Z1 hardware AES path.

**Root cause:** Pinned MSPSim `CC2420.java` strobe dispatcher has no SAES implementation. The hardware AES capability flag was enabled but no actual AES operation was performed; any key produced a "valid" tag.

**Fix:** `firmware/crypto/aes-backend.mk` explicitly selects `AES_128_CONF=aes_128_driver` (Contiki vetted software implementation) for all application and KAT builds.

**Verification:** `results/phase_04/z1-software-aes-kat/COOJA.testlog` — PHASE3_KAT_PASS. Exact formerly failing attack case passed at `20261114T063051801657Z-B1-2`.

**Preservation:** 31 pre-fix manifests excluded from secure-comparison qualification; listed in `closure-progress-20261114.json`. Artifacts intact.

---

### P2 — MSPSim native `int` is 2 bytes, mailbox broke on Z1

**Discovered:** Boot grant not received on Z1 — simulator wrote 32-bit magic `0x42544731` as `int`, MSP430 `int` is 16 bits, value truncated.

**Root cause:** `boot_gate.c` and runner used `int`-width grant; `MspMoteMemory.java` declares 2-byte int on MSP430.

**Fix:** Mailbox replaced with explicit 4-byte array `[0x42, 0x54, 0x47, 0x31]`. Runner uses `setByteArray` with size-verified symbol. Shared C code uses `memcmp` on 4 bytes.

**Verification:** `results/phase_04/resolution-host-20261114.log` — Z1 B2 protected network pass at `20261114T201854256422Z-B2-2`.

---

### P3 — NETSTACK_MAX_ROUTE_ENTRIES=8 missing 9th mote

**Discovered:** Root+8 scenario: node 9 never transmitted. `uip-sr.c` stores root+children; default 8 entries covers root + 7 clients only.

**Root cause:** Initial fix was placed in a local project-conf.h that was not selected by the include path — `viewconf` still showed 8.

**Fix:** `firmware/project-conf.h` (shared, always included) sets `NETSTACK_MAX_ROUTE_ENTRIES=LAB_LAST_NODE`. `LAB_LAST_NODE` = `clients+1`, e.g. 9 for 8-client scenario.

**Verification:** `results/phase_04/z1-route-config-inspection.log` documents the original failure. `20261114T054039517811Z-B1-8` transmitted from all 9 nodes (pre-AES-fix, excluded from secure comparison but confirms routing fix).

---

### P4 — B4 sender deadline exceeded (hold 3015ms vs 3000ms)

**Discovered:** `validation-20261114T063559727572Z` case 25 (static-123456): node 4 reported hold 3015ms against the 3000ms bound.

**Root cause:** Emulated Z1 scheduling jitter — the 125ms service tick fires slightly late, causing the oldest reading to be held 15ms over the deadline before the flush check runs.

**Fix:** Added 125ms early-flush lead (`flush_lead_ms=125`) for Z1 Phase 4 runs. Sender flushes at `deadline_ms - 125ms` on Z1. Zero lead retained for native (native scheduling is tighter). Added DROP71 for readings already expired when serviced.

**Bounds unchanged:** Validation still enforces original 3000ms submission bound.

**Verification:** `20261114T070425862495Z-B4-8/manifest.json` — max_hold_ms = 3000. Pass.

---

### P5 — Sensor reset fixture was insufficient

**Discovered:** Initial fixture reset sensor 2 after it submitted a packet but before root had authenticated and received it. This did not prove authenticated root receipt before the reset.

**Root cause:** Fixture design — reset triggered on sensor TX event, not root RX event.

**Fix:** Scenario script now waits for `RSLAB,1,RX2,2,` (root authenticated receive from sender 2) before replacing sensor 2. Metrics require: 2 boot requests for node 2, authenticated RX before last boot, no TX/GEN/CONTEXT_READY after final boot.

**Verification:** `20261114T070903748685Z-B1-2/manifest.json` (B1) and case 13 of `validation-20261114T075313282538Z` (B2) — both pass.

---

### P6 — Z1 optimized Ascon backend fails mote KAT

**Discovered:** `z1_kat_02/COOJA.testlog` — PHASE4_KAT_FAIL on Z1 with `opt32_lowsize` backend, despite host corpus passing.

**Root cause:** Not isolated. Hypotheses include compiler integer-width assumptions, alignment or optimizer flags on MSP430. Exact vector/operation not identified.

**Resolution:** Optimized backend excluded for Z1. Reference backend (`ref`) used for all Z1 application and KAT builds. Failure artifact preserved at `z1_kat_02/`. Sky target also excluded (ROM overflow 4136 bytes for reference, 3696 for optimized — `sky-feasibility-20261114.log`, `sky-opt32-build-20261114.log`).

---

### P7 — energy_reconcile trailing RAW at horizon boundary

**Discovered:** This session — static seed 123458, B1-8 run: node 4 had 100 `ENERGY_RAW` events vs 99 `ENERGY_MODEL` events. `ValueError: Missing model/counter snapshots`.

**Root cause:** Firmware emits `ENERGY_RAW` then `ENERGY_MODEL` in same code branch. At simulation horizon, `PHASE4_SCHEMA2_COMPLETE` fires between the two log lines for the last tick on node 4.

**Fix:** `host/energy_reconcile.py` now accepts `len(raw) == len(logged)+1` and trims the trailing unmatched raw (`raw = raw[:len(logged)]`). Rejects any other mismatch as before.

**Verification:** `results/phase_04/static-123458-rerun.log` — all 4 arms (B1/B2/B4/B5) pass. `PAIRED_EMULATED_125MS_SERVICE_BOUND`.

---

### P8 — Nashorn `Array.fill` not implemented in MSPSim JS engine

**Discovered:** First Z1 B2 run `20261113T202559430948Z-B2-2` — Nashorn threw on `Array.fill` in scenario script.

**Fix:** Replaced `Array.fill` with explicit zero-initialization loop in runner's provisioning JS.

**Verification:** `20261113T202636104292Z-B2-2` — Z1 B2 pass.

---

### P9 — Root+8 Z1 node 9 no TX (routing/resource failure)

**Discovered:** `20261113T205744358053Z-B1-8` and `20261113T210119018233Z-B1-8` — node 9 had no TX events, only queue/no-route drops.

**Status:** Not fully diagnosed. These ran under hardware AES (pre-P1 fix) so they are already excluded from secure comparison. After P1+P3 fixes, all subsequent root+8 runs transmitted from all nodes. Failure preserved.

---

## Summary Table

| ID | Problem | Fixed | Verification |
|----|---------|-------|-------------|
| P1 | Z1 hardware AES accepts wrong key | Yes | z1-software-aes-kat PASS |
| P2 | Mailbox int width on MSP430 | Yes | resolution-host-20261114.log |
| P3 | Route entries missing 9th mote | Yes | z1-route-config-inspection.log |
| P4 | B4 deadline 3015ms | Yes | 070425862495Z-B4-8 max_hold=3000 |
| P5 | Sensor reset fixture insufficient | Yes | 070903748685Z-B1-2 PASS |
| P6 | Z1 optimized Ascon KAT fail | Excluded | z1_kat_02 preserved |
| P7 | Trailing ENERGY_RAW at horizon | Yes | static-123458-rerun.log PASS |
| P8 | Nashorn Array.fill missing | Yes | 202636104292Z-B2-2 PASS |
| P9 | Root+8 node9 no TX | Preserved | Pre-fix runs excluded |
