# Signed Hate client release2026102901

Published October29 after the paired runtime passed its closed-admission gate.
The exact signed channel and all148 HTTPS files (300,603,700bytes) verify; the
retained proxy/catalog pair also passes. Publication preserved all five service
identities and kept admissions closed. `published.json` and
`public-verification.json` are the receipts; reopening is recorded by the parent
server release. Owner native gameplay acceptance remains pending.

Baseline: signed2026102803, channel
`eb09f02c097eed3ba35c97756ca00ce8cdbbe04453497aa376c6143cf8bb8c8e`.
Candidate channel:
`de5959ffdb6dff44e3de9626cb8dba7c57dd4787fbe9912505d5b1955f10c5d8`.
Seven required Hate files are added; all141 prior descriptors, proxy/catalog,
config, tombstones, launcher policy and existing patch history remain exact.
Both old and new envelopes verify against the shipped production public key.
Actual current proxy/catalog/config and installed eqgame.exe preflight pass.
The private signing seed stays local and is not part of staging.

The signed bytes are in `work/hate-client-release/signed`. `prepare.go` and
`verify.go` execute under a temporary `eq-launcher/cmd` package to use its internal
manifest parser. `verification.json` pins the concrete candidate.21publisher
fault/recovery tests pass on Linux;16pass on Windows with5POSIX cases skipped.

Executed commands from the repository root (historical; do not replay completed
staging or publication):

```sh
python docs/dungeons/hate-layout-20261029/release/client/ship_publish.py stage
# Only after the parent verifies new runtime health with admissions closed:
python docs/dungeons/hate-layout-20261029/release/client/ship_publish.py publish
work/hate-client-release/verify.exe -previous work/hate-client-release/signed/previous-channel.json -expected work/hate-client-release/signed/channel.json -hosted
```

Stage: `/opt/nightcap/releases/hate-client-2026102901`. The publisher requires
healthy running game/database, running web/tunnel, stopped gateway, and the exact
image/start time in `/opt/nightcap/releases/hate-layout-20261029-v1/evidence/activation/verified-closed.json`.
It holds the deployment lock, authenticates all retained on-host asset bytes,
writes immutable assets before the atomic channel replacement and verifies
service/control identities unchanged. It performs no service operation.

An interrupted pre-publication write can resume only after exact prefix/hash
checks. If the new channel became visible, clients may have recorded its release
number: do not roll back its number or remove files. Preserve the seven archives;
use a higher-numbered corrective release if needed. Server recovery is separate
and must retain earned runs/items. Inspect receipts after an uncertain result,
never blindly replay the remote staging/publication command. Native rendering,
travel and encounter acceptance remain owner QA after release.
