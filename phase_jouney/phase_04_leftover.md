# Phase 4 — Leftover / Pending Items

**Status: ALL DEFERRED CASES NOW COMPLETE — 16 November 2026**

All 7 deferred cases (cases 29–35) passed on 16 November 2026 as part of Work Package D closure per `finalPLAN_execute.md`. See the Phase 4 execution journal checkpoint dated 16 November 2026 for full run IDs, PDR, and lifetime event evidence. All 35 Phase 4 validation cases pass. Human review gates remain pending.

---

**Original record (14 November 2026):**

**Date:** 14 November 2026
**Reason for deferral:** Time constraint (mid-term evaluation 17 November 2026). Core Phase 4 implementation is complete and 28/35 matrix cases pass. These 7 cases are deferred to avoid blocking Phase 5.

---

## Pending Validation Matrix Cases

These 7 cases from `validate_phase4.py --section all` were not run:

| # | Case name | Command | Why deferred |
|---|-----------|---------|-------------|
| 29 | boundary `--period-ms 4000` | `--mode all --clients 2 --period-ms 4000` | Tool timeout (4000ms period × 24 readings = very long horizon) |
| 30 | boundary `--payload-budget 47` | `--mode all --clients 2 --payload-budget 47` | Low priority; 500ms boundary already pass |
| 31 | depletion-sensitivity-125ms | `--mode B2 --clients 2 --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 223456 --energy-sample-ms 125` | 120s warmup + 120 readings = ~10 min per run |
| 32 | depletion-sensitivity-250ms | Same as above, `--energy-sample-ms 250` | Same |
| 33 | lifetime-123456 | `--mode all --clients 2 --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 --deplete-node 2 --bottleneck --seed 123456` | ~40 min (4 arms) |
| 34 | lifetime-123457 | Same, seed 123457 | ~40 min |
| 35 | lifetime-123458 | Same, seed 123458 | ~40 min |

**Total estimated time to complete:** ~2 hours.

---

## What These Cases Would Prove

### Boundary 4000ms (case 29)
- Slower traffic (4000ms period): each sensor only flushes ~1 reading per batch even with cap 4
- Verifies deadline flush still works under low-frequency generation
- **Impact if skipped:** low — normal 1000ms scenario is the primary comparison scenario

### Boundary 47-byte (case 30)
- Payload budget reduced to 47 bytes: only 1 reading fits (47 - 11 header - 16 tag = 20 bytes = 2 readings, but 10-byte reading overhead means exactly 2)
- Verifies cap-effective-1 path under tight budget
- **Impact if skipped:** low — already tested through cap-1 modes (B1/B2)

### Lifetime / Depletion (cases 31–35)
- These are the most scientifically important deferred cases
- They would prove: actual multi-hop forwarder death, FND/HND metrics, survivor telemetry, prospective demand comparison
- Existing exploratory run `20261114T055834736669Z-B2-2` already demonstrated terminal depletion
- **Impact if skipped:** medium — depletion mechanism is implemented and tested in isolation, but full 4-arm lifetime comparison is not yet evidenced

---

## How to Run These Later

Run individually to avoid timeout:

```bash
# Boundary 4000ms
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --period-ms 4000 --timeout-seconds 600

# Boundary 47-byte
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --payload-budget 47 --timeout-seconds 300

# Depletion sensitivity
python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 223456 --energy-sample-ms 125 --timeout-seconds 900

python3 host/run_experiment.py --phase 4 --mode B2 --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 223456 --energy-sample-ms 250 --timeout-seconds 900

# Lifetime (each seed, all 4 arms)
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 123456 --timeout-seconds 900

python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 123457 --timeout-seconds 900

python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 123458 --timeout-seconds 900
```

---

## Human Gates (Permanently Pending)

These require human action and cannot be automated:

| Gate | Description | Status |
|------|-------------|--------|
| G0 | Two-student independent review of official RPL tutorial | Pending |
| Phase 4 human review | Security decisions, energy model assumptions, code review | Pending |
| Independent reproduction | Clean machine, fresh clone, reproduce all results | Pending |

---

## Does Phase 5 Need These?

**No.** Phase 5 requires:
- Profile contexts with independent keys ✅ available
- Static energy cost table (B1/B2/B4/B5) ✅ available from 3-seed static pilots
- Validated energy model ✅ available

Lifetime comparison data would strengthen Phase 6 results but is not a Phase 5 implementation dependency.

---

## What is Complete (not in leftover)

For clarity — these are NOT pending:

- All firmware implementation (crypto, energy, lifetime, sensor, root) ✅
- Python tests 21/21 ✅
- Security matrix 22 cases (attacks/resets/provisioning/critical) ✅
- Measurement controls (idle/CPU load) ✅
- Static 3-seed pilots B1/B2/B4/B5 × 8 clients ✅
- Boundary 500ms ✅
- Expanded Z1 AES KAT (empty + nonempty vectors) ✅
- All 9 bugs found and fixed (documented in problems report) ✅
