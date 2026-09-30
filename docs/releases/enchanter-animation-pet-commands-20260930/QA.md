# Owner in-game QA: Enchanter animation commands

The matching zone build is deployed on OVH; see [production evidence](PRODUCTION.md).
Record character classes, AA permissions, server build and zone. Use a disposable Enchanter without an
Animation Empathy/PetCommands unlock.

1. In East Commonlands, summon Pendril's Animation (spell 285), or a higher-level
   animation available to the character. Confirm it appears as the Enchanter's active pet and that no command AA is owned or granting
   `PetCommands` bonuses.
2. Target a nearby, attackable decaying skeleton and issue `/pet attack`. The
   animation must answer that it is attacking and enter combat. Issue `/pet
   backoff`; it must stop attacking and clear its hate. Reissue `/pet attack`
   and `/pet qattack` to verify both attack paths.
3. Issue `/pet follow`, move a short distance and confirm the animation follows.
   Then issue `/pet guard` and confirm it returns to and holds its guard point.
4. Issue `/pet sit` and `/pet stand`; verify the matching appearance and response.
   Toggle `/pet stop` on and off; confirm it stops, then resumes normal orders.
   Toggle `/pet taunt on` and `/pet taunt off`; confirm the response/state.
5. Confirm the existing legal-target, range, line-of-sight, fear and mez checks
   still reject invalid attack orders. Hold, Greater Hold, Spell Hold, Focus,
   Feign and Regroup remain subject to their existing AA permissions.
6. Repeat the standard commands on Magician and Necromancer pets to confirm their
   behavior is unchanged. If testing a multiclass character, repeat with Enchanter
   as a non-primary pet class.

Record any command that fails, the exact target and its range/mez state, and the
character's AA permissions. This checklist is a QA request, not an acceptance
record.
