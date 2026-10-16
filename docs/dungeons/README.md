# Raid and Grind release candidate

October 16, 2026. Feature branch only; installation, production activation and
owner gameplay acceptance have not occurred. The accepted contract is
[SPEC.md](SPEC.md). Do not describe a build or SQL rehearsal as gameplay QA.

## Behavior and catalog

The seven existing Keepers offer Raid, Grind, Enter, Join, Status, Claim Rewards
and Reset. Runs last twelve wall-clock hours, support up to six participants,
and keep their creator's mode. Each character must earn encounter credit for
every required boss; the shared unlock does not supply missed personal credit.
The encounter sphere is 200 units in the current instance. Group and owned-pet
attribution follow the native owner/party functions. Death near the encounter
does not by itself remove a connected party member's credit.

Grind keeps native difficulty and respawn duration/variance. Raid uses 135% HP
and 115% outgoing damage, including NPC spells; owned pets are excluded. Raid
mini-bosses precede the final boss, and killed spawn points never return.
Tasks show the authoritative checklist and mode until the original deadline;
Keeper Status also shows permanent completion counts. Abandoning a task only
removes its display until the next status/entry refresh.

`catalog.json` contains 52 objectives and 330 item definitions: 24 shared designs
at four equipment bands and three qualities, plus three exclusive designs per
dungeon in two Raid qualities. IDs are 960000–960329; Tasks are 9700–9713.
Grind completion is Normal; Raid completion and exclusive drops are 90%
Polished / 10% Ascended. Raid final bosses drop one/two/three distinct exclusive
designs at 80/18/2%. Designs are uniform and independent of class. The run seed
and per-character entitlement remain fixed across reconnects.

Items are permanent, tradeable, not attunable or lore, and have zero resale.
Weapon delay does not change with quality. Bags use 6/8/10 slots, at most ten
slots and 100% reduction. Existing native models/icons and the Tasks UI are
used. The dungeon ID range cannot enter the legacy or zoneforge upgrade paths.

## Persistence and recovery

`dungeon_service.cpp` owns native operations. `instance_list.notes` contains the
47-byte `nc-dungeon:<UUID>` marker; a run also matches the allocation start time.
Native instance IDs alone never identify a run. A no-retry transaction records
death, encounter credit, completion eligibility and the finalized native corpse
before publishing death. Grind respawn deadlines and death timestamps are
stored with that transaction. Successive Grind corpses have independent UUIDs.

Corpses retain native items, bonus items, currency, loot rights, private-corpse
timers and absolute decay. The existing advanced-loot receipts prevent replayed
items/currency from paying again. Managed checkpoints live under the permanent
run UUID and work independently of `Zone:StateSavingOnShutdown`. A death newer
than an old checkpoint prevents that checkpoint from restoring the old NPC.

Personal delivery calls the existing `NightcapLoot::ReceiveItem` after committing
the immutable entitlement. Inventory and its physical-drop receipt commit in
one transaction. Full inventories leave an earned Keeper claim. Ambiguous
delivery quarantines the client; do not retry in memory or clear the receipt.
Expiry/reset never deletes earned claims or completion history.

Reset is creator-only, confirmed for the same run within thirty seconds, and
refused while a participant is inside/entering or an unburied player corpse
remains. The entry reservation persists until a completed connection confirms
the character's location. A failed transfer can conservatively block reset;
reconnecting outside acknowledges that the character is outside. Never clear
presence manually without proving the transfer is cancelled and character is
outside. Retired native allocations remain reserved until their original expiry.

On a database ambiguity, the zone suspends managed death/spawning and retains
its last good checkpoint. Reboot the matched candidate in an authorized test
environment, then inspect UUID-ledger state and receipts. Do not delete ledger
rows to make a run work, reuse an old player snapshot, or load managed state in
an older receipt-unaware binary.

## Content provenance and isolation

`local-content.json` is a dated **local** public-content preimage, not a
production capture. Installation guards selected existing objective identities
and all reserved ranges. Runtime checks verify the schema columns/keys,
explicit content rows and the matching item-cache projection. Drift refuses
new runs and managed boot; investigate it instead of weakening the gate.

Classic Cazic-Thule uses the maintainer's pinned Quarm archive, SHA-256
`f49d712b45a193f737cb0f4de07fec7bf43c6c813e389ff9e7521b3915529b09`.
The parser reads only allowlisted public literal rows, never donor players,
accounts, executable SQL or triggers. Adapted content contains 188 spawn points,
29 NPC types, eleven paths with 128 nodes, and six objectives. Twenty-one donor
points reference a missing empty group and are explicitly excluded. All 32
relevant doors match the local public definitions and need no replacement.
The preserved level-39 Avatar reference supplies its 3,000 HP, 16–80 damage
and Shadowknight spell-list restoration. Four later-era caster spells are
explicitly removed: 1419, 1445, 2551 and 2554.

Private CT populations use a dedicated table; no public spawn2 row is added,
removed or replaced. Imported NPC/loot/spell identities use 985000+, private
spawn identities 9000000+, spell-entry identities 9800000+, and CT grids 9900+.
Native loot identities are matched to existing items, including five audited
article-name aliases. `permafrost-era-audit.json` records the donor's later-era
Ice Witch/Greshvoule gates. Chilling Terror lacks a qualifying NPC/spawn in the
pinned export. All three are explicitly suppressed inside managed Permafrost;
the local Chilling Terror point lacks an era gate. Public populations are unchanged.

Sources: [maintainer archive](https://github.com/SecretsOTheP/EQMacEmu/blob/main/utils/sql/database_full/quarm_2023-10-01-00_19.tar.gz),
[preserved Avatar](https://www.takproject.net/allaclone/npc.php?id=48003),
[contemporary Velious spell list](https://groups.google.com/g/rec.games.computer.everquest/c/bSotaKa9xS4),
[Luclin scroll distribution](https://www.takproject.net/allaclone/item.php?id=7654).

## Build, installation and disablement

1. Compare the integrated overlay with the latest retained deployed manifest.
   The feature integrates the deployed AA branch: projection, level-change
   refresh, expanded policy and Triple Backstab. It also retains credential-log
   redaction. The build driver asserts these match the October 15 retained
   source; main/dev alone were incomplete. Do not build from the stale default
   `E:/EQ_Local_Dev` checkout or replace unrelated current custom source.
2. Rehearse `20261016_dungeons.sql`, then `20261016_dungeon_content.sql`, in a
   fresh isolated database. Both start disabled. Existing/partial schemas or
   collisions require investigation. A failed stored-procedure invocation can
   leave the procedure definition; inspect and drop only that candidate
   procedure before retrying against a verified preimage.
3. Run `tools/dungeon_contract.py` only after the current migration/schema
   rehearsal. Generated schema/content/cache checks belong to the same build.
   Use `tools/build_dungeon_candidate.py` in the isolated retained-source build
   area. Pair zone/world/shared_memory with the regenerated item cache.
4. Install only in the authorized test environment with access closed. Keep
   original databases, binaries, cache and quest preimages. Match every running
   binary and the cache against the candidate manifest before enabling.
   No client assets are required. A quest-only reload cannot install native
   bindings, item cache changes or the persistence service.
5. Complete [QA.md](QA.md), keeping automated, deployed and owner-accepted states
   separate. Follow feature → dev → test only after required automated gates.
   Main promotion, production activation/restart and wiki publication require
   their separately authorized release.

Disable acquisition with `UPDATE nightcap_dungeon_state SET enabled=0 WHERE
id=1 AND revision=2026101601`. Existing managed runs and earned claims continue
under the matching binaries. Keep all catalogs, ledgers and advanced-loot
receipts. Do not drop tables/items or restore player data. An older binary is
not a safe rollback while managed allocations or unclaimed rewards remain.
On production, never kill an individual zone: the supervisor restarts the
whole runtime. Use the authorized operational release procedure.

## Evidence and acceptance

`rehearsal.json` records an isolated local migration and data-preservation check.
`inventory-verification.json` and `recovery-adapters-verification.json` execute
the actual receipt/inventory and corpse/currency code with dependency fakes.
`test_dungeon*.py` covers actual spawn selection, probability boundaries, item
catalog, parser rejection and integration ordering. These are not live gameplay
or balance evidence. Build/package evidence and manual QA must be recorded
before this candidate is represented as ready or deployed.

`activation-verification.json` verifies valid activation and refusal of altered
items, schema and triggers. `concurrency-verification.json` executes concurrent
real MariaDB sessions for allocation, the six-member cap, receipt rollback and
reset versus entry. These tests use synthetic records in the isolated database.
`wiki-review.md` records the whole-site assessment and the unreleased guide.
