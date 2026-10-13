# ADR 0042: Canonical spell eligibility with per-character presentation

Status: verified implementation candidate, September 20, 2026; in-game acceptance pending.

Production Monktest (CLR/MAG/NEC) could not see secondary-class vendor scrolls
with the usable filter enabled, and purchased scrolls could report level 255.
RoF2 tests the primary class in separate merchant, item-scribing and spell-level
paths. Legacy class selection additionally widened shared database spell columns;
11,057 packaged spell rows differ from preserved original class levels.

Use one generated immutable spell class catalog for server authorization and the
client projection. Its source is the existing pinned original spell file,
SHA256 `bae7ba7d897962f67581e3e731b94f4a31898d160c30c2edb74912b21aa11880`.
Exclude the malformed historical custom AA row 99001 (230 fields); the current
42604 recall remains on its independently validated AA path. Unknown learnable
spells fail closed and require a reviewed catalog update. Item/AA spell actions
are not converted to ordinary memorized-spell authorization.

The server derives required level and best caster from original levels and the
held classes, checks ownership again at gem casting, and stops widening
`spells_new` on class selection. Existing database values, spellbooks, inventories
and player progress are retained. No database-wide rollback of historical class
columns is required; other consumers of those legacy columns remain a documented
limit until separately migrated.

The pinned RoF2 proxy uses the validated NCUI1 character identity/classes to
project only local primary-class spell queries. Merchant level/usable checks and
scoped scroll scribing/placement recognize the held-class union. Scroll masks
come from the canonical catalog even when item masks were globally widened.
Native zero masks, race/deity/item restrictions, other queried classes and
non-scroll item behavior stay native. No client item or spell memory is globally
rewritten. The signed spell asset restores only original class-level fields;
the separately generated recall is validated and preserved.

October 12 early-scribing candidate: selected-class scrolls can enter the book
before their canonical spell level. Only the server scribing comparisons and
the client's dedicated spellbook level query change. Canonical ownership,
inspection/menu levels, gem memorization and gem casting remain level-gated.
See [paired candidate and QA](../releases/early-spell-scribing-20261012/README.md).

All added offsets and whole instructions are verified against the exact supported
executable and signed catalog. A required runtime feature stops startup if any
hook fails. Identity requests run at game entry and HUD/UI access; state clears
across non-game transitions. A response racing the first merchant list remains
an explicit immediate-login QA case.

Alternatives rejected: resynchronizing global widened rows would keep leaking
access between characters; making every scroll usable would hide ownership bugs;
changing the primary class would affect unrelated client systems. The canonical
catalog is deliberately explicit, following the existing pet ownership design.

See [release and exact QA](../releases/production-bugfixes-20260920.md).
