# Owner in-game QA after authorized paired activation

Candidate only. No live settings or binaries were changed by implementation.

1. **Ordinary low-level targets:** in public Unrest kill death beetles, in
   Permafrost kill ordinary goblins, in Upper Guk kill low-level frogs, and in
   Sol B kill kobolds. All regular static combat spawns should be eligible even
   below the old18/46 gates. Confirm names of any new drops: Haunted Hearthstone,
   Rimeheart Diamond, Bogmoss Emerald and Emberheart Garnet respectively.
2. **Lower Guk and Hate:** farm ordinary frogs below46 in Lower Guk and normal
   mobs in original Plane of Hate. Expected families: Ghoulheart Opal and
   Spiteglass Prism. Froglok Egg Capsule/Decayed Froglok Eye are older ordinary
   loot and are not evidence of this custom system.
3. **Grind and Raid:** enter each available mode through the relevant Dungeon
   Keeper, repeat regular-mob kills (including at least one named), and record
   zone, mode, NPC, kills and augment name/quality. The augment probability is
   the same0.5% in public, Grind and Raid; Raid statistics must not multiply it.
   Compare equipment drops separately: their old gates remain.
4. **Hate B:** in an authorized available zone186 public/Grind/Raid environment,
   verify a natural Blackspire Prism family drop. The separately prepared
   layout/entry release must be active before testing its new Keeper route;
   this change alone adds no travel route. Do not accept Spiteglass Prism as
   proof of correct186 mapping. Old76 runs must still yield Spiteglass.
5. **Day/night and excluded actors:** Kithicor regular daytime combat mobs may
   now roll augments; equipment still requires its old eligible nighttime undead.
   Services, pets, charmed victims and temporary encounter adds must not award
   augments. Test on an isolated QA server; do not attack live service NPCs.
6. **Death/recovery:** leave a natural augmented corpse, zone out/in and perform
   a supported instance unload/reload. The existing corpse's loot persists
   without rerolling/duplication. A living restored mob and a new Grind respawn
   each remain eligible when they later die. Verify normal Raid objective,
   corpse/loot claiming and exactly-once boss reward behavior.
7. **Item and balance:** socket/equip only at required level, trade, forge3 Base
   or4 higher-quality copies, loot through Advanced Loot, and relog. Existing
   stats/sockets/caps stay unchanged. Record clear time and rewards per eligible
   kill across solo/multiclass builds; confirm the broader supply is acceptable.

Random absence is not a deterministic failure: at0.5%,200 eligible kills still
have about36.7% chance of no augment;600 have about4.94%. Native exhaustive tests
prove probability boundaries. In-game QA proves end-to-end materialization and
recovery, not a guaranteed drop within any fixed number of kills.
