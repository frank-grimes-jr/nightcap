# Hunt shield block in the item Description

Owner report: Exalted Understone Heart shows no shield block in its item window;
Shielding does not increase. Read-only OVH confirms item940282 has the intended
1-point shield-block bonus and Palwar owns the drop from a spirit of the ruins.
The native server helper already applies this bonus. Shielding is a different
damage-reduction stat; neither its value nor the shield-block mechanics change.

Fix the pinned RoF2 Description rendering through the existing signed proxy:
add a clearly labeled Shield Block value plus the usable-shield, worn-socket and
strongest-Hunt-only restrictions. Keep item names, spells, ordinary item stats,
loot, inventory and server runtime unchanged. Base has no block bonus; Polished
and Exalted give1percentage point, Ascension2. Reuse the server policy directly.

Plan: add an exact-client native regression for the real Description render;
implement a bounded, idempotent description decorator and a guarded native update
hook; regenerate paired proxy/catalog and run native/runtime/preflight tests.
Review current signed live source before assembling any managed client delta.
No protected-client writes. Verify visible rendering separately from compiled or
signed delivery; the owner must fully exit EQ/use launcher Play for a DLL update.

QA: inspect all three shield-block families at each quality in bag, chat-link and
socket views; Exalted shows+1%, Ascension+2%, with Shielding clearly distinguished.
Refresh/reopen/resize must not duplicate text. Ordinary augments retain their
description. Equipping with a usable shield still uses the strongest bonus only.
No bonuses apply to bagged or Power Source training items. Owner visual acceptance
is pending until checked in the actual game.

## Candidate evidence and release boundary

The real pinned native Description renderer fails before the fix and passes25
checks after it, including all three families/four qualities, repeated refresh,
window reuse, ordinary text preservation and malformed/native-string guards.
Twenty-two client runtime/native groups pass, as do the120-site exact-client
catalog verifier and Go preflight/manifest/runtimehealth packages. Two report
checks execute the actual command against server bonus snapshots; seven existing
augment balance/migration tests pass. The report is self-only and read-only.

The paired0.13.3 proxy and catalog are locally signed as candidate2026110601:
146unrelated assets and their URLs are retained, with production-key signature,
proxy/catalog and exact-executable preflight verified. This is not publication or
owner native visual acceptance. The current public client remains2026103002.
The new server command and item Description correction require a paired release;
no item stats, stacking, spells, drop rates or saved inventories change.

`#augstats` reports server-calculated Shield Block with item/spell/AA components,
the active strongest-Hunt contribution, Shielding, Spell Shielding, Avoidance,
Accuracy, Spell Damage/Heal Amount with current caps/headroom and the relative
Dodge modifier. It distinguishes inactive shield-block components from the
actual shield-gated nominal frontal check; counter/facing rules remain native.
The native sheet's stock250healing cap is not authoritative for this server.

Fresh read-only Palwar evidence confirms item940282 was collected in zone39 from
NPC39026/a spirit of the ruins at2026-11-06 17:32:17UTC and is saved loose in
inventory. Its current filter is AlwaysTake(1); receipt/event logs establish the
loot transfer but do not separately record automatic versus manual execution.
No character inventory, filters or other saved rows were changed by investigation.

Wiki impact: owning augment/command/equipment guides, Features and Change Log
receive explicit Not released correction notes. The existing510-file public
augment publication remains unchanged until separately verified publication.

## Verified deployment and publication

Main PR408 merged as3343d6c8bb9c2d1c66de3e68c1c01309479838f6. All one-shot
preflight/activate/open jobs succeeded. `deployed.json` is a fresh independent
readback: zone3fc2b901, healthy reopened gateway, exact unchanged item cache,
content/rules and all prior command rows; only player-access augstats row added.
Stopped backup65580990compressed/471046452uncompressed bytes passed gzip checks,
SHA256 b2504e29c02bb2b748335ef2bf90f25327e10e59a4d427dc89fb5115cbea68a4.
Saved-state model/market rotation were verified before access reopening; no old
player snapshot was restored. World/shared_memory and compatible metadata retained.

`client-published.json` and `client-public-verification.json` verify signed
2026110601/proxy0.13.3: all148hosted assets/300608073bytes, production signature,
DLL/catalog pair, history and146unchanged assets/URLs. Fully exit EQ/use Play.
The client update does not change game power, item names, spell definitions or
player INIs. Twenty POSIX publisher/recovery tests passed before publication.

`wiki-publication.json` records20261106-augment-description-v1:510files/503HTML
routes, exact hashes, private downloads, unchanged service identities/start times,
atomic rollback rehearsal. Five owning guide/Features/Change Log instructions
were updated; all item/zone/catalog/Build Lab/asset data is preserved. Main plus
`published-source-overrides.patch` reproduces actual public source while keeping
unrelated source-only previews distinct. Global historical wiki drift remains
REVIEW REQUIRED; no blind ledger advancement. Public-scope/link/stacking tests pass.

Rollback before reopening uses the held native operator and compatible prior
augment image; no player restore. After reopening, use a fresh compatible forward
repair. Client recovery uses a newly signed higher counter with a matching DLL/
catalog pair and preserved current assets; never lower counters or reset history.
The prior proxy remains compatible with #augstats if only its description hook
needs reversal. Native pixel/skin/socket/link and gameplay acceptance remains
owner live QA; automated rendering/delivery checks do not establish acceptance.
