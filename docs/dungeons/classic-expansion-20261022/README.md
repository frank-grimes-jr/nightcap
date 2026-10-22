# Every Classic dungeon — candidate, October 22

**Reward follow-up:** [Unique Classic raid rewards](../classic-rewards-20261022/README.md)
supersedes this earlier candidate's shared-item fallback and zone-only pairing.
Its414 MAGIC definitions require matching world/zone/shared_memory and regenerated
item caches. The historical330-item compatibility/build/rehearsal receipts below
retain their original scope; use the reward follow-up for the combined candidate.

The owner requested the same Raid, Grind, Enter, Join, Status, Claim Rewards
and Reset choices in every Classic dungeon, explicitly including Fear, Hate
and Sky. This candidate covers 21 combat dungeon zones with 147 objectives and
42 journals. It is **not deployed or owner accepted**. [Exact QA](QA.md) owns
the remaining gameplay checks. Existing live releases and their acceptance
remain distinct.

## Behavior and compatibility

The original seven dungeon indices, 52 objectives, tasks 9700–9713 and revision
2026101601 stay exact. No existing item definition, player, run, deadline,
earned reward, credit or loot receipt is rewritten. The additional zones append
indices 7–20 and tasks 9714–9741. Existing legacy instances retain their old flow.
The shared Instance Keeper quest already delegates these operations to native
authorization; the catalog and entrance service definitions extend its reach.

Runs retain twelve hours, six participants, personal encounter credit and fixed
mode. Raid retains135% HP/115% outgoing damage, permanent deaths and final-boss
unlock. Grind retains ordinary stats and native spawn timers except four
script-only Sky bosses, which receive durable eight-hour canonical timers.
The Sky princess retains four hours. Added finals reuse existing band saber,
signet and field-satchel designs with existing Raid quantity/quality rolls;
the original seven keep their exclusive designs. All330 reward definitions
remain exact. This does not establish solo balance, especially in the planes.

The selected content is the current native population, **not a historical era
restoration**. In particular, the Hole keeps its currently installed named
population. The existing private Classic Cazic-Thule restoration remains exact.
Cities, outdoor zones and service temples are outside the combat-dungeon list.

## Screenshot error

A read-only production capture reproduced39 passing schema checks and41 failed
old item-batch predicates. The native contract still described pre-October 18
budgets, while every current item compiler field matched all 330 production
definitions. Refreshing only item guards made all 252 original content checks
pass against production. The new expanded contract additionally requires its
additive migration and therefore is not expected to pass the unchanged live DB.
See [diagnosis.json](diagnosis.json). No production item or cache was rewritten.
The repair remains a candidate until the paired native release is installed.

## Planes and durable keys

Fear's managed Cazic-Thule callbacks cannot toggle public instance-zero spawn
conditions. Sky globals use validated native run UUIDs through the new
`eq.get_dungeon_run_id()` binding and `nightcap_dungeons` Lua module. The identity
remains scoped even after expiry or suspension; it never falls back to public
behavior merely because a run is unhealthy.

Five canonical private Sky boss points replace script-only/gated objectives.
Managed callbacks do not duplicate them, remove Keeper of Souls after 30 minutes,
despawn the princess after a donation, or respawn the Spiroc Lord after death.
Seven protected, canonical Sirran services remain on the original key islands.
They require the same eight token exchanges. Native managed state deliberately
does not replay living dynamic NPCs: canonical services recover even if the
boss's death callback was interrupted or no Sirran checkpoint exists. Public
plane definitions and quest branches remain unchanged. Bazzt's private elevation
is ground-probed rather than retaining the old script's40-unit floating pose.

## Source, generation and evidence

`tools/classic_dungeon_catalog.py` owns the appended identities and private Sky
points. `prepare_classic_dungeons.py` extracts their reviewed public source from
the private full capture. `content.json` is the minimal content snapshot;
`placements.json`, `sky-geometry.json` and `identity-audit.json` own geometry and
collision evidence. Production and local map hashes match for all 14 added zones.
`compatibility.json` pins the original catalog and330-reward hash.

Regenerate in order: `tools/dungeon_catalog.py`,
`tools/classic_dungeon_migration.py`, `tools/dungeon_refresh_contract.py`.
The old October 16 contract generator is frozen to prevent silently reintroducing
obsolete item guards. Historical installation SQL remains unchanged.

`server-mods/sql/20261022_classic_dungeons.sql` inserts 15 NPC definitions
(14 Keepers and private Sirran),26 groups/entries,14 public entrance spawns,
28 tasks/218 activities and12 private Sky spawns. It locks the existing revision,
checks engines/triggers, source preimages, reserved identities and dangling
task references, and rolls back on any error. Initial proposed IDs collided with
live skeleton pets; the final998800–998814 range and986000–986011 groups were
audited free. Never reuse a failed first draft.

See [verification.json](verification.json), [rehearsal.json](rehearsal.json),
[build manifest](build-manifest.json), [review](review.md) and
[wiki impact](wiki-review.json). Automated evidence is separate from gameplay.

## Paired activation and recovery boundary

Main promotion requires the owner's sign-off under AGENTS.md. No production
release or website publication is authorized by this candidate. An approved
operator must first take a fresh backup, restore/rehearse the exact migration
against current content, recheck source/identity/quest preimages and record all
39 schema and483 content predicates. Quiesce admissions/runtime for the additive
migration and paired native installation. Preserve later player activity.

Ship the built zone,11 plane quest files, and module to the configured
`server/lua_modules/nightcap_dungeons.lua` search path together. Retain the shared
Instance_Keeper.pl. Existing world/shared-memory/client ABI and330 item definitions
are unchanged; verify the current production cache against the new guards.
Never replace it with an older local cache. A quest reload alone cannot install
the native binding. Production's supervisor restarts the whole runtime when a
child exits: use an approved full-runtime maintenance window, never kill one zone.

Before any added run exists, recovery can reinstall the retained native/quest
pair while leaving the additive definitions inert. After players create added
runs, do not revert to a seven-zone binary that cannot service them. Disable new
admissions, preserve all run/claim/receipt records, and repair forward or keep a
compatible21-zone build until they expire and rewards are claimable. Do not
delete added tasks referenced by characters or restore an older player snapshot.
