# DoT release deployment — November 12

Owner authorization: **“Deploy it to the live server so I can test it in game.”**
This authorizes this change's main/live promotion before manual acceptance.
Gameplay and combined-build balance acceptance remain open.

The fresh production probe identifies the current Quick Buff v2 image
`sha256:faf2e410d1b1927ef6e27d9cb187cf00ba58c7e06307fea9bef29a655efbc0d1`,
zone `3eeb72c9`, signed client `2026111201` and wiki
`20261112-quick-buff-v2`. Zero native players were present. Retained local inputs
reproduce that zone exactly before compiling the five-line spell-effects change;
candidate zone is `dfa5c6144490737619d6bcab8815da5f2cd725235284bbe13c54c9c5e861130c`.

The SELECT-only production spell capture supersedes local counts for this
release: 3,629 DoT definitions, 986 with 1,002 negative HPOnce slots and 2,643
without. It includes NPC/later-era definitions, not a legal player pool. Ninety
spell definitions differ from the local snapshot. No captured DoT has a separate
SPA147/350 percentage-HP or Mana Burn handler. `production-audit.json` records all
affected spell/slot identities; no content table is changed.

`rollout.py` authenticates its stage, binary, source, test evidence and exact
previous operator SHA-256, then binds the existing reviewed Quick Buff v2
functions to the new stage/image/manifest. Its operator is retained unchanged,
including deployment/GM locks, native online-player rejection, 125-second closed
admission drain, clean supervised whole-game stop, stopped full backup, exact
normal saved-state boot handling, one market rotation, content/rules/cache/quest
preservation, native identity/error checks and failure hold. New stage validation
has six tests; the unchanged admission/backup/state/open functions have nine fault
tests, also run on Linux before preflight. Existing Quick Buff console labels
come from that retained operator; the stage and DoT action receipt identify the
actual release. No old terminal activation is replayed.

The new image adds only `bin/zone` above the current immutable base. World,
shared-memory loader, login, UCS, supervisor, cache and quests stay paired.
Preserve the current signed client and wiki during the native restart. No client
download, rule, schema, SQL spell edit or player repair is needed. Failures keep
admissions closed. Recover by inspecting the one-shot receipts and current state;
never blindly replay activation or restore an old player snapshot. A rollback
must use the retained previous image with a fresh current-data preservation
check and the supported whole-runtime process.

After native activation, publish only the reviewed DoT guide delta from a source
tree that exactly reproduces the then-current public wiki artifact. Preserve
other public files, private downloads, Nginx inode/config, channel and all five
service identities during publication. Verify HTTPS hashes, headers and private
denials. Keep the historical global REVIEW REQUIRED and unrelated Build Lab pin
failure separate from current release proof.

Receipts and post-release status are appended after observing the actual result;
this plan alone does not establish deployment. Exact owner in-game steps are in
README.md, especially Disease Cloud/Poison Bolt versus Clinging Darkness/Heat
Blood, repeated casts, normal ticks and standalone nukes.

## Serialized release and replacement package

PR426 merged at `a97c55d0078967791430c02534c8513b9a9e427d`, preserving the
concurrent main Imitate Death change and both guide/changelog entries. The first
DoT stage passed preflight but its activation could not acquire the deployment
lock held by that release. It failed before calling activation, closing access
or changing runtime; no DoT activation receipt was created. Keep its proof and
`activation-v1-lock-refusal.log`; do not replay that old package.

The replacement DoT stage is `dot-no-initial-damage-20261112-v2`. Its isolated
build authenticates all 2,857 Imitate Death source files and retained inputs,
reproduces the `7bb5bd17` predecessor, then compiles the whole changed DoT
translation unit and links candidate
`7b61b5acdf3ba89b5326ac1bf13bb777fe7f02ea00a8cde622a10bc3835e8bf5`.
`native-build-current-baseline.json` records that proof. The Imitate Death AA
object is preserved; the additional source delta is only spell-effects.cpp.
Stage authentication tests pass with the new stage identity. The replacement
requires a fresh live baseline after the earlier release and its wiki publication
complete, plus a new one-shot preflight, backup and state-preservation cycle.

## Observed result

Stage v2 is deployed; admissions are open. Independent verification records all
12zone workers at7b61b5ac, restart count0 and native/quest/database errors0, with
world95fc228a/shared_memoryb60c4dfc, signed2026111201, cache, quests and DB/web/
tunnel identities preserved. The fresh stopped backup passes gzip integrity;
normal saved-state expiry and exactly one market rotation passed. No player
snapshot restore or spell/rule/schema edit occurred.

Wiki20261112-dot-ticks-v2 is published from the authenticated Imitate Death source
artifact. All613HTTPS hashes/security headers and five private404denials pass;
609outputs remain exact, all five services/private downloads/config stay intact,
and pointer rollback was rehearsed without Nginx reload. Review ledger and the
historical unrelated Build Lab source-pin failure remain unchanged.

Read deployment-receipt.json for exact host receipt pins, production-verification.json
for independent live identity/backup proof, and wiki-publication.json plus
wiki-public-verification.json for separate publication/HTTPS evidence. Owner
in-game and combined-build balance acceptance remain OPEN; this is a release
for their requested testing, not completed player acceptance.
