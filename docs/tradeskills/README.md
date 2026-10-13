# Stacked materials and Craft All

Deployed on main and OVH for live QA, October 13, 2026. The owner's accepted goal is to remove
stack splitting and repeated clicking from ordinary tradeskills. Recipe balance,
success/failure, salvage, discovery and earned skill gains stay native.

Owner explicitly authorized "Push to main and server for live QA" on October 13.
This authorizes the paired rollout before native gameplay acceptance. Operators
and recovery tests are in deployment/native and deployment/client. Activation
keeps the gateway closed until the exact signed client channel and every asset
are verified; opening is a separate guarded action. Preserve this release's
remaining gameplay checks after publication.

## Player behavior and acceptance

- Experimental combines count physical units in stackable ingredients, consume
  only the selected recipe's requirements and retain leftovers in bags/stations.
- Charged nonstackable tools count as one item. Missing or unrelated ingredients,
  augments and ambiguous recipe matches cannot consume anything. An exact recipe
  quantity match takes precedence; otherwise a unique feasible recipe is needed.
- The recipe browser offers Craft One, Craft All and Stop. Materials remain in
  personal inventory. Craft All repeats the selected recipe one acknowledged
  attempt at a time and puts each result away before starting the next attempt.
- Exhaustion, failed validation, full inventory, closing/changing the crafting
  context, zoning or disconnecting stops repetition. A failed skill roll is a
  completed attempt and may continue. A missing acknowledgement is never retried.
- Ordinary recipe/class/race/skill/station/quest requirements remain authoritative
  on the server. The client cannot grant items or authorize a recipe.
- Reforging Box, transformation molds and augmentation devices retain their
  distinct behavior. Container-consuming recipes require exact ingredients.

## Implementation

1. Add the reviewed full-source tradeskills translation unit to the tracked
   customization overlay. Replace slot-count matching and blanket deletion with
   a shared bounded quantity planner. Revalidate after quest callbacks.
2. Harden the existing recipe-list combine validation and component planning so
   repetition cannot multiply unchecked container or quantity mistakes.
3. Extend generated tradeskill SIDL and guarded x86 proxy controls using verified
   native notification/frame/reply paths and a small tested repeat controller.
4. Compile native regressions and proxy/runtime fixtures, verify all new exact
   executable signatures, and stage paired server/client outputs for review.
5. Review independently, update CHANGES/status and the installed Nightcap skill,
   and provide exact in-game QA. The owner explicitly authorized main and OVH
   delivery before gameplay acceptance for this release.

## Source and commands

Baseline: Nightcap origin/main e69cdf11ecc782fc70253babb9f510fd83648386.
The original zone/tradeskills.cpp in E:/EQ_Local_Dev/akk-stack/code has SHA-256
53cd12b0e8c4e677cfaac87108634086e6c7b53ed1f869c5820c121dde286c8f.
It matches the retained October 13 AA-class-rank source manifest exactly. The
candidate compiles that translation unit against the retained release's full
source tree, verifies every retained link input, and replaces only its object.
The [build manifest](build-manifest.json) records all source and link hashes.

Server C++ uses tabs under server-mods/code; native regression runners are Python
unittest scripts under tools/tests. Client UI source is eq-client-dll/src and
generated XML lives only in managed staging, never Client_RoF2_Dev.

Focused commands (from the repository root):

```powershell
$env:PYTHONPATH='tools'
python -m unittest discover -s tools/tests -p test_tradeskill_stacks.py
python -m unittest discover -s tools/tests -p test_tradeskill_auto.py
python -m unittest discover -s tools/tests -p test_client_tradeskill_ui.py
python tools/generate-client-patch-catalog.py --check
cmd /c eq-client-dll\build.bat
cmd /c eq-client-dll\tests\build-runtime-tests.bat
python eq-client-dll/tests/test_runtime.py --eqgame E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/eqgame.exe
```

Always validate full recipes and fresh item preimages before consumption. Preserve
all unrelated overlays, player state and current signed client history. Never
publish a partial DLL/config/catalog/UI pairing or recover by restoring old player
inventory. Native tests/builds do not establish in-game visual or gameplay QA.

## Native client contract

Proxy 0.9.0-dev adds guarded entry hooks for CTradeskillWnd notification
(RVA 0x37E7F0, thiscall with three stack arguments) and frame processing
(0x37CD70, thiscall with no stack arguments). The selected-recipe helper at
0x37B770 returns a recipe record pointer whose first uint32 is its ID. Pinned
eqgame.exe is 8,774,656 bytes, SHA-256
2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e.

Independent disassembly verifies native window offsets: visible +0x196,
recipe list +0x220, Auto Inventory +0x240, Combine +0x278, and container +0x424.
The native button's +0x1a enabled byte and global pending counter at RVA
0xA635AC guard dispatch. The stock Combine route retains its own class, cursor,
and approximately 2.1-second pacing checks. Craft All invokes those original
controls; it does not manufacture combine or item-movement packets.

The zone sends the existing OP_RecipeAutoCombine reply followed by a bounded
`[NCTS1]|spawn|recipe|attempted` completion marker only after native execution
and quest callbacks finish. The proxy consumes that marker and permits at
most one outstanding attempt. Mismatched/malformed replies and completions outside
the waiting phase cannot advance the run. The marker has no attempt sequence;
native reliable transport owns packet deduplication. A failed skill roll advances
normally; validation failure ends the run.
Known local rejection before the native pending counter increments ends the
run immediately. A sent attempt with no reply after 15 seconds is uncertain:
no automatic retry, and a new run requires zoning or relogging.

After each attempt the controller waits at least 2.2 seconds from dispatch,
uses native Auto Inventory, and waits for native readiness. It gives inventory
placement up to five seconds, then stops with the remaining result on the
cursor. Stop never interrupts or replays the outstanding native attempt.

## Evidence and release boundary

The isolated zone build and dependency resolution pass. Candidate zone SHA-256:
6317ba70619dbb0d012ec9f58a4a91a096374af0b20d411eccb44fc6ac20fbf3.
Only tradeskills.cpp is rebuilt; the new helper is included only there. Existing
headers, shared-memory layout, rules, SQL recipes and quest files are unchanged.
`tools/build_tradeskill_candidate.py` verifies the retained baseline, copies a
separate source tree, and records the complete candidate manifest. An initial
compile caught two const MySQL result declarations; these are corrected.

Server regressions extract the actual production methods and execute their SQL
in SQLite: 18 experimental groups / 22 cases and seven automatic groups / 52
cases. They cover physical stacks, split/duplicate requirements, charged items,
ambiguous matches, unrelated ingredients, leftovers and world-view refresh,
exhaustion, restrictions and quest mutation. Generic world stations deliberately
have null parent ItemData and GetID()==0. Their components remain real items.

Independent review identified and corrected the null-world-parent rejection
and false uncertainty after a native local rejection. It found no remaining
high-confidence issues. Client regressions compile actual hooks with x86 ABI
fixtures and test parsing, acknowledgement isolation, stop/no replay,
autoinventory, local rejection, identity/context changes and timeout. Stock XML
checks verify unique native/custom controls, layout and preserved schema. Exact
client verification and the generated 94-site catalog pass. Final check results
and candidate asset hashes are recorded in verification.json.

These checks do not establish real RoF2 rendering, transport timing, MariaDB
persistence under failure, or owner gameplay acceptance. Ordinary tradeskills
retain their native inventory/DB persistence behavior; this change does not add
an atomic receipt system. Reforging Box and zoneforge keep their separate receipt
contracts. Main and OVH delivery is verified below; owner gameplay remains pending.

## Production delivery, October 13

Owner-authorized PR #200 merged to main at `40da0107962655f8e7a8db78eb10f6e19ea5aaac`.
The supported full-game refresh deployed the reviewed zone together with signed
game release **2026101304**, proxy **0.9.0-dev**, and the new tradeskill window.
Player access reopened after both sides were verified. Close EQ and use launcher
**Play** to install the matching client; use the managed Nightcap skin.

Fresh full SQL backup passed gzip/completeness verification. All 12 running zones
match the new binary; native/quest/database error scans are clear and the new
runtime has zero restarts. All 47 player tables and 11 custom tables were preserved
while access was closed. Other binaries, the divine-summon loader, quests/plugins,
rules, checked content and supporting services were preserved. No migration or
SQL restore was performed. This backup was not separately restore-rehearsed.

All 106 hosted assets and the channel signature verify against the shipped
production public key. Exactly DLL/config/catalog changed and tradeskill XML was
added; 102 existing assets, prior patch history and tombstones were preserved.
The desktop launcher, starter archive and guide are unchanged. The local signed
package, native manifest, 31 operator recovery tests and 13 publisher tests passed
independent review before activation.

Evidence: [deployment receipt](deployment.json), [native manifest](deployment-manifest.json),
[signed asset audit](signed-release-audit.json), [hosted verification](hosted-verification.json),
and [publication comparison](publication-diff.json). These establish deployment
and transport integrity; the exact gameplay and rendering checks below remain open.

## Paired activation and recovery

For a subsequent authorized change, follow the current production runbook using fresh
runtime/public/data preimages. Rebase the candidate if the retained zone inputs
have advanced. Preserve the current October 13 divine-summon shared-memory
loader/cache and all other binaries. This change needs a rebuilt zone and a
supported whole-runtime refresh on OVH; rule/quest reload alone is insufficient.
Never kill one OVH zone as an isolated refresh.

Publish the DLL, nightcap-patches.cfg, generated nightcap-patch-sites.json and
new uifiles/nightcap/equi_tradeskillwnd.xml as one signed launcher release.
Merge these four asset changes into the latest signed inventory; retain every
other asset, patch summary, desktop/starter channel and user preference. Clients
must close EQ and use launcher Play. Existing custom skins need corresponding
controls or the managed Nightcap skin. The new zone's completion marker requires
the paired proxy; avoid exposing raw markers to old clients.

Rollback restores the verified prior zone with its matching existing runtime,
and republishes the prior DLL/config/catalog plus stock tradeskill XML under a
higher signed counter. Preserve all earned inventory, recipe history and skill
progress. Never restore old player SQL. Repetition stops on disconnect; no
queued batch is stored server-side to replay after a restart.

## Exact in-game QA for owner acceptance

Use an owner test character at the six crafting stations in the East Commonlands
tunnel workshop. Artisan Veyra (NPC 999820) supplies the separate Reforging Box
control; it must still require its existing four-copy upgrade. Also use a portable
tradeskill bag appropriate for the chosen ordinary recipe.

1. Use a known ordinary recipe with two stackable inputs. Record item IDs,
   quantities and skill. Put 20 of each into its experimental container and
   Combine once. Exactly one recipe's quantities disappear; leftovers remain
   visible. Close/reopen the station and relog to confirm persistence. Test both
   a world station and portable bag. Where those inputs match multiple recipes,
   expect no consumption and the instruction to select a recipe.
2. In the recipe browser, leave ingredients in personal bags. Choose that recipe
   and Craft One. Confirm one native result/skill roll and normal messages. Clear
   the cursor, then Craft All: results enter inventory, attempts proceed roughly
   every 2.5 seconds, and exhaustion stops without extra material consumption.
3. Test requirements consuming two units from one stack, split stacks across
   bags, and a partial final set. Verify totals through success, failure and
   salvage; failed skill rolls may continue and retain normal material costs.
4. Click Stop during a run, then immediately Craft All/Craft One. At most the
   already-sent attempt finishes; nothing replays. Change recipe, close the
   window, move away from a station, enter combat, zone, and relog during separate
   runs. Each must stop; no old run resumes in a new context.
5. Fill inventory before an output cannot fit. Confirm the result remains on the
   cursor and the run stops. Clear it and restart. Put an item on the cursor just
   before Craft All; a native local rejection must allow another run after the
   cursor is cleared. A genuinely lost completion must request zoning/relogging.
6. Try the wrong station, missing ingredient, unrelated experimental item,
   socketed ingredient, unavailable class/race/skill recipe, and a container-
   consuming recipe with surplus materials. No unintended items are consumed.
   Container-consuming recipes use exact Experiment ingredients.
7. Inspect both window sizes/UI scales in use: Craft One, Craft All, Stop and
   Auto Inventory are readable and clickable; recipe selection, search,
   favorites, experiment, and close retain native behavior. Recheck Reforging
   Box, transformation mold and augmentation-device controls independently.

Record character, recipe IDs, before/after totals and screenshots or logs for any
failure. Owner gameplay and visual QA remain pending until actually performed.
