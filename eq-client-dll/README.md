# eq-client-dll — Nightcap `dinput8.dll` proxy

Client-side UI-chassis unlock for the True Multiclass epic (#10), Track B / issue #12.
RoF2 auto-loads `dinput8.dll` from its own folder; this proxy forwards all
DirectInput exports to the real system DLL and patches the client's exact
caster and combat-ability capability tables so any base class can reach the
server-authorized UI chassis.

## Status

- **B1 (skeleton): built + smoke-passed.** Forwards all six exports, init thread
  logs only, no memory patched. Reproducible x86 build; its log
  confirms load/init/unload against `testeqgame.exe`, game ran identically.
- **B0 (feasibility): GO.** See `docs/adr/0004`. Symbol set confirmed in
  `mq-rof2/MQ2Main.dll`; full map in `docs/offsets.md`.
- **B2 survey: passed.** Simultaneous Done (Cleric) and Pups (Rogue) captures
  showed both window objects fully constructed for both clients. Live memory
  inspection and disassembly identified the exact shared class predicate and
  its two window-specific rejection branches.
- **B2 window-only correction: QA passed, but incomplete.** Pups could open
  Spell Gems and Spellbook with the two narrow branch corrections, proving the
  window analysis. The Rogue client still displayed `0/0` mana even though the
  server had saved mana `148`, so it could not cast.
- **B2 caster-class table: safe-build QA passed; not a mana gate.** Pups and
  Done both opened Spell Gems and Spellbook normally and zoned successfully
  without a crash. Pups remained without a mana bar at `0/0`.
- **B2 mana path: functional QA passed.** RoF2's exact 10-byte
  `OP_ManaUpdate` layout is encoded server-side; Pups receives raw `148/148`,
  and the guarded `Max_Mana` detour exposes that value to the client UI/casting
  path.
- **B2 mana gauge correction: flicker fix built + deployed, QA pending.**
  `CPlayerWnd`'s stock 500 ms refresh now bases `PlayerMana` visibility on the
  positive server-cached maximum. This replaces the competing direct
  `SetVisible` reassertion that manual QA found could flicker.
- **G006 held-Monk activation: built + deployed, QA pending.** Exact disassembly
  localized the no-op to RoF2's direct-skill dispatch. Six Monk attack
  hotbuttons now enter the stock special-attack submitter, with its one
  primary-class skill predicate corrected only for those positive
  server-granted skills. Feign Death and Mend retain their stock `UseSkill`
  handlers; the separate discipline window remains enabled but correctly empty
  for a character with no learned disciplines.
- **Fail closed:** the patch requires the expected file size, full SHA-256, and
  exact complete class-table signatures. Any mismatch leaves memory untouched
  and is recorded in the per-process log.

## B2 final functional QA — passed 2026-07-19

The completed server/client path is now functional for a Rogue-base multiclass:

- RoF2 `OP_ManaUpdate` is encoded as the client-required 10-byte layout
  (`spawn_id`, current mana, maximum mana).
- Pups (ROG/WIZ/DRU) receives raw local mana `148/148` after login.
- The guarded `Max_Mana` hook returns the validated local maximum for the four
  stock non-caster base classes.
- Inventory reports mana and Pups can cast spells successfully.
- Spell Gems and Spellbook open normally; zoning remains stable.
- No crash recurred after disabling `MQ2EQIM` autoload.

The standard mana bar correction is now deployed to the dev client and needs
the focused in-game QA below before promotion.

### Final QA steps

1. Fully restart MacroQuest2 and the EQ client so the deployed DLL and
   `MacroQuest.ini` are reloaded.
2. Confirm the DLL log contains `B2 patch APPLIED` and `B2 mana hook APPLIED`.
3. Log in Pups and verify the inventory mana value and mana-based spell cast.
4. Cast again to confirm current mana decreases, then zone and verify mana
   persists/reloads correctly.
5. Log in Done concurrently and verify its mana bar, gems, spellbook, casting,
   and one zone as regression coverage.
6. For Pups, confirm the standard player mana bar is visible. Cast a spell and
   verify the fill decreases; wait for regeneration, then zone and relog to
   verify it remains visible and tracks the restored value.

## Build

Requires VS Build Tools 2022 (x86). RoF2 is 32-bit — **do not build x64**.

```
build.bat
```

Output: `build\dinput8.dll`.

Static exact-client guard test:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tests\verify-exact-client-patch-sites.ps1
```

For held-class activated skills, the DLL also corrects the exact RoF2
**Actions -> Abilities** selector. It preserves the stock `HasSkill` result and
accepts a stock-negative skill only when the server-delivered base value is
positive. The assigned skill's hotbutton usability and the pre-submit
`CharacterZoneClient::UseSkill` value check use the same server-delivered
fallback. All subsequent client checks and all server authorization remain
stock. The Combat Abilities window is separate and remains the learned
discipline/tome surface.

RoF2 does not implement the six basic Monk attacks in direct `UseSkill`
dispatch. For Dragon Punch/Tail Rake, Eagle Strike, Flying Kick, Kick, Round
Kick, and Tiger Claw only, the hotbutton redirect calls the client's stock
special-attack submitter and then its stock skill-reuse sequence. The submitter
still owns client target/state/animation behavior, and EQEmu still validates
the packet, held classes, caps, range, reuse, damage, and skill-ups.

## Deploy / test (dev client)

1. Copy `build\dinput8.dll` next to `eqgame.exe` in
   `Client_RoF2_Dev\everquest_rof2\`.
2. Launch the client normally (desktop shortcut).
3. The survey writes `nightcap_dll_<PID>.log` beside `eqgame.exe`. Separate EQ
   clients get separate logs.

## B2 safe-build QA — passed 2026-07-19

1. Start `MacroQuest2.exe`, then launch EQ through the method that injects MQ2.
   `MQ2EQIM` has been removed from `MacroQuest.ini` autoload because the July 19
   dump identifies it as a separate null-pointer crash source.
2. Log in Pups (Rogue base). Confirm the new `nightcap_dll_<PID>.log` contains
   `client size check: OK`, `client sha256 check: OK`, and `B2 patch APPLIED`.
   It must not contain `B2 mana hook APPLIED`.
3. Use the normal EQ controls (not `/windowstate`) to open Spell Gems and the
   Spellbook. Both must still appear. Close and reopen each.
4. Confirm Pups remains at the known baseline (`0/0`, no mana bar). This build
   intentionally does not claim to correct mana.
5. Zone once and repeat the window open/close checks.
6. With Pups still running, log in Done (Cleric base) in a second client, then
   verify Done's stock mana bar, Spell Gems, Spellbook, memorization, casting,
   regeneration, and one zone.
7. Exit both clients and retain both new per-process logs.

Failure conditions: either guard reports a mismatch, a window fails to appear,
normal close/reopen stops working, Done regresses, or either client crashes.
Pups remaining at `0/0` is expected for this safe build. The MQ2 survey remains
for diagnostics, but the correction itself does not depend on MQ2.

Recorded result: all guard, window, dual-client, and zoning checks passed.
No crash recurred. The unresolved acceptance blocker is Pups' `0/0` mana.

## B2 mana gauge QA - pending

1. Fully exit MacroQuest2 and all EQ clients, then restart them so the newly
   deployed DLL is loaded.
2. Log in Pups and retain the new `nightcap_dll_<PID>.log`.
3. Confirm the log contains `B2 mana hook APPLIED` and
   `B2 mana gauge APPLIED`.
4. Confirm the normal player mana bar is visible and starts at the inventory
   value (currently `148/148`). Cast a known spell and verify the fill/value
   decreases; wait for regeneration.
5. Zone once and relog Pups. The bar must remain visible and track current and
   maximum mana.
6. Log in Done concurrently and verify its stock mana bar, Spell Gems,
   Spellbook, casting, and one zone.

Failure conditions: no `B2 mana gauge APPLIED` log, any flicker,
missing/stale bar, incorrect fill/value, a visible zero-mana bar on a
non-multiclass melee character, any window regression, or a crash.

## B2 initial-mana trace QA

1. Log in Pups and remain in world for at least 20 seconds.
2. Confirm Spell Gems and Spellbook still open normally.
3. Pups is expected to remain at `0/0`; this trace does not alter
   `EQ_Character::Max_Mana`.
4. Zone once, then remain in world for another 20 seconds.
5. Exit the client and retain the new `nightcap_dll_<PID>.log`.

Pass condition: after both login and zoning, the log contains
`local spawn raw mana current=... max=148` (or another positive authoritative
maximum). Any `max=0`, crash, or window regression fails the trace.

## Remove

Delete `dinput8.dll` from the client folder. Stock behavior restored (a backup
`eqgame.exe.nightcap-bak` also sits alongside).

## Layout

- `src/dllmain.cpp` — proxy + forwarding + init thread
- `src/dinput8.def` — export names
- `build.bat` — x86 MSVC build
- `third_party/` — cloned offset references (gitignored)
