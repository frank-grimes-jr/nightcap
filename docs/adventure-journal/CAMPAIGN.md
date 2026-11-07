# Wayfarer's Oath: The Last Lantern

Status: approved direction; implementation in progress, November 7, 2026.
The owner explicitly requested main/server deployment and client notes after
reviewing this campaign. This authorizes this release, not gameplay acceptance.
Implementation plan: [ordered slices](../../tasks/adventure-journal-endgame/plan.md).

The owner requested a
living story through endgame and confirmed useful progression armor with a
coordinated appearance. The implemented candidate now has sixteen native Tasks, eight private memory scenes
and the complete armor/refit system. The original eight-task catalog is preserved
as its path/spell foundation. Release, measured tuning and player acceptance are
tracked separately in release-20261107/. This document does not establish installation.

## The experience

A traveler arrives in Commonlands looking for adventures. By level 50, they have
retraced a lost expedition, brought its surviving members home, confronted the
man who traded their names for his survival, and earned armor that carries their
story. The journal should remember people, consequences and places, rather than
merely list named enemies to kill.

The campaign runs from level 20 through demanding level-50 Classic content.
Three introductory chapters still lead to any of the five level-35 archetype
paths. Finishing the first path earns the existing Epic 0.5 charm and opens the
continuation; collecting all five paths is never required. Primary class does
not select the story. Guardian, Striker, Arcanist, Warden and Binder remain
different ways to answer the same oath, not competing campaigns or factions.

The end reward is the **Last Lantern armor**, eight real equipment pieces across
seven visible regions: head, chest, arms, hands, legs, feet and two wrists.
The player receives pieces throughout the story and reforges their earned set
at later milestones. The final chest completes the silhouette at level 50.
The original charm retains its bounded five-attunement/600-second contract.
Armor does not multiply the click, shorten its cooldown or stack five powers.

## People worth returning to

All new people and the expedition below are original Nightcap fiction, not
claims about EverQuest canon. Existing named enemies retain their identities.

- **The Ancient Chronicler** commissioned the Company of the Last Lantern to
  document dangerous roads. He claims its journals were simply lost. In truth,
  he removed the failed expedition from his record because he sent it beyond
  what it was ready to face. He must eventually read the names aloud himself.
- **Mera Vell, the returning scout**, is introduced alive in the tunnel before
  the first expedition. She has been going back for her companions alone.
  Early she refuses help; later she leaves route notes and fights beside the
  player. Her arrival at the closing campfire depends on completing her rescue.
- **Oren, the company's quartermaster**, repairs old expedition equipment and
  remembers who wore it. He makes the armor personal without handing the player
  a dead person's unaltered belongings. Artisan Veyra supplies the binding work;
  Oren is the campaign's proposed fitting/recovery NPC, not a replacement for
  Veyra's existing services. His public placement needs collision/path QA.
- **Captain Selene Marris** is first known through practical letters: pay the
  porters, return a borrowed cloak, stop the scout from taking the first watch
  twice. Later chapters reveal her last decision to hold a retreat. Her rescue
  is impossible; returning her name and effects to the company is meaningful.
- **The Hollow Witness** was the expedition's recorder. He bargained away his
  companions' names to escape and is now erasing the remaining evidence. The
  player encounters his work and hears his voice before meeting him. The story
  never requires killing an existing god to explain this original antagonist.

## Twelve chapters

Levels below are minimum offer levels, not proof of encounter balance. Exact
new NPC identities, coordinates, maps and activity IDs must be audited before
they enter the executable catalog. Current eight-task IDs stay preserved.

| # | Chapter / minimum level | Play and story | Earned equipment |
|---|---|---|---|
| 1 | **The First Pages** / 20 | Meet Mera and Oren before leaving. Visit Upper Guk, Unrest and Runnyeye; read a short expedition note at each entrance. The three notes describe the same company, but one name has been scratched out of every copy. Return with your own route annotations. | **Roadworn Lantern Boots**; Oren repairs a spare pair for the new traveler. |
| 2 | **Beneath the Surface** / 25 | Defeat the froglok warden and reclusive ghoul magus, retaining the original field objectives. Discover Selene's supply request and follow a guaranteed trail to a trapped expedition porter. A short rescue teaches interruption and controlled pulls. The porter remembers a recorder whom the journal does not name. | **Lanternkeeper's Gloves**; the rescued porter returns to Oren's camp. |
| 3 | **Steel and Sorcery** / 30 | Defeat Battlelord Paluk and the goblin sage. Recover an expedition rubbing from a fixed interactable after the victories; it shows that the company went deeper willingly. Compare the two accounts with Mera instead of merely reporting two kills. | **Wayfarer's Left Bracer**; a blank panel is reserved for a name. |
| 4 | **The Oath You Keep** / 35 | Complete one existing Guardian, Striker, Arcanist, Warden or Binder trial. Each path gets its own preparation and completion dialogue. The Chronicler binds the player's answer into Wayfarer's Oath. Its awakening exposes an erased line: he commissioned the expedition. | Existing **Wayfarer's Oath [Epic 0.5]** charm; no second armor reward or five-path grind. |
| 5 | **A Name Beneath the Moss** / 38 | Follow Mera into Lower Guk. Recover a marked satchel, then escort her through a short prepared retreat while protecting the route from runners. She admits she left Selene behind. The player finds a recording signed by the Hollow Witness. | **Wayfarer's Right Bracer**, completing the pair. |
| 6 | **What the Fire Kept** / 40 | Follow the recorder's dealings through Solusek's Eye into Nagafen's Lair. Defeat two audited lieutenants rather than require Nagafen at level 40. Hold a furnace against a short, telegraphed attack while Oren restores the damaged expedition seal. | **Oathbound Vambraces** and a first refit of earlier pieces to the level-40 band. |
| 7 | **The Captain's Last Watch** / 42 | In a story encounter set in Cazic-Thule, reconstruct Selene's retreat from three fixed records. Defend the last survivor while the player chooses when to fall back through marked positions. The final record shows Selene stayed to save the others; no resurrection undoes that cost. | **Last Watch Leggings**; Oren works Selene's repaired company insignia into a new piece. |
| 8 | **The Debt of the Living** / 45 | Pursue the Witness's agent into The Hole. Recover a stolen roster and escape a collapsing ritual with Mera. Back in Commonlands, confront the Chronicler; he reads the erased names aloud. The scene opens because the player brings the evidence, never because of real-time waiting. | Earned armor fitting service and the company's restored roster in journal history; no invisible filler item. |
| 9 | **Where Courage Ends** / 46 | In a campaign-scoped Plane of Fear encounter, recover the company's standard and break three fear anchors while a pursuer pressures movement. Interrupt windows, line of sight and a readable retreat route matter. No mandatory death touch or existing Cazic-Thule god kill. | **Lanternbearer's Helm** and the second earned-set refit, using the level-46 band. |
| 10 | **The Weight of a Name** / 48 | Follow the Witness into Plane of Hate. Win a checkpointed gauntlet with deliberate pulls, then stop him from consuming three recorded names. Mera challenges the player's answer to their oath; role-specific dialogue changes the scene, not access or power. | **Last Lantern fittings**: a durable campaign milestone unlocking the final refit, not an inventory token to farm. |
| 11 | **A Light Carried Forward** / 50 | Assemble Mera, Oren and the surviving porter in Commonlands. Return a personal effect, choose a memorial inscription and prepare the restored standard. Speak to each companion; each recalls an earlier action. The player chooses to carry the dead forward rather than promise to bring them back. | Final expedition unlocked; no armor purchase, rare-drop toll or new charm power. |
| 12 | **The Last Lantern** / 50 | Enter the campaign's private final expedition, staged in an audited section of Hate. Break the Witness's bindings, protect the standard and defeat him in a three-phase encounter. Return to the campfire: the Chronicler records the player's name beside the company, not above it. | **Cuirass of the Last Lantern** (or robe/tunic equivalent), final refit of all seven earlier pieces, and proposed **Lanternbearer** title. The complete eight-piece set is earned. |

The three opening chapters and five alternative path trials make the existing
eight quests. The expansion adds eight shared chapters after the first earned
path, for **16 quest definitions and 12 chapters on one playthrough**. Additional
paths remain optional earned attunements and cannot replay armor claims.

## Scenes and voice

Use concise hail/saylink dialogue with optional longer accounts. Objectives
remain clear without reading every line. Preparation notes give route, expected
pressure, escape advice and a reminder of who the player is helping.

**First meeting, Mera:**

> If he asks you to bring back a story, bring back the people in it first.

**First boots, Oren:**

> Those soles were cut for somebody who never collected them. I've taken them
> apart and made them yours. Try to wear them out on the way home.

**The restored roster, Chronicler:**

> I thought an empty page was kinder than a list of the dead. It was only
> kinder to me. Stay. I will read every name.

**Before the final expedition, Mera:**

> Last time, we followed a man who promised we would all come home. You haven't
> promised me that. You've just kept coming back.

**The Hollow Witness:**

> They were already lost. I gave up the names so there would be one of us left
> to remember. Do you know how quiet it becomes when that stops hurting?

**Closing campfire, Oren:**

> No, leave that mark in the plate. I can mend a dent. I can't make you earn it
> twice.

Memorial wording is a flavor choice with identical rewards. There is no hidden
"correct" moral answer. Role callbacks acknowledge prior trials without requiring
specific spells, a primary class, a pet build or five separate completions.

## Armor that belongs to the journey

### Fit and appearance

Offer cloth/robe, leather, chain and plate fits using audited native item
materials and standard eligibility from held classes. Every supported primary
class must have an equippable complete route. All paths may choose any fit they
can legally wear; a Guardian is not required to wear plate, nor a Binder cloth.
Show the eligible choices before claiming. No global class-mask widening.

The family shares a charcoal/midnight-blue base, muted brass trim and a pale
company accent where the native material supports it. Early gear is visibly
plain. Refit pieces acquire the coordinated finished palette and stronger
materials. A robe and a cuirass share identity, not identical geometry.

The deliverable is worn equipment visible to the wearer and other players.
An icon, inventory render, Blender preview or armor name is not acceptance.
Stock Classic materials/tints are the initial asset strategy; custom embroidery,
emblems, glowing trim and new meshes are not promised by item metadata.
Native feasibility comes before promising a precise per-race color placement.
The published Classic robe waist repair must remain intact. If new archives or
selector work is needed, use staged assets and signed paired client delivery.
Never edit Client_RoF2_Dev or substitute Luclin models.

Two bracers count as two actual pieces but only one wrist material region.
Do not advertise eight independent visible regions. The helmet is a normal
coordinated option; existing Camil/Ashen Compact special helmets keep their
separate prestige and gameplay value. The player can choose to wear better loot.

### Power and refits

- Give each piece useful stats at its award level. At 40, 46 and final completion,
  permit the player to exchange each earlier piece for its earned current grade.
  Old pieces must not leave the last outfit with level-20 stats at level 50.
- Use four balanced equipment fits with different stat distributions, not 20
  combinations of five paths times four materials. The charm owns role powers.
  No passive set bonus, extra activated powers, heroic-stat budget or pet-count
  scaling in this first expansion.
- Set numeric budgets from actual reviewed dungeon-band and ordinary-tier
  catalogs. Early pieces sit in the useful Normal progression band. Finished
  pieces form a dependable level-50 set below the best same-slot difficult Raid,
  planar and earned class rewards. Compare the complete set including six
  eligible augment slots, held classes, legal AAs, buffs and pets. Do not assign
  arbitrary "endgame" stats before this comparison.
- Fixed campaign grades only: no random Polished/Exalted/Ascended rolls,
  matching-copy reforging, merchant resale, Bazaar sale or free pet outfitting.
  Inventory remains governed by current native restrictions; LORE alone is not
  an ownership fence because Nightcap disables ordinary LORE restrictions.
- Refit and supported fit changes preserve augments, binding and earned grade.
  Use a native atomic exchange/receipt path; do not hand-in/delete first and
  hope SummonItem succeeds. If that adapter is not available, keep exchanges
  disabled until implemented. Never silently strip sockets or destroy dyes.
- First claims, refits and recovery are serialized per character and reward
  slot. Completed task history determines entitlement; durable delivery receipts
  prevent repeated awards, socket-item recovery exploits, bank/cursor duplicates
  and reconnect replay. Missing equipment with conflicting records is a support
  case, not permission to manufacture another augmented copy.
- Claim/recovery checks include inventory, cursor, bank and other supported
  custody locations. Refuse uncertain storage or database state. A failed
  delivery remains claimable; an acknowledged or uncertain committed delivery
  is reconciled by receipt instead of blindly retried.

The final set is guaranteed progression from completing demanding objectives.
Difficulty belongs in encounters and preparation, not random proof drops,
seven copies of one chest, spawn camping or a requirement to farm all five paths.

## Encounters and persistence

Native Tasks remain the sole objective/completion authority. Campaign state may
store dialogue choices, delivery receipts and owned encounter checkpoints, not
parallel copies of kill or chapter-completion flags. Accept tasks before earning
credit; existing victories are not retroactively imported. Group/pet credit must
use the native legal attribution and personal eligibility of every participant.

Early audited named objectives retain their current behavior. New rescue,
defense and story scenes use explicitly owned private encounters; do not attach
public rescue actors to every player or make one player's scene change a shared
NPC for others. Fixed record interactables are individually gated. Reusing a
zone is not authorization to mutate an existing Keeper run, boss checklist,
reward table or public population.

New encounter integration must audit the current managed-instance lifecycle,
credit, receipts and corpses. Prefer a separate campaign contract with isolated
checkpoints. It may use reviewed Keeper infrastructure but cannot advance a
Raid/Grind completion, mint its rewards or let reset replay campaign deliveries.
Existing eight quests retain their exact IDs and earned history; new IDs are
unassigned until collision checks and an additive migration are reviewed.

Rescues have short routes and reset only their encounter on failure. An earlier
chapter and its rewards never reset. Connected eligible helpers may join under
normal instance/credit rules; SSF is supported solo without player assistance.
Do not balance by primary-class counters or demand a particular spell/AA.

Proposed finale phases:

1. **The borrowed names:** expose three bindings using readable interrupt and
   positioning windows. Each binding restores a recorded companion voice.
2. **The broken company:** protect the standard through a bounded add sequence;
   telegraphed unsafe ground forces movement without unavoidable class checks.
3. **The witness remains:** a direct fight with a manageable pressure cycle.
   Earlier objectives change the dialogue and available safe positions, never
   permit an unearned instant kill or endlessly multiplying pet exploit.

Tuned add counts, damage, HP, cast timings and reset boundaries follow measured
fresh/developed level-50 runs. Excessive HP, uninterruptible unavoidable deaths,
permanent loss of quest progress and a pet-required action are excluded.
Ordinary difficulty must be demanding for prepared solo builds. Optional later
challenge modes may add prestige; the complete advertised set is earned through
this campaign's ordinary finale.

## Implementation order and proof

This is a reviewable specification, not a completed implementation plan. After
design approval, split implementation into independently verifiable slices:

1. **Audit and reserve:** capture current content, item bands, native materials,
   map routes, SSF restrictions, task hooks and durable inventory adapters.
   Reserve collision-free task/item/NPC/spell IDs; preserve the existing catalog.
2. **First visible slice:** chapter 1, Oren, boots, durable first claim/recovery,
   personal notes and one closing scene. Verify a normal-account native task,
   worn appearance, inventory failure and reconnect before copying the pattern.
3. **Oath act:** chapters 2-4, first pieces and all five existing trial stories;
   retain the shared cooldown and earned attunement checks.
4. **Company act:** chapters 5-8, private rescue/defense scenes, intermediate
   equipment and atomic level-40 refits. Verify instance isolation and rollback.
5. **Planar act:** chapters 9-12, checkpoints, three-phase finale, completion
   receipts, final outfit and title. Measure each supported representative build.
6. **Release candidate:** matching native/content/cache/client package where
   needed; staged and reviewed wiki, full native/manual QA, dev -> test. Main
   and production follow the owner's normal sign-off boundary.

Existing implementation locations: `tools/epic05.py`, `tools/epic05_capture.py`,
`server-mods/plugins/epic05*.pl`, `server-mods/quests/ecommons/The_Ancient_Chronicler.pl`,
`server-mods/quests/global/items/900501.pl`, native `Epic05Contract()` and
`docs/adventure-journal/{catalog.json,SPEC.md,QA.md,RELEASE.md}`. Add new campaign
tests under `tools/tests/`; do not weaken the old eight-task validator to accept
unreviewed data. Extend the versioned contract deliberately after data design.

Existing baseline commands, from the selected checkout:

```powershell
$env:PYTHONPATH='tools'
python -B -m unittest discover -s tools/tests -p 'test_epic05*.py' -v
perl tools/tests/epic05_quests.t .
perl tools/tests/epic05_store.t .
python -B wiki/check_refresh.py --repo . --ref HEAD --include-worktree
```

The generator writes candidate outputs; database rehearsal uses a disposable
schema and the existing release guide. Neither is a production installation
command. No build or gameplay test result for the expansion is claimed here.

## Acceptance and review boundaries

- One normal character can finish 12 chapters from level 20 to level 50 with
  one chosen path, eight correctly fitted armor pieces and the original charm.
- All five paths receive meaningful callbacks. Completion never requires another
  primary class, all paths, player trade or grouping; SSF retains its restrictions.
- The player meets companions before being asked to care about their losses;
  each returns in later dialogue, and the campfire acknowledges the rescues.
- Every armor slot is useful at its award level and has its final earned grade
  at completion. Both wrists exist. All seven material regions are visible on
  supported Classic race/gender combinations, with robe, animation, dye,
  equip/remove, zoning, observer and relog checks recorded separately.
- Compare fresh/developed level 35-40 and 50 melee, caster, hybrid/sustain and
  one-/multi-pet builds; record legal AA pool, actual spent points, equipment,
  augments, active formulas, death/failure counts and encounter/route time.
- Native regressions cover prerequisites, out-of-order objectives, disconnect,
  failed claims, parallel clicks, custody/augment reconciliation, fit exchanges,
  reset/expiry, task abandonment/history and partial migration/disable.
- Durable disable preserves task history, rewards, item definitions, receipts
  and player inventories. No player snapshot rollback, global zone changes,
  broad buff-duration exemption or era.json changes.
- Source, automated evidence, native appearance, balance acceptance, deployment
  and public wiki publication remain separate statuses. A reviewed proposal is
  not built content; built content is not installed or player-accepted.

Review needed before implementation: chapter/story direction and guaranteed
eight-piece reward structure. Content audit then resolves exact new identities,
placements, legal fit masks, material/tint feasibility and numeric item/encounter
budgets. None of those are claimed verified by this design document.
