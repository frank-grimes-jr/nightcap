# Zone augment audit — November 6, 2026

Source-only dev/test integration is tracked separately in `integration.json`.
It supersedes the October29 static-combat candidate, preserves the existing
capacity candidate and previews, and matches all native/quest sources of the
linked main-based candidate. It grants no capacity or production activation.

**Candidate only. No production content writes, deployment, public wiki publication
or owner gameplay acceptance.** Source starts at `origin/main` `1b443b5a` in
`feature/augment-audit-20261106`. The default workspace is older and untouched.

The [complete 58-family top-quality list](AUGMENTS.md) names every zone, including
disabled pools. Ascension is the actual top-quality name; the request called it
Ascended. [Icon contact sheet](icon-review.png) begins with the old necklace and
cloth gloves, followed by all 24 selected stock gems/orbs/crystals.

## Audit findings and decisions

- Fresh, read-only production capture: 56 installed Classic zone rows, 48 enabled,
  eight disabled; 224 Classic augment definitions plus eight expedition augment
  definitions. All 232 use icons 517 (cloth gloves, 224) or 500 (necklace, eight).
- All 56 Classic configurations are already 150/50 (augment 1.5%, equipment 0.5%).
  The November 2 release changed chances without broadening eligibility. Its
  6,056-entry NPC/spawn allowlist admits **zero** of 585 guard spawn/NPC pairs
  across the configured zones (537 pairs in currently enabled pools). These counts
  describe names containing `guard`, not a claim that all are killable encounters.
- Native gates also exclude lower-level enemies, named/quest/service NPCs and
  most scripted actors. Kithicor requires nighttime undead. High Keep's
  prison-break cleanup removes a Hunt roll awarded before `PrepareLoot`.
- Managed Hate 186 currently inherits augment 940560 (Spiteglass) from zone 76,
  leaving its own Blackspire family dormant. The candidate reads actual-zone
  augment configuration and independently retains the inherited gear family,
  source list, minimum/night gates **and gear chance**.
- The candidate enables only Cazic-Thule 48 and Hate B 186: current retained
  release evidence establishes their Classic content/layout access. Do not add
  wearable sources. Highpass, Splitpaw, Jaggedpine, Nedaria and both tutorial
  pools stay disabled pending their own access/content review. No city pool is
  created. There are 50 candidate Classic pools plus two managed expeditions.
- No augment currently supplies avoidance, accuracy, Shielding, Spell Shielding,
  dodge, shield block, spell haste, mana preservation or Faerune. Existing direct
  damage/healing and heroics are preserved as floors. New specialties are explicit
  in `config/augment-specialties.json`, with full generated preimages/afterimages.

## Rates and balance

Keep 1.5% for Classic; raise Chapterhouse and Ashen Compact from 0.5% to 1.5%.
Quality remains 60/30/8/2. Per death: Base 0.9%, Polished 0.45%, Exalted 0.12%,
Ascension 0.03%. Mean one augment/66.7 kills, direct Ascension/3,333 kills;
95.1% chance of at least one augment by 200 eligible kills. No guarantee/pity timer.
Forging still costs 3/4/4 copies. The former ~940-kill forged-Ascension figure is
a long-run Base-equivalent yield estimate, **not** an exact first-completion time:
quality/carry leftovers and player trade affect actual pacing.

Any unowned, killable NPC in an enabled zone receives the augment roll: guards,
named/quest NPCs, killable merchants and unowned scripted combat adds. No spawn,
name, level, faction, merchant/class, allowlist or day/night gate. Equipped augments
retain their required levels. Owned/charmed pets captured before charm fade,
mercenaries/swarm pets, restored corpses and protected/noncombat body types remain
excluded. Native corpse ownership/player-kill rules still apply. Killable merchants
may leave corpses only where the native eligibility helper sees a reward pool;
city merchant policy remains unchanged. This is deliberately broader than the
unreleased October 29 regular-static-combat candidate.

Expedition static enemies retain deterministic per-run/spawn/life rolls; unowned
dynamic enemies roll through the zone RNG and per-life marker. Static miniboss
relic rolls remain 35% and keep their old template/spawn restrictions: dynamic
adds do not become miniboss relic farms. Corpse results retain native dungeon
receipt/staging behavior. High Keep's native augment roll now follows scripted
loot cleanup.

| Specialty | Families | Base / Polished / Exalted / Ascension | Six-socket constraint |
|---|---:|---|---|
| Avoidance | 5 | 1 / 2 / 3 / 4 | at most +24; active item cap 100 |
| Shield block | 3 | 0 / 1 / 1 / 2 percentage points | strongest Hunt only, max +2; usable shield required |
| Spell Damage | 7 | 1 / 2 / 4 / 8, retaining existing higher values | max +48 raw; active cap 750 plus existing headroom |
| Healing Amount | 6 | same | max +48 raw; active cap 750 plus existing headroom |
| Spell haste | 5 | none / Minor III / Minor III / III | strongest qualifying focus; 7% / 15% |
| Mana preservation | 8 | none / Minor III / Minor III / III | strongest qualifying focus; 1–5% / 1–10% |
| Faerune | 4 | none / none / none / Faerune | utility; no stacking multiplier |
| Dodge | 6 | none / none / Improved Dodge I / same | strongest worn dodge effect, +10% modifier, not +10 percentage points |
| Shielding | 5 | 0 / 0 / 1 / 1 | max +6%; active item cap 35 |
| Accuracy | 6 | 2 / 3 / 4 / 5 | max +30 |
| Spell Shielding | 3 | 0 / 1 / 1 / 2 | max +12%; active item cap 35 |

Existing spell IDs 4303/2341, 4306/2344, 3660 and 3889 are captured and checked;
correct Focus type 6 / Worn type 2 are used. Stock spell eligibility/stacking still
applies (including level-60 focus limit and haste's three-second minimum cast).
No new spells, ItemData ABI, AA, cap/rule or primary budget changes. The additive
worn rule must remain 0; migration rejects a different value. Shield block is
implemented natively because production has no suitable modest ShieldBlock worn
spell; Shielding is not misrepresented as shield block. Item lore exposes the
native shield-block amount without adding a LORE ownership restriction.

These budgets limit new power alongside six heroics, multiclass AAs, gear and
sustain; they are not encounter/solo balance acceptance. In particular, respawning
quest adds can accelerate acquisition and need the specific gameplay spike below.

## Icon audit

RoF2's `A_DragItem` uses a **vertical**, 40×40, six-by-six grid. `GetIcon` subtracts
500; exact client disassembly at RVAs 2655da/265af8 and `SetCurCell` 47a860 confirms
the mapping. IDs 944–967 are columns 2–5 of `dragitem13.dds`, all gems/orbs/crystals.
Every quality of one family shares an icon; icons repeat across families. The
review is of every selected cell, not an inference from an ID range. Protected
client assets were read only. [Hashes/evidence](icon-evidence.json).

## Verification and source authority

`tools/tests/test_zone_hunt_native.py` compiles actual Load/Award/eligibility/cap
bodies with warning-as-error fixtures. The exhaustive 10,000-value roll control
requires exactly 150 successes. The new broad-NPC regression first failed against
the unchanged implementation, then passed. Actual Load tests cover empty sources,
failed/ambiguous configuration, missing items and independent Hate augment/gear
rates. `test_augment_audit.py` checks every identity/quality, budgets, stock spell
typing, exact SQL and actual shield inventory scanning; six copies cannot exceed
the strongest +2. `test_augment_expedition_native.py` compiles both actual
expedition blocks and checks boundaries, static/dynamic once-per-life markers,
35% static relic gates and all 10,000 chance values.

[MariaDB rehearsal](mariadb-rehearsal.json) uses a new local-only schema with the
actual captured item/spell/config schemas. It verifies all 232 complete
afterimages, exact inverse checksums, replay rejection, last-row drift rollback,
zone-config drift rollback, incompatible worn-rule and disabled feature-state rejection. It does not
write PEQ or player rows. Re-run after any generated SQL change.

The native compile tool authenticates the six affected retained source files
against current main plus one explicitly inspected already-live Hate spawn-source
join correction. It preserves that correction in the selective repository mirror.
It compiles four changed translation units with retained CMake flags and PCH
header in a separate local directory. The isolated link authenticates 144 retained
objects/libraries and first reproduces both the unstripped and exact strip-debug
shipping baseline byte-for-byte. Candidate stripped zone is
`bc88a4688d722c89f882ddb3328cf0d26867781fea49199ef681abe4f6c51892`;
runtime-byte identity across stripping passes. This is not a deployed release. Current live
baseline is November 4 Power Source training display, not the old October source.
See [native compile](native-compile.json) and [native link](native-link.json);
no current production binary probe or activation is claimed.

Installed Nightcap items/wiki/operations references and 18 reviewed source/test/
evidence fingerprints were refreshed for source commit `e13a307d`. The dedicated
`augment-audit` context check reports every fingerprint unchanged; the skill
validator passes. Exact installed patch and readback hashes are retained under
`skill-update/`. Build tooling pins its original patch base, so committing the
feature cannot silently change the source it validates against.

Focused regression evidence: 12 Hunt tests, eight new audit/expedition tests,
five Chapterhouse tests and 22 wiki/content-refresh/preview checks pass. The old
Ashen fixture still expected Keeper Hate zone76 although the unchanged current
policy routes186; that obsolete expectation is corrected. Sandbox Perl launch
failed with Windows DLL relocation and its local-fixture rerun uses the working
host launcher. The separate historical `test_warhelm_client` archive-validation
fixture cannot run here: its prior candidate archive directory is absent. No
client assets change in this task; selected icons are directly extracted and
visually reviewed from the pinned protected client. No old client acceptance is
promoted into current QA.

The [whole-wiki impact review](wiki-review.json) covers all 41 authored articles
and every affected generated item/zone page. Published catalog values stay intact;
unreleased notices and a public-only 58-family preview describe this candidate.
Run `wiki/check_refresh.py --repo <this checkout> --ref HEAD --include-worktree`.
Historical unrelated ledger drift remains review-required; do not blanket-advance
it. No local preview is a publication receipt.

## Activation and recovery boundary

The repository's normal feature → dev → test → owner QA → main gate applies.
This audit grants no production deployment or public publication authority.

1. Build/link the candidate against the actual current retained release, preserving
   all current XP training/metadata, Hate density, faction, SSF and loot fixes.
   Pair compatible world/zone/shared_memory consumers and current quests/client.
2. Fresh read-only preflight must match all item/spell/config preimages, rule
   catalog and current schema; inspect the six remaining disabled pools explicitly.
   Reject drift rather than recapturing/blessing changes automatically.
3. Supported whole-runtime stop, fresh stopped backup, guarded `forward.sql`,
   regenerate the matching shared item cache and install the compatible zone.
   Quest/rule reload alone cannot activate native changes or cached definitions.
   No client asset update is required for stock icons/effects; fully relog for
   fresh item definitions and inspect real loot.
4. Verify exactly 232 changed definitions, exactly two enable flags, no other
   content/player changes, actual-zone Hate augment, independent gear rates,
   current live rule/cap values and all worker/native/cache identities. Verify
   fresh guards and preexisting saved spawns; existing corpses never reroll.
5. Only after authorized deployment, replace preview labels/catalog values and
   publish/verify the public wiki through its current guarded publisher.

`rollback.sql` is a full-preimage inverse for these item definitions and the two
enable flags. It retains all definitions, earned inventories and receipts. It is
not a player-state restore and must never be replayed after uncertain activity.
Use a compatible forward repair after player activity if any full afterimage
drifts. The prior native image ignores the new specialties/lore shield effect;
any native rollback must still be Power Source metadata-aware. Never use old
pre-XP binaries, kill one OVH zone, or restore inventories from an old snapshot.

## Exact in-game QA spike

1. In public High Keep, kill native goblins and killable guards; in Qeynos Hills
   kill a low-level non-allowlisted animal and a named/quest enemy. Each receives
   the same 1.5% augment chance; equipment keeps its old restrictions. Random
   absence is not proof of exclusion. Use a controlled QA-only forced RNG to
   prove single-corpse delivery, then a separately labeled normal-rate sample.
2. Run Osargen's managed High Keep rescue and kill scripted prison-break guards.
   Check the augment survives cleanup and the existing rescue/alarm/wave rewards
   and zero unintended coin/gear behavior remain. Check an unowned encounter add.
3. Kill a lootable merchant in an enabled QA zone. A client/player-owned pet kill
   can award the augment and leave a normal owned corpse. City merchants and
   protected services remain unchanged. Kill a charmed pet after charm fade and
   a merc/swarm pet: no augment. Keep access/service NPC safety intact.
4. In Kithicor, test daytime ordinary enemies and nighttime undead. In Classic
   public/private Cazic-Thule test guards/named. In new managed Hate B verify
   Blackspire Prism, while old Hate runs give Spiteglass. Wearable families remain
   inherited appropriately. Six excluded/access-check pools still cannot drop.
5. In Chapterhouse and Ashen Compact, test ordinary, named and unowned dynamic
   enemies at 1.5%; verify static-only 35% miniboss relic eligibility is unchanged.
   Suspend/reboot a saved live NPC and restore an existing corpse: original corpse
   loot persists exactly once. Exercise native failed death-staging recovery.
6. Socket the three shield-block families in each of the six allowed armor slots.
   One/six top copies give +2 Hunt block total, not +12. Remove the shield, use an
   ineligible/under-level shield or move armor into training slot21: no benefit.
   Pair with Paladin grip block, legal AAs and buffs; verify caps/eligibility and
   front/rear, strikethrough and ordinary shield-block behavior.
7. Compare six avoidance/mitigation/accuracy/damage/heal copies against mixed
   builds. Test level1/20/40/50 progression and strongest legal level50 multiclass
   gear/AAs/pets; measure kill time, incoming damage and mana sustain. No claim of
   encounter acceptance from isolated arithmetic alone.
8. Test duplicate dodge/focus items against stronger gear/AAs/buffs, stock spell
   limits (short casts/Bard/excluded spells/level limits), Faerune breathing,
   vision and invisibility. Check primary stats and item-XP training remain.
9. Inspect Understone Heart in The Hole and both expedition augments in inventory,
   corpse, advanced loot and item links. All qualities use their reviewed exotic
   icon. Test full bags, loot filters, one-for-one receipt transfer, forging 3/4/4,
   trade, relog and saved corpse recovery; no gloves/armor icons or lost augments.
