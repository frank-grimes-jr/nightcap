# 0073 — Additional item advancement through combat experience

Date: 2026-10-30. Status: candidate implementation; not released or owner accepted.

The owner requested a second path alongside the Reforging Box and selected a
4–8-hour Normal-to-top target. The additional path uses the Power Source slot as
a training location, without granting another equipment slot's combat benefits.
It keeps ordinary Ascended and Hunt Ascension families and existing output stats.

Use full modified combat XP before AA allocation and character-cap clamping.
Exclude gray/unknown con, noncombat, resurrection and owned/mercenary/swarm victims.
Character and AA awards remain unchanged. Normalize against the native
level-squared kill formula at the dated 0.65 normal-XP baseline. Candidate costs
80/160/240 reference-kill equivalents total480; 60–120 equivalents/hour models
4–8 hours. This is an explicit assumption, not a measured live completion time.

Store versioned current-item-ID-bound progress in existing inventory metadata,
which already travels through normal inventory, corpse and trade paths. Runtime
serials regenerate at login, so reject a GUID-keyed progress side table. Repair
and test native multi-key metadata loading so XP can coexist with grip metadata.
This requires paired consumers; old binaries are not a safe rollback after items
have earned multi-key data. Disabling new awards must preserve earned progress.

Use one InnoDB UPDATE for progress, target identity and any default-color change,
conditioned on every saved inventory field except the regenerated runtime GUID.
Retain the saved GUID and all other instance fields. Reject stale preimages; on
uncertain writes or publication quarantine the session before further saves.
Do not delete/summon, retry an uncertain award, restore player snapshots or mint
extra rewards. Exact numeric/name/catalog checks must establish all four tiers.

Removing an item retains partial progress. Combining copies consumes their partial
progress and creates the same clean output as before; partial XP is neither pooled
nor copied. This avoids a second progression conversion currency and preserves
the existing physical-copy costs. `#itemxp` reports saved progress and availability.

The feature defaults off behind Items:PowerSourceItemXP. Source promotion and
native compilation do not authorize production deployment. Evidence and outstanding
QA are tracked in docs/items/power-source-xp/PLAN.md; player-visible wiki and
installed knowledge updates remain completion requirements.
