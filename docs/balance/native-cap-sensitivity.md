# Native spell damage and healing cap sensitivity

Date: 2026-09-13. Isolated native experiment; baseline remains 250/250.

## Controls

The owner permits caps above 250 when evidence supports balance. Test damage/heal
250/300, 300/250 and 300/300 against the existing 250/250 reports. Each variant uses
54 fights: three profiles, zero/launch-maximum/later-maximum AA allocations, both
dragons and seeds 1729–1731. The same source-constrained candidate gear, purchases,
preparation, spell choices, controllers and NPC data are retained. This does not
re-optimize gear for the changed caps.

The current percentage path in Mob::GetExtraSpellAmt adds abs(base)*item_bonus/100.
For an eligible direct spell without other modifiers, raising 250 to 300 changes
3.5 times base to 4 times base, about a 14.3% increase. Focuses, criticals, spell
eligibility and DoT/HoT duration handling prevent treating that as a universal final
damage/healing multiplier.

The same isolated binary from aa-ownership-after-build.json runs every variant.
Guarded transactions change only the two ruleset-1 item caps in
nightcap_balance_20260912. Rule storage is InnoDB. Each phase restores the complete
captured cap rows, including notes, before starting the next phase. Every initial
native build matches its baseline exactly after allowing the two cap readouts;
all builds reach the intended effective caps.

## Launch-maximum results

Wins below are counts in three matched samples, not win-probability estimates.

| Build | Actual AA spent | Boss | 250/250 | Damage 250, heal 300 | Damage 300, heal 250 | Both 300 |
|---|---:|---|---:|---:|---:|---:|
| WAR/CLR/WIZ | 135 | Nagafen | 3/3 | 3/3 | 3/3 | 3/3 |
| WAR/CLR/WIZ | 135 | Vox | 2/3 | 1/3 | 3/3 | 3/3 |
| WAR/CLR/MNK | 141 | Nagafen | 3/3 | 3/3 | 3/3 | 3/3 |
| WAR/CLR/MNK | 141 | Vox | 3/3 | 3/3 | 3/3 | 3/3 |
| MAG/NEC/SHM | 165 | Nagafen | 0/3 | 1/3 | 0/3 | 2/3 |
| MAG/NEC/SHM | 165 | Vox | 3/3 | 3/3 | 3/3 | 3/3 |

With both caps at 300, the launch caster Nagafen samples last 97.10–129.65 seconds;
the launch pet Nagafen outcomes last 662.35–748.95 seconds, including its death.
At the deeper AA maximum, a damage-300 caster Vox sample ends in 57.5 seconds.
The pet's deeper maximum still produces only 1/3 Nagafen wins with both caps 300.
Higher AA and healing are therefore not monotonically better in these fixed
controller/seed samples; changed timing and RNG consumption matter.

All 18 melee-build reports under damage 300 match the baseline in full after
removing only the changed initial spell-damage readout. That controller's physical
damage and healing receive no direct benefit from this lever. The caster gains
far more, demonstrating why a global damage increase is not an even class adjustment.

Zero-AA results retain meaningful difficulty. With both caps 300, the melee build
wins none of six samples and the pet build wins one Vox sample and no Nagafen
samples. The caster wins all three Nagafen samples and two Vox samples. This is
still only three particular multiclass builds with endgame candidate gear.

## Decision and limits

Keep 250/250 for the next baseline. Damage 300 substantially boosts the caster
without fixing the launch pet Nagafen failure by itself. Healing 300 and both 300
improve some pet outcomes but do not establish consistent survival or reduce the
large role-dependent duration gap. Investigate pet preparation, support/threat and
appropriate expansion AA access before applying a broad cap change.

No permanent 250 ceiling is established. No NPC HP adjustment was tested here.
Three seeds, fixed controllers and candidate gear do not prove optimal play,
attainability of every item or release-wide balance. Complete AA offerings, owned
purchase lifecycle handling, fresh source parity and manual QA remain required.

## Evidence and reproducibility

cap-experiment-inputs.json selects the 54 exact prior gear-source cases. The three
cap-*.json.gz reports contain 162 native fights; cap-experiment-checks.json records
all 54 groups, win counts, outcome-duration and minimum-HP ranges. Six generated
SQL files preserve the exact apply/restore transactions. cap-final-checks.json
confirms restored rules and original AA-table hash, zero synthetic account,
character, owned-AA and inventory rows, and no temporary procedures. Only the two
verified synthetic reagent rows were removed after all batches completed.
An additional deliberately stale healing-cap precondition fails after the
spell-damage update and rolls that update back exactly. The rejected SQL and
before/after rule rows are preserved in cap-rollback-* evidence. All 310 automated
tests pass; the added rollback-evidence assertions also pass independently.

From tools/balance, run:

```text
python -m unittest tests.test_cap_controls tests.test_cap_evidence
python -m unittest discover -s tests
```

The host cap_controls.py runner refuses existing evidence, the wrong fixture,
nonempty characters, nontransactional rule storage or changed cap preconditions.
It waits for each batch and restores cap rules in a finally block on native or
verification failure. Each child native fight retains the existing 120-second
wall-clock timeout. Interrupted host execution still requires inspecting and
restoring the recorded clone state before another experiment.

## In-game QA before any future cap promotion

Use disposable level-50 WAR/CLR/WIZ, WAR/CLR/MNK and MAG/NEC/SHM characters with the
exact recorded equipment and launch-maximum purchases. In soldungb, fight Lord
Nagafen 32040; in permafrost, fight Lady Vox 73057. Record actual damage/healing,
duration, mana pressure, fear interruption, deaths, pet survival and heal threat.
Repeat at zero and the intended expansion's maximum AA allowance. If a future
proposal changes caps, compare the same characters before and after, reload the
rules explicitly, and verify the unchanged cap independently for a one-cap test.
No test promotion, live restart or live cap change occurs in this checkpoint.
