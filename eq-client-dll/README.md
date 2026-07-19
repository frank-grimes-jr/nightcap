# eq-client-dll — Nightcap `dinput8.dll` proxy

Client-side UI-chassis unlock for the True Multiclass epic (#10), Track B / issue #12.
RoF2 auto-loads `dinput8.dll` from its own folder; this proxy forwards all
DirectInput exports to the real system DLL and patches the client's exact
caster-class capability table so any base class can use the caster UI chassis.

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
- **B2 caster-class table: window QA passed; not a mana gate.** The four table
  entries enable the caster-window activation paths, but a verified successful
  table patch still left Pups without a mana bar at `0/0`.
- **B2 server-mana experiment: rejected and removed.** Runtime samples proved
  the object exported as `pinstLocalPlayer` does not hold the decoded
  `OP_ManaUpdate` values at `+0x494/+0x354`: Pups produced `22200/0`, not the
  server's `148`. The six-byte `Max_Mana` detour has been withdrawn.
- **Fail closed:** the patch requires the expected file size, full SHA-256, and
  exact complete class-table signature. Any mismatch leaves memory untouched
  and is recorded in the per-process log.

## Build

Requires VS Build Tools 2022 (x86). RoF2 is 32-bit — **do not build x64**.

```
build.bat
```

Output: `build\dinput8.dll`.

## Deploy / test (dev client)

1. Copy `build\dinput8.dll` next to `eqgame.exe` in
   `Client_RoF2_Dev\everquest_rof2\`.
2. Launch the client normally (desktop shortcut).
3. The survey writes `nightcap_dll_<PID>.log` beside `eqgame.exe`. Separate EQ
   clients get separate logs.

## B2 safe-build QA

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

## Remove

Delete `dinput8.dll` from the client folder. Stock behavior restored (a backup
`eqgame.exe.nightcap-bak` also sits alongside).

## Layout

- `src/dllmain.cpp` — proxy + forwarding + init thread
- `src/dinput8.def` — export names
- `build.bat` — x86 MSVC build
- `third_party/` — cloned offset references (gitignored)
