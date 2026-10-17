# Exact in-game acceptance

Run after the candidate zone and guarded timer conversion are installed in the
approved test environment. Keep the current signed client. Use a disposable or
owner-designated character with the named classes/earned AAs; do not grant live
player progress merely to run these checks.

1. With Warrior and Monk held and Rampage/Purify Body earned, use a valid combat
   target in East Commonlands. Activate Rampage. Only Rampage's button counts down;
   Purify Body remains usable. After a controlled test reset, reverse the order.
2. Where earned, repeat with Mass Group Buff, Escape and Ancient Attunement. A
   tunnel recall must not start the other four family clocks. Keep each real reuse.
3. Activate two families, zone to the tunnel and reconnect. Both independent
   remaining waits must continue, with no refreshed full-length wait or refund.
4. Buy another legal AA/rank while an existing timer runs. The existing clock
   must retain its deadline. A class-slot change must clear obsolete client
   clocks while retaining dormant server deadlines if that class is reacquired.
5. On a GM test character, `#resetaa_timer 258` resets Rampage only. The previous
   casting AA must not decide the target. `#resetaa_timer all` resets AA clocks
   while an active skill, item and discipline clock retain their waits.
6. Death: a family flagged reset-on-death clears, an unflagged family retains its
   deadline. Ordinary death EXP, memorized gems and buff behavior remain unchanged.
7. Item/augment test fixtures: IDs64350 and129886 must retain distinct timers;
   resetting one cannot reset another spell/skill. Check an ordinary linked item
   group still shares its declared reuse and the item display matches server wait.
8. Exercise available disciplines in groups11–19. None may lock basic combat,
   begging or linked spells. Thief's Eyes8001/Thief's Vision40294 retain separate
   ungrouped reuse and do not lock Disarm Traps. Administrative reset-all clears
   every discipline while preserving AA/item/skill waits.
9. Recheck all six basic Monk attacks, Bash/Frenzy and Mend to retain the earlier
   paired release behavior. With Monk held on RoF2, each of the six attacks must
   retain its own wait; Tail Rake and Dragon Punch are one skill. Zone/reconnect
   during a wait: a cleared client display must not refund the server deadline.
   Failed/out-of-range casts must not consume unrelated cooldowns; procs must not
   start ordinary persistent spell reuse.
10. Confirm expected unchanged content links: Harmshield/Cannibalize and Battle
    Cry/Throw Stone remain recorded open issues. Do not mark complete independence
    of all spell/discipline families accepted based on the AA correction.
11. On designated characters that can actually use both skills, record both
    orders of Bash/Kick without Monk, Backstab/Frenzy where available, and
    Begging/Pick Pockets. Timer 25 still groups the generic combat attacks and
    timer 27 groups the latter pair. Treat observed blocking as a documented
    unresolved grouping, not approval of that balance policy. With Monk held,
    Kick must move to 530 while Bash/Backstab/Frenzy still use 25. Check Disarm
    uses 26 and does not block held-Monk Tiger Claw at 552. Do not infer access
    merely from class or catalog membership; record rejected activation separately.
12. With long enough skill waits to observe, exercise `#resetaa_timer all`,
    `#resetdisc_timer all` and an approved test castbar/item reset independently.
    Generic combat, Disarm, utility and Monk skill waits must survive those
    domain resets; use `#show timers` and the native display to distinguish a
    real server reset from a client display refresh. Do not clear all saved
    timers to manufacture the result. Death is not a universal skill reset;
    the classic primary-Paladin Lay on Hands exception is separate.

At deployment, record actual zone hash, receipt/catalog hash, each test result,
native UI observations and any remaining exceptions. Existing ambiguous old
waits intentionally survive until original expiry; test fresh activations after
that boundary or use controlled resets on the designated test character only.
