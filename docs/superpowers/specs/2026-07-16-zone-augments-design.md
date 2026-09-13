# Zone Augments — Design Spec (#26)

Date: 2026-07-16
Status: Approved (design); pending spec review → implementation plan

## Goal

Give every genuinely-challenging zone a chase reward: a **zone-specific augment**
that pumps **heroic + advanced stats** into a player's gear. Augments are the
third and final layer of the THJ end-game power budget, after gear multipliers
(#25) and heroic-on-gear (#8). Per the owner: solo server — "don't make it
impossible, but make it worth the grind."

## Non-negotiable constraint (drove the whole design)

The server is **level-50 (Classic) locked**. Aug power must **not** be tied to
expansion or a zone's original level, or a capped level-50 would farm a trivial
newbie zone for aug rolls. Aug eligibility and tier are tied to a zone's **actual
difficulty for a level-50 character**, and trivial zones drop **nothing**.

## Content model

Custom augments (not reused PEQ augs — controlled stats required). Each difficulty
tier has a **caster / melee / priest** variant, matching the three combat roles:

| Variant | Heroic stats | Resource | Advanced (slight) |
|---|---|---|---|
| Caster | heroic INT + heroic WIS | +mana | spell damage |
| Melee  | heroic STR + heroic STA (+DEX) | +hp | melee damage |
| Priest | heroic WIS + heroic STA | +mana | heal amount |

(Melee's "resource" is +hp — the survivability analog to caster/priest mana —
so melee augs don't stack two offense stats; their offense is heroic STR + the
slight melee-damage line.)

- Augs are **NO-DROP, attunable** (loot → socket; not a tradeable economy item).
- Item type = augment (itemtype 54); `augtype` bitmask = dedicated slot type (below).

### Stat scaling by tier (8 tiers)

Values scale linearly across tiers `t = 1..8` (starting proposals — tunable):

| Field | Tier 1 | Tier 8 | Formula |
|---|---|---|---|
| Heroic primary (each of the two stats) | 5 | 30 | `round(5 + 25*(t-1)/7)` |
| Resource (+mana; melee = +hp) | 20 | 100 | `round(20 + 80*(t-1)/7)` |
| Advanced (spell dmg / melee dmg / heal amt) | 1 | 13 | `round(1 + 12*(t-1)/7)` |

Rationale: a full set of **top-tier** augs (one per Ascended slot) roughly doubles
the heroic a character gets from Ascended gear — the intended end-game power spike.
Bottom-tier augs are a small nudge that gets a fresh level-50 started.

## Difficulty tiers (manual, difficulty-gated)

~**8 tiers**. Built by **draft + curate**, not typed from scratch:

1. **Eligibility gate:** a zone is aug-eligible only if it's a real fight at 50.
   Signal = the zone's **characteristic mob level** (median of its spawn levels),
   NOT max — 434/435 zones have *some* 48+ mob, so max would let newbie zones
   through on a lone high named. Gate ≈ median mob level ≥ ~48. Ineligible zones
   drop nothing.
2. **Draft:** bucket eligible zones into 8 tiers by that difficulty signal
   (median mob level, group vs raid content).
3. **Curate:** hand-review the draft — drop special/broken zones, fix outliers,
   confirm the "2–3 on-par zones share a caster/melee/priest set" grouping. The
   **zone→tier list is reviewed by the owner before it goes live.**

Each tier = 3 augs (caster/melee/priest) → **~24 custom augs total**.

## Slot compatibility

Existing gear has assorted aug-slot types (1–21 all in use). To make zone augs
usable without colliding with the 13,683 existing PEQ augs:

- Use a **dedicated aug slot type = 22** (free; no existing aug fits it).
- Add **one type-22 "Nightcap" aug slot** to **Ascended** tiered gear (in the
  first free `augslotNtype` on each item), in `tiered_loot_setup.sql`.
- All zone augs are type 22 → they fit only the new Ascended slot, and existing
  augs can't occupy it.

Ascended-only keeps augs as the top-end layer (you need Ascended gear to socket
them). Extending to Exalted is a one-line change if wanted later.

## Distribution & drop rate

- Reuse the **`global_loot`** plumbing (already used for Essence of Ascension).
- **One `global_loot` entry per eligible zone**, scoped to that zone, dropping
  that zone's aug **set** (roll one of the 3 role variants on a hit).
- **Zone-wide:** any mob kill in the zone rolls the chance.
- **Rule-tunable rate**, proposed defaults by tier band:
  - Tiers 1–4: ~**1.0%**
  - Tiers 5–6: ~**0.5%**
  - Tiers 7–8: ~**0.3%**
  Feel: ~100–300 kills per aug — a grind, solo-doable, and you always know which
  zone drops what you need.

## Custom aug items — ID scheme

- Augment items: **900101–900124** (24 augs; after Essence at 900000). Well under
  the RoF2 link cap (1,048,575).
- `global_loot` / `loottable` / `lootdrop` rows in the existing 99xxxx custom range.

## Scope boundaries (YAGNI — explicitly out)

- No aug **upgrade/combine** path (drop-and-socket only).
- No aug **removal-cost** mechanic (standard distiller behavior stands).
- No per-aug **focus effects** (stats only, for now).
- Not touching the existing 13,683 PEQ augs.

## Deliverables (for the implementation plan)

1. `eq-solo-gm/scripts/zone_augments.sql` — creates the 24 custom augs (scaled per
   tier), the per-zone `global_loot`/loottable/lootdrop rows, and adds the type-22
   slot to Ascended gear (or folds that into `tiered_loot_setup.sql`).
2. A generated + curated **zone→tier assignment** (draft from median mob level;
   owner-reviewed).
3. Drop-rate rule(s) in `rule_values` (or reuse `global_loot.probability`).
4. shared_memory regen + zone restart; verify an aug drops, sockets into an
   Ascended item, and its heroic/advanced stats apply (`#showstats`).
5. CHANGES.md + thj-blueprint.md updates.

## Open items to resolve during implementation

- Confirm slot type 22 is truly free (no existing aug's `augtype` bit 22).
- Exact median-mob-level threshold and the curated zone list (owner review gate).
