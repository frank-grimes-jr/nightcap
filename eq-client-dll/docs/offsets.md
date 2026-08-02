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

## 2026-07-19 live-client result: exact window gates

The corrected two-client survey captured 991 initialized eqgame offsets in
each process. Done (Cleric base) and Pups (Rogue base) both had non-null,
fully initialized `CCastSpellWnd` and `CSpellBookWnd` objects. Pups' objects
also had valid on-screen rectangles, so construction and geometry were ruled
out.

MQ2 `/windowstate <name> open` reaches stock `CXWnd::Show(true, true, true)`,
but `CXWnd::Show` first calls the window's virtual `CanShow` method. Both
window overrides call the same base-class predicate. Its 16-byte class table
is:

| Class IDs | 1 WAR | 2 CLR | 3 PAL | 4 RNG | 5 SHD | 6 DRU | 7 MNK | 8 BRD | 9 ROG | 10 SHM | 11 NEC | 12 WIZ | 13 MAG | 14 ENC | 15 BST | 16 BER |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stock value | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |

The four zeros exactly match the four stock no-mana classes. The first B2
correction deliberately left the table unchanged and disabled only the
rejection branch immediately following that predicate in the two window
`CanShow` methods:

| Window | Signature RVA | Expected signature | Changed bytes |
|---|---:|---|---|
| `CCastSpellWnd` | `0x00248867` | `E8 E4 B6 DF FF 85 C0 74 E7` | final `74 E7` → `90 90` |
| `CSpellBookWnd` | `0x0035C97F` | `E8 CC 75 CE FF 85 C0 74 66` | final `74 66` → `90 90` |

These are RVAs from the loaded `eqgame.exe` base, not preferred virtual
addresses. The write is allowed only for the 8,774,656-byte client with SHA-256
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`, and
only when both full signatures match. This version preserved all other
`CanShow` conditions and all unrelated class behavior.

## 2026-07-19 window QA follow-up: shared caster chassis required

The window-only correction passed: Pups could open both Spell Gems and
Spellbook with normal controls. Pups then displayed `0/0` mana and could not
cast. A read-only database check proved this was not server state:

| Character | Base / class2 / class3 | Saved server mana |
|---|---|---:|
| Pups | ROG / WIZ / DRU | 148 |
| Done | CLR / SHD / MNK | 103 |

A complete disassembly search found exactly five calls to the shared caster
predicate in the entire executable:

| Preferred VA | Role |
|---:|---|
| `0x004916DF` | caster capability check |
| `0x004C300D` | caster UI initialization/activation |
| `0x004F731A` | spellbook command/activation path |
| `0x00648867` | `CCastSpellWnd::CanShow` |
| `0x0075C97F` | `CSpellBookWnd::CanShow` |

Because the predicate has a small, closed consumer set and the server remains
authoritative for actual mana and spell access, the replacement correction
enables its four stock-zero entries directly:

- table RVA: `0x00043F90`
- expected 16-byte signature:
  `00 01 01 01 01 01 00 01 00 01 01 01 01 01 01 00`
- enabled signature:
  `01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01`
- changed entries: class indexes `0, 6, 8, 15` = WAR, MNK, ROG, BER

This replaces the two branch patches rather than stacking with them and still
changes four bytes total. It was the next evidence-based candidate for the full
caster chassis; the mana test below proved its scope is window activation only.
The file-size and full SHA-256 guards remain, and the complete 16-byte stock
table must match before any write.

## 2026-07-19 mana QA follow-up: `Max_Mana` is independent

The shared caster table patch applied successfully in
`nightcap_dll_17020.log`, but Pups still had no mana bar and displayed `0/0`.
That disproves the table as the mana gate.

MQ2's captured build-exact methods led to the separate path:

| Symbol | Runtime RVA |
|---|---:|
| `EQ_Character::Cur_Mana` | `0x00044170` |
| `EQ_Character::GetManaRegen` | `0x00052DF0` |
| `EQ_Character::Max_Mana` | `0x00181E60` |
| `pinstLocalPlayer` | `0x009D2630` |

`EQ_Character::Max_Mana` dispatches on `BaseProfile.Class`. WAR, MNK, ROG, and
BER jump to a complete six-byte zero-return block:

- return-block RVA: `0x00181E96`
- exact stock signature: `33 C0 5E C2 04 00`
  (`xor eax,eax; pop esi; ret 4`)

Separately, RoF2's `OP_ManaUpdate` handler (`0x3791`) reaches preferred VA
`0x004CEDAE`, decodes `{spawn_id, cur_mana, max_mana}`, and calls preferred VA
`0x004BD210`. For the local spawn that function stores:

| Local-player field | Packet value |
|---:|---|
| `+0x494` | authoritative current mana |
| `+0x354` | authoritative maximum mana |

The complete handler proves the packet object is the exported local player:
preferred VA `0x004BD239` compares the spawn resolved from the packet ID in
`ESI` against the pointer stored at `pinstLocalPlayer` (`0x00DD2630` preferred,
RVA `0x009D2630`). Only the equal path writes `+0x494/+0x354`.

Runtime log `nightcap_dll_4860.log` showed those fields had not been populated:

- the sampled fields started at `0/0`;
- after entering world they became `22200/0`, not Pups' server value `148`;
- Pups still had no mana bar and remained at `0/0`.

The server zone-entry path explains why. It loads saved mana through
`Mob::SetMana(m_pp.mana)`, whose call site notes that it does not send a packet.
After `CompleteConnect()`, `Handle_Connect_OP_ClientReady` sends
`SendHPUpdate()` but did not send `SendManaUpdate()`. With no later mana
change, the local spawn fields remained stale.

The server now sends one self mana update after `CompleteConnect()` for modern
clients with a positive server maximum. A behavior-neutral DLL build again
samples `+0x494/+0x354`; it does not hook `Max_Mana`. The required proof is a
positive raw maximum for Pups after both login and zoning. The six-byte return
hook remains withdrawn until that capture succeeds.

The crash dump from the same session is separate from this rejected value
assumption. `eqgame_20260719_172253.dmp` records `0xC0000005` at
`eqgame.exe+0x003EFA80` (`mov eax,[ecx+0xD4]`) with `ECX=0`; the immediate
caller is `MQ2EQIM.dll+0x15C6`, which invokes
`CChatService::GetNumberOfFriends` after loading a null chat-service pointer.

## 2026-07-19 wire-layout finding: RoF2 `OP_ManaUpdate`

Disassembly of the exact client handler at preferred VA `0x004CEDAE` shows the
packet fields are read at offsets `0`, `+2`, and `+6`: `uint16 spawn_id`,
`uint32 cur_mana`, and `uint32 max_mana` (10 bytes total). The generic EQEmu
`ManaUpdate_Struct` is ordered `cur_mana`, `max_mana`, `spawn_id`, so a generic
encode produces a packet the RoF2 handler cannot resolve to the local spawn.
The server now uses a RoF2-specific `OP_ManaUpdate` encoder with the client
layout. The server diagnostic confirmed Pups was sending `148/148` with spawn
ID `260`; the client trace remained `0/0` until this wire correction.

## 2026-07-19 mana gauge visibility correction

The RoF2 `CPlayerWnd` constructor creates the `Player_Mana` child at
`CPlayerWnd+0x22C`. The child uses the normal `CXWnd::SetVisible` virtual at
vtable offset `+0xD8`. The new DLL correction runs from the guarded
non-caster `Max_Mana` return path and calls that stock setter only after a
positive server maximum is available. The global player-window slot is
`0x0091FC68` (RVA). All reads/calls are exception-guarded and the existing
client size/SHA and `Max_Mana` signature guards remain mandatory. The deployed
build is awaiting manual Pups/Done UI QA.

## 2026-07-28 mana gauge flicker root cause

Manual QA showed that the direct `PlayerMana::SetVisible(true)` correction was
temporary and flickered. `CPlayerWnd`'s update method begins at preferred VA
`0x00718D70`. Every 500 ms it calls the stock class predicate at
`0x0059FB90` from call-site RVA `0x00318E93`, then passes that result to
`PlayerMana::SetVisible`. Melee base classes therefore alternated between the
DLL's forced-visible state and the stock refresh's hidden state.

The stable correction replaces only the exact call bytes
`E8 F8 6C E8 FF` with a call to the DLL's guarded predicate. The replacement
returns true when the authoritative raw maximum at
`pinstLocalPlayer+0x354` is positive. This preserves the stock HUD refresh and
keeps true zero-mana characters hidden. The old direct `SetVisible` call from
the `Max_Mana` detour is removed.

## 2026-07-29 combat-ability window class gate

Manual QA on Monktest (Cleric / Shadowknight / Monk) showed that the Combat
Abilities control was grayed out and the window could not be opened even though
all six Monk skill rows were loaded at their level-50 caps.

`pinstCCombatAbilityWnd` is RVA `0x0091FCA0`. Its vtable is at preferred VA
`0x009E63B0`, and the `CanShow` override is the entry at `+0xDC`, preferred VA
`0x0065A070`. `CanShow` calls the base-class predicate at `0x00582350`. That
predicate indexes this 16-byte table by `BaseProfile.Class - 1`:

- table RVA: `0x0018238C`
- stock signature:
  `00 01 00 00 00 01 00 00 00 01 01 01 01 01 00 00`
- enabled signature:
  `00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00`
- changed indexes: `1, 5, 9, 10, 11, 12, 13` = CLR, DRU, SHM, NEC, WIZ,
  MAG, ENC

Table value `0` selects the predicate's true return and value `1` selects
false. The patch is presentation-only: the server still validates learned
skills, held classes, reuse timers, targets, and submitted ability packets.
It retains the executable size/SHA guard, requires the complete stock table,
verifies the replacement, restores the original page protection, and performs
a separately guarded verified rollback on failure.

The guard authenticates the executable file on disk and this loaded patch site;
it is not whole-process anti-tamper. The compare/write sequence is also not
atomic against another injected thread writing the same 16 bytes concurrently.
Supported plugins must leave this table alone; suspending every client thread
for a presentation-table patch would introduce greater deadlock/crash risk.

## 2026-07-29 Actions ability-selector skill gate

Monktest's six positive Monk skills were absent from the Actions window's
right-click ability picker even though the RoF2 profile encoder sends all 100
server skill values unchanged. `CSkillsSelectWnd::SetTypesToDisplay`, preferred
VA `0x00756CE0`, separates activated combat and non-combat skills but sends both
paths through `CharacterZoneClient::HasSkill`:

- non-combat predicate call RVA: `0x00356D2D`
- combat predicate call RVA: `0x00356DA5`
- stock call target: `CharacterZoneClient::HasSkill`, RVA `0x0004A1B0`
- raw received-value accessor: `CharacterZoneClient::GetBaseSkill`, RVA
  `0x00049C80` (one meaningful skill argument plus an unused stack slot;
  `ret 8`)

`HasSkill` calls the adjusted skill accessor, whose path reaches
`CSkillMgr::GetSkillCap` and therefore clamps a held-class skill through the
primary client class. The guarded replacement preserves a true stock result and
otherwise returns true only when `GetBaseSkill` reports a positive
server-delivered value. The selector's existing activated/combat classification
continues to decide which skills can be listed.

Only the two five-byte relative calls are redirected. The complete stock calls
and both accessor entrypoints are pinned by the exact-client regression. The
write covers their shared executable-page span, rechecks both sites after
changing protection, verifies both replacements, restores both originals on any
failure, and requires the original page protection to be restored.

## 2026-08-02 Held-skill hotbutton and activation gates

The selector correction made held Monk skills assignable, but a second
presentation check rendered the resulting type-9 hotbutton **Not Usable**, and
`CharacterZoneClient::UseSkill` independently rejected the activation before
packet submission:

- hotbutton `HasSkill` call RVA: `0x00151B59`
- `UseSkill` adjusted-value call RVA: `0x0005B33E`
- stock adjusted-value accessor: `CharacterZoneClient::GetSkill`, RVA
  `0x00049FE0`

The hotbutton call is redirected to the same boolean predicate used by the
Actions selector. The `UseSkill` call requires a separate integer-returning
wrapper: it preserves a positive stock adjusted value and otherwise uses the
positive `GetBaseSkill` value sent by the server. The execution patch is a
precondition for the presentation patch. Only these two complete five-byte
calls are changed; later `UseSkill` state, target, and reuse checks remain
stock, followed by server-side authorization.
