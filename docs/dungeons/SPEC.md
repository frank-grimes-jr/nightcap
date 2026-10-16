# Raid and Grind instances

Accepted October 16, 2026. Candidate feature; no production activation.

The existing seven Keepers offer Raid and Grind. Both have guaranteed required
bosses, version-zero geometry, a fixed mode, at most six characters, and a
12-hour wall-clock lifetime. Raid has 135% native HP and 115% outgoing damage;
defeated spawns never return. Its final boss unlocks after the mini-bosses.
Grind retains normal combat stats and respawn timers.

Every character needs proximity/party credit for every objective in this run.
Pets attribute to their owner. Grind respawns can supply missed objectives;
Raid has no retrospective credit. Completion is once per character/run, with
durable per-dungeon/mode history and claims surviving expiry/reset. Native Tasks
display the ledger; abandoning a task cannot reset credit or reward identity.

The shared catalog contains 24 designs (8 armor, 8 weapons, 6 accessories,
2 bags), each at bands 20/30/40/50 in Normal/Polished/Ascended. All are permanent,
tradable, non-attunable, non-lore, zero resale, and excluded from old tier/forge
systems. Grind awards Normal. Raid awards 90% Polished / 10% Ascended. Each
Raid end boss has three exclusive designs; Grind has no exclusive drops. One/two/three distinct drops occur at
80/18/2%, independently rolling the same Raid quality probabilities. Native
loot remains additional. Rolls are fixed by durable random state at creation.

End bosses: Befallen/Gynok Moltor (20), Unrest/Garanel Rucksif (30),
High Keep/Carson McCabe (40), Najena/Najena (30), Cazic-Thule/Classic Avatar of
Fear (40), Permafrost/Lady Vox (50), Sol B/Lord Nagafen (50). High Keep includes
Bosec, Boshinko and Dyrna with normal faction consequences. Exclude services,
controllers, fabled/event and later-era variants. Restore Classic CT privately
from a pinned maintainer database export; never un-gate the public PoP revamp.

The creator alone may reset, with a run-bound confirmation; reject occupied
instances and recoverable player corpses. Keep existing unmanaged instances
unchanged. Wrong revision, incomplete catalogs, schema drift, or ambiguous
storage outcomes fail closed. No live-player snapshot restoration on recovery.

## Implementation sequence and proof

1. Capture source/content preimages, create schema/catalog and deterministic
   native policy tests. Collision checks cover cross-table identities.
2. Deliver Befallen vertically: native Keeper API, spawn/death ledger, Tasks,
   atomic receipt-backed claim, and failure/reconnect/reset tests.
3. Add all other encounter and item catalogs, including isolated CT restoration.
4. Compile against retained release source; rehearse SQL in a disposable DB;
   exercise native integration, concurrency and interrupted commits.
5. Independent review, package candidate and exact player QA. Update CHANGES,
   status/runbook and installed Nightcap reference/fingerprints. Feature → dev
   → test only after gates pass; main/production requires separate sign-off.

## Trust boundaries

Keeper text cannot supply run identities, item IDs, other players or raw SQL.
Native code validates Keeper identity/proximity, leader/owner, membership,
instance generation and catalog revision. UUIDs are validated before SQL use;
other interpolated values are native integers, fixed enums or escaped catalog
text. Entitlement precedes the existing atomic inventory/receipt transfer.

Managed checkpoints use private run-UUID storage. They never load or replace
native instance-number checkpoints. Both modes commit a complete corpse loot
envelope with stable item/currency receipts and absolute decay together with the
death ledger. Replay filters through the same receipt-aware native loot path.

## QA boundary

Automated checks do not establish solo balance, visuals, pathing or owner
acceptance. Record all four states separately: implemented, verified, deployed,
accepted. Keep disabled until the complete catalog and native release pass.
