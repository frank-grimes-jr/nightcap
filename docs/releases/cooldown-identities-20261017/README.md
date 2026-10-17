# Cooldown identity correction — October 17 candidate

**Not deployed.** This follows the live Rampage → Purify Body report after the
October 17 duration release. Source starts at deployed main `0eef50e`; retained
zone baseline SHA-256 is `3c1d74926cb7cff032a3ee8c48c210e37740156e7e36cc0eeddd07f847e88d1a`.
The earlier release corrected arithmetic and six Monk skills, but left shared
identities open. This candidate addresses AA identities and cross-domain timer
collisions. Generic basic combat sharing and content-defined spell/discipline
links remain open; this is not complete cooldown independence for every skill.

## Reproduced cause and coverage

Rampage family109/rank258 and Purify Body family98/rank233 both use raw AA group1.
Mass Group Buff, Escape and Ancient Attunement also use it. The old server stored
key1001 and sent native slot1 for all five. This is a shared identity, not a global
cast-recovery delay. Resetting the group also reset its unrelated siblings.

Fresh SELECT-only capture: **2026-10-17 19:59:13 UTC**, SHA-256
`e71d550ac445732e36ba316a86f3a079f76a556835b4120c751deb05c8ba73be`.
It covers1,570 AA definitions/6,655 ranks,18,017 cooldown-related spells and7,798
recast items, with anonymous saved-timer aggregates only. At capture, active saved
group1001 had600s duration/351s remaining; this corroborates the group, not the
identity of the player or originating cast. Active zone memory was not inspected.

Current policy exposes165 ordinary activated AA families. Native-method tests
exercise27,060 ordered distinct-family pairs in activation and another27,060 in
catalog publication: each old path had1,616 aliases; candidate has none.825
within-family rank/expiry cases preserve the shared family clock. The full group
membership is [aa-shared-groups.md](aa-shared-groups.md); every inspected definition
is in [timer-membership.csv](timer-membership.csv). Catalog membership alone does
not prove item ownership or spell access.

## Corrected identities and resets

| Domain | Candidate persistent identity | Client contract |
|---|---|---|
| Activated AA | `0x100000 + ability_id` | Sorted held-class allowed-family projection into0–99; purchases/ranks do not renumber it |
| Unlinked item/augment | `0x200000 + item_id` | Existing item timestamp and packet contract; item IDs above1,048,575 rejected |
| Grouped discipline | `0x300000 + group` | Native groups0–19; all20 reset correctly |
| Ungrouped discipline | `0x400000 + spell_id` | `timer_id=-1`; no invalid group packet |
| Basic skills, Monk, linked spell/item groups | Existing nonoverlapping keys | Existing paired Monk client and native grouped reuse |

`pTimerType` is uint32; keys fit the existing SQL MEDIUMINT UNSIGNED. This prevents
unlinked item IDs wrapping into other items, spells or skills. High discipline
groups formerly overlapped combat, begging and linked-spell keys. Four ungrouped
Thief's Eyes/Thief's Vision definitions formerly used Disarm Traps key13.

RoF2 has exactly100 AA timer slots, not an arbitrary uint32 map. The exact pinned
client packet/getter/setter/readiness routines were executed in a native fixture.
Current three-class combinations need at most57 ordinary activated families.
The server allocates against the full allowed held-class catalog, including
supported toggles, independently of purchases/charges/rank visibility. Overflow
fails closed. Catalog rebuild clears old table entries; resend clears all100
native clocks and reconstructs owned family deadlines. Ranks, class changes,
reconnects and focus changes preserve the server's original expiry.

`SendAlternateAdvancementTimer` now accepts a family ID and performs the slot
translation at the packet boundary. Successful casts, aborted casts, login,
catalog refresh, death reset and administrative reset use the same identity.
Single reset honors its supplied **rank ID** rather than the stale casting member.
`#resetaa_timer 258` now clearly means Rampage's family; `all` clears only AA keys.
Death resets only families whose definition has `reset_on_death`.

Native packet `(begin=0,end=0)` starts a timer; reset is `(0,server_now)`. Resend
uses `begin=now+remaining-effective_reuse`, retaining signed native haste math.
Exactly-zero native effective reuse always reports ready even with a retained
legacy wait; the server still rejects early reuse. Current allowed haste totals
remain below base reuse; the synthetic zero case is explicitly covered, not
claimed as perfect UI synchronization.

## What really resets or starts multiple timers

| Entry point | Scope and remaining behavior |
|---|---|
| AA completion/abort/single reset | One AA family after this correction |
| AA death reset | Only owned families marked reset-on-death |
| `#resetaa_timer all` | Explicit administrative reset of all AA families; excludes items, skills and spells |
| `ResetAllDisciplineTimers` | All20 discipline groups and ungrouped disciplines; excludes other domains |
| Castbar reset by spell/slot | That memorized spell and its content-defined linked group; a negative slot/all reset visits all memorized gems |
| SPA389 `FcTimerRefresh` | Focus-filtered memorized spell clocks and their linked groups; not an AA-global reset |
| SPA390 `FcTimerLockout` | Focus-filtered memorized spell clocks, excluding the spell currently being cast |
| Ordinary proc/trigger completion | Persistent spell reuse remains behind the existing proc/trigger guards |
| Item reset | Explicit item or its declared item reuse group; no cross-domain clears after the key fix |

The earlier15:04 UTC effect capture contains six SPA389 refresh definitions and
three SPA390 Suppression of Ice/Fire/Magic lockouts of2,000ms. Negative SPA310
reuse adjustments intentionally add5/30/10s for Imposition of Order, Mind Collapse
and Venomous Sting. These effects are not evidence of hours-long AA lockouts.
The tracked quest/plugin review found no ordinary universal AA reset caller.

**Still open:** Harmshield/Cannibalize share linked-spell group1, and Battle
Cry/Throw Stone share discipline group8. The inventory also lists the other
content-defined groups. Their native client readiness remains group-based;
changing only a server key would make the UI and enforcement disagree. This
candidate isolates domains and AA families, but leaves that separate spell and
discipline family design unresolved. Linked potion/item groups are also retained.

## Basic combat and utility skills — unchanged membership

The bounded follow-up reviewed tracked source plus retained native server source.
The following sharing is observed implementation, not an approved multiclass
balance policy. Existing skill/class/target authorization still applies.

| Persistent timer | Current membership and evidence |
|---|---|
| `25` (`pTimerCombatAbility`) | Bash/Slam, Backstab, Frenzy and Kick outside the held-Monk RoF2 scope share one clock. `EQ::skills::CombatAbilityTimer` in `server-mods/code/common/combat_ability_timer.h:10` selects it; both `Client::OPCombatAbility` (`special_attacks.cpp:345,424`) and non-riposte `Client::DoClassAttacks` (`special_attacks.cpp:2129`) enforce it. |
| `26` (`pTimerCombatAbility2`) | `Client::Handle_OP_Disarm` (`client_packet.cpp:5710`) uses an eight-second clock. The helper's RoF2 Tiger Claw fallback also selects 26 outside held-Monk scope; that fallback does not establish non-Monk access to Tiger Claw. |
| `27` (`pTimerBeggingPickPocket`) | `Handle_OP_Begging` and `Handle_OP_PickPocket` (`client_packet.cpp:3945,11911`) share eight seconds. |
| `521,523,526,530,538,552` | Held-Monk RoF2 Dragon Punch/Tail Rake, Eagle Strike, Flying Kick, Kick, Round Kick and Tiger Claw respectively. These are `500 + skill`; Tail Rake is the Dragon Punch alias (`common/skills.h:53`). Older clients retain the shared fallback. |
| `3,4,5,6,7,8,9,10,12,13` | Feign Death, Sneak, Hide, Taunt, Intimidation/Instill Doubt, Fishing, Forage, Mend, Sense Traps and Disarm Traps respectively have distinct keys (`common/ptimer.h:30`; named handlers in `client_packet.cpp`). |
| Ranged attack timer | Archery and Throwing return before the combat-ability PTimer gate (`OPCombatAbility`, `special_attacks.cpp:393`). Their attack timing is not evidence of a global skill reset. |

Except where prefixed, source paths in this table are under
`server-mods/code/zone/`. Current source tests explicitly preserve non-Monk
Kick/Bash sharing, old-client Monk sharing, and Bash/Frenzy timer 25. The reviewer
reran all 16 `tools/tests/test_monk_combat_reuse.py` tests successfully. A shared
key means an admitted activation can block a different member until expiry;
these controls preserve scope, not acceptance of the sharing as final behavior.

The pinned RoF2 native submitter (RVA `0x1A5000`) uses two player timer slots via
RVA `0x1BA2B0`: Tiger Claw skill 52 selects slot 1, other submissions slot 0.
SkillManager's combat-type getters/setters/readiness at RVAs
`0x1BAC50`–`0x1BAE40` also share two records. Existing
`eq-client-dll/src/monk_reuse.h::IndependentMonkReuse` intercepts only the six
skills for a matching held-Monk identity. Further basic-attack separation needs
paired client readiness/submission/display work as well as server keys.

No blanket all-domain persistent reset was found reachable from ordinary player
activation in the inspected code. The whole-list `PTimerList::Clear(Database*)`
exists in retained `common/ptimer.cpp:327`, but the tracked and retained zone
callers use its keyed overload. The search covered `p_timers`/`GetPTimers`,
death, named `ResetAll` APIs, GM commands, Perl/Lua bindings and tracked
quests/plugins. Explicit `#resetaa_timer all` and `#resetdisc_timer all` remain
domain-scoped; quest `ResetAllDisciplineTimers`/`ResetAllCastbarCooldowns`
bindings are also domain-scoped, with no call found in tracked quests/plugins.
This is source evidence, not a probe of untracked live scripts. AA, discipline,
castbar and item reset APIs have the scopes above. `Client::Death` additionally
clears classic skill Lay on Hands for
primary Paladins (`zone/attack.cpp:2132`), not generic combat/Monk clocks.
`ui_hooks.h::StateHook` clears only transient Monk client records on leaving the
in-game state; persistent server waits survive. `DoClassAttacks` ripostes bypass
and do not extend reuse. No new universal reset or basic-skill split is introduced.

## Saved timers and release pairing

`tools/cooldown_identity_migration.py` only generates SQL. It never connects to
production. Run forward conversion only with gameplay stopped, fresh stopped
backup, held maintenance fence, and a fresh catalog matching SQL preimage checks.
Use one MariaDB session **without `--force`**. InnoDB/type/trigger/catalog assertions
must pass. Receipt and timer writes commit together; missing receipt makes the
candidate reject zone entry. A timer-load error also disconnects instead of
continuing with empty clocks.

Each ambiguous old AA clock is copied to every possible sibling family, including
unowned/dormant families, preserving original expiry. Item aliases are copied to
all possible items and merged with immediate `character_item_recast` timestamps.
Never shorten an existing deadline. Old low keys remain for unaffected domains;
receipt fencing prevents repeated import. Consequently a pre-release shared wait
can remain until its original expiry. This is not a blanket reset or refund.

Rollback first fences/stops gameplay, then conservatively merges current new
deadlines into old identities and removes **all** namespaced rows atomically.
Unknown new keys abort rollback. Keep the backup tables and receipt evidence.
Never launch the old uint16 binary while new rows remain, and never restore an
old player snapshot. Restoring old code also restores the old collision behavior.

Pair rebuilt zone/common code with this conversion. No new DLL hook, wire layout,
rule catalog or ItemData/cache layout change is needed; keep the deployed0.10.0
client required by the earlier Monk release. Rule/quest reload is insufficient.
Use the controlled whole-runtime deployment process; do not kill one OVH zone.

## Verification and acceptance

Source regression: 16 AA tests; 27 duration/item/discipline tests with 38 scenarios;
29 exact-native RoF2 checks. Baseline reproductions remain recorded as failures,
not candidate passes. The disposable local MariaDB rehearsal passes 15 tests,
including failure after receipt insertion, forward/rollback preservation, catalog drift,
receipt/backup engine and shape guards, item membership drift, duplicate apply
and unknown-key rollback rejection.
The complete native zone target rebuilt and linked successfully from the exact
retained baseline. All eight changed source hashes match the reviewed candidate;
the baseline and candidate sources stayed unchanged during compilation, and
`ldd` found no missing dependencies. Candidate zone SHA-256:
`d3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a`.
See `manifest.json`, `verification.json`, `build-final.txt` and `build-ldd.txt`.
Production was not modified. See `migration-rehearsal.json`, `REVIEW.md` and
[QA.md](QA.md). A compiled fixture/build does not establish
visible gameplay acceptance. Main promotion, migration and live deployment need
the owner's separate release authorization.

## Reproduce the catalog and migration evidence

From the repository root, the compressed capture is a reproducible SELECT-only
fixture. Neither command connects to a database:

```powershell
python tools/audit_cooldown_identities.py docs/releases/cooldown-identities-20261017/catalog-capture.json.gz work/cooldown-inventory
python tools/cooldown_identity_migration.py docs/releases/cooldown-identities-20261017/catalog-capture.json.gz work/cooldown-sql
```

The generator's SQL must still pass a fresh stopped catalog preimage check before
any authorized deployment. Never apply this historical capture blindly. The
retained local build uses `build.py` with `source.patch` and `expected-sources.json`;
`finalize_build.py` records the actual reviewed-source rebuild after superseded
compiles. Both refuse a source delta beyond the eight reviewed files. Build paths
are isolated under `/tmp/nightcap-cooldown-identities-build-v1`; no install occurs.
