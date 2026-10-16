# ADR 0008: keep AA buffs on native duration rules

> Superseded implementation scope (October 15, 2026): the current integrated
> `GetBuffDurationForTarget` blanket permanence policy bypassed this older direct-AA
> exclusion. The new [temporary AA repair](../releases/aa-temporary-buffs-20261015/README.md)
> restores timers there and includes passive procs and recursive recourse/trigger
> spells, with one-tick expiry for affected saved permanent sentinels. Ordinary
> player/pet blessings remain permanent. Owner-authorized main/OVH deployment
> completed October16; running hashes and preservation checks pass. Owner
> gameplay acceptance remains pending.

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Status: candidate verified in the isolated diagnostic; not deployed.

## Decision

Exclude spells directly referenced by the zone's loaded AA ranks from Nightcap's
long self-buff duration override. Apply their native duration formula and existing
focus bonuses. Keep the existing discipline and short-box exclusions. Ordinary
preparation self-buffs retain the long duration override.

The classifier consults current AA rank data when applying an eligible self-buff.
This avoids a stale cache after AA reload. It classifies by spell identity rather
than casting slot: AA activation has several native casting paths, including
instant paths. A spell shared with an AA consequently retains native timing even
when cast from another source. Triggered recourse spells are not transitively
classified by this change; further temporary-buff coverage remains open.

## Evidence and consequences

The prior isolated baseline gave Tenacity and Twincast million-tick durations.
Eighteen matched controls now verify native AA durations, focus rounding, expiry,
cooldowns, and preserved Arch Shielding/Resolution preparation durations. Six
idle/Frenzied Devastation/Divine Arbitration controls remain identical.

Normal timing does not eliminate maximum-rank Tenacity's native HP drain. Its
low-health unhealed control still dies. This is a correction to duration policy,
not a claim that Tenacity is safe to activate at any health or that boss balance
is solved. Celestial Regeneration's separate target-level rejection is unchanged.

The reviewed server mirror is compiled as a separate spells object and linked
only into the isolated diagnostic. Existing server objects and live services are
untouched. Promotion still requires the project's in-game QA gate.
