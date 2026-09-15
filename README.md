# Nightcap

A solo-preferred EverQuest emulator server where preparation, class choices,
earned gear and encounter execution matter. Friends are welcome; easier access
must preserve meaningful difficulty.

**Current release: deployed for live QA, September 15, 2026.** Gameplay acceptance
is pending. `dev` and `test` contain the candidate; `main` remains the accepted
history. Documentation and website updates do not certify new gameplay.

[Player website](https://frank-grimes-jr.github.io/nightcap/) ·
[Current status](docs/status.md) · [Documentation](docs/README.md) ·
[Live QA checklist](docs/releases/live-qa-20260915/QA.md)

## For players

- **Classic progression, level cap 50.** Plane of Knowledge is the shared hub.
  The custom spell/AA offering is not a claim of strict original-era parity.
- **Three-class characters.** Both additional disciplines can be selected from
  level 1 through the Ancient Chronicler. The primary class remains unchanged.
  Class uniqueness, free slots and individual ability requirements still apply.
- **See your choices.** Login, hail, `#classes` and `/say !classes` show Primary,
  Second and Third, including empty slots. Camp/relog when instructed.
- **Earn your progression.** Buy eligible spells, songs and tomes from class
  merchants and learn them normally. Skills unlock at native required levels
  with value 1 and improve through use/training. No automatic spell scribing
  or production skill maximization is part of choosing a class.
- **PoK arrival hub.** Sixteen class merchants flank arrival. The Chronicler is
  north of the aisle; bags, epic, blessing and waypoint services share a nearby
  row. The new layout and interactions await owner in-game acceptance.
- **Equipment tiers.** Polished, Exalted and Ascended items extend progression;
  Ascended items include heroic stats. Encounter balance remains under study.
- **Early AA progression.** AA experience is enabled from level 1. The setting
  survived startup of matching world/zone binaries; XP earning needs player QA.
- **Travel.** Ancient Attunement returns to PoK. Discover waypoint markers to
  unlock destinations at the hub service; discovery/recall remain QA checks.

### What changed in the current release

The combined release adds the arrival hub and clearer class dialogue, positive
prices for all 22 bags, earned-AA persistence and atomic discipline release,
and weapon/pet/direct-AA-buff fixes. Skills and waypoint work are in the deployed
baseline. Bag base prices range from 10 platinum (8 slots) to 7,500 (40 slots);
normal merchant modifiers apply. NO TRADE and specialty-container restrictions
remain. See the [full feature-by-feature checklist](docs/releases/live-qa-20260915/QA.md).

Discipline release commits class slots, eligible earned-AA refunds/removal and
retained-class skill clamps together. Shared AA families remain owned; scribed
spells are not erased by this release path. Spell usability still depends on
remaining eligibility. Test on disposable characters before changing a valued
build. Client equipment/Skills/trainer coverage, some stats/regen acceptance,
Bard behavior, missing AA titles, augments and launcher delivery remain open.

## For operators

This is an existing development workspace with independent subprojects, not a
one-command clean installation. Do not replay historical setup SQL against live
PEQ: some scripts describe superseded NPC layouts and contain destructive steps.
Use the reviewed release's guarded migration, exact preimages and rollback.

| Location | Purpose |
|---|---|
| `akk-stack/` | Local Docker stack, active C++ and runtime quests; separate/ignored project |
| `server-mods/` | Tracked custom server-source and quest/plugin mirror |
| `eq-solo-gm/` | Vue/Vite + Express GM tools and SQL scripts |
| `eq-client-dll/` | Guarded RoF2 UI/mana proxy source and evidence |
| `era.json`, `tools/` | Declarative era policy, audits, migrations and backups |
| `docs/` | Current status, operator runbooks, dated evidence and QA |

Run commands in the named subproject. There is no root package manifest.

```powershell
# Existing stack: ensure E: and the Docker data disk are available first.
cd E:/EQ_Local_Dev/akk-stack
make up

# Optional GM UI/API, using the project's existing dependencies.
cd E:/EQ_Local_Dev/eq-solo-gm
npm run dev
```

The GM UI uses port 5173 and API 3001; host MariaDB is **3307**, database `peq`.
Credentials/configuration belong to the local setup, not the public site.
Era control is **only** `era.json` plus `tools/apply-era.ps1`; the GM era/vendor
refresh route is retired. The current hub catalog supports reviewed Classic
inventory through level 50; future-era catalogs require review before applying.

### Deployment and cache boundaries

Take and verify a full backup before destructive SQL. Match source, binary and
quest versions. AA class release requires the matching `ReleaseMulticlassSlot`
binding and plugin; the old separate SQL/purge route is retired.

- Changes to compiled rules require **both world and zone** builds. Old world
  deletes unknown rules on boot; this previously removed `AAExpMinLevel`.
- Item/spell changes require the appropriate shared-memory refresh and fresh
  zones. NPC/merchant changes need a zone restart, not just repop.
- Skill caps load directly into world and every zone; restart both generations.
- NPC relocation must also handle affected `zone_state_spawns` records. Saved
  positions can restore old locations and deleted spawns. Preserve unrelated
  state and rehearse a guarded, scoped rollback.
- Never build or routinely modify `Client_RoF2_Dev/`.

[Deployment, checksums and rollback](docs/releases/live-qa-20260915/README.md) ·
[PoK runbook](docs/pok/QA.md) · [Bag pricing](docs/ops/bag-vendor-pricing.md) ·
[Docker storage](docs/ops/docker-data-migration-20260913.md)

## Working agreement

`feature/*` → `dev` → `test` → `main`. Automated verification precedes test;
each promotion includes exact in-game steps. Main gameplay promotion requires
owner sign-off. Keep small commits and update `CHANGES.md`; [AGENTS.md](AGENTS.md)
is the canonical workspace guidance. Historical reports retain their original
dates and scope; [current status](docs/status.md) supersedes old queue summaries.

## Acknowledgements

Built with [EQEmulator](https://www.eqemulator.org/),
[akk-stack](https://github.com/akkadius/akk-stack), and
[Project EQ](https://www.projecteq.net/). Independent community project, not
affiliated with the official EverQuest service.
