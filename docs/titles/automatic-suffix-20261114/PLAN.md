# Automatic title awards and equivalent suffixes

Accepted intent: no milestone should require opening Titles or running #titles
to receive its award and notification. Every existing prefix gains an equivalent
suffix from the same achievement. Keep stable IDs, permanent awards, eligibility,
current worn titles and cosmetic-only rewards unchanged.

Implement a shared reconciliation entrypoint, automatic login/history recovery,
and immediate callbacks for committed level, personal Keeper completion (including
High Keep rescue) and final campaign completion. Retain existing immediate kill
and persisted-skill paths. Failed cosmetic reads/writes must not veto gameplay or
replay a kill; automatic retry must be bounded and avoid per-frame SQL. Check
transaction ordering before issuing chat notifications.

One existing award/ID unlocks prefix and matching 'the …' suffix; the existing
suffix-only 'the Last Lantern' remains unchanged. No extra SQL award or duplicate
notification for the second placement. Enforce the native 31-byte display limit.

Tests first: missing automatic milestone recovery and paired packet fields;
then eligibility/failure/no-duplicate controls, hook ordering and full native
build from the freshly observed live source. Review independently, maintain
CHANGES/status/wiki/installed knowledge, and continue the already authorized
main/live/wiki title workflow with a guarded immutable release. Existing native
player acceptance remains a separately recorded gate.
