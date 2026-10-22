# Substantial class-armor rewards — October 22 release

**Deployed with owner approval via main PR285 (`7f97288`) on October 22 at 17:07 UTC. Palwar’s three pieces are corrected. Owner in-game delivery, relog and balance acceptance remain open.**

[Deployment, recovery and verification](deployment/README.md) record the current state; the original candidate capture and tests below remain dated evidence.

## Diagnosis and accepted behavior

A read-only production inspection on October 22 found Palwar wearing Normal
Crafted Vambraces (4176), Crafted Breastplate (4174) and Crafted Plate Boots
(4180). Shakrn and Ulan Meadowgreen's installed Lua scripts explicitly grant
those IDs. This is a missing reward conversion, not a missing item definition
or an item-display error. The October 18 automatic-quest proposal was never
implemented and excluded all repeatable quests.

The owner now explicitly includes substantial class-armor quests even when
repeatable, while excluding cheap/basic hand-ins. This supersedes the blanket
repeatable exclusion. [ADR 0066](../../adr/0066-substantial-class-armor-rewards.md)
and the [explicit catalog](../../items/quest-armor-catalog.json) own the rule.

## Implemented release

Ten quest scripts change exactly 37 terminal reward literals:

| Family | Zone | Quest NPCs | Rewards |
|---|---|---|---:|
| Crafted | South Karana | Shakrn (14075), Ulan (14073) Meadowgreen | 8 |
| Lambent | Temple of Solusek Ro | Cryssia Stardreamer (80012), Walthin Fireweaver (80011) | 7 |
| Darkforge | Temple of Solusek Ro | an undead knight (80000, 80001) | 7 |
| Ivy Etched | Kithicor | Gandari (20085), Leaf Falldim (20066) | 7 |
| Totemic | Lake Rathetear | Vrynn (51059), Kyralynn (51058) | 8 |

An eleventh script preserves the later Shadow Knight epic hand-in: Kurron Ni
accepts any mixture of Normal/Ascended Darkforge Helm, Breastplate and Greaves.
His original platinum>=900 check, actual helper cash-return behavior, faction
and once-per-spawn Letter to Duriek remain. This is not an epic-quality grant or
a new 900pp sink.

Only existing ordinary Ascended definitions are selected. For the ten armor reward scripts, input IDs/counts,
money, success conditions, XP, faction, class access, dialogue, repeatability,
native cursor delivery and rejected-item paths are byte-identical. No global
grant hook, database/stat change, client change or new item definition is added.
Compiled/native delivery is unchanged; fixture tests cannot certify an actual
full player cursor, item inspection or relog. Those remain explicit in-game QA.

The recorded 180 definitions include all four qualities of the 37 rewards and
eight small Crafted counterparts. All 37 target identities and class/slot/level/
socket constraints match their bases. Captured candidate-path probes found no
competing version-zero, ID, name+ID, language or global script for these NPCs.
Kurron Ni is a later-era compatibility correction and does not unlock Overthere.
Only the named version-zero paths are approved; refresh precedence before
activation, including actual configured quest roots and active zone versions.

A fresh full production quest literal scan found the Kurron dependency and the
unchanged sizing scripts. Debbis the Fish is a separate simple alternate grant,
not this earned class-armor quest; it remains Normal. Remaining numeric matches
are spell/task IDs or coordinates. No matching tradeskill-component or task
activity references were found. Dynamic/computed script references are not
proven absent by a literal scan.

No sizing scripts change. The current playable-race policy makes Crafted resizing
unnecessary for class-matching characters. Existing Tonsmith exchanges accept
Normal items only; converting augmented/dyed/bound higher-quality instances with
static SummonItem would require a separate preservation review. Their older
poor-faction no-return behavior is not endorsed or repaired here.

Armor of Ro ends in tradeskill recipes and needs a guarded recipe audit. Temple
cleric quests mix armor, weapons and shields, and Blaize lacks normal rejection
handling; they remain outside this first catalog. Cultural tradeskill armor is a
separate undeployed candidate. This does not mean every crafted or quested item
now qualifies.

## Evidence and checks

- `production-reference.json`: SELECT-only capture, UTC time, script bytes/hashes,
  actual Lua/Perl helpers, target definitions, NPC IDs and precedence candidates.
- `manifest.json`: exact before/after hashes for all eleven candidate files (ten rewards plus epic compatibility).
- `tools/quest_armor.py`: validates family identities and permits only the 37
  reviewed grant substitutions. It rejects input, return or other script drift.
- `tools/tests/quest_armor_rewards.lua` and associated runners: execute quest
  callbacks with the real captured helper code and controlled native boundaries.
- `QA.md`: actual in-game acceptance, not inferred from automated tests.

Production observations establish the cause and target existence. Local runtime
tests establish script behavior. Neither is deployment or balance acceptance.

## Activation and recovery boundary

The owner explicitly authorized main promotion, deployment and Palwar’s offline correction. Activation completed; the following gates also apply to any future reactivation. Re-capture scripts/precedence and verify their exact retained
before hashes; stop on drift. Verify the currently paired item cache contains all
37 existing targets (not merely SQL rows). If cache repair is needed, stop and
plan it with the current runtime pair; never kill a production zone process.

Under the existing deployment/GM locks, retain originals and install only the eleven
verified scripts with original owner/mode and atomic file replacement. Use the
supported global Quest reload and verify all current zones acknowledge it without
quest errors; compare all native process lifetimes and unrelated service states.
No restart was needed; the same constraint applies to future activation. Do not use an old release image or copy the entire local
quest mirror. Publish the matching wiki candidate-to-live wording only with the
authorized release; wiki20261022-quest-armor-v2 is published; its receipts record the preserved concurrent robe release.

Rollback restores only the exact retained eleven preimages and reloads quests after
verifying the installed candidate hashes. Keep all earned armor and player state;
never restore an old inventory/database snapshot. Partial installation or uncertain
reload acknowledgment requires inspecting exact live hashes before any retry.

### Palwar's already earned pieces

The authorized correction committed while world player count was zero and admissions were held: saved slots 7/17/19 changed from 4176/4174/4180 to
604176/604174/604180 respectively. All other fields across Palwar’s complete saved inventory were unchanged. The following describes the guard contract for this correction: Take a fresh full-row preimage and confirm exact
character, slot and item IDs plus offline status immediately before committing.
Change only item_id in one guarded transaction, retaining augments, dye, charges,
binding and every other field. This correction is separate from the quest-script release. Abort if the player moved/replaced a piece or is
online. Never restore this dated inventory observation over later player activity.
Verify the three items in game and after relog; no other owned items are implied.

## Wiki impact

All maintained guides and generated reward routes are reviewed in `wiki-review.json`.
Equipment, Features, home, In development and Recent changes describe the deployed five-family release as Live testing. Tradeskills explains the distinction. Commands,
Hunt/dungeon catalog values and published mechanics remain unchanged. The source ledger records the reviewed current-main baseline and supplemental deployment evidence. `check_refresh.py --include-worktree` reports the reviewed release records until their commit is recorded. Wiki20261022-quest-armor-v2 is published; public verification is recorded in deployment/.

## October 22 integration correction

The ingredient-quality release verified that the mounted configuration loads
root `plugins/`, not the unused `quests/plugins/` copies in this release's helper
capture. Historical Perl fixture results remain reward-delta controls only.
Kurron now declares submitted currency to native `CheckHandin` and refunds it
once on success, preserving the reviewed full-refund policy without weakening
global money checks. Native ordinary-tier matching also accepts Polished and
Exalted Darkforge ingredients. See
[paired integration evidence and QA](../quest-tier-handins-20261022/README.md).
The original source-only eleven-file activation cannot activate that native
policy: the later PR290 deployment installs the paired zone and seven quest/helper files.
The ten existing armor reward scripts are retained. Current evidence is in the
linked ingredient-quality deployment record.
