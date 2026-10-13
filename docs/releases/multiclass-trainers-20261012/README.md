# Multiclass trainers — October 12, 2026 release

Owner-approved PR #189 is merged to main at `7df224d` and deployed to OVH,
paired with signed client release **2026101204**. Palwar can use the new
held-class trainer paths by hailing or right-clicking Joren in East Commonlands.
Training still uses existing points and coins; primary class remains Paladin.
Visible trainer access, spending and relog acceptance remain pending owner QA.

## Cause and verified production facts

The October 12 read-only probe (01:15:19 UTC October 13) found Palwar, character
29, at level 4 with 20 training points, primary Paladin (3), class2 Warrior (1),
and class3 Monk (7). Joren (999656) is correctly class 26, a Monk guildmaster.
Garran (999650) is class 20; Aldric (999652) is class 22. Cross-class trainers
are disabled, which is correct: held-class authorization is separate from
allowing arbitrary classes. No Joren ID/name quest or default hail script is
installed; global_npc.lua only handles seasonal spawn appearances.

The native server already authorizes held-class trainers in `OPGMTraining`,
`OPGMTrainSkill` and `OPGMEndTraining`. RoF2's earlier right-click comparison
uses only the profile's primary class. Even if a window opens, its list,
button, display and purchase validation query primary-class skill tables.
Existing server policy/source tests could not catch those client gates.

## Change and limits

- `Client::CheckTrainerHail` accepts `hail` or the native `Hail, Name` greeting
  for a visible, unengaged trainer and delegates to `OPGMTraining`. The normal
  held-class and 3D-distance checks and current-level caps remain authoritative.
  It joins the existing targeted say/hail dispatch; no quest installation or
  broad default NPC script is needed. Invalid open packets no longer leak the
  copied response packet.
- Proxy `0.8.2-dev` projects an eligible trainer's class only at the right-click
  comparison. It never changes the profile. Trainer-only native calls use the
  highest held-class cap and lowest positive unlock level. Current server
  identity and primary class must match; missing/stale metadata retains stock
  behavior. The server still owns purchases, membership, points, money and caps.
- Exact guarded sites: class comparison RVA `0x1374AC`; cap calls `0x185890`,
  `0x381EE4`, `0x38201F`; level calls `0x18590B`, `0x381811`, `0x381F29`,
  `0x381F6B`, `0x3824E6`. Native accessor entries are independently guarded.
  The bridge preserves ECX/EDX and stack cleanup. Required `class_ui` startup
  fails closed if installation fails.
- No skill points, caps, class slots, coins or database rules are granted or
  rewritten. Normal skill advancement and balance remain unchanged.

## Build, pairing and recovery

Pair the rebuilt zone with the candidate proxy and generated signed patch
catalog. A rule or quest reload cannot install either change. The server-only
hail path does not fix the old client's skill-list/purchase restrictions.
The protected RoF2 executable is a read-only test input and stays unchanged.
This branch started at `4e3acd8` and now integrates main `ffaba1b`, including
early scribing and launcher patch history. Reconcile any newly promoted changes
before publication; do not overwrite another candidate or live release.

Imported early-scribing deployment receipts on main record server image
`sha256:058330bce1e2539612d705b95b726d5143daa7ca5e6897debe0f598ba470558f`
and signed client release 2026101203. The v2 trainer build already includes
those native/client source changes; this latest merge adds deployment evidence
and updates the patch-history packaging test. The full launcher `go test ./...`
suite passes using cached Go 1.27.2 with normal Windows permissions.

The live game image observed during diagnosis was
`sha256:4c0f464d64b6eb5dc787aaff380f4fbee41f2de8365e2622cb5fcc11cb940541`.
`tools/build_trainer_candidate.py` builds in a separate local container directory
against its retained sell-all source and fingerprinted objects. Main's single-
argument `MaxSkill` union differs from that release's primary-class inline
overload; the trainer additions and approved early-scribing changes are staged onto
retained source. That
unrelated difference is explicitly preserved, not silently promoted or removed.
The candidate adds no fields or virtual methods; only the three changed native
translation units require recompilation, without a stale precompiled header.

The owner explicitly approved main and server deployment. The reviewed operator
at `/opt/nightcap/releases/multiclass-trainers-20261012` layered only zone onto
the observed early-scribing image. New immutable image:
`sha256:1eef609e4daed95ad84fcbd193e56c0f7abbefedf325813f58316be5da558578`.
A fresh gzip-verified SQL backup preceded the closed-gateway graceful whole-game
restart. All 12 running zones match the candidate hash; 47 player tables and
11 custom tables passed stopped-state preservation checks. Rules, content,
quests/plugins and supporting DB/web/tunnel services were preserved. Access
reopened with zero restarts and no detected native, quest or database errors.
No SQL was restored. See [server receipt](server-receipt.json) and
[final health](final-health.json).

Signed game release **2026101204** publishes proxy 0.8.2-dev and the 87-site
catalog. DLL/catalog are the only changed assets among 105 files. Existing
patch history, minimum launcher 0.6.0, desktop channel, starter ZIP and guide
are preserved. Publisher service identities were captured after the restart;
all five services remained unchanged by publication. Public HTTPS verification
checks the shipped-key signature and every size/hash. See
[client receipt](client-receipt.json) and [hosted verification](hosted-verification.json).
The game channel expires November 12 UTC. Close EQ and use launcher Play to
receive the paired client; old clients retain their primary-class restrictions.

The exact reviewed operators and tests are retained under `deployment/`.
Nine native recovery tests and twelve publisher recovery tests pass. These are
release-specific records, not instructions to replay activation. Native reports
finish before client publication because they pin the previous public channel;
final health checks use the post-publication state. For a future deployment,
recheck live image, source and signed channel before staging. Never kill one
production zone: its supervisor restarts the whole runtime.

Rollback selects the freshly captured prior server image and republishes prior
client bytes with a higher signed game release counter. Preserve all skill,
currency, training-point and player progress earned after activation; do not
restore a player/database snapshot. No database migration is part of this fix.

## Verification and exact player QA

Automated evidence is recorded in `verification.json`. Regression entrypoints:
`tools/tests/test_trainer_hail.py`, existing multiclass trainer/skill lifecycle
PowerShell checks, `eq-client-dll/tests/trainer-native.cpp`, and the client runtime
suite with an explicit `--eqgame` path. The exact native test first failed on
stock RoF2 at Joren, then passed the patched comparison and real native skill
accessors, including repeated ABI, release and stale-identity controls. Synthetic
skill tables exercise native code, not actual Palwar skill values or gameplay.

Owner QA after the paired release:

1. Close EQ, update through launcher Play, log into Palwar and travel to East
   Commonlands. Record level, class slots, practice points, wallet and selected
   skill values. Primary Paladin must remain unchanged.
2. Stand beside Joren (Monk Trainer, NPC 999656; compact roster `/loc -1662,-349`).
   Right-click: the normal training window opens. Close it, target Joren and
   hail: the same window opens. Repeat at Garran (Warrior Trainer, 999650)
   and Aldric (Paladin Trainer, 999652).
3. Train one currently eligible, non-maxed skill (for example a shown Monk
   skill such as Mend when below its current cap). Exactly one practice point
   and the native quoted coin cost are consumed; skill increases by one, or
   starts at one if previously zero. Stop at the current-level cap. Future-level
   Monk skills must remain unavailable; no max-level grant occurs.
4. Try Elowen (Cleric Trainer, 999651), whom Palwar does not hold, and a distant
   trainer. Neither should grant access. Ordinary merchants and NPC hails still
   work. On a disposable QA character, also test zero points, insufficient funds,
   class release/re-adoption and non-Gnome Tinkering rejection.
5. Zone, camp and relog. Verify trained values, spent points/coins and all three
   class slots persist. Reopen each held-class trainer. Check client logs for
   required patch failures and server logs for new quest/native errors.

These steps remain pending until the owner reports the visible results.
