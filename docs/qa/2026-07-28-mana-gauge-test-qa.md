# Mana-gauge test QA spike — #12/#13

Date: 2026-07-28
Target branch: `test`
Client: exact RoF2 May 10 2013 build with the deployed Nightcap `dinput8.dll`

## Preconditions

1. Fully exit every RoF2 client so the deployed DLL reloads.
2. Start the Nightcap RoF2 client. If the world is black but UI is responsive,
   switch to fullscreen to recreate the D3D device.
3. Confirm the new `nightcap_dll_<PID>.log` contains:
   - `client size check: OK`
   - `client sha256 check: OK`
   - `B2 patch APPLIED`
   - `B2 mana hook APPLIED`
   - `B2 mana gauge APPLIED`

## Pups — Rogue/Wizard/Druid

1. Log in Pups and remain idle for at least 30 seconds.
   - Expected: the player mana gauge is continuously visible with no flicker.
2. Cast a mana-using spell and wait for regeneration.
   - Expected: current mana and gauge fill decrease, then rise smoothly.
3. Open Spell Gems and Spellbook, close them, and reopen them.
   - Expected: both windows behave normally.
4. Zone once, then camp and relog.
   - Expected: the gauge remains visible and tracks the restored value.

## Regression coverage

1. Log in a true zero-mana melee character.
   - Expected: no mana gauge appears.
2. Log in Done concurrently.
   - Expected: Done's stock caster mana gauge, Spell Gems, Spellbook, casting,
     regeneration, and zoning remain normal.

## Failure conditions

- Any gauge flicker, stale value, incorrect fill, or missing gauge on Pups.
- A visible mana gauge on a true zero-mana melee character.
- Spell-window regression, client crash, or a DLL guard/signature failure.

On a clean pass, explicitly sign off before merging `test` to `main`.
