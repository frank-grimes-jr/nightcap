# Stock PEQ comparison — October19,2026

Read-only research. No repository implementation edits, database import, production mutation or deployment. The proposed policy is a Nightcap calibration bounded by observed THJ items; it is not a recovered universal THJ algorithm.

## Source and identity

The official EQEmu documentation links ProjectEQ's public database archive at https://db.eqemu.dev/:
https://docs.eqemu.dev/developer/useful-links/ . Its public SPA uses `/api/v1/artifacts` and `/api/v1/dump/archive/{filename}`.

Pinned archive: https://db.eqemu.dev/api/v1/dump/archive/peq-1792195214.zip , created2026-10-17T00:00:14,32153587 bytes, SHA256 `c27a943e73890cdfd4ac2b1e30e58d557d2d3e4254030836888eacf4f102ef18`. `source-manifest.json` pins the complete content member, item SQL, selected rows, THJ catalog and Normal fixture independently. This is stock PEQ emulator content, not a Daybreak database.

All131 base IDs exist in stock PEQ, all131 stock names exactly match their captured Normal names, and all285 columns of these captured Normal rows match stock after numeric normalization. Thus there is no custom-Normal denominator drift in this sample. This describes the October18 research fixture, not current production: later companion migrations alter six observed families.

Five evidence names need explicit normalized crosswalks: Intsense→Intense spelling28664; apostrophe→backtick in Sal`Varae31239; MAG/BST suffixes on same-name Figurines35013/35015; trailing whitespace on Charm of Exotic Speech40342. The Figurines have distinct stock classes4096(MAG) and16384(BST), confirming the selected IDs. `identity-crosswalk.json` retains the raw mismatch evidence instead of silently erasing it.

## What the131 samples support

Counts below use positive stock denominators unless marked additions. Zero-to-zero observations never enter ratio fitting.

| Field | Observed result |
|---|---|
| AC |119/119 exactly2x |
| HP |122/122 exactly2x; three separate0→10 additions |
| Mana |116/123 exactly2x; seven positive exceptions; two0→10 additions |
| Primary stats |520/522 positive values exactly2x; two STA exceptions and three separate0→positive additions |
| Five resists |461/461 positive values exactly2x; two cold-resist0→positive additions |
| Weapon damage/delay |5/5 damage2x;5/5 delay unchanged; only five actual weapon observations, including one epic |
| Haste |9/9 round-half-up(1.5x);111 zero values remain zero |
| HP regen/mana regen |18/18 and3/3 exactly2x |
| Endurance |12/13 unchanged; one2x |
| Shielding, spellshield, avoidance, strikethrough, combat effects, stun resist |7/4/5/4/3/6 positive observations respectively, all unchanged |
| Damage shield |2/2 unchanged |
| Backstab/elemental damage |One4x backstab observation; one unchanged elemental observation, insufficient for global multipliers |

Spell Damage, Healing Amount and Accuracy are added to stock zero. `SD=max(2*stockINT,stockWIS)` fits127/128 observations (119/120 positive); `HA=2*stockWIS` fits125/126 (93/94 positive); `Accuracy=ceil(stockDEX/2)` fits125/127 (70/71 positive). Sharpened Bloodtusk Lance40035 is the shared older2024 screenshot exception: SD/HA8 instead of16, Accuracy3 instead of5. Magi`Kot sleeves11598 has Accuracy0 instead of9. No sampled item distinguishes max(2INT,WIS) from INT-present?2INT:WIS, so choosing max is an explicit calibration.

Heroics follow round-half-up(final primary/resist divided by4) in967/986 positive observations.19 exceptions remain exact overrides, including Shuriken's smaller heroics and several workbook anomalies. Do not inflate support by quoting only the1412/1431 count that includes zeros.

Attack is nonlinear: an optional candidate `(stockATK>0 ? stockATK+ceil(STR/4) : ceil((STR+DEX)/2))` fits125/128 (104/107 positive), but three exceptions are large or unexplained. Preserve native Attack for unobserved families unless deliberately selecting that calibration. Do not use the1.2 median attack ratio:72 zero→positive additions have no meaningful stock ratio.

Full per-cell evidence: `field-observations.csv/json`; summaries by field/category: `field-summary.json`, `category-summary.json`; descriptive candidate fits and exceptions: `candidate-model-fit.json`; heroic exceptions: `heroic-quarter-check.json`. Categories are25 weapons,50 armor,52 accessory/held,4 shields. There are no bags in the sample.

## Recommended deterministic policy

`proposed-field-rules.json` is the machine-readable proposal. Derive ordinary numeric targets from pinned stock rows, while treating the exact131 overrides and209 starter families as explicit higher-priority policies. Preserve Normal, Classic50 gates, current effects and sockets. Exclude custom dungeon/hunt families, bags, augments and epic offset families from a generic ordinary fallback. Keep unobserved negative and utility/nonlinear fields unchanged rather than extrapolating sparse or nonexistent evidence.

For ordinary positive scalar stats, derive final target T, then use Normal N, Polished N+round-half-up((T-N)/3), Exalted N+round-half-up(2*(T-N)/3), Ascended T. These fractions are Nightcap calibration: this131-item catalog supplies no lower-tier THJ samples. They yield roughly1.333/1.667 below a2x top and keep coherent distance from Normal. Keep Ascended-only heroics as a separate policy; blindly interpolating heroics would newly add them at lower tiers. Small integer plateaus are legitimate.

This replaces old HP/mana1.45/1.9/2.4 and weapon1.1/1.2/1.35 when adopted; AC/core1.35/1.65/2.0 was already similar. Modest starter families must keep their current0/1/2/3 spell/heal bonuses, +1 damage steps and fixed delays. Generic twofold weapon damage is supported by five observations, not every weapon category, and needs combined Classic50 balance measurement.

## Effects and required safeguards

The parity planner's owned field allowlist is numeric and does not overwrite effects. The current full-row companion layer deliberately adds third sockets to Hammer of Holy Vengeance20627(type8), Kelp Hilted Mace22946(type4), Shinai26740(type8), Shield of Strife27298(type8), Palladius' Axe31232(type4), across all four qualities. Diaku Armor Fragment51912 and its qualities get worn spell42847/Diaku Combat Blessing. These24 definitions must retain those changes; `deployed-family-effect-changes.json` captures exact old/new fields. Do not replace full current rows with stock rows when deriving numeric targets.

The current planner caps intermediate values rather than recalculating them; any generalized implementation and fresh-bootstrap SQL must share the same target/interpolation policy. Repeated planning must be idempotent, stock identity drift must fail visibly, and full-row guarded migrations must preserve unrelated fields. Keep effects/sockets in numeric rollback because players may already own socketed augments. These checks establish implementation integrity, not player balance acceptance.
