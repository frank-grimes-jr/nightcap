# September 19 silent UI synchronization — release 2026091906

## Behavior and cause

Owner login QA exposed two automatic `/say` commands. Class/AA metadata and pet
armor snapshots were requested through the normal slash-command interpreter,
which invoked the client's local Say echo. Release 1906 sends the same bounded
requests directly through the native channel packet sender. Login, zoning,
refresh and pet armor buttons require no typed commands and generate no local
command echo or history entries. Normal chat and server action errors remain
visible; metadata replies continue to feed the custom UI.

This is a client-only correction. The existing server dispatcher handles each
`#nightcapui` / `#nightcappet` request before chat broadcast or NPC say events.
Identity, ownership, nonce, rate limits, combat/trade restrictions and item
transactions are unchanged. This is silent presentation, not a new private
network protocol: server diagnostic logs may still record requests. Existing
channel handling still resets the AFK timer and rejects AI-controlled non-GMs.

## Native evidence and verification

The pinned executable's sender is VA `0x0051DCD0`, RVA `0x0011DCD0`, with
`__thiscall(eq, channel, target, text, arg4)` and `ret 0x10` at `0x0051E1FF`.
Native Say passes channel 8, text and arg4 0 at `0x0051F60E`; its separate local
echo occurs at `0x0051F67B`. The direct sender has no chat-display or interpreter
call. Generated requests have no percent tokens for native text conversion.
The new call uses a null target, so it does not address the selected NPC.

The signed catalog replaces the unused interpreter guard with the sender's
`6A FF 68 48 84 97 00` prologue. Runtime verification rebases its SEH operand
before comparing. Proxy version is **0.4.2-dev**, with **34 guards / 12 required
features / mask 4095**. Sending requires in-world identity, character profile
and a live connection pointer. Both refresh timers retain their five-second
retry interval; unsuccessful preconditions do not advance the timer.

Native tests exercise both login requests, all three pet action verbs, retry
throttling, missing context/character-select rejection and normal chat/error
visibility. Existing pet-state tests verify nonce/slot/action payloads without
`/say`. The x86 build, exact-client byte verifier and five runtime test groups
pass. Independent disassembly and implementation review found no blocking issue.
Native character login is still required to accept the visible result.

## Delivery

Signed package/build and installation evidence is recorded under
`E:/EQ_Local_Dev/artifacts/client-silent-ui-20260919/`. The established launcher
path remains `artifacts/client-gameplay-20260919/launcher-final/nightcap-launcher-qa.exe`.
Installation completed September 20 at 00:23:38 UTC (September 19 local). All 13
manifest files match size and SHA256; the original eqgame.exe hash is unchanged.
Actual game PID 26088 reported proxy 0.4.2, ready, required/enabled/applied masks
4095, then stopped cleanly after the ten-second startup check. Both Go test
configurations, frontend typecheck/build and the Windows launcher build passed.

Manifest SHA256: `b37a6ce0d7e399e034e971634942ab9dabebb6f3f97a9e1fef0b2b6958c6ff49`.
Launcher SHA256: `179975c238645af5d301ddd1949df37812c712a52e815d82b057af178a5a9605`.
The previous launcher files are retained in `launcher-before/`, its generated
policy/bundle in `bundle-before/`, and the installer retains transaction backups.

No server restart, database migration, gameplay tuning or AA title changes are
part of this repair. The prior owner authorization covers signed repair of the
original client folder and promotion of this release through main.

## Exact in-game QA

1. Use the usual QA launcher, log into a character in Plane of Knowledge, and
   wait ten seconds. No `#nightcapui`, `#nightcappet`, or automatic "You say"
   lines should appear. Inventory still shows three classes and AA rows retain
   their class column. Missing AA title strings remain a separate catalog issue.
2. Open Inventory > Pet Armor. The selected owned pet and eight armor slots
   populate. Refresh, equip an eligible cursor item, inspect it, then remove it
   with an empty cursor. Each action updates the UI without exposing requests.
3. Attempt a blocked armor action during combat: its normal error must remain
   visible. Type an ordinary `/say hello`; it must still display normally.
4. Zone out and back, then camp and log into another character. Metadata reloads
   for the current character without command echo; command history has no
   injected Nightcap requests.

Manual acceptance is pending. Rollback is to the retained signed 1905 launcher
and package using the established controlled rollback procedure; its visible
requests return, but server state and pet items require no rollback.
