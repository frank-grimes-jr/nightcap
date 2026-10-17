# Recommended AA filter — October 17 candidate

The owner approved a class-aware starter filter after the AA progression review.
This candidate adds **Recommended AA** beside **Can Purchase**, a Recommended
explanation column in all four native tabs, and a status line. It is implemented
and locally tested, **not deployed, signed/published, installed or player accepted**.
Full zone compilation/link and native rendered gameplay QA remain open.

## Behavior and accepted scope

The server selects up to ten next legal purchases from 34 curated AA families.
Natural Durability, Combat Agility and Combat Stability anchor survivability;
class-eligible melee/spell/pet criticals, Monk attacks, songs, healing and mana
efficiency supply damage and sustain. Recovery and movement complete the starter
choices. Targets generally begin at rank 3; after that, existing released deeper
ranks become specialization choices. The list may shrink as useful lines complete.
This is guidance, not a simulated optimum or evidence of encounter balance.

The normal native filters intersect the shortlist. With Can Purchase off, it also
shows selected future purchases; with it on, native affordability/prerequisites
still decide visibility. Missing prerequisites can enter the shortlist themselves.
Supporting skill/pet requirements appear as **Later**. Extra-class pet slots count.
Already owned, excluded and class-ineligible next ranks are not recommended.
Filter off restores the ordinary catalog; Reset clears the recommendation checkbox.
The checkbox starts off and is a window-session preference, not a saved account setting.
Recommendations apply across the existing four tabs; they are not a fifth combined tab.
The shortlist is selected by priority; native row sorting remains under player control.

No AA unlock, level purchase gate, cost, XP, character record or combat formula
changes. Passive AA remains the separately deployed 10% / 4,000 XP per point.
The AA expansion proposals in the progression review are still proposals.

## Implementation and proof

- `common/aa_recommendations.h`: bounded curated policy, starter/deeper priorities,
  reason vocabulary and deterministic deduplication. Advice never authorizes a purchase.
- `zone/aa_recommendations.inc`, included by `aa.cpp`: native held-class/era,
  ownership and prerequisite adapter. `SendAlternateAdvancementStats` computes
  updates before the native refresh packet. Identical results are cached; banked
  points remain the existing native filter's responsibility.
- `#nightcapui recommended` is an internal capability opt-in; legacy `refresh`
  still works. The first capability upgrade can complete the just-throttled
  refresh once; later requests keep the existing throttle. Old clients receive
  no new metadata. New clients on old servers retain class metadata and the full
  ordinary list, with an unavailable recommendation status.
- `[NCUI1]B/R/E` binds a bounded, counted, atomic batch to generation/character/
  zone/instance/spawn. Class snapshots and leaving game clear it. Incomplete,
  stale and invalid data cannot authorize anything or commit a partial list.
- `ui_hooks.h`: native filter call RVA `0x208C73` adds the recommendation predicate
  before row construction, preserving native selection reconciliation and purchases.
  Notification entry `0x20AA80` consumes the new checkbox and passes other controls
  through; stock Reset also clears it. The checkbox offset `0x1E4`, native filter
  callee and caller are exact-byte guarded. Scoped filtering restores on exceptions.
- `tools/client_gameplay_assets.py`: builds the 1020 x 524 XML window from the
  protected stock reference, preserving the lexical Schema declaration. No original
  client file is written. Layout dimensions/controls are checked; visible rendering
  has not been accepted.

Validation commands and retained results are in `verification.json`. The x86 DLL
and 21 fixture executables build; all eight runtime test groups pass. The actual
server sender is exercised against the captured legal catalog across 816 class
combinations, plus ownership, prerequisite, completion, skill and cache controls.
Native client tests execute the pinned RoF2 filter bytes with controlled transport,
affordability and UI boundaries; they do not launch the game. Five XML tests and
99 exact-client catalog sites pass. The full launcher Go suite passes.
The pre-existing multiclass refresh fixture needed four explicit unchanged
ownership/bonus boundary stubs to match the current source; this does not certify
ownership persistence. Re-run its seven scenarios with Python UTF-8 enabled.

## Build, integration and release boundary

Source baseline is `a59974d` plus the separately committed passive-AA operation.
Use feature → dev → test → main after owner acceptance. Do not promote this
candidate as production ready while the full zone build and visible QA are open.
The local Docker Linux engine is unavailable; no full zone build is claimed.

Pair a rebuilt zone containing the new `.inc` and common header with proxy
`0.10.0-dev`, generated patch catalog and `EQUI_AAWindow.xml`. Preserve all current
retained server source and signed client assets/history when integrating. In
particular, the separate Monk/cooldown candidates modify `ui_hooks.h`; combine their
changes rather than replacing that file with this branch. No new rule catalog,
ItemData, database migration or world ABI change is introduced. Rule/AA reload
alone cannot install native code. Use a coordinated authorized server release;
OVH child exits restart the full runtime. Never kill one production zone for this.

Rollback pairs the previous zone and signed client generation using the normal
retained-source/signed-counter process. No player records or earned ranks need
restoration. UI guidance is reversible without refunding purchases.

## Exact in-game QA before promotion

1. In the East Commonlands tunnel, use an ordinary new character. Open all four
   AA tabs; verify Class and Recommended headings, the new checkbox beside Can
   Purchase, status text, readable columns, keyboard selection and horizontal scroll.
   Try supported client resolutions and UI reload. No Default-skin fallback.
2. Enable Recommended; count at most ten families across tabs. Use a fresh melee,
   caster/healer and pet build, including PAL/WAR/MNK. Verify useful survival and
   damage choices match held classes. No released AA disappears with the filter off.
3. With Can Purchase off, select an unaffordable recommendation and inspect its
   cost/description. With it on, verify unaffordable/blocked ranks disappear. Compare
   passive/active, category and expansion filters, sorting and Reset. Purchase a
   selected legal rank; verify exactly the displayed AA is bought and points charged
   once. Its next rank appears or the completed line leaves the shortlist.
4. On a Monk test character, inspect Critical Mend without First Aid 3; the next
   eligible First Aid step is offered and the blocked recommendation is labeled.
   Below usable Monk/Backstab skill availability, later recommendations must not be
   presented as immediate damage. Train the skill and refresh the filter to recheck.
5. Summon a permanent pet through an extra class, refresh the filter, and inspect
   pet guidance. Dismiss it and refresh. Test a primary class without a native pet.
6. Use The Ancient Chronicler in the tunnel to adopt/release extra classes on a
   disposable test character, then zone, reconnect and switch characters. Verify
   recommendations refresh without stale rows; ordinary ownership/refunds still
   follow the existing class-release rules. Do not release Palwar's real classes.
7. On Palwar, verify completed starter lines are absent, preserved dormant Combat
   Fury rank 4 is never offered for repurchase, and deeper legal choices are advice
   only. An exhausted list must explain how to browse the full catalog.
8. Validate an old-client/new-server and new-client/old-server test pairing:
   ordinary class metadata, AA purchase UI and unfiltered catalog remain usable.
   Repeat purchases after sorting and toggling filters; no wrong-row purchase.

Wiki impact: progression, getting started, interface, Features, home, In development
and Recent changes receive local **Not released** notices. All maintained articles
and 432 generated hunt routes were assessed; no commands, stats, rewards, recipes
or generated catalog values change. Public wiki publication remains pending.
