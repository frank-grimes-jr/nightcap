# Exact in-game QA — not yet run

Use an authorized paired test release. Automated checks and a built binary are
not evidence that these player actions passed. Record character/build/gear,
zone, run UUID, mode, time, result and relevant logs for every failure. The seven
old zones' prior acceptance does not establish the fourteen new zones.

## All21 zones, both modes

| Zone | Keeper NPC | Keeper /loc (Y,X,Z) | Reward band | Grind/Raid journal |
|---|---:|---|---:|---|
| befallen | 999227 | `-67,35,3.1` | 20 | 9700/9701 |
| unrest | 999228 | `-38,67,3.1` | 30 | 9702/9703 |
| highkeep | 999229 | `-16,88,4` | 40 | 9704/9705 |
| najena | 999230 | `-61,858,4.1` | 30 | 9706/9707 |
| cazicthule | 999231 | `71,-74,4` | 40 | 9708/9709 |
| permafrost | 999232 | `-121,46,2.1` | 50 | 9710/9711 |
| soldungb | 999233 | `-424,-248,-108` | 50 | 9712/9713 |
| blackburrow | 998800 | `-159,23,2.0` | 20 | 9714/9715 |
| crushbone | 998801 | `-644,174,2.0` | 20 | 9716/9717 |
| runnyeye | 998802 | `106,201,3.0` | 30 | 9718/9719 |
| soldunga | 998803 | `-487.312,-474.688,71.969` | 40 | 9720/9721 |
| guktop | 998804 | `-36,23,2.0` | 30 | 9722/9723 |
| gukbottom | 998805 | `1197,-201,-81.969` | 50 | 9724/9725 |
| mistmoore | 998806 | `-314,120,-179.938` | 40 | 9726/9727 |
| kedge | 998807 | `100,30,301.875` | 50 | 9728/9729 |
| paw | 998808 | `-106,63,2.0` | 40 | 9730/9731 |
| hole | 998809 | `624,-1050,-78.969` | 50 | 9732/9733 |
| qcat | 998810 | `860,96,-39.969` | 20 | 9734/9735 |
| fearplane | 998811 | `-1139,1298,-0.371` | 50 | 9736/9737 |
| hateplane | 998812 | `-374.8,-337.08,2.0` | 50 | 9738/9739 |
| airplane | 998813 | `1415,630,-666.709` | 50 | 9740/9741 |

For **each table row**, perform both a fresh Grind run and a fresh Raid run:

1. Travel to the base-zone entrance. Target/hail the eye (`/target Instance_Keeper`
   if necessary). Verify separated, visible, reachable placement and all seven
   choices: Raid, Grind, Enter, Join, Status, Claim Rewards, Reset. No schema,
   content or item-cache mismatch should appear.
2. Select the desired mode, then Enter. Confirm a new private instance, correct
   mode, fixed 12-hour deadline and complete visible objective list. Hail inside.
   Re-enter/relog and confirm the same run, deadline and journal.
3. Have a second group member Join. Confirm same instance and six-player maximum;
   an outsider and a distant/non-enrolled character must not gain credit. Test a
   player-owned pet kill and 200-unit encounter-credit boundary on representative
   zones. Kill every catalog objective; Status and each personal journal agree.
4. Raid: confirm stronger combat, no defeated-spawn respawn, final locked until
   all required minibosses die, and final quantity/quality rolls. Grind: confirm
   normal stats, respawn and catch-up credit. Do not treat GM kills as balance QA.
5. Claim after a personal full clear. Exactly one earned personal reward persists
   through relog; repeat Claim cannot duplicate it. Added-zone finals use the
   existing shared saber/signet/satchel families for that band. Original seven
   retain exclusive families. Exercise full-inventory recovery in a test run.
6. Reset: non-owner rejected; owner must confirm; occupied, pending-transfer or
   recoverable-player-corpse runs cannot reset. After safe reset or expiry, earned
   claims/history remain and the next run has a new UUID. Use existing lifecycle
   tests rather than altering a live clock or deleting player records.

## Plane-specific acceptance

- **Sky:** traverse the actual island doors in both modes. Keep the same instance
  on every port; exchange20920–20927 for20911–20918, retaining the separately sold
 20919 key. Each of the seven canonical Sirran copies must be reachable and
  continue exchanging tokens after 20 minutes and a supported runtime restart.
  Client/pet attacks, charm, fear and NPC combat must not remove a key service.
- Visit Keeper of Souls after 30 minutes; he remains. Donate10 gold to the
  princess; she remains an eligible objective and repeated donations do not
  duplicate Gkzzallk. Kill Spiroc Lord before vanquisher/guardian: key access
  remains, while Raid never respawns the killed Lord. Bazzt stands on the island.
- With a second simultaneous Sky run and public Sky active, verify independent
  stage dialogue and key services. Complete the miniboss list before Eye of
  Veeshan unlocks. No script callback creates duplicate canonical bosses.
- **Restart:** on the test environment, exercise graceful unload and abrupt
  interruption immediately after a Sky objective death. The native death ledger,
  earned credit and corpse receipts persist, Raid boss stays dead, and all seven
  Sirran services reconstruct even when no dynamic-Sirran checkpoint exists.
- **Fear:** keep an observer in public instance0 while spawning/killing managed
  Cazic-Thule. Public population/conditions remain unchanged. Repeat with two
  managed runs. Hate and Fear objectives and loot must remain in their own run.

## Regression and balance gates

Preserve an original-seven run across the paired upgrade: UUID, mode, deadline,
credits, pending reward and completed journal remain exact. Confirm an unmanaged
legacy instance still uses its old flow. Cazic-Thule's private188-point population
and public doors/population remain unchanged. Test ordinary public Sky quest
timers/key exchanges and public Fear repop behavior separately.

Measure representative level 50 solo builds and progression gear against planes,
Vox/Nagafen and the added final encounters. Record legal multiclass/AA pool,
actual spent AA, pets/buffs, duration, incoming/outgoing damage and resource
pressure. No HP or spell-cap tuning is included; demanding solo/small-group
balance remains an explicit promotion gate. Current native Hole encounters are
intentional in this candidate; no historical population restoration is claimed.

Main promotion, production activation and public wiki publication remain pending
the applicable owner authorization. Record acceptance by scenario, not a blanket
claim based on a successful menu hail.
