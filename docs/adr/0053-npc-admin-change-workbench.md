# 0053: Local NPC workbench with portable change sets

Date: 2026-10-04
Status: implemented; local utility verified, owner in-game acceptance pending

## Intent

Give the Nightcap owner a local admin utility for routine NPC placement, loot,
appearance, combat, spawn and merchant work without repeatedly asking Codex to
write SQL. Preserve the ability to review and push the same edits to GitHub and
apply them to a selected server. This is content administration, not a player UI.

## Decision

Add `eq-npc-admin/`, an independent Vue/Express application. Keep the existing
character/account GM tool intact. An NPC-centric workspace joins template,
spawn, loot and merchant records; it exposes shared-resource impact before an
edit. Drafts persist locally, contain original and proposed values, and can be
exported as portable JSON plus review SQL. No draft save writes to PEQ.

Server targets are explicit named profiles. Local Docker uses port 3307;
remote databases use an owner-configured SSH tunnel or TLS connection. Secrets
stay in an ignored local config. Every apply compares the original rows, checks
schema/transaction support, saves a before-image, commits a single transaction,
and records a receipt. Rollback uses reverse comparisons and cannot overwrite
intervening changes. Git publication writes only the selected change set into
an isolated branch/worktree and pushes a feature branch; it never sweeps up
unrelated workspace changes or promotes gameplay to main.

## Practical advantages over ad hoc Codex requests

- Search by NPC name/ID and zone; navigate directly between an NPC and its spawns.
- See coordinate placement, heading, respawn timing and alternative spawns together.
- Inspect loot-table and lootdrop sharing before changing odds or adding items.
- Search items by name for loot and merchant inventory, retaining era restrictions.
- Keep durable drafts, before/after review, drift checks, backups and rollback.
- Display exact reload/activation steps; distinguish database applied from in-game active.
- Retain a GitHub audit trail for every selected content change.

Codex remains useful for new quest logic, schema/C++ changes, complicated balance
analysis and diagnosing server failures. The utility should own repetitive,
bounded edits with immediate visual feedback.

## Alternatives

1. Extend Spire: broad existing editors, but requires a maintained fork and a
   Nightcap-specific change/deploy layer.
2. Extend eq-solo-gm: reuses Vue, but its immediate-write API and unrelated
   character controls make a poor boundary for reviewable NPC content changes.
3. Dedicated workbench (chosen): focused workflow and smaller write surface;
   requires implementing the relevant joins, validators and deployment checks.

## Acceptance and evidence plan

1. Launch locally with a documented command and loopback-only API.
2. Browse real configured PEQ data; clear connection and empty-state errors.
3. Edit NPC locations, loot tables/drops, NPC stats/appearance and merchant stock.
4. Durable draft staging, item lookup, shared impact, before/after review and export.
5. GitHub feature-branch publication isolated from existing dirty/staged files.
6. Selected-target preflight, transactional apply, before-image and guarded rollback.
7. Saved-state-aware placement handling and accurate activation guidance.
8. Automated domain/security/integration tests plus rendered browser verification.
9. Rehearse writes and rollback in a disposable database, not live gameplay rows.
10. Document exact owner in-game QA; never claim manual acceptance from DB checks.

## Build order

Implement `api/domain.mjs` and tests first (table/field allowlists and reversible
changes); then `api/database.mjs` and `api/changes.mjs` (browse, impact, preflight,
transactions); `api/git.mjs` (isolated publication); `api/server.mjs` (local API);
Vue workspace components; disposable DB and browser verification; runbook,
changelog and phase report. Deployment concurrency and saved-state activation
are the highest-risk portions and require explicit failure/recovery tests.

## Boundaries

No arbitrary SQL/shell endpoint, client binary edits, expansion-rule writes or
automatic gameplay promotion. NPC/loot power changes retain owner balance QA.
Local HTTP protects against foreign origins and DNS rebinding. Database queries
use bound values and allowlisted identifiers; Git commands use argv without a
shell. JSON exports exclude credentials and operational backups.

Reference: https://github.com/EQEmu/spire and local EQEmu repository definitions
under `akk-stack/code/common/repositories/base/`.

## Outcome

The independent app and Windows launcher are implemented. Database and browser
rehearsals cover placement, nullable loot defaults, full merchant metadata,
FLOAT/BIGINT storage, rollback and uncertain-commit recovery. Git exports use a
durable manifest, pinned base/commit, and full-tree checks including gitlinks.
Rollback snapshots come from locked target rows, with schema-aware comparisons.
See `eq-npc-admin/QA.md` and `docs/milestones/phase-47-report.md` for evidence and
remaining limits. No live content, client binary or hosted deployment was changed.
