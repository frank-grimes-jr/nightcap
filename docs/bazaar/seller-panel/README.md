# Bazaar seller panel — live QA — October26

Main PR345/e43f2d4b and the paired runtime/client/wiki release are verified.
All12workers,51schema/565content checks and102saved-state tables pass; access is open.
Signed client2026102601 and wiki20261026-bazaar-grip-v1 are published.
Native player acceptance remains open. See deployed.json and evidence.json.

Adds Search and Sell / My Listings tabs to the native Bazaar window. Posting uses
an exact server quote and Confirm Post; owned listings have paged selection and
Confirm Cancel; Collect Proceeds shows the authoritative balance. Disabled trading
still permits cancellation/collection. Existing escrow, ownership and pricing rules
remain. No schema, quest, item stats or client executable changes.

Source baseline main465003f6; feature/bazaar-seller-panel. Public client baseline
2026102402 / proxy0.12.0 was freshly read and signature-verified; older source notes
calling game2026102301 current describe the retained proxy only. Candidate0.13.0
changes DLL/catalog/config and adds uifiles/nightcap/equi_bazaarsearchwnd.xml.
All137other asset descriptors, patch notes and tombstones are retained (141total).
Assets live under docs/bazaar/private/seller-panel/client-v2; signed2026102601 is published and all141HTTPSassets/signature/pairing verify.
The protected reference and installed player clients were not modified.

[Generated layout preview](layout-preview.png) (illustrative; not an in-game capture).

[Design](SPEC.md), [exact in-game QA](QA.md), [evidence](evidence.json).
Native fixtures and source checks are not a rendered-game acceptance record.
The October26 owner instruction explicitly authorizes this combined main/server/client QA release; see deployment/AUTHORIZATION.md. Native acceptance remains open.

## Build and validation

- `tools/build_bazaar_panel_candidate.py` authenticates the retained deployed84b6b9ff
  source/binary and overlays only two common headers and client.h/client_bazaar.cpp.
  It builds an isolated complete zone; it never installs it. `--resume` is only
  allowed after the prior build has ended. Do not modify its source while running.
- `eq-client-dll/build.bat` and `tests/build-runtime-tests.bat`; then
  `python eq-client-dll/tests/test_runtime.py --eqgame <read-only pinned exe>`.
  Exact-client115guards, generated catalog check and launcher tests are required.
- Real database tests use a disposable tmpfs instance with
  `NIGHTCAP_TEST_DEPS=E:/EQ_Local_Dev/artifacts/bazaar-test-deps`.
- `prepare_client.py` creates an exclusive local candidate from the pinned current
  public inventory. Validate with TestBazaarPanelCandidate using
  NIGHTCAP_BAZAAR_CANDIDATE=<client-v2> and NIGHTCAP_TEST_EQGAME=<pinned exe>.
  The actual DLL is required: compilation/signature alone cannot prove pairing.

## Promotion and recovery

Promote through dev/test with explicit GUI QA. The owner authorized main, signed client publication and
production activation for this combined Bazaar/Paladin grip QA release. Recheck
current public inventory and runtime baseline before packaging a signed successor;
never overwrite newer unrelated changes. No new desktop launcher build is needed.
A zone binary deployment requires a graceful full game-runtime restart under the
production supervisor, with the current backup/preservation/receipt controls.
Never kill a single production zone. Deploy the integrated world/zone/shared_memory set; existing cache/schema stay paired.

Rollback the panel using a compatible complete client pair at a higher signed
counter. Retain grip-aware native code after weapon metadata exists; never roll back blindly to old binaries. Keep all five escrow tables, receipts,
owned items and earned balances. Never restore old player data to undo a UI release.
A rule or quest reload cannot install this C++/client change.
