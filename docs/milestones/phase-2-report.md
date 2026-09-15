# Phase 2 milestone report — multiclass caster chassis

Date: 2026-07-28
Status: **Mana gauge flicker fix accepted and promoted to main**

## Built

- Version-guarded RoF2 `dinput8.dll` proxy.
- Caster-class capability table correction for WAR/MNK/ROG/BER base classes.
- RoF2-specific `OP_ManaUpdate` wire encoder.
- Server initial self-mana update through the connected-state path.
- Guarded `Max_Mana` hook backed by the validated local raw maximum.
- Guarded CPlayerWnd mana-visibility predicate backed by the server maximum.
- MQ2EQIM crash isolation by removing its autoload entry.

## Accepted

Pups (ROG/WIZ/DRU) receives `148/148` mana, shows a stable HUD gauge, and casts
spells. The gauge tracks casting/regeneration and survives zoning/relogging.
A true zero-mana melee character remains hidden. Pups and Done open Spell Gems
and Spellbook, and Done's stock caster HUD remains intact.

## Pending

No remaining work for the mana-gauge flicker fix. The user explicitly approved
the `test` to `main` promotion on 2026-07-28.

## Shaky / operational notes

- The active `akk-stack/code/` tree is a local ignored source overlay in the
  container workspace; the root feature commits contain the DLL, documentation,
  and audit trail, while the deployed zone binary was built from that overlay.
- RoF2 packet structs are client-version-specific; future packet changes must
  be disassembled against the exact executable and guarded by its size/hash.
- Every zone process must be restarted after a zone/common rebuild.
- `MQ2EQIM` must remain disabled until its null chat-service path is separately
  corrected and QA'd.
- If the world turns black while UI remains responsive, switching the RoF2
  client to fullscreen can recreate the D3D device and restore rendering.
