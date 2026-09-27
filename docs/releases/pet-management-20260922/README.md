# Three-pet management: live QA

Built September 22 and activated September 27, 2026, after explicit owner
approval for main and live server/client deployment. Production server, signed
game release 2026092201 and launcher 0.3.1 are live. The owner client at E:/Nightcap
was updated and passed an actual startup check. Graphical and gameplay acceptance
remain open. [Production evidence and recovery](PRODUCTION.md).

Pet Info shows three class/name/health rows. The `Commands:` line states the
server-acknowledged scope. Click a name or target your pet in the world to select
one. Targeting an enemy preserves that selection. Click the selected name again,
click All pets, or clear the game target to return to shared commands. Pet death,
dismissal, class release and zoning cannot retain a stale selection.

Window buttons use the existing server pet-command handler, including native
ownership, combat, line-of-sight/range, fear/mez and AA restrictions. `/pet`
commands use the same server selection. Pet Armor remains a separate selection.
The native detail gauges and buffs follow the selected representative; the three
roster rows show the complete live roster. Advanced controls still need their AAs.

## Failure evidence and limits

The reported live no-op has not been reproduced on the player's exact session.
Read-only analysis of the pinned RoF2 executable confirms that both its native
window and slash parser rely on one cached pet/capability set. Packet sizes and
the server decoder agree. The new window bypasses that local restriction
and its guarded slash hook permits requests for a fresh server-confirmed roster;
the server continues to authorize each recipient. A disposable native ABI test
exercises the controls while the original availability predicate returns false.

Regression tests also reproduced missing selection, stale lifecycle selection,
old-token snapshot rollback, and a stale individual order broadening to survivors.
The fixes reject stale UI scope before command dispatch and clear the exact
selected spawn when it disappears. The isolated native engine passed nine cases / 132 actions / 105 commands.
Attack and Quick Attack reached all three pets in shared scope, only the selected
NEC pet in individual scope after enemy targeting, and no pets beyond command
range. Target clearing and dismissal restored the expected scope. Synthetic rows
were removed from all six fixture tables. These checks bypass the RoF2 wire
decoder and do not establish renderer or owner gameplay acceptance.

## Delivery and recovery

Ship the matching server overlay/binaries with proxy `0.6.0-dev` candidate,
generated patch catalog and `uifiles/nightcap/equi_petinfowindow.xml`. The normal
signed launcher inventory accepts this UI asset; stock eqgame.exe remains
unchanged. Original client files are read-only during generation. Candidate assets
are staged under `E:\EQ_Local_Dev\artifacts\pet-management-20260922\assets-final`.

Take a fresh server backup before activation and preserve previous binary and
client manifests. No database migration is required. Revert only this feature's
binary/client generation together; never downgrade below the existing class-pet
persistence implementation or restore old player data. Signed game rollback uses
a higher release counter, as documented in the permanent patcher runbook.

[Exact QA](QA.md) · [Architecture](../../adr/0046-selected-pet-commands.md)

## Verification

- Fresh isolated world/zone build, followed by recompilation of the two final
  reviewed pet files: passed. All 56 overlay files match the final source manifest.
- x86 client runtime/ABI, real server selection/lifecycle fixture, generated XML
  and asset tests: 13 passed. The quick select/order regression was rerun after
  final review and passed. Required failures stop the disposable host as expected.
- Exact pinned RoF2 executable and 43 patch sites: passed. The verifier also
  validates the native 18-entry command mapping used by existing hotbar buttons.
- Go package, preflight and manifest tests: passed. Frontend and Wails QA build:
  passed. Signed local QA release 2026092201 contains 23 verified client files.
- Independent review: resolved missing hotbar backing controls, custom drag
  fallthrough and stale roster/selection hazards; no remaining required findings.
- Native engine: [nine passing cases](native-summary.json), including direct
  OP_TargetMouse selection, Attack/QuickAttack and range rejection.
  [Fixture cleanup](native-cleanup.json) confirmed zero retained synthetic rows.

[Build identities and remaining gates](verification.json) pin the exact binaries.
Full build/source manifests, native inputs/outputs and signed package are retained
under `E:/EQ_Local_Dev/artifacts/pet-management-20260922/`.

Repeat from this worktree:

```powershell
$env:PYTHONPATH='tools;tools/tests'
python -m unittest eq-client-dll/tests/test_runtime.py tools/tests/test_pet_command_selection.py tools/tests/test_pet_management_ui.py tools/tests/test_client_gameplay_assets.py
python tools/generate-client-patch-catalog.py --check
./eq-client-dll/tests/verify-exact-client-patch-sites.ps1 -EqgamePath E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/eqgame.exe
python tools/balance/verify_pet_management.py --runtime /tmp/nightcap-balance-pet-management-20260922 --output E:/EQ_Local_Dev/artifacts/pet-management-20260922/native-repeat
```

The isolated QA executable is `E:/EQ_Local_Dev/artifacts/pet-management-20260922/qa/nightcap-launcher-qa.exe`.
Its copied game directory is the sibling `client` folder. The updater initially
refused installation while an existing game was running. After it closed, the
normal updater installed and verified all 23 files. An owned startup/stop smoke
test reached the running state with proxy `0.6.0-dev`; enabled, required and
applied patch masks all equaled 8191. No authentication or gameplay was automated.
The original binary client remains unchanged. This startup check does not replace
the owner's graphical and gameplay checks in QA.md.
