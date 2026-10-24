# Candidate review

Reviewed from main7fe3a783, then reconciled with dev1a8a4917 in an isolated feature checkout. The merged hooks preserve High Keep rescue and aggro cleanup. No deployment,
installed-client mutation, production player write or wiki publication performed.

## Correctness and isolation

The new policy uses native class bit1<<5, while the item uses item class mask16.
Its task9801, personal tables, receipts, encounter tokens and reserved identities
are separate from Camil. Reconnect projection derives from the ledger; the last
task row never independently grants a reward. Native inventory receipts own
delivery and history. The admission capacity check is inside the allocation
transaction before transfer, with a reconnect check using the current run.

Encounter cleanup validates attempt/owner tokens so recycled entity IDs cannot
depop another attempt. Defense failure clears temporary actors and preserves
earned chapters. A native NPC-death gate excludes guardian/war-soul IDs from the
whole XP award block, including raid and leadership paths; exp_mod=0 alone was
insufficient. The dynamic actors are outside the curated loot predicate.

The actual native special-ability constants were checked:5is Flurry, not Enrage.
The Echo retains the5-percent flurry, and its guide names that mechanic accurately.
Champions have charm/fear/fleeing immunity14/17/21; stun remains available, and
war souls remain controllable so SK crowd control still matters in the defense.
Kael champions/knights use native StormGiant189, confirmed against captured
Watchman Sunderthorn113001 and common/races.h;49is LavaDragon. War souls use
Classic Spectre85/bodytype3. The guardian is human-sized6. Existing interaction
markers retain the shared Keeper EyeOfZomm108 model; native visual QA remains open.

Kael is appended after existing dungeon indices. Prior reward IDs remain stable;
new final rewards occupy960420–960425. Existing budget tests cover the new designs.
The contract includes all new content, schema and reward cache definitions.
Migration guards refuse preimage drift, reservations, item/task references,
unsafe engines/triggers and saved public living NPC state. It starts disabled.

## Asset and release boundaries

The recovered source EQG is hash pinned. The staged HE91 package retains every
preexisting WLD fragment's semantics and non-WLD file bytes, including HE90.
Independent8KiB extraction, typed palette closure, skeleton registration and
24-frame150ms animation checks pass. Blender inspection found face intersections;
the enclosed new head variant now omits that inner surface. This does not modify
other head variants. The preview also exposed inverted DDS-to-BMP vertical
coordinates: the conversion now flips V, consistent with the DDS branch in
[the reference importer](https://github.com/Zaela/EQGModelImporter/blob/master/src/viewer.cpp).
The regenerated decoded archive preview shows the skull texture and mouth flame
across all 24 fits. Native rendering, neck seams and animated flame playback
remain explicit in-game acceptance items.

The old Camil generator and candidate default generator produce identical archive
bytes. The repository's older reviewed-candidate hash assertion fails identically
on unmodified HEAD; see camil-preservation.json. Its expected hashes were not
silently changed. The 57 focused checks exclude that preexisting assertion and include the integrated High Keep, healing, aggro-departure and saved-home regressions.

The wiki overlay now uses published custom-Features source a0bd0faa. All 24
maintained guides are reviewed; Home and Features remain byte-identical and
existing preview anchors remain reachable. Fourteen current content/link/package/
history tests pass. POSIX publication/recovery cases remain a separate release
gate; no website was published. EVERFROST.md records the entrance-only revision,
its native routing regression, preserved combat definitions and exact placement.

## Acceptance still required

The final world, zone and shared_memory build passes with all overlay sources
matched to its manifest. Native combat measurements record 24 kills and four
lower-progression control deaths (see BALANCE.md). They are a bounded diagnostic, not proof of optimal gear,
every held-class combination or the complete scripted route. Follow QA.md for
native client and full-route acceptance. The shared dungeon/attack hooks include dev1a8a4917; recheck subsequent branch changes before promotion. Release
requires paired native binaries, schema/content/cache, exact scripts and signed
Classic archives, with fresh target-specific preimages and owner authorization.
