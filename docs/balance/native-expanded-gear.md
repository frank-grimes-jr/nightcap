# Expanded gear and augment baseline

Date: 2026-09-12. Diagnostic work only; no live items, AA availability, spell caps,
NPC HP, binaries or era rules were changed. This supersedes the *gear assumptions*
of earlier candidate comparisons; those older captured results remain historical
evidence. Full BiS and final balance are not certified.

## What changed

The old additive loadouts excluded items above level 50's recommended level,
two-handed weapons, dual wield and existing drop augments. The expanded generator
includes recommended-level stat scaling, separate shield/dual/two-hand/focus
layouts, and balanced, durability and melee scoring objectives. Haste substitutions
expose the max-item-haste tradeoff without adding item haste together. The assignment
solver maximizes each stated additive objective subject to slot and lore constraints.
Augments are assigned afterward, globally across sockets and against worn-item lore.
This sequential search does not claim a joint armor/augment/combat optimum.

The captured drop pool contains nine eligible type-7 augment families, including
their generated tiers. All selected augments have no item-type restriction and
recommended level zero. The generator deliberately excludes future restricted
augments and augments that would increase their parent's recommended-level penalty
until those cases are implemented. Visible sockets, type masks, actual worn slot,
class/race/deity, required level and lore are enforced. The native diagnostic loads
the real augment instances and exports the observed equipped inventory. It also
rejects duplicate worn slots, augment-as-armor inputs and above-required-level gear.

Native controls verify +12 item HP or +24 item mana when the corresponding Ascended
augment is installed in Halo of the Enlightened. In recommended-level-62 Band of
Swirling Air at level 50, those bonuses become +10 HP or +19 mana. Nine invalid
loadouts fail before producing reports. No equipment/socket differences were found
between the requested and observed inventories of all 90 generated builds.

The native binary is an isolated diagnostic linked from the previously pinned 130
objects/archives, with the candidate AA-duration source retained. This is not a
fresh complete production-source rebuild. Its SHA-256 is recorded in the evidence
manifest. Source parity and RoF2 interaction still require in-game QA.

## Acquisition assumptions

`captured_drops` includes positive, enabled sources in the frozen Classic snapshot,
with all existing generated item tiers. It includes level-72 A Legendary Behemoth
(NPC 56182, Steamfont), the source of the recommended-level-62 high-stat accessories
and 41-haste ring. Its solo acquisition difficulty has not been demonstrated.

`sources_at_most_65` retains items with at least one captured source of level 65 or
lower and their tier definitions. This is an acquisition sensitivity comparison,
not a new release rule or proof that those mobs are all soloable. Quest, crafting,
merchant and global-loot challengers remain in the separate acquisition review;
they are not silently treated as unobtainable. Farming probability/time and the
ability to complete prerequisite fights remain outside the gear optimizer.

The expanded balanced WAR/CLR/WIZ shield build has 7,814 HP and 7,780 mana before
buffs at zero spent AA, versus the earlier weapon/ring candidate's 6,037 HP and
4,719 mana. The five native preparation buffs raise its HP to 8,739. Both spell
damage and healing bonuses already reach the active 250 caps. These are combined
gear/augment differences, not an isolated augment effect.

## Matched zero-spend fights

Seven loadouts use identical free AA purchases, native preparation/recovery,
fixed nuke/self-heal routine and seeds 1729–1731 against each boss. Six unchanged
old-loadout runs provide regression controls. All 48 reports pass encounter,
preparation and movement checks; the six legacy report hashes match exactly.
Actual native inventories also match each new encounter's requested loadout.

Numbers below are wins in three samples and the full sampled elapsed-time range,
including deaths. They are not estimated win rates. The fixed caster routine does
not establish optimal melee play simply because the weapon layout changes.

| Gear candidate | Nagafen wins; seconds | Vox wins; seconds |
| --- | --- | --- |
| Earlier ring/weapon reference | 3; 170.55–238.35 | 1; 234.10–293.95 |
| All captured drops, balanced shield | 3; 178.50–258.60 | 3; 190.70–280.85 |
| All captured drops, durability shield | 3; 195.85–228.20 | 3; 205.30–456.50 |
| All captured drops, melee shield | 3; 195.85–267.25 | 3; 327.50–615.15 |
| All captured drops, melee dual wield | 3; 161.30–246.50 | 2; 287.70–536.85 |
| All captured drops, melee two-hand | 3; 186.35–229.30 | 0; 356.00–430.75 |
| Sources <=65, balanced shield/36 haste | 3; 177.50–209.85 | 0; 239.20–314.90 |
| Sources <=65, durability shield/36 haste | 3; 133.40–225.90 | 1; 125.50–223.65 |

The balanced shield candidate uses Blood Sword of Hate (662035) and Shining Shield
of Divinity (662014). The durability shield is Fearsome Shield (601555). The melee
dual comparison adds Hammer of Wickedness (662036); the two-hand comparison uses
Culler (631822) with an empty offhand. Their complete armor and socket assignments
are recorded in `gear-expanded-inputs.json`; layouts also change other equipment
according to their stated objective. These are whole-loadout comparisons.

The stronger balanced loadout improves the sampled Vox outcomes, but one Nagafen
run still falls to 9.5% of starting HP. Source-limited candidates retain significant
Vox difficulty. These results argue for checking acquisition and AA availability
together before increasing caps or inflating NPC HP.

## Fixed gear across AA budgets and proposed release pools

The balanced shield inventory is held identical for another 54 prepared encounters:
the requested 0/100/200/500/all open-AA budgets and four restricted-pool comparisons.
Every inventory, purchase sequence, preparation, movement and terminal state passes
verification. The six zero-spend encounters match the preceding gear comparisons
exactly. All scenarios below won all three sampled fights against each boss.

| Budget/policy | Actual spent | Nagafen seconds | Vox seconds |
| --- | ---: | --- | --- |
| Open pool, 0 | 0 | 178.50–258.60 | 190.70–280.85 |
| Open pool, 100 balanced | 98 | 80.30–223.70 | 135.05–431.35 |
| Open pool, 200 balanced | 198 | 31.90–77.45 | 52.30–261.75 |
| Open pool, 500 balanced | 496 | 26.75–39.85 | 28.00–47.35 |
| Open pool, all legal purchases | 13,738 | 11.40–22.50 | 11.40 |
| Proposed early core, 100 budget | 98 | 105.35–177.70 | 243.75–267.85 |
| Proposed early core, all | 114 | 111.90–225.20 | 186.30–285.45 |
| Proposed expanded core, all | 201 | 105.35–205.50 | 214.10–269.10 |
| Open pool without Twincast/Frenzied families | 13,528 | 52.65–65.15 | 23.25–42.95 |

Point totals alone do not define power: the retained abilities, ranks, prerequisites,
passives and activation policy matter. Three-seed nonmonotonic results are not
evidence that buying more AA makes a build weaker. The unrestricted all-purchase
case stays a stress ceiling, not the intended Classic endgame. Even without both
burst families, sampled minimum HP remains at least 76.6% for Nagafen and 95.8%
for Vox. Removing those two families alone does not resolve the high-power ceiling.

The proposed cores are defined in `aa-pool-policy.json`, including their rank caps;
the free six-ability baseline remains fixed and still requires release review.
The owner’s expansion direction should be implemented as a reviewed per-release
ability/rank policy, retaining early core progression, deferring later ranks and
excluding demonstrably unsuitable interactions. In release baselines, **all means
all legally purchasable AAs in that release's curated pool**. A pool can exhaust
before 200 or 500 points; it must report the actual spend rather than invent ranks.
These comparisons change diagnostic purchases only. Live policy enforcement,
existing-purchase handling and the exact release list remain unfinished.

## Reproduction and remaining checks

From `tools/balance`, run `python -m unittest discover -s tests`. Generate the
candidate inputs with:

```powershell
python gear_candidates.py --snapshot fixtures/classic-20260912-v2.json.gz --templates ../../docs/balance/native-aa-inputs.json --output ../../docs/balance/gear-expanded-inputs.json
```

The evidence manifest pins inputs, native outputs and source bytes. The diagnostic
requires its existing isolated clone/runtime and does not support the live PEQ
database. `gear_encounters.prepare` and `prepare_aa` generate the saved comparison
matrices from the earlier prepared inputs and explicit AA-pool inputs. Verification
uses `gear_encounters.verify`, `active_aa_controls.verify_encounters`,
`augment_controls.verify_equipment` and `verify_native_movement.verify`.

Before promotion, in-game QA must:

1. On a level-50 Human WAR/CLR/WIZ, insert Compressed Froglok Bile (651903) or
   Chunk of Amorphous Granite (679626) into Halo (601549), then the appropriate
   socket of Band of Swirling Air (609959). Confirm the four item-stat deltas above,
   required levels and lore rejection; ensure type-7 augments cannot fit Sabertooth's
   type-4 socket. Check real inventory/socket UI behavior and any acquisition gates.
2. Equip the complete balanced shield inventory recorded in the input, with the
   recorded free AA set. Verify native baseline stats, preparation costs, sitting
   recovery and maintained buffs. Do not substitute unrestricted purchased AAs.
3. In Solusek B, fight Lord Nagafen (32040); in Permafrost, fight Lady Vox (73057).
   Cast preparation spells 67, 314, 488, 64, and 60 for Nagafen or 61 for Vox.
   Compare danger, mana use, fear/dispel, movement and healing with the saved traces.
   Repeat the source-limited inventory to check whether its acquisition stage needs
   deliberate AA support. Timing parity is a measurement, not a presumed guarantee.
4. Validate Behemoth access/farming difficulty before labeling its loot ordinary
   level-50 BiS. Resolve quest/crafting contenders and representative melee/pet/DoT
   play before claiming complete server balance. Select and enforce the expansion AA
   policy separately, with the owned-rank/client behavior checks in the AA review.
