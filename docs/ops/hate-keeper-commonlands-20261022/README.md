# Plane of Hate Keeper relocation — October 22, 2026

**Main and production deployment verified; owner gameplay acceptance remains open.**
The owner explicitly approved "Push to main and server". PR299 merged as
`a736fb0`; the paired move is live and gateway access is open. All12 zone workers
match the tested new binary and39 schema/499 content checks pass. A fresh stopped
backup and exact player/state/content/cache preservation were verified.
`deployment.json` is the redacted receipt; private full backup stays on the host.
Wiki `20261022-hate-keeper-v1` verifies all466 public hashes/security headers and
five private-route denials. No client update. These checks do not replace the
owner QA below.

## Result

- Move existing NPC/group998812, public spawn9100012, to East Commonlands at
  XYZ `-346,-1570,3`, heading256: in-game `/loc -1570,-346,3`, between Mirielle
  and Khalure in the tunnel's travel area. Its `hateplane` label remains.
- Native routing binds this specific public Commonlands Keeper to Hate zone76.
  All menu actions, personal journal and destination coordinates select Hate.
  Wrong-host copies cannot fall through to legacy instance creation.
- Remove Hate version0's `min_status=80` gate, retaining `min_level=46`.
  **This also permits ordinary level46+ access to public classic Hate.**
  Admission is checked before creation/reset/join mutations.
- Retain a private-only Hate Keeper at its original entrance. Both fresh and
  checkpoint spawns override the moved base row, without duplicate Keepers.
  Preserve all existing run, credit, reward and character data.
- No client, quest, world, item-cache or spell-cache change. Install the new
  zone binary and scoped SQL together; old binaries reject the successor
  content contract. Production needs a controlled full runtime restart.

## Evidence

The baseline relink exactly reproduces deployed zone `8c9b97d5…`; the candidate
is `1d4ef362639722b7eaddc49ae2883e2c5abcefc7c5d958f622cfb048308b995f`.
`build-manifest.json` pins every retained input and changed source. The linker
and `ldd` passed. Source tests cover all21 Keeper identities, cross-zone
admission/arrival, selected-run journal, fresh/checkpoint private spawns and
idempotence. The successor runtime contract contains39 schema/499 content checks.

`rehearsal.json` records actual MariaDB forward/inverse equality, mid-transaction
rollback, repeated-apply rejection and preservation of private/unrelated saved
spawns. It uses captured production DDL and synthetic saved rows in an isolated
local schema. `geometry.json` authenticates the local map against production:
ten ground/headroom samples and a clear approach, with51 nearby hub NPC rows in
`hub.json`. These checks do not establish visual or gameplay acceptance.

Independent review's routing, journal and checkpoint findings were resolved.
The legacy-instance query now counts NULL notes correctly. The fresh read-only
probe found zero unmanaged Hate instances and zero public Keeper saved rows.
Repeat both after stopping writers; these observations are not deployment gates
that can be cached indefinitely.

## Activation and recovery

1. Owner main/live sign-off was received and PR299 merged. The steps below
   describe the completed release; do not blindly replay its immutable stage.
   Keep the manual checks below open.
2. Run `prepare.py --name approved-SHORTREV` with a fresh name from this checkout.
   Preparation never overwrites an existing immutable package. It authenticates the build sources and
   fresh live base image and pins the retained operator. Inspect its package
   manifest. Transfer only that immutable package to the release stage named in
   `rollout.py`; retain restrictive permissions. Never transfer private DB data.
3. Under deployment/GM locks, run `rollout.py preflight`. It rejects content,
   image or runtime drift and checks all baseline workers. New image changes
   only the zone executable. The current client and other services stay pinned.
4. Announce a brief game disconnect. Run `rollout.py activate`: close gateway,
   stop game cleanly, repeat legacy/startup guards, take a fresh full backup and
   capture fresh scoped rows, then apply one serializable guarded transaction.
   Invalidate only the old public non-corpse Keeper saved rows. All unrelated
   saved state, run/player tables, quests, public assets and caches are verified.
5. Boot the paired image, check all12 worker hashes, native health/logs,
  39/499 contract, modeled native saved-state expiry and one startup market
   rotation. Reopen gateway only after checks. Retain the private receipt;
   publish a redacted deployment summary and update skill/wiki status.

Any failure holds the game/gateway closed. Inspect the transaction receipt and
fresh state before recovery. `inverse-rehearsal.sql` is **only an isolated test
artifact**: never restore the old player snapshot or replay that inverse after
new runs/checkpoints exist. Prefer forward repair retaining the compatible
private Keeper. A content/binary rollback needs fresh guarded rows, zero
incompatible new activity and its own preservation check.

## Exact owner QA

1. With a normal account, visit East Commonlands `/loc -1570,-346,3`. Confirm
   the Hate eye/label is visible, selectable, separate from both travel NPCs,
   and hail shows Raid, Grind, Enter, Join, Status, Claim Rewards and Reset.
2. At level45, try entry/creation and confirm refusal without creating a run.
   At level46+, create a Grind run and arrive at the Hate entrance, never at
   Commonlands coordinates. Confirm the selected Tasks journal is Hate.
3. In Hate, confirm one Keeper at `/loc -374.8,-337.08,2`. Return to Commonlands,
   use Enter, and rejoin the same run. Have a second eligible character Join.
4. Use Commonlands Status/Claim Rewards against that Hate run; verify earned
   credit persists and no rewards are invented. Kill an eligible objective,
   leave/re-enter after unload, and verify credit plus the private Keeper.
5. With a disposable test run only, confirm Reset requires confirmation and
   recreates Hate with the selected mode. Exercise Raid and its final gate;
   preserve the live release's outstanding full-clear/balance QA.
6. Verify public Hate allows normal level46+ travel and still rejects under46.
   Check one original Keeper (Befallen) and another new Keeper (Fear) for menu
   and destination regressions. Relog and confirm saved progress remains.

Wiki publication preserves the exact preceding Build Lab release and its
interactive shell. Only seven guides plus search changed. All22 guides and432
generated routes were reviewed; catalog values, commands and other dungeon
policies remain.16 content/source checks,16 Linux publisher/recovery checks and
the real old/new pointer rollback rehearsal pass. Source:
`E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki`; publication and HTTPS receipts are
retained alongside this record. Owner gameplay acceptance remains open.
