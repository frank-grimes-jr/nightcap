# Preserve idle zone workers — October 17, 2026

Production correction applied at **14:47:02 UTC / 10:47:02 a.m. Eastern**:
`Zone:KillProcessOnDynamicShutdown=false` in ruleset 1 (`default`). This is the
only stored row for this rule. All alternate zone rulesets inherit default first
and have no override, so the one-row correction covers their effective value too.
All thirteen world/zone processes were using default at the verified reload.

## Cause and evidence

`Zone::Shutdown` unloads zone data, then shuts down its event loop when this rule
is true. Production's `/opt/nightcap/start.py` treats **any** native child exit
as fatal and restarts the complete runtime. An orderly idle unload therefore
disconnects players elsewhere. Original OS exit codes and the date this conflict
was introduced remain unknown.

Retained Docker records (UTC; Eastern is UTC minus four hours) show:

| Idle zone | Proper shutdown | Supervisor restart error |
|---|---|---|
| Befallen instance 101 | Oct 17 02:20:25.484 | 02:20:27.197 |
| East Commonlands | Oct 17 03:43:06.678 | 03:43:07.577 |
| East Commonlands, newly observed before this correction | Oct 17 14:42:35.321 | 14:42:36.679 |

The first two are October 16, 10:20:25 p.m. and 11:43:06 p.m. Eastern.
The third is October 17, 10:42:35 a.m. Eastern. Inspect the retained interval
before filtering; a filtered tail can miss the initiating zone. Capture both
stdout and stderr. Native file-log timestamps differ from Eastern; use Docker's
UTC timestamp for incident correlation. [Matching records](followup.json).

## What was verified

- [Read-only preflight](probe.json): one true row, default ruleset 1, no alternate
  overrides; deployed world/zone hashes match the October 16 journal release.
- The existing loader, world broadcast, zone reload and protocol sources match
  the deployed source manifest byte-for-byte. The tracked `zone.cpp` also matches
  that manifest; the old local full-source `zone.cpp` does not.
- [Operator](ops/apply.py) held the shared deployment lock, saved the complete
  rule-table preimage, rehearsed forward and exact inverse in a rolled-back
  transaction, then committed exactly one guarded update. All other rules and
  the rule's notes were preserved. No player data was written by this operator.
- [Activation receipt](result.json): world and all twelve zone workers completed
  the authenticated global Rules reload. All fifteen native PID/start tokens and
  all five service identities/start times/restart counts remained unchanged;
  game and database stayed healthy. No client, binary, quest, cache or timer
  change, maintenance disconnect, or local development database change occurred.
- [Read-only follow-up](followup.json) again checks lifetimes, service identities
  and stored value. **Natural idle-unload and player continuity acceptance remain
  pending** until an empty loaded zone reaches its timer. The activation receipt
  is not proof of that later event.

The first SSH payload failed Python parsing before any remote action. The fixed
[runner](ops/run.py) constructs the source with Python `repr`, parses the complete
payload locally, and transmits it through stdin. The successful receipt is the
authoritative write record. Do not rerun this one-time operator.

## Exact remaining acceptance

1. Keep one character online in a separate zone (for example Unrest). Visit and
   leave East Commonlands, or enter and leave an existing Befallen instance.
   Do not reset the run, alter timers, or terminate a zone process for this test.
2. Let the empty zone's configured one-hour idle timer expire. Expect its normal
   `Going to sleep` unload, followed by the **same worker PID/start token still
   alive**, world and other workers unchanged, and no new supervisor restart.
3. The character elsewhere must remain connected and able to move/interact.
   Re-enter the unloaded zone and check saved NPC/corpse state and existing
   dungeon progress. No change to their persistence policy was made.
4. Run [verify.py](ops/verify.py) through SSH stdin and retain its JSON. It compares
   against the activation baseline and checks lifecycle lines from captured
   file offsets. If a zone opened a different log file afterward, also inspect
   the corresponding dated zone log/full Docker interval. Pair machine evidence
   with the player's observation before marking acceptance complete.

## Recovery and future operations

Private preimages, exact SQL, reload helper and receipts are retained under
`/opt/nightcap/backups/dynamic-zone-worker-lifetime-20261017/`. A rule-table
snapshot is sufficient for this scoped configuration correction; no full player
backup restore is required or permitted as recovery.

On an uncertain result, read the receipt and current row before retrying.
If false persisted but reload failed, keep false and retry/verify the supported
global Rules reload. Do not automatically restore the known dangerous true
value. The guarded inverse exists for a deliberate rollback after resolving
supervisor compatibility; restoring true with this supervisor restores the bug.
Preserve unrelated rule edits and all subsequent player activity.

Existing-rule changes require world and every zone to reload; no new binaries
or client pairing are needed. Future alternate rulesets must not override this
rule to true under this supervisor. The supervisor still restarts everything
after a real native child exit. Historical October 9/11 runbooks describing true
are dated evidence, superseded for current operations by this correction.

## Wiki impact

[Whole-wiki assessment](wiki-review.md): add a narrowly worded reliability entry
to Recent changes. Player mechanics, Features, commands, home, travel/dungeon
instructions, generated item/zone pages, values and release labels stay correct.
Wiki source maintenance is separate from publication; no public release is claimed.
