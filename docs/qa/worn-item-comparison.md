# Worn-item comparison

Inspect an item to compare it against every worn slot allowed by the current character's native equipment check. Each row names the slot and the item currently there. The delta is the inspected item's listed value minus the worn item's listed value, including socketed augments on each side. Occupied slots with equal stats show “Same listed stats.” Empty slots use zero. The client reads these values again when the inspection description refreshes.

The comparison covers 62 numeric fields across health, mana, endurance, armor, weapons, attributes, heroics, resists, regeneration, combat modifiers, purity and elemental damage types. These are per-item values before level scaling, stacking and character caps. Conditional skill, bane, proc, click and focus effects remain in ordinary item inspection. Equipping or moving the item still requires the usual player action.

## Candidate

Built from the NPC target candidate `c254964f` on `feature/worn-item-comparison`. The normal launcher package delivers the combined 32-bit proxy, its matching catalog and the retained target skin. The comparison uses the existing native item window and requires no additional skin file, MQ process, plugin configuration, server release or database change.

| Staged file | SHA-256 |
| --- | --- |
| dinput8.dll (0.14.1-dev) | `af5abdd341e8c85571ebfab59ce50ba67e0682c9d8960c69d56e2ac29feb9fe4` |
| nightcap-patch-sites.json | `899424bf63070bb615e530ae75bde6f004ed2ebc0f08df5aa6b011aca6474483` |
| uifiles/nightcap/equi_targetwindow.xml | `ec59307a3091696b6c3284c829615628131ad4814d522c708b5d6c0a7e11f60f` |

Local staging directory is `eq-client-dll/build/worn-comparison/`. Signing and player delivery remain pending. At release, assemble against the current signed parent and preserve other reviewed client work, including the Cairnwright pairing. A full exit and launcher Play loads an authorized release. Recover with a forward release of the previous reviewed proxy and matching catalog.

## Verification

- The read-only client adapter is in `eq-client-dll/src/worn_comparison.h`. It follows RoF2's inspection slot loop, calling the same equipment predicate with the same flags for slots 0 through 22. The existing multiclass equipment patch supplies the held-class policy. Inventory and augment pointers stay on the UI thread. A failed read discards the partial comparison.
- `eq-client-dll/src/ui_hooks.h` appends the comparison during the stock item-description render and restores its source text. Independent windows can refresh without stacking or retaining each other's rows. The existing name colors and Hunt augment annotation continue through the same renderer.
- `eq-client-dll/tests/augment-item-window.cpp` runs original RoF2 item rendering with fixture equipment and a captured draw boundary. All 62 checks passed, including independent rings, augment totals, different damage types, equal and empty slots, changed selections, invalid or partially allocated inventory, zoning and native description preservation.
- `eq-client-dll/tests/equipment-native.cpp` runs original RoF2 eligibility code. All 81 checks passed, including two-sided and right-only ring masks, held Monk eligibility, weapon conflicts, class release and race restrictions. The target label regression and both target skin tests passed.
- The x86 build, staged DLL/catalog and target skin validation, launcher manifest and preflight suites, installer and Play suites passed. The pinned executable and retained configuration passed all 120 static preflight sites. These checks do not establish player-visible acceptance.

## In-game QA

1. On a QA installation carrying the combined client, exit EQ fully and use Play with MacroQuest closed. In the East Commonlands tunnel, use a QA character with two different rings, such as a Silver Fire Wedding Ring (14676) and Golden Fire Wedding Ring (14678). Inspect a Platinum Fire Wedding Ring (14679). Compare each printed delta to the three actual item descriptions.
2. Swap the two worn rings and inspect the same candidate again. Verify the baselines and deltas switch sides. Remove one worn ring and inspect again. Verify the empty side shows the candidate's values and the occupied side keeps its own comparison.
3. Compare ring instances with and without socketed stat augments. An augment in the inspected ring raises that side's total. An augment in a worn ring reduces the displayed gain for its slot. Inspect the worn item itself and check the equal-stat message.
4. On a character holding Monk, inspect a primary-only Bronze Knuckles. Check Primary is the only row. On a character unable to use that item, inspect it again and check that its native restriction and description remain. Check both earring and wrist slots with appropriate gear.
5. Inspect items from inventory, a merchant and chat links. Reuse one inspection window, then keep two open. Reopen after a gear swap and after zoning. Scroll a long description to check wrapping, colors, native effects and the last eligible slot. Select an NPC and check the target level/class line from the previous candidate.

## Wiki impact

The Equipment guide and Recent changes have staged player copy. The same two edits were applied to an isolated preview of the retained November 21 Cairnwright wiki. Home, Features, commands and the item/zone catalogs were reviewed. This UI feature changes no command, item value or zone. The refresh check against the working feature ref flagged the implementation and older source drift. The public wiki and its review ledger have not been advanced.
