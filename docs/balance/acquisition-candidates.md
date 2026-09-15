# Wider acquisition catalog

Captured 2026-09-12. Discovery evidence, not a certified full-BiS item pool.

`tools/balance/fixtures/classic-acquisition-20260912.json.gz` preserves 6,306
candidate item definitions, 27,567 merchant source rows, 21 global-loot definitions,
37 era-eligible global-loot entries, 8,663 enabled recipes with 67,271 entries,
and source text/hashes for 1,156 quest files containing reward references.
The adjacent manifest records the capture time and exact snapshot/query hashes.

The original v2 drop fixture remains unchanged. It captures unconditional,
unflagged Classic version-0 NPC drops and their generated gear tiers. The wider
catalog searches Classic and Plane of Knowledge quest/merchant sources, global
loot, and enabled recipes. Literal reward references are candidates only; dynamic
rewards remain unresolved. Same-path Lua scripts suppress Perl candidates, but the
discovery lexer does not establish NPC/script priority, event reachability, zone
version, quest prerequisites, or item acquisition. It is not a Perl/Lua interpreter.

Merchant records include NPC class, alternate currency, faction-list ID and primary
faction, plus complete inventory restrictions. A merchant-list row alone does not
prove that the NPC can be shopped. Native inventory checks can depend on birth
class, faction, buckets, status, level and probability. Recipe outputs likewise do
not prove that ingredients, containers, learning requirements or skills are available.

Human/agnostic wearable candidates cover the seven classes used by the three
diagnostic profiles. Required level must be at most 50; recommended level may
exceed 50. Augment rows can occur in the discovery pool and must not be treated as
ordinary worn items. No quest/merchant/crafted tier copies are automatically granted.
Epic IDs are included for explicit review, not certified acquisition or ownership.
The original capture omitted Orb of Mastery because the custom forge's Magician
mapping pointed to Staff of Elemental Mastery: Fire. Future captures explicitly
review the true orb, its proposed upgrade ID, the existing staff and its upgrade,
and the ornate exchange. This does not create missing item rows or grant gear.
See `acquisition-identity-audit.md` for the captured spell/quest chain and era limits.

## Findings that change gear selection

- The drop fixture already contains Band of Swirling Air and its generated tiers,
  sourced from level-72 A Legendary Behemoth in Steamfont. The ring is required
  level 0, recommended level 62, with 41% haste. The earlier additive optimizer
  excludes recommended levels above 50 and therefore misses it. Native controls
  now prove the level-50 scaling and full haste; see `gear-aa-encounters.md`.
  Source presence does not prove solo attainability of that level-72 encounter.
- Cloak of Flames (Ascended), from Nagafen, supplies 36% haste. Its haste does not
  stack with the ring. Both still need comparison against alternate slot choices.
- Ogog's Belt of the Four Winds reward is another 41% candidate. Its requirements
  include items 20976/20977/20978. The first two have captured ordinary Sky drops;
  Wind Tablet drops from script-spawned Bazzt Zzzt, outside the original ordinary
  spawn join. Torgon summons Ogog using a birth-class Warrior dialogue check.
  Full island access/spawn-chain and quest execution review remains open.
- Councilwoman Kerasha's high-stat reward cycle starts with Power of the Planes
  (16266), then permits exchanges among the ring, cord, mace and purse. Recipe 9921
  requires the four elemental essences and Sacred Bowl. The exchange cycle cannot
  establish acquisition of its own first item. These rewards remain unresolved
  until the ingredient, bowl and access chains are verified.

These findings rule out treating either the old drop-only additive score or all
rows in the expanded catalog as full BiS. The next gear search must account for
recommended-level scaling, weapon function, maximum worn haste, focus/procs,
item caps, acquisition constraints and the chosen encounter strategy.

## Reproduction

From `tools/balance/`, run:

```powershell
python acquisition_snapshot.py --quests E:/EQ_Local_Dev/akk-stack/server/quests --output fixtures/classic-acquisition-NEWDATE.json.gz
```

The collector uses read-only PEQ transactions and SQL over stdin, avoiding the
Windows command-line length limit. The recorded quest files are read from the
active quest tree. Five discovery/transport tests cover comments and quoted IDs,
unresolved dynamic calls, Lua precedence, zone scope and long read-only SQL.
