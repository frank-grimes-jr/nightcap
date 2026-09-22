# 0046: Three-pet window and command selection

Date: 2026-09-22. Status: implementation candidate; owner gameplay QA required.

The player can summon three class pets but reports unresponsive controls and sees
only one pet in the native window. Preserve native command permissions, attack
checks, class ownership, persistence and armor while exposing the entire roster.

The Pet Info window gains three named health rows and an All pets button.
Clicking a row or targeting an owned pet selects that exact spawn for commands.
Enemy targeting preserves this selection so an individual pet can attack.
Clearing the game target or clicking All pets clears the control selection.
Selecting the same row again also clears it. Login/zoning begins in All pets.
Death, dismissal or ownership loss clears a selection; stale row requests are
rejected rather than interpreted as a broadcast. The window displays the server's
acknowledged selection. Armor selection remains independent.

Keep GetCommandPets as the complete owned roster for spell/lifecycle callers.
Only the command handler filters it. Selection requests are session-bound and
validate the exact live spawn against ownership. A separate compact snapshot
provides names, health and selection without depending on armor storage or issuing
chat commands through the client's interpreter. Polling is limited to one second
after this client explicitly opts in. No new schema or balance values are needed.

The token validates the session and roster, not each deliberate selection change.
Select and order requests follow the client's ordered packet processing; a quick
select/Attack pair uses the new selection even before its snapshot returns.
Automatic selection loss rotates the token to reject unintended shared orders.

Implementation: reproduce the existing command failure; repair its actual path;
add the server selection and snapshot; add a guarded native pet-window callback,
labels and generated XML; compile client/server and test protocol, routing and
lifecycle. Stage signed delivery assets separately from the original client.
The alternative of selection equaling the current target makes individual Attack
impossible; a separate external management window would miss the requested UI.

Acceptance: all ordinary buttons and slash commands broadcast by default; every
row and world-pet click isolates commands; enemy targeting retains selection;
clear target/All pets restores broadcast; stale/foreign requests do nothing;
death/reclaim/zoning/relog and mixed toggle states remain coherent. Exact-client
runtime and owner gameplay checks must remain explicit until performed.
