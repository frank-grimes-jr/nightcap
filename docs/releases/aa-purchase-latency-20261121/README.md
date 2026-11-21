# AA purchase freeze — November 21, 2026

Owner authorized main and server deployment on November21 (AUTHORIZATION.md).
Candidate built and tested; activation evidence will record installation.
Player acceptance remains OPEN.

The owner reports that the whole game briefly freezes on every AA purchase.
`FinishAlternateAdvancementPurchase` called the full cooldown resynchronization:
100 reset packets followed by active deadlines. The pinned RoF2 receiver at
RVA `0x0b5bd0` tail-calls the AA-window update at `0x209f90` for every packet.
The installed UI hook also fills the class/recommendation columns on each update.
The isolated native executable test counts 100 update calls for the old sweep.
This establishes redundant synchronous UI work, not a measured frame-time claim.

Purchases now use the stable held-class timer map without resetting all slots.
An idle passive purchase sends no timer packets; an idle activated purchase
resets only its own slot. Existing active timers are reprojected with current
rank/haste and their unchanged stored deadlines. A purchased expired family is
explicitly reset. Imitate Death still retires a saved legacy wait and resets its
slot; Quick Buff remains immediately ready. Login, class changes, explicit resets
and bulk grants retain the full reset through the existing no-argument method.

Ownership and wallet transactions, costs, ranks, eligibility, effects and cooldown
durations are unchanged. Success feedback still follows acknowledged persistence.
No SQL, rules, caches, quest, client binary or client-download change is needed.
`client.h` adds only a nonvirtual overload; layout, vtable and existing symbol
remain unchanged. `native.py` asserts that exact header delta, rebuilds the PCH
and full `aa.cpp`, and retains the other authenticated shipping link inputs.

## Evidence

- The new purchase regression failed on unchanged source because it sent 100
  resets. The repaired cooldown suite passes 21 tests, including 46,872 ordered
  family pairs in each of activation/catalog checks and 2,416 rank-pair checks.
- New cases cover passive/activated purchases, expired purchased clocks, positive
  and negative synthetic focus, actual 1500→1200-second rank upgrade, native
  Hastened Rampage effect lookup, zero-reuse AAs and unchanged server deadlines.
- The pinned read-only RoF2 executable harness passes 49 checks. The two new
  checks count 100 versus one AA-window update calls. It does not render a window.
- AA availability: 5,808 purchase cases / 696 class sets and 5,724 packet cases
  pass. Unchanged-rank/cap and all-class bonus controls pass. Recommendation
  testing needs the MSVC environment; the initial shell lacked `cl`, then the
  focused rerun through `vcvars64.bat` passed. Retain both logs.
- Local shipping predecessor `13ad25346d8548b2c2592adafdc7dca2e52be020d836bbf0315a4f0f80ecc6c9`
  reproduced exactly, then the candidate full AA translation unit and link passed.
  Exact source/object/binary/input pins: `build.json`. A relative-path error in
  the first receipt writer was corrected; resume rechecked the reproduced binary
  and sources before compiling the candidate. No server was started or replaced.
- Independent review found no blockers. Requested real rank-change and passive
  haste controls were added and passed. No unrelated catalog or persistence edits.
- `wiki-impact.json` covers all authored guides, Home/Features/commands and
  generated catalogs. Only candidate status/history need changes. Historical
  global source drift remains REVIEW REQUIRED in `wiki-refresh.json`.

## Release and recovery

The November21 preflight capture matches the built native predecessor and has
zero players and6.39GBfree. The release operator binds both compiled source
pins, the immutable candidate image and manifest-approved preflight. Independent
review and10mocked fault tests pass on Windows and Linux. Preserve runtime-file
hashes as well as caches/publication. The game must stop in under70seconds,
before the supervisor's forced-exit boundary. Post-backup headroom must exceed2GiB.

Any uncertainty closes admissions. Only a drained game transition that has not
attempted opening may stop the runtime automatically; a failed drain or possible
admission keeps the game running. `opening.json` distinguishes possible exposure.
Do not replay terminal actions. Inspect actual state and receipts; any recovery
restart needs a fresh clean stop and backup of current player state. An old
database snapshot is never a recovery action. The binary-only prior image is
compatible, but restore it only through the supported controlled maintenance flow.

The candidate is not installed. Build artifacts are retained in the local Docker
container at `/tmp/nightcap-aa-purchase-latency-20261121/`. Before a later release,
compare the actual live binary/source against this pinned predecessor and rebuild
if it changed. Use the supported whole-runtime maintenance release with a fresh
stopped backup and saved-state/market preservation checks. Never kill one
production zone. No client pairing change is required; reconnect after activation.
Recovery uses the previous compatible immutable image, preserving all earned AA
and player data. Do not restore a player snapshot. The old image restores the
purchase refresh overhead. Public wiki publication remains pending.

## Exact in-game QA

Use a test character with earned points in the Arena, or safely in the East
Commonlands tunnel by the Ancient Chronicler. Keep the AA window open and move
or turn while purchasing several affordable ranks of Innate Strength or Natural
Durability. Repeat with Recommended enabled and disabled. Expect no repeated
full-game hitch, one deduction per purchase and immediate rank/point feedback.

With Warrior/Monk held, activate Rampage and Purify Body in the Arena. Buy a
passive rank and, if eligible, Hastened Rampage while those timers run. Both
existing deadlines must continue without resets, new waits or cross-family locks;
the next use receives the newly earned haste normally. Test an activated rank
upgrade and an expired family too. Quick Buff/Imitate Death purchases and repeated
use must retain immediate readiness under their normal eligibility checks.

Relog and verify purchased ranks, wallet, bonuses and remaining cooldowns persist.
On a disposable test build, release/reacquire a class through the Ancient
Chronicler and confirm normal refunds and correct remapped cooldowns. Try an
unaffordable/prerequisite-blocked purchase: no points spent, no rank gained.
Record the character/build, AA names, active timers and whether the visible
freeze is gone. Automated evidence is not acceptance of this player report.
