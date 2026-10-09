# Native equipped-stat measurements

The isolated native engine evaluated 24 synthetic level-50 loadouts: three multiclass profiles, four gear qualities, and identical equipment before/after six band-6 augments of matching quality. These are endgame augment controls even in the Base gear row; they do not represent a low-level character. Every profile spent **0 AA**, with no active buffs or pets. The captured production cap rules were applied to a content-only local PEQ fixture; no production player rows were copied.

Warrior/cleric/wizard and magician/necromancer/shaman use six Abyssal Thoughtpearls (heroic INT/STA). Warrior/cleric/monk uses six Ghoulheart Opals (heroic WIS/STA). The raw diagnostic calls the legacy top gear tier `Ascended`; the table uses the approved new-item label `Ascension`.

| Classes | Quality | HP before → after | Mana before → after | Spell Damage | Healing Amount |
|---|---|---:|---:|---:|---:|
| war-clr-wiz | Base | 3,525 → 4,335 (+23.0%) | 2,662 → 3,337 (+25.4%) | 0 → 12 | 0 → 0 |
| war-clr-wiz | Polished | 4,135 → 5,107 (+23.5%) | 3,314 → 4,182 (+26.2%) | 100 → 118 | 100 → 100 |
| war-clr-wiz | Exalted | 4,640 → 5,924 (+27.7%) | 3,907 → 4,883 (+25.0%) | 240 → 270 | 240 → 240 |
| war-clr-wiz | Ascension | 5,902 → 7,516 (+27.3%) | 4,707 → 5,877 (+24.9%) | 250 → 280 | 250 → 250 |
| war-clr-mnk | Base | 3,360 → 4,170 (+24.1%) | 2,385 → 3,082 (+29.2%) | 0 → 0 | 0 → 12 |
| war-clr-mnk | Polished | 3,913 → 4,885 (+24.8%) | 2,930 → 3,834 (+30.9%) | 100 → 100 | 100 → 118 |
| war-clr-mnk | Exalted | 4,354 → 5,638 (+29.5%) | 3,405 → 4,426 (+30.0%) | 240 → 240 | 240 → 270 |
| war-clr-mnk | Ascension | 5,542 → 7,156 (+29.1%) | 4,099 → 5,301 (+29.3%) | 250 → 250 | 250 → 280 |
| mag-nec-shm | Base | 2,669 → 3,457 (+29.5%) | 3,291 → 4,131 (+25.5%) | 0 → 12 | 0 → 0 |
| mag-nec-shm | Polished | 3,148 → 4,183 (+32.9%) | 3,935 → 5,019 (+27.5%) | 100 → 118 | 100 → 100 |
| mag-nec-shm | Exalted | 3,591 → 4,959 (+38.1%) | 4,473 → 5,907 (+32.1%) | 240 → 270 | 240 → 240 |
| mag-nec-shm | Ascension | 4,437 → 6,134 (+38.2%) | 5,832 → 7,633 (+30.9%) | 250 → 280 | 250 → 250 |

The equipped AC sum did not change in these selected augment profiles. Other catalog profiles with AC, avoidance, shielding, regeneration or different heroics require their own encounter checks. Spell Damage/Healing Amount reached 280 at the top tier as designed. The focused native cap tests separately verify that headroom never grants missing raw stats and that level, recommended scaling and eligibility gates apply.

Six endgame augments add roughly 23–38% HP and 25–32% mana in these zero-AA controls. That is material combined power, including native heroic effects, even though the output cap increase is bounded. The approved values are retained for owner-authorized live QA; these results do **not** establish acceptable solo encounter difficulty. Before gameplay acceptance, compare legal-AA builds, pet contribution, healing/sustain, resource use, failure rates and kill times using the exact encounters in [QA.md](QA.md). No NPC HP or additional cap tuning has been applied to conceal the gain.

Evidence: [inputs](balance-inputs.json), [raw results](balance-results.json), [fixture scope](balance-setup.json), [diagnostic build](balance-build-manifest.json). Reproduce this table with `python tools/summarize_zone_hunt_balance.py --release docs/releases/zone-loot-20261009`. The diagnostic links the actual candidate zone objects; it is not installed as a game server.

Production scope: these measurements used the earlier development diagnostic. The deployed hardened source preserves prior live combat/skill behavior and applies the feature separately. The table is a synthetic stat control, not a production encounter measurement. See [build provenance](PRODUCTION.md).
