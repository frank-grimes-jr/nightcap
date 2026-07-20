# Phase 2 milestone report — multiclass caster chassis

Date: 2026-07-19  
Status: **Mana gauge correction deployed; manual QA pending**

## Built

- Version-guarded RoF2 `dinput8.dll` proxy.
- Caster-class capability table correction for WAR/MNK/ROG/BER base classes.
- RoF2-specific `OP_ManaUpdate` wire encoder.
- Server initial self-mana update through the connected-state path.
- Guarded `Max_Mana` hook backed by the validated local raw maximum.
- Guarded Player_Mana visibility reassertion through the RoF2 CPlayerWnd child.
- MQ2EQIM crash isolation by removing its autoload entry.

## Accepted

Pups (ROG/WIZ/DRU) receives `148/148` mana, shows mana in inventory, and casts
spells. Pups and Done open Spell Gems and Spellbook and zone without crashing.

## Pending

The standard mana bar correction is deployed to the dev client. Manual QA must
confirm visibility, value tracking through casting/regeneration, and stability
for Pups before the feature is promoted.

## Shaky / operational notes

- The active `akk-stack/code/` tree is a local ignored source overlay in the
  container workspace; the root feature commits contain the DLL, documentation,
  and audit trail, while the deployed zone binary was built from that overlay.
- RoF2 packet structs are client-version-specific; future packet changes must
  be disassembled against the exact executable and guarded by its size/hash.
- Every zone process must be restarted after a zone/common rebuild.
- `MQ2EQIM` must remain disabled until its null chat-service path is separately
  corrected and QA'd.
