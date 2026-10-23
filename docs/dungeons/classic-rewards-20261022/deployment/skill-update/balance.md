# Combat and balance knowledge

## Classic dungeon relic budgets — October22 live testing

Owner-authorized main PR293 and paired live deployment are verified. Source
0d61d9b47322 in E:/EQ_Local_Dev/_worktrees/classic-dungeon-options. Exact receipts:
docs/dungeons/classic-rewards-20261022/deployment/. Zone8c9b97d5 preserves the latest
quest-tier matcher after byte-reproducing live6da991b6; world49f87aaf and loader
6b314bf0 are paired with the414-MAGIC cache and12 quest/module files. Signed
game2026102204 remains unchanged. All12 workers,39 schema/497 content checks,
414 cache definitions/888 rejection cases and full-cache preservation pass.
Fresh stopped backup and exact player/custom-state preservation are recorded;
only precisely authenticated native seven-day non-corpse cache expiry is allowed.
Gateway is open. Owner gameplay and solo/multiclass balance acceptance remain open.

Live release 0d61d9b47322 uses reviewed existing dungeon slot/band/quality values for84
new definitions, with equal primary-stat/resist totals. It introduces no raw
power tier, focus, heroics, haste or regen. Planes require46 and earn nine themed
relics, including native SeeInvisible/Invisibility/Levitate utility clicks with
shared quality-family cooldowns. Existing focus reductions and reagent/zone rules
remain; Sky itself forbids Levitate. Numeric budget tests and native cache checks
do not establish solo difficulty or multiclass/pet balance. Record legal spent
AAs, gear, resources, deaths and clear times at each band and46–50 planes during live QA. docs/dungeons/classic-rewards-20261022/{REWARDS.md,QA.md,verification.json}
owns the released budgets and acceptance boundary; source tools/classic_dungeon_rewards.py.


## THJ custom behavior and stock gear — October 19, deployed for live testing

Owner-authorized main promotion PR256/7104c6b and OVH activation are verified in
docs/releases/thj-behaviors-20261019/deployment/. Stage:
/opt/nightcap/releases/thj-behaviors-live-20261019. Matching world/zone/cache loader,
three guarded SQL components and regenerated target caches are installed. Signed
game2026101902 retains proxy0.11.0, its matching catalog and all136 unrelated assets;
all138 hosted files verify with shipped trust. Classic50 and209 starter families
remain. Owner gameplay and balance acceptance remain pending; ../QA.md owns tests.

NightcapTHJBehaviors gates new player/permanent-pet focuses and custom resource
conversions. Five focus types select strongest endpoints; ImprovedDamage/2 use10x,
Mage5915/11064 remain100/150%, Bard outgoing DD stays random10x and DoT stays
unmultiplied. Receiving songs get no focus; base3s songs become2.5s. Keep other
focus limits; supported AoE broadening is documented calibration. Valor pays50%
maxmana once and heals2HP/MP; Harvest restores40%; Burns pay10/20/30/40% and
retain4:1 damage, immunity guard before resource/timer mutation. Native branch
review and focus fixtures are executable; group/raid/client and encounter balance
remain owner QA. Dimensional120s/30min and stun exclusion are calibration.

## Combined THJ item/spell and pet/WPM deployed — October 18, 2026

Source: C:/Users/verre/.codex/worktrees/thj-item-spell-parity/EQ_Local_Dev. Owner-authorized main/OVH deployment is verified in
`docs/releases/thj-parity-20261018/deployment/README.md` and `receipts/`. PR235 promotes the tested source;
signed client2026101802/proxy0.11.0 and wiki20261018-thj-parity-v1 are published
and verified. Classic50 remains active; level65/PoP and389 stock additions stay
staged. Owner gameplay and balance acceptance remain open. Exact testing:
`docs/releases/thj-parity-20261018/QA.md`; measured limitations: `COMPARISON.md`.

Players and eligible permanent pets use additive effective SD for direct
damage/procs and floor(SD/2) per ordinary DoT tick, independent of duration.
Native focus/critical calculations remain; the half-SD critical contribution
uses the native ratio, an explicit Nightcap calibration. Throw Stone stays
single-additive. Hostile NPCs and disabled rules retain the legacy helper.
Clients gain0.1% per heroic INT/WIS on direct damage/healing after modifiers,
before caps. Item-mod opt-outs and reflections are covered. Heroics are
independent of the SD level gate, like focus; no DoT/HoT or owner-heroic transfer.
Both new Spells:NightcapTHJDamageScaling/NightcapHeroicSpellScaling rules default
false; deployed SQL enables them separately. Percentage healing and
HoT splitting remain. Bard runes exclude HA while instruments remain; native
Bard area-DoT dispatch is an explicit uncalibrated exception.

Preserve WPM held-class mitigation/damage/crit/double/triple-attack, six Way of
Steel attacks, earned shield/sustain AAs, independent innate/augment attempts,
Marr received-heal/Mend behavior and sympathetic-heal eligibility. Heroic STR
remains a separate switchable weapon curve. Holy rune230/HHE-338/400ms floor
and fragment magnitudes remain calibration. Shared750 caps retain Hunt headroom;
permanent pets add own SD/HA plus min(half effective owner stat,375), with eligible
earned caster AA transfer. Evaluate the combined item changes, not earlier
pet/WPM encounter results alone. Full matrix/evidence and limits are in COMPARISON.md.

All47 native cases and165 unique regression/migration tests pass. Same-item
controls expose WPM shield DPS+55%, fixed caster DPS-67% and equipped Classic
pet DPS-36%. Low-base spells/ticks gain; the caster controller was not optimized
for additive SD. Maximum-AA WPM kills captured Nagafen in7.1seconds (level50
fixture12.2seconds). Treat rank choice, mana and WPM burst as owner balance gates,
not approved parity or difficulty. Native fixtures enforce Lore/augment rules.

Actual source-method, full-row MariaDB recovery and native tests are separately
recorded in evidence/. Matching world/zone/cache-loader and the signed five-file NCPA2 update over the full138-file inventory are required. Owner RoF2, pack/raid and resource
balance acceptance remain open; no cap/HP-only balancing shortcut is implied.

## Cooldown audit acceptance boundary

October17 candidate2279169 fixes enormous/renewed duration errors across skills,
AA completion and item/spell reuse; it does not intentionally shorten positive
reuse or erase effects that add time. Native18 duration/16 combat tests and
independent review pass, not full zone/gameplay QA. Shared AA/spell/disc/item
identities remain an open design change: separate unrelated abilities while
preserving reviewed rank/family links, then evaluate combined-class throughput.
Catalog overlaps are not proof of current player ownership or observed incidents.
Evidence and source/build pairing: docs/releases/cooldown-audit-20261017/ in the
checkout listed in multiclass.md. Keep the six-Monk attack balance check below.

## Basic Monk reuse - October 17 candidate

The owner chose independent cooldowns for all six basic Monk attacks. The
reviewed candidate preserves damage, haste/AA reuse reductions and Master Wu,
but increases available attack frequency. Evaluate combined Monk/Paladin/earned-AA
damage and survivability after the paired server/client release; regression
checks do not establish balance acceptance. Source/test and deployment boundaries
are in [multiclass](multiclass.md#independent-basic-monk-cooldowns---october-17-candidate)
and `docs/releases/monk-independent-reuse-20261017/README.md`. Candidate b81fd66 is
not deployed; full zone build and actual gameplay remain pending.

## October 17 AA progression review

Passive AA is now 10%, with unchanged 4,000 XP/point; deployment/recovery details
are in multiclass.md. The read-only 14:58 UTC Palwar snapshot is level27
PAL/WAR/MNK, 1,018 spent/80 banked; these are dated saved values, not live telemetry.
Four AA tables still match the October13 fixture. His legal class/prerequisite
pool costs1,673 points:1,015 already legal,658 unbought,578 after banked points.
Three spent points belong to dormant Combat Fury4 (ability30/rank443), preserved
for future policy restoration. Slay9, Wu5 and key healing ranks are already owned.

Review artifact: docs/ops/passive-aa-ten-20261017/REVIEW.md and analysis.json in
C:/Users/verre/.codex/worktrees/passive-aa-ten/EQ_Local_Dev. Utility/stat/resist
depth, incremental Combat Fury/Strikethrough, and shallow Punch Mastery or separate
caster/pet trials are recommendations, not implemented releases. Keep level1
purchase access and canonical ownership. Do not silently unblock dependencies.
Warrior Flurry108 needs disabled Combat Fury309, distinct from enabled family30.
Rapid Strikes273 contributes flurry; inspected native code gates it behind triple
attack. Live skill caps begin Warrior/Monk Triple Attack at46, with ClassicTripleAttack
false. Exact deployed attack.cpp/mob.cpp differ from the tracked copies: verify
their actual path before promising level27 usefulness or claiming a runtime bug.
Punch Mastery1 has flat15/30 inputs; Critical Mend4 jumps30→68. These require
combined low-level/Slay/Wu/cooldown and sustain QA. Neither a large AA total nor
one non-dominant build establishes overall balance. The ideal XP curve is a
conditional pacing illustration, not measured player history or AA/hour.

## Buried Sea AA policy — expanded class ranks deployed October 13

**Every allowed AA and rank is available at character level 1.** Players decide
where and when to spend points. Never restore the rejected character-level gates.
Balance with the release pool, numeric rank ceilings, costs and prerequisites.

Current release evidence is in
`C:/Users/verre/.codex/worktrees/aa-tbs-policy/EQ_Local_Dev/docs/releases/aa-class-ranks-20261013/README.md`.
OVH image `sha256:cf9c62310b746be2bd95d9039e6fb975d00f61aa2c42e76ed86ce823f3f119ff`
runs the reviewed 26-line expansion and Triple Backstab repair. All 12 zones
were verified, including after separate tunnel maintenance restarted the runtime.
Activation preserved 47 player and 11 custom tables; fresh ownership preflight
resolved 242 rows / 1,200 earned ranks. Zero restarts or detected native, quest
or database errors in the recorded checks. Owner gameplay/balance acceptance and
main promotion remain pending; local dev/test contain the implementation.

`era.json` selects `config/aa-policy.json` (classic-tbs-class-ranks-20261013).
The pool is now 394 families / 1,051 ranks, retaining all prior 941 identities.
The 26 reviewed ceilings add 110 ranks: Slay Undead9 (60 points plus Combat Fury3),
Master Wu5, Triple Backstab9 and the exact remaining lines in the audit's
recommended-caps.csv. Most other ordinary families retain a three-rank ceiling.
Four passive dependencies deliberately reopen; Dance of Blades359, Hastened
Blades541 and Abundant Healing516 stay explicitly blocked. High-risk burns,
executes/refills, charged and grant-only veteran families remain deferred.

TBS13 is independent of the Classic world. The same six later exceptions open
at1: Eyes Wide Open938 eight ranks; Diminutive543 one; ENC Pet Discipline3202
one requiring Animation Empathy195 three; Durability3512/Agility3818 three each;
Sturdy1403 one (raw AC). Class/race eligibility, costs and prerequisites remain.
Offers, use, purchase and default grants ignore original DB level_req for clients;
explicit GM GrantAllAAPoints unlock_level remains an optional content filter.
Canonical earned ranks, charges, wallets and spent totals stay saved. Excluded
earned ranks remain dormant; newly legal ranks restore without rebuying. Level
changes no longer shrink the legal prefix. Class release still affects access.

`zone/special_attacks.cpp::Mob::TryBackstab` now permits a client with a positive
legal earned Triple Backstab AA bonus to enter the native double/triple branch
below55. The primary piercing weapon, rear/Seized Opportunity, native double-
attack check, living target and triple roll remain. Item/spell-only bonuses,
bots and no-AA clients retain the old level55 gate; Chaotic frontal minimum hits
retain their previous path. Do not globally lower DoubleBackstabLevelRequirement.
Rank9 contributes45% to the conditional triple roll, not every Backstab attempt.

Source/tests: generated `common/nightcap_aa_policy.h`, config/aa-policy.json,
tools/tests/{test_aa_tbs_policy.py,verify_aa_tbs_native.py,
verify_triple_backstab_native.py,test_aa_class_build.py} and
tools/build_aa_class_ranks_candidate.py. Seven policy tests, 6,306 native rank/
level cases, three restored-Slay ownership/save scenarios, 26 actual TryBackstab
controls, 13 deployment/preflight and seven publication tests pass. Independent
review fixed a manifest omission of versioned libperl.so.5.36.0; all 142 final
link inputs are now recorded and checked. Only the policy header and retained
special_attacks.cpp changed; recompile aa.cpp and special_attacks.cpp against
the exact retained source, preserving prior trainer/offhand and other patches.

Zone rebuild plus guarded whole-runtime refresh is required; normal AA/rule
reload cannot install this policy. No client binary, AA table or global rule
change. Preserve fresh player data during image recovery; never restore old SQL.
Signed notes2026101303 preserve all105 file records and previous patch history.
After an intervening rollout, recapture service identities and reverify the
candidate hashes before publishing notes; never overwrite its unrelated changes.

Combined QA remains essential: Slay amplifies physical skill hits such as kicks,
so test PAL/MNK coupling; pet critical/flurry, distinct double-attack and spell-
critical lines stack across held classes. Poison Mastery's application-time
effect remains a native no-op. Free knight-touch and Hunter's Attack Power ranks
remain deferred as reviewed. Pet HP changes on summon/restore; avoidance/AC reads
current owner bonuses. Catalog ceilings and native tests do not prove fun or
encounter balance. Exact disposable-character and live purchase/reconnect QA is
in the release README. Historical audit analyze.py pins baseline-policy.json so
its 941-rank baseline remains reproducible after the expansion. THJ confirms
Master Wu5/later progression, but its exact Slay cap was not verified; do not
import THJ combat rules, level autogrants or another emulator's catalog.

## Archived THJDI comparison material

October 16 research is retained at
`E:/EQ_Local_Dev/docs/audits/thjdi-archive-20261016/README.md` and
`artifacts/research/thjdi-20261016/` in that checkout. Use its local index,
provenance and pending inventory before requesting the archive again. Homepage
and changelog HTML plus a retained browser observation of 360 zone entries are
available. The first scheduled retry also saved the May 13, 2025 pet directory
(export label April 28, 2025): nine observed class links, no pet statistics.
Use derived/pet-class-directory.csv for those routes; their inherited capture
timestamps are unconfirmed. Capture dates and database-export dates differ.
THJDI identifies as an independent community interface, not an official/current
THJ specification.

The recovered changelog describes item progression/Enchanted/Legendary displays,
summoned-item description variants, waypoints and poison formula presentation.
These are interface notes, not proof of server formulas, summon behavior or
numeric tuning. The second scheduled wake recovered 360 ZEM table rows across
ten expansion groups (292 distinct zone links), captured May 13, 2025 at
20:39:08 UTC and labelled export April 28, 2025. Use derived/zem-values.csv
and .json with their original labels, duplicates, source links and dates.
Displayed ZEM ranges from 2.00 to 3.00; 305 rows show 2.00. In the Vanilla
group, Kedge Keep and Plane of Fear show 2.50, versus 2.00 for the other 77 rows.
The percentage column (e.g. 266% beside 2.00) has an unverified baseline; do
not equate it to a +266% bonus or verified total server XP multiplier. Lower/
higher NPC levels are query-generated 15th/90th percentiles, not curated ranges
or individual NPC statistics; preserve all 17 zero/zero rows without inference.
These historical interface data suggest comparison questions, not current THJ
behavior or Nightcap tuning targets. The direct user-requested item pass then
resolved an observed Unrest zone link through archive availability: its June 20,
2025 capture (export label April 28) supplies 371 distinct loot item listings,
1,203 listed item-to-NPC relationships and 34 NPC stat rows. See derived/
unrest-loot-items.csv, unrest-loot-relations.csv, unrest-npcs.csv and
unrest-recovery.json. NPC data cover level/range, class, HP and five resists;
retain mixed expansion labels and exceptional 100,000-HP entries. Item names/IDs
and acquisition relationships are recovered, but item stats and drop rates are
not. The zone displays XP Modifier 200% versus ZEM-page 2.00 / 266%; do not
invent a common percentage baseline or verified server formula.

The archived /items page is only a POST search form; skip its completed shell.
Dwarven Work Boots /item/3312 returned 404 and availability returned no closest
capture; retain that negative and skip repeat probes without new evidence.
The zone yielded 374 distinct observed item links, allowing concrete future
item targets without guessing IDs. Retry state prioritizes Bloodstained Tunic,
Bloodstained Mantle, Jagged Band and Dusty Bloodstained Gloves; inherited capture
timestamps are unconfirmed. Pet stats and individual item stats remain missing.
Consult current collection status before claiming further recovery.
Preserve its original expansion groupings and variant labels; do not infer
missing IDs from shortened browser links or import this as a current gap list.

The resumable collector makes one request at a time, spaces each host by 30s,
and stops on 429 with at least a five-minute cooldown. The authorized six-hour
heartbeat rotates pets, ZEM, items and NPCs, attempts one target per wake and
tracks backoff/completed targets in retry-state.json. It defers active cooldowns
and backs off a target for 24 hours after three consecutive failures. Follow
recorded links, retain negative lookups, and do not guess IDs. Directory-only
responses are not useful data recoveries and do not trigger notifications.
Metadata availability does not mean content recovery. Offline catalog checks verify saved hashes;
the zone observation has a separate source receipt and 360-row/group checks.
ZEM extraction verified ten headers, 360 six-field rows and observed links,
plus every displayed cell against the saved readable text. The per-wake
receipt is retry-validation-20261017T022147.json in the collection. The manual
item-pass receipt is items-validation-20261017.json: ten NPC columns, three
drop-table columns, numeric fields and observed item/NPC link multisets checked
against raw HTML, with retained-content hashes verified. Scheduled wake limits
remain one target; the direct item request used five serial top-level requests.
This is research only: no reload, paired client, gameplay deployment or player
acceptance. Whole-wiki review found no player-facing impact; broader default-
checkout drift remains separately reported, and no review ledger was advanced.

## THJ forum and player-workbook evidence (2026-10-18)

`E:/EQ_Local_Dev/docs/audits/thj-forum-20261018/README.md` routes the full
152-page, 3,031-post forum capture, original comments and269 attachment
renderings. `SCALING.md` holds28 manually transcribed observations from27
images; `RESOURCES.md` records four recovered public Google resources and
unavailable links. The searchable local archive and source receipts live in
`artifacts/research/thj-forum-20261018/`;313 workbook source rows retain
quality, cell ranges, original values/formulas and missing values. These are
player-maintained, mutable sources, not a server database or implementation.

The owner explicitly maps THJ **Legendary to Nightcap Ascension** for design
comparison. Preserve era, slot, class role, socket state and proc/focus effects.
A same-post Diaku Armor Fragment trio shows normal-to-Enchanted doubling of
AC/HP/mana/ordinary resists, unchanged endurance, and Legendary adding heroic
resists without another ordinary-stat increase. A normal/Legendary Cloak of
the Black Wind pair shows doubled ordinary fields, unchanged endurance,
41% versus62% haste and added heroics/combat stats. These examples do not
establish a universal tier-generation or rounding formula.

The pet workbook `Testing Data!B2` reports no extra inherited pet spell damage
above the owner's750 SD cap; distinguish this scoped player test from pet
gear caps and engine proof. `Luclin Mage Pet Gear!D1` explicitly uses an
equip bug; exclude that configuration from legal Nightcap baselines. Keep
test-server epics, ghost-augment reports, buffed character totals and revised
capstones separate from ordinary clean item screenshots. Documents include
later NMS revisions, so their capture date is not their forum-link date.

Research recommends measuring whole-build item progression, legal pet/owner
inheritance, forced-proc sustain, first-character AA pacing and encounter
resource pressure. It authorizes no feature or tuning change. Do not infer
current Nightcap gaps from forum complaints alone. The owner-requested parity
comparison below supplies the newer, source-specific design direction.
`verify_research.py` validates post continuity, loaded images, source cells,
one screenshot/workbook cross-check, local links and hashes. Browser search
was checked locally. No reload/client pairing, deployment or gameplay QA;
wiki impact is internal research only with no public publication or ledger
advancement. Existing THJDI recovery remains separately scoped.

## Nightcap versus THJ parity comparison (2026-10-18)

The owner now explicitly requests the closest practical item/spell scaling match
and is willing to change Nightcap systems. Use the dated comparison at
`E:/EQ_Local_Dev/docs/audits/thj-nightcap-comparison-20261018/README.md`, not a
blanket multiplier or old THJ blueprint. This direction is not deployment authority.

Read-only production captures at22:08/22:12 UTC retain zone29b80931 and eight
verified deployed combat source fingerprints. The crosswalk resolves122 explicit
Legendary workbook observations and22 Legendary screenshots; unlabelled rows,
ambiguous IDs, augmented examples and revised capstones retain their boundaries.
All122 recorded workbook AC values match; positive heroic INT94/98 and WIS86/88
match. Clean Luclin pools are commonly2.4x normal here versus2x THJ, while six
weapon damage comparisons are below THJ with unchanged delay. Do not double
already-matching AC/heroics. Generic20/20 SD/HA is both too high and too low
depending on item. Use exact, sourced per-item fields, including reductions.

The frozen pet candidate changes33 definitions and improves workbook SD matches
12->30 of120; it does not change the screenshot cohort, weapon ratios or the
percentage formula. Its750 caps and bounded half-owner inheritance are useful
components, not parity proof. The same chat's WPM completion is active/planned
for melee AAs, heroic STR, held-class combat and named effects; final afterimages
must be rechecked. The separate starter/dungeon candidate has zero overlap with
these reference families and preserves an explicit low-power starter exception.
All remain undeployed at this snapshot. See input-manifest.json and input-drift.json
in `artifacts/research/thj-nightcap-comparison-20261018/`.

THJ forum post713 (January6,2025) reports191 SD yielding20->211 initial damage,
8->103 and5->100 DoT ticks with no AAs. Deployed Nightcap gives58,9,5 in the
isolated equivalent inputs: percentage bonus plus duration-split DoT contribution.
Actual retained C++ helper/DoT methods pass72 local fixture cases. Consider an
explicit additive direct-damage policy and separate half-SD noncritical DoT
contribution; simply raising250->750 or disabling duration splitting fails this
reference. Do not silently switch healing/runes through the shared helper.
Critical weighting and heal/HoT/rune coefficients need separate evidence; the
pet fragment magnitudes are Nightcap calibration. March26 post2103 reports a
Bard-rune scaling nerf. Throw Stone's existing additive exception needs coverage.
Historical heroic INT/WIS prose specifies0.1% direct spell benefit excluding
DoTs/HoTs; converting heroics into capped item SD/HA is not equivalent.

Comparison JSON/CSV preserves source cells, IDs and candidate deltas. Native
formula cases are not full encounters or THJ engine proof. Implementation must
pair changed rules with world/zone, refresh matched caches/client spell data,
preserve earned inventories/AA/augments, and run legal whole-build and owner QA.
This audit changes no gameplay or public wiki and requires no reload/client
release; wiki impact is internal research with no publication/ledger advancement.

## Source routes

- `server-mods/code/zone/effects.cpp::GetExtraSpellAmt`: Nightcap flat/percent mode returns percentage-of-base scaling. At eligible 250 bonus, the simplified base-plus-bonus is 3.5x, not +250 damage and not a universal final-output multiplier. Exclusions, focus/criticals and DoT/HoT tick splitting still apply.
- Throw Stone spell 5225 has a specific direct additive nonnegative capped Spell Damage branch for client/bot/merc: base 1 + 250 gives 251 before downstream modifiers. It respects the explicit opt-out; NPC/reflection behavior remains distinct. `docs/releases/throw-stone-20261009.md` and its production-method regression.
- Hunt augment cap headroom is restricted to qualifying socketed items at level 50: at most +30, independently for effective heroic INT/WIS. Increasing cap doesn't create raw Spell Damage/Heal Amount. `zone/zone_hunt.cpp`, `common/zone_hunt_policy.h`, native cap fixture and `docs/releases/zone-loot-20261009/BALANCE.md`.
- Held-class HP/mana, monk weapon damage/skills, pet ownership/order routing and direct-AA buff lifetime have separate native controls. Read the source relevant to the effect, rather than reproducing the entire combat engine in Python.

## Reuse the diagnostic stack

`tools/balance/README.md` indexes the standard-library Python tools and native oracles. `baseline.py` compares active source/rules and rejects false-zero C++ runner results. Snapshot/manifest hashes pin content. Formula/resource oracles extract actual C++ methods; the native encounter harness uses real engine objects with explicit fixture/network boundaries. A fake transport test is not end-to-end gameplay.

Useful paths: `tools/balance/verify_cpp.py`, `verify_resources_cpp.py`, `native_runtime.cpp`, `native_harness.cpp`, `encounter_cli.py`, `aa_policy_preflight.py`, `aa_policy_projection.py`, `gear_candidates.py`, plus `docs/balance/` experiment reports. Native controls require the documented isolated database/source; inspect commands before executing fixtures. Don't run the entire suite for a narrow documentation/UI change.

Use legal acquisition, class/race/slot/socket restrictions and actual spent AA points. Compare held builds at equal recorded inputs and multiple progression stages. A curated pool may exhaust below the requested point budget; don't silently fill with unrestricted abilities. The old unrestricted stress ceiling isn't a Classic release target. Dated September cap comparisons retained 250/250 because pet gains weren't consistent and caster outcomes changed; later hunt headroom is a different scoped mechanic.

## Evidence limits and known gaps

Owner acceptance is feature-specific: July mana-gauge and held-Monk milestones, Permafrost portal function and the October pet-summon crash report have scoped confirmations. Many deployed systems still have visual or combined-balance QA open. Adventure Journal/Epic 0.5 and portions of combat/item and living-economy work are candidates; old THJ gap-map claims that all pets/upgrades/augments are missing are obsolete.

Historical-document hash tests can fail when their source is rewritten. Preserve historical reports and add follow-ups rather than relabeling old candidate evidence as current acceptance. Use current raw SQL/effective cache/runtime distinctions: FreeTrade and DisableLore deliberately change effective items without rewriting original SQL, so old acquisition/gear assumptions must be reviewed before new balance studies.

Record change inputs, deterministic seeds or sample scope, build/source fingerprints, before/after measurements, rollback and exact owner QA. Never claim that a few synthetic fights establish a population win rate or that automated checks prove fun, visual fidelity or final balance.
