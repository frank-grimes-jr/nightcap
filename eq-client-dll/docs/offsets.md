# RoF2 UI-unlock symbol map (B0 / issue #12)

Confirmed symbol set for the spellbook / spell-gem UI unlock (B2). Source:
`dumpbin /exports mq-rof2/MQ2Main.dll` (May 10 2013 RoF2-emu build — the same
client we ship in `Client_RoF2_Dev/`).

## ⚠️ What these addresses are — and are NOT

The addresses below are **RVAs inside MQ2Main.dll**, not `eqgame.exe` offsets.
Proof: MQ2Main.dll's image size is `0x242000`, and every `pinst*` address is
below that — they are variables in MQ2Main's own `.data` that hold the eqgame
runtime pointers at MQ2 load time; they do not themselves encode an eqgame
offset.

So this file **confirms the symbol set and names** (feasibility: MQ2-emu tracks
exactly the globals we need), but the **actual `eqgame.exe` addresses B2 must
patch are not recoverable from the export table**. Get them from one of:

1. **MQ2-emu source `eqgame.h` / `eqgame-private.h`** (macroquest2 repo, `ROF2EMU`
   config). These `#define __pinstCSpellBookWnd_x 0x…` constants are the eqgame
   VAs. **Preferred** — same build, offsets transfer directly.
2. **Live-client debugger** (x32dbg on `testeqgame.exe`): resolve the window
   instance pointers and the class-gate branch by breakpoint. Needed anyway for
   the B0 proof, so it doubles as offset validation.

Whatever the source, every offset must pass the version guard (client size
8,774,656 / sha256 `2a8702ad…`) before B2 writes memory — see `dllmain.cpp`.

## Window instances (force-show targets)

| Symbol | MQ2Main export RVA | Role |
|---|---|---|
| `pinstCSpellBookWnd` | `0x0022ACCC` | spellbook window instance |
| `pinstCCastSpellWnd` | `0x0022AED0` | spell-gem / cast bar window instance |

## Character / class (the gate input)

| Symbol | MQ2Main export RVA | Role |
|---|---|---|
| `pinstPCData` / `pinstCharData` | `0x00226D6C` / `0x00224B90` | local PcClient / char data |
| `pinstLocalPlayer` | `0x0022AFB8` | local player spawn |
| `pinstControlledPlayer` | `0x00228D64` | controlled spawn |
| `CEverQuest::GetClassDesc` | `0x00006DD0` (code) | class → name (for sanity logging) |
| `ProfileManager::GetCurrentProfile` | `0x00007D40` (code) | `BaseProfile` → `.Class` is the UI gate |

## Memorize / gem methods (server already authoritative)

| Symbol | MQ2Main export RVA | Role |
|---|---|---|
| `CSpellBookWnd::MemorizeSet` | `0x00224C88` | scribe→gem; server re-validates |
| `CCastSpellWnd::ForgetMemorizedSpell` | `0x00228CEC` | clear a gem |

## Minimum viable B2 surface

Server-side right-click scribe already works (`Spells:AllowSpellMemorizeFromItem
= true`, 2026-07-15), so a base class can scribe without the spellbook. The DLL's
required surface therefore shrinks to: **force `CCastSpellWnd` (spell gems) +
memorize UI available regardless of `BaseProfile.Class`.** Spellbook window is a
nice-to-have, not a blocker. This is the smallest thing to prove in B0.
