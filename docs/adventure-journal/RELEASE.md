# Epic 0.5 installation and recovery

Historical eight-task foundation. The current level20–50 implementation and
one-shot release package are in [release-20261107/README.md](release-20261107/README.md);
use [CAMPAIGN-QA.md](release-20261107/CAMPAIGN-QA.md) for current player testing.
Do not install this older prototype migration independently.


Status: candidate only. Follow the repository's `feature` → `dev` → `test`
policy. Main and hosted activation require the recorded manual acceptance gate.
Do not treat prior release-specific production exceptions as this release's
authorization. All deployment files must come from one reviewed commit.

## Owned content and contracts

| Resource | Reservation |
|---|---|
| Tasks / objectives | 9500–9507 / 22 activities |
| Charm | item 900501; global item quest `900501.pl` |
| Invocation | spell 42800, harmless blank effect |
| Five effects | spells 42801–42805, native duration exception |
| Native API | `Client::Epic05Contract()` returns 1 only with loaded spells and required task rules |
| State | `nightcap_epic05_state`: character ID, active path, ready time, use count |
| Gate | `nightcap_epic05_control`: singleton 1, native/catalog version 1; initially disabled |

Required runtime rules are `TaskSystem:EnableTaskSystem`,
`TaskSystem:RecordCompletedTasks` and `TaskSystem:EnableTaskProximity`. The native
contract refuses journal actions when any is false. Keep `era.json` unchanged;
this candidate is Classic with the existing level-50 cap.

## Prepare the test runtime

1. Capture the actual target's content/schema and save a backup before changes.
   The checked-in snapshot is local PEQ evidence, not a hosted preimage. Check
   exact IDs, names, levels, HP, damage, spell lists, special abilities and active
   Classic spawn/entry gates. The generated SQL refuses drift; investigate it
   instead of deleting the guards or assigning occupied IDs.
2. Build matching world and zone in a fresh isolated output from the complete
   source plus this checkout's `server-mods/code` overlay. Retain production
   hardening for a hosted candidate; verify source hashes remain unchanged.
   Do not overwrite the active `akk-stack/code` checkout or installed binaries.
3. Apply `setup.sql` through a client that stops on errors. It is additive and
   starts with the gate disabled. InnoDB content writes roll back together.
   MariaDB DDL auto-commits: if a later insert fails, empty owned state tables can
   remain. Inspect them and take a fresh backup; never blindly rerun or drop a
   populated state table. Reapplication deliberately refuses existing ownership.
4. Install all three `server-mods/plugins/epic05*.pl` files in the configured
   `server.directories.plugin_paths` (or scalar `plugins`) directory. Install
   the updated `ecommons/The_Ancient_Chronicler.pl` and
   `global/items/900501.pl` under the quest root. Item quest discovery requires
   `global/items`, not a top-level `items` folder. Preserve other quest files.
5. Stage the six client spells with `tools/epic05.py --client-source <current
   packaged spells_us.txt> --client-output <separate staging>/spells_us.txt`.
   Compare the source hash and full preserved prefix. Rebuild and sign the
   ordinary candidate launcher package; retain every unrelated current file.
   Install only into a QA client copy. `Client_RoF2_Dev` remains read-only.
6. With test writers stopped, select the matching binaries/content, regenerate
   shared memory and restart world/zones so items/spells/tasks are loaded.
   Verify plugin path logs and an actual native Chronicler hail. A Perl syntax
   check does not prove installed plugin discovery. Confirm ordinary multiclass
   dialogue still works while the journal reports unavailable.
7. After the matched client and native runtime are ready, enable the test gate:
   `UPDATE nightcap_epic05_control SET enabled=1 WHERE id=1 AND native_contract=1
   AND catalog_version=1;`. Verify exactly one matching row. Run every step in
   [QA.md](QA.md) with a normal account. Record native hashes, client release,
   legal AA pool, rules, gear and results before considering main promotion.

Task completion owns eligibility. `nightcap_epic05_state` is not a duplicate
quest tracker. Never grant rewards from user-provided path names without the
native completed-task checks. Never manually reset cooldowns on real characters
to repair an uncertain effect. An acknowledgement lost after commit may consume
the timer without power; that is the deliberate failure boundary.

## Disable and preserve progress

Apply `disable.sql`, reload task definitions and verify the unavailable journal
message plus blocked clicks. This disables new offers and abilities while
retaining all task records, character state, owned charm definitions and spells.
Existing active objectives may still earn native progress. Allow already active
effects to expire (at most three ticks); do not claim disable instantly removes
an already granted buff. Keep the item interception quest installed.

Do not delete/truncate state or native task history, remove spell/item definitions
that characters own, restore an old PEQ dump over new progress, or downgrade to
a receipt-unaware advanced-loot binary. Corrected client publication must use a
higher signed release number. Re-enabling requires the matched candidate and
explicitly re-enabling tasks 9500–9507; `setup.sql` is not a refresh tool.
