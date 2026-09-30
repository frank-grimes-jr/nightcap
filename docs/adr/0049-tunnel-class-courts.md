# 0049: Tunnel class courts

Date: 2026-09-30. Status: accepted for the candidate; owner visual QA pending.

The owner requested intentional placement, familiar races, matching class
uniforms, Roman stock-page numerals and a wizard companion to Khalure. The live
roster has sixteen class merchants, sixteen trainers and twenty-two suppliers.
The class vendors use races 407/411/417/419; trainer/supplier templates cycle
unrelated races and outfits.

Use eight separated courts around the chamber perimeter. Each class retains its
adjacent trainer and merchant, matching race, material, size and color with gender
variation. Familiar Classic playable races are a design choice, not a claim of
measured popularity. Suppliers also share profession outfits. Stock, merchant
IDs, trainer classes, prices and progression remain unchanged.

Khalure gains `Druid Rings`. Male Dark Elf wizard Khaleid gains `Wizard Spires`
and the display material/color of Carmine Robe (1226) and Blue Crystal Staff
(14337); no loot/item instances are created. Both occupy the verified northwest
travel area. The prior row placed Khalure at database X=-1506,Y=-185, outside
the chamber mapped by the native geometry; only his placement changes here.

Alternatives: one race/outfit for everyone would erase useful class identity;
dense central schools obscure circulation; custom wall signs need client object
meshes/materials and signed asset packaging. A texture alone cannot attach itself
to the world. The stock ecommons object archive has no class-sign actors. Blender
MCP was disconnected and Unity tools were not exposed. Use uniforms/subtitles
for this release; signage remains an optional client-art follow-up.

Guard SQL against exact preimages and reference collisions. Clear only
unambiguous affected instance-zero NPC states; recapture before recovery after
zone activity. Geometry checks include DB furniture, patrols and approach rays,
not just ground. Khaleid's eight normal Classic destinations exclude planes and
future expansions. [Candidate and QA](../releases/tunnel-class-courts/README.md).
