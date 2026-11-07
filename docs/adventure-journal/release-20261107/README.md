# The Last Lantern release candidate

Owner-authorized main/server/client-notes release, November 7, 2026. See
AUTHORIZATION.md. Nothing is deployed or player-accepted until dated activation
and publication receipts exist here.

The implementation adds sixteen native Task definitions (twelve chapters on one
playthrough), sixty-four objectives, eight private version-80 company memories,
nineteen actor definitions, six public services/couriers, eight earned armor
pieces in four legal fits and four earned grades, the existing bounded oath
charm, an inscription choice and the Lanternbearer suffix. The existing Keeper
runs, reward ledgers and ordinary public populations retain their contracts.

Native completed_tasks owns progression. Native task saves now acknowledge SQL
failures and retain retry flags; campaign completion persists before cancelling
its active checkpoint. A subsequent company interaction reconciles a completed
checkpoint from durable native history. No second story-progress mask exists.

First delivery reserves a stable character/slot UUID. Its chosen item is frozen
until delivery; a full-inventory retry cannot mint another identity. If that
reserved fit becomes illegal after a class release, an operator must review it
while the character is offline. Delivered pieces refit through a dedicated
complete inventory-row CAS, ownership update and operation receipt in one
transaction. Preserve augments, custom dye, saved binding, ornaments, custom data
and the persisted GUID. Unknown commit acknowledgement quarantines the client;
reconnect reloads authoritative inventory. Never clone a missing receipted item.

Campaign cache policy runs after FreeTrade: personal, no pet use and zero resale.
Current native FVNoDropFlag=0 is part of the reviewed release baseline. Preserve
the new cache policy and compatible native consumers after any equipment claim.
A recovery disables both story/oath gates, retains player history/receipts and
moves members home. After access opens, recover forward; never restore old
player snapshots or select an older cache generator that makes this gear tradeable.

Private runs have their own UUID/start/version/membership identity and no Keeper
completion, XP or loot. Interrupted transient scenes reset; earned native Tasks
and equipment remain. A return companion is independent of attempt cleanup.
The allocator never reuses an ID with a recoverable player corpse.

The native map probe verified arrival, floor/headroom and three connected poses
for all seven physical zones. Version80 uses reviewed version0 zone metadata;
Hate scenes use original76 and its already-shipped terrain, without changing186.
The retained saved-state loader explicitly creates new spawn2 points absent from
an existing snapshot, so the six new public NPCs need no population deletion.
No player or unrelated saved-state invalidation is authorized.

Automated evidence: test_lantern_*; actual native compile logs; guarded disposable
MariaDB migration and real one-connection refit rehearsal (complete metadata,
rollback, replay, unrelated-player corpse, ambiguous committed acknowledgement).
Current public combat definitions are captured separately under balance/.
Thirty-two earned-gear native arena runs pass across progression tiers, continuous
three-wave resources, three deterministic seeds and three level50 builds. Explicit
purchases spend48–98AA for fresh stages and500for the developed control. The
pre-final builds use seven Restored pieces and a Normal chest; no reward from
the finale is equipped beforehand. All worn support gear is current Normal, with
no pets, augments or preparation buffs. Failed drafts remain separate; this is
not whole-scene or all-class balance acceptance.
All three shipping baselines reproduce exactly; candidate world/zone/shared-memory
links and stripped ELF identity checks pass. Production cache/deployment preflight
continues under the one-shot release operator.

Signed client candidate2026110701 preserves all148 inventory descriptors except
spells_us.txt, retaining proxy0.13.5/catalog and all38 prior notes. Six campaign
changes are prepared together in the new client-note entry. The signature and exact executable
preflight pass. Publication is still pending; client-candidate.json owns that
boundary. No protected or installed game client is modified.

Build scripts are isolated: tools/build_last_lantern.py and
link_last_lantern.py. The release must reproduce the current zone baseline and
pin fresh production world/shared-memory identities before activation. Never
copy the selective Git mirror over the retained full source. Player appearance,
normal-account whole-campaign, pet/group/SSF and complete balance acceptance are
separate from these automated checks; CAMPAIGN-QA.md is the exact player spike.
