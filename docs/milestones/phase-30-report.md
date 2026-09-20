# Phase 30 - Named tunnel residents

Date: 2026-09-20. Additive candidate after the finite living economy.

## Built

Six owner-specified residents with persistent native costume materials/tints,
weapon models and hail dialogue. Sortre is the confirmed Dark Elf; Nalin wears
Classic planar Valorium with SoulFire. Trift is exactly level 12 and tells the
requested Butcherblock story in OOC every three to five minutes. Khalure offers
all nine Classic druid rings with explicit era-gated later destinations through
Luclin, local range/instance checks and guarded individual travel.

Repository regression: 59 tests, 58 passed and one existing opt-in skip, including
five resident tests. All 21 Perl assertions, 16 disposable-database checks and
five-point geometry checks at 25 locations passed. Independent review's ownership
finding and rehearsal's coordinate formatting bug are corrected.
[Evidence](../economy/VERIFICATION.md) and [exact QA](../economy/residents/README.md).

## Not Included

No equipment loot, new market offers, fee, player-state migration, client patch,
live activation or automatic post-Luclin travel catalog. No pricing changes to
the first candidate. No extended character backstories beyond requested flavor.

## Remaining Gates

The configured Classic Lavastorm map alias is missing. Its installed Classic
source is verified, but the alias must be installed and the normal probe rerun
before enabling Khalure. Backup, controlled activation, costume/landing checks,
owner economy balance acceptance and main promotion remain open.

## Operational Learning

Probe the map named by the zone row; a short-name map can refer to newer terrain.
Zero NPC RGB means no tint, not black. Persistent native material/tint fields
avoid equip-on-spawn visual drift and do not need loot-table gear. Fixed-precision
spawn coordinates must retain native formatting in exact rollback preimages.
Guard dangling references as well as reserved row IDs before adding tint sets.

## September 20 Activation Addendum

The owner authorized a fresh full backup, server map repair and controlled restart
for QA, plus preparation of a separate QA-client terrain update. The configured
map alias is installed; all 25 server positions pass the installed-map probe.
Classic Lavastorm client terrain is absent from both inspected workspace clients
and the owner's suggested `E:/EQ_Local` source. Khalure therefore withholds that
one destination and rejects stale links; no client files were changed.

Initial activation exposed stale build objects. The launcher was stopped before
any zones opened, all affected C++ inputs were invalidated, and both binaries
were rebuilt from unchanged reviewed sources. Future builds now require fresh
output and verify source stability and the actual binary startup contract.
The updated regression suite passes 61 of 62 tests (one existing opt-in skip),
plus all 23 resident Perl assertions. Historical preflight findings above remain
dated evidence; see [current verification](../economy/VERIFICATION.md).
