# Player guide content audit — October 4, 2026

The owner requested a clean list of custom changes followed by a separate list
of implemented custom quests. The expanded guide now has 70 feature/control entries in eight system sections,
two installed quest lines, and eight built but unreleased journal quests.
The game source/status baseline is main `b1110e8`, merged into the website branch.
This is a website-only publication; no gameplay promotion or acceptance is implied.

## Content ledger

| Guide group | Current evidence |
|---|---|
| Custom loot window (8) | `docs/releases/advanced-loot/{README.md,ACTION-REPAIR.md}`; current `tools/client_advanced_loot_ui.py` labels and deployed currency/loot code |
| Multiple pets & custom pet window (9) | `docs/releases/pet-management-20260922/{README.md,QA.md,PRODUCTION.md}`; ADRs 0038/0039; Enchanter animation-command release |
| Classes, skills & progression (13) | July/August changelog; September 8 held-Monk acceptance; September 15 combined live release; current spell-menu and inspection releases |
| Custom gear, bags & selling (11) | July/September item, heroic and merchant changes; current helmet publication; hosted October 4 gear/stat checks below |
| Combat, buffs & recovery (6) | September 19 gameplay release and ADR 0038; current blessing reconnect/lifetime release records |
| Tunnel life, shops & services (9) | Current tunnel class/workshop/social layout and market release records linked from `docs/status.md` |
| Travel & private adventures (7) | Current Merrin/travel alcove records; installed Keeper audit; waypoint content below |
| Launcher, interface & appearance (7) | Current launcher/model/startup releases; established caster UI in September 15 combined live QA; native animation repair release |
| Ascension | Installed `quests/ecommons/Epic_Forgemaster.pl` read directly; NPC 999226 spawned in ecommons version 0 |
| Waypoint Explorer | Installed Waypoint Master and marker scripts; hosted waypoint/title records below |
| Journal / Epic 0.5 | Candidate `docs/adventure-journal/{SPEC.md,catalog.json,RELEASE.md,native-evidence.json}` in local `adventure-journal-epic05` worktree; hosted absence checks below |

The older eight-court layout is replaced by four gatherings with four trainer/
merchant pairs each. Loot All now describes earned loot across the current zone
or instance, while ordinary/public corpse looting stays range-limited. The helmet
has no acquisition source. Combat/item corrections and augments remain separate
from installed changes. Buff/pet/client repairs retain player-retest caveats.

## Read-only hosted content checks

Queries selected content tables and specific rules only. No player rows or
credentials were exported, and no database or game-service changes were made.

- Ancient Chronicler (999220), Epic Forgemaster (999226), and Waypoint Master
  (999239) are spawned in ecommons version 0; waypoint marker 999240 exists.
- `nightcap_waypoints` contains 72 destinations. Title 398 belongs to title set
  100 and grants suffix `the Explorer`.
- Ascension's installed script consumes exactly the documented materials when
  handed in as instructed: eight Essence of Ascension and 100,000 platinum, plus
  the original epic removed from inventory. Eligibility uses the starting class
  (IDs 1–14); both supported Ranger epics are upgraded if carried. Excess hand-in
  materials are consumed, so the guide explicitly says exactly eight.
- Journal tasks 9500–9507, journal control/state tables, and `epic05*.pl` plugins
  are absent. Reward item 900501 is absent. The eight quests are built candidates,
  not installed content. Essence item 900000 and helmet 990500 exist.
- Ruleset 1: `Character:StatCap=425`, `ItemSpellDmgCap=250`, `ItemHealAmtCap=250`;
  `Spells:ItemExtraSpellAmtCalcAsPercent`, `FlatItemExtraSpellAmt`,
  `IgnoreSpellDmgLvlRestriction`, `DOTsScaleWithSpellDmg`, `HOTsScaleWithHealAmt`,
  `DOTBonusDamageSplitOverDuration`, and `HOTBonusHealingSplitOverDuration` are true.
  The website describes item bonuses, not a cap on total spell damage or healing.

Installed SHA256 evidence:

| Quest file | SHA256 |
|---|---|
| ecommons/Epic_Forgemaster.pl | `dfc286eabf1fb40194e71b62a74e01e9c3a448cf3e618fb4c2978f9aa1bea0de` |
| ecommons/Waypoint_Master.pl | `94148dfb4241e0bfaf8af9de19280eaa8afb49396b194a089808fe9d082a1440` |
| global/999240.pl | `78edf254f2b484c6d8855059b1ecddb062b5dae6f64f3c70f7a771fb9f0ec0b4` |
| ecommons/The_Ancient_Chronicler.pl | `777d57939ab1a813f502e1b389c7665f9da2febdb51a049a22bcd0e25a11413e` |

Local audit scripts and screenshots are under
`E:/EQ_Local_Dev/artifacts/player-website-20261004/`.
Independent content review prompted the explicit health, scroll-learning,
percentage gear-bonus and raised-stat-cap additions.

## Website validation

The browser suite checks the 70 visible feature/control entries, two installed quests, eight
unreleased quests, important warnings, anchors, keyboard FAQ, history, deep links,
five viewport widths, 200% text, original images, no runtime scripts and strict
branding/CSP. The hosting runbook records the activation and private-access result.

## Systems coverage follow-up

The owner's loot-window/multiple-pets/custom-pet-window examples were present in
the initial list but too compressed. Each now has explicit named entries and a
front-of-section shortcut. The audit covers the complete changelog from June
through October, cross-checking current release scope rather than repeating every
historical repair as a separate feature.

The current loot UI defines all five saved rule choices and six settings. Leave
does not change a saved rule; Ignore does. Automatic personal collection, new-loot
opening, unfiltered-only display, saved rules, split coin and classic fallback
are documented. Pet scope matches both window and slash commands; armor selection
is independent. Class-pet persistence supersedes the older summon-again limit.
Temporary summoned armor is rejected by managed slots. Player and owned-pet
beneficial buffs share the permanence policy. The broader combat/skill candidate
remains undeployed, including Beastlord and Monk fist corrections.

Independent review checked the expanded draft and identified these final
clarifications. Desktop/mobile views and the featured-link behavior were inspected.
This inventory covers custom player systems and their controls; infrastructure,
GM tools, historical superseded layouts and build-only experiments are excluded.

## Latest live release reconciliation

Current main `b1110e8` adds three deployed releases. `docs/releases/passive-aa-20261004.md`
defines additive 1% of the full AA award at focus off, full allocation at focus on,
and conversion of historical partial allocations to 100%. The earlier `#aaexp 50`
example is removed. Tiny passive awards can round down to zero.

`docs/releases/free-trade-20261004/README.md` and the current native sell-all path
establish all-item trading, one-platinum resale per physical original-NO-DROP item,
container retention, and removal of obsolete advanced-loot NO TRADE consent.
Previously protected former-NO-DROP items, including temporary/free rewards, can
now be sold. Ordinary temporary/zero-value exclusions do not protect those items.
Equipment eligibility, lore, capacity, temporary expiration and Pet Armor limits
remain. Merchant preview can differ from the actual fixed payout.

`docs/releases/loading-screens-20261004.md` verifies game 2026100407 and desktop
0.4.0: ten paintings cover 55 numbered loading slots and the fallback. Both game
and launcher must be fully closed before reopening the normal shortcut to update.
The website continues using its two original images without payload expansion.
The passive-AA deployment repeated full-catalog free-trade verification and retained
the gallery/client files. These are deployed changes with manual gameplay QA open.
Independent content review identified every obsolete website claim before editing.
