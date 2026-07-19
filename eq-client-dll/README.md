# eq-client-dll — Nightcap `dinput8.dll` proxy

Client-side UI-chassis unlock for the True Multiclass epic (#10), Track B / issue #12.
RoF2 auto-loads `dinput8.dll` from its own folder; this proxy forwards all
DirectInput exports to the real system DLL and (eventually) patches the client's
class-gated UI in memory so any base class can open the spellbook / gem / disc
windows.

## Status

- **B1 (skeleton): built + smoke-passed.** Forwards all six exports, init thread
  logs only, no memory patched. Reproducible x86 build; its log
  confirms load/init/unload against `testeqgame.exe`, game ran identically.
- **B0 (feasibility): GO.** See `docs/adr/0004`. Symbol set confirmed in
  `mq-rof2/MQ2Main.dll`; full map in `docs/offsets.md`.
- **B2 survey: active.** MQ2 injection and hidden-image discovery are proven.
  Survey v2 uses verified wall-clock waits, initialization retries, and a
  per-EQ-process log so caster/melee clients can run simultaneously.
- **B2 UI unlock: not started; awaiting the corrected survey capture.** The
  capture decides whether melee-base spell windows exist but are hidden or must
  be constructed before showing.

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

## B2 survey QA

1. Start `MacroQuest2.exe`, then launch EQ through the method that injects MQ2.
2. Confirm `/plugin list` is handled by MQ2.
3. Log a caster-base character (Done, Cleric) in one client. Open the spell-gem
   and spellbook windows and leave the client running for at least 60 seconds.
4. Log a melee-base character (Pups, Rogue) in another client. Try the same
   windows (stock behavior is still expected to do nothing) and leave it running
   for at least 60 seconds.
5. Exit both clients and collect every new `nightcap_dll_<PID>.log`.

A valid log contains `MQ2 found`, at least one `OFFSET` block, and `watch`
samples whose `elapsed=` values advance by approximately 15 seconds. The
caster log should show nonzero spell-window instances. Whether the Rogue log
shows zero or nonzero instances determines the B2 implementation path.

## Remove

Delete `dinput8.dll` from the client folder. Stock behavior restored (a backup
`eqgame.exe.nightcap-bak` also sits alongside).

## Layout

- `src/dllmain.cpp` — proxy + forwarding + init thread
- `src/dinput8.def` — export names
- `build.bat` — x86 MSVC build
- `third_party/` — cloned offset references (gitignored)
