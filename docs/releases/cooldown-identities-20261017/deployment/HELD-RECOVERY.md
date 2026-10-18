# Verified checkpoint continuation

The original activation completed the stopped full backup and both directions of
the real-catalog migration rehearsal. Its next preservation check held both game
and gateway before `migration-attempted.json` or any live migration SQL existed.
The scratch schema had been removed; live timers and item timestamps were intact.

The owner concurrently requested a character port in **Port Karl to Befallen**,
chat `01a14f71-6c38-7f42-afc7-6b00dcbabba5`. That chat's executed location-only SQL
explains the difference. Restoring only the backup's character table into a fresh
disposable schema reproduced the exact original fingerprint. Comparison found
one row with only the five requested location fields changed; every other player
and custom table, timer and item timestamp matched. The live database was never
restored. Detailed row evidence stays in the private production stage.

`resume.py` is a separate, one-shot continuation, reviewed independently by the
parent after implementation. It authenticates the original manifest, exact prior
hold, private comparison and original/new character fingerprints. It rejects
different changes, new holds, any live migration state or replay. Both maintenance
locks and stopped states are required. A fresh supplemental full backup preserves
the port before continuing at the original migration checkpoint. The completed
rehearsal and original backup are not replayed or replaced.

Its separate manifest pins `resume.py` and `test_resume.py` under the immutable
release's `resume/` directory. Original operators and receipts remain unchanged.
Closed verification and opening use only the narrowly reconciled baseline; the
exact original hold remains and is linked by a resolution receipt. Any new failure
holds both services. No player comparison or restore happens after access opens.

The isolated rehearsal took longer because CTAS copies omitted lookup indexes.
It nevertheless passed in both directions. Future operators should preserve those
indexes before full-catalog joins. This does not justify skipping guards or
replaying an uncertain migration.

## Committed migration and finite market pools

The resume committed and verified the live migration, then held at the original
market check. The existing rotation procedure can legitimately leave slots empty:
five eligible find items with a two-offer duplicate limit fill ten of twelve
actors. The original validator incorrectly required44 offers; there were42.
Both services stopped and the original committed migration remained intact.

The separately manifested `finish.py` pins both prior manifests, both held-receipt
hashes, the exact stopped game identity/lifetime, the resolved location baseline
and migration receipt. It has no migration SQL or backup-restore execution path.
It validates every offer, actor maximum, item eligibility, price, duplicate cap,
merchant exclusion and epoch. Every deficient actor must have zero remaining
eligible candidates using the procedure's full predicates, including actors with
zero offers. An arbitrary shortfall is rejected.

The first rotation80→81 was verified while stopped. After restarting only the
already migrated image,81→82 was verified against that new lifetime. All twelve
zone hashes, native health and preserved data passed before gateway opening.
The final report records access open and owner gameplay acceptance pending.
Original and supplemental backups and both holds remain private and unchanged;
only sanitized receipts and aggregate counts are committed here.

The original25 operator tests,9 resume tests and7 completion tests pass. The
completion suite covers19 scenarios including eligible underfill, invalid offers,
data/receipt/image drift, lost start acknowledgment and pre/post-open failure.
