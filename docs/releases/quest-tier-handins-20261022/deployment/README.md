# Quest-tier deployment - October22, live QA open

The owner explicitly requested main promotion and server deployment for live QA.
PR290/main `c66df0e4b36a6f9a041f9ef3ad609779fd1eb85e` is merged. The native runtime
started at **18:01 UTC**, access reopened after verification, and the retained
18:08 UTC probe confirms the same healthy game container with zero restarts.
Owner gameplay acceptance remains open; [exact QA](../QA.md) is separate.

Installed image:
`sha256:085f3021e6a9cd9d67bdf027575f3d15b61516e3db3e375b281b5551051bad1a`.
All12 zones run `6da991b688a5b25819b24274506f2d7a427cd7990ff8ca1992d2beabca75c2f0`.
Its sole added layer replaces zone over authenticated image15a159c0/zone5dd5a655;
world, shared_memory, loginserver, ucs and supervisor hashes are identical.
The source build reproduced the predecessor byte-for-byte before rebuilding the
two affected objects. No new ABI, SQL migration, rules or client patch.

Seven files are paired with the binary: `quests/lua_modules/items.lua`, Kurron Ni,
and Gardern/Joyce/Sultin/Vilissia/Vurgo in soltemple. The other ten live class-armor
reward scripts, robes/game2026102203 and waypoint release are preserved.
Shakrn now accepts any ordinary Aviak Charm quality plus two Star Rubies for the
configured Ascended Crafted Gauntlets604178. Explicit-quality requirements and
crafting recipes retain their own rules.

`live-verification.json` records:

- Fresh stopped64,937,715-byte gzip database backup, integrity checked.
- Exact47 player tables and28 custom/timer tables preserved across boot.
- All14 content-table checksums, item/spell caches, signed public client files,
  db/web/tunnel identities, and8,133 other runtime files preserved.
- Normal market startup90→91 authenticated:42 valid offers within44 slots.
  No NPC-cache expiry reconciliation or player snapshot restore was needed.
- Healthy game, all12 expected zone executables and no native/quest/SQL error
  markers; gateway running/open. Gateway has no Docker healthcheck (null), so
  the collector checks running/no-OOM rather than interpreting null as failure.

The first collector used an inapplicable gateway healthcheck assertion; inspection
confirmed identical healthy game state and an open, running gateway. Corrected
read-only collection succeeded. No retry of activation or service mutation.

`rollout.py` pins the manifest, helper, image and seven predecessors. It holds
deployment/GM locks, stops the whole supervised runtime, backs up every quest
preimage before writing any, and keeps access closed until all checks pass.
Independent review and16 offline fault tests pass. `preflight.log`, `activate.log`
and `open.log` preserve successful phases. Detailed private stopped-state and
backup receipts stay under `/opt/nightcap/releases/quest-tier-handins-20261022/`.

Disk preparation removed seven redundant upload archives only after exact retained
local-copy verification. No image, volume or backup was deleted. Plans/receipts
are retained; final free space was about2.82GiB. The earlier1GB probe and cleanup's
3.26GB starting measurement differ; the cleanup receipt claims only its measured
1.08GB removal, not ownership of other free-space changes.

## Recovery

Do not replay an activation/open attempt after uncertain failure. Inspect its
immutable receipts and current service/file hashes first; a failed stop may leave
a service running or unknown. Hold access before diagnosing. Do not kill one zone:
the supervisor restarts the full runtime on child exit.

Recovery pairs the retained immediate predecessor image15a159c0 with all seven
exact predecessor quest files in `evidence/activation/quest-preimages/`, guarded
against this release's installed hashes. Use a fresh stopped backup and a reviewed
one-shot recovery under the same deployment/GM locks. Verify current earned state,
content, cache/client pairing, native processes and startup market rotation before
reopening. The forward operator intentionally has no permissive generic rollback
or resume command. Never restore old inventories, task progress, rewards or player
snapshots. Preserve the ten already-live armor reward scripts and current client.

## Wiki and maintained knowledge

All21 guides and432 generated routes were reviewed. Six notices and search changed;
catalog384 values and commands did not. Wiki20261022-quest-tiers-v1 follows the
current class-armor-v2 publication and preserves robe2203 guidance. All465 HTTPS
hashes/security headers and five private-route denials verify. The unchanged
updater's16 Linux fault tests and actual pointer rollback rehearsal pass; private
downloads, config and services remain. `wiki-review.json`, `wiki-publication.json`
and `wiki-public-verification.json` separate review, origin publication and public
verification. Installed Nightcap knowledge is updated by `refresh_skill.py`, with
exact patch, fingerprints and receipt in `skill-update/`.
