# Food and drink removal — October 11, 2026

Status: implemented candidate; not deployed and not manually accepted.

## Behavior and scope

Characters never become hungry, thirsty or starved. The server sends full food
and water meters (6000) in the initial zone profile and every stamina update.
Legacy saved zero/negative meters are repaired before the profile is sent.
Quest setters retain their callable signatures but always restore both meters.
Manual, automatic and delayed consume packets cannot spend inventory items.
The existing HP, mana and endurance regeneration paths see `IsStarved() == false`.
Legacy food requirement, hunger penalty and depletion rules cannot re-enable this.

Food/drink items remain available for recipes, quests and optional item bonuses.
Their existing bonus calculation is unchanged; keeping stat food no longer has
an upkeep cost. This does not add regeneration beyond the existing fed baseline,
raise stat caps, change AA ranks or alter combat tuning. Nutrition-only abilities
have no remaining benefit. Alcohol/intoxication and spell reagents are unchanged.

The out-of-food/water text originates in the client. This change prevents its
trigger by keeping the protocol meters full; it does not modify client files.
Actual RoF2 rendering must be accepted using the checks below.

## Verification

- `python tools/tests/test_food_drink.py`: 250/250 compiled checks pass. Before
  the change only 37/250 passed, with failures for depletion, starvation, setters
  and item consumption. The test compiles the actual C++ methods with packet and
  inventory fixtures; it does not replace their behavior with a Python model.
- Login ordering guard confirms both meter assignments follow character loading
  and precede `OP_PlayerProfile` construction.
- Checked the complete diff for correctness, scope, packet validation, ownership,
  inventory side effects and API compatibility. No new dependency or schema.
- All three modified C++ translation units pass Clang C++20 syntax checks
  against an isolated patched copy of the retained production source, with its
  real Perl/Lua/dependency flags. Retained source hashes are unchanged. Existing
  unrelated warnings remain. This is not a linked release binary or a rollout.
  Local evidence: E:/EQ_Local_Dev/artifacts/remove-food-drink/compile-check.log.

## Exact in-game QA

Use a normal (non-GM) character in East Commonlands, preferably one whose saved
food/water meters were already depleted. No NPC interaction is required.

1. Bank all food and drink. Log out and back in, zone to North Freeport and back,
   then remain in East Commonlands for at least 15 minutes. Expect no hungry,
   thirsty, out-of-food or out-of-water messages at login, zoning or while idle.
2. Repeat while mounted, if available. Food/water remain full. Check HP recovery
   after combat, mana after casting, and endurance after combat abilities with
   identical gear/buffs to a fed baseline. No starvation-related suppression or
   negative endurance regeneration should appear; ordinary combat restrictions
   and ability upkeep still apply.
3. Carry a known stack of food and drink in general inventory and then in a bag.
   Wait through stamina updates; right-click each item, zone and relog. Both
   stack counts remain unchanged and meters stay full. Other players should not
   receive eating/drinking broadcasts from these requests.
4. Carry stat food/drink and compare the appropriate stats against the same
   character without those items. Existing bonuses still apply; banking the
   items removes only those optional bonuses and never applies starvation.
5. On a disposable test character, call the existing quest setters with zero and
   negative values. Both reported meters return to 6000, and no warning appears.
   Verify a new character also starts full without any food/drink inventory.

## Activation and rollback

Build the candidate zone executable against the current approved server source.
All zone processes need the new binary; `#reload rules` or quest reload alone
cannot activate this C++ change. There is no SQL migration, world catalog change,
shared-memory refresh or client update. Saved meters converge through normal
character saves; no bulk character update is necessary.

Follow feature -> dev -> test; owner manual sign-off is required before main
unless the owner explicitly authorizes another live-QA promotion. On OVH, use
the controlled game-runtime rollout with current-image capture and backup, not
a single-zone process kill (the supervisor restarts the entire runtime).
Rollback restores the immediately preceding zone image while retaining current
database/player state. Full saved meters are valid under the old implementation.
In-game acceptance and production activation are not claimed by compiler tests.
