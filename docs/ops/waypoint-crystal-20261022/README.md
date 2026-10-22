# Waypoint crystal — deployed October 22, 2026 for live QA

The owner reports waypoints have no obvious graphic and selected a glowing
crystal with a label. NPC 999240 now uses Crystal Shard (race 425, neutral gender,
size 6), retaining its existing `a waypoint` nameplate and WizardPortal nimbus
178. Actual model geometry provides an additional cue; appearance with particles
off still requires native QA. **Main PR280, signed game2026102202 and the paired quest are deployed.**
Do not apply the quest without the paired client below. Existing positions are retained.
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
  Published proxy/catalog version is 0.11.1.

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

1. The owner authorized this main/server release and its necessary paired
   publication. This is not standing approval for later releases.
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
4. Run the retained operator's `activate.py rollback`: restore the exact backed-up
   quest, reload without timer reset, then signal only NPC999240 with20261011.
   The verified old handler actively restores race127/gender0/size6 and portal178;
   no temporary quest is needed. Restoring bytes alone does not undo an illusion.
   The operator preserves the original admission state, holds access after uncertain
   post-write failure, validates owned partial files and supports exact rollback retry.
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

All21 maintained guides and432 generated reward routes were reviewed again.
Waypoint Explorer, In development and Recent changes now describe the deployed
crystal with Live testing labels and the paired launcher instructions. Other
guides, Features/home summaries, commands and catalog values retain their meaning.
See deployment/wiki-review.json and the separate publication/HTTPS receipts.

## Pre-publication compatibility evidence (historical)

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

## Verified activation

The owner authorized “Merge to main and server” and confirmed EverQuest was
fully closed. Main PR280 (`f293626`) and signed game **2026102202** are deployed.
The complete signed 140-file client inventory, actual DLL/catalog pairing and
all HTTPS hashes verify; 135 prior descriptors, including Classic robes, are
preserved. Quest activation verified zero clients, the exact committed LF hash,
12 aggregate reload acknowledgments and signal20261022. Login admissions were
restored; world/all12 zone lifetimes, five services and Keeper quest are unchanged.
No database write, native restart, repop or saved-state rewrite was needed.

Fully close EverQuest and use normal launcher Play before testing. Crystal/label
appearance, particles low/off, both model modes and discovery/recall still need
owner in-game acceptance. Locations and earned progress are unchanged.

[Operator, tests, release hashes and recovery](deployment/README.md).
