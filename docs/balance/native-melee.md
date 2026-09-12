# Native melee baseline and held-class weapon correction

Date: 2026-09-12. The attack fix is a source candidate verified in the isolated
diagnostic. No live binary was replaced and no server restart, item change,
AA removal, cap adjustment or NPC tuning was performed.

## Correctness before balance

The first WAR/CLR/MNK pilot exposed audit gate G018.11: inventory accepted the
Monk/Beastlord-only Balanced Tonfa of Serenity (662038), but native weapon damage
rechecked only the Warrior base class. All 632 normal swings returned -5 (immune).
Monk button attacks still dealt damage, which initially masked the broken weapon.
The 900-second pilot timed out with Nagafen at 19,580 HP. Its original input/report
remain in `melee-pilot-*`; it is a reproduced defect, not a valid balance result.

The candidate `server-mods/code/zone/attack.cpp` now uses `Client::CanEquipItem` for
player weapon legality, preserving the native worn-slot, required-level and race
checks and non-player/bot paths. The difference from captured source is six added
lines and the replaced class condition. ADR 0010 records the contract and QA.

Fifteen native `GetWeaponDamage` controls pass across WAR/CLR/WIZ, WAR/CLR/MNK and
MAG/NEC/SHM. The held-Monk Tonfa returns 26 base damage at level 50/recommended 58,
while the unheld-class profiles still get zero. Ordinary Warrior weapons retain
16 damage for 662035 and 42 for 631822. Race-ineligible 5100 and required-level 65
24587 still return zero. The repaired exact pilot now deals 20,255 normal-weapon
damage in addition to monk attacks and kills Nagafen at 755.50 seconds.

The diagnostic is built with both the prior AA-duration candidate and the new
attack candidate. `melee-native-build-manifest.json` pins all 130 objects/archives
and source hashes. This remains a partial native-object rebuild, not complete
fresh-source or live-runtime parity. The prior failure binary is retained in the
isolated runtime as `balance-zone-before-weapon-gate`.

## Controller and verification

The new `melee_heal` policy uses normal autoattack and submits `OP_CombatAbility`
through the native client packet loop for Flying Kick and Tiger Claw. The native
handler controls held-class eligibility, damage, Master Wu and the separate RoF2
cooldowns (timer IDs 25/26). Each button has an additional conservative 250 ms input
floor. Movement, casting, control effects and affordable self-healing interrupt the
button routine. Superior Healing (9) is requested below 55% HP; when unaffordable,
melee buttons remain available. There are no manually added damage multipliers.

The five previously recorded preparation buffs and sitting recovery are retained.
The current database has globally widened spell class levels: Arch Shielding and
even Ice Comet appear available to Warrior/Cleric. As recorded in
`project-understanding.md`, those fields do not prove original class ownership.
This experiment intentionally isolates a melee/self-heal playstyle; it does not
claim that WAR/CLR/MNK cannot cast other spells or that this is its optimal rotation.
Per-character spell ownership/client access remains a separate unresolved gap.

Native wire damage types distinguish ordinary weapon damage from kick/claw/strike
damage. Type30 can represent several kicks; type23 can represent claws/strikes,
including Master Wu additions. The report does not assign every packet to one
precise button. Zero-spend tests require positive ordinary weapon damage, so the
original broken Tonfa pilot is rejected even though its monk skills land.

A high-AA Vox fight ends after 5.70 seconds with two blocked swings, two riposted
swings and one miss, and no positive incoming melee damage. The encounter verifier
now requires native enemy swing attempts, not a guaranteed hit. Deleting those
attempts fails the regression test. Player positive physical damage remains required.

Sixty reports pass purchase, preparation, terminal-state and movement verification:
54 monk cases plus six caster controls. Every monk inventory matches its requested
gear. The six caster native report hashes match the preceding fixed-gear AA phase
exactly. The full matrix regenerates from the frozen AA and expanded-gear inputs.

## Results

Each row covers three fixed seeds (1729–1731) against each boss. Times are seconds,
including timeouts where shown; three samples do not estimate win rates. All rows
with monk buttons enabled won all three fights against each boss.

| Layout / AA budget | Actual spent | Nagafen seconds | Vox seconds |
| --- | ---: | --- | --- |
| Shield / 0 | 0 | 755.50–797.10 | 721.20–755.45 |
| Shield / 100 balanced | 94 | 585.90–618.20 | 572.90–627.45 |
| Shield / 200 balanced | 200 | 442.20–471.50 | 506.70–552.45 |
| Shield / 500 balanced | 498 | 324.50–378.35 | 415.55–514.90 |
| Shield / all open-pool purchases | 13,261 | 11.65–15.70 | 5.70–7.65 |
| Dual wield / 0 | 0 | 538.45–572.15 | 601.05–612.75 |
| Two-hand / 0 | 0 | 676.35–777.30 | 711.70–765.00 |

With monk buttons disabled, zero-AA shield fights all time out at 900 seconds.
At 498 spent points, button-disabled shield runs win 2/3 against Nagafen and 1/3
against Vox; the other runs time out. Disabling buttons preserves native passive
effects rather than attempting to strip every possible triggered monk attack.

The shield uses Tonfa 662038 and Fearsome Shield 601555. Dual wield pairs the Tonfa
with Blood Sword of Hate 662035; two-hand uses Culler 631822. Their other slots and
augments follow the recorded melee objective, so layout comparisons are complete
loadout comparisons. Gear includes Behemoth-sourced accessories whose solo farming
access is still unproven. The shield AA sweep holds the entire inventory constant.

These results support reviewing physical progression alongside caster progression:
the tested low/medium-AA melee routine remains slow while its unrestricted ceiling
is trivial. Do not solve that gap by simply increasing spell/heal caps or inflating
NPC HP. The caster-only proposed AA cores are not yet approved pools for this role.
Better melee rotations, relevant activated AAs/disciplines, Mend, pet/DoT play,
spell-ownership reconciliation, acquisition and manual QA remain outstanding.

## Reproduction and in-game QA

From `tools/balance`:

```powershell
python -m unittest discover -s tests
python melee_controls.py --inputs ../../docs/balance/melee-inputs.json --verify ../../docs/balance/melee-encounters.json.gz --previous ../../docs/balance/gear-expanded-aa-encounters.json.gz --output ../../docs/balance/melee-checks.json
```

Use `melee_controls.prepare` with `gear-expanded-inputs.json`, `native-aa-inputs.json`
and `gear-expanded-aa-inputs.json` to regenerate the matrix. The native runner
requires the existing isolated clone/runtime and its pinned candidate binary.
Build with `--spells-source .../spells_duration_candidate.cpp --attack-source
.../attack_multiclass_candidate.cpp`; omitting the attack candidate restores the
old native object and invalidates these corrected-weapon expectations.

Before promotion, execute the exact weapon/class/race/level checks in ADR 0010.
Then equip the complete recorded WAR/CLR/MNK shield and dual inventories at level 50,
verify actual AA purchases, cast preparation spells 67, 314, 488, 64 and 60/61, recover
while sitting, and fight Lord Nagafen in Solusek B and Lady Vox in Permafrost.
Check normal swings independently from Flying Kick/Tiger Claw, hotbutton cooldowns,
fear/position recovery, self-healing and resource consumption. Compare the 0/100/
200/500 stages; retain the unrestricted all-purchase case as a labeled stress test.
Manual client/bot parity and full BiS/final balance are not certified by these runs.
