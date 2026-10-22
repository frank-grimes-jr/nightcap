# Waypoint crystal — October 22, 2026 candidate

The owner reports waypoints have no obvious graphic and selected a glowing
crystal with a label. NPC 999240 now uses Crystal Shard (race 425, neutral gender,
size 6), retaining its existing `a waypoint` nameplate and WizardPortal nimbus
178. Actual model geometry provides an additional cue; appearance with particles
off still requires native QA. **Not deployed or published.** Do not apply the
quest alone: it requires the paired client below. Existing positions are retained.
Historical October 13 portal acceptance does not resolve this new report.

## Design and pairing

- `server-mods/quests/global/999240.pl`: same entity, nameplate, pose, 25-unit
  horizontal / 30-unit vertical discovery bounds and earned progress. Signals
  20261011/20261022 refresh existing markers idempotently. No timer, new spawn,
  NPC/recall SQL, native server build or cache rebuild.
- `eq-client-dll/src/model_hooks.h`: exactly one complete model-import list per
  mode. Classic retains all 155 former rows plus `crs,crs`; Modern retains the
  13 pinned stock global rows plus the crystal. Native Luclin preferences and
  the original resource/INI bytes are untouched. User-customized global import
  tables are outside this pinned contract.
- `tools/client_classic_models.py` and `generate-classic-model-contract.py`
  generate/hash both lists and byte-identical stock `crs.eqg`. Proxy and packager
  share the 25-file contract. All 22 existing isolated model archives retain their
  bytes. Missing/changed paired assets fail the startup gate in both modes.
  Proxy/catalog candidate version is 0.11.1.

Portal-only presentation depends on particles and has no mesh. A banner was
considered; the owner chose the crystal. A humanoid guide would avoid client
asset work but changes the chosen appearance. No gameplay power, travel range,
discovery/reward, Keeper or balance change is included.

Both installed `E:/Nightcap` and the protected reference have native imports
`Resources/GlobalLoad_chr.txt` SHA256
`0b0ca125859b4737b04f0d7ad4b5a885fea315fbc2b7fee6bb18da79bf4d3a69`.
Crystal archive SHA256:
`0a06d4b41d49843b40518105b50057a50d1abb07147e10fb3769135ee1223f6b`.
It contains `crs.mod`, texture, animation and effect dependencies. Its material
`AddAlpha_MaxCBSG1.fx` still needs native particles-off visibility QA.
[EQEmu's model inventory](https://docs.eqemu.dev/server/npc/npc-models/)
identifies race 425 as CRS/Crystal Shard; actual client bytes own compatibility.

The pinned native parser at VA 0x48CB80 writes count at 0x48CC12 and replaces
the table pointer at 0x48CC4A. Calling it twice would replace earlier entries.
The hook calls it once at the existing guarded global-import call site; separate
zone import calls are unaffected. The initial two-call proposal was discarded
after native disassembly, before any deployment.

## Validation

`verification.json` records completed checks and staged hashes. The test-first
quest assertions failed on invisible race 127/gender 0; the import regression
also rejected the old Modern path. Final quest19/Keeper52, Python27 including
eight model checks, x86 runtime9 groups, native model-animation288 cases,
invisible-actor regression, all107 exact-client guards and launcher
package/preflight/manifest suites pass. All22 existing generated archive hashes
and prior import rows must match the retained baseline. Independent review found
no blocking source issue; signed publication and visible QA remain separate.

Reproduce from the checkout: `perl tools/tests/waypoint_visuals.t`,
`perl tools/tests/instance_keeper_visuals.t`, with `PYTHONPATH=tools` run
`python -B -m unittest discover -s tools/tests -p 'test_*waypoint*.py'`.
Build `eq-client-dll/build.bat` and `tests/build-runtime-tests.bat`, then run
`python -B eq-client-dll/tests/test_runtime.py --eqgame PATH_TO_PINNED_EQGAME`.
Both catalog generators support `--check`; the model generator also requires
`--assets PATH_TO_GENERATED_MODELS`. Run Go tests from `eq-launcher/`.

## Activation and recovery

1. Main promotion and production/client/wiki publication require owner approval.
   Inspect the latest channel and preserve its complete signed inventory, current
   DLL/catalog pairing, unrelated assets and patch-note history. The staged
   five-file client delta is not a complete signed release. Assign a fresh higher
   game counter and add a waypoint crystal patch note only for an approved release.
2. Publish/verify proxy0.11.1, catalog, `nightcap_models_chr.txt`,
   `nightcap_modern_chr.txt` and `crs.eqg` through the existing guarded signer.
   Validate the exact DLL/catalog and full assembled inventory. Existing launcher
   asset policy supports these paths; no desktop update is required. Players close
   EQ and use normal Play; old running clients need this update before activation.
3. Recheck the live quest preimage, retain exact bytes, use the shared deployment
   lock and supported quest reload without timer reset. Signal only NPC999240 with
   20261022. Verify hashes, reload logs, continuity and no Perl errors. Unbooted
   zones apply on spawn. No process kill, repop, saved-state deletion or SQL rewrite.
4. For quest recovery, restore race127/gender0/size6 on active markers using a
   scoped temporary signal handler, then reinstall the retained quest bytes and
   reload. Restoring bytes alone does not undo an active illusion. Retain portal178.
   Client recovery uses the prior complete matching pair at a higher counter;
   never lower checkpoints or restore player snapshots. Added crystal files may
   remain inert with the old proxy.

## Exact in-game acceptance

1. After launcher Play, visit Befallen `/loc -82, 35, 3`, Unrest `/loc -38, 52, 3`,
   and Crushbone `/loc -644, 158, 4`. Expect a crystal and readable `a waypoint`
   label, with portal glow when particles are enabled. Check ordinary approach
   distance, darkness, scale, ground contact and low ceilings. Reject invisible
   or human fallback, excessive flicker, oversized geometry or service/path blocking.
2. Repeat with spell particles low/off and NPC names on: the mesh must remain
   recognizable. Names-off may hide the label, not the mesh. Fully restart between
   Classic and Modern model modes and repeat.
3. Approach on an unattuned character: exactly one attunement/progress update.
   Leave/re-enter silently. Recall must land at the existing location; existing
   discoveries remain intact.
4. Keep a zone loaded with another player, join later and observe for60seconds.
   Check persistent crystal/glow, normal fresh and saved-state loads, and an
   existing private dungeon where available.
5. Target/hail the separate Instance Keeper and verify its dungeon choices. Check
   one outdoor and one zone-line waypoint. Report bad placement with zone and
   `/loc`; this candidate does not relocate markers or expand discovery range.

## Wiki impact

`wiki-review.json` assesses all maintained guides and generated reward routes.
Waypoint Explorer, In development and Recent changes receive explicitly
unreleased notices. Features/home/travel/dungeon descriptions, commands and
reward catalog retain their released meaning. Local edits are not public;
publication remains pending.

## Current release compatibility

The candidate now incorporates main26761ff, including the published Classic robe
release. A fresh HTTPS channel read exactly matches the previously verified signed
game2026102201 envelope. `client-inventory-plan.json` retains all 135 unrelated
asset descriptors/URLs, including both robe archives, plus patch history and
tombstones. The five-file waypoint delta replaces three files and adds two;
all 25 model-contract digests match the assembled 140-file inventory plan.
This is an unsigned plan, not a publishable channel. A fresh baseline, higher
counter, approved patch note and signing remain part of authorized publication.

All 14 tested waypoint implementation hashes are unchanged by integration.
`integration.json` and `wiki-integration-review.json` record the new baseline;
the original verification/review files retain their earlier scope. Both published
robe notices and unreleased crystal notices survive the resolved wiki merge.
The published robe ledger e209649 is retained. The merged wiki passes 14 Python,
6 search and 7 equipment checks and builds 458 pages. No native gameplay or
publication acceptance is implied by these source/inventory checks.
