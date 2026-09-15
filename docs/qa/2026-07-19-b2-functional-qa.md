# B2 functional QA — 2026-07-19

## Scope

Validate the RoF2 DLL caster-chassis correction and the server mana path for a
melee-base multiclass character. Test characters:

- **Pups:** Rogue / Wizard / Druid (GM account)
- **Done:** Cleric / Shadow Knight / Monk (non-GM account)

## Evidence and implementation

- The exact RoF2 `OP_ManaUpdate` handler reads a 10-byte packet as
  `uint16 spawn_id`, `uint32 current mana`, `uint32 maximum mana`.
- EQEmu now has a RoF2-specific encoder for that layout.
- The server's `[ManaInit]` diagnostic recorded Pups as spawn ID `260`, mana
  `148/148`.
- The DLL trace subsequently recorded Pups's local raw fields as
  `current=148 max=148`.
- The guarded `Max_Mana` detour returns `LocalPlayer+0x354` only for the four
  stock non-caster base classes and only after the exact client guards pass.
- `MQ2EQIM` autoload is disabled after its independent null chat-service crash.

## Manual result — PASS

- DLL loaded and caster-class patch applied.
- Spell Gems opened for Pups and Done.
- Spellbook opened for Pups and Done.
- Pups inventory reported mana.
- Pups successfully cast spells.
- Zoning remained stable.
- No client crash recurred.

## Known cosmetic limitation

The standard mana bar is still absent for the Rogue-base HUD chassis. This does
not block mana accounting, inventory display, or spell casting and is tracked
as a separate cosmetic follow-up.

## Regression checklist for future builds

1. Fully restart MacroQuest2 and both EQ clients.
2. Confirm the DLL log contains `B2 patch APPLIED` and `B2 mana hook APPLIED`.
3. Log in Pups; verify inventory mana and cast a spell.
4. Confirm current mana decreases after casting; zone and verify it reloads.
5. Log in Done concurrently; verify its mana bar, gems, spellbook, casting,
   and one zone.
6. Retain both per-process DLL logs and check for crashes.
