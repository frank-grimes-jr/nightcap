# Production activation: three-pet management

Activated September 27, 2026, for owner live QA at play.nightcapgame.org. The
owner explicitly approved main and live server/client deployment, then required
that independent EverQuest Legends remain untouched. Pet code entered main in
PR 72; the installer correction entered main through PRs 76, 77 and 78.
[Machine-readable evidence](production.json) records the exact hashes and counts.

## Delivered behavior

Pet Info lists three class/name/health rows. Commands affect all eligible pets
until one is selected by clicking its name or its body in the world. Enemy
selection keeps that pet scope. All pets, clicking the selected name again or
clearing the target restores shared commands. Existing AA, ownership and combat
restrictions remain. Native buffs/detail gauges still follow one representative.

Server image: `nightcap-game:pet-management-20260922`, digest
`sha256:d9aadb51fc2d1b6cb773c102baea1747b734b764028a84e044cde03090e19806`.
The fresh five-target build uses the reviewed production hardening. Actual server
startup was `2026-09-27T20:47:20.833455437Z`, with 12 zones plus world, loginserver
and UCS verified against their exact binaries. No schema or balance change.

Signed game release **2026092201** contains 23 files, proxy **0.6.0-dev**, the
43-site catalog and generated Pet Info XML. Signed desktop **0.3.1**, release
**2026092701**, arrives through the existing starter. The existing starter,
friends ZIP and guide are unchanged. Hosted signatures, sizes and hashes passed.

The E:/Nightcap install passed through the production updater controller with the
reviewed exact-executable guard. All 23 managed files verified; its base executable
and 20 existing INIs were unchanged at installation. Actual owned startup/stop
reached ready with required/enabled/applied masks all 8191. The independent Legends
process remained running; no authentication or gameplay was automated. The desktop
UI automation tool was unavailable because its sandbox process service failed;
the actual controller, file hashes and native health were checked directly.

## Verification and preservation

- A complete 444,687,702-byte uncompressed PEQ backup was restored successfully in
  a disposable database before changing the live image.
- All 46 player/account/inventory/rule/merchant preservation fingerprints matched.
  All 8,134 quest/plugin/Lua runtime file hashes matched; the newer travel-hail fix
  was retained. Normal startup advanced the market epoch from 8 to 9.
- All 15 native process hashes matched, with zero restarts and no matched native,
  quest API or database errors. Four encrypted public native handshakes passed.
- [Nine hardened native cases](native-production-summary.json) passed: 132 actions
  and 105 commands, including shared/individual orders, world selection, enemy
  targeting, dismissal and range rejection. [Cleanup](native-production-cleanup.json)
  confirms no retained synthetic rows in any of the six fixture tables.
- 47 isolated rollout/publication fault tests and independent review passed.
  Six Windows guard tests plus production installer/controller suites passed.
  Frontend type/build checks and dependency audit passed with zero vulnerabilities.

The interrupted September 22 work was revalidated before continuing. The previous
server had one historical restart and had run since September 22 20:56 UTC; its
exact count/start were pinned for preflight. Candidate and recovery checks still
require zero restarts. The recorded prior supervisor exit was not diagnosed as
part of this pet release. Recovery explicitly recreates the old container.

## Recovery

Private host locations (no credentials or player rows are committed):

- Server package: `/opt/nightcap/releases/pet-management-20260922`.
- Backup and preservation evidence:
  `/opt/nightcap/releases/pet-management-evidence-20260922`.
- Previous game metadata: `/opt/nightcap/releases/pet-client-2026092201/previous-channel.json`.
- Previous desktop metadata:
  `/opt/nightcap/releases/pet-desktop-2026092701/previous-launcher-channel.json`.

The backup SHA256 is
`4d4dabe22f4121cb484ed0101bcc76865b4e3810c245a45e96da906169211bc6`.
The previous image is `nightcap-game:tunnel-services-20260921`, pinned as
`sha256:7219a5e43b6f00e96e6abf88914e309f0ea3c36ad381a9f840f6a605c8e0c570`.

For a paired pet rollback, use the hash-pinned `rollout.py rollback` from that
server package. It closes the gateway, stops the game, captures current progress,
recreates the previous image, verifies preservation and health, and only then
reopens the gateway. **Do not restore old player data.** Restore the previous
reviewed client bytes by signing a new game release above 2026092201; never lower
or reuse the public counter. A desktop rollback likewise requires a signed
release above 2026092701. Preserve the stable starter repair and current quests.
See the [permanent patcher runbook](../../ops/permanent-patcher.md).

[Reviewed operation scripts and repeatable failure tests](ops/README.md) are
retained with this record. The deployment scripts intentionally reject image,
file, baseline or public-channel drift and are specific to this release.

## Remaining acceptance

The reported no-op was not reproduced in the owner's original session. Native
engine, compiled client ABI and startup checks provide bounded evidence; they do
not prove the rendered three-row window or authenticated player interactions.
The owner must run [the exact in-game checks](QA.md). Manual graphical/gameplay
acceptance and three-pet encounter balance remain open. Deployment approval is
not recorded as gameplay acceptance.
