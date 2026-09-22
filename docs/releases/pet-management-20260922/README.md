# Three-pet management candidate

September 22, 2026. Implementation and verification are in progress. No hosted
deployment or owner gameplay acceptance is claimed.

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
the server decoder agree. The candidate's window bypasses that local restriction
and its guarded slash hook permits requests for a fresh server-confirmed roster;
the server continues to authorize each recipient. A disposable native ABI test
exercises the controls while the original availability predicate returns false.

Regression tests also reproduced missing selection, stale lifecycle selection,
old-token snapshot rollback, and a stale individual order broadening to survivors.
The fixes reject stale UI scope before command dispatch and clear the exact
selected spawn when it disappears. The native full-engine check and exact owner
gameplay matrix are separate from the compiled fixtures.

## Delivery and recovery

Ship the matching server overlay/binaries with proxy `0.6.0-dev` candidate,
generated patch catalog and `uifiles/nightcap/equi_petinfowindow.xml`. The normal
signed launcher inventory accepts this UI asset; stock eqgame.exe remains
unchanged. Original client files are read-only during generation. Candidate assets
are staged under `E:\EQ_Local_Dev\artifacts\pet-management-20260922\assets`.

Take a fresh server backup before activation and preserve previous binary and
client manifests. No database migration is required. Revert only this feature's
binary/client generation together; never downgrade below the existing class-pet
persistence implementation or restore old player data. Signed game rollback uses
a higher release counter, as documented in the permanent patcher runbook.

[Exact QA](QA.md) · [Architecture](../../adr/0046-selected-pet-commands.md)

## Verification

Pending final build and native integration evidence. This section will be updated
with exact commands, results and hashes before the candidate is handed off.
