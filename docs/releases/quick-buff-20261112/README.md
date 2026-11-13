# Quick Buff native Make Hotkey follow-up

The owner reported v1 **Make Hotkey disabled on Palwar**, who owns rank3. This is a confirmed manual QA failure, not an ownership problem. Follow-up `hotkey-fix/` (PR423/60d51362, zone3eeb72c9) is deployed with access restored; remaining gameplay/balance QA stays OPEN.

The pinned RoF2 executable disables creation when base reuse<=0 (native gate0x6081E4, ability+0x64). The authoritative rank retains zero reuse; only family48 packet presentation uses1. Every family48 timer packet is a reset `(begin0,end=current time)`, so no one-second deadline exists. Generic native AA detail may show nominal1second; actual readiness is immediate. No new client download or AA grant.

The exact native gate/receiver fixture failed against the old metadata and passes36checks after correction. AA identity17tests and follow-up rollout9fault tests pass; fresh-context native-path review has no blocker. `hotkey-fix/native-build.json` reproduces the deployed full-build zone1fe268a1, compiles only AA/spells against an isolated source clone, pins unchanged link inputs and Client layout, and produces zone3eeb72c9. The original full-build requirement remains for the v1 Client member change; this follow-up starts from that completed build.

After deployment, relog Palwar, select Quick Buff in the AA window, verify **Make Hotkey** enables, place it on a bar, then activate with sufficient mana and eligible memorized buffs. Confirm one50% maximum-mana debit, immediate buffs, no cooldown; restore mana and repeat immediately. Verify ordinary AA timers remain independent. Native UI/gameplay acceptance remains OPEN until owner testing.

# Quick Buff activated AA — deployed for live QA, November 12, 2026

Requested and confirmed by the owner: an AA hotkey immediately casts the buffs
memorized on the player's spell bar, costs 50% of **maximum** mana once per
activation, targets the caster, retains normal group/pet delivery, and has no
reuse delay. The initial paired release is main PR422/a2ae50f0; the Make Hotkey follow-up is PR423/60d51362. All12zone workers now run3eeb72c9 with admissions open; world/shared_memory retain the augment-icon repair. Signed client2026111201 remains unchanged, and wiki20261112-quick-buff-v2 is published and verified. Native visible hotkey/delivery and balance acceptance remain open.

## Implementation and decisions

- Family 48, ranks 147–149 retain their earned ownership, costs, prerequisites
  and class masks. Every existing rank activates the same behavior. The old
  passive buff-casting haste is removed from the loaded AA graph.
- `common/quick_buff.h` applies the runtime AA metadata projection on load or
  reload. Type 3, no passive effects, server reuse0, wire-only reuse1, and string147
  hotkey labels enable the native AA window's Make Hotkey action. Every own
  timer packet is a reset, retaining immediate readiness. Existing instant self spell
  8 is solely a RoF2 presentation marker; Quick Buff never casts Cleanse.
- `zone/aa.cpp` dispatches after earned-state, rank/class, charge and native-slot
  checks. Family 48 never consults a cooldown. Other AA timers are unchanged.
- `zone/aa_quick_buff.inc` snapshots and deduplicates the memorized spell IDs in
  gem order, filters to beneficial duration buffs, requires scribing, held-class
  ownership and current level, and checks native caster/zone/target restrictions.
  Pet-only buffs require a pet. Instant heals, attacks, ordinary summons and
  travel spells are excluded by the buff classification; disciplines are excluded.
- Mana cost is floor(maximum / 2), at least one mana for a positive pool. No
  eligible buffs or insufficient mana costs nothing. Eligible activation debits
  once before callbacks, independent of per-spell focus or group recipient count.
  Reentry, death, unconsciousness and existing casting/recovery block activation.
- Each buff runs the native instant `CastSpell`/`CastedSpellFinished` path with
  zero individual mana and a zero-duration family timer. Reagents, stacking,
  target permissions/range, events and group/pet delivery remain native. A buff
  rejected at completion (for example missing reagents or stacking) does not
  refund the activation cost or abort the remaining buff attempts.
- Only an active Quick Buff cast bypasses the memorized spell's reuse check and
  the ten-millisecond inter-cast recovery. Existing spell/discipline/item/other AA
  deadlines are preserved. Successful consecutive activations are immediate.

Alternatives: queued ordinary casts would fail the immediate/no-delay intent;
direct buff installation would bypass native reagents and delivery. A SQL rewrite
would introduce a separate content/cache migration for metadata the zone can
project without altering saved purchases. Runtime projection is used here.

## Verification and release boundary

`tools/tests/test_quick_buff.py` compiles the actual dispatcher and metadata
projection with explicit spell, inventory and transport boundaries; it also
checks a scoped, repeatable client string delta. The added cooldown-suite scenario
compiles the actual activation and AA packet methods, verifies unearned and
released-class rejection and confirms active hotkey metadata with zero reuse.
The existing suite checks independent families, resets, relog and exact deadlines.
The adjacent gameplay-policy fixture previously failed to compile even on the
unchanged baseline because it omitted the existing THJ duration header/rule gate.
The fixture now includes that dependency with the deployed rule enabled; its
original spell/death assertions pass. Baseline failure evidence is retained in
`baseline-fixture-failure.txt`. `verification.json` records the final check counts.

`native-compile.json` records successful complete `aa.cpp` and `spells.cpp` syntax
checks against an isolated November 7 retained source snapshot. The baseline
versions of all three modified existing files exactly matched task HEAD before
overlay. Those initial syntax checks are separate from the completed full zone link and production verification in full-build.json and production-verification.json. The new Client member required a **full zone rebuild**, not a retained-object two-file relink.

No database, rule, spell cache, quests, signed DLL or reference client was changed.
This release built the full zone against the authenticated current native baseline, reran focused checks and published signed `dbstr_us.txt` using `tools/quick_buff_client.py` and the existing authenticated client-delivery flow. For future changes, retain that same source/pairing discipline. Do not
reuse an old full client manifest. No new spell asset is needed. Fully exit EQ
and use launcher Play for the paired text update. The server binary must load the
new AA graph; AA reload alone cannot install the C++ behavior. Production requires
the supported whole-runtime release procedure; never kill one zone worker.

Follow feature → dev automated verification → test manual QA → main after fresh
owner sign-off. For this release the owner explicitly authorized main/live QA before manual acceptance; server, signed client and wiki are now deployed and verified. Future releases retain the default branch policy.
Rollback uses a compatible prior full zone build and restores the scoped client
text through a newer signed release. Keep earned/player state; never restore a
player snapshot. No SQL rollback or AA refund is needed.

## November 12 live-release preparation

The owner explicitly requested: “Build it and deploy it to the live server so I
can test the Quick Buff hotkey in game.” This authorizes this release's main/live
QA promotion before manual acceptance; it does not change future branch policy.
The owner confirmed logged out and declined an optional cross-model review.
A fresh-context source/operator review found one Bard instrument issue, now fixed
and covered by the actual extracted native reagent branch. Eight operator fault
checks and twenty publisher recovery checks pass on Linux without skips.

Fresh production probe identifies the newer augment-icon image c8cc0951 with
zone2fc2d72b, world95fc228a and shared_memoryb60c4dfc. Full source build starts
from that retained source and reproduces the shipping baseline exactly first.
The repo overlay has an older Hate header (176 instead of the released223 and
missing the spawn-source mapping); preserve the retained newer header. The fresh
snapshot also needs the already-released augstats declaration. Exact two-header
source reproduction is retained in `retained-native-overlay.patch`; no dungeon
behavior is being changed. Full build and final correction receipts authenticate
all source files. Initial build's old immutable source assertion is expected to
reject the two reviewed snapshot corrections; finalization verifies their exact
hashes and reruns the complete zone target before producing the shipping receipt.

Signed client2026111201 changes only dbstr_us.txt, preserves147other descriptors,
URLs and the proxy/catalog/config pair, and adds three live-QA patch notes. The
local production seed is never uploaded. The scoped publisher checks every
retained asset and changes the signed channel last. Wiki preparation reproduces
all613current public files, then changes only five guides and search (607retained).
Neither prepared artifact is a publication receipt. `rollout.py` requires exact
staged build/source/review/test pins, keeps deployment/GM locks, zero players and
125-second auth drain, clean full-runtime stop, fresh stopped full backup, exact
saved-state boot and one-market-rotation verification, and separate guarded reopen. Signed client text is published with admissions still closed under the same locks; its exact hash must pass before reopening.
Any failed mutation holds access closed. No content, rules, caches, quests,
world/shared binaries, player snapshots or inventory rows are rewritten.

## Exact in-game QA after a test release

1. In East Commonlands, use a normal character with a held Cleric, Druid or
   Shaman class and earned Quick Buff. Open the AA window: Quick Buff is active,
   Make Hotkey works, its text says 50% maximum mana/no reuse, and ranks 1, 2 and
   3 each expose the same action. Reconnect and repeat with a secondary class.
2. Memorize legal self/single-target buffs such as Spirit of Wolf and Inner Fire,
   a group buff legal to that character, one direct heal and one attack. Clear
   those buffs and fill mana. Select a hostile NPC, then press Quick Buff: all
   eligible buffs resolve in the same activation, no casting bars are queued,
   and the heal/attack do not fire. The selected target remains unchanged.
3. Measure maximum/current mana immediately before activation. Cost equals
   floor(maximum/2), minimum one. Group size and mana focus do not multiply or
   reduce it. Press again immediately: no AA cooldown or gem recovery blocks the
   second batch when its full cost remains. A third press with insufficient mana
   produces no buffs or additional mana debit. Include an odd maximum-mana pool.
4. With a pet and memorized pet buff, verify its normal pet/roster delivery.
   Without a pet, that spell is skipped. Check the group spell with near and
   distant members; native range and stacking/block rules still apply.
5. Test a reagent buff with and without components. Native consumption/failure
   messages remain, the rest of the bar is still attempted, and the activation
   charges once. Test incompatible/duplicate buffs and a full buff window.
6. An empty bar or a bar with only attacks/heals costs nothing. Stun, silence,
   death, unconsciousness, active casting, an ineligible/unscribed spell and a
   class-released stale gem cannot bypass normal eligibility. Sitting may stand.
7. Start an unrelated AA, item, discipline and long spell cooldown; use Quick
   Buff and reconnect. Their original deadlines remain. Quick Buff is immediately
   ready. Ordinary manual casts retain their normal reuse/recovery.
8. Evaluate full-bar shielding, HoTs, pet/group sustain and mana recovery with
   representative multiclass builds and progression gear. Native visible behavior,
   encounter balance, signed-client pairing and owner acceptance remain OPEN.
