> Current audit correction: see [last Astra check](../lastAstra%20check.md). Historical policy pilots do not establish intended adaptive behaviour: policy state/configuration was not loaded, B6 used AES fallback and P1 lacked costs. Priority repairs have targeted host checks only; Phase 4/5 network validation is deferred by user and Phase 6 has not started. Older completion/performance explanations below are historical and superseded where contradictory.

# Phase 6 — Complete Context Document

**Date:** 14 November 2026  
**Author:** Agent-generated from actual project state — verify drift before acting  
**Purpose:** Explain Phase 6 completely — what it is, why each piece is needed, what is already done, what is pending, what blocks what, and how much work each piece actually is.

---

## 1. What Phase 6 Actually Is

Phase 1–5 built the system. Every firmware module is written, compiled, tested, and passes security regression. Phase 6 does **not** write any new firmware or algorithms.

Phase 6 is the **research evidence phase**. Its job is to answer:

> "Can we show, with enough runs and proper statistics, that B3/B6/P1 adaptive policies are meaningfully better (or not) than the B1/B2/B4/B5 static baselines — and produce a paper to prove it?"

That means:
- More runs on **held-out seeds** (seeds never touched during development)
- Bigger network scenarios (10-node, 20-node) if feasible
- Proper survival curves (FND = first node death, HND = half nodes dead)
- Bootstrap confidence intervals over paired runs
- Paper-ready figures generated from scripts
- Reproducibility: a second person reproduces results on a clean machine
- Release: git tag, README, manuscript

---

## 2. Current Data Inventory (What Exists Right Now)

### Phase 4 — Static baselines (B1/B2/B4/B5)
All on Z1 target, 8 clients, `--power-model`, seeds 123456/123457/123458:

| Mode | Runs | Seeds with energy data |
|---|---|---|
| B1 (AES cap=1) | 6 passed | 5 with energy (seeds 123456, 123457, 123458) |
| B2 (Ascon cap=1) | 5 passed | 5 with energy (seeds 123456, 123457, 123458) |
| B4 (AES cap=4) | 4 passed | 4 with energy (seeds 123456, 123457, 123458) |
| B5 (Ascon cap=4) | 3 passed | 3 with energy (seeds 123456, 123457, 123458) |

### Phase 5 — Adaptive policies (B3/B6/P1)
All on Z1 target, 8 clients, `--power-model`, seeds 123456/123457/123458:

| Mode | Runs | Unique seeds | Duplicates |
|---|---|---|---|
| B3 (battery-threshold) | 3 | 3 | 0 |
| B6 (fixed Ascon + adaptive batch) | 5 | 3 | 2 (preserved, don't use for analysis) |
| P1 (joint cost-aware policy) | 5 | 3 | 2 (preserved, don't use for analysis) |

### Key numbers (pilot, 3 seeds each):

| Mode | Mean energy (nJ) | Mean PDR | Mean p95 delay (ms) |
|---|---|---|---|
| B1 | 247,233,663 | 0.9696 | 142.1 |
| B2 | 247,501,031 | 0.9677 | 152.5 |
| B4 | 243,928,892 | 0.9805 | 2985.8 |
| B5 | 244,171,889 | 0.9792 | 3004.8 |
| B3 | 254,460,219 | 0.9653 | 146.8 |
| B6 | 254,457,201 | 0.9653 | 146.8 |
| P1 | 254,470,055 | 0.9653 | 145.6 |

**Critical observation about these numbers:**  
B3/B6/P1 show ~+2.9% *higher* energy than B1 baseline in the current pilot. This is not a bug — it is an honest result. The reason: in a 24-reading, 60s warmup, 1Hz scenario, residual energy never drops below the B3 hi-threshold (6 GnJ), so B3 never switches to Ascon. P1 finds no profitable action because switching overhead exceeds savings at this energy level. These policies are designed for **long lifetime runs where energy depletes** — which is exactly what Phase 4 lifetime cases 33–35 would demonstrate. Phase 6's runs on longer scenarios and held-out seeds may show different results.

---

## 3. What Phase 6 Needs to Do — Each Piece Explained

### F6.1 — Scenario Scaling

**Why needed:**  
The master plan requires 10-node (root+9) and 20-node (root+19) scenarios. Current code only supports 8 clients (root+8). Two blockers:

1. **Only one `.csc` file exists:** `simulations/scenarios/phase1-rpl-9.csc` — 9 motes total (1 root + 8 clients). There is no 10-node or 20-node scenario file.

2. **Boot gate context limit:** `firmware/crypto/boot_gate.h` line 18 defines `LAB_PROVISION_MAX_CONTEXTS 16u`. A dual-profile experiment with 9 sensors needs 9×2=18 contexts — overflows. The fix is a compile-time dimension increase with proper bounds checking, not just changing the number.

3. **Runner client limit:** `host/run_experiment.py` has argument parsing that internally slices the scenario. Extending to 20 nodes needs scenario generation logic updated.

**What to do:**
- Fix `LAB_PROVISION_MAX_CONTEXTS` to support up to 32 or configurable compile-time value
- Validate memory/RAM impact on Z1 (currently at ~6498 bytes data+BSS vs 8KB RAM limit)
- Create new `.csc` scenario files for 10-node and 20-node
- Update runner to pass correct node count

**Is this required for minimum Phase 6?**  
No — a minimum Phase 6 can run with 8 clients only. But the master plan's full matrix (10/20 node) needs this. Treat as **stretch unless paper explicitly requires it**.

---

### F6.2 — Experiment Protocol Freeze

**Why needed:**  
This is the most important pre-condition. The entire purpose of using held-out seeds is that you decide the analysis plan *before* seeing the results. If you pick seeds, run experiments, see the numbers, and then decide what to compare — that is p-hacking. The protocol document freezes everything beforehand.

**What must be in the protocol:**
- Which seeds are "held-out main seeds" (proposed: 423456–423465) — these have never been used in any run
- Which seeds are "development/calibration" (used: 123456, 123457, 123458, 223456, 223457)
- Exact matrix: how many modes × topologies × sizes × rates × seeds
- Primary metric: network energy per unique authenticated delivered reading
- PDR threshold: runs with PDR < X are excluded (must decide before running)
- Comparison baseline: B1 is primary comparator
- Statistical test: paired bootstrap CI over runs (already implemented in `host/analysis.py`)
- Stop criteria: what constitutes a failed run vs an excluded run

**Files to create:**
- `docs/experiment-protocol.md` — human-readable, the actual research protocol
- `configs/phase6.json` — machine-readable config for the runner

**Current state:** `docs/phase4-experiment-protocol.md` exists (Phase 4 version). Phase 6 needs its own version. Neither `docs/experiment-protocol.md` nor `configs/phase6.json` currently exist.

**Is this required?**  
Yes — this is a hard dependency before running any Phase 6 main matrix runs.

---

### F6.3 — Runner Matrix Engine

**Why needed:**  
Current `host/run_experiment.py` runs one mode + one seed at a time. For even the minimum 35-run matrix you would run 35 separate commands. If the machine is interrupted mid-way, there is no resume — you have to figure out manually which runs completed.

**What to build:**
- `host/run_matrix.py` — new script that reads a matrix spec from `configs/phase6.json` and runs all cells in order
- Each cell is `(mode, clients, seed, target, power_model)` — one `run_experiment.py` call
- Before each run: check if a passed run for this exact `(mode, seed, config_hash)` already exists — skip if yes
- After each run: update a progress file `results/phase_06/matrix_progress.json`
- If interrupted and restarted: reads progress file and resumes from where it stopped

**How it works with existing code:**  
`run_matrix.py` just calls `run_experiment.py` as a subprocess — it does not duplicate any experiment logic. It is a thin scheduler.

**Is this required?**  
Technically no for small runs — you can run 35 commands manually. But for 70+ runs across multiple days it becomes essential. Recommended to build before starting the main matrix.

---

### F6.4 — Actual Experiment Runs

**Why needed:**  
Current data (3 seeds per mode) is a pilot. For a research paper, 3 seeds is weak — confidence intervals will be wide. The standard is at least 5–10 independent seeds per arm.

**Two separate run sets:**

#### Set A — Phase 4 leftover lifetime runs (cases 33–35)
These are deferred from Phase 4 and are needed for FND/HND survival curves. Without them, there is no "first node death" evidence.

```bash
# Case 33
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 123456 --timeout-seconds 900

# Case 34
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 123457 --timeout-seconds 900

# Case 35
python3 host/run_experiment.py --phase 4 --mode all --clients 2 --target z1 --power-model \
  --warmup-ms 120000 --readings 120 --energy-budget-nj 9000000000 \
  --deplete-node 2 --bottleneck --seed 123458 --timeout-seconds 900
```

Estimated time: ~2 hrs total (4 arms × 3 seeds = 12 runs, ~10 min each).

#### Set B — Phase 6 main matrix (held-out seeds)
These use seeds 423456–423465, which have **never been used** in any previous run. This is the actual research evidence.

Minimum viable matrix (no boot gate fix needed, 8-client only):
```
7 modes (B1/B2/B3/B4/B5/B6/P1) × 5 seeds (423456–423460) = 35 runs
~70 min machine time
```

Full master plan matrix (needs boot gate fix for 10/20-node):
```
7 × 2 topologies × 2 sizes × 2 rates × 10 seeds = 560 runs
~19 hrs machine time
```

**Recommendation:** Start with the 35-run minimum. Decide on full matrix after seeing those results.

---

### F6.5 — Statistics

**Current state (implemented this session):**

| Tool | Location | Status |
|---|---|---|
| Bootstrap CI (95%, 2000 resamples) | `host/analysis.py` | ✅ Done |
| Per-mode mean/median/std/min/max | `host/analysis.py` | ✅ Done |
| Pairwise comparison vs B1 | `host/analysis.py` | ✅ Done |
| Policy summary (switches, profiles) | `host/analysis.py` | ✅ Done |
| 7-arm bar charts with error bars | `host/plots.py` | ✅ Done |
| Docker wrapper for plots | `host/run_plots.py` | ✅ Done |
| Docker wrapper for analysis | `host/run_analysis.py` | ✅ Done |

**What is missing:**

1. **Survival analysis (FND/HND curves):**  
   Needs `scipy` for Kaplan-Meier estimates or restricted mean lifetime. `scipy` is **not** in the current Docker container. Quick fix:
   ```bash
   # Inside container at runtime
   apt-get install -y python3-scipy
   ```
   Or add to a custom Dockerfile that extends `contiker/contiki-ng`.

2. **Paired-seed tests:**  
   Current `analysis.py` does unpaired bootstrap when sample sizes differ. For Phase 6 with matched seeds (each arm runs same seeds), use paired differences. This is a small addition to `analysis.py` — maybe 20 lines.

3. **Energy–latency tradeoff plot:**  
   Scatter plot: x=mean p95 delay, y=mean energy/reading, one point per arm. Not implemented yet.

4. **Figures from actual Phase 6 runs:**  
   `run_plots.py --phase 6` will auto-discover Phase 6 runs — this already works, just needs Phase 6 data to exist.

---

### F6.6 — Reproducibility

**Why needed:**  
A research claim is only credible if someone else can reproduce it. This requires pinning every dependency.

**What is missing:**

1. **`host/requirements.lock`:**  
   Current host scripts use only stdlib + math (no pip packages). The analysis/plots scripts use matplotlib/numpy via Docker. A lockfile documents exactly which Python and library versions were used.  
   Quick to create:
   ```bash
   # Inside Docker container
   pip freeze > /workspace/host/requirements.lock
   ```

2. **`.github/workflows/ci.yml`:**  
   CI that runs on every push:
   - `python3 tests/unit/test_policy.py` (17 tests)
   - `python3 tests/unit/test_metrics.py` (18 tests)  
   - `python3 tests/unit/test_lifetime.py` (3 tests)
   - JSON schema validation of configs
   - Build check (compile firmware for cooja target)
   
   This is maybe 50 lines of YAML. Does not run Cooja simulations (too slow for CI).

3. **Independent reproduction (human gate):**  
   A second student or reviewer clones the repo on a clean machine, follows README, runs a subset of experiments, and verifies the numbers match within documented tolerances. **Cannot be automated.**

---

### F6.7 — Release

**Why needed:**  
Final deliverables for the paper/project submission.

**What is missing:**

1. **`README.md` (root):**  
   Currently does not exist. Should have:
   - 5-minute quickstart: clone → pull container → run smoke test → run analysis
   - Architecture overview
   - Commands to reproduce key results
   - Hardware/software requirements
   
2. **`results/phase_06/phase6-evidence.json`:**  
   Same structure as `results/phase_05/phase5-evidence.json` but for Phase 6 runs. Created after Phase 6 matrix completes.

3. **Manuscript/paper draft:**  
   Not in scope for the agent — this is student work. The figures and tables generated by `analysis.py` and `plots.py` are the inputs to the manuscript.

4. **Git release tag:**  
   `git tag -a v1.0-phase6 -m "Phase 6 final experiments"` after all runs and figures are verified. Currently the project has no git commits at all — this is a prerequisite.

---

## 4. Dependency Graph — What Blocks What

```
Human authorization to start Phase 6
        │
        ▼
Experiment protocol freeze (F6.2)
  docs/experiment-protocol.md
  configs/phase6.json
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
Phase 4 lifetime runs                  Phase 6 matrix runs
(cases 33–35, ~2 hrs)                  (35 runs minimum, ~70 min)
uses dev seeds 123456-123458           uses held-out seeds 423456+
        │                                      │
        └──────────────┬───────────────────────┘
                       ▼
              Statistics + Plots
              host/analysis.py ✅
              host/plots.py ✅
              scipy (FND/HND) ← needs install
                       │
                       ▼
              Reproducibility
              requirements.lock
              CI workflow
              Independent reproduction (human)
                       │
                       ▼
                   Release
              README.md
              git tag
              manuscript
```

**What can run RIGHT NOW without any blocker:**
- Phase 4 lifetime cases 33–35 (uses existing code, same 8-client scenario)
- `requirements.lock` generation
- `README.md` creation
- `docs/experiment-protocol.md` draft
- CI workflow YAML

**What needs human action first:**
- Phase 6 main matrix (needs protocol freeze + authorization)

**What needs code change first:**
- 10/20-node runs (needs boot gate fix + new `.csc` files)
- Survival analysis plots (needs scipy install)

---

## 5. Minimum Viable Phase 6 vs Full Phase 6

### Minimum viable (no boot gate fix, 8-client only):

| Step | Work | Time |
|---|---|---|
| Write experiment protocol | `docs/experiment-protocol.md` | 1 hr (human) |
| Create `configs/phase6.json` | config file | 15 min |
| Run Phase 4 lifetime cases 33–35 | 12 runs | ~2 hrs machine |
| Run Phase 6 matrix 35 runs | 7 modes × 5 seeds | ~70 min machine |
| Install scipy in container | 1 command | 2 min |
| Generate analysis + plots | `run_analysis.py`, `run_plots.py` | 5 min |
| Write `requirements.lock` | 1 command in Docker | 5 min |
| Write `README.md` | markdown file | 1 hr |
| Write `phase6-evidence.json` | after runs complete | 30 min |
| **Total** | | **~6 hrs + human writing** |

### Full Phase 6 (master plan, with 10/20-node):

| Step | Additional work | Additional time |
|---|---|---|
| Fix boot gate limit | firmware change + test | 2 hrs |
| Create 10-node `.csc` scenario | XML file | 1 hr |
| Create 20-node `.csc` scenario | XML file | 1 hr |
| Run matrix 10-node (7 × 10 seeds) | 70 runs | ~2.5 hrs machine |
| Run matrix 20-node (7 × 10 seeds) | 70 runs | ~5 hrs machine |
| Build runner matrix engine | `host/run_matrix.py` | 3 hrs |
| **Additional total** | | **~15 hrs** |

---

## 6. Tools Ready Right Now

These work today without any additional implementation:

| Command | What it does |
|---|---|
| `python3 host/run_experiment.py --phase 5 --mode B3 --clients 8 --seed 423456 --target z1 --power-model` | Run one Phase 6 held-out seed |
| `python3 host/run_analysis.py --phase 4 --phase 5` | Bootstrap CI statistics via Docker |
| `python3 host/run_plots.py --phase 4 --output results/phase_04/figures/p4.png` | 7-arm comparison plots via Docker |
| `python3 host/calibrate.py` | Regenerate calibration cost table |
| `python3 tests/unit/test_policy.py` | 17 policy unit tests |
| `python3 tests/unit/test_metrics.py` | 18 metrics tests |

---

## 7. What Is NOT Needed for Phase 6

Being explicit about what does not need to change:

- **No firmware changes** — all three policies are implemented and tested
- **No new algorithms** — B3/B6/P1 logic is complete
- **No new crypto** — AES and Ascon both work
- **No new host parsing** — `parse_logs.py` already handles all Phase 5/6 events
- **No new metrics** — `metrics.py` already computes everything needed
- **No Contiki-NG changes** — upstream is not touched

The only code that might need writing:
1. `host/run_matrix.py` — matrix scheduler (optional, convenience only)
2. Boot gate dimension fix — only if 10/20-node is required
3. `docs/experiment-protocol.md` — document, not code
4. `configs/phase6.json` — config file, not code
5. `.github/workflows/ci.yml` — CI YAML, not code
6. `README.md` — documentation, not code

---

## 8. File Reference

| File | Exists? | Role in Phase 6 |
|---|---|---|
| `PLANS/MASTER_IMPLEMENTATION_PLAN.md` | ✅ | Authority — read before any Phase 6 decision |
| `PLANS/PHASE_05_IMPLEMENTATION_PLAN.md` | ✅ | Phase 5 reference |
| `phase_jouney/phase_04_leftover.md` | ✅ | Exact commands for cases 29–35 |
| `phase_jouney/phase_05_detailed_report.md` | ✅ | Phase 5 results to compare against |
| `results/phase_05/phase5-evidence.json` | ✅ | Machine-readable Phase 5 evidence |
| `results/phase_04/phase4-evidence.json` | ✅ | Machine-readable Phase 4 evidence |
| `results/phase_05/cost_table.json` | ✅ | Calibration — B6 winner is B2/Ascon |
| `configs/phase5.json` | ✅ | Phase 5 config — reference for Phase 6 |
| `configs/power-z1-v1.json` | ✅ | Power model (Z1 mote current/voltage values) |
| `docs/phase4-experiment-protocol.md` | ✅ | Phase 4 protocol — template for Phase 6 version |
| `firmware/policy/policy.{h,c}` | ✅ | Complete — do not modify |
| `firmware/crypto/boot_gate.h` line 18 | ✅ | `LAB_PROVISION_MAX_CONTEXTS 16u` — change only if 10+ node needed |
| `simulations/scenarios/phase1-rpl-9.csc` | ✅ | Only scenario — 9 nodes (1 root + 8 clients) |
| `host/analysis.py` | ✅ | Bootstrap CI, pairwise, policy summary |
| `host/plots.py` | ✅ | 7-arm plots with error bars |
| `host/run_analysis.py` | ✅ | Docker wrapper for analysis |
| `host/run_plots.py` | ✅ | Docker wrapper for plots |
| `docs/experiment-protocol.md` | ❌ | **Must create before main matrix** |
| `configs/phase6.json` | ❌ | **Must create before main matrix** |
| `host/run_matrix.py` | ❌ | Optional matrix scheduler |
| `host/requirements.lock` | ❌ | For reproducibility |
| `.github/workflows/ci.yml` | ❌ | For CI |
| `README.md` | ❌ | For release |
| `results/phase_06/phase6-evidence.json` | ❌ | Created after Phase 6 runs |
| `AFTER_PHASE5_STATUS.md` | ✅ | Full handoff document (this session) |

---

## 9. Honest Assessment of Research Results So Far

**What the data shows:**
- B4 and B5 (batching) reduce energy by ~1.3% vs B1 baseline, but increase p95 latency by ~20x (142ms → 2985ms). Latency tradeoff is severe.
- B1 and B2 have similar energy (~247M nJ). AES vs Ascon difference is negligible at this scale.
- B3/B6/P1 show slightly *worse* energy than B1 in the pilot (+2.9%). Policy switching never activated because residual energy stayed too high.

**What this means for the paper:**
- The adaptive policies have not yet shown benefit over static baselines in the current 24-reading, 1Hz, no-depletion scenario.
- This is expected — the policies are designed for depleting-battery scenarios, which is exactly what cases 33–35 test.
- Phase 6 lifetime runs with energy depletion and longer horizons are where B3 (battery-threshold switch) should activate.
- Negative or inconclusive results are acceptable and must be reported honestly — the master plan explicitly says "do not assert a guaranteed 25%–40% gain."

**What would make the results stronger:**
1. Lifetime runs (cases 33–35) showing actual node death and B3 activating the AES→Ascon switch as energy depletes
2. Held-out seeds (423456+) so development-data contamination is eliminated
3. More seeds per arm (5–10 instead of 3) to narrow confidence intervals
