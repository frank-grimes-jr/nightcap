# Broad Classic focus and defensive coverage

Deployed through dev/test/main and verified on all twelve production workers. Official wiki release 20261121-classic-defense-v1 is published and verified after explicit owner approval. Player encounter acceptance remains OPEN. Reconnect to refresh existing gear; no client download.

## Intent and implementation plan

The owner requests useful coverage across Classic stock dropped gear, including defensive abilities, without reducing healing strength or changing custom content. The previous nineteen-family release is the baseline, not the scope ceiling.

1. Capture current production drop routes, full item/spell rows, enabled conditional spawns, global-loot gates and runtime pins. No player data changes.
2. Build explicit item policy and coverage by class, slot, progression source and effect category. Expand early/mid dungeon rewards, planar class armor and raids. Preserve occupied effect fields. Use stock spell definitions and identical effect strength at all four qualities.
3. Generate full-row guarded forward/replay/inverse SQL. Test preservation of all other fields, custom content, loot and quality relationships. Rebuild and compare native item caches in disposable rehearsal.
4. Test the current shipping engine with before/after legal equipment sets, AAs and existing Dodging scales. Verify native dodge/parry/block, regeneration caps, healing/mana/cast time, incoming pressure and relevant defensive limitations. Treat additive protection as a full-loadout budget, never distribute uncapped mitigation blindly.
5. Independent review, dev/test promotion and exact player QA instructions. Maintain release evidence, CHANGES/status, installed skill and wiki impact review. Record automated validation separately from player acceptance and deployment.

The riskiest step is defensive stacking: strongest-only dodge/parry effects differ from additive AC, resist, regeneration and mitigation. Prefer modest stock dodge/parry/block and regeneration over broad defensive-discipline or rune effects. No rule/cap, spell formula, rank, loot, client or custom-item changes are planned. Any confirmed engine issue requires a separate regression and scope review.

## Baseline

Read-only production capture 2026-11-21T02:56Z: 87,268 routes, 1,569 usable stock base families including enabled conditional spawns; 1,458 have no focus. Production zone13ad2534 and item cache2ecee168 retain the approved mana-only correction and unchanged healing. Runtime pins are in runtime.json. This capture preceded activation; the current deployment is recorded above.

## Policy and evidence

119 families / 476 definitions: 84 casting focuses and40 defensive worn additions, with five overlaps. Only empty effect fields change. Normal/Polished/Exalted/Ascended use identical effect strength. `policy.json` owns exact IDs; `coverage-after.json` contains the full source/class/slot matrix. Existing healing calculation, custom content, loot, stats, ranks and signed client remain unchanged.

The native engine reproduces current shipping zone13ad2534 exactly. `native-build.json` identifies a separate diagnostic with deterministic RNG/clock, login completion and probe-only access to the two existing regeneration methods. It cannot be staged by the content-only release operator. Current caches and452production rules seed the isolated database; all four NPC templates match production.

Validation passes188 paired pressure comparisons and259 paired defensive checks (41,440,000 conditional skill rolls). All108ordinary cases survive180seconds before and after. Three-attacker pressure deaths fall23/80 to5/80; surviving longer increases total damage exposure, so raw damage totals across unequal lifetimes are not mitigation percentages. NoAA pre-raid cases retain five deaths; resource management and earned AAs still matter. Endgame curated defensive/sustain selection spends131points; no unrestricted-AA claim.

Per-cast healing never decreases, haste never slows, mana cost never increases, and HP/mana/HA/SD are identical before/after for matched equipment. Existing Dodging scale stays10. New regeneration is at most3HP/tick from a head item and3mana/tick from boots, before existing caps. Dodge/parry/block are skill-chance modifiers, not flat percentage-point protection. Integer rounding means some low-skill/priest cases show no extra dodge rolls. Monk block and pureINT caster dodge increase; behind/ranged restrictions retain native behavior.

These are primary-hand pressure and conditional skill tests with six-second native combat regeneration. They do not simulate full NPC AI, bash/stuns, special attack rounds, spell AEs, movement or player latency. Full encounter acceptance remains OPEN. Exact in-game steps are in the release QA document. No engine/client/spell changes are required; rebuild the paired item cache and use a supported whole-runtime restart. Reconnect to refresh existing item copies.

## Verified activation

Gameplay main 50626fbe79b97f512f147fd9c9de83eae7b8d2d8 (PR511), test PR510 and dev PR508/509. Stage classic-defense-coverage-20261121-v1 retained native image/binaries and installed item cache 92d057642282f4a8d608b68e9c0089d0c990774cd6728627461b82309252180f. Zero-player maintenance, fresh stopped backup, saved-state/market preservation, twelve workers, zero detected errors/restarts and open gateway verified. Rules, spell cache and signed client2026112001 remain unchanged.

Wiki 20261121-classic-defense-v1 is published and verified after the owner explicitly approved publication. All 631 canonical files, hashes, headers and private-path denials passed; five outputs changed and 626 remained identical. Sixteen Linux publisher tests and rollback rehearsal passed. Game/client services and configuration were preserved. Full AI, bash/stun, AE and visible player QA remain open.
