# WPM melee and pet integration candidate

**Current status:** This dated component candidate was integrated into the owner-authorized
[combined THJ release](../thj-parity-20261018/deployment/README.md), deployed October18
with signed client2026101802. Its separate level65/PoP profile remains staged.
Use the combined evidence and QA; older component-only measurements are historical.


This release completes the Warrior/Paladin/Monk implementation alongside the
existing [pet candidate](../thj-pet-scaling-20261018/IMPLEMENTATION.md). It is an
**undeployed candidate** on `feature/thj-pet-scaling`, based on `a8e0a91`.
Production remains Classic/50. No production inventory, AA ownership, cooldown,
runtime, signed client, or public wiki was changed.

The combined 134-test regression suite passes without skips. Native AA checks
pass 6,960 eligibility cases, eight client-expansion boundaries, nine projections
and three restored-earned-rank cases. The paired world/zone/cache-loader build
and all26 native scenarios pass, with eleven mechanics assertions across six
stat/shield-swap probes and20 encounters. [Recorded comparisons](COMPARISON.md)
include DPS, healing, rune absorption, proc activity and resources. Automated
evidence does not establish visible client acceptance or final balance.

## Implemented melee contract

| Component | Candidate behavior |
|---|---|
| Held classes | Best held-class AC softcap/returns and class/race AC; Warrior mitigation and critical eligibility; Monk weapon damage table, rear dodge and riposte Kick; best held-class double/triple attack eligibility. Identity is unchanged. |
| Monk attacks | Six independently timed attacks use Way of Steel. Remove the duplicate initial automated strike; native Master Wu extra attacks remain. |
| Shield Specialist | Five earned ranks, 20/40/60/80/100% native shield-equipped damage modifier, available to Warrior or Paladin. |
| Way of Steel | Two ranks add 100/200 native skill damage to Kick, Round Kick, Tiger Claw, Eagle Strike, Dragon Punch and Flying Kick; native Fists of Fury proc modifiers 30/60. No added weapon-skill damage from this AA. |
| Holy Shield | New Paladin family 30200/rank 43210, costing nine points and requiring earned Shield Block. While a shield is equipped: native proc bonuses and self-rune proc 42840. Warrior family 914 is preserved. Removing the shield removes AA contributions on bonus refresh. |
| Healing Light / Blessing of Life | Three earned ranks each. Healing Light uses stun-triggered native focus groups; Blessing of Life uses native self-heal combat procs. |
| Remaining AA depth | Rage of Rallos rank one with 60-second base reuse; Flurry 12, Rapid Strikes 10, Veteran's Wrath 6. Obsolete Combat Fury prerequisite edges point to the active earned family without granting or doubling benefits. |
| Heroic STR | Optional player weapon-hit multiplier behind `Combat:NightcapHeroicMeleeScaling`. Integral 1% per point through 100, then marginal decrease of 0.0055 to a one-third-percent floor. Retains native flat damage and shield AC. Excludes pets, spells, runes, ranged, Bash and Monk specials. |
| Proc composition | Player and eligible permanent-pet innate weapon procs and all six augment sockets attempt independently. Hostile NPCs retain their native one-proc policy. AA skill-proc traversal respects the actual active rank and skill limits. |
| Received healing | Marr's shield adds 10% once to received `HealDamage` healing and successful Mend, before missing-HP clamping. It does not amplify runes or regeneration. |

The final shared policy contains **1,160 ranks in 408 families**, including the
pet additions. All permitted ranks remain purchasable at level one. Costs,
prerequisites, held-class eligibility, existing earned ranks, charges and saved
deadlines are preserved. Content SQL never rewrites character ownership.

For policy-approved post-RoF2 ranks such as Companion's Fury IV, the native
expansion check accepts a fully enabled RoF2 client profile when client-based
expansion settings are enabled. Partial/zero profiles, other clients, current-era
restrictions and ranks outside the compiled policy remain restricted. No stored
expansion masks or AA expansion metadata are widened.

## Items, spells and acquisition

`tools/wpm_content.py` generates 12 new item definitions, 12 nonlearnable spell
definitions and 20 changes to existing item definitions, across four qualities.

| Item | Implementation / earned source |
|---|---|
| Hopebringer / Cloak of the Black Wind | Sympathetic healing VII/VI respectively. Positive-mana, beneficial instant current-HP spells, in disjoint native casting-level bands 61–65 / 50–60. Native focuses roll individually and choose one successful result; zero-mana proc heals cannot recurse. |
| Diaku Armor Fragment | Worn weapon-proc effect, including when socketed in a shield; retained type 7/8 sockets and level 65 requirement. Worn-proc contribution is cleared when unequipped. |
| Aegis of Altruism / Shield of Strife | Second combat socket, preserving existing cosmetic socket and original stats/weapon ratios. |
| Bloodfrenzy Core, base ID 180620 | New power-source item retaining the selected Bloodfrenzy stats and riposte skill modifier; the original weapon is unchanged. Earned from Cursed's existing loot table. |
| Marr's shield, base ID 180621 | Shield stats, 68% item haste, received-healing marker and extra combat socket. Earned from Tallon Zek. |
| Hastened Fragment of Truth, base ID 180622 | Weapon augment: 12-second Hundred Hands proc at -100/-175/-250/-338 by quality. Earned from Seru, independently of the pet candidate's healing/runic fragment drop. |

Each new family has one weighted quality drop (60/30/8/2); original boss loot
is retained. Exact boss ID, level and loot-table identities are guarded. The
new IDs include +200000/+400000/+600000 quality variants. All fit RoF2's item
link range. New rewards have zero merchant value. Owned definitions and socket
metadata remain on acquisition rollback.

Holy Shield's base rune is 230; native Fists of Fury uses -338 Hundred Hands and
the native 400ms floor. These and the heroic curve are explicit Nightcap
calibrations, not claims of recovered THJ engine formulas. The separate THJ
comparison's proposed additive spell-damage policy is outside this WPM contract;
the existing Nightcap percentage helper remains shared with the pet work.

## Shared pet work preserved

The same binaries include 22 equipment locations with 15 Mage / eight other
permanent-pet item capacity; full-instance and augment preservation; temporary
hand-in compatibility; own item SD/HA plus bounded half-owner inheritance;
750 player base caps; eligible earned caster-AA transfer; Healing Amount rune
scaling; direct pet healing and roster buffs; coexisting support lines and
bounded Doppelganger spell assistance. Rabid Bear's benefit and illusion are
separate permanent, independently removable effects with normal death behavior.
The catalog calls this AA **Rabid Bear**, rather than “Rabid Pair.”

The Seru migrations compose in either retry order: each accepts the exact
reviewed companion acquisition link without creating or deleting it. Both
migrations replay twice successfully in the dedicated synthetic database.

## Verification and evidence

- `evidence/regression.json` / `.log`: 134 tests pass, zero skips. Includes real
  native-method compilation and MariaDB temporary-table migration rehearsals.
- `evidence/aa-native.json`: full earned-policy eligibility/projection controls.
- `evidence/native-comparison.json`, `native-results.tar.gz`: all26 cases and
  checked effect/AA/equipment records; `analyze_native.py` reproduces assertions.
- `evidence/native-pairing.json`: source, paired binary and all144 diagnostic
  object/library fingerprints verified without installation.
- `PLAN.md`: original implementation contract and deliberate deviations.
- `content/`: exact guarded AA/item/rule afterimages and acquisition rollback.
- `build.py`, `stage_native.py`, `refresh_build.py`: isolated retained-source
  pairing, input/output hashes and dynamic-library checks; no installation.
- `make_matrix.py`, `run_matrix.py`, `tools/balance/native_*.cpp`: explicit
  synthetic identities, gear, native AA purchase gates and seeded encounter
  controllers. The diagnostic has no world connection or auto DB updates.

Native comparisons pass. Stat/swap probes cover all six WPM class orders;
Warrior-first encounters cover shield/dual/two-hand, living/controlled-undead,
Classic50/level65 and zero/max-earned AA stages, heroic-rule off, equipped/bare
pets and a caster control. Fixed native controllers and captured gear are
diagnostics, not optimal-play simulations or statistical balance certification.

Independent review found no blocking production-code issues in the reviewed
WPM changes. Follow-up review identified and resolved diagnostic Rage allowlist
and legacy cooldown-key errors. Healing ledgers explicitly exclude regeneration
and direct-SetHP Mend; Mend request/pulse state is recorded separately.
Native runs also caught two class-ineligible fixture items, a weapon-only Runic
Fragment placed in a shield, and the RoF2 expansion ceiling blocking an approved
pet rank. Gear fixtures were corrected without weakening equipment rules; the
narrow AA compatibility fix passed independent review and the real native gate.

## Release and gameplay gate

Follow [ACTIVATION.md](ACTIVATION.md). The matching client delta contains proxy
0.11.0, Inventory/Pet Info XML, `spells_us.txt` and `dbstr_us.txt`. It is staged,
unsigned and uninstalled. Preserve all current signed-base assets, including
the October18 travel repair. Never edit the protected reference client.

Owner gameplay acceptance is still required: visible six-attack reuse and AA
labels; shield swapping during combat; actual augment/item proc effects and
nonrecursive sustain; all class orders; pet equipment transfer, death, zoning,
camping, suspension and resummoning; independent Rabid benefit/illusion removal;
earned acquisition and PoP access. No main promotion, production deployment or
wiki publication is implied by this implementation work.
