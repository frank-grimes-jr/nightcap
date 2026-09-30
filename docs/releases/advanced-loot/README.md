# Advanced loot implementation

Date: 2026-09-30. Branch: `feature/advanced-loot`, based on `origin/main`
`20608bb`. **In progress; not usable as a released feature and not deployed.**
The original RoF2 installation remains read-only. No live database migration,
gameplay binary replacement, signed publication or main promotion occurred.

Scope and acceptance requirements: [ADR 0048](../../adr/0048-advanced-loot-client-server-contract.md).

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
  The catalog has 58 sites, each at most 64 bytes. Runtime verification rebases
  the command/constructor SEH immediates and every native vtable pointer.
- Build command, source hashes and artifact hashes are in
  [client-build.json](client-build.json). This records a client build only.
- Shared protocol and decision-policy fixtures passed in the earlier foundation
  iteration. Subsequent UI integration has been compiled; these fixtures have
  not been rerun against all current changes. Native skin reload, zoning,
  message transport and action behavior have not been exercised in eqgame.
- Per-character preference source and candidate SQL are written. They are not
  yet wired into the zone build/command handler or applied to a database.

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

## Outstanding implementation

1. Register physical NPC drops after kill-credit/raid permissions are settled;
   retain immutable item identity through corpse removal and entity-ID reuse.
2. Wire `#advloot`, preferences, snapshots and lifecycle publication into the
   authoritative zone. Handle disabled clients and unavailable preference storage.
3. Connect personal take/leave/all and automation to a checked native transfer
   path. Preserve complete metadata, lore/augment checks, dynamic-zone rules,
   quest veto, task updates, range, corpse locks and NO TRADE consent.
4. Connect master assignment, timed Need/Greed/Pass and free grab. Shared
   automation must select exactly one recipient and retain current loot rights.
5. Handle coin splitting and saved corpse state. Native `PutLootInInventory`
   currently ignores save results; automated transfer must not treat an uncertain
   save as a confirmed award or retry it. Saved corpse loot must not restore an
   already awarded physical drop.
6. Build the paired world/zone, review integration, prepare signed QA-copy assets
   and run the requested verification/owner acceptance process. No release claim
   follows from a successful proxy build alone.

## Manual acceptance plan (not executed)

Use a separate QA client and isolated database/server candidate. Final candidate
documentation must pin exact NPC IDs, items and fixtures before promotion to test.

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

Rollback retains preference and any transfer-audit data, restores the paired
previous binaries/assets, and disables the feature. Never drop player data as
part of rollback. Normal feature → dev → test → main gates remain in force.
