# Advanced loot implementation

Date: 2026-09-30. Branch: `feature/advanced-loot`, based on `origin/main`
`20608bb`, integrated with dev `ffac9ba`. **Implemented candidate; native gameplay
acceptance remains open. Not deployed live.**
The original RoF2 installation remains read-only. No live database migration,
gameplay binary replacement, signed publication or main promotion occurred.

Scope and acceptance requirements: [ADR 0049](../../adr/0049-advanced-loot-client-server-contract.md).

## Current evidence

- The x86 proxy builds with native screen allocation/destruction, an exact
  `/advloot` command hook, atomic server snapshots, row selection, paging,
  item-name search, item actions, filters, settings and NO TRADE confirmation.
  Commands go through the existing private UI transport. Inventory remains
  server-owned. The UI controller never manufactures loot packets.
- The generated Pet Info SIDL document also defines `NightcapAdvancedLootWnd`.
  Using an already included document avoids replacing the complete `EQUI.xml`.
  Existing pet controls are retained. XML generation is not proof of native
  rendering or usable layout.
- Proxy `0.7.0-dev` and the generated launcher catalog require `advanced_loot`.
  The integrated catalog has 63 sites, each at most 64 bytes. Runtime verification rebases
  the command/constructor SEH immediates and every native vtable pointer.
- Build command, source hashes and artifact hashes are in
  [client-build.json](client-build.json). The signed QA package installs in an
  independent copy and actual RoF2 startup reports all 15 required patches active.
  [Package evidence](qa-package.json) records the 46 files, hashes and clean shutdown.
- All three current focused C++ fixtures pass: snapshot protocol, personal/shared
  decision policy including saved roll checkpoints, and the x86 screen ABI/lifetime
  fixture (1,000 reload cycles). The screen fixture substitutes native dependencies;
  native skin reload, zoning and real message traffic remain untested in eqgame.
- The zone queue, command handler, per-character preferences, native corpse
  adapter, checked inventory placement, coin transfers and saved-state extension
  are wired into the candidate source. A clean paired world/zone build passed,
  followed by an incremental integration of the current enchanter command fix.
  Source fingerprints remained unchanged during compilation:
  [server-build.json](server-build.json).
  All 73 overlay files match the build; the complete source manifest is retained
  in [compressed form](server-source-manifest.json.gz).
  The build includes the final classic-loot/master review corrections. An initial
  incremental attempt skipped a file because its copied timestamp was older than
  its object. This was detected before installation; the verified file was
  recompiled, zone relinked, and its changed binary hash checked.
- `tools/tests/test_advanced_loot_inventory.py` compiles the actual production
  inventory translation unit with dependency fakes. Its checks cover complete
  metadata, stack merging/splitting, bag placement, full/stale slots, evolving
  records, and failures/exceptions at database boundaries. No inventory packet is
  published before acknowledged commit; uncertain outcomes quarantine the client.
  [Fault evidence](inventory-fault-rehearsal.json).
- `tools/tests/rehearse_advanced_loot.py` passes 16 checks against disposable
  MariaDB tables, including preference constraints, item/coin receipt atomicity,
  replay rejection and conservation of split coin. PEQ rows were not copied or
  changed. This is SQL storage evidence, not native gameplay acceptance.
  [SQL evidence](database-rehearsal.json).
- Production currency and saved-state bodies also pass with explicit dependency
  fakes: split/remainder conservation, offline/bot eligibility, stale/overflow
  wallets, each query failure, transaction exceptions, receipt replay, complete
  metadata roundtrips, stable legacy checkpoint IDs and malformed-state quarantine.
  [Adapter evidence](adapter-rehearsal.json). This does not execute a real zone.
- Five runtime Python tests and three Go package suites pass. Package assembly
  caught a missing `advanced_loot=1` in the shipped configuration; it is corrected
  and a regression test now validates the shipped file against the launcher catalog.
  UI regression fixtures cover auto-show for items beyond page one and preservation
  of NO TRADE confirmation across unrelated row updates.
- Independent integration review is complete for the candidate source. Corrections
  preserve classic cursor pickup, inventory/cursor fallback, native auto-equip and
  authorized GM recovery, and replace disconnected masters from the existing
  eligible roster. [Review record](REVIEW.md); production access helpers pass the
  [access fixture](access-rehearsal.json). Native acceptance remains open.
- The isolated login server, world and East Commonlands zone boot successfully
  with matching running binary hashes and no startup errors. The fresh content
  database has two fixture accounts and zero characters, inventory or saved states.
  [Service evidence](gameplay-qa.json). Empty quests mean production quest behavior
  is still outside this startup check. Client access remains gated by port 9000.

## Native ABI evidence

The supported executable is exactly 8,774,656 bytes, SHA-256
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`.
The client was read without modification. Primary layout references are the
[eqlib RoF2 branch](https://github.com/macroquest/eqlib/tree/emu-rof2), specifically
`include/eqlib/game/CXWnd.h`, `UI.h`, `EverQuest.h` and
`include/eqlib/offsets/eqgame.h`. The retrieved reference hashes are retained in
local `artifacts/advloot-20260930/reference/sources.json`.

| Native member | RVA / layout | Evidence used |
|---|---|---|
| `CEverQuest::InterpretCmd` | `0x11fce0` | Two stack arguments; SEH prologue |
| `CSidlScreenWnd` constructor 1 | `0x45f070` | Native disassembly: five arguments, `ret 14h` |
| `CreateChildrenFromSidl` | `0x45dcf0` | Exact executable bytes and primary header |
| Native allocator | `0x4dbb3b` | Exact entry signature |
| Screen vtable | `0x61982c`, 95 entries | Full table plus preceding RTTI locator |
| Screen allocation | `0x220` bytes | Native class layout |
| SIDL piece | `+0x1e0` | Missing template is detected before child use |
| Notification / frame / show / text | `0x88 / 0xc4 / 0xd8 / 0x124` | Native virtual layout and guarded entry bytes |
| Enabled / visible / text | `+0x1a / +0x196 / +0x1a8` | Native `CXWnd` layout |
| Edit limits / input | `+0x1e4 / +0x1e8 / +0x1ec` | Native `CEditBaseWnd` layout |

The custom object uses the game's allocator and deleting destructor. Its private
vtable preserves RTTI, forwards ordinary notifications, and clears cached window
and control pointers during destruction. Client field reads are presentation
only; none grant server permissions.

## Server behavior

- A client registers the protocol with its automatic refresh. A 500 ms zone pulse
  discovers NPC corpses after native death/quest processing has established rights.
  Corpse generations, physical UUIDs and session/revision checks distinguish repeated
  item IDs and reused entity IDs. Players still need native corpse rights and must
  be within 25 units to take an item; owned distant items can be inspected/found.
- Ask leaves a decision pending. Always Take/Need/Greed can collect personal loot;
  Need/Greed also preselect shared rolls. Never hides personal offers and excludes
  awards while filters apply. Shared offers remain visible to the master. Leave
  removes the offer while retaining the corpse item. Saved filters can be edited
  independently of a current corpse. Disabling the feature stops automation and
  effective filters; existing shared decisions remain protected.
- A shared master is selected from eligible raid/group leadership, falling back
  to native loot rights. The master assigns to an eligible target, opens free grab,
  or starts a 60-second roll. Need has priority over Greed. Rolls exclude characters
  without current rights or an active connection. Free grab is manual, preventing
  competing auto-loot clients from racing for it.
- A disconnected or ineligible master is replaced by a connected character who
  still has native rights and belongs to the original participant roster. Existing
  votes, the roll deadline and an already selected recipient are preserved.
- Automatic attempts that fail wait for an inventory change, filter edit or explicit
  refresh before retrying. Full bags do not spill items onto the cursor. NO TRADE
  items and their contents require an explicit confirmation; Loot All skips them.
- Coins commit with a physical purse receipt. Auto Split distributes each coin
  denomination among connected clients in the current group or raid in this zone;
  the looter receives remainders. Bots/mercenaries do not consume shares. Existing
  raid item-looter restrictions still govern initiating the pickup and item awards.
- Inventory and claims must be transactional, with the expected inventory layout
  and no transfer-table triggers. The adapter preserves complete available corpse
  metadata and rechecks lore/augments, quest vetoes, dynamic-zone access, source
  identity and character state. Classic NPC looting uses the same receipt-aware
  path and cannot take a different player's shared award.
- Classic manual pickup uses an empty cursor. Classic auto pickup retains native
  auto-equip selection, then inventory placement and an empty-cursor fallback.
  Advanced pickup places items in inventory. Worn-slot checks and equipment quest
  notifications share the classic implementation. Occupied cursor queues are never
  extended by the checked path, including when the native empty-cursor rule is off.
  GM recovery requires a native `GMAllowed` classic session and is rechecked after
  loot quest callbacks; it does not grant advanced-window ownership.
- Saved NPC/corpse records retain physical IDs and complete loot metadata; corpse
  records also retain rights and distribution decisions. Legacy records receive
  repeatable IDs. Receipts suppress awarded drops after a checkpoint replay.
  Malformed records are retained and locked for recovery instead of rerolled.

## Remaining release gates

1. Exercise native server command/session, saved-state and coin paths with fault
   cases. The production-body fixtures do not prove real packets, quests or lifecycle
   behavior. Inspect disconnected masters/winners and changed group/raid membership.
2. Validate actual native rendering, `/advloot`, skin reload, zoning and gameplay
   with the packaged QA client. Signed installation/startup alone does not establish
   those behaviors. The original client stays read-only.
3. Complete saved-state rollback/recovery review. An older server that ignores
   receipts is unsafe with a checkpoint containing already awarded items.

## Manual acceptance plan (not executed)

Use the separate QA client and an isolated database/server candidate.
[Exact native QA](QA.md) pins zone 22, NPC 22003 and items
13073/1068/1041 with commands, expected results and remaining operator fault gates.

- Solo: `/advloot`, close/reopen, multiple corpse rows, paging, search, inspect,
  loot/leave/all, Ask/Always loot/Never, auto-show off/on and disabled/classic mode.
- Persistence: change filters and settings, camp, reconnect and confirm the same
  character retains them while another character retains its own choices.
- Shared: two clients, master assignment to target, Need before Greed, 60-second
  roll, all-pass, free-grab race, disconnected winner and changed raid loot rights.
- Restrictions: move out of range; full bags; occupied cursor; lore item and lore
  augment; NO TRADE cancel/confirm; quest veto; locked and busy corpses.
- Lifecycle: kill then zone/die/disconnect; classic loot removes an advanced row;
  decay and entity-ID reuse; `/loadskin`; malformed/interrupted snapshot; rapid
  double click and stale click after another player wins.
- Persistence faults: no inventory save, uncertain commit and zone saved-state
  restart must neither duplicate nor silently discard the physical item.

Behavior rollback disables advanced loot while retaining a receipt-aware server
and all preference/claim data. A previous server binary requires a separately
reviewed reconciliation of NPC saved-state checkpoints before activation; a
binary swap alone can resurrect awarded loot. Do not delete receipts to unblock
an uncertain award. Normal feature → dev → test → main gates remain in force.

## Local QA package

Launcher: `E:/EQ_Local_Dev/artifacts/advloot-20260930/qa/nightcap-launcher-qa.exe`.
Client: `E:/EQ_Local_Dev/artifacts/advloot-20260930/qa/client/everquest_rof2`.
Release **2026093005**; the signed manifest expiry is recorded in
[package evidence](qa-package.json).
This is a locally signed offline package, not an Authenticode or public release.
The copied client targets `127.0.0.1:15998`. Isolated services are running, but the
client login listener deliberately uses an unpublished port until QA world access
is enabled. RoF2 requires world port 9000, which the live local container occupies.
An explicit temporary cutover is needed before the owner can enter this QA server;
do not change the client's login target to production to bypass the gate.
The [access and restoration handoff](QA-ACCESS.md) records the proposed switch,
preservation steps and approval boundary. It has not been executed.
Candidate world/zone and SQL are under the artifact root's `server` directory.
Private signing material is outside the package and must not be copied into it.
