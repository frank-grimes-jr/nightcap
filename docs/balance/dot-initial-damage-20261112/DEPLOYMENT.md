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
