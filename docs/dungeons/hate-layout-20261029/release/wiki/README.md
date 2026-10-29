# Hate layout wiki release

Published after the owner's approved paired Hate runtime/client activation and
verified open admissions. Release20261029-hate-layout-v1 passes all 499 HTTPS hashes,
security headers and five private-source404routes. Owner gameplay acceptance
remains open. Exact receipts: `wiki-publication.json` and
`wiki-public-verification.json`.

The owner approved main, server, client and wiki delivery before manual QA in
`../AUTHORIZATION.md`. Main PR362 is merged at `8b23d739`. This source promotion
does not by itself establish runtime or website activation. The initial server
disk-space guard stopped safely with access still open; the separately audited
preservation and continuation completed before activation. The completed runtime
and client receipts were checked before this publication; `activation-guard.json`
pins their exact hashes and all five service identities.

The previous public baseline was read directly from the production pointer and
manifest: `20261028-bazaar-owner-qa-v1`, 499 files. The immutable candidate is
`work/hate-wiki/20261029-hate-layout-v1.tar.gz` (about 2.85 MB). Its exact manifest
changes seven files: dungeon modes, Features, In development, Change Log, travel,
Zone Hunt and search index. The other492 files retain their baseline bytes.

All 40 article sources were reviewed. The owning guides distinguish the new Keeper
layout from existing original-layout runs and ordinary spell travel; correct the
private Keeper location; retain the same objective/reward identities; explain the
original `hateplane` Hunt-family label; and keep rendered gameplay, patrol/pull
difficulty and full-run acceptance open. Old anchors remain. Home, commands,
launcher guidance, catalogs and all unrelated release labels remain unchanged.
Historical source-ledger drift remains review-required, recorded separately in
`source-drift.json`; this scoped review does not approve unrelated source changes.

Validation: 19 Python content/refresh tests and 16 Linux publication/rollback tests
pass. Node search, seven equipment cases, handbook behavior and Build Lab scenario
suites pass. Initial Windows sandbox temporary-file permission failures were
resolved by running the same 19 tests with TEMP/TMP in the task workspace.

The release performed read-only activation capture after paired native/client
verification and open admission, writing `activation-guard.json` from the
actual current signed channel hash and five service identities, tying the game
image/start to the deployment receipt and pinning both receipt files. Commands
used are below; publication has already completed and must not be replayed:

```text
python docs/dungeons/hate-layout-20261029/release/wiki/capture_activation_guard.py
python docs/dungeons/hate-layout-20261029/release/wiki/publish_wiki.py
python docs/dungeons/hate-layout-20261029/release/wiki/verify_wiki_public.py
```

The publisher derives from the reviewed October28 Bazaar owner-QA publisher. It
requires the exact previous pointer, manifest, Nginx config and signed channel,
checks the seven-file allowlist, pins all uploaded bytes, reruns 16 Linux tests,
and preserves all five service identities before and after publication under the
deployment lock. `wiki/update.py` adds the shared website lock, atomic pointer
change, scoped rollback rehearsal and private-download preservation. It neither
restarts services nor changes configuration. A prior receipt or occupied staging
path requires inspection before any retry; do not replay after uncertainty.

The post-publication verifier passed all 499 HTTPS hashes/security headers and five
private-source404routes at 14:44:45 UTC. The final whole-release verification at
14:46:21UTC independently reconfirmed the paired runtime/client/wiki and unchanged
service lifetimes. Three release-specific receipt-gate tests also pass.
