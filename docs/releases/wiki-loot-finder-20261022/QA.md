# Loot finder acceptance

Local browser/test checks and approved production publication are complete.
Deployment receipts record the actual service/timer, public-file/JSON checks,
rollback rehearsals and live browser results. These steps remain a repeatable
owner QA guide; agent checks do not imply owner or gameplay/balance acceptance.

Scheduled refresh evidence: `deployment/timer-verification.json`, trigger
2026-10-23 01:40:27UTC, success01:41:15, new public snapshot and old immutable item
both verified. Live browser evidence: `deployment/live-browser.json`.

1. Open the published Loot finder. Confirm Classic, capture time and any-held-class
   default. Select Warrior, Cleric and Enchanter. A fourth selection is rejected.
2. Search Flowing Black Silk. Open item1365: a frenzied ghoul in The Ruins of Old
   Guk, level42, calculated59.04% from the reviewed capture. Open three spawn
   locations and compare `/loc 1072,-1073,-193`, `1072,-1042,-193`, `1077,-1057,-192`.
   Spawn weight10 is displayed as a weight, not a spawn percentage. Changes after
   a later capture should be explained from updated production content.
3. Return, clear the name, switch between any/all matching. Confirm all-mode
   results require all selected classes. Filter slot, quality and source zone;
   inspect item classes and source locations. Check pagination, Back and reload.
4. Check320px mobile and desktop in light/dark modes, keyboard navigation, no
   horizontal overflow and no warning/error console entries.
5. Confirm the actual sandboxed reader succeeds and the timer is enabled. Observe
   a second successful capture after15minutes and the immutable snapshot changing;
   an existing tab must continue loading details from its original generation.
6. Verify all467static files and public JSON hashes/security headers. Raw captures,
   manifests, scripts, private player routes and POST remain denied. Record the
   unchanged private downloads and all five container identities/start times.
7. Rehearse the guarded route/config inverse and existing HTML pointer rollback.
   Record public release, capture/timer evidence and owner browser acceptance
   separately from native gameplay/balance QA.
