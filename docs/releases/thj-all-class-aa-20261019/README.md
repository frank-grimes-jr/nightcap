# All-class AA update — October 19, 2026

**Deployed to main and the server for live testing on October19. Owner gameplay and balance acceptance remain open.** All16 classes were reviewed against
566 archived THJ ability records, the retained Google notebook and released forum
patch notes. The source includes main client-contract repair16bfe18 and its published follow-up07b002b;
the AA comparison baseline remains the unchanged October18 release73358d.

- **75 newly available AA lines,111 expanded lines, no removed lines.**
- **1,836 ranks /483 families**, up from1,160/408:676 additional earned ranks.
- Druid also gains access to the existing six-rank Healing Boon line.
- Every existing legal rank, price, prerequisite, ownership identity, saved
  deadline and reviewed pet/WPM ceiling is preserved. Classic remains level50.

The [clean list](CHANGELIST.md) lists shared changes once, then Added / Changed /
Removed for every class. [CSV](changes.csv) gives unique global rank changes;
the separate Druid access correction is described above. The complete
[disposition ledger](dispositions.json) explains all566 source records, including
exclusions and prerequisite-blocked tails. Counts overlap across class lists
because shared abilities belong to more than one class.

This is an **AA rank/access pass**. Native effect values remain, except Druid's
added class eligibility. The list explicitly identifies remaining THJ behavior
differences; matching native IDs is not proof of matching THJ effects. Balance
work and owner acceptance follow this candidate.

## Reproduce

From this checkout:

```powershell
python tools/all_class_aa.py --check
python tools/aa_tbs_policy.py --check
$env:PYTHONPATH='tools;tools/tests'
$env:NIGHTCAP_DB_TESTS='1'
python -m unittest -v test_all_class_aa test_all_class_aa_native test_aa_tbs_policy test_wpm_aa test_aa_cooldown_identity test_aa_temporary_buffs
```

The opt-in SQL test uses connection-local temporary content/player tables,
replays forward and rollback twice and rejects preimage drift. It never updates
real character rows. Generated SQL changes only `aa_ability.id=389` classes
518→550. Production-content-check.json is a fresh read-only check of all four
AA tables against the released fixture, not deployment evidence.

## Deployment and rollback contract

The owner explicitly requested this AA update move to main and the server for
testing on October19. PR250 promoted the tested source at c3f0686. The
[deployment record](deployment/README.md) and immutable receipts verify
activation, preservation and publication; this approval does not imply gameplay
acceptance or standing permission for future releases.

1. Recheck current native source, production AA content, era, client repair and
   the latest release receipts. Use the preserved client0.11.0 with its matching
   catalog repair; this pass supplies no client binary or spell-file change.
2. Back up before the guarded Healing Boon migration. Install the matching
   compiled zone policy and clear/reload content through the supported release
   procedure. AA reload alone cannot install `nightcap_aa_policy.h`.
3. Use the actual production supervisor procedure. Never kill one zone under
   the assumption it leaves the rest of production running.
4. Confirm the published table, player purchases, class changes, deadlines and
   Classic50 per [QA](QA.md). No gameplay acceptance is inferred from tests.

Rollback restores the prior zone policy and runs `healing-boon-rollback.sql`
against its exact afterimage. New earned ranks remain saved and become dormant
where unavailable; they are not deleted or refunded twice. Do not restore a
player database snapshot over newer play. Re-enabling restores eligible earned
ranks. Keep the separately released pet/WPM content and client repair intact.

The local candidate binary is built from fingerprinted retained source with only
the policy header changed. The new header's consumer is `zone/aa.cpp`; no rule
catalog, ItemData or world/shared_memory implementation changes are introduced.

## Verified live release

All12 zone processes run SHA256 `e1dd9c4cdd6bf95db7ffc909f224b1603e9e07e1ad05925bcdd7bd0359cd3eb0`.
The existing world/shared-memory binaries, Classic50, rules, item/spell caches,
quests and client2026101901 remain. A fresh64,416,158-byte gzip-tested backup
and47 player/28 custom-table fingerprints verify preservation. No player rows
were restored and no points/ranks were granted. Market startup rotated once
from85 to86 with42 valid offers within44 slots. All138 published client assets
remain exact. Game and gateway are healthy and open.

Wiki20261019-all-class-aa-v1 is published; all465 public hashes/security headers
and five private-route denials pass. Six guides changed after all21 guides and
432 generated reward routes were reviewed. Owner AA gameplay/balance checks
remain open; reconnect and turn Recommended AA off before following QA.md.
