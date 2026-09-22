# Tunnel travel alcove: production activation

Deployed September 22, 2026 at 18:01 UTC (14:01 Eastern) to
`play.nightcapgame.org` after the owner explicitly requested main promotion and
production deployment. Main promotion: [PR 66](https://github.com/frank-grimes-jr/nightcap/pull/66),
commit `eba1eeea1320e36b80425379f9b4fc78b77c0d3f`.
This is release authorization; manual appearance and gameplay acceptance remain
open in the [exact owner QA](README.md#exact-in-game-qa).

## Installed and verified

The ten outbound city stones are replaced by one Merrin spawn and three native
props. All ten destinations and exact landings, plus twelve return/PoK books,
are preserved. Production's newer tunnel services remain in place. Three files
were added under runtime `quests/`: `plugins/tunnel_travel.pl`,
`plugins/tunnel_travel_data.pl` and `ecommons/999810.pl`.
No native binary, supervisor, image, client asset or public launcher release changed.

The retained image is `nightcap-game:tunnel-services-20260921`, immutable ID
`sha256:7219a5e43b6f00e96e6abf88914e309f0ea3c36ad381a9f840f6a605c8e0c570`.
All 15 running native executable hashes match that release. Game health passed
with zero restarts and no matched quest API, native crash or database startup
errors. The gateway is open; all four TLS-verified native handshakes passed on
ports 5998, 9000, 7778 and 7000. These are transport checks, not a RoF2 gameplay
session or a visual acceptance claim.

Before changing live content, closed the gateway, gracefully stopped game
writers and captured production's own preimages. The full 445,454,139-byte
uncompressed PEQ backup passed integrity checks and restored into isolated
MariaDB using the production DB image, with no network, production volume or
published ports. Backup archive SHA-256:
`041590cd1c330f1a77b42ea8117a1307058980c2317bf3b2048489265e5434ed`.

All 20 SQL regressions and exact forward/rollback checks passed on the stopped
production snapshot. Forty-six preservation fingerprints matched in the
restored database, after application, and after startup before reopening:
character/account data, inventory, quest globals, starting rules, market audit,
rule values and merchant rows outside the normal rotating market range.
The existing startup policy advanced the market once, epoch 5 to 6, producing
20 sale offers, 12 buy offers and ten merchant finds with one copy each.

Readback confirmed one guide NPC, one guide spawn, three scenery doors and
twelve retained books; every scoped static row matches the generated result.
All three runtime file hashes and in-container Perl syntax checks passed.
Post-start guide saved state also passed the strict reference checks. Seventeen
local deployment failure tests passed, and independent review found no remaining
blocker after corrections to saved-state verification and the quest mount path.
Original migration, quest and geometry checks are in the dated
[local activation](ACTIVATION.md).

## Evidence and recovery

[Sanitized production record](PRODUCTION.json) contains the manifest, backup,
rehearsal, activation, content readback and public handshake evidence.
Local operational artifacts:
`E:/EQ_Local_Dev/artifacts/tunnel-travel-alcove-20260921/production-20260922/`.
The immutable package SHA-256 is
`459dbdba83ad917d452547943274f847f1dcb6e09268094fdbd454095751c4be`;
its manifest SHA-256 is
`2fa6586d78a2da190feae87870f94cf13e1a20b796a20150b8ca2ef4fdd518ad`.

Private backup, preimages and target-specific SQL remain on the production host:
`/opt/nightcap/releases/tunnel-travel-evidence-20260922/`.
The pinned helper and main-revision source package are in
`/opt/nightcap/releases/tunnel-travel-20260922/`.

For an authorized rollback:

```sh
sudo -n python3 /opt/nightcap/releases/tunnel-travel-20260922/rollout.py rollback
```

The helper closes access, saves zones, captures current preservation fingerprints,
verifies the pinned artifacts and generates rollback SQL against current scoped
state. It restores the original stones, removes the new guide definitions,
unambiguous guide saved state in EC instance zero and the three matching quest
files, then verifies the unchanged native runtime and preserved data before
reopening. Other-instance, other-zone, corpse, partial-ID or content drift leaves
the gateway closed for investigation. Never bypass those guards or restore the
full backup over later player progress. A restart follows the existing market
rotation policy.

A failed preparation retains its private evidence and requires an operator to
retain/rename that evidence before a fresh attempt; no live content is changed
until the prepared artifact hashes and full rehearsal pass.
