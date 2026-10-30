# Cast-bar timing repair — October 30, 2026

**Published as signed client 2026103002 for owner testing; visible acceptance remains open.** Based on integrated
`989a464c` in `E:/EQ_Local_Dev/_worktrees/cast-bar-timing`, branch
`feature/cast-bar-timing-20261030`. The owner reports that two level-1 Wizard
nukes barely move the casting bar until the final instant. This resolves the
data defect behind the older September 27 investigation; visible QA stays open.

Main PR376 merged as `ea2f7efc591643339b7dedf6b0759471f558866b` after explicit
owner approval. Signed client2026103002 and wiki20261030-cast-bar-v1 are published.
All148client assets/signature/runtime pairing and499wiki hashes/security headers
verify. Allfive service identities/start times/restart counts are unchanged.
Client publisher20Linux tests and wiki16Linux recovery tests pass. Publication
changes only spells_us.txt and three wiki files, preserving the newer recall
label and Cazic-Thule releases. See deployment.json and release/ receipts.

## Cause and scope

The October 30 read-only production snapshot gives Frost Bolt (54) and Numbing
Cold (374) 1000-ms casts, and Blast of Cold (372) 1500 ms. The installed client
and current published spell asset give all three 50 ms. Native RoF2's gauge at
VA `0x761fb0` divides remaining time by spell-memory cast duration (`+0x10`) and
clamps at 1000 per mille. It therefore stays full until the final 50 ms. This is
a client spell-definition mismatch, not evidence of slow server execution.

The defect covers 638 non-DoT spell definitions, including 100 definitions whose
server cast time is zero. Every repaired time matches both the read-only current
production value and the SHA-pinned original spell file. The explicit reviewed
catalog avoids resetting intentional Bard, DoT and custom spell changes.
`assets/spell-cast-times.csv` records each ID, name and authoritative base time.
Its 638-row scope spans the full packaged catalog, not 638 currently legal spells.
No server timing, damage, spell access, AA/focus modifiers or content is changed.

`tools/client_spell_cast_times.py` accepts only the stale 50-ms value or the
reviewed corrected value, verifies identity/completeness, preserves all other
fields/line endings, and stages exclusively outside the input client directory.
`tools/client_gameplay_assets.py` applies it before the existing instant-DoT
transform so ordinary regeneration cannot reintroduce the known mismatch.
New deliberate timing changes to these IDs require reviewing this catalog too.

## Evidence and limits

Production content was read at `2026-10-30T11:32:57.618506+00:00` using one
consistent READ ONLY transaction, restricted to spell ID/name/cast time. No
character data was queried. The 40,746-row capture is private local evidence;
the reviewed subset and hashes are recorded here. DB content is not a fresh
inspection of every worker's memory. Current source starts the server timer
from its effective cast time and announces base cast time through BeginCast.

The initial public channel capture was release `2026102901`, SHA-256
`de5959ffdb6dff44e3de9626cb8dba7c57dd4787fbe9912505d5b1955f10c5d8`,
with 148 descriptors. A read-only host check verifies the hosted spell bytes
against that descriptor; they exactly match the installed input file. This is
not a new HTTPS/signature verification of all unrelated assets.

A continuation recheck at `2026-10-30T12:03:15Z` finds release `2026103001`,
channel SHA-256 `fa9488d44023362d7d8e792fdd5eae6af2c9e8cdc0a26f3d31a6d734ba578f6b`.
It repairs Ancient Attunement labels but retains the same faulty spell asset.
The local unsigned plan now proposes `2026103002` over this newer baseline,
changing only the spell descriptor and retaining all other 147 descriptors,
history and tombstones. See release-plan.json. Recheck the public baseline and
available counter again before signing; this plan is not publication approval.

The exact pinned executable is mapped in a separate x86 test process; no game
is launched or modified. The original gauge executes unchanged, with only spell
lookup/profile/item-cast classification supplied by the fixture. The shipped
spell file fails 2752 of 5105 checks; the corrected file passes all 5105 across
638 spells, covering progress, zero times, expiry, cancellation and no player.
The fixture's initial spell-lookup ABI setup was corrected to native `ret 4`
before these recorded RED/GREEN runs. Native drawing, actual packet arrival,
focus combinations and the owner's installed play session require in-game QA.

Four repair tests and six existing asset tests pass. Exact-file preservation and
the repaired scope through normal spell-generation composition are verified.
The existing class-restoration stage rejects published custom spell 43220, so
the normal generator is checked from its preserved input; it is not used to
replace the entire current signed file. The release applies the standalone
correction directly to verified current bytes, retaining all later custom spells.
See verification.json and wiki-review.json.
The protected reference and installed game were read only throughout.

## Delivery and recovery

Only `spells_us.txt` changed in signed release2026103002. The retained staged output is
`.local/cast-bar/staged/spells_us.txt`, SHA-256
`a4bedf590660b9a3441bc1406f40a8427b71ff56694496f8fca97e3ed9c7a34a`.
For future recovery, publish at a new release counter after authorization, verifying the then-current
manifest and retaining all 147 other descriptors, runtime DLL/catalog/config,
history and tombstones. No server/quest/cache reload or launcher/DLL rebuild is
required. Fully exit EQ and use launcher Play so the client reloads spell data.
Never edit the protected reference or an installed player folder directly.

If recovery is necessary, publish the retained spell asset in a higher signed
release counter while preserving the then-current remaining inventory. This
restores the old display defect; it does not require any player-data rollback.
The owner approved main, signed client and wiki publication in AUTHORIZATION.md.
Signed2026103002 is published and its 20 Linux publisher tests pass; release/
holds exact preparation, activation and HTTPS receipts. See
[QA.md](QA.md) for the exact live check. Wiki20261030-cast-bar-v1 is published and verified. No visible gameplay acceptance
is claimed; Diiv testing is the remaining owner check.
