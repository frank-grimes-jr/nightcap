# Class-armor deployment and Palwar correction

The owner explicitly authorized promotion to main, production deployment and
upgrading Palwar's three affected pieces after confirming logout. Main PR285
merged at `7f97288e7972b80f0e5003c9ca725dc542a692bd`. `apply.json` verifies the
October22 17:07UTC activation. Native gameplay/balance acceptance remains open
in [QA](../QA.md); deployment is not player acceptance.

## Verified outcome

- The configured quest root, container mount and all existing version-directory
  overrides were checked. All eleven original scripts matched retained hashes.
- All37 existing Ascended IDs and names were present in the current paired
  item cache. No cache, native binary or client update was performed.
- World reported zero clients, including character-select/zoning states. Under
  deployment/GM locks, world admissions were locked and the gateway paused.
  Zero was rechecked after settling and after the global Quest reload.
- All eleven scripts match the reviewed new hashes. Twelve aggregate Quest
  acknowledgments occurred without quest errors; the log does not identify
  every idle worker individually. World plus twelve zone lifetimes and all five
  service identities/start times were preserved.
- Palwar's complete saved inventory was read twice after reload and remained
  stable. A single InnoDB transaction guarded all17 columns of each target row.
  Only slots7/17/19 item IDs changed:4176/4174/4180 to604176/604174/604180.
  Full afterimage comparison preserved every other field and inventory row.
- Admissions were restored and services verified. No old player snapshot was
  restored. Already-owned items are not generally converted by the quest change.

Current live state is authoritative. The earlier `probe.json` and `verify.json`
are preflight evidence; a separate robe release changed the public client
channel before activation. The actual before/after channel in `apply.json`
matches, so that concurrent release was preserved.

## Tests and review

Seventeen operator fault tests and five actual MariaDB10.5.4 rehearsals passed.
The latter execute SQL captured from `repair()` against a connection-local
temporary inventory table: all17 fields/unrelated rows preserved, charge drift,
case-only and trailing-space custom-data drift roll back all writes, and replay
rejects. Only a local disposable schema was used and it was removed.
Windows ownership/directory-fsync boundaries are mocked in unit tests; actual
file fsync, replacement and partial recovery execute. Original113 Lua,39 Perl
and21 source-validator tests remain recorded in ../verification.json.
Independent review and corrected recovery findings are in `review.json`.

The later ingredient-tier audit identifies root plugins/ as the active native
helper path. Historical Perl tests here execute captured quests/plugins fixtures;
they do not establish native currency behavior. The separate quest-tier-handins
candidate corrects that pre-existing Kurron behavior and broadens tier matching.
It is not part of this reward-only deployment; retain its separate release gate.

## Retained recovery

Private full inventory rows, attempt receipts and eleven original files are at
`/opt/nightcap/backups/quest-armor-20261022`, mode0700. They are not published in
the wiki or copied into Git. `deploy.py apply` refuses replay. After uncertain
tool completion, inspect the existing remote receipts/live state first.

`deploy.py rollback` restores only authenticated quest originals and reloads
quests, preserving earned gear and player state. It requires unchanged original
runtime identities and a zero-client admission hold. An attempted inventory
write cannot release the hold without a successful SQL-client completion marker
and an exact original/intended afterimage comparison. A missing marker or SQL
error requires proving the original MariaDB session is terminal before a
separately reviewed recovery; observing old rows alone is insufficient. Never
restore the old inventory preimage or kill a production zone process.

## Wiki

The whole wiki impact review covers21 maintained articles,432 generated routes
and384 catalog values. Six guides gain Live testing notices; commands/catalog
values remain unchanged. The first updater stopped on the website lock before
any publication. The concurrent robe-waist release was then preserved from its
verified source/receipt, and the rebuilt payload changes only six armor guides
plus search. Publication and public verification receipts accompany this file.
