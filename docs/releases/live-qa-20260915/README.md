# Combined live QA release — 2026-09-15

Owner request: "Deploy ALL of our changes and I'll test each one in live."
This authorizes the maintenance restart and candidate deployment for manual QA;
it does not certify gameplay. The later explicit request, "Move all gameplay
changes into main. I will test it live," authorizes promotion before manual
acceptance. See [promotion record](../main-live-qa-20260915.md).

## Integrated implementation

- AA ownership / atomic release candidate `8294e15`, including all five server
  fixes and earlier skill/waypoint work inherited from the reconciled baseline.
- PoK arrival hub and class guidance `d1a9ee9`.
- Bag pricing `dc96e5f` and issue/title audit `87aaaa9`.
- The plugin merge retains native boolean `ReleaseMulticlassSlot` and adds hub
  guidance. Its server C++ is identical to the reviewed final AA candidate.

Production zone SHA256:
`e79e7f2eacd50237a8c74aeda44896e124159d114b5b7c37979e9a1356eb645c`.
Matching world SHA256:
`4ce4709f866889bbcde05f59690cff3cefb7760f85029cff1ee277d85f3d762f`.
The durable candidate is `artifacts/live-qa-20260915/zone.candidate` in the main
workspace. Never deploy the similarly named native diagnostic executables.

## Verification before activation

- 351 integrated calculator/native-evidence unit tests passed.
- Four PoK planner/migration tests, 14 real isolated MariaDB controls, three bag
  pricing integration tests and 13 AA-title audit tests passed.
- Lua checks cover all 16 primary classes; Perl tests pass 16 Chronicler,
  seven guidance and 15 native-release assertions. Era preflight and atomic
  release source guards pass.
- The unchanged candidate has retained 87/87 C++ and native AA transaction
  evidence. An independent reviewer verified binary lineage, exact hashes,
  all-five-fix inclusion and merged plugin compatibility for this deployment.
- Live hub preimage matched the reviewed snapshot exactly. Full backup gzip
  integrity and hash were verified after stopping all gameplay processes.

## Rollback and operations

Private operational evidence/backups are under
`E:/EQ_Local_Dev/artifacts/live-qa-20260915/`: full PEQ dump, original zone,
original changed files, original operational scripts, exact before/after images
and deployment manifests. These are local rollback assets, not public player data.

Rollback order while gameplay is stopped: reverse bag prices using its guarded
rollback mode; reverse the hub with `docs/pok/hub-rollback.sql`; restore matched
old world/zone and plugin/quests and original operational files; rebuild shared memory;
start all processes and verify hashes/PIDs. Stop on any preimage drift. Do not
restore the whole database merely to undo content, or erase post-deployment player
progress without a separate recovery decision.

The scheduled era/backup entry point uses the root workspace, so the new durable
restock, `tools/apply-era.ps1`, its hub guard and catalog policy must also be
installed there together. Era stays Classic / cap 50. The AA audit remains
read-only; no blanket AA disablement or experimental release pool is installed.

The deployment log records initial operational retries: Docker cp could not
resolve the binary symlink, so the verified resolved target was used; Docker cp
created the staged binary as root-owned, so root set ownership/mode before the
atomic rename. Both occurred before gameplay resumed.

## Startup defects found and repaired

The first new-zone startup exposed two existing operational defects. The old
world binary did not compile `Character:AAExpMinLevel`; its orphan-rule cleanup
deleted that row on boot (the September 13 world log explicitly records this).
Built world from the same pinned source as zone, retained the original, and
installed it as part of this release. Reinserted the absent rule at value 1.
The world build passed and all 2,787 final source hashes match the pinned manifest.

PoK had 17 cached custom-NPC states with old coordinates. `LoadZoneState` can
recreate a deleted spawn and `LoadNPCState` restores the cached position. Retained
the complete cache preimage and ran [the scoped cleanup](clear-stale-hub-state.sql)
first with ROLLBACK, proving exact restoration, then committed. Exactly those 17
non-corpse, instance-0 rows were removed; 245 other PoK states were unchanged.
The initial database-only hub test could not catch this missing runtime-cache step.
Future hub activations must inventory and evict affected saved states with exact
guards. After any later gameplay, rollback must reconcile that newer cache rather
than blindly restoring this historical state.

Fresh full PEQ backup: 46,341,767 compressed bytes, 440,671,787 uncompressed,
SHA256 `e8f81a82f279a5d2b6e6f2569e568933615efbebbc24596226d336c1aea5ce90`.
No character rows or AA ownership/wallets were directly edited during deployment.

Website follow-up: the owner explicitly approved the updated HTML and public
GitHub Pages publication on September 15. This resolves the earlier approval
block. See [website publication evidence](../../ops/player-website.md); game-server
acceptance remains independent.

See [the full test checklist](QA.md). All manual acceptance remains pending.

## Final runtime check

Matching world and eight zone workers started successfully. Every executable hash
matched its candidate; all loaded 58,359 skill-cap rows. The AA XP minimum remained
1 after world startup; hub stock remained 1,747 listings / 1,229 unique items.
Current process logs contained no startup Error/Fatal/exception matches. PoK
terrain, interaction, transactions and client rendering await owner gameplay QA.
