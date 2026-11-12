# Imitate Death without cooldown

Owner request: Monk Imitate Death should have no cooldown. Source candidate based
on current origin/main 423f9c3b. Not deployed or accepted in game.

Family 420 / retained rank 1255 / spell 5918 previously had 1080 seconds base
reuse. `common/imitate_death.h` projects zero reuse for this family on AA load.
`zone/aa.cpp` clears only its old saved deadline during timer resend or authorized
activation and passes zero reuse into ordinary AA casting, including negative
cooldown focus. Native ownership, held-class eligibility, spell effects, casting,
standing and zone/target checks remain. Basic Feign Death skill reuse is unchanged.

RoF2 requires positive advertised reuse to enable Make Hotkey. The packet catalog
advertises one second; every family 420 timer packet uses begin=0/end=now, so the
button is immediately ready. Generic AA details may show the nominal one second.
This reuses the verified Quick Buff wire contract without modifying Quick Buff.

## Verification

The new regression failed against the old implementation because a saved Imitate
Death wait survived resend. `tools/tests/test_aa_cooldown_identity.py` compiles the
actual AA methods and completion packet code with controlled cast/persistence
boundaries. It covers repeated use without clock advance, saved wait removal,
focus values 0/120/-60, unrelated Purify Body reuse and authorization/cast failures.
The broader suite retains pair identity, same-family expiry, reset and relog checks.
`test_cooldown_duration.py` covers adjacent skill/item/discipline timers.

`eq-client-dll/tests/aa-reuse-native.cpp`, run through
`test_quick_buff_hotkey_native.py`, executes the pinned RoF2 hotkey predicate and
timer receiver/readiness instructions in an isolated x86 process: 47 checks pass.
It reads the protected client binary without changing or launching it. Fixtures
do not establish a full Linux zone build or live gameplay/balance acceptance.

## Activation and recovery

This is a zone binary change; AA reload alone cannot install it. No SQL migration,
rule, cache, quest, Client layout, world/shared-memory or signed client change is
required by this patch. Preserve the current native dependencies and deployed
Quick Buff/augment/Last Lantern systems when building. Use the supported guarded
whole-runtime release procedure; never kill one production zone. Deployment and
test-to-main promotion remain pending owner approval under normal branch policy.
Rollback uses the prior verified zone with current player data; never restore a
player snapshot. Already cleared Imitate Death waits are intentionally not restored.

## Exact in-game QA before promotion

1. On a character holding Monk with earned Imitate Death, reconnect in East
   Commonlands. Open AA -> Imitate Death -> Make Hotkey; the control must work.
2. Start combat with an ordinary NPC, activate Imitate Death and confirm its
   existing feign/aggro behavior. Stand normally and repeat immediately. No
   ability reuse countdown or server cooldown rejection should appear. Ordinary
   casting/recovery and standing rules still apply.
3. With a pre-update saved Imitate Death wait, reconnect and repeat step 2: the old
   18-minute wait must not block use. Zone and relog; it must remain ready.
4. Activate earned Purify Body, then Imitate Death. Purify Body must keep its own
   wait. Check basic Feign Death still uses its own unchanged skill reuse.
5. Test a secondary/tertiary Monk character. Release Monk or use a character that
   has not earned Imitate Death: activation must be unavailable. Verify Quick
   Buff still creates a hotkey and follows its existing mana/readiness rules.
6. Assess repeated aggro escape against representative solo/multiclass encounters;
   record success/failure, NPC reset behavior and balance separately from UI QA.

Wiki impact review: `wiki-review.json`. Local candidate prose is not publication.
