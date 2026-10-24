# Initial escort tuning and acceptance boundary

The existing four High Keep Raid bosses, raid modifiers and earned rewards remain
the combat/progression baseline. This change adds a rescue requirement to the
compact route; it does not substitute a new reward tier or a fourth floor.

Initial escape pressure is three fixed pairs, rather than an endless add farm.
Each pursuer clones the reviewed Captain Bosec base combat profile: level34,
1496HP, AC144, damage41–208, attack delay30 and attack speed-8. It has no spells,
charm escape, flee behavior, loot, faction reward or XP. These are dynamic actors,
so the ordinary spawn-backed raid scaler does not apply. The first pair runs
from the cell-block approach toward Osargen; later pairs block the stairs and
entrance approach. Existing surviving guards can join within line of sight.

Osargen has6000HP, zero native/OOC regeneration, normal native damage handling,
beneficial spell permission and no melee/aggro of his own. Failure preserves the
boss investment and restarts only the escort. The player can protect him through
fast damage, taunt/tanking, crowd control, healing or a combination. The objective
requires clearing each wave; running straight to the exit cannot bypass it.

This establishes a testable initial pressure, not a balance acceptance claim.
Legal AA availability, multiclass damage/sustain, pets, high-quality equipment,
heroics and augments may make the low-HP pursuers brief encounters. Do not call
this maximum-power endgame difficulty. Before main promotion, measure the QA.md
route on a level40 progression build and a maximum legal geared build, recording
classes/level, AA points and ranks, weapons/augments, elapsed wave times, Osargen's
lowest HP and heals/taunts used. Include a no-intervention failure case and a
competent non-healer rescue; the encounter should reward action without requiring
a specific healing class. Adjust only the new actor profile after those results.

Baseline NPC values are from `docs/dungeons/local-content.json`; native behavior
is in `zone/highkeep_rescue.inc`. The coordinator, terrain and navigation tests
do not measure actual attack rolls, skill effects, damage or sustain.
