# PoK arrival hub: activation and in-game QA

Deployed September 15, 2026 as part of the combined server/AA/hub release.
Owner in-game acceptance remains pending.

## Operator state and future deployment

The hub is active. Use the [combined deployment/rollback runbook](../releases/live-qa-20260915/README.md)
for matching world/zone binaries, the merged class plugin, SQL guards, shared
memory and scoped saved-NPC-state handling. The original isolated content
activation procedure is superseded: restoring its old plugin alone would break
the paired AA release contract. Do not replay captured SQL or cached-state IDs
against later gameplay without reviewing fresh preimages.

## Player checks — normal account, current RoF2 client

Use disposable characters for class changes. Do not spend or refund a main
character's AAs to test this UI. Test native AA persistence/refunds separately
using the [combined checklist](../releases/live-qa-20260915/QA.md).

1. **Arrival and walking:** enter PoK normally. Arrival is approximately
   x=-285, y=-148, z=-159. Walk between both merchant rows, through the center,
   around the guide, and to all five utility NPCs. Confirm nobody floats,
   sinks, overlaps a wall, blocks an arrival/door/path, or requires standing
   inside another NPC. Check target line of sight and facing from both sides.
   Positions are provisional until this passes; capture exact corrections.
2. **Find window and labels:** locate the Ancient Chronicler, all 16 class
   merchants, bags, both blessing services, Epic Ascension, and Waypoint Travel
   through Find. Confirm spell/song/tome labels match `hub-layout.md`. The old
   Loremaster and II/cont. shops should no longer spawn at the former location.
3. **Class status:** on a character with no secondary classes, log in, hail the
   Chronicler, type `#classes`, then `/say !classes`. Each shows Primary plus
   explicit empty Second and Third slots. Repeat with one and two selected
   secondary classes; status should agree with the saved character after relog.
   Check unrelated player commands still work.
4. **Selection:** on a disposable Warrior, preview Cleric. Preview changes
   nothing. Open confirmation and choose No; slots remain unchanged. Repeat
   and choose Yes; Second now says Cleric immediately. `#classes` agrees.
   Select Wizard as Third and confirm. Duplicate choices and attempts to add
   a fourth class must not change the selected classes. Camp to character
   selection and return; all three classes persist.
5. **Release UI:** only on the disposable zero-AA character, cancel a release
   and verify no change. Confirm releasing Second; Wizard promotes to Second
   and Third becomes empty. Hail/status/relog must agree. Native AA refunds,
   failed class-write behavior, and paid-AA release are not certified here.
6. **Shopping:** open every class shop. Counts at level cap 50 are in
   `hub-layout.md` (3–275 items each, 1,747 total listings, 1,229 unique items).
   Warrior/Monk/Rogue/Berserker stock contains tomes; Bard contains songs.
   Cleric and Wizard spells appear at their respective shops. Shared spells
   may appear on several appropriate class shops. No generic II shop is needed.
7. **Prices and learning:** compare displayed prices on the same character
   against pre-activation samples; charisma/client pricing may affect the
   displayed amount. Buy representative eligible spell/song/tome items using
   disposable characters with the matching selected class. Verify scribing,
   memorizing/training, and use subject to their level and current client UI.
   A melee-primary caster test requires the already established client patch;
   this change does not introduce a new client capability patch.
8. **Utilities:** verify bags, blessings, premium blessings, epic quest hails,
   and waypoint dialogue still open with the same costs and prerequisites.
   Five identical Forgemaster spawns were consolidated into one; confirm one
   quest response, no missing service, and no repeated NPC overlap.

## Rollback and limitations

Follow the combined rollback runbook linked above, preserving the matching
binary/plugin pair. Hub rollback restores exact captured content and refuses
unexpected later NPC, stock, price or era changes. Cached NPC state requires
separate reconciliation after later gameplay; never restore stale state blindly.

The current inventory policy preserves the already stocked pool at expansion 0,
with original class levels up to 50. It does not certify each spell's original
expansion availability. Later releases require a reviewed expanded catalog;
both era preflight and restock refuse to silently invent that pool. Caps below
50 filter by original class level; caps above 50 require review.

The class plugin still performs the existing global spell-access widening and
requires a camp for all client state to refresh. Client spell-data synchronization
remains an operator procedure with the client closed; it is no longer printed as
a script command in player dialogue. This change improves status and navigation;
class-change transactions and AA lifecycle acceptance require the combined QA.
