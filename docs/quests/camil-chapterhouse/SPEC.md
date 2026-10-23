# The Vigil of the Dawn — Chapterhouse

2026-10-23. Implemented on feature/camil-chapterhouse, based on main
5d0a0d31bd1b8c07ca1df3cc620d323c0c07f175. Promoted to main c0c9896e and deployed
October23 for live testing. **Owner gameplay acceptance remains open.**
[Delivery evidence](deployment/README.md).
The owner selected Chapterhouse, native Tasks, challenging level-50 encounters,
era-safe loot, custom miniboss items, a zone augment, waypoint and Instance Keeper.
The accepted difficulty target is demanding even at maximum legal power: this
is a level-50 endgame capstone, not a fresh-50 progression step.

## Player route

Camil Silvermist (999521, East Commonlands) offers The Vigil of the Dawn to a
level-50 character holding Paladin in any class slot. His social behavior remains.
Accept before creating a run. Keeper 998820 near Befallen in West Commonlands
opens a 12-hour Raid or Grind run. Helpers need level 50; personal campaign
credit requires an eligible enrolled Paladin. Existing six-person limits apply.

| Tasks objective | Encounter or action |
|---|---|
| Enter the expedition | Managed Chapterhouse run, zone 760 |
| Defeat Vicar Sered | Bell every 15 seconds, three-second warning; Classic Stun 216 within 30 units. Interrupt or escape. |
| Read three memorials | Separate counters before Sister Elowen |
| Protect Elowen | Three waves of two shades, at least 15 seconds between starts. Guardian death, absent living participants or five-minute timeout resets the attempt. Retry at Elowen. |
| Defeat Warden Halvyr | Two shades at half health; encounter-owned cleanup on wipe/death |
| Release three knights | Mercy, Courage and Resolve, separate counters |
| Defeat Sir Vaelen | Three-second ash brand: move more than ten units from the marked position or interrupt; 18-second cadence |
| Defeat the Unbroken Shadow | 5% flurry and a three-second ash brand every 12 seconds; Raid requires all minibosses first |
| Reconsecrate the altar | Final story interaction |
| Return to Camil | Claim existing Winged Helm of the Dawn, item 990500, once |

The implemented ending is Vaelen, Shadow, then altar. The proposed second
spirit-defense sequence is superseded; Elowen is the dedicated defense. Camil
led civilians to safety; Vaelen bound the fallen Order of the First Dawn to its
armor. These are original Nightcap characters, not claims about EQ canon.

## Durable journal and credit

Task 9800 has 14 explicit activities and ordered chapters. Dungeon journals
9742/9743 separately track four bosses. The native character ledger owns
progress; abandoning Tasks does not reset it. Reconnects and service interactions
restore the display. Capacity is checked before acceptance and entry, including
an earned helmet entitlement whose delivery is pending.

Credit uses the existing run UUID, allocation generation, enrollment and nearby
party participation, including owned-pet attribution. Dead players receive no
campaign credit. First acceptance during an existing run is refused. Previously
earned personal kills in a valid campaign run reconcile when their prerequisite
story interaction completes; another character's or the run-wide checklist's
kills cannot substitute. Earned chapters survive expiry/reset; defense attempts do not.

The final display row never grants ordinary task rewards. Camil persists a
unique helmet entitlement and uses the native atomic inventory receipt adapter.
Full inventory retains the claim. Completed history requires the owned delivery
receipt; the active task is removed only after history succeeds. Repeated claims
cannot duplicate the helm. Pausing expeditions preserves earned claims. Helmet
stats/sockets are unchanged; production-helmet.json is a dated read-only probe.

## Population and economy

There are 35 private static spawns: four bosses, 21 trash, Keeper, waypoint and
eight story services. Dynamic shades/guardian are separate. Original Rain of
Fear NPCs, spells and loot are not reused. Custom combat NPCs have no stock or
global loot, merchant, stock spell list or regeneration. Dynamic adds award no XP/loot.

| Boss | Level | Grind HP | Base hit range |
|---|---:|---:|---:|
| Vicar Sered | 50 | 250,000 | 450–1,100 |
| Warden Halvyr | 51 | 325,000 | 500–1,250 |
| Sir Vaelen | 52 | 400,000 | 575–1,400 |
| Unbroken Shadow | 53 | 480,000 | 650–1,550 |

Bosses have two attacks, delay 20, ATK 300/325/350/375. Raid retains 135% HP /
115% post-calculation damage and permanent deaths; Grind respawns. Trash is
level 46/48, HP 22,000/28,000. Dynamic shades have HP 30,000, hits 175–400;
Elowen’s guardian has HP 10,000. Vaelen/Shadow use Classic Wrath 329 with
authored spellscale 1200/1500 for the warned brand. All combat bodies remain
undead and stunnable; no immunity suppresses Slay Undead or Ghoulbane.

[Calibration](BALANCE.md) covers 48 current-content native runs at 3,319 legal
purchased AAs, including Ghoulbane and Instrument of Nife. All completed; final
Raid fights took 129–151 seconds before scripted mechanics. Values remain
candidates; full encounter execution and other strong builds require [QA](QA.md).

Each miniboss has a 35% custom drop: Sered's Memorial Chain 961010, Halvyr's
Unbroken Mantle 961011, Vaelen's Last Oath 961012. They use existing level-50
Polished budgets. Final Raid exclusives append six variants 960414–960419;
previous 414 reward identities and shared completion policy remain unchanged.

Static curated combat NPCs have a 0.5% Ember of the First Dawn augment roll,
Base/Polished/Exalted/Ascended weights 60/30/8/2, IDs 961000–961003. HP/mana
60/87/114/144; heroic STA/WIS 5/6/8/10; AC 2/3/5/6. Type 22, six armor slots,
required level 50, MAGIC, no effects, zero resale. Existing Hunt headroom and
three/four-copy zone forging apply. This adds no socket to Camil's helm.

## Access and isolation

era.json references config/chapterhouse-access.json. Global Classic and cap 50
remain. Only zone 760 bypasses expansion checking; it stays tagged expansion 19,
requires level 50 and prohibits binding. Generic era apply validates the declaration;
the guarded paired content migration installs it, initially campaign-disabled.

Public Chapterhouse is a service foyer. Stock spawns require a disabled content
flag; managed instances clear native spawns and load only the curated population.
Outward doors/zonepoints return to Classic commons. Scoped later-era ground items,
forage/fishing, objects and traps are removed. The installer refuses public saved
living spawns; back up and invalidate only those rows, preserving player corpses
and other instances. Waypoint recall lands in the public foyer; Keeper controls
run admission and never falls back to legacy allocation. Exact NPC-ID scripts
avoid shadowing global Keeper/waypoint scripts with a zone default.

## Verification and operational boundaries

- Authored data: tools/chapterhouse_content.py and chapterhouse_migration.py.
- Native state/credit/journal/receipts: chapterhouse_vigil.inc and dungeon_service.cpp.
- Exact-ID scripts: quests/chapterhouse/ and ecommons/999521.pl.
- Tests: tools/tests/test_chapterhouse*.py plus dungeon, Hunt and receipt regressions.
- rehearsal.json pins the successful migration hash and real SQL failure checks.
- authored-geometry.json checks 40 points against native map floor/headroom.
  It does not establish visible client placement or full navigation.
- native-build-manifest.json pins paired binaries and complete source. Compare
  current inputs before claiming a final-source build.
- capstone-results.json and BALANCE.md record current native arena calibration;
  superseded preliminary data is compressed and labeled. The arena excludes quest Perl,
  Chapterhouse paths and real player execution. Do not call it accepted balance.
- [Runbook](RUNBOOK.md) records install/reload/rollback and local test incidents.
  [QA](QA.md) specifies owner acceptance. Wiki changes retain candidate labels;
  neither gameplay nor public wiki publication is claimed.
