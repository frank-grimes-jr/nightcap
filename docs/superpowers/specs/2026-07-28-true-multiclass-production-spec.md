# True Multiclass Production Parity

Date: 2026-07-28
Epic: GitHub #10
Status: Approved product contract; implementation not started

## Objective

Make every held class—primary, secondary, and tertiary—function as a real class in ordinary play. A character must be able to learn, improve, display, train, equip, and use the spells, disciplines, activated skills, passive skills, and equipment of all held classes. The result must be a production-grade Nightcap asset with the same broad multiclass expectation as The Heroes' Journey (THJ), not a one-off workaround for a test character.

## Confirmed product contract

- A held class grants its normal player-facing gameplay at the class's native character-level thresholds.
- Eligible skills are automatically granted at skill value `1` when their native unlock level is reached.
- Skills improve through normal use and normal training after unlock. Production code must never silently maximize a character's skills.
- Trainers for every held class are optional shortcuts and must work for eligible skills.
- Client windows and controls must expose eligible spells, disciplines, skills, trainers, and equipment actions.
- The server remains authoritative. A client patch may permit an action to be submitted, but the server must validate class membership, level, race, deity, slot, item, skill, and other normal restrictions.
- The existing caster work (spellbook, spell use, mana/stats, and disciplines) remains supported and receives regression coverage.
- The epic includes a branded launcher that installs, validates, repairs, and updates the exact required client assets on a clean RoF2 installation.

## Scope

### Included

1. Skill unlock, persistence, improvement, and trainer behavior for all held classes.
2. Activated combat skills and disciplines for all held classes.
3. Player-facing passive and innate class mechanics where EQEmu currently gates behavior on the base class.
4. Equipment submission, server authorization, bonuses, and combat effectiveness for held-class items.
5. RoF2 client UI and gate patches needed for skills, combat abilities, trainers, and equipment.
6. Exact-client version guards, fail-closed patching, configuration, logging, and static patch-site verification.
7. A production launcher and signed-release workflow for required client files.
8. Automated, integration, and in-game QA, including a dedicated `Monktest` character.

### Explicitly excluded

- Multiple simultaneous pets.
- Self-buff stacking changes.
- New progression systems.
- Unrelated THJ feature gaps.
- Global item-table class widening or other database corruption used to fool the client.

## Core definitions

**Held class** means any class present in the authoritative primary/secondary/tertiary class mask.

**Native unlock level** means the earliest character level at which the stock `SkillCaps` data gives that skill a positive cap for a held class.

**Eligible skill** means a player skill included by the authoritative skill-acquisition policy whose cap is positive for at least one held class at the character's current level.

**Production character** means every character except the one local QA fixture named `Monktest`. Production characters follow the value-`1` unlock rule and natural progression. `Monktest` is the sole fixture that may receive an artificial capped-skill grant.

## Architecture decisions

### 1. Server authority is the invariant

The server's held-class mask is the single source of truth. Client modifications make hidden or prematurely rejected actions available for submission; they do not authorize an action. Existing single-class server behavior must remain unchanged.

### 2. Skill seeding is idempotent repair

A single server helper will reconcile unlocked multiclass skills:

1. Read the authoritative held-class mask.
2. For each skill and held class, read the stock skill cap and train level; take the highest current cap and earliest valid unlock level across held classes.
3. Apply the checked-in acquisition policy and its normal race/specialization restrictions.
4. If the current level meets the threshold and the raw stored skill value is `0`, set it to `1`.
5. Never increase a value already above `0`.
6. Never lower a skill.

The acquisition policy is explicit:

- Include level-gated combat, casting, class-ability, specialization, and class tradeskills such as Alchemy, Make Poison, and Research when their stock class/race requirements are satisfied.
- Do not seed languages or universal tradeskills that have no held-class unlock event; they retain stock acquisition.
- Tinkering retains its stock race-only acquisition.
- Preserve stock specialization limits and every other mutually constrained skill rule.
- Maintain a checked-in table covering every `SkillUseTypes` value with its acquisition category, restrictions, and test.

The effective multiclass cap is the highest legal cap across held classes at the character's current level. The helper must never make a non-held class eligible and must remain safe to call repeatedly.

Run the helper:

- after the multiclass mask is loaded on login/zone entry, to repair characters missed by an older hook;
- immediately after a class is adopted and the mask is refreshed;
- after a level increase.

The legacy Perl helper that maximizes multiclass skills must be removed or changed so it cannot violate this policy. The active Lua level-up path must stop relying on base-class-only `MaxSkill` checks.

Class release must run the existing purge/reconciliation path and receive explicit tests proving that no capability unique to the released class remains authorized, while skills shared with a retained class keep their valid value and cap.

### 3. Trainers are optional, not required

The client must permit a trainer session and eligible training requests for any held class. The server continues to reject non-held classes, premature skill levels, values above the effective cap, or invalid training currency/points.

### 4. Player mechanics use held-class capability

Every player-facing base-class branch in the relevant combat, spell, AA, skill, stat, and inventory paths will be classified before it is changed:

- **Additive class capability:** use held-class membership, an eligible skill, or the effective multiclass cap.
- **Shared chassis/client protocol rule:** retain the existing rule unless the client patch contract requires a change.
- **NPC or non-player rule:** retain base-class behavior.
- **Contract mismatch:** block epic closure until the behavior is implemented or the user explicitly changes the product contract.

This audit must cover at least combat-ability dispatch, empty-fist dual wield, weapon damage legality, Monk hand-to-hand and special attacks, class innates/criticals, defensive passives, Bard casting/mobility exceptions, and class-specific activated abilities. Blind global replacement of `GetClass()` is prohibited.

The audit is a checked-in completion artifact. Every discovered gate records file/symbol, player and NPC call paths, classification, remediation or blocking reason, automated evidence, and manual evidence where required. Epic closure requires zero unresolved in-scope rows; ordinary-play class parity cannot be waived as an undocumented or merely documented exception.

### 5. Equipment is submitted permissively and authorized narrowly

The preferred RoF2 patch bypasses only the local class rejection that prevents an equip attempt from reaching the server. Server inventory code then applies the held-class union plus every other stock restriction. Runtime weapon damage and item bonuses must use the same authoritative decision.

If a narrow, exact-build client gate cannot be proven safe during the timeboxed reverse-engineering spike, the fallback is per-character item-class serialization. That fallback must derive the class mask while building packets for one authenticated client; it may not mutate or cache widened global item data. Tests must cover cache isolation, relog, zoning, trade, shared bank, and class-mask adoption/release, while the server independently rejects every non-held-class equip attempt. Global item database widening is not an acceptable fallback. If neither design satisfies those invariants, the equipment portion and epic remain blocked.

### 6. Client patches fail closed

Every RoF2 modification must:

- require the exact supported executable size and SHA-256;
- verify the original bytes/signature at every patch site;
- distinguish parity-critical from optional patches;
- block client startup when a parity-critical patch is disabled or fails validation;
- disable only the affected feature when an optional patch fails;
- emit a useful local log message;
- have an explicit on/off configuration key; parity-critical patches are enabled and required by production configuration;
- be covered by exact-client static verification.

The launcher performs the same on-disk executable and patch-site preflight before Play. The DLL emits a versioned runtime health record and stops before login on parity-critical activation failure. The reverse-engineering spike must identify exact sites for spellbook/discipline regression, combat-ability visibility/dispatch, Skills-window visibility, trainer acceptance, and equipment submission before feature implementation proceeds. Any unresolved required site is a Phase 0 blocker unless a separately specified, server-authoritative fallback is approved in the epic.

### 7. Launcher owns client asset integrity

The branded launcher reuses the existing Wails/Go updater foundation and synchronizes a versioned release manifest. The canonical manifest bytes are signed with Ed25519 by the release pipeline and verified with an embedded public key before any entry is trusted. The release identifier is monotonic; downgrade requires an explicit, separately signed rollback authorization. Key rotation uses a new key certificate signed by an already trusted key. Tampered, unsigned, wrong-key, expired-key, replayed, and unauthorized rollback manifests must all fail closed.

The launcher, updater, and DLL release binaries are Authenticode-signed by the Nightcap release certificate. Signing credentials remain outside the repository and CI logs.

A manifest entry contains:

```json
{
  "path": "dinput8.dll",
  "sha256": "<64 lowercase hex characters>",
  "size": 123,
  "url": "https://...",
  "required": true
}
```

The manifest has a schema version, release identifier, minimum launcher version, complete file inventory, and an explicit tombstone list for retired Nightcap-owned files. Only allowlisted, relative EQ client paths and allowlisted HTTPS release hosts are accepted; absolute paths, traversal, redirects to other hosts, duplicate paths, oversized files/releases, and entries outside the authoritative inventory are rejected.

The authoritative asset inventory is version-controlled and exhaustive for each release. It includes `dinput8.dll`, `spells_us.txt`, `dbstr_us.txt`, every owned `EQUI_*.xml` file, patch configuration, patch-site metadata needed for launcher preflight, and any later required asset. A clean-client test must prove that every inventory row is installed and valid.

Synchronization is transactional at the whole-release level:

1. Refuse mutation while `eqgame.exe` is running.
2. Diff local files by size and SHA-256.
3. Download the complete candidate generation into a release-specific staging directory over HTTPS.
4. Verify its manifest signature, inventory, sizes, and hashes before activation.
5. Write a recovery journal, back up every affected Nightcap-owned path, and replace files using Windows-safe replacement semantics.
6. On any failure or interrupted restart, roll back the entire generation from the journal.
7. Mark the new generation active only after all replacements, tombstones, configuration, and executable preflight succeed.
8. Block Play whenever the active generation is incomplete, mixed, disabled, or invalid.
9. Record repairable, user-readable logs and status without secrets.

The launcher may operate offline only when all required local files match the last trusted cached manifest.

## Delivery phases

### Phase 0 — Baseline and test seams

- Record this contract and the live implementation matrix in epic #10.
- Add focused seams/tests around held-class membership, native unlock level, skill seeding, trainer caps, equipment authorization, and player mechanic gates.
- Create the checked-in class-gate audit and classify every player-facing base-class check using Architecture Decision 4.
- Create a generated class × held-slot × capability acceptance matrix covering every playable class as primary, secondary, and tertiary.
- Timebox the required RoF2 reverse-engineering targets and record addresses, signatures, and call-site evidence.

Exit: the current behavior is reproducible, every audit/matrix row has an owner and evidence requirement, and every exact client patch site is proven or has an approved server-authoritative fallback.

### Phase 1 — Server skill lifecycle and trainers

- Implement idempotent value-`1` skill seeding.
- Invoke it on mask load, class adoption, and level-up.
- retire the production skill-maximizing path.
- Verify natural skill-ups and effective held-class caps.
- Complete server trainer validation for held classes.
- Verify class release purges unique capability without damaging skills shared by retained classes.

Exit: a production multiclass character receives each eligible skill once at its native level, improves naturally, and can optionally train it.

### Phase 2 — Server ability, passive, and equipment parity

- Correct activated ability dispatch to held-class/skill capability.
- Correct empty-fist dual wield for held Monk/Beastlord classes.
- Use authoritative held-class equip legality for player weapon damage and bonuses.
- Complete and remediate the classified base-class gate audit.
- Regression-test spell learning, spellbook population, memorization, casting, hotkeys, discipline listing/activation, AAs, mana/stats, persistence, and single-class behavior across primary, secondary, and tertiary held slots.

Exit: server-side normal play behaves as though each held class is real, without widening authorization to non-held classes.

### Phase 3 — RoF2 client parity

- Verify and preserve spellbook and discipline UI parity.
- Patch combat-ability visibility/dispatch.
- Patch Skills-window visibility.
- Patch trainer acceptance.
- Patch equip-attempt class rejection or implement the documented serialization fallback.
- Add feature configuration, logs, version guards, and exact patch-site tests.

Exit: the supported clean RoF2 client exposes and submits every required action. Launcher preflight and runtime health prove all parity-critical patches are enabled; any required mismatch blocks play safely.

### Phase 4 — Integrated M3 QA

- Snapshot every relevant `Done` character and skill row.
- Create `Monktest` as Human Cleric / Shadowknight / Monk in Plane of Knowledge through an ID-scoped local QA script.
- Use normal progression tests for unlock and natural skill-up behavior, then grant `Monktest` all eligible held-class skills to current caps only for the functional QA pass.
- Run the full matrix below, compare `Done` logically to its snapshot, and perform an interim `dev` → `test` M3 QA promotion with explicit steps.

Exit: automated tests and the generated all-class matrix pass, the user signs off on the interim M3 spike, and all later launcher or hardening changes are understood to require a fresh final `test` promotion and sign-off.

### Phase 5 — Branded launcher and manifest synchronization

- Rebrand/extend the current Wails launcher foundation.
- Add EQ directory detection and selection, manifest diff/repair, atomic replacement, rollback, process guard, status, settings, patch notes, and Play.
- Add Go unit tests and a local-server integration suite for signature/key rotation, rollback prevention, manifest validation, path/host traversal, hashing, whole-generation repair/rollback, offline behavior, and required-file failure.
- Publish launcher and client assets together from the release pipeline.

Exit: a clean supported RoF2 installation can become a valid Nightcap client without manual file copying.

### Phase 6 — Hardening, clean-install acceptance, and release

- Finish DLL configuration/lifecycle hardening and release packaging.
- Validate launcher self-update and a complete release N → N+1 client transition, including changed files, tombstoned files, interruption recovery, and authorized rollback.
- Test clean install, partial/corrupt install, unsupported executable, interrupted download, running-client, offline-valid, and offline-invalid cases.
- Promote `dev` → `test` with an explicit QA spike; promote `test` → `main` only after user sign-off.

Exit: all Definition of Done items pass from a clean installation, a fresh final `dev` → `test` spike receives user sign-off after all code and asset changes, and epic #10 can close.

## `Monktest` QA matrix

`Monktest` is the sole capped-skill QA fixture, not a model for production grants. Preparation uses a repository QA script that requires exact character ID, name, and CLR/SK/MNK class assertions; refuses any non-local database target; takes pre/post snapshots; writes an audit log; and supports rollback. The broad cap grant is not compiled into, installed with, or callable from production game code.

| Character level | Expected newly eligible Monk behavior |
|---:|---|
| 1 | Kick, Mend, dual wield/hand-to-hand behavior supported by stock caps |
| 5 | Round Kick |
| 10 | Block and Tiger Claw |
| 15 | Double Attack |
| 17 | Feign Death |
| 20 | Eagle Strike |
| 25 | Dragon Punch |
| 30 | Flying Kick |
| 50 | Triple Attack |

At every threshold:

1. Verify newly unlocked production skills begin at `1`, not at cap.
2. Verify the skill appears in the client and can be activated where applicable.
3. Verify successful use can improve it and that the effective cap is correct.
4. Verify a Monk trainer opens and can train it without exceeding the cap.
5. Verify Cleric and Shadowknight spells/disciplines/skills still work.

Before the cap grant, prove on `Monktest` or another uncapped production-policy fixture that a skill seeded at `1` increases through successful normal use and optional training without automatic maximization.

Equipment QA must include:

- equipping and using a Monk-only one-handed weapon;
- empty-fist and weapon/offhand dual-wield behavior;
- a Shadowknight-only item;
- item bonuses and nonzero combat damage after equip;
- rejection of an item restricted to a class not held by `Monktest`;
- race, deity, slot, level, and lore restrictions remaining enforced;
- restart/zone/death persistence;
- a stock single-class control and the existing `Pups` caster regression.

The checked-in acceptance matrix covers every playable class in each of the three held slots across spells, disciplines, activated skills, passive/innate mechanics, equipment, trainers, client visibility, persistence, adoption, and release. Deterministic rows require automated evidence. In-game coverage must exercise every class at least once as secondary and once as tertiary, plus representative primary stock controls; no row may remain unresolved at closure.

## Definition of Done

- All automated, static patch-site, integration, and launcher tests pass.
- The class-gate audit and class × slot × capability matrix contain zero unresolved in-scope rows.
- Every ordinary-play in-scope class capability is held-class aware; exceptions are limited to the explicitly excluded product scope.
- A normal character receives eligible skills at value `1` at native levels and never receives automatic skill maximization.
- `Monktest` passes the full in-game matrix, its QA grant is auditable/reversible, and the post-QA `Done` comparison is unchanged.
- Non-held classes and all non-class restrictions remain enforced.
- Exact-client mismatch and individual signature failure are safe, diagnosable, and prevent play when parity-critical.
- A signed launcher release verifies a signed, anti-rollback manifest and installs/repairs one complete asset generation on a clean supported client.
- End-to-end release N → N+1, interrupted update recovery, tombstones, and authorized rollback pass.
- `CHANGES.md`, relevant ADRs, the EQEmu skill notes, milestone report, and GitHub issues reflect the shipped behavior.
- The user signs off on `test` before merge to `main`.

## Issue map

- #10 — living epic and production Definition of Done
- #11 — server multiclass spell eligibility
- #12 — discipline eligibility
- #13 — server/client parity umbrella
- #14 — branded launcher and client asset synchronization
- #15 — hardening and release pipeline
- #36 — `Done` Monk skills/dual wield report
- #38 — held-class equipment report
- #39 — secondary/tertiary trainer report
