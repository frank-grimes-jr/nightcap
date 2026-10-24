# 0071 — Run-scoped High Keep prison break

Status: candidate,2026-10-24; no deployment or owner acceptance.

The current boss checklist does not explain a break-in or provide a rescue. Use a
native coordinator in the existing dungeon service so dialogue, temporary faction,
NPC movement, guard pursuit, checkpoint restoration and reward transactions share
one run identity. Reuse the four objective/boss identities and their loot; move two
boss poses into a continuous entrance-to-prison route only in the new mode.

An additive opt-in run row freezes eligibility at creation. A durable alarm and
extraction receipt survive restart; attempt actors remain ephemeral and return to
the cell after reboot. Player completion updates only at extraction and requires
each participant's existing four personal credits. Existing inventory receipts own
delivery. No new repeatable escort reward or player-faction write is introduced.

Native follow/navigation keeps the player responsible for the route. Three fixed
pursuer pairs prevent skipping combat at the exit; dynamic actors are excluded
before XP/task awards as exp_mod=0 alone does not prevent raid/leadership XP.
Scoped heal/attack hooks make Osargen healable and protect him from player/pet harm.
Failure resets the escort rather than repeating the boss grind.

Consequences: zone/schema must ship together; the enable flag controls new runs.
Once rescue runs exist, old binaries are incompatible with their completion rule.
No world/cache/client change is needed. Static navmesh proof does not establish
actual movement, visible dialogue, balance or owner acceptance; QA.md is the
promotion gate. Public High Keep, Grind and unmarked older runs retain their rules.
