# Directory audit and cleanup proposal

Audit date: 14 November 2026. No existing file was deleted, moved, renamed or reformatted. This report is the only addition from the audit.

## Scope and method

Inspected top-level layout, Git status, disk usage, recursive file inventory, first-party file roles, generated artifacts, SHA-256 duplicate groups and result manifest statuses. Checked references for charts, generated configuration and security-test applications. Upstream dependency contents were inventoried, not reviewed line by line for dead code. Git metadata and environment-owned `.aws`, `.codex` and `.agents` contents were excluded from content hashing. No build/test was run and no claim of exhaustive source dead-code analysis is made.

`du` reports approximately 165 MiB allocated workspace space: external dependencies 136 MiB, results 18 MiB, firmware 6.1 MiB and project `.git` 5.2 MiB. Recursive inventory excluding Git/environment metadata counted 8,971 files. Allocated disk usage differs from file-byte totals.

## Findings and candidate actions

| Path | Finding | Proposed treatment |
|---|---|---|
| `host/__pycache__/` | Regenerable Python bytecode; 36 KiB allocated | Clear cleanup candidate when processes are idle |
| `firmware/root/build/` | Generated native compilation outputs; 1.8 MiB | Cleanable after checking run evidence retains needed binaries |
| `firmware/sensor/build/` | Generated native compilation outputs; 1.8 MiB | Same; rebuild required afterwards |
| `firmware/security_test/build/` | Generated KAT/boot/reset build outputs; 2.4 MiB | Preserve/hash any unique test binaries before clearing; do not assume every security-test binary was archived |
| `results/phase_02/unit/test_core` | Compiled test executable, identical to Phase 3 copy | Optional future archive/dedup only after provenance review |
| `results/phase_03/unit/`, `results/phase_04/unit/` | Test executables plus evidence files | Never delete whole directories as cache; separate rebuildable binaries from logs/manifests first |
| `firmware/generated-conf.h` | Generated but actively included by application configuration | Keep; future runner should archive exact generated header per run before overwrite |
| `results/phase_02/.runner.lock` | Empty file with active concurrency role | Keep stable path/inode; deleting while locked can break mutual exclusion |
| `external/contiki-ng/`, `external/ascon-c/` | Pinned required upstream dependencies, 111/25 MiB allocated | Keep intact; unused upstream examples/backends are not first-party clutter |
| `phase_jouney/tmp/` | Preserved phase plans, including original and synced Phase 4 plans | Never delete; their distinct historical/current roles should be labelled in navigation |
| `PLANS/`, journals, evidence manifests and raw failures | Authoritative requirements and reproducibility history | Preserve unchanged except expressly authorized documentation updates |

The immediately recognizable cache/build candidates total about 6 MiB, with the binary-preservation conditions above. No obviously disposable first-party source module was established. No editor `.tmp`, `.bak`, `.swp`, `.orig`, `.rej` or trailing-tilde file was found outside excluded upstream/metadata directories.

## Exact duplicates that require context

Five 30,091-byte Phase 3 charts have identical SHA-256 contents:

- `results/phase_03/pilot-comparison.png`
- `results/phase_03/pilot-current.png`
- `results/phase_03/pilot-final.png`
- `results/phase_03/pilot-phase3.png`
- `results/phase_03/pilot-verified.png`

`pilot-phase3.png` is referenced by the detailed report and evidence index; `pilot-verified.png` is referenced by the execution journal. Recommend `pilot-phase3.png` as the current navigation target. The other names are candidates for a future archival/alias decision, not immediate deletion. Removing four copies would save only 120,364 file bytes; preserving traceability matters more. No reference was found for the other three names in the inspected docs, journals, scripts and Phase 3 evidence index; this is not proof that no external consumer uses them.

Other identical groups include repeated Phase 1 logs; repeated Phase 2 scenarios, summaries and logs; Phase 3 summaries and captured binaries; repeated host-test PASS logs; and the two successful Phase 4 logs. They belong to different runs or source-validation steps. Identical console text does not mean identical execution or coverage. Keep their original paths and run associations.

The identical root/sensor `project-conf.h` files each include the common parent configuration. They are tiny application entry-point wrappers, not redundant implementations. Likewise `scripts/smoke.sh` is a shell entry point for `smoke.py`; both have a role. Security KAT, boot and reset applications are referenced by scenario helpers and must remain.

## Evidence and repository issues

- Found 40 run manifests: 36 report passed and 4 failed. These are declared statuses, not a new validation of every artifact or every run. Failures comprise three early Phase 2 build/Cooja failures and one Phase 3 timeout. Preserve all four.
- The empty Phase 3 timeout `console.log` is evidence of that attempt, not automatically junk. The empty runner lock is also intentional.
- Project `git rev-parse --verify HEAD` fails; top-level project content remains untracked. Untracked does not mean unused. `.git` has data despite no resolvable HEAD and must not be removed as clutter.
- `.gitignore` excludes firmware build trees and Python cache, but ignores only one named Phase 2 unit executable. Future hygiene should consistently exclude regenerated executables across phases while retaining required evidence through an explicit archival policy. Do not add a blanket `results/` ignore or delete rule.
- Root `README.md` is absent. Current entry points are scattered across handoff, phase index and usage docs. Navigation is the main organizational issue, more than disk waste.
- The original Phase 4 plan's historical status and handoff snapshot can disagree with later progress. Keep historical records, but point current navigation to `phase_04_synced_completion_plan.md` and the latest journal. Do not rewrite historical test claims as current verification.

## Proposed reformatting and organization

Retain the existing top-level structure; it already separates concerns and is embedded in scripts, scenario paths and manifests:

```text
README.md                 proposed project entry point
AGENTS.md                 collaboration constraints
PLANS/                    authoritative plans
docs/                     contracts, usage, handoff, audits
configs/                  executable experiment settings
firmware/                 shared production C and mote test apps
host/                     runner, parsing, metrics, plots
scripts/                  thin setup/test/scenario entry points
tests/                    host fixtures and assertions
simulations/scenarios/    saved simulator scenarios
phase_jouney/             chronological reports and phase index
  tmp/                    permanent original/synced phase plans
results/                  immutable run records and evidence indexes
external/                 pinned upstream checkouts
```

Recommended next changes, if requested:

1. Add a concise root README linking setup, current Phase 4 plan, journal, usage and evidence indexes; identify historical versus current documents.
2. Add results navigation that labels primary, regression, calibration and failed runs without moving their artifacts or rewriting manifests.
3. Standardize future names around explicit run IDs and purposes; avoid new `final/current/verified` chart copies. Preserve historical names already referenced.
4. Review `.gitignore` for executable/cache hygiene, keeping evidence retention separate from version-control inclusion.
5. Before any build cleanup, ensure no active writer, acquire the existing shared runner lock, and verify or archive unique compiled artifacts with hashes. Clear only the specifically approved cache/build paths.
6. Treat code formatting as a separate change with behavioral regression checks. Broad automatic formatting or folder moves are unnecessary for this inventory request.

No deletion commands are provided or executed. No change to `phase_jouney/tmp`, original plans, upstream dependencies, archived logs or run binaries is authorized by this proposal alone.
