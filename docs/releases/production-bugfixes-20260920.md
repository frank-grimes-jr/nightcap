# Production NPC and multiclass spell fixes — September 20, 2026

Status: built, tested, independently reviewed and signed; deployment awaiting
explicit host/payload approval. No upload or production switch by this task.
The owner explicitly authorized main source promotion with "Push to main when
you're done" on September 20. Existing automated verification and independent
review pass; manual gameplay acceptance and production deployment remain open.
Branch: `feature/production-bugfixes-20260920`, isolated from the original working
tree. User intent: repair Tunnel Trader errors, missing NPC auctions, secondary
class merchant usability and purchased spells reporting level 255.

## Evidence and scope

- Initial production image `production-candidate-20260920` lacked native
  `LivingEconomy` and `MarketAnnouncement` support required by its quests. The
  separate coordinated deployment installed release 2026092004 during this task;
  a fresh read-only check confirmed the two bindings and healthy services.
- Release 2026092004 still lacks `quest::ooc`. Trift's timer calls that absent
  Perl API. The new adapter sends a real zone OOC packet with the NPC sender,
  including when no client initiated the event, with safe literal text formatting.
- Monktest's confirmed class tuple is CLR/MAG/NEC. Merchant class-mask and
  spell-level checks use the primary class; scribing also checks an item mask
  before its spell-level gate. The new required client feature covers these
  separate paths. [Catalog design](../adr/0042-per-character-spell-access.md).
- Canonical server checks ignore legacy global widening. Class selection stops
  modifying shared spell definitions; current memorized casts recheck the held
  classes and level. The cast handler checks the slot before indexing gems.
- Startup refuses a world/zone pair missing required economy, OOC or spell-access
  contracts, preventing another new-quest/old-binary deployment.

No changes to prices, finite offer quantities, class selection costs, era policy,
inventory, currency or saved spellbooks. Restarting world rotates finite market
stock by its existing design. Unheld spells already memorized are retained but
rejected when cast; ordinary item and AA casts keep their separate authorization.

The exact purchased spell name was requested. An inventory/log read was blocked
by automatic approval review; it has not been retried or bypassed. Regressions
use original Summon Waterstone (spell 4, MAG 17), all canonical class rows and
Monktest's selected-class tuple rather than private inventory data.

## Verification

Local artifacts: `E:/EQ_Local_Dev/artifacts/production-bugfixes-20260920/`.

- Failing-before/passing-after native test: globally widened Summon Waterstone
  still requires held MAG 17; class release and class ordering are covered.
- Actual native cast branch: invalid slots never index the gem array; released
  classes and insufficient levels cannot cast an already memorized spell.
- Actual OOC adapter: ownerless/no-client cases, NPC timer delivery to multiple
  clients, channel/sender and literal percent signs.
- Exact pinned executable verification for all 41 guarded sites; proxy builds.
- Disposable x86 hook tests: level/accessor/scribe calling conventions, both
  merchant flags, stale identity, non-scroll behavior, native rejections and
  nested/exception-safe scribe scope restoration.
- Asset tests preserve other spell fields, reject drift and accept only the
  reviewed generated recall afterimage. Staged output restores 11,057 rows.
- Repository suite: 66 passed, one opt-in pet database test skipped; its bag-price
  fixture hit sandbox Docker denial. The focused rerun passed all three bag tests
  in an isolated schema (69 passing tests in total).
- Five disposable x86 client runtime tests passed after the final hook changes.
- Go production-tag suite passed all 13 packages with tests; frontend TypeScript,
  Vite and Wails launcher 0.2.2 builds passed. Dependency audit: zero advisories.
- Five production supervisor tests passed on Linux. A clean Linux native build
  produced loginserver, world, zone, UCS and shared_memory with the existing
  production security patch. Crypto self-test and binary compatibility pass.
- Independent review found no remaining actionable source issues. Seven mocked
  activation scenarios passed, including partial plugin/image writes and failed
  startup, preservation and gateway gates. Image-contained hashes are checked
  before production stops. Five publication interruption scenarios also passed;
  already-visible new channel metadata is never downgraded. Manual gameplay is
  not claimed by these checks.

## Rollout and rollback

Staged signed client release: 2026092005; launcher 0.2.2; proxy 0.5.0-dev.
The package has 22 files, uses the existing production signing authority and
expires October 20, 2026. Private signing material remains local.

| Artifact | SHA-256 |
|---|---|
| Server archive | `1c3d55b9ad37ad2bce5eab993e237355fb3e550db1da88e7e2d5bc103e2a7e89` |
| Public archive | `08741cbe60df11ca11c04a840681445d0e3fb6ada5cf93be5f78834010bf084d` |
| Launcher ZIP | `1e665b6d644b20f88c627ea57a9e388e2ca9d67675cd6c3ed45fbd987b5dd2c8` |
| Signed channel | `fdbf8486da06342593eca7efebb78916e50c0923a26a7993009d5a715e17f5cc` |
| world | `f17fc319bdba5636b352e585c1899b13847580866bf613340ff9766bb757e71f` |
| zone | `7e755806435f249ff378c19b8b8ae28dcef9104ab50ac9552cad3f34dd4a310a` |

Automatic approval review rejected SCP to the existing OVH production host
`135.148.47.202`: the request did not explicitly authorize exporting these
binaries, plugin/source artifacts and release script to that host. Explicit
approval for upload, short restart, deployment and client publication is pending.
No retry, indirect upload or production change followed that rejection.

1. Complete full native build, independent review, launcher tests and signing.
   Preserve the source and binary hashes, security hardening and package hashes.
2. Retain production image 2026092004, its supervisor, multiclass plugin and
   public channel/launcher. Stage all new files and verify hashes before downtime.
3. Stop gateway/game gracefully, create/validate a full on-host database backup,
   then switch only the paired runtime, supervisor and multiclass plugin. Preserve
   hosted account/configuration files and player data; do not reapply SQL content.
4. Start and verify startup gate, actual process binary hashes, world/zone health,
   required rules and economy state. Publish immutable signed client files first,
   launcher ZIP second and channel metadata last. Verify signed hosted hashes.
5. Players must install the new client release and restart EQ. No direct edits to
   `Client_RoF2_Dev` are part of this task. Retain the Lavastorm readiness gate.

On server failure, restore the retained image, supervisor and plugin together.
Do not overwrite subsequent player progress with a whole database restore. For
client rollback publish retained contents under a higher signed release number;
do not lower or replace an already published immutable release. The owner's
explicit main-promotion authorization applies to source; automated checks are
not manual acceptance or approval of the blocked production upload.

## Exact owner in-game QA

Use Monktest, CLR/MAG/NEC level 50, on the supported updated RoF2 client.

1. Log in directly to East Commonlands. Without first opening Inventory or AA,
   open **Magician: Spells** (NPC 997912) with **Show only items I can use** enabled. Confirm
   native MAG spells appear with normal required levels. Repeat **Necromancer: Spells** (997910) and **Cleric: Spells** (997901).
   Repeat immediately after zoning and after camping to a different character.
2. Buy a native MAG scroll such as Summon Waterstone (spell 4, required level 17),
   or repeat with the exact originally reported scroll. Its required level must
   not be 255. Try right-click scribing and cursor-to-spellbook scribing on separate
   unlearned scrolls; memorize and cast. Confirm inventory/currency move once.
3. At an unrelated class vendor, check that exclusive spells do not become usable.
   On a lower-level character confirm held-class spells retain their real level
   restriction. Shared spells use the lowest requirement among held classes.
4. On a disposable test character, memorize a spell exclusive to an extra class,
   then release that class. Reopen the shop: the spell is unusable, and the old gem
   cannot cast. Reacquiring the legal class restores eligibility. Do not remove
   earned classes on an established character just for this negative test.
5. Hail each EC Tunnel Trader (NPCs 999500–999509). Verify a real finite WTS/WTB
   offer, successful/declined transactions and no quest errors. Enable auction
   chat and wait for several 75–120 second pulses; WTS and WTB include item links,
   actual prices and NPC names. Sold/exhausted offers must not advertise.
6. Hail Trift (999524), then wait 3–5 minutes. His corpse story appears in OOC
   under his name without a Perl error. Other resident hails/ring travel still work.
7. Confirm normal non-scroll equipment, race/deity restrictions, item clickies,
   Ancient Attunement, class skills and pets retain their prior behavior.

Record observed results and any immediate-login refresh race before gameplay
acceptance; the owner authorized source promotion ahead of that acceptance.
