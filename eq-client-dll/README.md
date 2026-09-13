# eq-client-dll — Nightcap `dinput8.dll` proxy

Client-side UI-chassis unlock for the True Multiclass epic (#10), Track B / issue #12.
RoF2 auto-loads `dinput8.dll` from its own folder; this proxy forwards all
DirectInput exports to the real system DLL and (eventually) patches the client's
class-gated UI in memory so any base class can open the spellbook / gem / disc
windows.

## Status

- **B1 (skeleton): built + smoke-passed.** Forwards all six exports, init thread
  logs only, no memory patched. Reproducible x86 build; `nightcap_dll.log`
  confirms load/init/unload against `testeqgame.exe`, game ran identically.
- **B0 (feasibility): GO.** See `docs/adr/0004`. Symbol set confirmed in
  `mq-rof2/MQ2Main.dll`; full map in `docs/offsets.md`.
- **B2 (UI unlock): not started; blocked on offset extraction + interactive
  proof.** The MQ2Main export RVAs are *not* eqgame offsets (see `docs/offsets.md`)
  — real offsets come from MQ2-emu `eqgame.h` or a live-client debugger, mined in
  the same session that proves a Warrior can open the spell-gem window.

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
3. B1 pass = game runs exactly as without the DLL, and `nightcap_dll.log` appears
   in the client folder with "init complete".

## Remove

Delete `dinput8.dll` from the client folder. Stock behavior restored (a backup
`eqgame.exe.nightcap-bak` also sits alongside).

## Layout

- `src/dllmain.cpp` — proxy + forwarding + init thread
- `src/dinput8.def` — export names
- `build.bat` — x86 MSVC build
- `third_party/` — cloned offset references (gitignored)
