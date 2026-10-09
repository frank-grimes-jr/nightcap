# Classic zone hunt and forge: live deployment

Deployed October 9, 2026 under the owner's explicit instruction to promote to main, deploy the server, and update documentation/site. PR #132 promoted the tested feature through dev/test to main `77f5d63`. Live gameplay acceptance remains open in [QA.md](QA.md).

The acquisition gate is active: 48 audited Classic combat zones, 6,056 exact spawn/NPC pairs, 384 droppable variants and 64 dormant definitions for eight access-check zones. All 448 item definitions and 2,290 existing armor socket edits passed exact value checks. Both independent family rolls are 0.5%; quality weights remain 60/30/8/2. `#zoneforge` is available to ordinary players. Existing named loot, content and era rules are preserved.

## Verified runtime and preservation

- Immutable image: `sha256:43b216727a5f4dad4492fa8da03ca81e2f22e5cb721428645e59b8e203dcdf5a`.
- Five compiled binaries match the deployed image; running world, zone, ucs and loginserver hashes match. Shared_memory is a startup utility. The 12 zone workers are healthy, with zero container restarts and no native, quest or database error matches in the rollout scan.
- A complete PEQ backup passed gzip/SQL completion checks before installation. It remains private on the server; no database snapshot was restored.
- All 47 captured player/account/inventory/rule/saved-state tables matched after clean shutdown and before reopening access. All 8,139 quest/plugin/module file hashes and four protected client/download files were retained. Database, web and tunnel service identities were unchanged by gameplay deployment.
- The 309,409-item shared cache passed full-catalog trading/resale validation. All 448 new reward definitions have zero merchant resale; prior fixed-price items retain 1pp resale.
- Source recapture regenerated all seven approved migration artifacts byte-for-byte before writes. No Adventure Journal SQL/quests, unreleased combat/skill candidate, client publication, NPC HP or extra cap tuning was deployed.

See [machine-readable verification](production-verification.json), [production build provenance](production-build-manifest.json), and [initial inverse rehearsal](initial-inverse-rehearsal.json). Player fingerprints and the full backup stay outside Git.

## Production build provenance

The early development build was rejected during preflight because it lacked the deployed authentication self-test. That build was never activated and no gameplay SQL had run. The corrected build starts from the fingerprinted deployed Throw Stone source, applies the reviewed feature/integration delta to 14 existing files and adds six files, and builds world, zone, shared_memory, ucs and loginserver in a fresh tree. It retains production authentication hardening and passes the private login crypto self-test with networking disabled. The prior main overlay also contains unreleased combat/skill work; only the scoped patch was applied to production.

The market/world startup-contract verifier does not certify authentication hardening. The older development manifests remain historical candidate evidence; `production-build-manifest.json` is authoritative for this deployed binary set. The 24 synthetic stat measurements retain their earlier development-object scope and do not certify this server's full encounter balance. The feature's cap/forge logic is retained, but live combined multiclass/AA/pet acceptance remains required.

The controller has nine failure tests, including immutable image selection and base-layer ancestry. Nine disposable MariaDB checks rehearsed exact installation and first-install inverse, restoring the original item rows. The source-capture CLI argument-shadowing repair has a regression test and completed the real read-only capture.

The exact production source also passed all ten existing native zone-hunt and trading tests and all 108 Throw Stone compiled checks. [Results](production-source-checks.json).

## Website publication

The private [player guide](https://play.nightcapgame.org/) now uses `20261009-zone-hunt`. It documents all 48 zone reward pairs, drop/tier odds, six armor sockets, level-50 heroic cap relief and three-copy forging. Existing access restrictions and protected downloads remain intact. The origin activation/rollback rehearsal and final activation passed; all five service identities/start times were preserved during the website operation.

The exact five-file package passed ten Linux packaging/deployment tests, local and live HTTPS browser checks, 320/390/768/1024/1440 layouts, 200% text, keyboard/history/anchors, strict CSP/private caching and clean console/network checks. No scripts, analytics, public route or DNS/WAF changes were added. [Published file hashes](website-files.json).

Initial website staging caught a restrictive-umask bug and restored the old guide. The publisher now explicitly makes only public payload directories traversable by Nginx; private receipt directories remain mode 0700. A Linux test reproduced the failure before the repair and passed afterward. The successful rehearsal and activation used the corrected publisher. No game restart was required for this repair.

## Recovery and remaining acceptance

Use `generated/rollback.sql` to disable acquisition and forging, then refresh through the supported supervisor procedure while retaining the matching binaries. Keep all item definitions, sockets, earned stats and forge/advanced-loot receipts. Do not restore player data from the backup or downgrade to pre-receipt binaries. The controller's destructive first-install inverse is restricted to the verified closed-gateway interval before players can receive rewards and is no longer an operational rollback option.

The live supervisor restarts the whole game runtime when a native child exits; do not kill one zone as a refresh shortcut. Website rollback is independent: use the retained publisher/receipt in `/opt/nightcap/deploy/production/website-history/20261009-zone-hunt/`.

Owner QA must still cover item/socket rendering and removal, natural acquisition, forge/reconnect recovery, advanced loot and demanding encounters with legal AA/multiclass/pet builds. The approved six-endgame-augment stat gains are material; deployment is permission for live testing, not a record of balance acceptance.
