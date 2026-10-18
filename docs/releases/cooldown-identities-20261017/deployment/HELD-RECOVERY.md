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
