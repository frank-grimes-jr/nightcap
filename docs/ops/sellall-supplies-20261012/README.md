# Sell-all supply protection — October 12, 2026

The owner explicitly authorized main promotion and production deployment.
[PR #183](https://github.com/frank-grimes-jr/nightcap/pull/183) is merged and the release is live on OVH.
All 12 zone hashes match, access is open and follow-up health checks pass.
Manual client acceptance remains pending.
`#sellall` preserves food, drink, every loaded spell reagent (including
Bone Chips), and casting focus items, in general slots and bag contents. This
applies to all classes and eras and overrides fixed resale eligibility. The
existing ordinary and former-NO-DROP resale prices and inventory bounds remain.
Spell reloads take effect immediately; missing spell data blocks sales safely.

The command remains a voluntary bulk sale. Preserving supplies does not grant
items, power, currency, or change manual merchant sales. Food/drink remains
optional following the separately deployed removal of hunger/thirst requirements.

## Verification and release

`python tools/tests/test_sell_all.py` compiles the actual command and real shared
resale policy with inventory/spell fixtures. Tests exercise general and bag
slots, full stacks, fixed prices, charged items, exclusion boundaries, spell
reloads and absent spell data. Production build/deployment evidence will be
recorded here after verification; this candidate does not claim activation.

The server candidate is built against the fingerprinted retained item-upgrade
release, changing only `zone/command.cpp` and `zone/gm_commands/sell_all.cpp`.
Only the two affected command-library unity objects are rebuilt; all retained
objects, archives and source files are fingerprinted before and after linking.
Existing runtime libraries, world, shared-memory loader, quests, rules, item
upgrades and player data are retained. Deployment uses an immutable image over
the current live image, a verified database backup, graceful full-game restart,
closed-gateway data checks, and all running zone executable hashes.

## Exact owner in-game QA

1. In East Commonlands, use a normal player with a bag, purchased food and drink,
   Bone Chips (13073), and ordinary saleable loot. Put some supplies in main
   inventory slots and some inside a bag. Record quantities and wallet.
2. Run `#sellall`. Food, drink, Bone Chips and the bag must remain with identical
   quantities. Ordinary loot sells; wallet increases by its expected resale.
3. Include a casting reagent such as a peridot and a non-consumed casting focus
   such as a Fire Beetle Eye. Both remain regardless of held classes.
4. Include a former-NO-DROP item with fixed resale. Ordinary loot of that kind
   still pays 1pp per physical unit; protected supplies never sell, even if they
   qualify for fixed pricing. Ordinary temporary and worthless items remain.
5. With only protected supplies left, run the command again. Inventory and wallet
   stay unchanged, and the message lists the supply exclusions.
6. At a merchant, use the newly published Sell All button. It invokes the same
   command and must preserve the same supplies. Relog and confirm persistence.

## Recovery

Before activation record the exact live image and zone hash. Rollback closes
the gateway, gracefully stops game, selects that image, starts game with its
health gate, verifies running binaries, then reopens access. Retain current SQL
and saved character/corpse state; never restore a stale database. Production
restarts the full runtime when a native child exits, so do not kill one zone.

Deployment verification and manual client acceptance are separate; QA remains
pending until the owner reports results.

## Verified deployment

Verified at `2026-10-12T19:56:39.250907+00:00`. Main merge: `890a9c0708dfdc4e967340c4b3b6bcc0889a8b9c`.
New immutable image: `sha256:4c0f464d64b6eb5dc787aaff380f4fbee41f2de8365e2622cb5fcc11cb940541`.
Zone SHA-256: `6a548967fb7af03b60144c4b40c61f383d003011ac3b313370a907d10b7d7537`.

The full backup passed gzip integrity and completion checks before downtime.
The graceful game stop passed; 47 player/state tables and
11 custom tables matched after restart while access was closed. All rules
and content checksums matched. Other native binaries, supervisor, quests,
client release and database/web/tunnel services passed preservation checks.
The gateway is open with zero new runtime restarts or detected native, quest
or database errors. No SQL restore ran and no client update is needed.

Remote release: `/opt/nightcap/releases/sellall-supplies-20261012/`.
Local complete build/deployment evidence: `E:/EQ_Local_Dev/artifacts/sellall-supplies-20261012/`.
Rollback image: `sha256:5e8a26cf1275758dc78ae4327f520389c98e01dcba3ffaed42e8f84ce7502022`;
rollback zone hash: `f44c318a551186cf9f8c5099d6649326910050a9640e19507cda1ef6392c8aeb`. Use the recovery procedure above
with those recorded identities and retain current player data.
