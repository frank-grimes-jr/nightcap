# Local QA activation — September 21, 2026

Installed on **Local Development Server** for owner QA. No hosted deployment or
main promotion was performed. Implementation commit: `4cd97b5`.

Zero players were online. All eight zones exited gracefully before the launcher
stopped. A full PEQ dump passed gzip integrity and decompression checks:
441,742,100 uncompressed bytes, archive SHA-256
`90679bea5517eaa7928876f8dc7c4f5fc9cd8494dc286479245735c6101c08a6`.

The exact stopped-target capture passed all 20 disposable-database rehearsal
checks before application. Installation verified every scoped afterimage, three
quest-file hashes and seven unchanged table fingerprints: character data,
inventory, currency, AAs, multiclass, binds and merchant stock. The three new
runtime files also passed `perl -c` inside the server container.

At 23:21 UTC the original launcher, world and eight zone workers were online;
world and zone binary hashes were unchanged. This verifies process health and
installed content, not a rendered client session or completed in-game acceptance.
An independent process check verified all nine running world/zone executable
hashes, eight established zone-to-world connections and no error/fatal entries in
their current-process startup logs.
The local baseline had 39 custom EC spawns and now has 40. The separate newer
90-NPC hosted layout was not copied to local QA by this change.

## Automated evidence

- Six migration/catalog unit tests and 25 quest checks passed.
- Existing hub/client checks (five) and resident quest checks (21) passed.
- Twenty SQL checks cover exact apply/rollback, drift/collision rejection,
  replay, player data preservation and saved-state rollback boundaries.
- Native geometry passed 35 ground/headroom samples and two approach rays.
  Minimum clearance from the newer NPC layout is 28.02 units; from its patrol
  segments, 47.01 units. These checks do not prove prop rendering or collision.
- Independent review blockers were resolved before activation.

Sanitized results: [verification.json](verification.json),
[database-checks.json](database-checks.json), [geometry.json](geometry.json).
Full local operational evidence, stopped preimages, guarded SQL, quest manifests
and the private database backup are retained under
`E:/EQ_Local_Dev/artifacts/tunnel-travel-alcove-20260921/activation/`.
They are deliberately not committed with account/character records.

## Owner acceptance and rollback

Run the [exact in-game QA](README.md#exact-in-game-qa): appearance/placement,
Find/hail, all ten city round trips, travel guards, pets, existing services and
persistence after a zone restart. Main/hosted promotion awaits that sign-off.

For rollback use the [post-activity capture procedure](README.md#activation-and-rollback)
against `activation/candidate/` above. The runtime has restarted: do not assume
the immediate rollback remains valid. Remove only the three introduced quest
files after matching their recorded hashes, then restart the original launcher.
