# Tunnel travel alcove — deployed for owner QA

September 22, 2026. The owner explicitly authorized main promotion and production
deployment. Installed on `play.nightcapgame.org`; see
[production activation and rollback](PRODUCTION.md). Manual in-game acceptance
remains open. The earlier [local QA activation](ACTIVATION.md) is preserved as
dated evidence.

The initial production install had a plugin-directory error, corrected in the
[September 22 hail fix](HAIL-FIX.md). Reconnect and hail Merrin; no client patch
is needed. Current full rollback uses the hail-fix wrapper linked there.

## What changes

- Remove the ten oversized outbound city stones (DBIDs 40600–40609).
- Add **Merrin — Tunnel Travel**, a stationary, findable human guide (NPC 999810).
  Hail him and click a destination link. No cost, item hand-in or new command is
  required. Invalid links never supply player-selected coordinates.
- Add a native lantern, barrel and crate using three retired door identities.
  They are scenery, not transport objects. Model names are HANGLANT, BARREL3 and
  CRATEA; the lantern is size 60, other props size 100.
- Keep the ten destination return books, both PoK books, existing bind/arrival
  rules, merchants, residents, player data and all waypoint progression unchanged.

The local QA database initially had 39 custom EC spawns; hosted started with 90.
The migration does not upgrade that separate feature baseline. Geometry checks
also compare the alcove against the latest 90-NPC placement and patrol plan.
No new world/zone binary or client download is needed. Older optional map-layer
labels can still mark the retired stones; use Find/Merrin for this QA pass.

## Exact in-game QA

Use a normal account with the existing supported Nightcap client.

1. Zone into **East Commonlands (ecommons, 22)** and walk to the northwest edge
   of the main tunnel chamber, beside the PoK travel book. Merrin stands at
   server **X=-335,Y=-1537,Z=3.75**; `/loc` prints approximately **-1537,-335,3.75**.
   Find should list him as Tunnel Travel. The old ten-city stone row is gone.
2. Confirm one human guide, one lantern, one barrel and one crate are visible.
   Walk around all four: no floating, buried feet, wall clipping or blocked
   approach. Props should stay still and must not teleport when clicked.
   Inspect the lantern appearance at day/night; automated checks do not prove
   its texture, apparent light or RoF2 collision behavior.
3. Hail Merrin. Exactly ten clear destination links should appear. Click **every
   destination below**, check the named zone and safe arrival, then use its
   nearby return book. Each return should reach the existing tunnel arrival
   near Shady at X=-190,Y=-1725,Z=3.75. Original PoK books must retain their routes.

   | Destination | Arrival X,Y,Z | Return book X,Y,Z |
   |---|---|---|
   | North Qeynos | 487,219,3.75 | 504,184,0 |
   | West Freeport | 77,-642,-29 | 77,-662,-34 |
   | Greater Faydark | -734,-188,0 | -738,-174,-3.75 |
   | Butcherblock | -523,1726,0.5 | -487,1755,-3.5 |
   | Everfrost | -31,2835,-60 | -58,2887,-63.25 |
   | Misty Thicket | -1263,-546,12 | -1243,-560,4.5 |
   | Nektulos (classic) | -349,705,-1.75 | -322,743,-9.5 |
   | The Feerrott | -163,908,-7 | -141,867,-9.5 |
   | Innothule | -30,-709,-25.75 | -10,-729,-28.25 |
   | Toxxulia | -583,2345,-43.25 | -563,2325,-47.25 |

4. Walk over 50 units away and click an old link: no travel. Try during a spell
   cast or combat: travel is refused. Rapid repeated clicks should not trigger
   repeated zone requests. Return normally and hail again to verify recovery.
5. With your class pets, walk the approach and both tunnel passages, travel out
   and back, then camp/relog. Check pets, armor and normal pathing persist.
6. Use the retained PoK book; check Waypoint Master and Khalure still offer their
   own services. Buy from nearby merchants. On the newer content baseline,
   watch nearby walkers to confirm the alcove leaves their routes clear.
7. Re-enter after a QA zone restart. Confirm Merrin/props persist once each and
   the ten old stones do not return.

Record appearance/placement, all ten round trips, Find, state guards, pets and
regressions separately. Passing SQL/Perl tests is not owner acceptance.

## Reproduce checks

From the feature/test checkout:

```powershell
python -m unittest discover -s tools/tests -p test_tunnel_travel.py -v
perl tools/tests/tunnel_travel_quests.t .
python -m unittest discover -s tools/tests -p test_tunnel_travel_runtime.py -v
python tools/tunnel_travel.py --capture --output NEW_CANDIDATE_DIRECTORY
python tools/tests/rehearse_tunnel_travel.py --source NEW_CANDIDATE_DIRECTORY/before.json --evidence NEW_TEST_DIRECTORY
python tools/tests/probe_tunnel_travel.py --probe /tmp/nightcap-map-probe-20260920/map-probe --evidence NEW_GEOMETRY_DIRECTORY
```

Inside the target runtime, also run
`perl tools/tests/tunnel_travel_quests.t /path/to/repository /path/to/server`.
The optional server argument reads its `eqemu_config.json`, resolves configured
plugin and quest paths, and exercises the installed files. Repository tests and
`perl -c` alone do not prove that EQEmu loads the installed helpers.

The geometry command needs the existing native map probe in the local server
container. It checks 35 floor/headroom samples, two approach rays and clearance
from the newer NPC/patrol plan. It does not render the RoF2 client.

## Activation and rollback

For the deployed production release use the pinned wrapper in [HAIL-FIX.md](HAIL-FIX.md).
For a new authorized target:

1. Target the authorized environment. Check no players are online, gracefully
   stop world/zones through its existing supervisor, and take a full PEQ backup.
   A world restart follows the existing market rotation policy.
2. Recapture the stopped target with `tools/tunnel_travel.py --capture --output
   NEW_STOPPED_CANDIDATE`. Rehearse that exact snapshot. Never apply a local
   preimage to hosted PEQ. Verify the generated route catalog is unchanged.
3. Read the target's `server.directories` configuration. A nonempty
   `plugin_paths` array overrides `plugins` (default `plugins/`); `quest_paths`
   similarly overrides `quests` (default `quests/`). Install together
   `server-mods/plugins/tunnel_travel.pl` and `tunnel_travel_data.pl` into a
   configured plugin directory, and `server-mods/quests/ecommons/999810.pl` into
   a configured quest root's `ecommons/` directory. Production uses `plugins/`
   and `quests/ecommons/`. Preserve prior files and hashes; new paths must be
   free. Run the installed-runtime hail smoke before reopening access.
4. Apply only that candidate's `forward.sql` without `--force`. Verify every
   scoped afterimage, unchanged preserved tables, and installed quest hashes.
   Start the original runtime and check quest errors and process health.
5. **Before any zone activity only**, `immediate-rollback.sql` restores the
   preimage. It deliberately rejects saved-state drift.
6. **After any zone activity**, gracefully stop again and run
   `python tools/tunnel_travel.py --capture --rollback-from ORIGINAL_CANDIDATE
   --output NEW_ROLLBACK_DIRECTORY`. Rehearse/review, then apply that new
   directory's **forward.sql**. It restores original stones and removes this
   guide's validated base-instance, non-corpse cached state. Ambiguous references
   abort without deleting them. Global reference guards also abort if any corpse,
   zone metadata or other instance/zone refers to this guide; preserve those rows
   and resolve their ownership before retrying. Unrelated corpses, instances/zones
   and NPC states are preserved. Remove only the three introduced quest files after verifying
   their installed hashes, then restart the original runtime.

The owner explicitly authorized main/production release on September 22 before
completed manual acceptance. A Git push alone does not deploy the hosted server.
