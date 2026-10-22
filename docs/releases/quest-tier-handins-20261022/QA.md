# Exact owner QA â€” quest item qualities

Status: pending; run against the paired deployed zone and seven quest files.
Provision test items on a disposable test character, then perform ordinary NPC
trades. Keep before/after inventory and task screenshots. Do not infer live
activation from source promotion to test.

1. **Crafted Gauntlets, Shakrn Meadowgreen, South Karana (`southkarana`, NPC
   14075).** Give Aviak Charm (Polished) **213737** and two Star Rubies **10032**
   in separate trade slots. With the deployed class-armor reward policy, expect
   exactly one Crafted Gauntlets (Ascended) **604178**, the
   ordinary quest EXP, and no returned ingredients. Repeat independently with
   Normal **13737**, Exalted **413737**, Ascended **613737**. All award the same
   configured quest reward; no bonus reward. The historical captured Normal **4178** fixture is not the current live reward.
2. **Rejected and excess items at Shakrn.** Give Polished charm with only one
   ruby: expect no reward and both original items returned. Give a complete set
   plus an unrelated fourth-slot item: expect one reward and that exact extra
   returned with its charges/binding/custom data. Give both Normal and Polished
   charms plus two rubies: consume Normal, return Polished. Repeat a rejected
   trade, zone and relog; confirm no disappearance, duplication or quality loss.
3. **Legacy Perl quests, Temple of Solusek Ro (`soltemple`).** Gardern: Heart of
   Fire **10548**, Heart of Frost **10549**, Polished Rod of Bone **210550** and
   Polished Darkwood Staff **206048** -> Staff of Temperate Flux **6342**.
   Sultin: Dull Ruby **10087** plus Polished Golden Rod **206337** -> Rod of
   Insidious Glamour **6329**. Vurgo: A Fungus Eye **10538**, Fire Opal **10031**,
   Polished Shadowed Knife **207331**, Polished Shadowed Scythe **205103** ->
   Harvester **5316**. Confirm each NPC hails after script installation.
4. **Other migrated recipes.** Joyce: Fire Goblin Skin **202361**, Frost Goblin
   Skin **402362**, spell scroll **15109**, Twice-Woven Cloak **602360** -> Robe
   of the Elements **1356**. Vilissia: Glowing Mask **202352**, Patch of Shadow
   **402368**, **10558**, Bonechipped Mask **602367** -> Acumen Mask **2366**.
   Leave out one ingredient, retry, then complete; missing trades return intact
   and complete trades give one reward. Relog and verify retained extras.
5. **Native quantity/multiquest and journal delivery.** In an isolated test
   quest, require Normal **13737 x2** and accept **213737 + 413737** once. Require
   both **13737 x1** and explicit **213737 x1**: one Polished alone must fail;
   Normal+Polished must pass. Add a one-platinum requirement, omit money, and
   confirm both items return. For an explicitly enabled multiquest, split charm
   and gems across two trades and confirm only one completion. Use an isolated
   Deliver objective for Normal **13737** at NPC 14075 in zone 14: each ordinary
   quality credits the required count only; wrong NPC, wrong zone, inactive
   objective, wrong family and +800000 identity must not credit it.
6. **Quality-specific controls.** Existing Reforging Box/forge costs and explicit
   quality requirements remain exact; unrelated hunt/dungeon/epic items do not
   satisfy an ordinary quest ingredient. Unchanged Lua scripts still expect
   duplicate ingredients in separate trade slots unless they explicitly support
   stacks. No client patch should be required.

7. **Kurron Ni, Overthere, later-era isolated QA only.** Give Darkforge Helm
   **3140**, Breastplate **3141**, Greaves **3145**, using any mix of Normal or
   +200000/+400000/+600000 versions, plus **900 platinum**. Expect +7 Truespirit
   and one Letter to Duriek **18099** on the NPC per spawn. All submitted coins
   return exactly once, preserving the class-armor release's reviewed policy.
   Repeat with **901pp + 1gp + 2sp + 3cp**, and verify the exact full refund once.
   Missing/wrong pieces, **899pp**, or equivalent gold without 900pp must fail;
   native returns retain original items/coins. A second complete set on the same
   spawn may grant faction but no duplicate letter. This does not unlock Kunark.
