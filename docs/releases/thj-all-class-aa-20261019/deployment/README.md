# All-class AA deployment — October 19, 2026

Owner explicitly requested main and server deployment for live testing. PR250
promotes the tested source at c3f0686. This release layers only the AA-policy zone
binary on the current combined item/spell/pet/WPM image, then changes only
Healing Boon389.classes518→550. Client2026101901, world/cache loader, rules,
quests and Classic50 remain. Owner gameplay acceptance is separate.

The operator authenticates all four AA tables against the tested fixture,
normalizing only the candidate Healing Boon field to its known preimage.
An isolated content clone rehearses forward/reapply/inverse/reapply/forward.
Only the exact afterimage is allowed. New SQL attempts have immutable attempted
and committed receipts; uncertain acknowledgments require diagnosis.

Activation uses shared deployment/GM locks, closed access, a stopped gzip-tested
backup and current player/timer fingerprints. The immutable image must have exactly
the base layers plus one and all other runtime binaries unchanged. All12 zones,
health, saved state, item/spell caches, Classic routing and market rotation must
verify before the separate open action. Capacity checks reserve backup, cache
regeneration and operating headroom. No old backups/images are pruned.

Recovery takes a fresh backup of current earned state, guards the inverse AA
content change and restores only the immediately preceding image. It never
restores player rows or erases new purchases. If access was never attempted,
current player/timer state must match the original stopped receipt and the first
startup market must independently verify. Later legitimate play is preserved.
Unknown content, routine remnants or uncertain SQL hold for explicit diagnosis.

Independent review is in review.json;21 operator/failure groups passed on Windows
and Linux, in addition to the candidate's57 tests and11,016 native eligibility
checks. The initial read-only preflight rejected a candidate/preimage fixture
mismatch before any image, clone, evidence or live mutation. The corrected check
is covered by a drift-rejection regression. Staging review revisions were applied
only before any activation evidence existed. Runtime receipts record the
actual deployment; original candidate verification remains historical.

## Verified outcome

Main PR250; immutable image `sha256:32bf376af4402c3288c83c5d72f2810b8d35ddae06327d5521d1efb6b20ef942`.
All12 zones match the reviewed policy binary. A fresh stopped64,416,158-byte
compressed backup passed integrity.47 player tables and28 custom/timer tables
were preserved; Classic50, item/spell caches, rules, quests and all138 current
client2026101901 assets remain exact. Market rotated85→86, with42 valid offers
within44 slots. Access reopened after checks; no snapshot restore or player
grant occurred. Owner gameplay/encounter balance acceptance remains open.

Wiki20261019-all-class-aa-v1 publishes the six reviewed AA guides. All465 public
files/security headers and five private routes verify; private assets, Nginx
configuration and all five service identities were preserved during publication.
