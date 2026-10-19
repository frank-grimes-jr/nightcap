# Combined THJ item/spell, starter and pet/WPM release

Deployed to main and OVH on October18 at the owner’s explicit request.
PR235 promotes the tested tree; signed client2026101802/proxy0.11.0 and
wiki20261018-thj-parity-v1 are verified. Classic50 remains active.
[Deployment and recovery](deployment/README.md) retain the exact receipts,
including the reviewed rule-description startup normalization. Owner RoF2
gameplay and balance acceptance remain open.

The owner's target is THJ Legendary ≈ Nightcap Ascended (Ascension). The full
forum research covered 152 pages and 3,031 posts, including comments, screenshots and
player workbooks. Exact source rows, cells, image/post URLs and reviewed identity
crosswalks are embedded in `config/thj-item-parity.json`. Original archives remain
in `E:/EQ_Local_Dev/artifacts/research/thj-forum-20261018/` and the adjacent
`thj-nightcap-comparison-20261018/`; `source-evidence.json` pins the input hashes.

## What changes

- **131 observed Ascended targets:** 4,501 supported numeric values, including
  reductions where Nightcap exceeded THJ. No blanket universal multiplier.
  Ordinary Normal items stay unchanged; intermediate numeric values are capped
  only where a reviewed top reduction would reverse progression.
- **Spell damage:** player/permanent-pet direct damage and procs add effective
  Spell Damage; ordinary DoT ticks add `floor(effective SD/2)` independently of
  duration. Existing focus/critical logic remains; critical DoT contribution uses
  the native critical ratio. This critical ordering is Nightcap calibration.
- **Heroics:** clients gain 0.1% per heroic INT on direct damage and per heroic WIS
  on direct healing, after existing modifiers, before final caps. No DoT/HoT
  multiplier or owner-heroic inheritance. Item-mod opt-outs are honored. Heroics
  act independently of the SD spell-level restriction, like a focus modifier.
- **Healing:** existing percentage HA and HoT duration distribution remain.
  Bard songs are excluded from the added HA rune bonus; instrument scaling stays.
  Existing Bard area-DoT dispatch remains an explicit uncalibrated exception.
- **Starter progression:** the reviewed 209-family policy is integrated: modest
  Normal starters, +1 weapon damage per quality with fixed delay, Ascended starter
  below comparable Normal dungeon equipment. Cultural armor is excluded.
  Dungeon generation now emits the same reviewed 330-definition catalog.
- **Combined pet/WPM:** preserve 750 caps, Hunt headroom, own pet stats plus capped
  half-owner inheritance, full instances/augments, earned AAs, heroic STR,
  shield/sustain mechanics and named effects. Their standalone evidence is in
  `../wpm-melee-20261018/`; new balance measurements must use this combined build.

## Exact anchors

| Ascended item ID | Candidate values |
|---|---|
|607869 Heavy Yttrium Chestplate|AC150; HP/Mana250; End125; SD/HA40|
|626549 Blood Cord|AC70; HP/Mana200; End100; STA40+10; STR0+0; SD/HA40|
|608364 Talisman of Vah Kerrath|HP/Mana250; End125; all seven heroics8; SD/HA30|
|628926 Cerulean Sleeves|HP250; Mana150; SD/HA12|
|640035 Sharpened Bloodtusk Lance|Damage80/Delay44; HP60; Mana50; End25; SD/HA8|
|626766 Cloak of the Black Wind|HP/Mana200; haste62; ATK15; Accuracy8; SD/HA30|
|805532 Water Sprinkler of Nem Ankh|Damage40/Delay32; Mana200; SD25/HA50|

Blood Cord and Talisman use independently inspected clean screenshots over
conflicting workbook attributes. Unresolved attribute relocations, below-Normal
workbook reductions, the augmented dagger, ambiguous IDs and unmapped proc
presentation are deferred in `catalog-decisions.json`. These exclusions prevent
unsupported precision. Formula research describes historical THJ evidence, not
access to THJ's current engine.

The spell references are the [191 SD player measurements](https://www.firesofheaven.org/threads/the-heroes-journey-multiclass-eqemu-progression-server.15510/post-5005001),
the [archived heroic-stat guide](https://github.com/P1xt/thj-wiki/blob/main/classes-and-abilities/heroic-stats.md),
and the [Bard rune correction](https://www.firesofheaven.org/threads/the-heroes-journey-multiclass-eqemu-progression-server.15510/post-5085200).
The measurements support the noncritical additive targets; they do not establish
THJ's critical ordering or current live formulas.

## Implementation and reproducibility

`tools/thj_item_parity.py` plans exact targets. `tools/thj_combined_content.py`
composes companion changes before item/starter/dungeon tuning. It generates
**1,393 changed existing definitions**, with full 285-column captured preimages.
One transaction owns these existing-item changes; separate pet/WPM content is
generated with `include_gear=False`. It accepts only the original, complete
companion, or complete final row. Every final full-row hash must match.

Numeric recovery restores 1,369 parity/starter/dungeon rows to the companion
baseline, retaining new effects and sockets that may contain owned augments.
It is not a return to the old whole database. Ownership, receipts, inventories,
AA points and saved cooldowns are never part of these item statements.

`tools/item_scaling_overrides.py` maintains the final fresh-bootstrap override
block. The generic two-column SD/HA planner excludes explicitly owned families.
`tools/dungeon_catalog.py::legacy_items` is the dated migration baseline;
`items()` is the current compiler. Never rerun the destructive tier bootstrap on
an existing server. No client item IDs, effect identities or era gates are widened.

The two new rules default false in the compiled catalog. Guarded candidate SQL
enables `Spells:NightcapTHJDamageScaling` and
`Spells:NightcapHeroicSpellScaling` independently. Paired world/zone binaries are
required or world can remove unknown rules. Item/spell caches and the pet/WPM
client delta must match. Current Classic50 remains the live profile; staged PoP65
content does not activate its acquisition or level gates automatically.

Read [QA.md](QA.md) for the exact owner test pass and [ACTIVATION.md](ACTIVATION.md)
for preparation/recovery. `evidence/` contains actual automated results and build
hashes; those do not replace owner acceptance or production receipts.

## Verification and testing handoff

The 157-test regression run plus focused follow-ups cover **165 unique tests**,
including real MariaDB forward/recovery/reapply and fault-injection checks.
All **47 native scenarios** and 12 mechanics assertion groups pass: six class-order
probes, 23 encounters and 18 spell probes with 10,800 samples. Native AA checks
cover 6,960 eligibility cases. All 2,827 retained source files, 119 overlays,
three server binaries and 144 diagnostic objects/libraries are fingerprinted.
Native fixture failures exposed duplicate Lore items and an augment selected as
ordinary armor; the selector was corrected without changing game restrictions.

[COMPARISON.md](COMPARISON.md) records a significant balance shift. Same-item
controls give WPM shield 4,510 versus 2,911 DPS, the fixed caster controller 225
versus 685, and equipped Classic pets 290 versus 452. Low-base spells and DoTs
gain substantially. Spell-rank choice, mana sustain, pet contribution and maximum-AA
WPM burst are mandatory owner gates; these diagnostics do not approve balance.

`package_test_bundle.py` stages the matching server binaries, ordered SQL,
numeric recovery, unsigned five-file client delta, manifests and test guides
beside this worktree in `thj-parity-test-bundle/`. It does not install or publish
anything. Regenerate caches on the actual test target and preserve its complete
current client base. The installed Nightcap knowledge and wiki candidate notices
are maintained separately from deployment and acceptance.
