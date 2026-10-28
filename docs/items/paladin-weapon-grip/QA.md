# Owner QA — not yet run

## October28 — SoulFire animation investigation remains open

Owner confirms1HS inspection but two-handed-looking swing on Palwar. Two local
regression groups pass (80 server skill/animation selections), without reproducing
client rendering. No gameplay fix/deployment claimed. The subsequently approved production check confirms saved1H metadata and the
October26 running server; the client still behaves as2H per owner. The local
paired cache repair remains undeployed. No live writes occurred. Controlled14:48UTC check
confirms SoulFire equipped1H with an empty offhand; rendered swing QA remains open.
Evidence: docs/items/paladin-weapon-grip/client-refresh/animation/README.md.

**Current October28 candidate:** [approved progression implementation and release QA](balance/README.md) supersedes the earlier unchanged-stats/separate-Defender-forge plan. Not deployed.

**October 27 owner QA failed:** SoulFire printed the conversion messages but
remained 2H and refused a shield; zoning was not tried. The client cache repair
is implemented and locally tested, but is not deployed. See the
[repair candidate and current QA](client-refresh/README.md). The October 26
build/deployment evidence below is historical and does not validate the repair.

After the new candidate is authorized and deployed, use its matching native binaries
and signed RoF2 client;2026102601 alone does not contain the repair. Record each weapon ID, grip, saved instance fields and observations.

1. In East Commonlands, inspect and right-click each of the ten IDs in README.md
   from primary, a main inventory slot and a carried bag. The Skill line changes
   2HS → 1HS → 2HS exactly once per click. Check the effect label, no spell/buff/
   healing animation, no spell-bar lock and no target requirement. Confirm damage/delay match the balance table and restore exactly in2HS;
   other stats, procs, quality and equipment slots stay unchanged.
2. Repeat with SoulFire at 5, 1 and 0 saved charges. Every click toggles; no charges
   are consumed or restored and no Complete Heal is cast. Spam/repeated click
   packets must not duplicate or delete items. Verify the CastSpell follow-up
   never causes a second transition or casts spell 288/13.
3. Equip a shield with the 1HS weapon. Returning to 2HS must refuse and retain both
   items. Remove the shield; conversion succeeds. The 1HS sword remains primary-
   only. Ordinary equipment class/deity/level restrictions still apply.
4. Check both a 1HS-only and a 2HS-only augment: conversion to its unsupported
   type must refuse with all six sockets intact. Compatible, unrestricted augments,
   ornaments, color and attunement survive accepted toggles.
5. While autoattacking, engaged, casting, stunned, feared, mezzed, dead, trading,
   running a merchant buyer/trader or using a tradeskill station, conversion must
   refuse. Confirm no item changes. Return to a safe state and retry successfully.
6. Toggle to 1HS, zone East Commonlands → West Commonlands, log out/in, move through
   bags/personal bank/shared bank, trade to another character, and recover from a
   corpse. Confirm the grip, identity and every saved instance field persist.
   Test Commonlands bazaar posting/cancel/buy with that actual item. Inventory and
   listing inspection should show its grip; generic item links/search filters
   still describe the base definition. Stop on metadata or item loss.
7. Attack an appropriate training target with each grip. Confirm 1H/2H Slashing
   animations, skill gains, damage-bonus/AA handling and existing Avenger/Defender
   procs; compare shield-plus-1HS against2HS with the new damage/delay profiles.
8. Confirm a matching quest/task hand-in recognizes the same ID in either grip.
   Reforging rejects the 1HS customization. Toggle to 2HS, then verify the ordinary
   recipe accepts otherwise eligible plain copies and awards its usual 2HS item.
   Epic Forgemaster output remains the existing Ascended Fiery Defender identity.
9. On an isolated test character only, inject a stale saved-row preimage or a
   database failure. The session must reconnect without overwriting the saved
   result, losing the weapon, altering unrelated slots or retrying an uncertain
   UPDATE. After reconnect, inspect the authoritative saved grip.

These are acceptance steps, not completed native client observations. The earlier coordinated Bazaar authorization covered October26 only; this extension
is not yet deployed.
Passing source/build checks does not establish owner gameplay acceptance.
