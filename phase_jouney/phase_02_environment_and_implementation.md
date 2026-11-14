# Phase 2 execution journal

Status: automated Phase 2 engineering work complete; stopped before Phase 3. Read PLANS/MASTER_IMPLEMENTATION_PLAN.md and PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md before changes. Saved implementation plan under tmp/phase_02_implementation_plan.md before C source edits. Original plan hashes saved under results/phase_02/original-plan-hashes.json.

## First implementation and checks
Shared fixed-memory C protocol/aggregator, custom Contiki sensor/root, central JSON pilot config and host runner/parser/metrics created. Existing pinned Docker image reused; no new packages installed. Production C sources passed gcc -Wall -Wextra -Werror -pedantic with ASan/UBSan for caps, packet bounds, invalid packets, deadlines/wrap, byte cap, interruption and dedup.

## First integration failure
Run 20261113T092355028182Z-N0-single-2 failed during mote compilation: -Wextra exposed unused ev/data parameters in Contiki process entry functions, promoted to errors by build settings. Fixed custom process functions with explicit (void)ev/(void)data; retained warnings. Failed manifest and full console retained. No upstream source change or suppressed acceptance check.

Second build reached upstream beep.c then failed because global -Wextra also applied to upstream driver parameters. Removed extra global warning flags (kept upstream defaults/-Werror); portable project modules remain tested separately with -Wall -Wextra -Werror -pedantic and sanitizers. No upstream edits.

Third integration built both motes, then failed because Python scenario generation interpreted JavaScript newline escapes. Converted embedded script to a raw Python string. Retained failed scenario and console for diagnosis. Also made READY log effective byte-limited cap, so validation can detect actual bounded configuration.

First successful individual 1+2 modes exposed a paired-trace mismatch: 1ms GEN logging delay after deadline flush in batch mode. IDs/values/local timestamps matched; actual simulator log times differed. Moved GEN event before network work, while preserving flush-before-offer for expired readings. Exact global trace comparison remains required; no tolerance silently introduced.

## Restart recovery
The agent server restarted before the first 1+8 run started. Re-inspected AGENTS, current phase plan/journal, manifests and Docker containers before resuming. The completed 1+2 paired run had exact global generation identity; no completed run was repeated blindly. Added explicit resolved-config hashes, bounded horizon checks and a fragmentation failure check for future pilot runs.

## Required topology passed
Actual 1+8 paired runs: 20261113T093713547602Z-N0-single-8 and 20261113T093733639048Z-N0-batch-8. Each generated/submitted/delivered 192 unique readings; no explicit drops or missing readings. Packet submissions 192 versus 64. Batch run count=3 due to 3s deadline expiring before the fourth 1Hz reading is offered. Max hold=3000ms; p95 delays about 103.554ms versus 3074.6856ms. Exact paired global generation trace matched. Radio capture classified all frames with zero FRAG1/FRAGN dispatches. These are one-seed unprotected observations, not energy/security results. Additional integration scenarios now exercise full count-4, deadline-only and byte-limit behaviour.

## Final validation and documentation
Boundary runs all passed: 20261113T093944037183Z (500ms period, count4, 12 submissions/48 readings), 20261113T094002866908Z (4000ms period, count1, 3000ms deadline flush), and 20261113T094021560664Z (byte budget47 incl. reservation, count2, 24 submissions). All delivered 48/48 with zero observed fragmentation. Final C sanitizer checks and ten Python tests passed; logs retained. Pilot plot generated using existing container matplotlib and visually inspected. Phase 1 unchanged smoke rerun passed at smoke-20261113T094208160354Z. Plan hashes unchanged and upstream diffs empty; existing artifact hashes verified.

Created phase_02_detailed_report.md covering downloads/reuse, every module's purpose, problems/fixes, exact run results, limitations and next-phase handoff. Machine-readable evidence and run index saved. No new package/image installation required. Phase 3 not started; human gate checks remain explicitly pending.
