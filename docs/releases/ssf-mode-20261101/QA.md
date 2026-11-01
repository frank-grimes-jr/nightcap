# Solo self-found mode: QA

## Automated

```
python tools/tests/test_ssf.py
python tools/tests/test_passive_aa.py
python tools/tests/test_level_aa.py
python tools/tests/test_level_aa_integration.py
```

`test_ssf.py` compiles the real AA award methods: an SSF character at 0% earns no
AA, a normal character keeps passive AA, SSF at 50% and 100% earns focused AA
only. It also checks that every gated handler calls `SSFBlocked`.

## In-game spike (two characters, local)

A is a new level-1 character; B is a normal character. Zone, `#reload quest`.

1. A hails the Ancient Chronicler in the East Commonlands tunnel, clicks `walk alone`, then Yes.
   Expect "You now walk alone." and a `character_ssf` row. The AA window shows 0%.
2. A and B request trades with each other: both refused with a red message.
   A hands an item to a quest NPC: the turn-in still works.
3. A uses `#bazaar` and `/trader`, and buys from a trader: refused.
4. A sends a parcel to B, and B sends one to A: both refused, and the parcel
   window closes.
5. A uses the shared bank (an item, then plat) and the guild bank: refused.
6. A and B invite each other to a group, then to a raid: refused both ways. A can still group
   with a bot or mercenary.
7. A kills at 0% AA: `aa_exp` does not change and normal XP rises. A presses + to
   50%: AA accrues and normal XP halves. B at 0% still earns passive AA.
8. A GM deletes A's row and A zones: steps 2–6 now work.
