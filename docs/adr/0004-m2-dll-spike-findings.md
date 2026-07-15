# ADR 0004 — M2 (B0) spike findings: RoF2 UI-unlock offsets source

Date: 2026-07-15
Status: Proposed (go-leaning; final go/no-go needs one in-game proof session)

## Context

Epic #10 / issue #12: unlock spellbook, spell-gem and disc windows for any base
class via a `dinput8.dll` proxy patching the RoF2 client in memory. The B0 spike
must confirm the class-UI gating is patchable and identify the offset source.

## Findings

1. **`mq-rof2/` is a binary distribution, not a source tree.** It contains
   compiled MQ2 DLLs (MQ2Main.dll etc.) and inis — no `eqgame.h`, no offset
   headers. The epic's assumption that it is "effectively a complete eqgame
   offset map" holds only indirectly: the *source those DLLs were built from*
   is the offset map.

2. **The actual offset source is the MQ2-emu source tree**: the
   [macroquest2 repo](https://github.com/macroquest/macroquest2) carries a
   `ROF2EMU` build configuration whose `eqgame.h`/`eqgame-private.h` map the
   May 10 2013 RoF2 client — window classes (`CSpellBookWnd`, `CCastSpellWnd`),
   `PcProfile.Class`, and the display-manager vtables. This is the same client
   build we ship (`Client_RoF2_Dev/`), so offsets transfer directly.

3. **Precedent confirms feasibility ("go" signal):** THJ ships exactly this —
   a custom `dinput8.dll` that makes every base class caster-capable in the
   RoF2 UI. The client's class gating is compiled conditional checks against
   `PcProfile.Class`, patchable in memory (either by flipping the class checks
   in the window-activation code paths or by hooking window `Activate`).

4. **Server-side scribing no longer blocks on the DLL.** With
   `Spells:AllowSpellMemorizeFromItem = true` (enabled 2026-07-15), right-click
   on a scroll scribes it without opening the spellbook — so the DLL's minimum
   viable surface shrinks to: spell-gem window + memorize UI. That lowers B0
   risk further.

## Decision (proposed)

- Offset mining: clone the macroquest2 ROF2EMU tree and extract the window /
  PcProfile offsets from `eqgame.h`; do not reverse the binary DLLs.
- B1 proxy skeleton can proceed in parallel (no offsets needed to forward
  DirectInput exports).
- Final B0 proof (Warrior opens an empty spellbook in a dev client) requires an
  interactive client session — scheduled as the first step of the next M2 work
  block, before any B2 patch work.

## Consequences

- New subproject `eq-client-dll/` (C++, MSVC, x86) when B1 starts.
- Offset-versioning strategy (B3) should pin to the RoF2 build string the same
  way MQ2-emu does (compare `eqgame.exe` timestamp/checksum before patching).
