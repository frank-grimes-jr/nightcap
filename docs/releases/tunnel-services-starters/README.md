# Tunnel services and starting provisions

Deployed to OVH on September 21, 2026 after the owner explicitly approved main
promotion and live deployment. **Online for in-game QA; not manually accepted.**
This approval applies to this release and does not change the normal branch
policy. The latest main inventory refresh is included. See the
[activation record](ACTIVATION.md) for running hashes, preservation checks,
external connection checks and rollback instructions.

## Delivered behavior

- Tessa sells 50 basics: food, water, bandages, all four instrument families and
  every one of the 46 positive component IDs used by the approved 1,229-spell
  Classic level-50 hub pool, including reusable foci and all pet reagents.
  Original class access comes from `docs/pok/hub-stock-audit.json`, never the
  globally widened spell class columns. Later-era access is not added here.
- 21 tradeskill suppliers cover all 12 disciplines and 2,149 listings, using
  existing era-eligible, ungated PoK vendor stock. Each NPC has at most 150 items.
  Portable containers, research lexicons/tomes, fishing poles and bait are included.
  Six fixed stations provide forge, kiln, pottery wheel, oven, barrel and loom.
  Looted/foraged crafting components still come from their normal sources.
- Sixteen class trainers join the class merchants in four irregular conversational
  groups. Existing utilities, traders and residents are regrouped. Eight additional
  residents patrol short routes with pauses. Total custom population: 90 NPCs.
- Six residents have six personal lines each; walkers draw from sixteen ambient
  lines. One coordinator sends OOC every 45-80 seconds and auction every 30-55
  seconds, only with players present. Consecutive speakers and each voice's last
  line are avoided. Channels use first names only; overhead identity is retained.
- Ten sellers and six buyers each have two distinct finite offers: 20 sales and
  12 buys per world-start rotation, plus the existing ten merchant finds. Auctions
  show actual available linked items/prices, varied phrasing, item order and `//`,
  `--` or commas. Existing price policy, sold-out checks and native atomic trade
  remain. Per-item caps are three sale copies and two buy offers per rotation.
- New characters receive exactly 100pp, one class weapon and one no-trade 10 AC
  robe with +5 to the primary class's main stat. Existing characters are unchanged.
  No proc, heroic stats, regeneration, level requirement or repeatable login grant.
  Only audited rusty weapons are replaced; an unexpected chest/weapon fails
  creation instead of overwriting future race/deity rewards.

Plains Pebble (12832), needed for Imbue Plains Pebble, had no existing vendor
stock and zero price. This candidate explicitly sets its base price to 100 copper;
SellRate=10 and normal CHA/faction/merchant rules determine the displayed quote.
The original price is restored by rollback. Every general supply has a positive
reviewed effective base price. This exception is covered by regression tests.

The 100pp request permits new-character currency farming; no unrequested account
restriction was added. Starter weapons improve on rusty weapons but keep damage /
delay below 0.25. Bard/Rogue get DEX, priests/Beastlord WIS, INT casters and Shadow
Knight INT, remaining martial classes STR. Further combat tuning needs measured
in-game evidence; these items do not replace the existing AA/gear balance gates.

## Reviewable artifacts and evidence

- [Layout, exact inventory IDs and starter items](layout.json)
- [Reviewed source catalog](catalog.json)
- [Original candidate verification record](verification.json)
- [Live activation evidence](ACTIVATION.json)
- [Decision record](../../adr/0044-tunnel-services-and-creation-provisions.md)
- [Exact in-game checklist](QA.md)

Local evidence is under `E:/EQ_Local_Dev/artifacts/tunnel-services-starters/`:
`source-v3.json`, `candidate-v3/`, `tests-final/` and the integrated native build
manifest/log. The first capture read the stopped local PEQ volume through a
network-isolated MariaDB process; it wrote no PEQ content. It was handed back to
the separate Docker recovery task. Initial mutation rehearsals used a separate empty
disposable database container with no shared volume or ports. Production activation
then restored the full stopped OVH backup into another disposable container and
rehearsed the exact target forward migration, three rotations and rollback.

Source-v3 extends the source-v2 item scope using the exact Plains Pebble row already
captured there. These are local rehearsal preimages, **not production migration
inputs**. `catalog.json` preserves the source-v2 capture digest. Generation is
repeatable; new output directories prevent evidence from being overwritten.

Passed checks: 26 focused Python tests (including compiled native creation,
formatter, two-offer selection and unchanged atomic trade failure matrices), 36
Perl assertions, 29 content database checks, 97 market database checks across 30
rotations, five Linux supervisor tests and seven inventory-refresh regressions.
All 227 geometry samples and 24 path segments passed the native map raycaster.
Fresh isolated world/zone compilation, recorded incremental updates with fresh
source mtimes, production hardening and source-stability fingerprints passed.
The actual ELF pair passed the production starter/chatter startup contracts.

Independent review caught and resolved missing wallet persistence, the zero-price
reagent, creation packet replay, unexpected starting slot replacement, repeated
cluster headings, finite-offer pool exhaustion and baseline-generator overwrite.
Remaining limit: upstream SaveCharacterCreate still uses best-effort internal
profile writes; this change does not claim a transaction across every creation
repository. SQL and native fixtures prove selected failure paths, not a real RoF2
client session or graphical station/trainer/robe behavior.

## Activation procedure (completed on OVH September 21)

1. Select the exact reviewed source/binary/plugin/supervisor manifest. Retain the
   previous full paired runtime. Preserve current hosted account/configuration
   files and the existing production hardening. This is a server/content update;
   no new client files are required beyond the already-deployed PoK object assets.
2. Keep gateway access closed; gracefully stop the target world and all zones.
   Take and validate a full database backup. Export preservation fingerprints for
   character data, inventory, wallets, AAs, multiclass state, spells and market
   audit. Capture all 148 baseline starting-item rules (or stop on differences).
3. On the target host, run the read-only capture with that MariaDB container:
   `python tools/tunnel_services_capture.py --container TARGET_DB --root-env --output SOURCE.json`.
   Existing container root credentials are resolved internally, never emitted.
   `--root-env` requires the container's existing root-password environment;
   the default path is the local eqemu/peq database. Capture only while stopped,
   since the SELECT/SHOW calls are not one multi-table snapshot.
4. Generate into a fresh directory:
   `python tools/tunnel_services.py --source SOURCE.json --output TARGET_CANDIDATE`.
   Compare the generated stock, starter definitions, positions and counts with
   the reviewed layout. Stop on unexpected differences, collisions or topology.
   Rehearse this exact target preimage in a disposable schema before applying.
5. Apply `server-mods/sql/2026-09-21-multi-offer-market.sql` to the existing market
   database, then the newly generated `forward.sql`. Never replay the historical
   initial market schema or seed. The content patch checks complete scoped rows,
   counts, engines and triggers before its transaction writes. No character
   tables are changed by content SQL. Only affected EC instance-zero, non-corpse,
   non-zone cached states are removed; unrelated/corpse/instance states survive.
6. Verify composite offer and audit keys, `SHOW CREATE PROCEDURE
   nightcap_market_rotate`, 90 custom NPC placements, 16 trainer classes 20-35,
   2,199 merchant listings, six objects, eight grids / 32 waypoints and 32 starter
   item definitions. Procedure replacement is DDL and is not transactional: if
   CREATE fails after DROP, rerun the resumable upgrade before starting world.
7. Install the matching world/zone, supervisor, all new quest adapters and the
   `living_economy`, `tunnel_residents`, `tunnel_chatter` plugins together. Preserve
   other plugins and Khalure travel/readiness rules. Regenerate shared memory
   after item changes and before starting world/zones. A quest reload alone is
   insufficient. The new supervisor rejects an old world or missing TunnelChatter.
8. Start once behind the closed gateway. Confirm real running binary hashes,
   startup contracts, 20 sale/12 buy/10 find offers, quantity one, expected rules,
   character preservation fingerprints, intact audit and zero relevant native,
   DB or missing-quest-API errors. Check Plains Pebble base price=100 and no
   duplicate spawns. World startup legitimately advances the market epoch.
9. Open the test environment, execute [QA.md](QA.md), record owner results and
   retain unresolved gates. Production/main promotion follows explicit sign-off.

## Scoped rollback

Stop gateway/world/zones and capture current preservation fingerprints. Restore
only this release using its exact generated `rollback.sql`, which checks current
scoped afterimages before writes. Normal saved-state writes can cause that guard
to reject: compare the new rows, back up and invalidate only affected non-corpse
EC instance-zero states, then regenerate/rehearse the reviewed rollback. Never
remove guards or restore a whole old database over subsequent player progress.

The content rollback restores prior NPC locations and Plains Pebble price,
removes only new services/grids/objects/actors, and **retains all 32 starter item
definitions**, character wallets/items and historical market audit. Already
created characters keep their provisions. Then apply
`2026-09-21-multi-offer-market-rollback.sql`; it restores the original one-offer
rotation procedure exactly while keeping the expanded primary keys, which the
old runtime supports. Verify the routine before restart. Restore the previous
world/zone, supervisor and changed plugins/quests as one set; remove only the
release's new quest/plugin files. Regenerate shared memory and start once.

Verify original actor/layout counts, one offer per old actor, preserved player
progress and audit before reopening access. Do not run the retired baseline
content generator or delete retained item definitions. Keep release backups and
manifests until the owner accepts the in-game checks.
