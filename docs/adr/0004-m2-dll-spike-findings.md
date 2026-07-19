# ADR 0004 — M2 (B0) spike findings: RoF2 UI-unlock offsets source

Date: 2026-07-15 (updated 2026-07-19)
Status: **Accepted — GO on the DLL approach.** B1 smoke-passed; B2's guarded
caster-chassis correction is built and awaiting mana/casting QA.

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

## Update 2026-07-15 — offset source confirmed, B1 skeleton built

- **`mq-rof2/MQ2Main.dll` is directly the offset map** — its export table exposes
  the named globals we need, no gated mqemulator source required:
  - `pinstCSpellBookWnd` @ `0x0022ACCC`, `pinstCCastSpellWnd` @ `0x0022AED0`,
    `pinstPCData` @ `0x00226D6C`, `ppSpellBookWnd`/`ppCastSpellWnd`.
  - window methods `CSpellBookWnd::MemorizeSet`, `CCastSpellWnd::ForgetMemorizedSpell`.
  Read with `dumpbin /exports`. These must still be validated against our exact
  `eqgame.exe` build before B2 patches anything (version guard below).
- **B1 skeleton built and deployed** (`eq-client-dll/`): x86 `dinput8.dll`
  forwarding all six DirectInput exports to `System32\dinput8.dll`, init thread
  logs to `nightcap_dll.log` and does a client-size sanity check (8,774,656 bytes,
  sha256 `2a8702ad…`), no memory patched. Placed in `Client_RoF2_Dev/everquest_rof2/`
  next to a backup `eqgame.exe.nightcap-bak`. Awaiting user smoke test (B1
  acceptance: game runs identically, log appears).

## Update 2026-07-16 — B1 smoke-passed; offset-source claim corrected; GO

- **B1 acceptance met.** The proxy rebuilds reproducibly (MSVC x86, VS Build
  Tools 2022 at `C:\BuildTools`; `eq-client-dll/build.bat`), is confirmed x86
  with all six DirectInput exports forwarded, and **passed its in-game smoke
  test**: `nightcap_dll.log` shows load → client-size OK (8,774,656) → init
  complete → clean unload against `testeqgame.exe`. Game ran identically. B1 is
  done.

- **Correction to the 2026-07-15 offset-source claim.** The MQ2Main.dll export
  *table* does **not** directly give eqgame offsets. Its `pinstCSpellBookWnd
  0x0022ACCC` etc. are RVAs **inside MQ2Main.dll** (image size `0x242000`; all
  the `pinst*` addresses fall below it) — i.e. MQ2's own `.data` variables that
  hold the eqgame pointers at MQ2 load time. The export dump **confirms the
  symbol set and names** (feasibility), but the real `eqgame.exe` addresses B2
  patches must come from MQ2-emu **source** `eqgame.h` (ROF2EMU) or a live-client
  debugger. Full symbol map + this caveat: `eq-client-dll/docs/offsets.md`.

- **GO decision.** Feasibility is confirmed on every axis that can be settled
  without an interactive session: toolchain works end-to-end here, THJ precedent
  proves the class-UI gate is patchable, the exact symbol set exists, and the
  proxy loads cleanly in the real client. Proceed with the DLL approach (not the
  packet-illusion fallback).

- **B2 is NOT started, by design — it cannot be built-and-verified autonomously.**
  It writes client memory at offsets we do not yet hold, and its only real
  acceptance test ("a Warrior opens the spell-gem window and mems a scribed
  spell") requires a human watching a live client. Building speculative
  memory-patch code against unvalidated offsets would risk crashing the client
  with nothing verified. B2's concrete first step is the offset extraction above,
  done in the same interactive session as the B0 proof.

## Update 2026-07-19 — live gate identified; guarded B2 correction built

- Simultaneous Done (Cleric base) and Pups (Rogue base) captures passed the
  corrected timing checks and produced 991 eqgame offsets each. Both spell
  windows were non-null and fully initialized for Pups. `/windowstate` reached
  the stock show path but still did not make them visible.
- Live memory inspection and disassembly located the cause: both window
  `CanShow` overrides call one 16-byte base-class caster table. Its zero entries
  are exactly WAR, MNK, ROG, and BER.
- B2 deliberately leaves that shared table unchanged. It NOPs only the two
  conditional branches that reject the predicate result in
  `CCastSpellWnd::CanShow` and `CSpellBookWnd::CanShow`—four changed instruction
  bytes total. All other `CanShow` checks and all unrelated uses of the client
  class predicate remain stock.
- Writes fail closed behind three independent checks: exact file size, full
  SHA-256, and both complete nine-byte code signatures. A partial write is
  rolled back. Exact RVAs and signatures are recorded in
  `eq-client-dll/docs/offsets.md`.

## Update 2026-07-19 — window QA passed; caster table required for mana

- The window-specific correction worked: Rogue-base Pups opened Spell Gems and
  Spellbook normally. Pups still displayed `0/0` mana and could not cast.
- The server is not the fault. Pups is ROG/WIZ/DRU and has saved mana `148`;
  Done is CLR/SHD/MNK with saved mana `103`. The existing multiclass
  `CalcMaxMana()` path is active.
- A complete executable disassembly found only five calls to the shared caster
  predicate: the two known `CanShow` overrides and three caster
  initialization/activation paths. The consumer set is therefore bounded and
  matches the required chassis behavior.
- Replace, rather than stack on, the two branch patches. Enable the four
  stock-zero entries in the exact 16-byte class table at RVA `0x00043F90`.
  This still changes four bytes total and lets every caller see WAR/MNK/ROG/BER
  as caster-capable. The server continues to decide actual mana, spells, class
  membership, and casting legality.

## Decision

- Retain the `dinput8.dll` proxy approach.
- Enable the shared caster-class table because in-game evidence proved the
  window-specific correction is insufficient and the complete caller set is
  small, known, and aligned with the intended caster chassis.
- Require immutable version checks plus the complete stock table signature
  before every memory write.
- Promote no farther than the feature branch until Pups and Done pass the
  explicit in-game QA in `eq-client-dll/README.md`.

## Consequences

- `eq-client-dll/` remains a Windows x86-only subproject.
- Each newly supported RoF2 executable requires its own size, SHA-256, and
  verified table signature; unknown clients remain unmodified.
- The B2 scope is the caster UI chassis. Disc-window or other base-class
  corrections still require separate evidence and patches.
