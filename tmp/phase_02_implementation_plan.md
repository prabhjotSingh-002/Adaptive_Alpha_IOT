# Temporary Phase 2 implementation plan

Status: executed; automated Phase 2 work complete. Final report: ../phase_02_detailed_report.md. This file was written before source implementation and retained as requested.
Authority: PLANS/MASTER_IMPLEMENTATION_PLAN.md Sections 3,4,6,7,8 and PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md W1–W3. Original plans stay unchanged.

## Scope and sequence
1. Specify diagnostic v1 wire format and RSLAB events, failure/dedup semantics and experiment timing.
2. Implement portable bounded encoding/decoding and a fixed-memory ring aggregator using shared production C sources for host tests and firmware.
3. Test caps 1/2/4, deadline boundary/wrap, byte limit, overflow, wrong sender, duplicate IDs, build without commit, malformed packets and duplicate accounting. Use warnings-as-errors and sanitizers in the existing pinned container.
4. Add thin Contiki sensor/root processes using simple-udp and built-in etimer; preserve RPL/6LoWPAN/MAC. Generate a finite deterministic reading trace independently of batching/network RNG. Log generation, submission, drop and root receive events. Unknown security profiles rejected; Phase 2 only accepts explicit profile 0/N0.
5. Config-driven runner generates firmware config and saved scenarios; verify custom 1+2 then 1+8 topology, N0 caps 1 and 4, deadline-only and byte-limit flushes. Include raw simulator timestamps, config/source/binary hashes and process status. Reserve tag space without claiming AEAD or fragmentation safety.
6. Normalize simulator-global GEN/TX/RX timestamps, validate all generated/submitted/received IDs and deadlines, compare paired generation traces and compute diagnostic packet/PDR/latency summaries centrally. Distinguish missing delivery from instrumentation failure. Use standard-library Python initially; no new host installs expected.
7. Inspect actual radio frames for fragmentation evidence, retain result/limitations; reject unsupported claims. Run Phase 1 regression, inspect upstream diffs and original plan hashes.
8. Write detailed phase journey plus downloads/problems/resolutions report; stop before Phase 3.

## Initial pilot parameters (engineering pilot, not frozen main research protocol)
One root/eight clients; seed 123456; warmup 60 s; 24 readings/client; period 1 s; caps 1 and 4; batch deadline 3 s; 15 s drain; identical generated values and schedules. Use the Phase 1 topology subset. Local boot timestamps are payload metadata; global simulator times define measured end-to-end latency. Extend scenarios only if evidence justifies, and record changes.

## Acceptance and boundaries
Production modules pass meaningful host tests and actual mote builds. All clients generate expected IDs; no unlogged drops; same readings/schedule in matched arms; received IDs unique/accounted; deadline and byte caps checked. One-command runner saves manifests even on failure. N0 results explicitly unprotected; G2 and protected G3 not passed. Formal G0 human review remains unverified and is not inferred from authorization. No source changes upstream; no invented results; no change to original research scope.

## Plan provenance at implementation start
{
  "PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md": "69b6033b2301d61c160c5d8f8ecc1107afb0bfe9fd0c73063d23b92d861d3e3a",
  "PLANS/MASTER_IMPLEMENTATION_PLAN.md": "2fad0d0b731e4b57409e3500bd18597c34e83991b6e495b2d60b94daab0bc385"
}
