# Owner-authorized production rollout

The owner authorized main promotion, installation of matching native binaries
and an item cache, and a server restart on October 16, 2026 for in-game testing.
This supersedes the earlier test-only release boundary for this release. It
does not establish owner gameplay acceptance. Deployment evidence is recorded
separately from the original local package and fourteen-mode acceptance matrix.

`rollout.py` uses the pinned production helper from the October 9 zone-hunt
release and the reviewed October 16 equipment operator's publication, image
selection and maintenance checks. Their source hashes, including the imported
cache helper, are pinned in the release manifest. The previous image provides
unchanged loginserver, UCS, startup/configuration and other support files.
Only world, zone and shared_memory are replaced in one immutable image layer.

The retained-source audit verifies every old source path, all 104 normalized
overlay fingerprints, latest AA duration/projection dependencies, authentication
redaction and the exact equipment-loader source after removing the two dungeon
additions. Divine-summon, FreeTrade, DisableLore, race policy and the 1,332-byte
ItemData definition are preserved. Gameplay acceptance is still pending.

## Staging and phases

The host stage is `/opt/nightcap/releases/dungeons-20261016`. Verify the original
package SHA-256 before extracting only its binaries, SQL, Keeper quest and native
build manifest. **Do not install its local-content item cache.** Stage the actual
compiled `CacheMatches` verifier, `install-rows.json`, `target-content.json`, the
audited item-reference map, signed client verification receipt and operator/tests.
The manifest pins every input plus the freshly inspected production image,
binary hashes, restart baseline and current signed client channel.

Run each phase with `sudo -n python3 -u <stage>/rollout.py PHASE` over the pinned
host connection. Every phase takes the deployment and GM file locks and refuses
active GM maintenance or an in-flight GM SQL action.

1. `preflight`: verify the live baseline and signed publication; audit reserved
   references; build the immutable candidate layer. Copy only public content
   into a uniquely named database with empty player/instance dependency schemas.
   A scoped temporary account runs the real old/new loaders. Rehearse the exact
   schema/content/activation SQL, verify every existing public row is unchanged,
   check all 330 new items and compare every old cache record byte-for-byte.
   Remove the temporary account and its private configuration on completion.
   The public-only clone is retained for diagnosis. Gameplay stays open.
2. `activate`: recheck all preimages, close gateway and stop the complete game
   cleanly. Capture stopped player/custom fingerprints and a verified full
   private backup. Apply additive schema/content, atomically replace only the
   Keeper quest, select the image and let startup regenerate the item cache from
   the actual production database. Check all running hashes, cache contents,
   public/player/custom preservation and signed client. Enable revision
   2026101601 only after those native/cache checks. Access remains closed.
3. `open`: revalidate the activated process identity, all preserved data, cache,
   content, rules and signed publication. Persist the opening record before
   requesting gateway startup. After that request, never compare or restore a
   stale player snapshot. Verify current process continuity and access.
4. `report`: verify running binary hashes, zero new container/native restarts,
   errors, active revision, cache and unchanged supporting services/publication.

The manifest's baseline restart count records prior history; it is not a claim
that the old release never restarted. Candidate checks require zero restarts.

## Recovery boundary

Any activation failure closes access and retains current SQL, receipts, image
selection and evidence for reconciliation. An existing opening record also
closes access and refuses replay, even if a previous process died after opening
the gateway. Do not remove evidence markers to bypass this boundary. Diagnose
the recorded phase and actual state before preparing a bounded recovery action.

Do not automatically return to an older binary after managed runs exist. Disable
new acquisition with `nightcap_dungeon_state.enabled=0` under maintenance while
keeping matching native code, all catalogs, runs, corpse state and receipts.
Existing managed runs and earned claims continue. Never drop the added item or
ledger tables or restore an old player/database snapshot to undo this feature.
The private backup is retained for disaster investigation, not routine rollback.

## Review and tests

The independent provenance review found no missing or regressed retained source.
The operator review found and repaired native `spawn2` identifier validation,
the equipment helper's explicit import/pinning, uncertain opening replay, and
the native items table's UNIQUE ID index (which is not a primary key). All eighteen
offline checks pass, including schema failure after a verified backup, opening
journal failure, lost acknowledgment, process failure, drift, duplicate opening,
cache preservation the actual unique-index shape and the active read-only configuration mount. The owner retained the
current-model review; no additional model was requested.

The first complete raw-row content fingerprint exceeded the database container's
2 GiB cgroup memory limit. Kernel evidence records an OOM kill at 18:53:02 UTC;
MariaDB recovered and was ready at 18:53:04 UTC. Game/gateway containers did not
restart. No feature migration or activation had begun. Fingerprints now stream
compact SQL row digests, retain FLOAT precision through DOUBLE projection and
limit each operator SQL session to 128 MiB. Eighteen offline controls pass,
including the memory/streaming contract and credential-error redaction. Treat
this incident separately from the later successful rollout health record.

Native runtime interruption experiments, CT geometry/paths/doors and level-50
Vox/Nagafen balance remain owner-test work in `../QA.md`. Do not inject failures
into this live host. The source wiki must be updated after deployment; public
website publication remains separate from the game rollout.

The production rehearsal also identified MariaDB's documented collation alias:
`utf8_general_ci` is reported as `utf8mb3_general_ci` on newer MariaDB versions.
The generated native and SQL schema contracts canonicalize only this exact alias;
all other schema metadata remains strict. The actual SQL fixture and isolated
production clone accept both aliases and reject `utf8mb4_general_ci`; the fixture
also rejects a changed column length. See `schema-alias-verification.json` and
`tools/tests/test_dungeon_contract.py`. All eleven focused dungeon tests pass.
The [MariaDB collation reference](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/supported-character-sets-and-collations)
documents the alias. No production column alteration is needed.
