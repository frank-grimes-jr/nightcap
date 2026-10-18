# Independent review — cooldown identities

Reviewed the candidate based on deployed main `0eef50e`, using the code-review-and-quality review-agent pattern. The reviewer did not edit production code or apply a migration.

**October 17 review status:** approved as a source candidate for the documented AA and cross-domain identity correction, with no remaining actionable findings in that delta. At that review, the native build was verified but not installed. The owner subsequently authorized main promotion and deployment, completed October 18; see [production verification](deployment/production-verification.json). This does not establish complete independence for all skills or owner gameplay acceptance.

## Findings resolved in source

- Replaced the unsafe proposed uint16 AA allocation with disjoint positive namespaces. Item bounds prevent overlap with discipline keys; casting and persistent-timer consumers retain uint32 identities.
- Kept AA client slots independent of ownership, charges and rank purchases. Table/timer refresh, completion, abort, reconnect and scoped resets use stable family identities. Single reset and the GM command now use the requested rank.
- Corrected the native AA test oracle: excess focus remains signed; exactly-zero effective reuse bypasses the native clock check. The server still enforces the retained deadline.
- Preserved legitimate discipline `timer_id=-1` with independent spell keys. Tests now use the actual signed int8 field; all twenty grouped timers and ungrouped reset paths preserve other domains.
- Moved the migration receipt query after packet validation and successful zone authorization, before ghost/profile work. Missing receipt or failed timer loading disconnects.
- Added receipt/backup transaction-engine checks and backup shape checks. An existing nontransactional receipt must not survive a failed timer transaction.
- Added item click/delay preimage checks: a same-count swap in qualifying catalog membership must not silently omit a successor timer. Ungrouped discipline membership is also guarded.

## Evidence and tested bounds

The reviewer independently passed 16 AA tests, including 27,060 ordered distinct-family pairs in each of activation and publication, 825 same-family rank cases, and the production completion slice. The duration/item/discipline suite passed 26 tests / 37 scenarios; the subsequently added longer-native-item-deadline test also passed independently, for 27 tests / 38 scenarios across those runs.

Inspected the pinned RoF2 packet, getter/setter and readiness instructions and native fixture. Verified the retained PTimer load/store, casting timer fields, repository types and remaining external callers for narrowing. The current catalog needs at most 57 ordinary activated AA slots; runtime refuses more than 100. Tested item bounds, discipline groups 0–19, signed -1, invalid groups, reset isolation, relog/class remapping, and preservation of the longer item deadline.

Reviewed the final local MariaDB rehearsal report and its test implementation: 15 tests passed, zero failures/errors, scratch schema removed and production untouched. Coverage includes failure after receipt insertion, precreated nontransactional receipt/backup tables, backup shape mismatch, same-count item membership swaps, positive click/delay drift, conservative deadline merging and rollback rejection of unknown keys. This reviewer independently regenerated both SQL outputs in memory and verified exact agreement with the report:

- Catalog SHA256: `e71d550ac445732e36ba316a86f3a079f76a556835b4120c751deb05c8ba73be`
- Forward SQL SHA256: `e7e012ecaa289e7376855763bd9896932137dd15557b427c2a7faa767f696e85`
- Rollback SQL SHA256: `4bb4fdce6990c66acb05c300821084855e17b05f06766a0aca53d5fcd0faaa74`

The rehearsal ran in a disposable local schema; this is migration evidence, not production deployment evidence. The reviewer inspected the report rather than independently repeating its database execution.

Reviewed [manifest.json](manifest.json), [build-final.txt](build-final.txt), [build-ldd.txt](build-ldd.txt) and the build/finalization scripts. The final zone target linked successfully and all recorded dynamic dependencies resolved. Independently compared the manifest's eight changed source hashes with the exact committed LF bytes in candidate `d7f5c1d54c6436066e0522f0cd9e62a5d3521e84`: all match both the full source manifest and the current worktree, and the changed-file set matches the commit. The manifest records 2,823 source fingerprints and zone SHA256 `d3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a`. The build scripts preserve the fingerprinted baseline and verify final source stability; the reviewer inspected this build evidence rather than repeating the complete build or independently hashing its remote executable.

## Remaining acceptance limits

- The October 18 migration and deployment are verified. Owner gameplay acceptance remains open; source/build/runtime checks do not establish visible gameplay acceptance.
- Execute [QA.md](QA.md) with the paired server/migration and existing Monk client. Native fixtures do not establish visible hotbutton, login, class-change, inventory or live cast behavior. Unlinked items use inventory timestamp publication; their recast-delay helper does not emit a native group packet.
- Exactly-zero native AA reuse cannot display a retained server wait. Current allowed haste totals stay below base reuse, but future content must retain this check and the 100-slot capacity check.
- Content-defined spell, grouped-discipline and linked-item sharing remains unchanged, including the documented Harmshield/Cannibalize and Battle Cry/Throw Stone groups. Catalog presence does not prove learned/owned access.
- The follow-up basic-skill audit confirmed generic combat timer 25 still groups Bash/Slam, Backstab, Frenzy and Kick outside held-Monk RoF2 scope; Begging/Pick Pockets share 27. Disarm uses 26; the six supported Monk skills retain separate 500+skill keys. These are unresolved behavior boundaries, not endorsed multiclass policy. [README.md](README.md) records exact source/native evidence and [QA.md](QA.md) adds scoped reset checks. All 16 Monk/combat tests were rerun successfully; no implementation changed in this follow-up.
- Migration is a stopped-game, one-session operation without `--force`, using a fresh backup and matching catalog. Preserve timer rows and their receipt together on restore. Rollback must retain the original migration catalog, conservatively merge current deadlines, reject unknown keys and remove namespaced rows before old uint16 code starts. Existing ambiguous waits are preserved until expiry.
