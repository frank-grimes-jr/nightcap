# Cooldown audit and duration corrections — October 17

Status: source candidate; **not deployed**. This follows the owner's report of
Dragon Punch/Round Kick sharing reuse and their request to examine cooldowns
across all classes. The separate six-attack Monk change is PR #218. This audit
starts from its reviewed `64b6e42` candidate, based on main `a59974d`.

The investigation found both duration bugs and timer-identity collisions.
The duration bugs are corrected here. Shared-AA, linked-spell/discipline and
unlinked-item identity collisions remain open, with reproducible evidence below.
This is not a claim that every reported gameplay lockout is fixed.

## Corrected behavior

- Item click cooldowns and Mend subtract reuse reductions in signed arithmetic
  and clamp at zero before entering the unsigned timer API. Previously a
  reduction of 21 seconds from a 20-second item cooldown became 4,294,967,295
  seconds (about 136 years). Mend's analogous excess reduction also wrapped.
- Bash and Frenzy clamp the reduced, haste-adjusted duration before damage and
  timer submission. Their early-return paths previously bypassed the common
  clamp, allowing negative seconds to become similarly enormous unsigned reuse.
- Linked spell completion decodes the signed focus adjustment carried in the
  unsigned millisecond field before division. Both Bard and ordinary completion
  paths preserve negative focus that intentionally adds seconds, and clamp
  excess reductions to zero. The native wire field and packet layout stay intact.
- A zero cooldown means ready. `PersistentTimer::Start(0)` intentionally restarts
  an existing timer's previous duration; it does not replace that duration with
  zero. Linked spell and custom AA/disc completion now clear zero-duration timers.
  Mend, Disarm Traps, Feign Death, Hide and Sense Traps skip a zero-duration start
  after the existing expiry gate. Expired retained timers cannot revive this way.

These changes preserve positive reuse, intended negative focus, haste, ownership,
admission checks and successful-cast rules. Proc/trigger/nonclient guards remain
in place. `GetFocusEffect` actually returns `int64`: an additional hypothesis
about discipline negative-focus arithmetic was disproved by compiling the full
current `UseDiscipline` method. No discipline calculation change was needed.

## Audit coverage and findings

Read-only OVH content capture: **2026-10-17 14:57:44 UTC**, plus timer effects at
15:04:54 UTC. Reviewed 1,570 AA definitions / 6,655 ranks, 18,017 cooldown-related
spell definitions (including 1,545 disciplines), and 7,798 recast item definitions.
The capture includes public content and anonymous saved-timer aggregates, not
character names, inventory, account information or secrets. Exact counts,
fingerprints, selected definitions and limitations are in `catalog-summary.json`.

| Cooldown family | Finding and disposition |
|---|---|
| Basic Monk attacks | Six independent timers in PR #218, requiring its paired server/RoF2 change. Preserved here. |
| Other combat/basic skills | Bash, Frenzy, Mend and four zero-duration skill paths corrected above. Existing positive constants and deliberate shared legacy keys retained. |
| Activated AAs | 17 raw groups are shared by 157 distinct allowed ordinary activated families. Actual activation reproduces Divine Resurrection (18 hours) blocking Divine Stun (30 seconds), and Harm Touch/Lay on Hands blocking each other. Identity fix remains open. |
| Normal spells | Per-spell persistent reuse uses `5000 + spell_id` narrowed to 16 bits; source, focus and completion paths inspected. IDs above 60,535 are a latent namespace hazard. The captured 99,001 Ancient Attunement definition has no learnable class; the active AA uses spell 42,604. Do not call that unused row a live collision. |
| Linked spells | 2,523 definitions use linked groups. Harmshield (199, 600 seconds) and Cannibalize (265, 1.5 seconds) both use group 1. Canonical access permits a held Necromancer/Shaman to learn both by level 23. Source/data overlap confirmed; exact client/gameplay reproduction pending. |
| Disciplines | Battle Cry (5027, 1,800 seconds) and Throw Stone (5225, 10 seconds) both use group 8, including native Berserker access by level 30. Higher groups 11–19 also overlap the older server skill/linked-spell key ranges. Accessibility and native client behavior must be assessed before migration. |
| Grouped item clicks | 6,640 item definitions intentionally use named reuse groups; no cross-domain aliases found for their current group range. Do not split potion/rank/family groups indiscriminately. |
| Unlinked items and augments | 1,158 definitions use `-item_id` narrowed to uint16. Two item-pair groups alias after a 65,536 ID difference; 364 items also have catalog aliases into other cooldown domains. Actual item methods reproduce item/item, item/spell and delete-item/clear-spell defects. Ownership/accessibility of catalog examples is not established. |
| Triggered effects and procs | Ordinary persistent reuse is guarded by `!isproc && !IsFromTriggeredSpell`. Native regression checks preserve those guards. The three catalog SPA390 lockout effects are Suppression of Ice/Fire/Magic, each 2,000 ms; six SPA389 refresh effects deliberately reset matching gems. Those definitions alone do not explain an hours-long lockout. |
| Negative reuse focus | Catalog SPA310 effects include Imposition of Order (-5s), Mind Collapse (-30s), Venomous Sting (-10s). Added time must remain intentional, not wrap or be erased. Linked completion was incorrect; full discipline controls pass unchanged. |
| Timer resets, persistence and utility paths | Reviewed AA/spell/disc resets, item set/get/delete and persistence boundaries. Quest-driven Epic 0.5 has its own 600-second contract plus item cooldown. Existing utility/mercenary keys and encounter/session timers are not a universal shared combat cooldown; no unrelated reset or content policy was changed. |
| Buff duration | Effect lifetime is separate from ability reuse. Existing AA temporary-buff/follow-on regressions were rerun; the October 15 duration/expiry repair remains intact. |

The saved snapshot had only two active groups, each with a 4,320-second duration;
it did not contain a century-long saved timer. That does **not** inspect every
active zone's in-memory timers or prove the reported incident's cause. Native
fixtures establish reachable code defects, not that a particular player hit them.
Current widened SQL spell class columns are not ownership evidence: this audit
uses `common/spell_class_catalog.h` for original learnable classes and levels.

Detailed catalog inventories: `aa-shared-groups.csv`, `item-spell-aliases.csv`,
`item-item-aliases.csv`, and `spell-discipline-groups.csv`. A raw group shared by
multiple definitions is an audit candidate, not automatically an unintended link.

## Tests and remaining identity work

`tools/tests/test_cooldown_duration.py` compiles actual item/Mend/linked-reuse
methods, full `UseDiscipline`, the guarded custom completion block, and four
skill admission/reuse prologs through their first gameplay-effect statement.
It uses the native persistent timer lifecycle from the pinned retained-source
fixture (`common/ptimer.cpp` SHA256
`e62d800263b87439d094ddbda0975caadc6ffcbcb8fb46dc3b34b9f05defbda5`).
Database, time, inventory and downstream gameplay are controlled test boundaries.
All 18 tests / 28 scenarios pass, including the previously failing overflow and
expired-timer cases. The prolog fixtures do not certify trap detection or feign
success. The packet fixture matches native field order and preserves assignments.

`tools/tests/test_monk_combat_reuse.py` now has 16 passing tests: the existing
Monk isolation/expiry/eligibility coverage plus Bash/Frenzy equal/excess reductions
and ordinary/negative-reduction/haste controls. The timer boundary takes the actual
unsigned duration type. Thirty-six zero/excess combinations and thirty-six
positive controls cover native/secondary class and haste variations.

`reproduce_collisions.py` is an **audit diagnostic**, intentionally outside the
passing test suite. It compiles actual AA activation and item timer methods and
the native key declarations. It currently reports **six failures and five passing
controls**, proving the unresolved identity defects. Do not mark these expected
failures green, suppress them, or describe this candidate as fixing them. Run:

```text
python docs/releases/cooldown-audit-20261017/reproduce_collisions.py
```

The follow-up identity change needs stable families and distinct namespaces on
both server and client. Preserve same-ability ranks and reviewed deliberate links
while isolating unrelated abilities. AA timer projection, readiness, resend,
reset and persistence must agree. Spell/disc native client groups are bounded;
server-only key changes will leave client controls locked. Item identity needs a
wider native key and a positive reserved namespace compatible with the existing
24-bit unsigned SQL `timers.type`; simply widening negative item keys to uint32
would overflow that database column. Existing ambiguous saved keys need an
explicit, tested transition; do not delete all timers or guess their origins.

## Build, deployment and player QA

This is an additive source candidate on top of PR #218. Apply its scoped delta to
freshly fingerprinted retained production source, preserving dungeon/journal,
authentication, item receipts, AA duration and intervening releases. Build/link
the complete zone before activation. Full zone compilation remains pending because
the local Docker Linux-engine pipe is unavailable; native fixture compilation is
not a complete deployable binary. No SQL, installed client, cache or runtime was
modified by this audit. Current shared-identity failures remain open.

These duration edits alone require a rebuilt zone, with no new rule, ItemData or
wire layout. The inherited Monk work still requires its matching signed proxy
0.9.2-dev/catalog. Quest or rule reload cannot install C++ changes. OVH native
child exits restart the whole runtime; use the coordinated release procedure.
Main promotion, activation and wiki/client publication require release-specific
authorization. Recover with prior paired binaries and a higher signed client
counter if necessary, preserving earned player state; never restore old player SQL.

After an authorized test release, record character/classes, exact ability/item,
active focus effects, displayed duration and server rejection text. Verify each
fixed action at ordinary, full and excess reduction; repeat after expiry, zone
and reconnect. Check successful, interrupted and rejected casts, both Bard and
ordinary routes, negative focus, and items with augments. Confirm the same action
still obeys positive reuse and procs do not start unrelated timers. Review any
already-corrupted saved timer individually before a separate repair; this patch
does not erase existing player cooldowns or retrospectively identify their cause.

Whole-wiki review, installed skill maintenance, adjacent regression results and
independent review are recorded with this candidate. Candidate wiki notices are
local and unpublished; automated tests are not owner gameplay acceptance.
