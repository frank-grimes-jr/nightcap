# Spell selection menu level cache — October 2, 2026

Merged to main and published on OVH October 2 under the owner approval.
Native rendered acceptance remains open.
The owner reports `255 - Elementalkin: Water` in
the spell-gem selection menu, with the correct level after memorization. This
is separate from the October 1 canonical scroll-inspection correction.

## Evidence and accepted behavior

The supplied screenshot shows the nested spell-selection menu. The running
`E:/Nightcap` client is proxy 0.7.3-dev and logs all four prior inspection hooks
as active. Spell 315 is canonically Magician level 2. A read-only process
inspection finds native primary class 11, six cached menu rows, and three cached
255 levels, including spell 315. No memory was written and no client restarted.
Evidence: `E:/EQ_Local_Dev/artifacts/spell-menu-20261002/live-menu-before.json`.

The native builder at RVA `0x248200` walks the 720 spellbook slots and queries
the existing spell-level hook at `0x2482BC`. The insertion routine at `0x247960`
stores `{spell ID, required level}` and sorts on that stored level. The renderer
at `0x247189` formats the cached level using `%02d - %s`; it does not query the
current held-class level. Constructor/visibility/spellbook changes rebuild the
menu, but the class snapshot handler currently does not invalidate it. Thus a
menu built before the snapshot can retain 255 while gem inspection is correct.

After a valid class snapshot, the next safe cast-window frame must rebuild the
native menu using the existing held-class spell-level calculation. Correct both
the visible labels and native level ordering. Repeat after class changes and
zoning. Preserve canonical original-class inspection, native spellbook contents,
memorization/casting permissions, and all newer loot/pet/model repairs.

## Implementation and verification

1. Reproduce the stale cache using the exact native builder, formatter and
   sorting instructions, with the real spell-level hook and identity snapshots.
2. Mark accepted class snapshots and game-state transitions as requiring menu
   refresh. Hook the native cast-window frame at `0x2488A0`; defer until identity,
   the active native profile, spell manager and context-menu manager are ready.
   Reuse the native builder; do not rewrite labels or widen shared spell data.
3. Bind the frame, builder and profile accessor to the signed exact-byte catalog.
   Keep reentrancy guarded, forward every native frame return, and do not swallow
   errors after native menu mutation starts.
4. Verify snapshot ordering, missing/stale identity, class changes, AA messages,
   UI construction and state transitions. Run existing inspection/access and
   native runtime checks, build the DLL and verify launcher catalog agreement.
5. Preserve the latest live assets when signing the follow-up. Verify the normal
   production updater, all public hashes, service preservation and rendered
   menu behavior. Automated fixture checks do not prove native visual acceptance.

## Verified evidence

The independent regression executes the complete 259-byte native builder,
its formatter and sorting branch from the pinned executable. Before the fix,
an accepted snapshot leaves cached levels 255/255/20 while the direct gem query
returns 2. After the fix, labels and descending order are 20/17/02. Coverage
includes all 720 book slots, stale identity, null native globals/profile, a
nonzero virtual-base offset, class changes, zoning/relogin, malformed/duplicate
snapshots, AA updates, reentrant frames and 1,000 unchanged frames. Signature
rejections and the installed 10-byte frame trampoline pass; native mutation
exceptions propagate while the recursion guard is restored. Original-class
inspection remains independent.

The DLL and all native runtime binaries build with warnings as errors. All five
runtime checks, four advanced-loot fixtures, the full Go launcher suite and all
70 exact patch-site checks pass. The old PowerShell verifier assumed every RVA
was in .text; its new bounded PE section lookup also verifies the existing loot
vtables in .rdata. Independent source review found no required changes.

Signed release **2026100202**, proxy **0.7.4-dev**, verifies against the public
key shipped in launcher 0.3.1. All 46 local release files verify; only the DLL
and patch catalog differ from previous live release 2026100201. All 42 gameplay
assets, the helper and config are preserved. The publisher's 12 interruption/drift checks
pass. Local evidence is under `E:/EQ_Local_Dev/artifacts/spell-menu-20261002/`.
The [publisher](spell-menu-20261002/publish.py) checks the current baseline under
the shared deployment lock, retains the old channel and replaces the channel
last. Recovery uses the retained asset contents in a higher-numbered signed
release; never lower the channel counter.

## Approved main and server publication

[PR 116](https://github.com/frank-grimes-jr/nightcap/pull/116) merged at
`1c3cb0d1bb7afbb20dd07cc543f55a506c101d5b`. The promotion is scoped to this
correction on current main; the separate Epic candidate in dev/test is excluded.
The concurrent campfire source and documentation are retained. Publication
waited for that deployment's lock, then recaptured the healthy game/gateway
restart baseline. Public assets and all server image identities were unchanged.

The publisher retained the previous channel and switched to **2026100202**
atomically. All 46 public HTTPS files and the signature verify independently
against the key shipped in launcher 0.3.1. That existing production controller
also installed and verified all 46 files in a fresh isolated fixture without
recovery. No game was launched by that fixture check. All five services retain
their post-campfire IDs, images, start times, restart counts and health; the
desktop channel, starter ZIP and guide remain unchanged. This client correction
requires no database mutation or server restart.

[Checked production evidence](spell-menu-20261002/verification.json). The private
server stage `/opt/nightcap/releases/spell-menu-2026100202/` retains both the
original and post-campfire baselines and the previous channel. If recovery is
needed, publish the retained prior asset contents with a higher release counter.

## Exact owner QA (open)

Close the game and click Play in the ordinary launcher to apply release
**2026100202**. With Necromancer/Magician classes held, open an empty gem's menu and
select Pet > Sum: Water. Elementalkin: Water must read **02 - Elementalkin: Water**,
and its gem must retain level 2 after memorization. Check all available menu
entries, both initial login and after zoning. Shared spells must use the lowest
level among held classes for selection, while scroll inspection still lists
each original class's own level. Check native ordering and ordinary scribing,
memorization and casting restrictions.
