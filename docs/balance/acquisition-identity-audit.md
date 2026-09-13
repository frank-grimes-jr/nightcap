# Acquisition and AA identity audit

Read-only follow-up to the 2026-09-12 baseline. Exact capture time, SQL, result rows
and quest text/hashes are in `acquisition-identity-audit.json`; native source
hashes and relevant excerpts are in `acquisition-native-excerpts.json`.
No live content, binaries or AA access changed.

## Behemoth gear remains conditional

Live content confirms A Legendary Behemoth 56182 at spawn 137415 in Steamfont
version 0, unconditional, enabled and without an expansion minimum. Its native
definition has level 72, 400,000 HP, AC 519 and damage 400–1,404. The frozen drop
catalog ties several selected accessories, including Band of Swirling Air, to it.
Those items are present in Classic content; this does not establish that a
level-50 solo character can earn them before the dragon baseline.

The isolated clone's `native-clone-manifest.json` lists `spawnentry` but not
`spawn2` among copied content tables. Its missing spawn join therefore cannot
prove this live NPC is absent. Use the captured live source evidence for
acquisition, and the clone for its documented combat purpose.

Retain existing fights as conditional gear measurements. A certified baseline
needs either a demonstrated Behemoth acquisition path or a separately measured
gear set excluding its rewards. NPC level alone is not an attainability test.

## Magician epic identity and expansion dependencies

| Item | Captured behavior |
| --- | --- |
| 11566 / 811566 | Staff of Elemental Mastery: Fire / current Ascended staff; Mage class mask 4096, focus 4401. These are the custom forge's current Magician targets. |
| 14341 / 814341 | Staff of the Four / Ascended version; Wizard class mask 2048. They are not Magician epics. |
| 28034 | Orb of Mastery; Mage class mask 4096, click 1936, click level 50. |
| 828034 | No item row in the targeted live query; cannot equip a hypothetical Ascended orb. |
| 55273 | Ornate Orb of Mastery; exchange script consumes 28034, but this item has no click or pet focus. It is not an equivalent epic-pet substitute. |

The final Sky quest gives scroll 19436, not item 28034 directly. That scroll
scribes Summon Orb 1944 (Mage level 45), whose native SummonItem effect 32 creates
28034. The orb clicks Manifest Elements 1936, native SummonPet effect 33 with
pet type `SumMageMultiElement` (NPC 598). Its spell class level is 59 while its
item click level is 50. Native item-click eligibility and pet behavior need an
explicit control; spell memorization rules cannot stand in for click validation.

The final hand-in requires elements 28032, 28009, 28006 and 28033. Captured scripts
award Earth in Firiona Vie and Fire in Skyfire; both zones are expansion 1 and
have bypass disabled. Water is in Cauldron and Wind in Sky. Consequently the
observed standard chain is not a demonstrated Classic acquisition route, even
though its final reward NPC is in a Classic zone. An alternate custom source
would need explicit evidence. Quest presence alone does not prove spawn priority,
access or successful hand-in.

The discovery collector now reviews the real orb and the legacy forge targets
separately, including the ornate exchange. The frozen original capture is unchanged.
Changing the forge and generating new epic rows are separate gameplay changes
requiring their own migration, tests and in-game QA; no such correction is deployed.

## Ancient Attunement is not a verified travel AA

Live spell 99001 uses effect 33 with `teleport_zone=poknowledge`. Native constants
and the handler establish that 33 is SummonPet, 32 is SummonItem, 26 is Gate, and
83 is Teleport. `teleport_zone` is also a pet-type field; a nonempty value does not
identify a travel spell. No `poknowledge` pet definition exists in the targeted query.

The setup SQL `eq-solo-gm/scripts/pok_attunement_setup.sql` selects the first
positive effect from any row with a nonempty `teleport_zone`. That query can choose
a pet spell and explains the observed wrong effect. The earlier AA-pool document's
claim of a confirmed PoK gate has been corrected. A repair must use verified
native travel semantics and coordinates, then test activation with and without
pets; changing a label or choosing another arbitrary populated row is insufficient.

This AA was included as a free purchase but never activated by the combat
controllers. The 108 shared-pool fights and their purchase evidence remain valid;
they do not validate recall. Utility AAs need behavioral review alongside offensive
and defensive AAs before the expansion offering is finalized.

## Validation and next evidence

The acquisition regression confirms that the scroll's indirect wearable reward
is reviewed without classifying the Wizard staff as Magician gear or inventing
an Ascended ornate orb. Run `python -m unittest tests.test_acquisition` from
`tools/balance`. All six acquisition tests and the full 230-test suite pass.
Embedded quest hashes, JSON structure and the captured key findings were checked.
Targeted SQL is embedded in the audit and can be reissued through
`baseline.query_json`; re-captures should use new files rather than overwrite
dated evidence. Native excerpts identify their full source hashes.

Next: measure a source-constrained gear alternative and review the remaining
quest/craft/global-loot challengers. Final balance still requires the legal AA
pool, obtainable gear, representative strategies and explicit in-game QA.
