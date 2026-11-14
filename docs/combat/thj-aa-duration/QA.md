# Rank-one Rage and Bloodlust player checks

Use a Warrior with Rage of Rallos Zek or a Beastlord with Bloodlust learned at rank one, with sufficient endurance. Record application and fade times for spell 21773 or 30736. Check the buff window and the actual combat effect separately.

1. Activate each ability shortly after, halfway through and shortly before a six-second tick. Repeat with duration focus. Time from successful application. Expect Rage to last 12 seconds and Bloodlust 24, within one server processing frame and client latency.
2. Remove a buff early. Confirm its combat effect ends and the old timer cannot remove a later buff in the same slot.
3. Cross a zone or reconnect while the buff is active. Measure against the original application time. Repeat with a reconnect after the original expiry.
4. Run a neighboring ordinary timed buff and confirm its normal duration and focus behavior. Record reuse separately from active duration.

5. Enter a zone that suspends buff timers. Bloodlust should preserve its remaining active time and resume on returning to an ordinary zone. Rage should still expire on schedule. Try the Extended Bloodlust AA and check that it grants no extra time.
