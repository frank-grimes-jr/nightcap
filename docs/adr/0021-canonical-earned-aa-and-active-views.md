# 0021: Keep canonical earned AAs separate from their usable view

Date: 2026-09-13. Status: implementation direction; native reproduction captured.
The five-fix test candidate remains unchanged. No ownership feature is deployed.

## Native finding

With the full AA catalog intact, a synthetic character owns Natural Durability's
six ranks (24 nominal points), has five expended points and 17 unspent points.
Restricting the character's expansion mask to Luclin leaves ranks 1–3 eligible;
ranks 4–6 require expansion 15. Native reload drops the entire ability instead of
exposing its usable prefix. Native SaveAA then reports only five spent points,
although the database still contains all six earned ranks. Restoring expansion
access and loading/saving restores six effective ranks and the 29-point total.

This is an active-view/accounting failure, not lost saved ownership or lost wallet
currency. The current balance clone has modern AA scaling disabled; broader XP or
purchase effects are not asserted from this reproduction.

The control changes only the synthetic client's expansion mask, never the AA
catalog, live era, server rules or real character data. Source: native
`ZoneDatabase::LoadAlternateAdvancement`, `AA::Ability::GetMaxLevel`, and
`Client::SaveAA`. Evidence: `docs/balance/aa-owned-view-*`.

## Direction

Retain `character_alternate_abilities` as canonical earned ownership and keep the
complete underlying rank catalog. Derive a separate effective rank view in the
client, bounded by earned rank count and current eligibility. Expansion policy
must restrict offering/use without truncating the source rank chains. This avoids
creating a second durable copy of every purchase merely to preserve the first.

The earlier offline earned/active model remains useful for allocation and impact
validation. Its separate logical views do not require physically rewriting the
canonical purchase rows. The earlier isolated catalog-projection experiment is
not the deployment path for this approach. ADR0019's preservation and lifecycle
requirements remain in force.

Before enabling curated caps, native code must cover the complete lifecycle:

- Load the greatest eligible prefix while retaining the full earned row.
- Save full earned ranks and charges; total active plus suspended nominal costs
  and existing expended-AA cost without changing the wallet.
- Reject repurchase of an earned rank, including after temporary suspension.
- Preserve new legitimate purchases and explicit grants.
- Make refund/reset/class-release paths remove the relevant earned rows as well
  as the effective view, so later unlocks cannot resurrect removed purchases.
- Preserve charges across suspension; consumption must not replenish charges or
  count expended cost twice.
- Handle catalog inconsistencies and persistence errors explicitly, without
  silently lowering ownership or reporting a successful partial currency change.
- Apply curated availability through the declarative era workflow, preserving
  the full catalog needed for accounting and restoration.

The first control is deliberately failing the desired behavior. Simply changing
the loader to return three ranks would let the current SaveAA overwrite the six-
rank canonical row, making the problem worse. Loader and persistence changes must
be tested together; lifecycle integration is required before promotion.

Permanent removal and compensation remain a separate policy decision. Temporary
expansion suspension must never implicitly refund earned points.

## Native integration points

| Path | Required responsibility |
|---|---|
| `ZoneDatabase::LoadAlternateAdvancement` | Read canonical ownership successfully before replacing session state; validate exact rank count and derive the eligible prefix |
| `Client::SaveAA` | Persist full earned counts/charges and account for suspended cost; do not infer refunds from a smaller effective map |
| `HasAlreadyPurchasedRank`, purchase/grant/toggle paths | Recognize already-earned ranks and keep wallet, effective state and persisted ownership consistent on failure |
| `RefundAA`, `ResetAA`, `PurgeAfterClassRelease` | Operate on earned ownership, preserve grant-only/shared-class behavior, and prevent later resurrection |
| `RemoveExpendedAA`, `ResetAlternateAdvancementRank`, charge consumption | Remove or update canonical ownership even when a family is inactive; preserve native expended-cost accounting |

`GetRankByPointsSpent` returns the chain's last rank for an oversized count, so
checking only for a non-null rank is insufficient. Validate that the returned
rank's `current_value` exactly matches the saved earned count before trusting its
cost. A truncated or missing source catalog must not silently reprice ownership.
