# Native class-release session recovery

2026-09-13; feature/aa-ownership, candidate engine commit 82866d1.
No engine change, live installation, promotion, or restart in this increment.

Three separate diagnostic processes pass eight native operations. A synthetic
level-50 WAR/MNK/WIZ owns six Wizard AA ranks (30 nominal points), has wallet 17,
spent 35 including five expended points, and raw skills 1H Blunt 260 and
Abjuration 250. A real MariaDB trigger rejects the skill write during release.
The transaction rolls back; the old client retains its pre-release state but
has invalid AA ownership and a closed mock transport. Real Client::Process
returns false and executes OnDisconnect: ingame changes 1 to 0, a stats record
is inserted, and one WENT_OFFLINE event for character 1 is captured. A later
SaveAA returns false. Every other character_data column remains unchanged.

A fresh process calls native LoadCharacterData, LoadCharacterSkills,
LoadMulticlassMask, and LoadAlternateAdvancement. Loaded classes, positive raw
skills, earned and usable AA ranks, profile and all three counters match storage.
Its diagnostic wallet initially contains 999, so the observed wallet 17 proves
the profile loader replaced that input. Releasing Wizard succeeds: wallet 47,
spent 5, no Wizard AA, Abjuration 0 and shared 1H Blunt 260. Another fresh process
loads this committed state and cannot release the empty slot or refund again.
Both fresh sessions retain open transports and emit no logout event.

Evidence is aa-session-recovery.json, with its build manifest and durable
preimage alongside it. Diagnostic SHA256:
17810d42cb37346da3fe06ba37112172b9a7363a895be4c953cf06bf03715aea.
It links 130 pinned objects against the previously built candidate. The only
new C++ behavior is in the diagnostic; Process, OnDisconnect and database loaders
are native code. The mock transport intercepts explicitly permitted player events
without forwarding them to world. Event 11 is enabled only in the clone during
the test, then its exact prior settings are restored.

The final run restores its class rows including timestamps, skills and event
setting, removes synthetic character/AA/stat rows and trigger, and leaves the AA
catalog unchanged. The pre-review passing run is retained. The initial failed
run reached disconnect but expected an event disabled by default. That first
runner did not persist its class timestamp preimage; its original synthetic
applied_at value cannot be certified restored. Known test rows were checked and
cleared, and its observed timestamp became the documented next fixture baseline.
The corrected runner saves its preimage before any writes and refuses to replace
an existing report or preimage. This limitation concerns only the isolated clone.

Independent review required cleanup protection from the first event-setting
write, immutable preimages, exact logout identity, open-transport assertions in
both fresh processes, and passing status only after restoration checks. Three
evidence tests also reject deliberately stale classes, skills, ownership and a
duplicate refund.

The first full Python run passed 350 of 351 tests. Its failure was the earlier
candidate's immutable hash check against now-updated status/audit documents.
The exact four documents from commit 82866d1 are retained in
aa-release-pinned-documents.tar.gz and verified against that unchanged historical
manifest. Other historical evidence remains checked directly. No prior hashes
were regenerated to conceal a difference.
The final full suite passes all 351 tests in 142.346 seconds; its complete log
is aa-session-recovery-python-tests.log.

This proves Process/OnDisconnect execution from an already invalid, disconnected
mock client and native loader recovery in fresh processes. It does not distinguish
the new Process entry guard from the older disconnected branch, execute the
post-packet guard, or perform real network login. ClientDataLoaded starts false;
the transition from a fully loaded player and general-save suppression remain
unproven. Group, raid, mercenary, trade, dynamic-zone, aura and disconnect-quest
state are empty. Uncertain COMMIT, wider class-selection/AA lifecycle work, client
rendering and explicit in-game QA remain release gates. Balance is not declared
clean or complete by this test.

Run from this worktree after retaining/archiving previous evidence deliberately:

    python -B tools/balance/run_aa_session_recovery.py

Run its evidence tests from tools/balance:

    python -B -m unittest discover -s tests -p test_aa_session_recovery.py -v
