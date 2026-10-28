# Paladin grips and Ascended quest rewards â€” October 27 candidate

**Review rejected the current numerical table.** The fresh [progression review](review-followup.md) found comparator, quest-progression and damage-cap gaps. Values below are retained as the rejected candidate, not approved balance. No replacement values or deployment were made.

The subsequent [quantitative assessment](assessment/ASSESSMENT.md) proposes a
replacement test package, accuracy/block budgets and support-stat progression.
It includes fresh selected public stat definitions and native-function sensitivity
calculations. None of its proposed gameplay values is implemented or approved for
release; maximum shield-AA builds still favor 1H in the comparative model.

The [isolated Palwar/Vox experiment](vox-test/README.md) now records all quality/grip
variants, actual and matched skills, comparison weapons and timestep controls.
All retained encounters won, but Monk abilities dominate and small rankings are
timing-sensitive. This is candidate-viability evidence, not final balance approval.
The local Docker blocker is resolved; native client toggle/shield QA and a fresh
paired release remain pending.

Implemented locally on `fix/paladin-grip-client-refresh`, together with the
[RoF2 same-ID definition repair](../client-refresh/README.md). Not committed,
published or deployed. User authorized 1H balancing and Ascended SoulFire/Fiery
Avenger quest rewards, retaining Fiery Defender's separate epic upgrade.

## Weapon profiles

| Weapon | ID | 2HS damage/delay | 1HS damage/delay |
|---|---:|---:|---:|
| SoulFire | 5504 | 23/45 | 7/30 |
| SoulFire (Polished) | 205504 | 31/45 | 10/30 |
| SoulFire (Exalted) | 405504 | 38/45 | 12/30 |
| SoulFire (Ascended) | 605504 | 46/45 | 15/30 |
| Fiery Avenger | 11050 | 33/44 | 11/30 |
| Fiery Avenger (Polished) | 211050 | 44/44 | 14/30 |
| Fiery Avenger (Exalted) | 411050 | 55/44 | 18/30 |
| Fiery Avenger (Ascended) | 611050 | 66/44 | 22/30 |
| Fiery Defender | 10099 | 35/40 | 13/30 |
| Fiery Defender (Ascended) | 810099 | 47/40 | 17/30 |

These are optional defensive grips. The 2H values match fresh production item
rows, including SoulFire Ascended46/45 and Avenger66/44; the older local snapshot
31/45 and45/44 was stale. All other stats, procs, quality, slots, identity, augments,
charges and saved fields remain. Damage/delay are absolute per-ID projections,
so repeated toggle/load/copy/Bazaar reconstruction cannot compound scaling.
Returning to2HS restores the reviewed canonical values exactly. There is no item
layout, schema, rule or SQL content change. Existing1HS metadata receives this
profile on load after activation; this does not upgrade owned item quality.

The1H ratio is slightly below half the2H ratio. Legal Shield Specialist rank4848
adds100% base weapon damage; Knight's Advantage rank1626 adds24% double-attack
chance only with2H for a knight without a martial secondary. Held Warrior/Monk
can remove that1H penalty. A70% ratio would become about140% of the original
weapon component with Shield Specialist before shield defense. Dedicated1HS
Ascended Ghoulbane30/34 and Sword of the Morning32/27 remain stronger raw1HS
options; these grips deliberately pay for flexible shield access.

Ascended Avenger already has a higher2H ratio than Ascended Defender in production.
This candidate preserves that existing relationship; it does not retune the epic
forge or promise that every later sword has a higher raw ratio.

## Evidence and limits

`production-reference-complete.json` is an owner-approved SELECT-only capture of
public item definitions and installed quest sources/precedence, excluding player
and account data. The earlier capture is retained as provenance. Native production
functions GetWeaponDamageBonus/GetProcChances execute in300diagnostic cases over
all10profiles, levels1/20/28/40/50, shield modifiers0/100 and added damage0/5/10.
At level50 with no augment and100% shield modifier,1H/2H normalized damage indices
are SoulFire22.67/24.22, Avenger32.00/33.64 and Defender25.33/27.00. Every unaugmented
case retains the2H advantage; the diagnostic deliberately gives both grips equal
attack opportunities, so it does not rely on the knight double-attack penalty.

These indices are not measured combat DPS. The fixed2x weapon term omits actual
hit/mitigation/crit/Slay distributions, damage caps, multi-attacks, stance spells
and encounters. +5/+10 augment rows are sensitivity cases, not proven obtainable
Classic loadouts;100augmented rows favor1H. Strong augments and specialized builds
can reverse ordering. The actual proc function preserves normalized cadence when
AdjustProcPerMinute=true using the October23 captured rules; confirm the current
rules at release. No universal2H-DPS-superiority or completed balance acceptance
is claimed. Full Linux build and native combat measurements remain blocked by
Docker Desktop's unresolved local Secrets Engine socket startup fault.

## Quest rewards and chain compatibility

Three captured scripts change only terminal reward IDs and obsolete heal dialogue:

- `paw/v0/Brother_Hayle.lua`: SoulFire5504 -> Ascended605504.
- `southkarana/#Brother_Hayle.lua`: same reward correction. Its later-era spawn
  gate remains; this does not make that version Classic-accessible.
- `airplane/Inte_Akera.lua`: Fiery Avenger11050 -> Ascended611050.

The installed tier-aware items.lua already accepts Ascended605504 for Inte's
SoulFire hand-in and Ascended611050 for Irak Altil's Avenger hand-in. All four
ordinary qualities pass the actual captured Lua helper in tests, including1HS
metadata. Irak still grants Normal Fiery Defender10099; both Epic Forgemaster
scripts and the separate810099 upgrade are unchanged. No global grant hook,
recipe change, blanket quest-upgrade rule or retroactive owned-item conversion.

Faction/ingredients/XP/coin/repeatability/returns are preserved. The existing Paw
Hayle script consumes a complete low-faction hand-in without a reward; the later
South Karana script resummons its components. Differential tests preserve those
existing behaviors rather than silently changing this quest's faction contract.
Warn testers to meet the faction requirement. Heal dialogue now describes grips.

## Tests and release gate

Lua tests require `python -m pip install -r tools/tests/requirements-paladin.txt`
(or the task-local interpreter path). Run `python -B -m unittest discover -s tools/tests -p "test_paladin_*.py"`.
The production capture is never executed by test discovery.

- Four grip groups pass, including250repeat-toggle cycles across ten distinct
  production profiles, exact2H restoration, metadata load, copy and field preservation.
- Four Lua5.1 groups execute actual quest handlers and captured helper; earned
  rewards, reordered/partial/empty branches, faction failures,
  money/XP/return identity and downstream Normal Defender behavior are covered.
- Three preflight groups reject canonical stats, script/helper digests, precedence,
  new recipe consumers and stale/future captures. Captures are exclusive new files.
- Bazaar's four native groups cover current projected damage/delay through actual
  Restore/Snapshot buy/cancel paths. Existing item-transfer safeguards remain.
- Actual x86 DLL/runtime fixtures build;11runtime tests and117guard catalog checks
  pass. Go preflight/manifest/package suites verify the balanced actual binary pair.
- All19wiki content/link/anchor and refresh tests pass; full40article review is
  recorded. Historical global source drift remains review-required.
- Native diagnostic has300cases. Full server build/MariaDB/native encounters and
  owner gameplay QA remain pending. A fixture build is not a full zone link.

Before release, run the read-only capture into a NEW file and run
`python tools/paladin_grip_preflight.py --capture NEW_FILE`. CLI requires capture
within one hour; compare exact ten canonical damage/delay/type/class/slot values,
three reward scripts, three unchanged epic scripts, tier-aware helper, script
precedence and recipe consumers. Do not overwrite the reviewed reference or accept
new hashes to bypass drift. Reconcile all current native/source/client releases.

Pair a fresh integrated native build with proxy0.13.1/catalog/config and all three
quest files. Common ItemInstance behavior changes, so rebuild the paired native
binaries; preserve the current cache layout, rules and unaffected scripts/data.
Use the supported graceful whole-runtime release on OVH, never kill individual
zones. Exit EQ and install the signed launcher update after authorized publication.
Unsigned balanced client assets preserve138of141descriptors/notes/tombstones from
signed2026102601. `verification.json` binds their hashes. No release authorization
is implied by the read-only capture approval. Website edits remain unpublished.

Recovery must retain grip-aware code and current player state. Do not restore old
inventory snapshots or downgrade to pre-grip binaries. Restoring reward scripts
would affect future grants only; already earned Ascended weapons remain owned.

## Exact owner QA after activation

1. Meet Hayle's faction requirement in Classic Splitpaw, complete SoulFire and
   inspect Ascended605504:2HS46/45; click1HS15/30 and equip a shield without zoning.
2. Meet Inte Akera's required faction in Plane of Sky; AscendedSoulFire in either
   grip earns the first blessing. Complete the original four-item final hand-in:
   AscendedAvenger611050 starts2HS66/44 and toggles1HS22/30.
3. At Irak Altil in Plane of Fear, AscendedAvenger plus the original component
   still yields NormalDefender10099. Its1H profile is13/30; Epic Forgemaster still
   requires the separate existing upgrade and yields810099,2HS47/40 or1HS17/30.
4. Repeat every quality's toggles, shield refusal when returning2H, stance refresh,
   same-ID copies with opposite grips, augments, charges, relog/zone/bank/trade/corpse
   and Bazaar buy/cancel. Verify no quality/stat loss outside specified damage/delay.
5. Compare both grips at matched level/skills/gear on the same living and undead
   target: Paladin alone and Paladin/Warrior or Monk, no AAs and legal purchased
   shield/weapon/crit/Slay AAs, with/without compatible damage augments. Record
   survival, melee/proc damage separately, attack counts and actual purchased AAs.
   Native live shield/animation/proc/combat acceptance is still pending.
