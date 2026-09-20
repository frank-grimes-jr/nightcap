# Phase 30 — Hosted owner-test deployment

2026-09-20. OVH runs the five private containers; Cloudflare provides the domain,
tunnel and tested IP restriction. Database/runtime data were copied without
changing local QA. Three verified login namespace mappings preserve existing
characters. A backup and transaction rollback rehearsal precede the change.

Production launcher0.2.0 and signed release2026092003 are built and hosted for
the owner. All20hosted file hashes/signature and ZIP hash pass; native session
handshakes traverse the actual WSS tunnel to login/world/UCS/zone. Host checks
cover Docker mount semantics, private networks, password hashing and failed
backup behavior. Idle memory fits the8GBVPS, but ten-player load is unmeasured.

Unfinished: owner/native gameplay acceptance, friends' onboarding, R2 encrypted
backup setup and restore rehearsal, release automation and scheduled downtime.
No gameplay promotion or friend distribution approval was inferred.

Operational learning: Compose parsing alone did not catch comma-split tmpfs
strings; validate resolved mounts and actual engine startup. Consistent dumps
must include stored procedures and propagate producer failures. Source-tree
opcode symlinks require resolved copies. Private login migration needs exact
identity checks and native-collation collision checks before changing namespaces.

[Detailed activation and recovery](../releases/ovh-activation-20260920.md).
