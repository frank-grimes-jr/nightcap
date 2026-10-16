# Authorized loader-only rollout

The owner authorized “Push, merge, and deploy with server restart” on October 16.
The policy candidate is 5cea9cb. The staged loader is the exact final native/cache
tested binary 71dfdd18d12fba844bcc222c54125c621a3c5e895a61ef3ae258ecc3dfbbb5c8.

`rollout.py` adapts the current AA-duration operator to replace only shared_memory.
It requires the current world/zone/login/UCS hashes, client 2026101501 signature
receipt and all 106 existing assets. Full item-cache comparisons are mandatory
before access, during rollback and in the final health report. Thirty-seven
offline recovery/pairing tests pass. Independent review has no blockers; exact
rollback cache equality is required, otherwise access stays closed.

Stage `/opt/nightcap/releases/equipment-race-policy-20261016` has immutable
manifest fingerprints. Run under its deployment and GM locks in order:

1. `python3 rollout.py preflight`: inspect baseline, build/verify one image layer,
   verify current cache and signed assets, and capture a fresh verified backup.
2. `python3 rollout.py activate`: close gateway, cleanly stop the whole game,
   capture stopped player/custom checksums, start candidate, compare full cache
   and unchanged data/runtime/public fingerprints. Gateway remains closed.
3. `python3 rollout.py open`: reverify current cache, saved checksums, services
   and publication before durable opening intent and gateway startup.
4. `python3 rollout.py report`: verify all 12 zones, zero unexpected restarts,
   client assets, cache and supporting services. Save production receipts.

Do not replay activation or uncertain gateway commands. Pre-access recovery
regenerates the previous image's cache and requires exact preflight equality;
failure holds closed. After possible access, retain the candidate and subsequent
player activity and reconcile. Never restore SQL or an old cache over changed
definitions. Review phase evidence before deciding any recovery action.

Presence of this runbook or staged manifest is not proof of deployment. See the
parent release deployment receipt for the observed outcome and pending owner QA.
