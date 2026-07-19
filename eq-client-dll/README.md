# eq-client-dll — Nightcap `dinput8.dll` proxy

Client-side UI-chassis unlock for the True Multiclass epic (#10), Track B / issue #12.
RoF2 auto-loads `dinput8.dll` from its own folder; this proxy forwards all
DirectInput exports to the real system DLL and narrowly patches the client's
spellbook and spell-gem visibility gates so any base class can open them.

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
- **B2 spell UI correction: built; awaiting in-game QA.** Four instruction
  bytes are changed: the two conditional branches that reject a non-caster
  base class in `CCastSpellWnd::CanShow` and `CSpellBookWnd::CanShow`. Other
  client class logic and the remaining window safety checks stay stock.
- **Fail closed:** the patch requires the expected file size, full SHA-256, and
  both complete nine-byte code signatures. Any mismatch leaves memory untouched
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

## B2 spell UI QA

1. Start `MacroQuest2.exe`, then launch EQ through the method that injects MQ2.
2. Log in Pups (Rogue base). Confirm the new `nightcap_dll_<PID>.log` contains
   `client size check: OK`, `client sha256 check: OK`, and `B2 patch APPLIED`.
3. Use the normal EQ controls (not `/windowstate`) to open Spell Gems and the
   Spellbook. Both must appear. Close and reopen each, then move each window.
4. Memorize one already-scribed spell into an empty gem and cast it on a valid
   target. Zoning must preserve a usable gem bar and spellbook.
5. With Pups still running, log in Done (Cleric base) in a second client.
   Repeat open/close, memorize, cast, and zone as a stock-caster regression.
6. Exit both clients and retain both new per-process logs.

Failure conditions: either guard reports a mismatch, a window still fails to
appear, normal close/reopen stops working, memorization/casting fails, Done
regresses, or either client crashes. The MQ2 survey remains in this build for
diagnostics, but the correction itself does not depend on MQ2.

## Remove

Delete `dinput8.dll` from the client folder. Stock behavior restored (a backup
`eqgame.exe.nightcap-bak` also sits alongside).

## Layout

- `src/dllmain.cpp` — proxy + forwarding + init thread
- `src/dinput8.def` — export names
- `build.bat` — x86 MSVC build
- `third_party/` — cloned offset references (gitignored)
