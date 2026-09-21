# Immediate inventory class refresh

The owner requested a fix for the inventory class label after selecting all three
classes, with direct promotion to main and deployment to the hosted server.
This release-specific authorization does not change the normal branch policy.

## Cause and change

Trainer adoption writes `character_multiclass` and calls
`Client::ReconcileMulticlassSkills`. That reloads the authoritative slots, but
previously did not send a class/AA snapshot. The client kept its valid same-zone
identity and cached the old class tuple, so reopening Inventory did not request
fresh metadata. Zoning/relogging could refresh it.

The reconciler now publishes the existing loaded AA/class snapshot when either
extra slot changes, including when no new skills unlock. Native slot assignment
uses that same publication rather than sending twice. Class release already
publishes its committed snapshot and remains unchanged. Unchanged classes and
ordinary level-up reconciliation do not cause additional full-table refreshes.

No protocol, client binary, skin, class-selection policy, database schema or
balance changes are required. Existing supported Nightcap clients consume the
updated generation immediately. Metadata remains opt-in through `#nightcapui`.

## Verification

- Regression first reproduced stale second-class, third-class and consecutive
  selection labels. It compiles the actual reconciler and snapshot sender with
  the real client `UIState` parser; those scenarios pass after the fix.
- Unchanged-class and level-only reconciliation retains skill seeding without
  extra snapshot traffic.
- All seven native-method/client-parser controls pass, including native insert
  and update adoption, first UI opt-in after both selections, exactly one
  publication per selection, and consecutive updates during the request throttle.
- Spell-access (2), gameplay-policy (2), UI-layout (4), Perl release (15) and
  skill/lifecycle/login/release architecture guards pass. Independent source
  review found no blocking issues.
- Native build and deployment evidence will be recorded here before completion.
  Automated packet/parser checks are not visual in-game QA.

## Deployment and recovery

Build in a fresh isolated Linux directory with the existing production hardening
patch. Retain the previous `nightcap-game:release-2026092005` image, verify staged
binaries and runtime contracts, stop gateway/game, and take a verified on-host
backup. Switch the game image only, start it, compare player/merchant/rule
fingerprints and running binary hashes, then reopen the gateway. No content SQL
or client channel publication is needed. World startup rotates market stock by
the existing design.

Rollback selects the previous retained game image and restarts gateway/game.
Do not restore the whole database over later player progress. Build/deployment
artifacts are under `E:/EQ_Local_Dev/artifacts/inventory-class-refresh-20260921/`.

## Exact owner in-game QA

1. Use a disposable character on the current Nightcap client in East Commonlands.
   Open Inventory before adopting classes. Confirm the primary class and empty
   extra slots match the class-status command/banner.
2. Select a second discipline from its class trainer and confirm it. Without
   closing Inventory, zoning or camping, confirm the second abbreviation appears.
3. Immediately select and confirm a third discipline. Confirm the full tuple
   appears in the same zone. Close/reopen Inventory and verify it stays correct.
4. Check the newly selected class's merchant usability and AA class labels. The
   refreshed metadata must agree with the held classes.
5. On that disposable character, release an extra discipline and verify the
   retained class order and empty slot update immediately. Reacquire another
   class and check again. Avoid releasing earned classes on an established
   character solely for this test.
6. Zone and relog. Confirm the tuple persists and no internal `[NCUI1]` messages
   appear in chat. Manual visual acceptance remains separate from deployment.
