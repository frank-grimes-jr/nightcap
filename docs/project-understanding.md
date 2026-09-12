# Nightcap project understanding and balance baseline

Date: 2026-09-12
Scope: repository onboarding, custom-system source review, and read-only local PEQ inspection.

Follow-up: [baseline reconciliation](balance/reconciliation.md) corrects the
initial main-only view below. The newer dev and spell/healing feature histories
explain the observed source/item discrepancies and are now integrated on the
reconciliation feature branch. The missing AA rule has been restored in PEQ;
runtime reload remains pending. Treat the remainder as the dated initial audit.

## Product intent

Nightcap is a solo-preferred EverQuest server with meaningful difficulty and earned
progression. THJ is a reference for multiclass capability and item progression;
Nightcap's balance requirement governs which ideas fit. PoK as hub, four item tiers,
and permitted MacroQuest QoL are established local choices.

The owner explicitly allows evaluating spell damage/healing caps above 250 and NPC
HP changes. That is design latitude, not evidence that either should change now.
Success means a prepared solo player can overcome demanding content through build,
gear, resource management, and execution. Encounter duration alone is insufficient
evidence of difficulty.

## Architecture and operating agreement

| Layer | Role and authority |
|---|---|
| `akk-stack/code/` | Active C++ source overlay: world/zone processes, combat, spells, skills, AA access, loot. Much of it is outside the root tracked mirror. |
| `akk-stack/server/` | Runtime quest/plugin files and compiled server assets. Perl plugins actually live under `server/plugins/`; Lua takes precedence over the global Perl player script. |
| PEQ, host port 3307 | Live content, items, spells, rules, characters, and custom state. A setup script's presence does not prove deployment. |
| `server-mods/` | Tracked mirror of selected custom source and quests; currently incomplete and partly stale. |
| `eq-client-dll/` | Guarded x86 RoF2 DirectInput proxy for caster UI, mana calculation access, and mana gauge visibility. Actual mana and class membership remain server-owned. |
| `eq-solo-gm/` | Vue/Vite UI (5173), Express API (3001), SQL setup scripts, character/account/rule administration, vendor refresh, manual boss tracking. |
| `era.json` and `tools/` | Declarative era control, spell-access synchronization, database backups. Use the era script rather than the GM era endpoint. |
| Supporting projects | Wails expansion switcher handles client assets; Monocle provides zone/import tooling; the Go installer and akk-stack support setup. MQ/EQZip/client folders are supporting assets, not the core gameplay implementation. |

Branch flow remains `feature/*` -> `dev` -> `test` -> `main`. Automated checks precede
promotion to test; every test promotion includes concrete in-game steps, NPCs,
zones, and expected results. Main requires owner sign-off. Back up before destructive
SQL. Record significant changes in CHANGES.md.

Cache boundaries matter: new item/spell rows require shared-memory regeneration
and zone restarts; quest changes require quest reload/restart; NPC/merchant data
require a zone restart. Skill caps are process-local in this build and require world
and all zones to restart. Compiling a binary does not replace existing processes.
The binary client folder remains protected from routine modification.

## Implemented systems and current limits

- **Multiclass:** `character_multiclass` is authoritative; Chronicler dialogue calls
  a Perl plugin. C++ consults held classes for AA access, best HP/mana, spell gates,
  skill eligibility, and equipment legality. Current adoption code has no 20/50
  level gate. Spell class-level widening is still global; server checks using those
  widened fields cannot by themselves establish original class ownership. The
  broader client/per-character access work remains important.
- **Skills:** the active overlay now seeds eligible native skills at value 1 through
  `ReconcileMulticlassSkills`, including login/level-up paths. This differs from the
  tracked plugin's max-training behavior and older documentation. Active C++ tests
  cover native unlocks, held-class eligibility, trainer decisions, and monk ability
  eligibility; that is source coverage, not a claim that tests ran in this review.
- **Client casting:** July 28 QA explicitly accepted the stable mana gauge, casting,
  zoning/relog behavior, and stock-caster regression checks. That milestone is done.
  It does not prove all equipment, trainer, skill-window, or combat-window gates are
  solved. The DLL README still contains older pending/trace instructions.
- **Loot:** Base/Polished/Exalted/Ascended variants use +200k/+400k/+600k IDs; epic
  upgrades use +800k. Source default tier probabilities are 10%/2%/0.25% per eligible
  item drop, not per kill. No matching database override was found. The active loot
  hook itself is absent from the tracked mirror.
- **Tier power:** script multipliers reach 2.4x HP/mana, 2x core stats, 1.2x endurance,
  and 1.35x offense. Ascended gear adds heroics. Live data also has added advanced
  stats that this script does not reproduce; see below.
- **QoL:** PoK start/recall, seven documented instance destinations, level-bracket
  buff NPCs, long-lived self buffs, permanent bard song data, waypoint discovery,
  Ascended summons, and player commands are present in source/history. PEQ confirms
  both buff NPC rows and 72 waypoint definitions. No-corpse rules are installed;
  zero death XP loss is not established.
- **Progression:** the GM API has manual per-character boss checkmarks, not automatic
  account-wide progression unlocks. Item combining/upgrading beyond the epic quest,
  general self-buff stacking, and multiple pets remain gaps in the local design map.
- **Zone augments:** approved design exists; no rows in its proposed 900101-900124
  range exist in PEQ. Eligibility must reflect actual difficulty at level 50.
  The spec requires owner review of the zone-to-tier assignment before deployment.

## Observed balance configuration

Read-only database observations, not combat parses or proof of each running
process's in-memory rules. Relevant Classic combat zones use ruleset 1; PoK uses
ruleset 2. The source rule loader loads default rules before non-default overrides.

| Setting | PEQ ruleset 1 value |
|---|---|
| Era / level cap | Classic (0), level and XP cap 50 |
| AA era restriction | Disabled |
| XP / AA XP multiplier | Approximately 0.65 each |
| AA XP per point | 50,000 |
| Stat cap | 425, with heroic cap effects handled separately |
| Item spell damage / heal amount caps | 250 / 250 |
| Flat item extra spell amount | Enabled |
| Item extra spell amount as percent | Enabled |
| Ignore spell damage level restriction | Enabled |
| DoT / HoT scaling | Both enabled |
| DoT / HoT bonus split across duration | Both enabled |
| Heroic INT -> spell damage / WIS -> heal amount | Both disabled (0) |
| Merchant loot buy multiplier | 2.5 |
| Leave corpses / naked corpses | Both false |

`Mob::GetExtraSpellAmt` in `akk-stack/code/zone/effects.cpp` returns
`abs(base_amount) * item_bonus / 100` immediately with the two enabled flat/percent
rules. For an eligible direct spell, ignoring other modifiers, 250 points therefore
adds 250% of base (3.5x total); 500 adds 500% (6x total). That is about a 71% increase
in this simplified capped total. It is not a flat +250 hit/heal, nor a universal
final-output multiplier: spell exclusions, focus/critical effects, and the separate
DoT/HoT duration-splitting paths matter.

The equipped-item aggregate observed at review time topped out at 60 spell damage
and 60 healing; no equipped augments were found. This is a raw inventory snapshot,
not a legal endgame loadout model or measurement of effective bonuses. It does not
justify assuming the 250 cap currently constrains these characters.

Example encounter rows: Nagafen and Vox are level 55, 32,000 HP, 85-218 melee damage;
Phinigel is level 53, 18,000 HP, 61-156 damage. These are database baselines before
runtime effects and encounter mechanics, not conclusions about solo difficulty.

## Reconciliation needed before implementation

1. **Source/mirror drift:** after normalizing CRLF, nine mirrored files differ from
   the active overlay: `aa.cpp`, `client_process.cpp`, `client.cpp`, `client.h`,
   `exp.cpp`, `perl_client.cpp`, `plugins/multiclass.pl`, and both global player
   Lua/Perl files. Other raw hash differences were line endings. Preserve the active
   work and reconcile deliberately; copying the mirror over it would lose behavior.
2. **AA minimum override absent:** no `Character:AAExpMinLevel` row was found in any
   ruleset. The active source defaults to 51 and checks it in `exp.cpp`; the tracked
   SQL explicitly intends an override of 1. Verify the running build/rules and
   deployment history before treating the documented level-1 AA XP feature as live.
3. **Item reproducibility gap:** item 9289 has 0 spell damage/healing; live variants
   209289/409289/609289 have 5/12/20 respectively. The tracked script only multiplies
   positive existing values, so regeneration would lose these additions. Trace and
   preserve the authoritative item-generation changes before any rerun.
4. **Documentation drift:** README, blueprint, old QA reports, and DLL README mix
   superseded and current claims. Use dated acceptance records plus source/data.
   The next-steps file itself has both a shipped-waypoint statement and an older
   reconciliation instruction. Historical GitHub write restrictions are not current
   authorization policy.
5. **Operational bypasses:** the GM era endpoint still writes rules and de-levels
   characters directly; this conflicts with the declarative working agreement.
   Its generic solo presets also overwrite the intended XP/AA tuning. The NPC-scale
   GET endpoint ignores its zone parameter and reads a global scale table; it is not
   an implemented encounter tuning workflow.
6. **AA names:** 189 enabled abilities currently have names containing `Unknown`.
   This is only one discriminator; it is not the reviewed removal set. Recheck
   purchased ranks and client string coverage before disabling anything in #16.
7. **Verification scope:** root main was 36 commits ahead of origin/main, with an
   existing modified Chronicler file and untracked workspace components. No commits,
   pushes, gameplay edits, deployments, or client changes were performed in this
   review. Docker was running; process/binary correspondence and manual gameplay
   acceptance were not revalidated. Live GitHub issue status was not checked.

## Recommended next work

Balance-diagnostic follow-up (2026-09-12): native activation controls now reproduce
Celestial Regeneration's target-level rejection despite legal AA ownership, the
Tenacity/regeneration shared cooldown, and temporary AA buffs entering the permanent
self-buff path. Reconcile those interactions before numerical tuning. The 144-case
activated-AA boss matrix is candidate evidence; preparation, final BiS and broader
build coverage remain open. See `balance/native-activated-aa.md` for the dated
findings and reproduction controls.

The separately compiled AA-duration candidate now passes 18 native controls:
direct AA spells keep native timers and ordinary preparation buffs keep their
long duration. Maximum-rank Tenacity remains dangerous at low health even with
normal timing. See `balance/native-aa-duration.md`; the live binary is unchanged.

First reconcile the current source, migrations, and AA minimum rule so tests and
balance measurements describe the same server. Then refresh the concrete backlog:
#16 AA strings, #22 bag pricing, #23 feature page, #26 augments, and #19/#20 bard
behavior, alongside the remaining multiclass/client access work. Treat these as
local backlog references, not freshly verified GitHub issue states.

For balance, build a small encounter baseline before selecting new numbers:

- Cover leveling, fresh level 50, intermediate gear, and Ascended/augmented endgame;
  keep AA budgets, buffs, skills, and gear recorded for every comparison.
- Exercise melee/sustain, direct caster/healer, and pet/DoT/control builds, including
  burst/stacking combinations. A gain for one archetype can leave another behind.
- Use repeatable trash pulls, dungeon named encounters, and era bosses. Measure
  kill time, incoming burst, mana consumption, sustainable healing, cooldown usage,
  deaths, and recovery rather than only DPS or HP.
- Use HP mainly to control fight duration and attrition; use incoming damage,
  resists, mechanics, adds, and resource pressure to control danger. Tune rewards
  against that difficulty and check for trivial farming routes.
- Change a small set of related values, capture before/after results, retain a
  rollback, and provide explicit in-game QA. Raise caps only when reachable gear
  hits them and encounter/build evidence supports the additional power.

No numerical balance change is recommended as a concluded fix from this onboarding
alone. The core balance requirement is now in AGENTS.md for future development.
