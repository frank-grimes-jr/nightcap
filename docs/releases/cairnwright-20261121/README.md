# Cairnwright live server test

On November 21, 2026, main advanced from `ec3b22fe` to `cf536ec5`. OVH now runs the class 17 world and zone and the East Commonlands and Plane of Knowledge Chronicler scripts. The server added three spell records, two starter items, fifty class stat rows, one creation combination and one start location. The reviewed native world, zone and quest integration evidence is in the [Cairnwright QA record](../../qa/cairnwright-creation-20261121.md).

## Client and player testing

The regular launcher still serves signed release `2026112101`. The checked client candidate `2026112102` replaces `dinput8.dll` and `spells_us.txt` and preserves the other 146 signed file descriptors. The signing input is external to source. The candidate passed parent signature verification, exact RoF2 executable preflight and proxy/catalog pairing without signing or publishing. Client asset SHA-256 values are `ba6f5a24eb93e81c449a131656387f4bd8dae94e6f943cb8919d46f2b998613c` and `d67df84974b4bad55f0f4e18f37c12abcc61f1cf14e23f1725cb5a8f8f83feeb`, respectively.

Once the paired client is installed, enter the East Commonlands tunnel on a character with a free discipline slot. Leave two empty slots in the spellbook. Hail the Ancient Chronicler, select Cairnwright and confirm. Memorize Strike Cairn and Sound the Seam. Strike Cairn costs four mana. Move a few steps with an engaged enemy between you and the stone. Sound the Seam costs five mana. Camp and return, then verify access again. At the Chronicler, release the chosen slot, reconnect, and verify the spells lose cast eligibility and the other disciplines remain available. RoF2 character creation still offers the original 16 starting classes. Player acceptance and the mail-and-below change remain open.

## Production receipts

A player reported choosing Cairnwright and seeing repeated control messages in chat. A scoped live read confirmed a level-one Berserker in East Commonlands had Cairnwright in slot two and both starter spells scribed. This confirms live secondary adoption for that character. The recent world and zone logs contained no matching control-frame text. A native parser replay used synthetic identifiers and the same class and zone values. The released parser rejected the new class snapshot and passed its following AA messages to chat. The candidate consumed the snapshot, AA row and complete recommendation batch and displayed `BER/CRW/---`. Regression coverage is in `eq-client-dll/tests/ui-state.cpp`. Casting, release, relog and primary creation on the player's client remain unverified. The public guides already identify the pending launcher update.

| Check | Observed |
|---|---|
| World SHA-256 | `a641bef73c39fcc37192685bb077f1f5e9acf77dd4d79e7998ae899912eff521` |
| Zone SHA-256 | `771122fc9f8b208eb9338f82df3c614288582a8ae9f5bd19ed7ed4c1b5665989` |
| Game image | `sha256:e5e3a8b8f294d15d9b5dd6d99da9e603f086368a82bf90d4a82dd3e5eec32e84` |
| Stopped database backup SHA-256 | `bfd0590ac9d3e83c537129ec0a9fb5b32751ca724483565639eb23c647bbef05` |
| Startup | World, loginserver, UCS and 12 zone workers. Game and gateway healthy, zero game restarts at verification. |
| Production caches | 324,798 item records. IDs 998616 and 998636 contain the expected starter item names. Spell records 44381–44383 contain Strike Cairn, Sound the Seam and Seam Fracture. |
| Website | `20261121-cairnwright-v1` replaced `20261107-last-lantern-guide-v1`. All five files verified at the private origin. |
| Wiki | `20261121-cairnwright-v1` replaced `20261121-visible-ornaments-v1`. Multiclass, Features, Change Log and search changed. The other 627 files retained their hashes. |

Production uses a 2-damage Rusty Warhammer template. Local PEQ uses 4. The first temporary-table rehearsal rejected the difference. The corrected migration recognizes both preimages and sets a 6/30 starter hammer. First application and replay passed on temporary copies of the production content before activation. The release checked the three quest-file preimages, confirmed no ID collisions and required zero connected players before draining admission and taking the backup. Server-side deployment used `rollout.py` in the private OVH release directory `/opt/nightcap/releases/cairnwright-testing-20261121-v1`. Its activation receipt is terminal. Use the verify action for later inspection.

The public wiki package reproduced the preceding 631-file release before the four edits. Its update rehearsed rollback and verified the active origin. All 631 files also passed HTTPS hash checks and five private paths returned 404. The private guide returned 403 to the external check. The source refresh check reports historical drift from October 24. This release leaves that ledger open. [HTTPS verification](public-verification.json)
