# Cast-bar owner QA

Owner confirmation October30: “fIXED” after the Diiv recheck instructions.
The reported frozen-bar issue is resolved. The extended checklist below remains
available for regression testing; individual steps are not all claimed passed.

After authorized signed delivery, fully exit EverQuest and use normal launcher
Play. Keep the current proxy/catalog and other managed assets.

1. Log in as Diiv. In public East Commonlands, stand safely near the tunnel and
   memorize Frost Bolt (54) and Blast of Cold (372); also try Numbing Cold (374)
   if that was the second reported spell. Target a suitable attackable creature,
   such as a nearby decaying skeleton or a fire beetle. Clear the area first.
2. With autoattack off, cast each several times. The bar should start moving
   promptly and progress throughout the cast, not stay full until the end.
   Base times are 1.0 / 1.5 / 1.0 seconds respectively; existing focus modifiers
   still apply. Confirm the spell lands once, consumes its normal mana, and
   keeps its normal recovery. Record spell name and observed duration.
3. Repeat with autoattack on when safe. Interrupt one cast by moving and one
   with duck/cancel. The bar should clear normally and the next cast should work.
4. Cast Minor Shielding on yourself (2.5-second base cast), then zone to West
   Freeport and repeat a self buff. Relog and retest a nuke in East Commonlands.
   Confirm no stale gauge or spell access changes.
5. On an eligible held-class build, check an ordinary instant DoT, a Bard song,
   an item click and an activated AA. Their established timing/effects should
   remain intact. Test an existing cast-haste focus separately if available.

Record visible acceptance separately from native fixture and asset checks.
The reported Diiv issue is accepted above; the remaining cases are not all claimed passed.
