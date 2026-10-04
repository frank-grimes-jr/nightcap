# Enchanter weapon twitch: native actor identity follow-up

October 4, 2026. The owner reports that release 2026100404 fixed beetle walking
and death, but the first two Enchanter animation pets still twitch. Their
nameplates stay stationary while their sword/shield move. E:/Nightcap's proxy
hash and startup log confirm the published 0.7.6-dev ran with classic defaults.
This is a failed pet acceptance test, not an installation failure.

## Second native requirement

The first fix restored eqgame's animation-family lookup. EQGraphicsDX9 also
examines the actor name directly at RVA 0x44EA2. IVM and IVF branch to 0x44F76,
skipping automatic animation-controller setup. ZBB (the imported IVM alias)
does not. The skipped path includes a random animation starting position
(0x44F21 calls the CRT rand routine at 0x11060E) and controller setup calls.
Restoring the family name alone cannot preserve this separate actor-name rule.

Pinned graphics SHA256:
ade556b68e98f6f39c5578f70431e11c0b9babcc15b8571eb22cf1e2b654417e.
Read-only native evidence and the failing pre-fix executable are retained in
E:/EQ_Local_Dev/artifacts/enchanter-identity-20261004/.

## Repair and verification scope

Preserve IVM/IVF in RegisterHook instead of substituting an alias. The already
loaded native globals provide the invisible actor and its rig. Race 600 remains native and unchanged; all other aliases, including beetle ZEC and its
spider-family fallback, remain unchanged. The old unused ZBB asset stays in
the package, avoiding an unrelated inventory or archive change.

`model-invisible-native.cpp` hashes the pinned graphics DLL before copying its
31-byte prefix-check block into a private executable buffer. Only the two
outgoing destinations become boolean-return stubs; no renderer initialization,
imports or game process runs. Native IVM/IVF take the exclusion and ZBB does not.
The published RegisterHook fails the regression with:
`registered Enchanter pet must retain native invisible-actor exclusion`.
The repaired registration must pass, alongside remake, modern-mode and beetle
preservation checks. This tests the newly discovered native contract, not
rendered motion or completed player acceptance.

Candidate proxy 0.7.7-dev must ship with its matching signed patch catalog.
No graphics DLL patch, server binary, database or model-asset change is needed.
The owner's main/server live-testing authorization continues to cover this
follow-up; preserve all concurrently published helmet updates in the package.

## Exact live retest

After publication, exit EQ completely and launch through the normal updater.
Confirm proxy 0.7.7-dev in the new startup log. In East Commonlands, summon each
of the first two Enchanter animations. With no target, watch sword/shield and
nameplate for 30 seconds; expect stable idle motion without rapid twitching.
Then test follow, guard, combat and back-off, and repeat after zoning and relog.
Compare the Necromancer skeleton alongside it. Recheck beetle walking/death
to confirm the previous correction remains effective.

Retain the broader NPC/elemental checks in README.md. If the pet still twitches,
record the spell, action and whether both weapons move together. Do not mark
the original goal complete based only on native branch tests.

Recovery is a higher signed release with the prior reviewed proxy/catalog and
all current model assets; never lower the channel or restart unrelated services.
