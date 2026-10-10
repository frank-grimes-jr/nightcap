# Advanced loot stock icons — October 10, 2026

Merged to main and published for owner live QA; in-game acceptance is pending.

Each Drops and Filters row shows the stock image identified by the existing
server `Row.icon` field. The native item icon cache supplies the artwork; no
download, database change, or protocol change is needed. Clicking the image
selects the same item as its name. The 20-by-20 image occupies a separate
22-by-22 button, retaining the eight-row layout and inline loot rules.

Missing or out-of-range images are hidden while the item remains selectable.
Every redraw clears unused slots. Detail/settings panels hide the row images.
The cache owns the returned animations; this feature neither mutates nor frees
them. XML owns the decal geometry and native buttons own their usual lifetime.

## Exact-client evidence

RoF2 MQ2Main.dll exports resolve GetAnimationCache to RVA `0x265430` and
IconCache::GetIcon to `0x265a60`. Disassembly of the pinned
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`
eqgame.exe confirms item cache type 0, minimum/maximum at `0x18`/`0x1c`,
and the cache-owned animation result. Native button setup at RVA `0x21baee`
assigns the same result to decal slots `0x240`, `0x248`, `0x244`, `0x250`.
The six contiguous decal states end at `0x254`. Runtime guards validate the
cache entry, relocated GetIcon SEH entry and native assignment bytes before
binding. Existing global exact-client checks still apply.
The three signatures also appear in the canonical signed patch-site catalog,
the generated runtime header and the launcher's embedded preflight catalog.
All 74 catalog sites pass the exact-client verifier; generator `--check` passes.

## Verification and delivery

Five x86 production-header fixtures pass with `/W4 /WX`, including native cache
bounds, all six decal states, missing cache, stale-image clearing, selection by
icon and visibility in list/filter/detail panels. Six Python XML checks pass,
including viewport, non-overlap and decal scaling. The x86 DLL build passes.
The four shared client UI tests, ten native UI/model regression executables and
launcher preflight, manifest and assets packages pass. The asset package requires
loopback HTTP and temporary junction permissions; the sandboxed run was blocked,
and the permitted rerun passed with the repository's Go 1.27.2 toolchain.

Deliver the DLL together with a newly generated
`uifiles/nightcap/equi_petinfowindow.xml` through the signed launcher workflow.
An old XML lacks the eight required Icon controls. Roll back both together.
Do not modify `Client_RoF2_Dev` or an active game installation.

## Required in-game QA

1. In East Commonlands, kill a loot-bearing skeleton and open `/advloot`.
   Compare each icon with the same item's native inventory/inspection icon.
   Confirm names, quantities, Always Loot and Never Loot remain readable.
2. Click the image and loot the selected item. Confirm the correct item transfers
   and the last awarded item still closes the queue.
3. Open Filters and compare saved item images. Search, page forward/back and
   switch to Settings/Item rule/More: no previous row image may remain visible.
4. Exercise a missing icon fixture: the name stays usable, with no unrelated
   icon. Test a NO TRADE item: clicking its image must not bypass confirmation.
5. Reload the Nightcap skin, zone and relog; verify images repopulate and ordinary
   inventory, spell and item-display icons remain correct. Use a 640x480 viewport
   to confirm row images do not overlap labels or inline rules.

Native rendering and owner in-game acceptance are still pending.

## Production publication — October 10, 2026

The owner explicitly requested “Push to main and server.” PR #151 promoted
`test` to `main` at `01453d593aec9862154515bad8a9b9431ff094d6`.
The published production client release is `2026101001`, proxy `0.8.0-dev`.
Its signed manifest contains 104 files (211,913,439 bytes); exactly three assets
change from release `2026100901`: `dinput8.dll`, `nightcap-patch-sites.json`, and
`uifiles/nightcap/equi_petinfowindow.xml`. The remaining 101 assets match.

DLL SHA-256: `56b8e21c3d5226cdd1af05cc61673a318d5cf1bc3cd76b2489b37d333a1f9b23`.
Channel SHA-256: `4432fa74642d2ae9856a22e80fd1a0d257cd19325b2a4d4ae741bcacf11ef9ed`.
The manifest expires November 9, 2026 at 20:59:17 UTC. Independent verification
uses the public production key already shipped in launcher 0.4.0. Twelve
publication/recovery tests pass, including drift refusal and channel-last atomic
publication. The publisher preserves the previous signed channel for rollback.
Local evidence is under `artifacts/advanced-loot-stock-icons-20261010/deployment/`.

Native rendering and the in-game checklist above remain pending owner acceptance.
Restart EQ and use launcher Play to obtain the matching DLL, catalog and XML.

Production publication verified all 104 files on the server. All five service
identities, images, restart counts and health states remained unchanged; desktop
channel, starter bundle and guide hashes also remained unchanged.
