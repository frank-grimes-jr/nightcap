# Native gear acquisition sensitivity

Date: 2026-09-13. Isolated diagnostic evidence; no live balance change.

## Question and controls

The previous dragon loadouts include rewards from level-72 A Legendary Behemoth
56182. This study removes that NPC as an item source. An item remains eligible
when the frozen Classic drop catalog supplies another source; generated tiers
and augments follow the same rule. Other high-level Classic raid sources remain
eligible. This isolates the Behemoth dependency rather than imposing an arbitrary
NPC-level definition of obtainable gear.

Re-optimize the same additive objective used by each existing shield loadout:
balanced for WAR/CLR/WIZ and MAG/NEC/SHM, melee for WAR/CLR/MNK. Assign legal augments
across the resulting sockets. Retain exact class/creation stats, native AA
purchases, spells, preparation, movement policy, bosses and seeds. The comparison
uses all 18 shared AA allocations against both dragons at seeds 1729–1731.
Inputs record a paired original case ID and every surviving source for each worn
item and augment. The old tier label is retained as a prefix for provenance;
the actual equipped inventory and source-policy metadata define the new loadout.

The unforced replacement sets have worn haste 0/27/0 respectively. Because an
additive item score does not optimize haste's combat effect, a second Monk-only
comparison forces Ascended Cloak of Flames 611621 for 36% haste, reassigning the
remaining equipment and augments. It retains all six Monk allocations and six
boss/seed combinations, adding 36 fights without repeating the other roles.

This remains a drop-pool sensitivity study, not a proof of global gear optimality
or a complete solo farming path. Surviving sets still include Cazic-Thule sources.
Quest, craft, merchant, global-loot and click/focus challengers need their own
acquisition and combat evidence. Three seeds are samples, not win probabilities.

## Verified results

At zero spent AA, before combat preparation, the gear change produces:

| Profile | HP: previous → replacement | Mana: previous → replacement | Worn haste |
| --- | ---: | ---: | ---: |
| WAR/CLR/WIZ | 7,794 → 6,607 | 7,780 → 5,778 | 41% → 0% |
| WAR/CLR/MNK | 7,746 → 6,478 | 5,766 → 4,396 | 41% → 27% |
| MAG/NEC/SHM | 6,331 → 4,994 | 8,181 → 6,920 | 41% → 0% |

Every build still reaches both item spell-damage and healing caps of 250. The
changed HP, mana, other stats and gear interactions therefore materially affect
outcomes even while those two capped bonuses remain fixed.

For the unforced replacement sets, each entry below gives wins in three samples
and the full outcome-duration range in seconds, including deaths and timeouts:

| Profile | AA stage (actual spent) | Nagafen | Vox |
| --- | --- | --- | --- |
| WAR/CLR/WIZ | Zero (0) | 3/3; 249.40–323.40 | 1/3; 319.85–583.55 |
| WAR/CLR/WIZ | Launch maximum (135) | 3/3; 117.00–136.20 | 2/3; 230.05–586.75 |
| WAR/CLR/WIZ | Deeper maximum (261) | 3/3; 120.00–148.80 | 3/3; 261.95–446.75 |
| WAR/CLR/MNK | Zero (0) | 0/3; 751.50–786.55 | 1/3; 877.45–900.00 |
| WAR/CLR/MNK | Launch maximum (141) | 3/3; 549.50–652.65 | 3/3; 602.55–643.35 |
| WAR/CLR/MNK | Deeper maximum (288) | 3/3; 390.50–452.90 | 3/3; 482.45–494.45 |
| MAG/NEC/SHM | Zero (0) | 0/3; 135.05–532.85 | 0/3; 484.30–631.30 |
| MAG/NEC/SHM | Launch maximum (165) | 0/3; 613.35–810.30 | 3/3; 609.40–705.15 |
| MAG/NEC/SHM | Deeper maximum (306) | 1/3; 666.10–711.00 | 3/3; 637.95–742.80 |

The Monk cloak comparison produces 0/3 wins against both bosses at zero AA
(all Vox cases time out). At 141 spent it wins all samples in 555.50–623.50s
against Nagafen and 628.50–643.55s against Vox. At 288 spent it wins all samples
in 425.85–484.45s and 449.45–624.75s respectively. The higher-haste cloak does
not consistently dominate the unforced loadout. Preserve both comparisons;
three seeds do not support selecting a universal optimum from small differences.

The pet build's Nagafen result falls from two wins and a timeout at the old
launch maximum to three deaths, and from three deeper-pool wins to one. This
gear dependency must be resolved alongside owner survivability, pet support and
threat management before declaring an AA pool balanced. It does not by itself
justify increasing global caps or changing dragon HP.

All 144 source/haste fights pass independent gear/allocation/native verification.
Twelve unchanged prior-build reports retain identical raw hashes. All 90 completed
reports from the interrupted attempt match after removing the optional death-
evidence fields. The full 243-test suite passes. Only native_runtime.o changed
among the pinned build objects; all four candidate sources, harness, adapter
hashes and compiler/link flags match the prior build. Afterward the two synthetic
reagent rows were removed; clone account, character and inventory counts are zero.

## Death-callback evidence

The first attempt stopped verification after 90 completed cases. In the next
pet case (later pool, 98 spent AA, Nagafen, seed 1729), the owner reached -500 HP
at the native death callback at 164.65 seconds. A pending heal then completed
within the same MobProcess pulse, leaving the final sampled HP at +732.

The diagnostic's death adapter records terminal combat without executing a real
corpse transition. A final positive HP sample therefore could not by itself prove
that the player survived. The verifier correctly refused that old report.

Optional `capture_terminal` now records native death-callback order, time, actor,
HP, maximum HP and mana. For these pet comparisons, the first callback determines
the outcome, including when both actors die within one pulse. The verifier requires
nonpositive callback HP and the terminal pulse time, rejects missing/duplicate/
wrong-actor evidence, and includes an owner death as zero minimum HP. It retains
the old strict final-HP checks when callback capture is absent.

The focused replay changes only the two echoed input flags and the added callback
events. All other report fields match the failing report exactly. The post-death
heal remains visible; this change does not fabricate a negative final snapshot or
claim to validate real corpse, resurrection or pet-persistence behavior. Damage
and resource activity later in that terminal pulse remain diagnostic limitations.
Exactly one final gear-comparison case exhibits positive post-death owner HP;
none contains two terminal actor callbacks. Callback-order handling also has
explicit synthetic rejection tests for simultaneous deaths and invalid evidence.

The build retains all four previous native candidates (AA duration, weapon
eligibility, pet ownership and pet commands) and the same pinned native objects.
It does not establish fresh complete source/header parity. See
`gear-source-build.json` and the evidence manifest for exact provenance.

## Reproduction and QA

From `tools/balance`, regenerate source inputs with `gear_source_controls.py`,
the frozen v2 snapshot, `release-pool-inputs.json` and the build manifest's binary
SHA-256. Add `--monk-cloak36` for the second matrix. Run each with the shared native
driver in the isolated runtime, using distinct output filenames. Verify both with
`gear_source_controls.py --verify`, passing the original pool inputs, snapshot,
native AA catalog and corresponding generated input. Run the full unittest suite.
The failed attempt is preserved as partial evidence, not a completed balance run.

Before test promotion, use the exact input loadouts and AA ranks in soldungb
(Nagafen 32040) and permafrost (Vox 73057). Check actual worn haste, augmentation,
cast/heal amounts, all three pet slots, belly casting, fear recovery and aggro.
Compare zero spend and both candidate maxima, plus the Monk cloak swap. Record
fight time, death, low HP, mana pressure and failed mechanics. A late heal must
not resurrect a dead character or leave a false living state. Source acquisition
and in-game QA remain required before calling the balance ready; main promotion
requires owner sign-off.
