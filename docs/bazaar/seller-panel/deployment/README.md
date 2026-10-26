# Combined Bazaar and Paladin grip release

The owner authorized one combined main/server/client/wiki deployment for live QA.
This chat owns deployment; the weapon chat holds production writes. See AUTHORIZATION.md
and coordination.json. No separate weapon promotion or runtime installation.

Build and verify the integrated zone/world/shared_memory tree. Keep the original
standalone weapon source/manifest/binaries and full integrated debug binaries locally.
Use strip --strip-debug only on new runtime copies: elf_runtime_identity.py must
prove identical PT_LOAD bytes (except section-table header location/count), all
program headers, allocated sections, entry, permissions and ELF identity. Four
negative/positive tests cover code redirection, mapped padding and header changes.
This reduces transfer/disk use. The exact unmounted previous Bazaar staging zone
was additionally archived losslessly with a decompressed-hash proof to retain the
reserve. Its adjacent zone.bazaar-grip-debug-preserved.gz and receipt preserve every
byte; restore and authenticate it before reusing its old staging operator. Active
images, player data and DBbackups were not removed.

ship.py authenticates the current source, retained baseline, all three runtime
identity reports, package and established helper/contract hashes. It stages only
three binaries, operator and manifest, then runs preflight under deployment/GM
locks. Preflight preserves services, content, caches, quests and publication.
The 672MiB reserve is required; it must not be relaxed to make a release pass.

rollout.py activate stops gateway then the entire supervised game, requires a
clean timely exit, takes a fresh stopped DB backup, authenticates current saved
state (including all five Bazaar tables), and allows only the established boot
expiry/market rotation. It installs the matching three-binary image and verifies
all workers, health, contract and preservation before recording verified-closed.
rollout.py open is separate and rechecks the verified receipt before access opens.
Failed/uncertain operations hold closed and cannot replay.

Once 1HS metadata exists, recovery must retain grip-aware native code. Do not
restore old player snapshots or use the pre-grip binary as a blind rollback.
After public client/wiki updates, any forward continuation must authenticate those
new publication preimages; never relax the old operator's drift checks.

After server access is verified, publish signed client2026102601 through the
reviewed four-file publisher. Verify all141 HTTPS assets and signature/pairing.
Then publish the combined499-file wiki and verify public hashes/security headers.
Protected reference/player client installs are untouched; users update with Play.
Gameplay QA remains open: ../QA.md and ../../../items/paladin-weapon-grip/QA.md.
