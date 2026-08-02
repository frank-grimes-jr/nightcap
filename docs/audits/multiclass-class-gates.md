# Multiclass Player Class-Gate Audit

Date started: 2026-07-28
Epic: #10
Status: in progress

## Scope and classification

The source inventory currently contains 581 `GetClass()`, `GetBaseClass()`,
`IsMulticlassMember()`, and `GetMulticlassList()` match lines in zone code.
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
| G002 | `client_packet.cpp:Handle_OP_CastSpell` ability slot | Client only | additive | Authorize Lay on Hands for held Paladin and Harm Touch for held Shadowknight; preserve spell IDs, levels, targets, and independent reuse timers. | Ability authorization/timer tests | Use each ability in all held slots; verify reuse and negative class. | open |
| G003 | `client_packet.cpp:Handle_OP_Hide` | Client only | additive | Grant Rogue evade behavior when Rogue is held and Hide is eligible. | Hide/evade capability test | Evade as secondary/tertiary Rogue and compare stock Rogue. | open |
| G004 | `client_packet.cpp:Handle_OP_Sneak` | Client only | additive presentation | Emit Rogue-specific success/failure feedback for held Rogue; Sneak authorization remains skill-driven. | Packet message selection test | Verify feedback and skill-up in all Rogue slots. | open |
| G005 | `client_packet.cpp:Handle_OP_Shielding` | Client only | additive | Authorize `/shield` for held Warrior at the stock level/rule/timer requirements. | Shield authorization/timer test | Shield as secondary/tertiary Warrior; reject non-held Warrior. | open |
| G006 | `special_attacks.cpp:Client::OPCombatAbility` | Client only | mismatch (manual QA); additive server dispatch, partial | Held-Monk dispatch authorizes the six stock Monk attacks from a positive current-level held-class cap and avoids double-routing Kick. The guarded client patch now exposes the skills, enables their hotbuttons, and routes those six through RoF2's stock `OP_CombatAbility` submitter. Verify activation/reuse/damage in game, then replace the remaining base-class generic Kick and Berserker extra-round gates. | Monk authorization matrix, pinned static integration check, and exact-client activation/reuse signatures; generic Kick/Frenzy dispatch tests remain | Combat Abilities is correctly empty because Monktest has no disciplines. Repeat all six attacks through Actions -> Abilities against the temporary arena dummy; confirm animation, damage, reuse, and single-routing of Kick. | mismatch |
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
| G018 | Shared `Mob` combat gates in `attack.cpp`, `bonuses.cpp`, `effects.cpp`, and `spell_effects.cpp` | Client plus NPC/bot/merc | mixed | Split client capability from NPC class identity at each reachable symbol; never globally replace `Mob::GetClass()`. | Per-symbol client/NPC paired tests | Combat comparison against stock class and NPC controls. | inventory |

## Completion rules

- Every player-reachable lexical gate must map to a row above or a later
  per-symbol row.
- `open`, `verify`, and `inventory` all count as unresolved.
- A row closes only when its implementation and named automated evidence pass.
- Required manual evidence is collected during the `test` promotion spike.
- Epic #10 cannot close until this audit and every acceptance-matrix row contain
  zero unresolved statuses.
