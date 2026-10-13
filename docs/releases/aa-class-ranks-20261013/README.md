# Class AA depth and Triple Backstab — October 13, 2026

The owner authorized implementation, signed patch notes and OVH deployment for
in-game QA. This is not gameplay acceptance or permission to promote to main.
Status: built and native-tested; deployment receipts will record activation.

## Behavior

Implements the [26 reviewed AA lines](../../audits/aa-class-ranks-20261013/recommended-caps.csv)
exactly: 394 families / 1,051 legal ranks, an increase of 110 ranks. Slay Undead
now reaches 9, Master Wu 5, and Triple Backstab 9. All 941 previously legal ranks
remain legal. Every allowed rank is available at level 1, with existing class/race
eligibility, costs, prerequisite ranks and the same six later-era exceptions.
Dance of Blades, Hastened Blades and Abundant Healing retain their previous
blocked state; the four reviewed passive dependencies reopen deliberately.
There are no new character-level gates, refunds, point grants or catalog edits.

The retained `Mob::TryBackstab` required level 55 to reach the triple roll, above
Nightcap's maximum 50. A client with a positive, legal earned Triple Backstab AA
bonus now enters that branch at any level. It still requires a primary piercing
weapon, rear position or successful Seized Opportunity, a successful native
double-attack check, a living target and the triple roll. Chaotic Stab retains
its minimum-damage frontal behavior. Item/spell bonuses alone, bots and clients
without the AA keep their previous level requirement. No global combat rule changes.

Canonical purchases and charges stay saved, including excluded higher ranks.
Newly legal earned ranks reactivate on reconnect without rebuying them. Unspent
points and spent accounting remain based on earned purchases, not the usable
projection. This release changes only the compiled policy and native backstab
gate; it does not rewrite AA tables or player records.

## Proof and build provenance

- Seven policy tests pass: exact audited pool, all ranks at 1 even with database
  requirements set to 255, preserved old rank identities, dependencies and deferrals.
- The native AA harness passes 6,306 rank/level cases, existing projection/save/
  charge controls, and three restored Slay purchase/save scenarios. An earned
  rank 10 stays saved while the legal rank 9 becomes usable; duplicate buying is
  rejected, actual seven-point rank-9 cost and Combat Fury prerequisites remain.
- The actual native TryBackstab method passes 26 deterministic cases: level 1/50,
  first/ninth-rank bonuses, no-AA and item/spell-only controls, bots, legacy level55,
  double/triple roll failures, target death, piercing weapons, rear/front/Chaotic/
  Seized Opportunity paths. The previous native source failed the level-1 case.
- Ten activation/recovery, three catalog/ownership preflight, seven notes-only
  publication tests, and a versioned-library fingerprint regression pass.
- Source is the retained live level-1 build. Only `common/nightcap_aa_policy.h`
  and `zone/special_attacks.cpp` differ. The latter is introduced into the tracked
  overlay from that exact retained file; all other bytes are unchanged.
  Recompile `aa.cpp` (the sole policy-header consumer) and `special_attacks.cpp`
  without stale PCH; preserve other objects and all 142 final link inputs.
  Prior source, binary and link inputs are checked before/after compilation.

Zone SHA-256: `5dfe3d8a944a29ac963644298eb7a1563a08748ae72ae210edd78268ea106681`.
See [build manifest](build-manifest.json), [native AA](native-aa.json),
[native backstab](native-backstab.json), and [manifest completeness](manifest-review.json).

The first expanded ownership test used an inconsistent spent baseline; corrected
it to 69 Slay + 12 Combat Fury + 5 expended = 86 points. No gameplay code changed
for that test correction. Independent review found a versioned Perl library
omitted from the new manifest filter. The builder and regression now retain it;
the finished build was rechecked and its metadata completed without changing the
binary. Current and prior checks both verified that library's exact hash.

## Deployment, publication and recovery

The guarded operator checks the freshly captured OVH base binary hashes and
complete AA catalog, tests candidate/rollback native startup and crypto contracts,
and takes a fresh verified database backup. Under deployment and GM locks it
closes the gateway, gracefully stops the whole game runtime, fingerprints current
player/custom tables, selects the immutable zone-only image, verifies all 12
zones and preserved data, and reopens access. No SQL is restored. The prior image
is retained for recovery; after any player access, recovery must preserve new
activity. Persistent closed-state data drift keeps the gateway closed.

Only a zone rebuild/restart is required. Normal AA/rule reload cannot install
the compiled policy. World, login, client binaries, assets and rules are retained.
Signed game metadata 2026101303 adds the rank expansion, Triple Backstab and
purchase-preservation notes while preserving all 105 complete file records,
previous history, desktop channel, starter and guide. Publish only after the
native release verifies; take a new service baseline for notes publication.
No client downloads or additional restart are required for notes alone.

If another runtime or metadata release intervenes, the preflight fails closed.
Reconcile that release before retrying; never replace it with an old baseline.
Later metadata recovery must use a higher signed counter.

## Exact in-game QA

1. Close EQ, reopen the normal launcher shortcut and check the latest notes for
   the expanded class AA ranks and Triple Backstab correction. Enter East
   Commonlands on an existing character; record unspent/spent points and existing
   ownership before buying anything. Newly legal ranks already bought should
   be usable without another purchase. Camp/reconnect and zone to North Ro;
   ownership and point totals should persist.
2. On disposable level-1 PAL/WAR/MNK, ROG/RNG/WAR, MAG/BST/NEC and caster/healer
   controls, earn or explicitly GM-grant only the test points you intend to spend.
   Inspect General/Archetype/Class tabs. Buy the reviewed AA lines to their listed
   ceilings at level 1. Slay requires Combat Fury3 and costs 60 points for its own
   nine ranks. Test normal deductions, missing-prerequisite rejection and inability
   to buy the excluded next rank. Never grant points to a normal player character
   merely to perform this check.
3. For Triple Backstab, use a Rogue-held character with a primary 1H piercing
   weapon and trained Backstab/Double Attack against a durable rear-facing target
   in East Commonlands. At level 1 and again 50, compare no AA, rank1 and rank9
   over many attempts. Successful double attacks can now generate a third stab;
   rank9's AA contribution is 45%. A single attempt need not proc. A non-piercing
   weapon must reject Backstab; ordinary frontal attacks and Chaotic Stab must
   retain their existing restrictions. Repeat with Rogue as a secondary class.
4. At appropriate progression, test Slay1/3/6/9 against undead in Unrest and
   Lower Guk, then living enemies as controls. Record weapon, Kick Mastery,
   Master Wu, gear, spent AA, kill time and resource use. Physical skill attacks
   can also feed Slay; watch PAL/MNK synergy and repeat-pull speed.
5. Test MAG/BST/NEC pet criticals with each controlled pet; resummon when checking
   summon-time stats. Test BRD/BST double attacks, WIZ plus Fury of Magic, and
   CLR/SHD/SHM healing/procs as combined builds. Record survival, burst, mana and
   recovery; native/unit checks do not establish balanced encounters or fun.
6. On disposable controls, change level 1 → 50 → 1 without changing classes:
   every allowed AA rank remains available and owned legal ranks remain usable.
   Class release/reselection must retain canonical ownership/refund behavior.
   Keep excluded burn/execute families dormant and confirm no purchase disappears.

Owner acceptance and combined encounter balance remain pending.
