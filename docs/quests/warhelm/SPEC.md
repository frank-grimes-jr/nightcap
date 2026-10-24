# The Ashen Compact

Candidate implementation, 2026-10-24. Not deployed or accepted in game.

The owner rejected the Commonlands entrance and selected Everfrost's hidden
pathway immediately before Permafrost. The candidate now places Drazhul at
server XYZ (-6974, 2158, -61.0625) and the Keeper/return at
(-6974, 2174, -61.0625), inside the side passage bypassing the giant guards.
The opening pledge and frostbound crossing supply the story connection without
adding a fifteenth objective or changing combat/reward progression. Native host
routing, exact quest bindings, final journal destination and Kael exits use
Everfrost (zone 30). Normal Everfrost/Permafrost content is preserved.

The owner requested Camil's Paladin quest structure for Shadow Knights, with high difficulty for a Shadow Knight main and lore-connected zones permitted. This campaign mirrors the fourteen-row Vigil structure, personal ledger, managed Raid/Grind runs, three-wave defense, recovery and atomic one-time helmet delivery. Eligibility remains level 50 with Shadow Knight in any slot; calibration targets Shadow Knight as the main class. No deity restriction is added.

Kael Drakkel is the home of Rallos Zek's storm giants and has his temple ([official zone history](https://www.everquest.com/news/imported-eq-enus-51649)). The Ashen Compact, its characters and relic history are original Nightcap fiction. The player challenges a renegade war cult's claim that stolen souls make a worthy general, and takes command of its war-fire by defeating its champions. Rallos himself is not killed and the original Avatar of War is not repurposed as a level-50 boss.

The route is: enter; defeat Herald of the Iron Oath; claim Conquest, Dread and Dominion standards; protect Soulbinder Veyra's three-wave binding; defeat Marshal Kharzug; claim the oaths of the knights of Hunger, Ruin and Defiance; defeat General Vhalek; defeat the Echo of Endless War; temper the Warhelm at the War Altar; return to Drazhul Blackmantle.

## Implementation sequence and proof

1. Capture local public Kael content and reserve IDs; preserve the global Classic level-50 era. Stage an explicit zone exception, empty public foyer and a curated private population. Probe placements against native map geometry.
2. Implement an isolated Ashen ledger and native campaign service using the reviewed Vigil pattern. Wire managed admission, recovery, personal kill credit and independent reward receipts. Exercise ordered progression, cross-campaign isolation, capacity, expired runs, failed defense and inventory retry.
3. Author combat and bounded rewards. Keep four bosses, three miniboss relics, one four-quality augment family, and three final Raid reward families, with existing item budgets. Add warned movement/interrupt/add pressure rather than HP alone. Record native calibration and its limits.
4. Convert the recovered Warhelm geometry into unused Classic helmet material 91, preserving Camil's material 90 and original mesh palettes/animation. Stage archives only. Validate every supported race/gender, archive preservation and PFS limits; record visible gameplay QA as pending until actually observed.
5. Generate guarded disabled SQL, paired build instructions and recovery. Review and test the native code, Perl, content, asset and migration boundaries. Update CHANGES, status, lore, player documentation and installed skill evidence.

Reserved candidate identities: zone 113 (kael); Keeper 998860; combat/story 998861â€“998876; patron 998877; campaign task 9801; dungeon tasks 9744/9745; spawn IDs 9230000â€“9230099; helmet 990510; augment 961020â€“961023; miniboss relics 961030â€“961032; final Raid variants 960420â€“960425. Installation must reject collisions, including references. These are proposals until the capture and rehearsal pass.

The helmet matches Camil's budget: 18 AC, 25 HP/mana, 5 STA, 7 INT instead of WIS, equal resist total, no new effect/socket. Main, production activation and signed client publication require the repository's release approval; prepare and test the concrete candidate first. Existing player state and completed Camil entitlements must remain unchanged.
