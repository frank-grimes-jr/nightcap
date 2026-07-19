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

That disassembly established where one packet-handler object receives the
values, but not that the object is MQ2's exported `pinstLocalPlayer`. The first
experimental hook assumed they were the same.

Runtime log `nightcap_dll_4860.log` rejected the assumption:

- the sampled fields started at `0/0`;
- after entering world they became `22200/0`, not Pups' server value `148`;
- Pups still had no mana bar and remained at `0/0`.

The `LocalPlayer+0x354` detour and the field-sampling code were therefore
removed. The `Max_Mana` class dispatch and six-byte zero-return block remain
verified research facts, but no further hook should be installed until the
packet destination or authoritative profile field is identified dynamically.

The crash dump from the same session is separate from this rejected value
assumption. `eqgame_20260719_172253.dmp` records `0xC0000005` at
`eqgame.exe+0x003EFA80` (`mov eax,[ecx+0xD4]`) with `ECX=0`; the immediate
caller is `MQ2EQIM.dll+0x15C6`, which invokes
`CChatService::GetNumberOfFriends` after loading a null chat-service pointer.
