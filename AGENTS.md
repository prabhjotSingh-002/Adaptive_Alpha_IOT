# Project collaboration rules

Read PLANS/MASTER_IMPLEMENTATION_PLAN.md and PLANS/IMPLEMENTATION_AND_DECISION_REVIEW.md. Original plans are authoritative and must remain unchanged unless the user explicitly asks to edit them. Follow user instructions and current phase scope. Read phase_jouney/README.md and current phase plan/journal before work.

Reuse the pinned Contiki-NG/Cooja and official container. Keep custom code under firmware/ and host/. Do not modify upstream core. Never invent cryptographic primitives, logs, results or security/energy claims. N0 is unprotected. Build/test execution and actual logs are required evidence; host fixtures are not research results.

One writer owns generated config/build dirs: host/run_experiment.py serializes Phase 2 runs. Shared production C protocol/aggregation code must be used for host tests. Record commands, source/config/scenario/binary hashes and errors. Preserve failures. Before finishing a phase, update detailed phase_jouney/ Markdown reports and stop; wait for user instruction before starting the next phase. Human gate checks stay pending until actually performed.

Never delete the phase_jouney/tmp directory or its contents. Preserve temporary phase plans as permanent project records, including during cleanup.
