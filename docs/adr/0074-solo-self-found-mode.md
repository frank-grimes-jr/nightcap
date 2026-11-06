# Solo self-found (SSF) mode

Date: November 1, 2026. Status: implementation candidate; not built, deployed or
owner-accepted.

## Intent

Offer an opt-in, permanent, per-character mode where the character owns only what
it found or earned itself. The owner's requirements: no trading with players, no
bazaar, AA experience off by default (the player turns it on with the native AA
window +/-), and the normal (unboosted) experience rate.

## Decision

- A row in `character_ssf` (one table, primary key `character_id`) marks a
  character as SSF. The zone loads it on ZoneEntry next to the multiclass mask.
  If the query fails the character is treated as normal, so a zone deployed
  before the table exists changes nothing.
- The character opts in at the Ancient Chronicler (East Commonlands tunnel) by saying `walk alone` at
  level 1 and confirming a popup. Only a GM can reverse it, by deleting the row.
- One gate, `Client::SSFBlocked(other)`, refuses the action with a red message
  when this character or the other client is SSF. It covers:
  - player trade (request and ack)
  - native trader, buyer and barter, and trader purchases (including Commonlands
    escrow purchases)
  - `#bazaar` (Commonlands escrow posting and the panel)
  - player parcels in both directions (the recipient is looked up by name, so
    offline characters are covered)
  - shared bank items and coin
  - guild bank
  - group and raid invites and accepts with other players
- NPC and bot trades are untouched, so quest turn-ins still work. Bots and
  mercenaries can still group.
- Normal XP is unchanged: SSF uses the current PEQ seed rate, which is already
  unboosted. AA XP is where the server is boosted. For SSF characters
  `Client::PassiveAAPercent()` returns 0, so 0% allocation earns no AA. New
  characters already start at 0%, and joining SSF forces 0%. At N% the character
  gets the server's level-scaled AA pace at N% with no passive blend.

## Consequences

- SSF is a per-character exception to ADR 0054 universal FreeTrade. The global
  item policy is unchanged.
- No `ruletypes.h` change. This is a zone binary, one table and one quest script.
- Quest rewards (epic AA points, veteran/attunement ability grants) are not
  leveling AA and still apply.
- A refused shared-bank coin move leaves the client's coin display stale until
  it zones. Server values never change.
- A level-1 character could have received gear before swearing the oath.
  Accepted for now; a never-traded check can be added if it matters.

## Alternatives rejected

- Server-wide SSF: the owner wants it as a choice.
- A choice during character creation: the RoF2 `CharCreate_Struct` has no free
  field.
- A 1.0x XP multiplier: "default rate" here means the current unboosted seed,
  not live EQ's rate.
- Data buckets instead of a table: GM tools and ad-hoc SQL need a simple
  authoritative row, as with `character_multiclass`.
