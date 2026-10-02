# Resident campfire correction — October 2, 2026

The owner requested Nalin, Rekk, Sortre, Camil, Trift and Glorphyndel closer
together around a fire, corrected Glorphyndel's race, and reported Nalin's sword
occasionally pointing sideways before recovering. Direct main and OVH deployment
are authorized. This is a follow-up to the installed October 1 social layout.

## Changes

- Six stationary residents form a compact, irregular circle centered at world
  X -274, Y -1707. Diameter shrinks from about 53 to 27 units; they face inward.
- Native `CAMPFIRE`, already in `ecommons_obj.s3d`, uses door 211 / database ID
  999606 at 65% scale. The Misty Thicket template is retained untouched. No client
  asset update, custom texture, damage aura or gameplay effect is added.
- Glorphyndel changes from race 3 (Erudite) to race 5 (High Elf). Full Valorium
  material 3 / RGB 115,135,250, Falchion of the Koada'Vie (IT42) and Trueheart
  Shield (IT202) remain as requested. These are display costumes, not loot.
- Nalin keeps SoulFire (IT62), full Valorium, his hail and social facing. He no
  longer plays nod/wave emotes. His primary skill changes from 1H slash (1) to
  2H slash (3), matching SoulFire's item type. The skill correction affects attack
  animation; it alone is not proof of an idle attachment fix. RoF2's global
  Holding byte remains unchanged. Intermittent self-recovery suggests an emote
  transition problem, but the exact client mechanism is not yet proven.

## Guards and recovery

`tools/tunnel_campfire.py` captures only the six residents' definitions, tints,
one-to-one spawn topology, referenced visual items, native fire template,
reserved fire identity and scoped saved spawns. Only six poses, Glorphyndel's
race, Nalin's primary skill, the new fire and those residents' non-corpse,
instance-zero caches may change. Inventory, economy, rules and other actors are
outside the mutation scope. All row preimages and collision scopes are checked
inside a serializable transaction before writing.

Deployment reuses the reviewed October 1 rollout machinery through the small
adapter in `ops/rollout.py`. It pins the currently running native image, takes
and fully restores a private production backup into an isolated MariaDB,
rehearses exact forward/rollback and drift rejection, and checks preserved
data/runtime hashes before opening the gateway. Only `plugins/tunnel_social.pl`
is installed. The current client publisher and newer loot/pet files are retained.

Rollback must capture fresh state, prove the installed static afterimages,
restore only these six original poses/fields, remove the exact owned fire and
restore the previous plugin. Newly saved resident caches are invalidated;
historical caches are never reinserted. Never restore a whole old production
backup over subsequent player progress. Private deployment evidence belongs at
`/opt/nightcap/releases/tunnel-campfire-evidence-20261002`.

## Validation and exact rendered QA

The complete 119-actor scene is checked against the revised six positions,
existing furniture/stations and all eight walking routes. Outside approaches
remain accessible; minimum resident clearance is 13 units. Native map probing
passes 65 ground samples and six approach rays. Resident quest regression has
28 assertions, including 100 Nalin idle ticks with facing but no emotes.

Rendered acceptance remains open until observed in the installed game:

1. Enter East Commonlands and approach the tunnel circle. EQ `/loc` reports
   Y, X, Z: approximately **-1707, -274, 4**.
2. Confirm all six named residents are standing around one visible, grounded
   small fire with clear space between bodies, flame and weapons. Walk around
   and approach each resident; confirm hails and normal passage remain usable.
3. Inspect Glorphyndel: male High Elf, complete blue/lavender Valorium plate,
   Falchion of the Koada'Vie and Trueheart Shield.
4. Observe Nalin from 25–60 units away for at least four minutes (idle interval
   35–80 seconds). He can face companions but should not nod/wave; SoulFire must
   remain attached correctly. Then zone out/in or reconnect and inspect again.
   Within 20 units, the existing interaction guard suppresses social actions,
   so a close-up alone cannot validate the transition fix.
5. Check the surrounding traders, tradeskill corner and paths for obstruction.

Automated data/geometry/quest checks do not certify the rendered sword or fire.
