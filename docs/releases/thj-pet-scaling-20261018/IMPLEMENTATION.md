# Implementation and handoff

This is an **undeployed candidate** on `feature/thj-pet-scaling`, base `a8e0a91`.
No production rows, running processes, protected client files, signed releases
or published wiki files were changed. Native-client gameplay and combined-build
balance acceptance remain pending. The catalog names the requested Shaman AA
**Rabid Bear**, rather than “Rabid Pair.” Research is retained in the originating
chat's `outputs/nightcap-minion-master-audit-and-plan.txt` and WPM source audit.

## Implemented behavior

| Area | Candidate behavior | Boundary |
|---|---|---|
| Persistent equipment | 22 selectable worn locations; 15 stored items for Mage pets, 8 for other permanent class pets; pages of 8/8/6 | Budget applies to persistent loadouts. Native temporary gear remains separate; ammo is excluded. |
| Item preservation | Original eight slot IDs stay stable. Full instances, augments, binding, colors, ornaments, charges and custom data move transactionally. Capacity and hand conflicts are checked under row locks | Lost commit acknowledgements still quarantine/disconnect instead of saving stale inventory. New slots require the schema migration. |
| Hands | Persistent two-handed equipment excludes secondary. Conflicting temporary native gear is suppressed, retained in the existing in-memory backup and restored on removal | Summoned weapon/jewelry hand-ins remain possible where they cannot overwrite managed equipment. Their native temporary lifetime remains. |
| Procs | Permanent pets pass actual hand instances into native execution; innate and all six augment sockets get independent attempts | Native level/target/hand chance rules remain. Hostile NPC proc policy stays unchanged. |
| Shared output | Player base item SD/HA caps become 750; earned Hunt headroom remains. Pet contribution is own item SD/HA plus `min(max(owner effective item stat,0)/2,375)` | Live inheritance applies once and excludes charms, familiars and temporary/target-locked pets. NPCs also read their own equipped SD/HA instead of returning zero. Weapon damage/delay remain unchanged. |
| Caster AAs | Half the eligible owner's item/spell/AA caster crit bonuses; full strongest eligible earned AA damage/heal focus; earned Twinheal for beneficial instant pet heals/procs | No ordinary melee-crit inheritance, owner item-focus copying or owner charged-buff focus copying. Twinheal excludes DoTs/HoTs/DD. |
| Runes | Players and eligible pets apply Healing Amount through Nightcap's existing percentage helper, after instrument scaling | Native replacement/refresh, not additive runes. This is Nightcap calibration, not a recovered THJ formula. |
| Pet targeting | Ordinary direct heals can target the caster's own permanent pet. Group/raid beneficial delivery covers eligible class-pet rosters | Native ownership, permission, affinity, no-pets, range and stacking restrictions remain. Instant direct heals stay on the selected pet. |
| Pet buffs | Mage, Necromancer and Beastlord support lines coexist through effect-slot relocation | Magnitudes and effects are conserved; native haste chooses the strongest rather than adding all three. |
| Rabid Bear | Eight roots and illusion 30709 use native permanent duration. Illusion is named `Illusion: Rabid Bear`; both effects are independently removable | Existing cast-time trigger, purchases, cooldowns and normal death behavior remain. Independent dismissal survives restore; visible verification is pending. |
| Doppelgangers | Marked Enchanter clones select the owner's memorized, scribed, level-eligible single-target combat spells; coordinate healing, buffs, debuffs and stackable DoTs | Owner mana/reagents and native completion are used. Missing, dead, changed or charmed owners invalidate clones. Summons, charm, transport, recursive triggers, Bard songs, AoE/group and utility casting are excluded. Native melee/pathing remains; THJ circular formation is not implemented. |

The WPM contract is shared percentage output and rune/proc behavior, legal AA
depth, and the same fragment effects. This patch does not establish THJ DPS
parity or replace pet-template melee damage/delay with weapon ratios.

## Earned progression and content

AA policy grows from 1,051 ranks / 394 families to 1,119 / 400. Curated caps include
Elemental Alacrity 7, Warder Alacrity 8, Frenzied Burnout 6, Host of the Elements 6,
Servant of Ro 6, Army of the Dead 6, Companion's Fury 4, Destructive Fury 6,
Malosinete 2, Twinheal 1, Cascade of Decay 1 and Combat Stability/Agility 18.
Bloodlust rank 1 has 60-second base reuse; Frenzied Burnout has 600-second base
reuse. Only the two documented Alaran-culture prerequisite edges are waived.
Ownership, points, charges, other prerequisites and saved deadlines remain.

`tools/pet_content.py` generates eight Healing/Runic Fragments of Truth and eight
self-target proc spells, IDs 42830–42837. Four-quality base heals are
95/175/250/350; runes are 55/118/168/230 with a 60-second native duration before
ordinary duration policy. These are **Nightcap calibration values**. Augments
fit type 4/8 weapon sockets, permit pets and have zero merchant value. Seru's
existing populated loot table receives one random fragment, with paired quality
weights 30/30, 15/15, 4/4, 1/1. Existing loot stays intact.

Thirty-three existing definitions receive only reviewed SD/HA/haste floors or a
second combat socket. Weapon families: Hammer of Holy Vengeance, Kelp Hilted Mace,
Shinai of the Ancients and Palladius' Axe of Slaughter. Existing stronger stats,
cosmetic sockets, damage and delay remain. Guide floors are not full THJ item
conversion. Palladius' guide SD/HA target is zero; stronger native stats remain.

`content/progression/` stages expansion 4 / level cap 65 and 389 append-only class
merchant entries for 311 distinct native-vendor scrolls/tomes at original class
levels 51–65, from vendors available through PoP. All 1,747 existing stock rows
are guarded and preserved; no merchant exceeds 500 slots. Hub faction/status/
pricing retains its existing contract. **No levels, spellbooks, AAs, points or
epics are granted.** Manifest Elements retains Mage level 59. Root `era.json`
remains Classic/50 until activation.

## Verification

- `evidence/regression.json` and `.log`: 76 tests pass, no skips. Actual native
  methods, complete-instance transfers, quarantine guards, 22-location snapshots,
  hand restoration, proc attempts, live getters, focus eligibility, rune math,
  roster targeting, native buff stacking, clone resource completion, paired spell
  data and real MariaDB temporary-table rehearsals are covered.
- `evidence/aa-native.json`: 6,714 eligibility, nine projection and three saved-rank
  preservation cases pass. The harness matches the already-deployed AA refresh
  sequence; no redundant clear packet was added to gameplay code.
- Native heal targeting: 99 cases pass using the production function.
- PoP activation runs twice and restocks without duplicates. A late occupied
  destination rolls back prior inserts and all three era/level rule changes.
- Fragment activation/rollback are idempotent. Rollback stops acquisition while
  retaining definitions for already-owned fragments and socketed gear.
- Paired world/zone build and library checks: `evidence/native-build-manifest.json`.
  Build scripts operate in a fingerprinted isolated retained-source tree.
- x86 proxy 0.11.0 builds with required DirectInput exports. Generated launcher
  catalog/runtime contract agree on 107 guarded patch sites. `client-stage.json`
  records the unsigned, uninstalled four-file delta. `stage_client.py` reads the
  protected reference and writes only to a new staging directory.
- Five affected x86 patch/UI/pet executables pass, including 21 patch-write/failure
  cases. The standalone fixture runner requires the repository's explicit
  `asInvoker` manifest to avoid Windows installer-name detection.
- `wiki-review.json` records all 21 guide decisions and 432 generated reward
  routes. Thirteen guides have candidate notices; live values remain. No publication.
  All 30 Linux tests and eight Node test entries pass. Windows sandbox/POSIX
  fixture failures were rerun successfully in the isolated Linux test directory.

The native compiler caught and resolved clone reagent-focus access and an empty
equipment aggregate initializer. A compiler warning also identified an invalid
material comparison; the new regression rejects appearance packets for jewelry.
Review caught summoned hand-in compatibility, current merchant identities and
client Inventory XML pairing. These checks do not establish visible gameplay or
balance acceptance. Author review is not independent review or release approval.

## Activation and recovery

1. Obtain independent source review. Recheck current main, production source,
   catalog, item-ID namespace, Seru spawn binding, rule preimages and signed client
   manifest. October18 captures are dated inputs, not future preflight evidence.
2. Validate three pet variants, all six class orders, WPM and a caster control
   in an isolated native client/server environment. Measure DPS, healing, rune
   absorption and survival at fixed gear/AA/encounter settings. Exercise death,
   zoning, camping, resummoning, class release, inactive gear recovery, suspension,
   invalid targets, clone interruption and reagent exhaustion. Independently
   click off both Rabid effects before/after zoning and confirm normal death.
3. Package matching world/zone, AA policy, pet schema, shared-cap rules, guarded
   Rabid/support/fragment SQL, regenerated item/spell caches and signed client
   proxy/UI/spells. Use the established maintenance operator and stopped
   preservation backup. New rules require matching world and zone. Never use
   the older local zone-kill recipe on OVH: child exit can restart the runtime.
4. Activate PoP only after travel, encounter, content and archive checks. Apply
   `content/progression/forward.sql` and promote its `era.json`,
   `catalog-policy.json` and `vendor_restock.sql` with a compatible era operator.
   Current root era/restock tools intentionally reject >50; do not run them
   against this staged profile. Changing rules alone does not prove world access.
5. Verify runtime/client/cache hashes, inventory/loadout counts, earned AA state,
   saved deadlines, merchant stock and services. Publish matching wiki guidance
   only after the corresponding release status is verified.

Recovery preserves earned state. Rabid/support data have guarded reverse SQL.
Fragment rollback **stops acquisition only** and retains IDs, sockets and gear
definitions. Never remove sockets containing player property, restore old player
snapshots, de-level characters or erase newly earned AAs. An eight-slot binary is
incompatible until newly supported equipment has been reclaimed. Prefer a
compatible forward fix or disable an affected action while retaining saved data.

## Remaining acceptance and deliberate limits

Independent review, native client/combat/lifecycle QA, full signed-manifest
reconciliation, a compatible guarded era activation operator and deployment are
pending. Exact THJ rune/fragment magnitudes, template-melee replacement and clone
formation were not established; calibration/native behavior is explicit. PoP is
a staged rules/stock profile, not acceptance of every later encounter or quest.
