# Player guide content audit — October 4, 2026

The owner requested a clean list of custom changes followed by a separate list
of implemented custom quests. The guide now has 43 visible changes in six groups,
two installed quest lines, and eight built but unreleased journal quests.
The game source/status baseline is main `f9ab114`, merged into the website branch.
This is a website-only publication; no gameplay promotion or acceptance is implied.

## Content ledger

| Guide group | Current evidence |
|---|---|
| Character / progression (8) | July changelog; `docs/releases/main-live-qa-20260915.md`; October 1 spell inspection and October 2 spell-menu repair; multiclass plugin/source |
| Loot / gear / money (11) | July changelog; `docs/releases/advanced-loot/ACTION-REPAIR.md`; current helmet publication records; hosted rules below |
| Combat / buffs / recovery (5) | `docs/releases/client-gameplay-20260919.md`; current reconnect and permanent-lifetime repair records in `docs/status.md`; October 1 death-rule audit |
| Pets (4) | `docs/releases/pet-management-20260922/`; Enchanter animation command release; pet-window layout repair in `CHANGES.md` |
| Tunnel / travel / services (9) | Current tunnel workshop, class gatherings, residents, market and travel records linked from `docs/status.md`; October 1 installed Keeper and buff-script audit |
| Updates / interface / appearance (6) | Launcher, Classic models and startup release records; `docs/releases/npc-animation-20261004/enchanter.md`; loading artwork sources in the hosting runbook |
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

The browser suite checks the 43 visible changes, two installed quests, eight
unreleased quests, important warnings, anchors, keyboard FAQ, history, deep links,
five viewport widths, 200% text, original images, no runtime scripts and strict
branding/CSP. The hosting runbook records the activation and private-access result.
