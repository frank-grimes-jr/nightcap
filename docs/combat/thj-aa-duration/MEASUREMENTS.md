# Rank-one Rage of Rallos Zek and Bloodlust

At level 50, the candidate faded Rage at 12,000 ms of active time and Bloodlust at 24,000 ms for every combination of tick phase and duration focus tested. The June 12 THJ notes specify both exact durations, independent of duration extension and server tick timing. The baseline was the source at `1880fc55f970fc3ccd27c2a36c6b37da84169578`. The two receipts retain the hashes of the compiled source files and every phase observation. [Baseline](before.json) · [Candidate](after.json)

| Spell and duration focus | Baseline fade after application, ms | Candidate fade after application, ms |
|---|---|---|
| Rage 21773, all four focus inputs | 12,001 / 15,000 / 17,999 | 12,000 / 12,000 / 12,000 |
| Bloodlust 30736, none | 18,001 / 21,000 / 23,999 | 24,000 / 24,000 / 24,000 |
| Bloodlust, Extended Bloodlust +1 tick | 24,001 / 27,000 / 29,999 | 24,000 / 24,000 / 24,000 |
| Bloodlust, +50% | 30,001 / 33,000 / 35,999 | 24,000 / 24,000 / 24,000 |
| Bloodlust, +100% and +2 ticks | 48,001 / 51,000 / 53,999 | 24,000 / 24,000 / 24,000 |

The three timings in each cell correspond to the first zone tick landing 1, 3,000 or 5,999 ms after application. The read-only production capture identified Rage rank 8303 with native formula 3 capped at two ticks and Bloodlust rank 13484 with formula 8 capped at three. Both occupy the short-buff box. Rage already bypassed duration focus via its endurance-based discipline classification. Extended Bloodlust rank 15414 grants one tick specifically to spell 30736. The two percentage cases are synthetic stress inputs. A neighboring ordinary timed spell reproduced all twelve native focus and phase combinations on both versions. [Spell and rank records](../../releases/fixed-aa-duration-20261114/ops/spell-preimages.json)

## Application and lifecycle

- Both spells start their deadlines at successful application. A rejected refresh retained the existing deadline. A successful refresh restarted that spell's full window. An early dispel followed by slot reuse left the replacement untouched. Both AAs could coexist and fade independently.
- Neither managed AA asked the duration-focus subsystem for a bonus, including on a rejected refresh. The first candidate still queried it twice for Bloodlust, which could consume a matching limited-use focus charge. The final candidate passed this regression. Ordinary timed spells still performed both lookups.
- Explicit duration overrides, individual duration edits and bulk duration edits retained the fixed deadline. The ordinary control accepted the bulk edit. NPC applications and new player applications with the behavior rule off used the original timing. An already active managed buff kept its deadline across a rule change.
- At 4,000 ms a saved and restored character retained the remaining deadline. At the original expiry a reconnect restored only the ordinary long buff. Baseline save omitted the AA's short slot. The candidate wrote the managed AA and the ordinary long buff. Other short-slot effects remained subject to native persistence.
- Restored RoF2 effect packets installed the proper slot and displayed the remaining ticks. Their coordinate fields were zero for the managed AAs. An ordinary long buff retained its saved coordinate in the packet. Expiry between load and effect restoration suppressed installation. Corrupt, expired and legacy unmarked rows gave no new time.
- A suspended Bloodlust with 19,000 ms remaining survived a long wait and logout in suspension. Upon loading in an ordinary zone it expired after exactly those 19,000 ms. Rage continued counting down while the zone suspended other buffs. With an 82 ms gap after the deadline, the first subsequent processing frame faded the spell.

## Reproduction and scope

From the checkout, run `python tools/tests/test_fixed_aa_duration.py`. Use `--source /path/to/code --baseline` to measure the pre-change shipping tree, or omit `--baseline` for the candidate. The source directory must contain `zone` and `common`. Add `--receipt path.json` to retain the output. The adjacent AA temporary-buff suite has 21 controls. [Runner](../../../tools/tests/test_fixed_aa_duration.py) · [Fixture](../../../tools/tests/fixed_aa_duration_fixture.cpp) · [Adjacent suite](../../../tools/tests/test_aa_temporary_buffs.py)

The runner compiles the original duration formulas, `AddBuff`, client slot selection, buff tick and deadline processing, save/load methods, RoF2 restore and duration-packet construction, and duration-edit methods. Synthetic inputs supply time, focus results, stacking verdicts, the row repository, and packet transport. Native processing frames are scheduled at 1 ms for phase measurements. A separate control skips a deadline to test normal frame granularity. The fixture intercepts `BuffFadeBySlot` and observes removal of the buff slot. Combat proc frequency, real network delivery and human observations of the RoF2 UI remain player QA. [In-game checks](QA.md)
