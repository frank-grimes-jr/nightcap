# Review reconciliation

The owner chose to continue the current review and declined a second-model
review. Three bounded fresh-context review cycles examined the native service,
inventory/receipt boundary and Keeper/spawn/death integration. Findings were
checked against the implementation before accepting them. No review result is
owner gameplay acceptance.

Actionable findings fixed:

- UUID-owned checkpoints and finalized corpse envelopes replace recyclable
  instance-number recovery. Raid deaths and both-mode corpse state commit before
  death publication. Native loot filtering, hunt drops and loot rights are captured.
- Grind respawn/death timestamps invalidate an older living checkpoint and retain
  independent successive corpses. Managed recovery does not depend on the global
  state-saving rule. The native marker fits the actual 50-byte notes column.
- Keeper proximity/state failure consumes the command, preventing legacy fallback
  from mutating managed runs. The old confirmation popup enters the native gate.
  Existing unmanaged Enter/Join behavior is retained. Hail prefixes are accepted.
- Entry reservations are cleared only by completed connections. Admission locks
  the run and checks generation, membership, expiry and retirement. Reset checks
  pending/inside members and recoverable player corpses under the same run lock.
- Native instance allocation is selected/inserted in a checked no-retry transaction;
  it does not call the legacy allocator that already inserts a reservation.
- Schema columns, keys, engines and triggers, all explicit catalog definitions,
  objective identities and effective cached item fields are gated. Item defaults
  are explicit; a fault test confirmed formerly omitted stats now reject drift.
- A lost feature-state query cannot permit legacy reset of a managed allocation.
  New creation rechecks enablement under its state lock. The release rejects split
  game/content database configuration rather than validating the wrong content.

Scope/operational decisions: preserve six lifetime participants, durable claims,
the native 200-unit encounter sphere and a journal display independent of reward
ownership. Single-database installation is an explicit release constraint. The
current era is Classic; future eras require a new audited catalog revision.
No tuning claim is inferred from arithmetic tests. External loot native behavior,
CT geometry and dragon balance remain in the in-game matrix.

Verification follows each repaired boundary: real schema/activation/concurrency
rehearsals, compiled actual policy/spawn/credit functions, full native build and
existing complete inventory/corpse/currency translation-unit fixtures. Manual
runtime failure injection remains separate. Packaging and test-branch delivery
must preserve these distinctions and leave production disabled.
