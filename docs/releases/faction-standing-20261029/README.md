# Player faction standing window — October 29, 2026

Main promotion authorized October30; server deployment deferred by the owner's
latest instruction, “Merge main only for now”. The clean main-based source and
faction-only native build pass. No server installation, public wiki publication
or owner visual acceptance is claimed. Current scope and verification are in
`release/AUTHORIZATION.md` and `release/verification.json`.

## Intent and existing options

The owner requested an in-game view of the character's faction standings with
bars, numbers and easily readable white text. Current integrated source
85a42253 retains `#faction` at QuestTroupe access, with reset operations and
earned-hit review; it is unsuitable for general player access. `/consider`
reports a target's reaction, not a numerical faction browser. The inspected
RoF2 default EQUI catalog has no faction window. No existing Nightcap player
faction browser was found in command registration or global-player handlers.

## Candidate behavior

- `#factions`: all loaded named factions, alphabetically, six per page.
- `#factions qeynos`: case-insensitive literal name search, including spaces.
- `#factions 2 qeynos`: page 2 of the same search. `#factions 2` pages all factions.
- `#factions target`: your own standing with a targeted NPC's positive faction.
  Missing targets, player targets and special/non-numerical factions return a
  white-text explanation. This never reads another character's earned standing.

The existing scrollable popup displays white `#FFFFFF` text, standing names,
exact signed totals, 20-segment text bars, numeric min/max and earned/modifier
breakdown. Bars show the full attainable range, not the next tier. Reissue the
command to refresh after a kill, hand-in, gear change or faction spell/illusion.
No new client patch is required; native font, scrolling and saved window size
still require visual QA. A fixed range has a `[fixed]` indicator.

Totals call native `GetModCharacterFactionLevel`; labels call
`CalculateFaction(nullptr, total)` and use current server faction threshold
rules. Bounds follow `SetFactionLevel`/`SetFactionLevel2`: personal minimum
`min(0, mods.min - mods.base)`, maximum `max(0, mods.max - mods.base)`, shifted
by the same modifiers as the total. This preserves base, primary class, current
faction race, deity, spell and item modifiers, including factions without an
earned row. Only bar fill is clamped; the exact total remains visible.

NPC reactions are distinct: invisibility, feign, noncombat zones, pet ownership,
merchant adjustments, aggro and custom encounter policies can override `/con`.
The view does not change these policies or any faction values.

## Implementation and verification

- `server-mods/code/common/faction_standing.h`: bounded request parser, escaping,
  bar arithmetic and popup composition.
- `server-mods/code/zone/faction_standing.inc`: caller-only loaded-cache access,
  sorting, native totals and bounds; included from registered `command.cpp`.
- `server-mods/code/zone/command.h`: declaration; existing GM command unchanged.
- `tools/tests/test_faction_standing.py` and both faction fixtures: compile/run
  the real view and command, including extracted native total calculation.

Run `python -B -m unittest discover -s tools/tests -p test_faction_standing.py -v`.
Windows sandbox testing sets TEMP/TMP to this checkout's `work/test-temp`.
Initial tests failed for the missing feature, then passed after implementation.
After integration, all three faction groups, five inherited augment groups and
19 wiki checks pass; the integrated site builds 497 pages. The inherited augment
tests need UTF-8 mode on Windows (`PYTHONUTF8=1`). Separate code review found no
blocking findings; rule thresholds are source-reviewed because the command
fixture stubs label formatting.
Tests cover cache gaps, base-only factions, modifier changes, self/target isolation,
invalid inputs, literal search, escaping, pagination, range endpoints/overflow,
fixed/invalid ranges, payload size and unchanged earned state. The popup is capped
below its actual 4096-byte packet field. All feedback is Chat::White.

All 45 authored wiki articles and generated catalogs were assessed; Commands, Features, In development and
Change Log carry explicit candidate notes. Home, generated rewards and all
unrelated live release labels are preserved. See `wiki-review.json` and the
source-drift report. Historical global drift is not silently approved.

## Scoped main promotion — October30

Dev PR366 and test PR367 verified the feature. The main promotion starts from
ea2f7efc and takes only the four faction C++ files plus their tests/documentation.
Newer main/client/wiki work is retained; the unrelated augment and zone-capacity
candidates are excluded. All three faction test groups pass on this source.

`tools/build_faction_release.py` authenticates the retained Hate baseline and
enforces exactly four changed/new source files. Only the command unity unit is
recompiled; its archive member is replaced and the retained inputs first reproduce
the predecessor byte-for-byte. `release/native-build.json` records the successful
selective zone link and complete provenance. No rule catalog or data ABI changed.
This build is a prepared release artifact, not an installed runtime.

The earlier six-file integrated test build below remains historical evidence.

## Native build evidence

`native-build.json` records successful Clang14/C++20 compilation of the complete
unity unit containing command.cpp, plus the inherited dev zone_hunt.cpp. Both use
full native headers in an isolated source copy. The command header is checked to
add only its declaration. The tool authenticates all 2,842 retained source files,
reproduces the retained zone byte-for-byte, preserves every unchanged static-
archive member and link input, then links the new candidate and rechecks sources.
This is a selective rebuild against authenticated retained objects, not a clean
full rebuild. Existing compiler/system dependencies are reused. There are no
new compile errors; existing MySQL-comparison and command empty-body warnings
remain. The candidate is not installed.

Reproduce with `python -B tools/build_faction_candidate.py --baseline-manifest
docs/dungeons/hate-layout-20261029/native-build/manifest.json` on the documented
local build host. The manifest records exact commands, paths and binary hashes.
Separate review found no blocking source/object provenance issue.

## Delivery and recovery

For the faction display alone, only a matching rebuilt **zone** is required. No schema/content migration,
quest reload, cache rebuild, client asset or custom rule catalog change. Preserve
the current release's world, shared_memory and signed client pairing. Runtime
command settings can override compiled access: verify `factions` has access 0
and does not collide with a persisted alias during release preflight. Do not
lower the existing `faction` command's access.

The integrated test binary also retains the unreleased dev augment change. It is
not a faction-only production payload: a later release must rebuild on its
authorized production source, preserving live changes and excluding or separately
authorizing the augment delta. The native builder deliberately enforces this
exact six-file integrated delta.

The owner authorized scoped main promotion, then explicitly deferred server
deployment. A later live deployment needs renewed authorization. OVH's
supervisor restarts the whole game when a child exits: never kill one zone as a
reload shortcut. An authorized rollout must use current retained source/evidence
and the established guarded release process. Recovery removes only this display
change in a compatible rebuilt zone; it never restores player snapshots.

## Exact in-game QA after authorized installation

1. Log in with an ordinary player account and run `#factions` in East Commonlands.
   Verify white readable text, positive/negative values, standing labels, bars,
   scrolling and resizing with the managed Nightcap skin. Reopen with saved size.
2. Run `#factions qeynos`, then `#factions 2 qeynos` if multiple pages exist.
   Check alphabetical order, no overlaps, page count, no-match and invalid-page
   feedback. Multiword searches need no quotes. Try `#factions 0`.
3. In North Qeynos, target a city guard with a positive faction and use `#factions target`.
   Compare with a privileged read-only inspection of that character's earned
   value and modifiers. Target another player, clear target, and target a
   special-faction NPC: no other character's standing is shown.
4. On a disposable QA character, record a faction hit from an ordinary kill or
   hand-in; reopen to verify its change. Equip a faction item or use an appropriate
   faction spell/illusion and confirm current modifiers update. Zone/relog and
   confirm persisted earned values. Untouched factions retain base standing.
5. Compare neutral, hostile and allied rows plus a min/max standing fixture.
   Confirm bar endpoint labels match totals; white remains readable throughout.
   `/con` overrides must not be described as a faction arithmetic defect.
6. Verify the player's existing `#faction reset` remains inaccessible. Check
   server logs for command errors and confirm repeated views make no faction writes.

Native rendering, actual player command access and gameplay acceptance remain
open until these observations are recorded.
