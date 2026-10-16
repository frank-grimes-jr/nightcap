# Buried Sea AA cutoff and solo-play audit

**October 13, 2026. Recommendation: use Buried Sea as the outer catalog limit,
add a very small utility/control exception list, and apply separate early-level
power caps.** The retained catalog is ample in breadth. A bare expansion cutoff
does **not** establish balanced solo play or solve the beginner list by itself.
No rules, abilities, player purchases, client assets, or running services changed.

## Evidence and what the counts mean

Production PEQ was captured at **09:33:44 UTC / 5:33:44 a.m. EDT**, using one
read-only consistent transaction. The capture contains 1,570 abilities, 6,655
ranks, 9,850 effects, 2,525 prerequisite rows, 40,725 spell definitions and
anonymous purchase aggregates. It contains no character/account identities.
[Snapshot](production-snapshot.json.gz), [capture query/script](capture.py),
[calculation](analyze.py), [summary](summary.json).

The current integrated source reviewed is
`E:/EQ_Local_Dev/_worktrees/multiclass-trainer-access` at `114c730f246d771b5a480c515d9c1da94d3800c5`.
The default checkout hosting this audit is older (`ce161c5` plus existing working
changes); it was not substituted for that source. Fresh content/rule capture is
separate from source inspection and from dated native fight evidence.

Counts below use enabled, ordinary-player, class-eligible families, excluding
grant-only/shroud entries and placeholder ability 0. Shared families count once
per class union. Each retained family is a contiguous first-rank prefix, with
**inherited prerequisites and conservative prerequisite closure**. Missing
prerequisites block the proposed pool, even where native purchase skips an
absent ability. These are **legal catalog counts, not an observed AA-window row
count**, an optimized build, or an activation guarantee. Race/deity masks are
unrestricted in this capture. Prices are summed once per rank; repeatable glyph
spending is not an unlimited amount added to the totals. Zero-price normal
families are included; grant-only rewards are not silently granted.

### Fresh configuration findings

- All **6,655 ranks require level 1**. Early leveling does not reduce this pool.
- Default ruleset: `CurrentExpansion=0` (Classic), level cap 50,
  `UseCurrentExpansionAAOnly=false`, `AAExpMinLevel=1`, passive AA **40%**,
  **4,000 XP/point**, and full expansion bitmask `2097151`.
- Native `CanUseAlternateAdvancementRank` gates class/race/deity/status/era;
  purchase checks level separately. `SendAlternateAdvancementRank` transmits
  expansion **0** to avoid client hiding. There is currently no independent
  Buried Sea AA-era rule in the reviewed path.
- Buried Sea is expansion **13**, and **no captured ranks are tagged 13**.
  On this dataset, cutoffs at Serpent's Spine (12) and Buried Sea (13) are identical.
  Tags reach 21. This is the captured PEQ/RoF2-era catalog, not modern live EQ.
- Do not change `CurrentExpansion` to 13: that also changes content-era policy.
  The proposed AA policy must be distinct from Classic world progression.

## How much remains?

| Held classes | Open families | TBS families | List reduction | TBS ranks | Points for one full purchase pass |
|---|---:|---:|---:|---:|---:|
| WAR / CLR / WIZ | 434 | 178 | 59.0% | 845 | 3,413 |
| WAR / CLR / MNK | 391 | 164 | 58.1% | 828 | 3,249 |
| MAG / NEC / SHM | 423 | 162 | 61.7% | 730 | 2,861 |
| PAL / WAR / MNK | 385 | 162 | 57.9% | 820 | 3,198 |
| SHD / SHM / BRD | 429 | 165 | 61.5% | 829 | 3,224 |
| RNG / DRU / ENC | 429 | 168 | 60.8% | 821 | 3,111 |

Across all 16 class masks, the global catalog falls from **1,458 families / 6,289
ranks** to **440 families / 1,852 ranks**. That global union is not a playable
16-class character. Individual classes retain **92–116 families** and **1,677–2,142
points**. Complete comparisons: [class coverage](class-coverage.csv),
[every family and its TBS cap](families.csv), [every linked rank](ranks.csv).

| Class | Open → TBS families | TBS points | Examples retained at TBS; not all suitable at level 1 |
|---|---:|---:|---|
| Warrior | 193 → 97 | 1,710 | Area Taunt, Shield Specialist, Planar Durability |
| Cleric | 202 → 98 | 1,916 | Healing Adept/Gift, Purify Soul, Divine Resurrection |
| Paladin | 207 → 105 | 2,089 | Divine Stun, Hand of Piety, Purification, Lay on Hands |
| Ranger | 202 → 108 | 2,142 | Archery Mastery, Endless Quiver, Guardian of the Forest |
| Shadow Knight | 228 → 110 | 2,117 | Leech Touch, Soul Abrasion, Touch of the Cursed |
| Druid | 215 → 101 | 1,891 | Enhanced Root, Spirit of the Wood, Convergence of Spirits |
| Monk | 163 → 96 | 1,843 | Critical Mend, Rapid Feign, Purify Body, Master Wu |
| Bard | 181 → 102 | 1,949 | Instrument/Singing Mastery, Fading Memories, Shield of Notes |
| Rogue | 170 → 100 | 1,810 | Escape, Chaotic Stab, Shroud of Stealth, Triple Backstab |
| Shaman | 229 → 101 | 1,868 | Cannibalization, Virulent Paralysis, Spirit Call, Ancestral Aid |
| Necromancer | 237 → 111 | 1,872 | Critical Affliction, Feigned Minion, Blood Magic, corpse tools |
| Wizard | 207 → 105 | 1,864 | Spell Casting Fury Mastery, Harvest of Druzzil, Mind Crash |
| Magician | 233 → 116 | 1,971 | Pet Discipline/Affinity, Elemental Agility/Durability, Reclaim Energy |
| Enchanter | 229 → 108 | 1,793 | Animation Empathy, Gather Mana, Eldritch Rune, Stasis |
| Beastlord | 212 → 105 | 1,981 | Paragon, Bestial Frenzy, warder crit/attack support |
| Berserker | 169 → 92 | 1,677 | Throwing Mastery, Uncanny Resilience, Savage Spirit |

**Sufficiency judgment:** the cutoff leaves a strong solo toolkit and ample
spending choices for representative multiclass builds. There is no catalog-breadth
reason to keep all later AAs. This does not mean every possible class combination
can solo every boss, or that every retained active works at level 50. Resurrection
does not make a dead solo character able to resurrect itself; group effects can
be weak or ineffective when alone. Native target/level restrictions still matter.

The important gap is **later shared pet support**, not a general shortage of
damage AAs. Magician retains earlier class-specific pet defenses, so newer
shared versions must also be checked for stacking. Pure caster and melee builds
retain many strong choices without needing later burst families.

## Why a bare cutoff still permits overpowering content

These are actual retained ranks, not hypothetical later expansions:

| Family / ability ID | TBS maximum | Concern and recommendation |
|---|---:|---|
| Combat Stability 33 / Combat Agility 34 | 18 each | End ranks carry SPA values 45/39. Stability modifies AC softcap; these are not literal 45%/39% damage reduction. Start with ranks 1–3 and stage deeper ranks after measurements. |
| Natural Durability 28 | 3 | Keep staged ranks 1–3; final raw MaxHPChange 1000 is native percent scaling, not 1,000 flat HP. |
| Frenzied Devastation 308 | 3 | Adds spell-critical chance/damage with mana penalty. Defer burst access; mana penalties weaken as healing/mana engines combine. |
| Destructive Fury 397 / 398; Veteran's Wrath 314 / 338 / 339 | 9/6; 6 each | Crit-damage amplification combines with other held classes, gear and spells. Defer deep ranks; validate duplicate-family stacking. |
| Headshot 218 / Anatomy 555 | 7 / 8 | Retained SPA inputs include 60,280 damage with level 70 cap and 65,440 with level 66 cap respectively. Defer Classic execute lines pending actual eligible-target/proc tests. |
| Warlord's Tenacity 300 | 6 | Top retained spell has 5,000 flat HP plus heal/debt effects. Far too large to expose merely because a level 1 player can afford it. Gate and measure. |
| Mortal Coil 697 | 3 | Kill-triggered sustain can create uninterrupted killing chains. Test the proc spell and combined melee/healing sustain before including. |
| Slay Undead 75 | 9 | Preserve class identity with shallow, staged ranks; test undead reward camps rather than only dragons. |
| Cannibalization 47 | 2 | Rank 2 has raw 4,057 HP cost /2,248 mana return. Can be unsafe on low-HP characters and powerful with cross-class healing. Do not advertise as an unconditional starter pick. |
| Mana Burn/Blast/Blaze 565/793/794; Gather Mana 57; Mana Draw 616 | present | Burst/resource magnitudes and long native reuse must be evaluated together. A long reuse timer does not prevent one trivial boss kill. |
| Charged Glyphs 585–589,5000,5002–5004,7016–7019 | present | Cheap repeatable power can become routine at 4,000 XP/AA. Defer combat glyphs from the early Classic offering; review harmless AA sinks separately. |

Deep AA mitigation, caster percentage-based Spell Damage, held-class HP/skills,
multiple pets, tiered gear, heroic stats and hunt augments must be tested together.
The captured item damage/heal caps are 250, but changing them or padding boss HP
would obscure which AA change helped. Keep other levers fixed for the first tests.

## Later-expansion review and exception list

[Later-AA review](later-review.csv) accounts for **all 1,310 families with at least
one post-TBS linked rank**, including disabled/grant-only entries. It contains
**45 named source/content reviews**; the remainder receive conservative inventory
triage, explicitly marked as such. This is not a claim that 1,310 families received
individual combat testing. Among the normal prerequisite-closed open pool,
**1,018 families begin after TBS** and **240 older families gain later ranks**.
Default disposition is to defer later power and later rank increments.

### Small positive shortlist

| Ability | Exact candidate cap | Why include or test |
|---|---|---|
| Eyes Wide Open **938** | rank 8; preserve existing free ranks | Extended-target capacity, with no damage/HP/regen effect. Keep this quality-of-life exception rather than losing it to its Underfoot tag. |
| Diminutive Companion **543** | rank 1, rank ID 12941 | Pet shrink; native MAG/BST eligibility. Verify the intended pet is targeted with Nightcap extra pets. |
| Enchanter Pet Discipline **3202** | rank 1, ID 7733 | Useful pet hold/control. Retain Animation Empathy 195 rank 3 prerequisite. Tactical control is valuable, though not strictly power-neutral. |
| Companion's Durability **3512** | trial ranks 1–3, IDs 6051–6053 | Raw pet HP bonuses 1/3/5%. Suggested trial stages 30/40/50; compare all pets and existing Magician defenses. |
| Companion's Agility **3818** | trial ranks 1–3, IDs 6383–6385 | Avoidance input 5/7/10; test with Durability and held-class pet bonuses. |
| Sturdy Companion **1403** | trial rank 1, ID 9503 | Raw 100 enters owner-derived pet AC. It is **not 100% mitigation**; even rank 1 needs a matched test. |

The first three are the small utility/control proposal. The last three are
**conditional balance experiments**, not automatic backports. Punch Mastery 3511
ranks 1–3 and Companion's Fury 1205 rank 1 are reserve tests only if melee/pet damage
remains materially behind; do not import their full chains.

Gate 1217, Perfected Levitation 1202/1666 and Perfected Invisibility 3812 can be
later progression rewards. Their zero-mana casting, travel access and escape
effects matter even without a DPS increase. Preserve native class masks and
interrupt/target rules. Summon Remains 7002/7007 and resurrection 3711/3800 reduce
recovery friction but do not fill a core solo-combat gap. Keep them in a small
recovery category if eventually added, not the beginner shortlist.

**Do not backport Companion's Relocation 3816 yet.** Captured spell 13500 contains
only the CHA 0 placeholder effect, and a relocation handler was not found in the
reviewed source. A valid-looking description is insufficient. Perfected Undead
Invisibility 291 and its group version 280 depend on Alaran culture 1685→1684;
do not silently bring those era grants along to satisfy a convenience exception.

### Keep later power deferred

- Improved Twincast 515 and hastening 400: first-rank 100% twincast /10 eligible hits
  adds a major multiplier to existing critical and percentage gear scaling.
- Decapitation 133, Thunderfoot 1236, Massive Strike 9300, additional flurry families
 1669/7700 and crit/proc amplifiers: combine all held-class sources before tuning.
- Spire families, Rogue's Fury 3514, Gift of Deathly Resolve 677 and other burn
  buttons: defer by default; stacking/cooldown rotations require exact trials.
- Death Bloom 7703, Hastened Cannibalization 634, Hastened Mana Draw 8347 and
  Hastened Harvest 561: preserve resource decisions; higher-level magnitudes can
  be either lethal at early levels or a nearly free sustain engine.
- Companion's Blessing 3705, Fortify Companion 3707 and Divine Companion Aura 1580:
  not simple pet convenience. Rank 1 Blessing already has raw 1,200 HoT ticks,
  absorb and recourse effects. Test full spell chains and threat behavior.
- Divine Guardian 463, Brace for Impact 1686, Flurry of Life 6488 and other
  defensive/healing rotations: do not balance each cooldown in isolation.
- Cosmetic-looking, unknown-title and later grant entries require verified
  identity/effects. An unknown name alone is not evidence of excessive power.

Exact IDs, spell/effect inputs, first later rank, eligibility, proposed caps,
reasons and review depth are in the CSV and
[named decisions](named-exceptions-and-deferrals.json).

## Make the early list usable

Even 162–178 families are too many for a beginner. Recommend a default **Starter**
view of roughly **8–12 relevant families**, then filters for currently purchasable,
selected class, passive/active, survival, damage, resources, pet control and travel.
Keep owned abilities easy to find. Offer an explicit full eligible catalog view;
do not confuse a search/filter preference with authoritative purchase legality.
Where RoF2 cannot provide those filters, a curated guide or native-client UI work
is a separate implementation task; this audit does not claim stock support.

Starter advice should use held classes and dependencies: shallow Natural
Durability/Combat Agility/Stability; then modest healing/mana, melee or pet-control
choices for that build. Do not recommend caster-only abilities to a melee union
or count a cast that fails native level/target rules as a useful choice.

Suggested trial staging: utility and first basic passive ranks at levels 1–10;
second core ranks at 20; third at 30; selected role abilities/limited pet defenses
at 30/40/50. Exact levels are **design proposals**, not measured thresholds. Deeper
offense/defense and burst unlock by tested content milestone, not point price alone.

The October 9 native neutral-XP curve, rescaled arithmetically to the freshly
captured 4,000 XP/AA setting, gives about **73 /686 /2,439 /16,471 cumulative AA** at
levels 10/20/30/50, before per-award rounding, deaths, quest differences and other
modifiers. This is not an observed leveling timeline. It illustrates why retaining
meaningful early point earning still requires rank/progression limits: price
alone will not protect a roughly 3,000-point TBS pool through the entire era.

## What existing combat evidence establishes

September 12 native experiments used much smaller, curated combat cores and fixed
level 50 gear/controllers. At their actual maximum spends of 135/141/165 points:

- WAR/CLR/WIZ defeated both sampled dragons in all three seeds, about 112–338s.
- WAR/CLR/MNK defeated both in all three, about 501–532s.
- MAG/NEC/SHM defeated Vox in all three, about 596–715s; Nagafen had two wins and
  one900s timeout. A 306-point deeper core won three Nagafen samples in 700–753s.

These support the possibility of demanding solo play with far fewer AAs than the
TBS pool. They do **not** test this cutoff: the old cores included post-TBS
Punch Mastery 3511, pet support 3512/3818/1403/1205 and Eyes Wide Open 938. Gear,
controllers and source were dated, and current production has intervening
changes. Three seeds do not establish a population win rate or fun. There were
**no new native combat encounters or owner in-game acceptance tests in this audit**.

Sources: [shared core report](../../balance/native-aa-release-candidates.md),
[core definitions](../../balance/aa-release-candidates.json),
[expanded gear limitations](../../balance/native-expanded-gear.md).

## Enforcement and acceptance before a release

The snapshot contains **238 saved ownership rows**, of which **64 contain at least
one post-TBS rank**. These are rows, not 64 players. The separate strict-purchase
classification also excludes grant/system entries and missing dependencies; do
not confuse its 134 outside/over-cap rows with 64 expansion conflicts. Current
aggregates are sufficient to identify a migration concern, not determine refunds
or each character's effective held-class policy.

Preserve canonical earned ranks, charges and point accounting. Use the current
earned-versus-usable AA model; choose explicitly between dormant retained ranks
and a tested refund policy. Do not delete purchases or overwrite higher earned
ranks by buying a lower one. Re-evaluate policy on login, class changes, AA/rule
reload and purchase, and keep display, activation and passive bonuses consistent.
Re-run per-character preflight immediately before any eventual deployment.

Follow declarative `era.json` policy and the established feature→dev→test→main
workflow. Native independent AA caps need native code, tests and the appropriate
world/zone rule catalog pairing if new rules are added. A catalog-only deployment
still needs the serving-zone AA refresh procedure; a generic rules reload is
not proof that cached passive bonuses were recalculated. Production native child
exits restart the whole runtime. Client UI changes require signed client delivery.

**Exact proposed QA:**

1. On disposable single-class controls for all 16 classes and the six unions in
   the table, verify first allowed rank, first disallowed successor, shared
   prerequisites, level gates, point cost and a family not held by the character.
   Check native AA tabs, sorting/Starter recommendations, buy, activate, passive
   stats, zone and camp/relog. Preserve the 64 existing conflict rows in a clone
   and demonstrate earned-rank/charge/point retention through policy changes.
2. Compare levels 10/20/30/40/50 at 0/25/100/200/500 points and full **legal** closure.
   Report actual spend when the pool exhausts. Use the same legitimately obtainable
   gear/buffs, pets, spell/heal caps, NPC definitions and fixed seeds per comparison.
   Compare open stress ceiling, strict TBS, then TBS+each exception/cap change.
3. Early targets: East Commonlands orcs at an appropriate level, then suitable
   Crushbone/Unrest/Lower Guk single targets and two-to-three add pulls; record exact
   spawn/NPC IDs at fixture capture rather than invent them. At 50 use Nagafen
   **32040 in soldungb** and Vox **73057 in permafrost**, plus undead/humanoid camps
   for Slay/Headshot/Anatomy and pet-danger encounters. Revalidate IDs/content.
4. Record time to kill, incoming burst/minimum HP, heal/mana use, recovery and
   consumables, deaths/timeouts, cooldown usage, pet deaths/threat, kills/hour and
   loot/hour across repeated fights. A one-boss win misses refill/execute farming
   and cooldown chaining. Require mechanics and earned upgrades to remain relevant.
5. Test all owned pet slots, hold/backoff/follow, relocation only after implementing
   a verified action, and combinations of pet HP/avoidance/AC. Verify retained
   heal/utility AAs actually accept legal level 50 targets. Owner in-game sign-off
   remains required for balance, readability and enjoyment before main promotion.

## Verification and reproduction

From the workspace root:

```powershell
python -B docs/audits/aa-tbs-20261013/analyze.py
python -B docs/audits/aa-tbs-20261013/review.py
python -B -m unittest discover -s docs/audits/aa-tbs-20261013 -p test_analysis.py -v
```

Eight focused tests cover rank-prefix truncation, inherited/count-based
prerequisites, missing/grant-only dependencies, class-union deduplication, cycles,
shared ranks and real-capture monotonicity/closure. Independent review found a
spell-link metric mislabeled as active; it was renamed `spell_linked_families`.
The capture lacks some native spell-validity/target fields, so linked spells are
not claimed to be activatable. The owner declined an additional cross-model review.

Reference RoF2 `dbstr_us.txt` coverage falls from 177 missing-title families in
the open legal pool to 2 at TBS, but this is **only the protected reference client**,
not a fresh verification of the delivered signed strings. The two custom families
are Ancient Attunement 2220 and Expeditious Dispatch 30196. Current production maps
them to Teleport spells 42604/42603; older reports describing Ancient Attunement
as spell 99001/pet-summoning are historical and do not describe this snapshot.
No travel activation was tested here.

The general distinction between ability families, rank rows and client strings
matches the [official EQEmu AA documentation](https://docs.eqemu.dev/server/aas/customizing-aas/).
Nightcap's inspected custom code and captured content determine this recommendation.
