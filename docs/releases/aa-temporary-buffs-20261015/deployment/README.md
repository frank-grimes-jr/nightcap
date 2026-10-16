# Authorized native rollout — October 16, 2026

The owner explicitly requested **"Push to main and server"** on October 16.
This authorizes direct main promotion and this OVH rollout before owner gameplay
acceptance; it does not change the standing branch policy. The source candidate
is `248bf5c5efc92c40c53a1a8eb06ccc14b4ebda8c`.

The native operator derives from the reviewed tradeskill release operator, with
the existing signed client required to remain unchanged. The fresh read-only
baseline is the tradeskill zone `6317ba70...` in image `051efd28...`, with two
historical restarts and no current native/quest/database errors. The manifest
pins that restart count and all five binary hashes. Only `bin/zone` changes;
support files, quests, content, rules, other binaries and player data remain.
Signed client 2026101501 has 106 files and is verified against the shipped public
key before rollout. No new client package or spell export is required.

Stage: `/opt/nightcap/releases/aa-temporary-buffs-20261016`. Run `rollout.py`
with `preflight`, `activate`, `open`, then `report`. Each action takes the
deployment and GM locks and refuses active GM maintenance/SQL. Preflight checks
the complete baseline, builds one zone-only image layer, checks runtime libraries,
native startup contracts and authentication, and creates a gzip-verified backup.
Activation closes the gateway and gracefully stops the game, fingerprints stopped
player/custom tables, then starts and verifies the candidate with access closed.
Open requires the same runtime, zero candidate restarts, preserved data/content
and the exact existing signed client. Report verifies health after access.

Evidence files are exclusive and durable; do not delete them to replay uncertain
actions. Before access, failed checks restore the immediately prior image only
when preserved-state checks permit recovery. If access was attempted, observed
open, or cannot be established, hold the gateway closed and retain the current
candidate/activity for operator reconciliation. No path restores SQL, inventory,
AA progress, receipts or old saved positions. The old binary restores the bug.

`python test_rollout.py`: **33 offline checks pass**. Independent review approved
the final operator after unexpected-open recovery was corrected and covered in
both activation and open paths. These fixtures do not establish gameplay QA.
The parent release README retains the exact live owner tests.
