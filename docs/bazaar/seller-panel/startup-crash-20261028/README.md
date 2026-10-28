# Bazaar startup crash — October 28, 2026

## Observed failure and root cause

The owner reported a crash after the Bazaar/1HS/SoulFire update. The local
12:57:25 EDT dump records access violation c0000005 while initializing game UI,
before world entry completes. Runtime eqgame base is 0x600000; fault 0xa8dc6d is
preferred VA 0x88dc6d. EAX is zero and the invalid read is 0x30. Raw dumps/logs
remain private at E:/EQ_Local_Dev/artifacts/client-crash-20261028/.

Installed proxy0.13.1 and catalog hashes match signed2026102801. Installed
Bazaar XML matches 41fefb05f3c523ee70221329a23824834e376cf5afc2c2949deb2c33455b557e.
The earlier ASCII parser repair lets the skin reach native window creation,
exposing a second defect: NCBZ_Tabs has neither native border-template reference.

Read-only disassembly of pinned eqgame.exe establishes:

- CTabWnd constructor at 0x88dd90 copies template+0xa8 into window+0x1d8
  (0x88de6f/0x88de75), and template+0xac into window+0x1dc.
- Page insertion at 0x88db60 loads EAX from window+0x1d8 at 0x88dc63,
  then unconditionally reads [EAX+0x30] at the exact crash instruction 0x88dc6d.
- The stock SIDL TabBox defines TabBorderTemplate and PageBorderTemplate as
  FrameTemplate references with no defaults. Stock AA and Options TabBoxes
  supply FT_DefTabBorder and FT_DefPageBorder; both exist in EQUI_Templates.xml.

This identifies the observed missing-template fault. It does not prove that all
other native UI or SoulFire behavior has passed player acceptance.

## Repair and verification

tools/client_bazaar_ui.py supplies both stock references. The generated XML in
this directory changes exactly those two semantic elements; removing them makes
the normalized tree equal to the installed failing XML. candidate.json pins the
old and new hashes and sizes. No DLL, catalog, config, SQL or server change.

Two independently written regressions failed before the repair with four missing
template subtest failures. After the fix, all seven Bazaar tests, six gameplay
asset tests and five gameplay UI tests pass, without skips. The real stock skin
is provided through NIGHTCAP_BAZAAR_XML. Independent source/native review found
no actionable issue. Native login, rendering and interaction remain open.

## Delivery, rollback and exact owner QA

The owner explicitly approved publication in this chat. Signed client2026102802
is published, changing only the Bazaar XML and preserving all140 other signed
descriptors/URLs, the runtime pair, history and tombstones. Twenty Linux publisher
fault/preservation tests and three Go suites pass. published.json records all five
services unchanged across publication, including their IDs, start times and
restart counts. No installed client files, server binaries or player data were
modified. Native owner acceptance remains pending. For any future delivery,
re-read the public channel first to preserve concurrent releases.

The launcher hashes every managed asset before launch. An unsigned local XML
replacement is not a durable repair and must not bypass its integrity checks.
The owner's explicit "Publish the launcher hotfix" approval applies to this release;
it does not grant standing future release authority.

After authorized publication, fully exit EQ and use launcher Play. Log Palwar
into East Commonlands: world entry must complete without the crash dialog.
Open /bazaar, switch Search and Sell / My Listings, resize, close/reopen and
reload the Nightcap skin. Check fresh dbg/UIErrors for native exceptions,
ParseTag failures or fallback. Test a posting quote/confirmation, cancellation
and proceeds collection separately; do not count these as accepted yet.
Confirm the paired SoulFire grip behavior remains independently testable.

Recovery must use a higher-counter complete signed generation. Restoring the
old XML restores this known crash, so it is not a healthy fallback. If this
candidate has another issue, prepare and verify a stock-Bazaar XML fallback
with the seller panel unavailable; do not lower launcher checkpoints or restore
player data. No server restart is required for either UI-only change.

## Wiki impact

All article sources were reviewed; wiki-review.json lists each assessment.
Launcher and Recent changes describe the published2802 hotfix with native
acceptance still open.
Home, Features, commands, items, zones, catalog values and unrelated release
labels retain their scope. Global source drift remains review work, not a reason
to advance unrelated historical pins. Public wiki publication remains pending.
