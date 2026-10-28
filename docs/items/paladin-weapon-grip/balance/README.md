# Paladin weapon progression — October 28 candidate

Implemented and tested locally; **not deployed or published**. The owner approved
the assessed weapon package, direct Ascended Fiery Defender and removal of its
extra payment requirement. Monk AAs are unchanged. This supersedes the rejected
October 27 numerical profiles and the earlier separate-Paladin-forge plan.

## Effective owned weapon profiles

| Weapon | ID | 1HS | 2HS | Accuracy | Added shield block |
|---|---:|---:|---:|---:|---:|
| SoulFire | 5504 | 13/30 | 23/45 | 4 | 0 |
| Polished SoulFire | 205504 | 18/30 | 31/45 | 6 | 0 |
| Exalted SoulFire | 405504 | 22/30 | 38/45 | 8 | 0 |
| Ascended SoulFire | 605504 | 26/30 | 46/45 | 10 | 0 |
| Fiery Avenger | 11050 | 15/30 | 33/44 | 5 | 0 |
| Polished Fiery Avenger | 211050 | 20/30 | 44/44 | 8 | 0 |
| Exalted Fiery Avenger | 411050 | 25/30 | 55/44 | 12 | 1 |
| Ascended Fiery Avenger | 611050 | 30/30 | 66/44 | 15 | 1 |
| Fiery Defender | 10099 | 32/30 | 64/40 | 20 | 2 |
| Ascended Fiery Defender | 810099 | 36/30 | 72/40 | 25 | 3 |

Accuracy applies in either grip through normal item caps. Shield block adds the
listed percentage points only to clients with the supported primary weapon in
1HS and an eligible secondary shield; both items must meet held-class/race/deity
and required-level checks. Native frontal/rear permissions and strikethrough
remain. It is not the Shielding stat. Bonuses recompute without accumulation.
No Avoidance, Shielding, haste, strikethrough or Monk-AA changes were introduced.

Normal Defender now has Mana 50, STR/WIS 30, heroic STR/WIS 8, Healing Amount 30,
Spell Damage 15 and proc level 45. Ascended Defender gains heroic WIS 10,
Healing Amount 35 and proc level 45; its existing AC 30, HP 168, Mana 72,
STR 40/WIS 30, heroic STR 10 and Spell Damage 20 remain. Other stats are retained.
Ascended Defender's raw ratio is 20% above Ascended Avenger in either grip;
support stats do not fall below Avenger. Ratios are not whole-build DPS promises.

## Quest and legacy-owner transition

Paw v0 and South Karana Brother Hayle award 605504; Inte Akera awards 611050;
Fear's Irak Altil awards 810099 for Mark of Atonement and any supported Avenger
quality. Ingredients, faction, XP, branch behavior and era availability remain.
The later Halls of Honor Irak predicate also recognizes 810099.

Other classes retain their paid Epic Forgemaster recipe. Paladins no longer
pay eight Essences or 100,000 platinum. Existing normal Defender owners can
place one in a top-level inventory slot and say **ascend fiery defender** to
the Epic Forgemaster in East Commonlands or Plane of Knowledge. This exchanges
one copy free; it does not require Paladin to be the original starting class.
The sword stays in inventory; do not hand over the sword or payment.

The native exchange copies the owned instance and atomically changes only the
saved item ID 10099→810099 after checking character/slot/GUID/charges/color/binding,
all six augment IDs, metadata and ornaments. Grip, charges, augments, GUID,
binding, color and ornaments persist. No delete/summon, currency debit, mass
inventory rewrite or player snapshot restore. Replays find no eligible old copy.
Customized/evolving/scaling items and incompatible socket fits are refused.
Uncertain writes or publication failures quarantine the session for reload.
Paladin payment hand-ins call native ReturnHandinItems, returning instances and
all four currencies. Other classes' original payment handlers are unchanged.

## Implementation and proof

`common/paladin_weapon_grip.h` and `ItemInstance::RefreshPaladinWeaponGrip` own
absolute projections; `zone/bonuses.cpp` owns conditional block.
`Client::AscendPaladinEpic` in inventory.cpp is bound in perl_client.cpp.
No ItemData layout, rule, spell or content-SQL migration is needed. Raw SQL/base
links and generated public catalogs retain old definitions; owning guidance
states effective candidate values separately. A later publication must retain
this distinction, not label raw catalog rows as updated item definitions.

Five grip/native groups (including session-local MariaDB exchange and toggle
preimage/replay controls), three progression groups, five Lua 5.1 quest groups,
three preflight groups, four Bazaar groups and two native hand-in/task groups
and sixteen Perl forge assertions pass. Extracted native functions use bounded API fixtures; these are not live
client acceptance. The isolated native relink builds the four changed translation
units and links zone/world/shared_memory with retained unchanged object inputs.
See progression/native-build-manifest.json, verification.json and review.md.
The Perl binding lives inside libperl_zone.a's generated unity member. The final
relink replaces that member and verifies both native exchange and Perl binding
symbols in the zone binary; compiling a loose perl_client object alone is insufficient.

The prior Palwar/Vox and Wu/Steel experiments remain diagnostic evidence for the
assessed package. They used fixture overrides, not these new production functions.
They do not certify all eras/builds or the exact value of each added stat.

## Release, rollback and owner QA

This package needs the matching same-ID RoF2 repair (proxy 0.13.1 candidate) and
the paired server binaries plus seven quest scripts. Use a fresh approved
read-only capture and `tools/paladin_grip_preflight.py`; it verifies original
SQL values separately from projected stats, quest/helper preimages and precedence.
Never substitute the historical capture at release; freshness is limited to one hour.
Use the supported whole-game restart, regenerate the paired item cache, and sign
and publish the matching client. Quest/rule reload alone is insufficient.

Hold or revert acquisition on rollback; preserve earned Ascended items, grip
metadata and subsequent activity. Never restore an old player inventory snapshot.
Keep grip-aware binaries and client paired; old client caching is a known failure.

After authorized deployment: complete each quest with faction/ingredients;
verify the new IDs and 1H/2H values, shield equip, accuracy, block eligibility,
proc level 45, and saved stats after relog/zone/Bazaar. Test both legacy grips,
six augment sockets, charges, color, binding and ornaments through the free
exchange; verify mixed currency/item returns exactly once and other classes'
unchanged paid route. Repeat encounter checks without treating the Monk-heavy
Vox pilot as a complete balance certification. Public publication and owner
gameplay acceptance remain pending.
