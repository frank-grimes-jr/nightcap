# Immediate inventory class refresh

Status: deployed to OVH at **2026-09-21 01:27:35 UTC** (September 20 locally).
Runtime and transport verification passed. Source promotion is tracked in
[PR #54](https://github.com/frank-grimes-jr/nightcap/pull/54).

The owner requested a fix for the inventory class label after selecting all three
classes, with direct promotion to main and deployment to the hosted server.
This release-specific authorization does not change the normal branch policy.

## Cause and change

The Ancient Chronicler's adoption quest writes `character_multiclass` and calls
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
- Full Linux loginserver/world/zone/UCS/shared-memory build passed, including the
  private-login crypto self-test and economy contract check. All 2,788 source
  hashes remained stable across compilation. The production hardening patch
  matches the previous deployed release. Both changed C++ units compiled.
- Twelve local activation/rollback fault scenarios pass, covering drift,
  backup failure, image switching, startup, data/rule preservation, process
  hashes, gateway failure and failed rollback. Unverified rollback holds the
  gateway closed and does not overwrite the database.
- All 15 running native process hashes match, the game is healthy with zero
  restarts, and startup scans found zero missing-API, native-crash or selected
  database-error markers. Four encrypted native handshakes pass after restart.
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

### Completed activation

Running image: `nightcap-game:inventory-ui-20260921`, image ID
`sha256:d797c1246ea4359b5d6758b06c215f2fea821c110594686438a5874c59533ea6`.
The built source commit is `30fbdcc8ab062909cd1fe1ab2c9828bd546f761c`.
The previous image, plugin and supervisor are retained; only native binaries
changed. The game client remains release 2026092006 and needs no new update.

All eight player/merchant preservation fingerprints and all rule values stayed
unchanged. The existing world-startup rotation advanced market epoch 3 to 4,
with ten finds, six sell offers and four buy offers, quantity one each.
The validated on-host backup contains 445,236,292 uncompressed bytes, SHA-256
`02023bb06699ec7c34f2d0f9202d5f40d69a1aad0cb3ef36d4cb6ad2fb9f4400`.
Recovery evidence remains at
`/opt/nightcap/releases/inventory-ui-evidence-20260921/`; the staged image inputs
remain at `/opt/nightcap/releases/inventory-ui-20260921/`.

[Verification summary](inventory-class-refresh-20260921/verification.json)
records deployed hashes, health, backup and transport results. Raw database
contents, secrets and startup logs remain on the host. The original local client
and local gameplay server were not modified or started.

## Exact owner in-game QA

1. Use a disposable Warrior on the current Nightcap client in East Commonlands.
   Hail **The Ancient Chronicler (999220)** near the tunnel hub. Open Inventory
   before adopting classes; it should show `WAR/---/---`, matching `#classes`.
2. At the Chronicler, select Cleric, choose **Choose this class**, then **Yes**.
   Without closing Inventory, zoning or camping, confirm `WAR/CLR/---` appears.
3. Immediately select and confirm Necromancer through the same dialogue. Confirm
   `WAR/CLR/NEC` appears in the same zone. Close/reopen Inventory and verify it
   stays correct; `#classes` should agree.
4. Check the newly selected class's merchant usability and AA class labels. The
   refreshed metadata must agree with the held classes.
5. On that disposable character, release an extra discipline and verify the
   retained class order and empty slot update immediately. Reacquire another
   class and check again. Avoid releasing earned classes on an established
   character solely for this test.
6. Zone and relog. Confirm the tuple persists and no internal `[NCUI1]` messages
   appear in chat. Manual visual acceptance remains separate from deployment.
