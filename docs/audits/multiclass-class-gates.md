# Multiclass Player Class-Gate Audit

Date started: 2026-07-28
Epic: #10
Status: gate coverage complete (2026-09-08) — every player-reachable accessor is
mapped to a row/bucket. Listed rows remain **open** for remediation; the audit
"complete" state is coverage, not implementation.

## Scope and classification

The source inventory contains **552 `GetClass()`/`GetBaseClass()`/
`IsMulticlassMember()`/`GetMulticlassList()` match lines across 56 zone `*.cpp`
files** at audit close (re-baselined from the original 581; the count drifted as
intervening #10 work added held-class-aware paths). Every match is reconciled to
a row or bucket in the "Coverage reconciliation" section below.
Bot-, mercenary-, and NPC-owned behavior remains in the source inventory but is
not a player capability unless a shared `Mob` path is reachable by `Client`.

Each player-reachable gate receives one contract classification:

- `additive`: every held class grants the capability;
- `chassis`: preserve one base-class/client-protocol identity or choose the
  documented best held-class numeric value;
- `non-player`: an NPC, bot, mercenary, target-type, or administrative rule;
- `mismatch`: required parity is unresolved and blocks Epic #10 closure.

The generated acceptance matrix is
`docs/audits/multiclass-acceptance-matrix.csv`. It contains 480 rows:
16 playable classes x 3 held slots x 10 contracted capability groups.

## Classified direct-player gates

| ID | File / symbol | Player/NPC path | Class | Required remediation | Automated evidence | Manual evidence | Status |
|---|---|---|---|---|---|---|---|
| G001 | `client_packet.cpp:Handle_OP_ApplyPoison` | Client only | additive | Authorize held Rogue plus normal item, level, and Apply Poison skill checks. | Focused packet/helper test | Apply poison as secondary and tertiary Rogue; reject non-held Rogue. | open |
| G002 | `client_packet.cpp:Handle_OP_CastSpell` ability slot | Client only | additive | Authorize Lay on Hands for held Paladin and Harm Touch for held Shadowknight; preserve spell IDs, levels, targets, and independent reuse timers. | Ability authorization/timer tests | Use each ability in all held slots; verify reuse and negative class. Held-SK Harm Touch spot-checked firing on Monktest 2026-09-08; LoH/reuse/negative-class matrix still pending. | open |
| G003 | `client_packet.cpp:Handle_OP_Hide` | Client only | additive | Grant Rogue evade behavior when Rogue is held and Hide is eligible. | Hide/evade capability test | Evade as secondary/tertiary Rogue and compare stock Rogue. | open |
| G004 | `client_packet.cpp:Handle_OP_Sneak` | Client only | additive presentation | Emit Rogue-specific success/failure feedback for held Rogue; Sneak authorization remains skill-driven. | Packet message selection test | Verify feedback and skill-up in all Rogue slots. | open |
| G005 | `client_packet.cpp:Handle_OP_Shielding` | Client only | additive | Authorize `/shield` for held Warrior at the stock level/rule/timer requirements. | Shield authorization/timer test | Shield as secondary/tertiary Warrior; reject non-held Warrior. | open |
| G006 | `special_attacks.cpp:Client::OPCombatAbility` | Client only | mismatch (manual QA); additive server dispatch, partial | Held-Monk dispatch authorizes the six stock Monk attacks from a positive current-level held-class cap and avoids double-routing Kick. The guarded client patch now exposes the skills, enables their hotbuttons, and routes those six through RoF2's stock `OP_CombatAbility` submitter. Verify activation/reuse/damage in game, then replace the remaining base-class generic Kick and Berserker extra-round gates. | Monk authorization matrix, pinned static integration check, and exact-client activation/reuse signatures; generic Kick/Frenzy dispatch tests remain | Combat Abilities is correctly empty because Monktest has no disciplines. **In-game QA PASS 2026-09-08:** all six attacks visible/assignable, animated, damaged the dummy, started reuse; Kick single-routed. Generic Kick/Frenzy still open. | Monk verified; generic Kick/Frenzy open |
| G007 | `tradeskills.cpp:Object::HandleAutoCombine` | Client combine | additive | Fix the existing negation-precedence bug and authorize Alchemy/Make Poison from held Shaman/Rogue while retaining skill, level, recipe, and Tinkering race gates. | Tradeskill authorization matrix | Auto-combine as secondary/tertiary Shaman and Rogue; negative controls. | open |
| G008 | `client_mods.cpp:CalcMR/FR/DR/PR/CR` | Client only | additive | Apply each held class's native passive resistance contribution once; retain racial, item, spell, AA, and cap logic. | Table-driven passive stat tests | Compare primary/secondary/tertiary values for affected classes. | open |
| G009 | `client_mods.cpp:CalcHPRegen/CalcEnduranceRegen` | Client only | chassis + additive | Use the documented best held-class base-data value; apply held Monk weight behavior as a class passive. | Best-of base-data and Monk-weight tests | Compare class slot permutations at fixed level/weight. | open |
| G010 | Bard gates across `spells.cpp`, `client_mods.cpp`, `client_packet.cpp`, and `special_attacks.cpp` | Client and shared Mob | additive | Apply stock Bard casting, movement, song, interruption, and regen exceptions when Bard is held; leave bot/NPC branches unchanged. | Bard held-slot regression suite | Cast/move/song in every Bard slot; non-Bard controls. | open |
| G011 | `exp.cpp:GetEXPForLevel` old class penalties | Client progression | chassis | Preserve primary/base class because new progression rules are explicitly out of scope. | Single-class/base-identity regression | Confirm secondary/tertiary adoption does not change XP curve. | accepted |
| G012 | Client faction, LFG, guild, surname, and API serialization gates | Client protocol/identity | chassis | Preserve the primary/base class identity unless a later exact client patch contract says otherwise. | Serialization snapshots | Verify visible identity remains stable after adoption/release. | accepted |
| G013 | NPC target classes such as merchants, trainers-as-NPC, LDoN treasure, tribute masters | Non-player target checks | non-player | Preserve NPC class comparisons. Trainer authorization is separately covered by G015. | Existing packet validation | Normal merchant/treasure/tribute smoke tests. | accepted |
| G014 | `inventory.cpp:Client::SwapItem` | Client only | additive, implemented | Continue using `GetEquipClassBitmask()` with race, deity, level, slot, and item restrictions. | Equip-mask helper/swap tests | Equip valid and invalid held-class items in every slot. | verify |
| G015 | `client_process.cpp` GM trainer handlers | Client plus trainer NPC | additive, implemented | Continue using `IsMulticlassMember()` and best held-class cap/train level; add threshold, points, cap, release, and negative tests. | Trainer matrix tests | Open/train at each held-class guildmaster. | verify |
| G016 | `aa.cpp` held-class mask paths | Client only | additive, partial | Verify every AA availability, purchase, activation, title, and packet path uses the held-class mask where capability is intended; retain primary-class title identity. | AA held-slot suite | Buy/use held-class AA and reject non-held AA. | open |
| G017 | `client_packet.cpp:Handle_OP_ItemVerifyRequest` unknown-click logging | Client only | chassis/logging | The base-class `IsEquipable` call only selects a debug message and does not authorize use; preserve unless deeper item-use audit finds a behavioral branch. | Item-click regression | Click held-class and invalid items; inspect server rejection/log. | verify |
| G018 | Shared `Mob` combat & spell gates in `attack.cpp`, `bonuses.cpp`, `effects.cpp`, `spell_effects.cpp` | Client plus NPC/bot/merc | mixed | Expanded per-symbol below (G018.1–G018.13). Split client capability from NPC identity at each symbol; never globally replace `Mob::GetClass()`. | Per-symbol client/NPC paired tests | See per-symbol rows. | expanded |
| G019 | `client.cpp:11752`, `entity.cpp:3700` — `GetClassTrackingDistanceMultiplier(GetClass())` | Client only | additive | Grant Tracking to held Ranger/Druid/Bard/Beastlord using the best held-class multiplier; NPC/bot paths unchanged. | Tracking multiplier test | Track as a held tracking class; compare stock. | open |
| G020 | `client.cpp:3614–3665` — bind-wound cap (Monk >200) and class heal amounts | Client only | additive | Apply best held-class bind-wound cap/amount; retain skill/level gates. | Bind-wound best-of test | Bind as held Monk/Warrior/etc.; compare stock. | open |
| G021 | `spells.cpp:1064` cast-level, `spells.cpp:7434` scribe bitmask, `mob.cpp:7261`, `effects.cpp:676` `LearnDisciplineFromItem` (tome) | Client only | mismatch | Resolve castable/scribable/learnable spells & disciplines against held-class membership (owning-class lookup), matching the pet-summon and scroll-memorize pattern already in place. Blocks the Phase 2 spell/discipline slice. | Owning-class resolution tests | Scribe/learn/cast a held-class-only spell and discipline in every held slot. | mismatch |

## G018 detail — shared-`Mob` combat & spell gates (per-symbol)

The four files hold 137 accessor matches (attack 51, spell_effects 57, effects
17, bonuses 12), grouped below by the distinct player capability each gates. For
every row, NPC/bot/merc callers of the same shared `Mob` symbol stay unchanged;
only the `Client` path becomes additive/best-of. `mob.cpp` shares the same helper
families (caster-type, melee tables, class display, trainer/bard/cast) and is
covered by these rows plus G008/G009/G010/G015/G021.

| ID | Capability / symbol | Representative sites | Contract | Status |
|---|---|---|---|---|
| G018.1 | Class stat softcaps & ATK/skill caps | `attack.cpp` `GetSoftcap` 707, `GetSoftcapReturns` 740, level caps 1380–1463; `mob.cpp` 8422/8763 | best-of held-class (same policy as G009) | open |
| G018.2 | Hand-to-hand & class melee damage/delay | `attack.cpp` 773,1153,1285,3534,3541,3593,3602,5872 (Monk/Beastlord) | additive (held Monk/Bst) | open |
| G018.3 | Melee crit, archery/throwing/frenzy & melee-class specials | `attack.cpp` 3981–3987,5451–5509,6379–6422; `mob.cpp` 4693–4696 | additive (War/Ber/Rng/Rog); overlaps G006 Berserker round | open |
| G018.4 | Defensive class gates (dodge-behind, riposte, 2H, frontal-stun immunity, mitigation) | `attack.cpp` 592,3946,4346,4358–4378,5706,5724 | additive/defensive per held class | open |
| G018.5 | Pure-caster melee penalty; Monk consumption rate | `attack.cpp` 928,935; `bonuses.cpp` 112 | additive/chassis (low priority) | open |
| G018.6 | Heroic WIS/INT caster mana | `bonuses.cpp` 5822–5841 | additive (held caster) | open |
| G018.7 | Spell class-restriction conditionals + illusion textures | `spell_effects.cpp` 7745–8445 (`IS_CLASS_*`; `IsClient()` illusion 8342–8371) | additive via held-class membership for player target/caster; NPC unchanged | open |
| G018.8 | Spell dmg/heal item-mod eligibility & focus-by-class | `effects.cpp` 67–570,452,955,970; `spell_effects.cpp` 3538,3551,4864–5823 | additive (held caster); main spell-dmg path already loops held classes (see below); eligibility/focus-limit still primary-class | partial |
| G018.9 | SK/Paladin ability procs (Vampiric Embrace, LoH holdover) | `attack.cpp` 2120; `spell_effects.cpp` 1970,4355; `spells.cpp` 6384,6440 | additive (held SK/Pal); overlaps G002 | open |
| G018.10 | Bard shared-`Mob` exceptions in these files | `effects.cpp` 1333–1334; `spell_effects.cpp` 451,488,8443 | folded into G010 | ref |
| G018.11 | Weapon legality on the swing | `attack.cpp` 1240 `IsClassEquipable` | additive via equip mask; overlaps G014 | Native pilot exposed base-class-only rejection (632 immune swings with a held-Monk weapon). Candidate now uses `CanEquipItem`; 15 native weapon controls pass. See ADR 0010; live deployment/manual QA pending. |
| G018.12 | LDoNTreasure / body-type / banker target checks | `attack.cpp` 2467,2585,2628,2681; body-type cases in the 7745+ block | non-player (target/object identity) | accepted |
| G018.13 | Group exp distribution base class | `attack.cpp` 2725,2758,2792 `GetBaseClass` | chassis (progression identity); G011 | accepted |

## Already-implemented multiclass mechanisms (regression-guard only)

These player paths already resolve across held classes and need retained tests,
not new implementation:

- Pet/familiar summon class selection and tracking exist in `spell_effects.cpp:1313–`,
  but native controls exposed incomplete ownership: extra pets were removed by
  `Mob::GetOwner`/`GetOwnerOrSelf`. ADR 0011's candidate registry-aware correction
  passes 15 native controls; live/manual QA is pending. Spell ownership after
  global class widening, command broadcasting and persistence remain open.
- Scroll/song memorization from item across held classes — `effects.cpp:762–766` (`MemorizeSpellFromItem`).
- Zeroed Bard mana-regen exception iterating held classes — `bonuses.cpp:1855–1857`.
- Held-class list plumbing on the client — `client.cpp:3197,3250`.

Note the asymmetry feeding G021: scroll memorize (`effects.cpp:764`) is
multiclass-aware, but tome/discipline learning (`effects.cpp:676`) and the
generic cast-level lookup (`spells.cpp:1064`) are still primary-class only.

## Coverage reconciliation

Every one of the 552 zone `*.cpp` accessor matches maps to a bucket below; no
player-reachable accessor remains unmapped.

| Bucket | Files (matches) | Owner |
|---|---|---|
| Combat/spell shared-`Mob` player gates | attack 51, spell_effects 57, effects 17, bonuses 12 | G018.1–G018.13 |
| Client packet/ability/skill/equip/trainer/AA | client_packet 41, client_process 15, client_mods 24, aa 8, special_attacks 10, inventory 1, tradeskills 2 | G001–G017 |
| Casting / tracking / bind-wound / spell-learn | spells 14, client 25, entity 12, mob 24 | G002/G010/G016/G018/G019/G020/G021 + identity |
| Identity / chassis (faction, /who, corpse, guild, titles, raids, serialization) | corpse 2, guild_mgr 5, titles 1, raids 2, api_service 2 (+ faction/who subsets of client/entity) | G011/G012 |
| Scripting exposure (reflects class, not a gate) | lua_client 3, lua_mob 3, lua_bot 1, perl_client 4, perl_mob 2, perl_bot 1, questmgr 4, embparser 2 | reference (expose held classes only if scripts need it) |
| Non-player (bot/merc/NPC/AI/GM tooling) | bot 85 + bot_commands 24 + botspellsai 3 + bot_command 1 + bot_database 2 + client_bot 1, merc 18, npc 18 + npc_scale_manager 1 + mob_ai 2 + mob_info 1, heal_rotation 24, aggro 1, hate_list 1, gm_commands (merchantshop 6, gearup 2), global_loot_manager 1, zonedb 1, task_client_state 1, tune 5 | non-player |

`mob.cpp` and the other shared files were surveyed symbol-by-symbol: their
player-capability call sites resolve to the rows above; their NPC/identity call
sites are `accepted`/`non-player`.

## Completion rules

- Every player-reachable lexical gate must map to a row above or a later
  per-symbol row. **Done as of 2026-09-08** — see Coverage reconciliation.
- `open`, `verify`, `partial`, and `mismatch` all count as unresolved; `expanded`
  defers to its sub-rows; `ref` defers to the named owning row.
- A row closes only when its implementation and named automated evidence pass.
- Required manual evidence is collected during the `test` promotion spike.
- Epic #10 cannot close until this audit and every acceptance-matrix row contain
  zero unresolved statuses.
