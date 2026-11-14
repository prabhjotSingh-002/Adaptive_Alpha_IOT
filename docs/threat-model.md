# Security scope and required next-stage invariants

Phase 2 uses profile 0/N0: unprotected UDP. Confidentiality, sender authentication, tamper resistance and authenticated replay protection are absent. Source-IP/header checks and a bounded reading-ID window are diagnostic validation only; an attacker can forge N0 traffic and alter receiver accounting. These modes cannot serve as security-equivalent controls.

Bounds checks, exact length/version checks, unknown-profile rejection and fixed memory help protect parsing. Phase 3 protected modes must use vetted AEAD, unique per-key nonces, authenticated metadata, tag verification before plaintext release and replay-state updates, fail-closed reset/wrap behaviour, and no plaintext fallback. The current zero epoch and diagnostic counter are not a production key/nonce system. Existing master requirements for separate suite keys, known-answer vectors and failure tests remain authoritative.

## Phase 3 implemented scope

See [Phase 3 security contract](phase3-security-contract.md) for implemented controls, controlled reset evidence, and explicit boundaries. Test keys and generated scenarios are public simulation fixtures; neither production provisioning nor arbitrary snapshot rollback is covered.
