# Respect the dragons' native spell-range restriction

Date: 2026-09-12. Diagnostic correction; no live NPC, AA or spell tuning.

The previous [pet-support comparison](native-pet-support.md) used an 80-unit
approach. Both captured dragons have special ability 26, named
`CastingFromRangeImmunity` in `common/emu_constants.h`. In native
`Mob::ResistSpell`, this returns zero spell effectiveness unless
`caster->CombatRange(this)` is true. This is belly casting, separate from their
high elemental resistances. Therefore the previous ranged controller is a
measured weak strategy, not a defensible estimate of this build's full power.

The `native_spell_range` approach reads that native ability. It walks into native
melee range with line of sight before requesting offensive spells, using the
existing bounded position/history packets and native pathfinding. It respects
healing and control priorities, and returns after displacement. It retains the
same eight gems, gear, preparation, AA ranks and seeds. The default 80-unit policy
remains available as a matched historical control.

Closer approach exposed a native timing boundary: fear can begin after a movement
request but before the client processes it. The engine can then ignore that
request. `BalanceMeleeReturn::Confirm` records `controlled_after` on a request
that was not applied. Validation accepts this only when native AI control
interrupted it, preserves the requested speed bound, and reports the interruption
separately. It still rejects ordinary failed or inconsistent position reports;
it does not count fear movement as successful player input.

Every final report records the native range-immunity flag, sampled melee range
and line of sight, and range/LoS at each owner cast request. Both bosses must
start outside melee range at the configured 80-unit distance. An offensive
request outside the required range/LoS fails validation. Cast completion still
uses the actual native position and resistance calculation; approaching does not
guarantee a spell lands.

| Actual spent AAs | Boss | Wins / three samples | Outcome duration range |
| ---: | --- | ---: | --- |
| 0 | Nagafen | 0/3 | 162.80-764.05s |
| 0 | Vox | 3/3 | 574.20-595.55s |
| 100 | Nagafen | 0/3 | 555.00-801.05s |
| 100 | Vox | 2/3 | 561.25-698.15s |
| 199 | Nagafen | 0/3 | 83.25-844.65s |
| 199 | Vox | 3/3 | 574.75-685.30s |
| 494 | Nagafen | 3/3 | 654.75-707.45s |
| 494 | Vox | 3/3 | 628.20-666.65s |
| 13,288 (stress) | Nagafen | 3/3 | 195.35-277.70s |
| 13,288 (stress) | Vox | 3/3 | 84.65-128.80s |

Duration includes time to owner death in failed runs. Six requested movement
packets were interrupted by native control; these are recorded separately.
No sampled slow landed despite correct request range, so resistance and
rotation limits still matter.

These remain three-seed strategy comparisons, not win-rate estimates or release
certification. The open-all row is unrestricted stress, not Classic's maximum.
Release-pool comparisons must use this corrected approach for pet builds. Gear acquisition, optimal rotations, pet resummoning,
complete activated-AA usage and full source/client parity remain separate work.

To verify from `tools/balance`:

```powershell
python pet_belly_controls.py --inputs ../../docs/balance/pet-belly-inputs.json --verify ../../docs/balance/pet-belly.json.gz --output ../../docs/balance/pet-belly-checks.json
python -m unittest discover -s tests
```

Build with all four candidate source flags as described in the prior native
controls. Manifests pin the final runtime and unchanged production candidates.
All 65 historical native reports remain byte identical: 30 prior active-support
fights, 12 command/passive-combat controls, 15 ownership controls and eight
caster/monk fights. The focused 217-test suite passes. Clone reagent cleanup
removed only the two verified synthetic inventory rows after the matrices;
clone accounts, characters and inventory are empty.

On eventual test promotion, use level 50 MAG/NEC/SHM with the recorded build in
soldungb against Lord Nagafen 32040 and permafrost against Lady Vox 73057. Cast the
same offensive spell from outside melee range and from inside the dragon's belly;
outside attempts must be fully resisted, while inside attempts use ordinary
resistance checks and can still fail. Verify movement interrupted by fear yields
to native control and returns after control ends. Repeat the recorded AA stages
with combat logs, resource snapshots and the preparation checks from the support
QA. Do not expect identical random outcomes. Main still requires owner sign-off.
