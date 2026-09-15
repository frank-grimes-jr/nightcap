# Native spell actions for the balance model

Date: 2026-09-12. Status: direct action samples and simulator integration verified;
full BiS, activated-AA combat, and complete boss fights remain incomplete.

The isolated native harness now resolves direct spell actions for the 24 AA
candidate scenarios. It constructs the captured Vox/Nagafen NPC types without
registering them in EntityList or running AI. Each of 120 actions has 4,096
samples: 491,520 in total. An independent same-seed run produced byte-identical
output. A different-seed control changed three stochastic action histograms.

## What the samples include

Each sample keeps final effect amount, mana cost, cast time, and landed percentage
together. The path calls native cast-time focus, immunity/resist checks, effect
formula/base focus, direct damage/healing focus and crits, then mana-cost focus
and specialization. Partial resists reduce the base before the native damage
calculation; applying another percentage to the final amount would be wrong.
Casters start with full HP/mana, maximum trained held-class skills under the
documented specialization policy, their exact candidate items/AAs, and no active
buffs. Outputs record resource state. Damage is measured before `Damage`, healing
before `HealDamage`; actual damage mitigation, HP clamping and overheal are not
performed by this probe.

The explicit roster covers Ice Comet, Conflagration, Superior Healing, Complete
Heal, Retribution, Blizzard Blast, Shock of Swords, and Greater Healing as assigned
in `native_spell_inputs.py`. The harness checks held-class level entries and
rejects unsupported effect/target shapes. These are single-target, single-effect,
instant-duration CurrentHP probes, not a complete spellbook or optimal rotation.
The actual database has globally patched spell class entries from multiclass
adoption. Those entries alone do not establish canonical ownership or acquisition.

## Observed AA differences

WAR/CLR/WIZ, existing Ascended candidate set, `balanced` finite-budget policy:

| AA stage | Ice Comet mean vs Nagafen | Mana | Conflagration mean vs Vox | Mana | Superior Healing mean |
|---|---:|---:|---:|---:|---:|
| 0 | 2,024 | 179 | 2,255 | 220 | 2,100 |
| 100 | 2,556 | 175 | 2,848 | 215 | 2,168 |
| 200 | 2,648 | 159 | 2,950 | 195 | 2,364 |
| 500 | 3,547 | 149 | 3,952 | 183 | 2,556 |
| All purchasable | 5,671 | 149 | 6,298 | 183 | 3,474 |

Damage means include full resists, partial resists, and crits. Healing is unclamped
potential healing, not effective healing. Each row has the exact spend recorded
in `native-aa-stats.md`. The direct nuke cast time is 5 seconds through the finite
stages and 4 seconds at all purchasable AAs. Complete Heal, represented as a
7,500-base CurrentHP effect in this data, produces 26,250 potential healing at
zero spent points with the current 250 item cap; this is not evidence of useful
healing throughput during an interruptible 10-second cast.

All 4,096 Ice Comet samples against Vox fully resisted at each tested AA stage.
The raw native report and summary retain counts and Monte Carlo standard errors.
For example, zero/all Ice Comet mean standard errors against Nagafen are about
17.5/55.6 HP. Sampling errors do not account for missing fight mechanics, client
limitations, active effects, or different gear/rotation choices.

## Reproducibility and event integration

The diagnostic link uses GNU `--wrap` for libstdc++'s
`std::random_device::_M_getval`. With `NIGHTCAP_BALANCE_RNG_SEED`, it supplies only
the seed; the native EQ::Random engine and distributions remain unchanged.
Without that environment variable, the wrapper calls the real random device.
This is confined to the diagnostic executable. No production source, header,
binary, RNG implementation, live process, or database setting was changed.
The build manifest records the link arguments, random header, reused objects,
and executable. This hook is specific to the pinned GNU runtime, not a portable
cross-compiler replay guarantee. Each action reseeds before sampling; comparisons
must not assume branch-dependent random draws stay paired across AA allocations.

`native_spell_actions.py` validates complete input/action coverage, histogram
counts, seed-hook execution, and full resource state. `Action.resolved_outcomes`
preserves each joint sample in the event engine. It uses the raw mana requirement
to start a normal spell and the sampled cost at completion, capped by available
mana. Interrupted casts spend no completion mana. Sampled amounts are not resisted
or crit-scaled again. Callers must supply the effective cooldown/recovery policy;
the adapter does not silently treat raw spell reuse as resolved reuse.

Two 2,000-trial inert-target controls check the integration independently against
exact weighted damage expectations and cast/resource accounting. Zero-AA casts
nine times in 60 seconds under the control's 1.5-second recovery; all-AA casts
eleven times. Both have exact mana/cast accounting. Observed mean damage differs
from expectation by 0.104 and -0.557 standard errors. These controls use artificial
resource pools and an inert target: they are not boss fights.

114 Python tests pass. The native run also retains all 7,868 accepted AA purchase
steps, 24 matching HP/mana pairs, seven early isolation refusals, and empty cloned
player/account tables.

## Evidence and remaining work

- `native-spell-inputs.json`, `native-spell-samples.json`, `native-spell-summary.json`:
  exact inputs, all joint histograms, and sampling summaries.
- `native-spell-replay-check.json`: complete same-seed byte identity and different
  seed control. `native-action-control.json`: event integration expectations/results.
- `native-spell-aa-check.json`, `native-spell-resources-check.json`, and
  `native-spell-guard-check.json`: AA/resource and isolation checks.
- `native-spell-build-manifest.json`, `native-spell-runtime-manifest.json`: binary,
  object, input/output, and cache provenance.

Complete casting still requires fizzle/interruption, item and AA triggers,
twincast, HP-to-mana conversion, buffs and their counters, effective reuse,
DoTs/HoTs, pets, weapons, and actual boss AI/breath/fear/healing behavior. Birth
class remains important: the WAR-base diagnostic profiles do not establish that
an unmodified RoF2 client exposes spell gems. Final playable profiles must use a
working client chassis or a verified override. No cap or NPC HP recommendation
follows from these direct-action measurements alone.

The next integration should evaluate accelerated native combat to avoid duplicating
stateful engine behavior. Source inspection found the engine timer's millisecond
`current_time` state and `Timer::RollForward`, but persistent AA/spell timers read
`gettimeofday` separately. Any accelerated runner must keep both clocks aligned,
validate the mock-client/EntityList lifecycle, and exercise NPC AI and buff ticks;
advancing one clock alone would produce incorrect cooldown evidence. The Python
event controls remain useful for independent arithmetic and scheduling checks.
