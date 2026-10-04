# Phase 47 — Local NPC Admin

Date: 2026-10-04. Candidate utility; no gameplay promotion or live content write.

## Built

Independent `eq-npc-admin` Vue/Express app, Windows launcher and local/remote
profile configuration. NPC search by name/ID/zone; template stats and appearance;
spawn coordinates, heading, respawn and path-grid assignment; schematic placement
plot and `/loc` paste; loot tables/groups/items and merchant stock; item-name lookup.
Shared NPC, zone/version and global-loot impact appears before application.

Durable 200-record drafts, revision checks, before/after review, portable JSON,
review SQL and isolated Git feature-branch publication. Git retry retains a pinned
manifest and rejects extra commits, pending files and hidden gitlink changes.
Fresh preflight, InnoDB-only serializable transactions, locked target before-images,
scoped saved-state handling, transactional receipt ledger, uncertain-commit recovery
and guarded rollback. Curated class-hub stock cannot bypass catalog policy.

## Verification

Node 24.17.0; MariaDB 10.11.19. Fifteen domain/API/store/Git tests and thirteen
database test-runner cases (twelve scenarios plus the parent) pass. The production
Vite build passes. Database tests include stale previews, induced write failure,
FLOAT decimals, lossless BIGINT and VARCHAR metadata, nullable defaults, merchant
restoration, corpse/unrelated/wrong-zone preservation, all-version spawns,
duplicate-key refusal, nontransactional-table refusal, and lost commit-ack recovery
through HTTP. Git tests use real temporary repositories and a bare local remote.

Independent fresh reviews covered deployment and publication boundaries. Concrete
findings became regressions. Live local PEQ field/engine compatibility and sample
NPC/item queries passed read-only. Browser tests used real copied schemas in an
isolated database on 3317: decimal movement, shared-loot and merchant additions,
destination confirmation, receipts and rollback. The actual live NPC data was
never used as a mutation target. See [exact evidence and owner QA](../../eq-npc-admin/QA.md).

## Cut and limitations

- No new NPC/spawn creation, loot-container cloning, terrain maps or path-grid editor.
- No quest/C++/schema editing, arbitrary SQL, era-rule editor or branch auto-promotion.
- Hosted credentials/tunnel must be configured locally. This release does not
  expose OVH database ports, stop game services or claim hosted runtime activation.
- Shared loot remains shared; review its scope before changing it. Full-schema
  target mismatch and duplicate composite keys fail closed.
- Single local operator. Retain `.local` receipts and the database ledger with
  backups. In-game visual/loot/encounter acceptance is still pending.

## Learning

Small synthetic schemas hid real nullable defaults and merchant metadata. The
browser rehearsal therefore copied actual table definitions before testing writes.
Precision must follow column types, and rollback evidence must come from locked
target rows. Git safety checks must explicitly include submodules regardless of
the operator's diff configuration. Keep these cases in future regression runs.
