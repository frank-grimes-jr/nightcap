# Phase 2 milestone report — multiclass caster chassis

Date: 2026-07-19  
Status: **Functionally complete; cosmetic HUD follow-up remains**

## Built

- Version-guarded RoF2 `dinput8.dll` proxy.
- Caster-class capability table correction for WAR/MNK/ROG/BER base classes.
- RoF2-specific `OP_ManaUpdate` wire encoder.
- Server initial self-mana update through the connected-state path.
- Guarded `Max_Mana` hook backed by the validated local raw maximum.
- MQ2EQIM crash isolation by removing its autoload entry.

## Accepted

Pups (ROG/WIZ/DRU) receives `148/148` mana, shows mana in inventory, and casts
spells. Pups and Done open Spell Gems and Spellbook and zone without crashing.

## Cut / deferred

The standard mana bar is not rendered for the Rogue-base HUD chassis. It is a
cosmetic client follow-up; it does not block the functional B2 acceptance.

## Shaky / operational notes

- The active `akk-stack/code/` tree is a local ignored source overlay in the
  container workspace; the root feature commits contain the DLL, documentation,
  and audit trail, while the deployed zone binary was built from that overlay.
- RoF2 packet structs are client-version-specific; future packet changes must
  be disassembled against the exact executable and guarded by its size/hash.
- Every zone process must be restarted after a zone/common rebuild.
- `MQ2EQIM` must remain disabled until its null chat-service path is separately
  corrected and QA'd.
