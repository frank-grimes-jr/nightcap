# Living economy activation

September 20, 2026. **Active QA candidate; manual acceptance and main promotion
remain open.** The owner approved a full backup, map repair and world/all-zone
restart, plus preparation of a separate QA-client terrain update.

## Verified live state

The final activation audit completed at 17:25 UTC. World PID 42812 and all eight
zone workers run the corrected binaries below. Every zone has an established
world connection. The native health audit found no Error/Fatal/Perl runtime
errors; 14 startup log files were checked. Spire initially reported stale counts,
but its final snapshot agrees with all eight native workers.

| Check | Result |
|---|---|
| World SHA256 | `c7a008e95615ff7f74cdca946ef889ad013052227b5593854e56e0091d8c51b3` |
| Zone SHA256 | `6f110f50ad9018a380f65fe47bd4cc0388bb7c4103a9665d569902d4411a843e` |
| Economy | Enabled, epoch 1; 10 find + 6 sell + 4 buy offers, all remaining 1 |
| Trades at verification | Zero; no player transactions were simulated on live PEQ |
| Runtime files | All 29 effective source/plugin/quest hashes match |
| Six residents | All 30 exact database afterimages match |
| Preservation | 12 table fingerprints unchanged across SQL; 11 unchanged after boot, excluding saved-zone state |
| Existing class merchants | 1,747 listings, 1,229 unique items retained |
| Required rules | Classic era, AA minimum 1, saved state enabled, item rolls 4, vendor payout 2.5 |
| Automated tests | 61 passed / 1 existing opt-in skip; 23 resident quest assertions passed |

Source release: `46283a6`, travel guard `98691d0`, build-provenance repair
`8fbfddd`. These are promoted through dev/test only. Pricing still requires owner
balance acceptance: current scaling models increased item-roll/vendor income,
not a raw coin multiplier, then adds the requested seller premium.

## Backup and recovery

Full consistent PEQ backup, including routines, triggers and events:
`E:/EQ_Local_Dev/artifacts/living-economy-20260920/activation/peq-before.sql.gz`.
SHA256: `5b3944119f28581448c262a78cefb26e4e7d3eb83a4a22db3c9682df040fd322`.
Verified size: 46,407,267 compressed / 441,720,304 uncompressed bytes.
All eight original zones saved and exited without forced termination.

The first startup failed before opening zones because the initial world artifact
retained an obsolete one-argument SQL call. Current source/SQL require three.
The launcher retry loop was stopped; epoch remained zero with no offers/trades.
All changed C++ sources/headers and their dependents were rebuilt, source hashes
were checked against the reviewed manifest, and the actual binary contract was
verified before replacement. See [detailed verification](VERIFICATION.md).
Do not redeploy the rejected initial artifact hashes listed there.

The guarded schema/content/resident SQL stages completed once. Do not rerun them
blindly. No existing merchant stock, character state or unrelated saved spawns
were cleared. Native saved-state loading includes newly added spawn2 records.
Resident exact-row SQL guards were slower than expected on the live catalog;
future generated guards should add indexed identity predicates while retaining
all exact preimage checks. This did not require weakening or retrying SQL.

Retained evidence directory:
`E:/EQ_Local_Dev/artifacts/living-economy-20260920/activation/`.
It includes original file/binary manifests and backups, SQL journals,
`first-start-failure.log`, corrected `rebuilt/` artifacts, effective manifests,
`live-verification.json` and `native-health.json`. Original evidence was not
overwritten by recovery. Use the scoped rollback procedures in [market QA](QA.md)
and [resident QA](residents/README.md); do not restore a full backup over later
player progress merely to remove this feature.

## Remaining gates

The configured `lavastorm_v0.map` alias is installed from the pinned Classic
source; all 25 positions pass the installed-map geometry probe. However, the
original client, approved separate QA copy and owner-suggested `E:/EQ_Local`
client all lacked `lavastorm.s3d` at activation. The owner has since supplied
the asset; its archive contents and ring geometry verify, and the update is
staged. Signing/build/installation remain pending after dependency approval
was blocked by the approval service's usage limit. No client files were changed.

Khalure offers eight Classic rings; missing global readiness hides Lavastorm and
rejects old links. Do not enable it just because one client was patched.
[Client terrain prerequisite](residents/CLIENT-TERRAIN.md).

Owner QA must still verify all six costumes, Trift's OOC story, each offered ring,
normal-account WTS/WTB, city merchant stock, failure/refund cases, simultaneous
purchases and restart-only rotation. Exact NPC names, positions and expected
results are in [market QA](QA.md) and [resident QA](residents/README.md).
