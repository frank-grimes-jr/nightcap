# Faction display OVH release — October30, 2026

Prepared under the owner's renewed deployment authorization. Activation and
access reopening must be recorded separately; no owner gameplay acceptance is
inferred from automated checks. Main feature PR378/3c3d815e is the source scope.

## Payload and preparation

The faction-only zone is built by tools/build_faction_release.py. It authenticates
the retained Hate source/objects, reproduces the baseline and recompiles only the
command unity unit. native-build.json records this selective rebuild. The
53,022,096-byte shipping copy fa77ba02 preserves all mapped bytes, allocated
sections and runtime headers of the full debug build d4ee3a64; see native-identity.json.
Keep the full local debug executable. No unrelated augment/capacity change ships.

prepare_host.py authenticates the live baseline and reviewed helper source,
keeping detailed runtime inventory on-host. State-helper core token comparison
excludes two appended, unused function definitions; all core source matches.
The bounded preserve_staging.py archived five authenticated unmounted copies,
verified decompressed SHA256, fsynced archives/restoration receipts before
unlinking originals and preserved service/image identities. The user explicitly
approved this step; active images, backups, mounts and player data remain intact.
Restore recorded bytes/mode/owner before using an affected historical operator.
Full receipts are under /opt/nightcap/releases/faction-standing-20261030-v1 and
adjacent to each retained archive. Compact summaries are committed here.

stage_release.py verifies the exact three-file package, authenticates the manifest
and runs27Linux fault/recovery tests on the host. Manifest and private backup stay
on-host. Operator validation also passes Windows and the local Linux container.

## One-time activation

run_action.py preflight authenticates current image, command access/aliases,
51schema/650content predicates, world cleanup guards, current caches/quests/client
and service lifetimes; it builds a zone-only image with dependency/startup/crypto
checks. No gameplay restart occurs in preflight. Reserve672MiB before activation;
retain512MiB after the fresh stopped backup and before reopening.

run_action.py activate takes deployment/GM locks, closes gateway admissions,
gracefully stops the whole supervised game, captures current saved state and
takes a verified full backup. It models exact native cache expiry, installs the
new image, then verifies12zone hashes, one expected market rotation, saved state,
content/quests/caches/client preservation and native health behind closed access.
Only native command registration may add factions/access0; existing settings
and aliases must remain exact. Do not kill individual zone workers.

run_action.py open requires the authenticated closed verification, unchanged
saved state/market/publication and all health guards before reopening admissions.
Exclusive logs/receipts prevent replay. Failures hold access and record evidence;
inspect the actual state instead of rerunning an uncertain action.

## Recovery and QA

The retained operator supports an explicitly authorized recovery to the immediate
prior compatible Hate image, with a new stopped backup and current earned state.
Old native startup removes only its now-unknown factions command row; all other
command settings remain guarded. Unverified activation or uncertain opening
requires a reviewed continuation, not a newly assumed baseline. Never restore
an old player database, erase receipts or broadly exempt state drift.

The parent README owns exact player QA: ordinary-account #factions in East
Commonlands, Qeynos search/paging, target-NPC lookup, min/max values, modifiers,
white text, scrolling/resizing and persisted faction hits. Visual/gameplay QA
remains open. No signed client update is required. Wiki source availability must
be updated after verified activation; public publication is tracked separately.

## Pre-shutdown normalization continuation

The original activation stopped before creating its activation directory or
stopping services: only the zone checksum changed after preflight. Same-day
capture comparison identified map_file_name/content_flags/content_flags_disabled
on id163/hateplaneb186/version0 changing NULL to empty strings. A temporary SQL
clone with only those three fields reverted to NULL reproduced the exact original
preflight checksum; all other content stayed exact. No live content was rewritten.

The retained native ApiGetZoneAttributes calls SaveZoneCFG; ZoneRepository maps
these NULL strings to empty strings and writes the whole row. This is a matching
native writer path; the calling actor was not logged, so actor attribution is
not claimed. Preserve the normalized live row. The old attempt/log/preflight stay
immutable. resume_normalization.py repeats the exact clone proof and admits only
that one checksum difference, verifies unchanged service identities and invokes
the original activation under the same locks and state-preservation checks.

Use run_action.py activate --normalization and open --normalization for this
continuation. Any future authorized rollback/open-rollback must also use
--normalization; the original preflight intentionally rejects the known drift.
Six continuation guard/routing tests pass on Windows and the host. Independent
review found and closed the recovery routing gap, with no remaining blocker.
Never rerun the failed original activation or substitute an unexplained baseline.
