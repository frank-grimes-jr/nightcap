# NPC-targeted heal fallback — October 9, 2026

The owner explicitly requested promotion to main and the OVH server for this
release. In-game acceptance remains separate from deployment verification.
Current status: production build in progress; activation has not run.

## Scope and verification

Player healing spells aimed at an NPC resolve to the caster before implied
targeting and target-specific checks. The selected combat target is retained.
The [behavior and in-game QA](../../qa/2026-10-09-npc-heal-targeting.md) cover
player targets, pets, special target types and direct/triggered healing.

The original fix is `ce161c5`; `26a2e7d` applies it to the latest main baseline.
A fresh CMake zone build uses the retained hardened production source at
`/tmp/nightcap-zone-hunt-hardened-build-20261009` in the local build container.
The baseline binary hashes match OVH. Only `zone/spells.cpp` changes; all source
fingerprints are checked before and after compilation. No stale build objects
are reused. World, UCS, loginserver, shared_memory, supervisor, quests, client
release, database definitions and rules are preserved.

- 99 compiled heal regression checks pass on the patched production source.
- Five isolated rollout tests pass: success, baseline drift, failed health,
  persisted-data drift and a lost gateway-open acknowledgment.
- The deployment builds one image layer over the exact live image, containing
  only the new zone executable. Both images pass native/crypto validation.
- A full database backup precedes downtime. Activation closes the gateway,
  stops the game gracefully, captures persisted data, starts the new game image,
  verifies all 12 zone process hashes and reopens access only after validation.
- Existing `nightcap_market_offers` and `nightcap_market_state` are excluded from
  static checks because the unchanged world process owns market rotation.
  Character data, loot receipts, waypoints, custom content and other custom
  tables are compared while access is closed. No SQL restoration is performed.

## Evidence and recovery

Release directory on OVH: `/opt/nightcap/releases/npc-heal-self-20261009/`.
Local build/release evidence: `E:/EQ_Local_Dev/artifacts/npc-heal-release-20261009/`.
The former contains the binary, manifests, patch, verified backup and activation
reports. The latter also retains build logs. `rollout.py` shares the established
production deployment lock and uses the prior release's read-only runtime
inspection helpers.

The rollback image is the immediately preceding, receipt-aware immutable image:
`sha256:43b216727a5f4dad4492fa8da03ca81e2f22e5cb721428645e59b8e203dcdf5a`.
Its zone hash is
`54689a1ad67e8bb753a9e8ad897c3b1cebf51642c8e7a3f0ea5eeb1c96b1d5b1`.
Activation failure closes access and restores that image while retaining all
current SQL state. Do not restore an old database or pre-receipt game image.
OVH restarts the entire game runtime when a child exits; never kill a single zone
as a deployment shortcut.

For later operator recovery, acquire `.deployment.lock`, verify the current
image is the one recorded in `evidence/preflight.json`, stop gateway and game,
select the recorded `old_image_id` using the same atomic environment update,
start game with the Compose health gate, verify old process hashes, then reopen
gateway. Retain current character/corpse/receipt data throughout recovery.

## Owner acceptance

After deployment, use a normal injured caster in East Commonlands. Keep an orc
pawn or Camil Silvermist selected and cast an available heal. The caster must
recover HP while the NPC remains selected. Check another player as a direct
target and an available pet-only heal separately. Complete the linked QA matrix;
server health alone does not prove client animations or actual HP restoration.
