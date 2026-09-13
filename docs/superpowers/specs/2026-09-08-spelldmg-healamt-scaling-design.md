# SpellDmg / HealAmt as Master Output Scaling — Design

Date: 2026-09-08
Status: design (approved for spec review)
Epic/Issue: TBD (new GitHub issue — distinct pillar from #10)
Branch flow: `feature/spelldmg-healamt-scaling` → `dev` → `test` → `main`

## Goal

Make the item stats **SpellDmg** and **HealAmt** the single lever for caster and
healer output on Nightcap. Instead of retuning individual spell base values or
mob HP per era to keep content soloable, tune soloability from two knobs: a
per-tier gear grant and a stat cap. One stat pair drives both damage and healing.

This replicates what THJ did (not previously captured in the THJ blueprint): they
turned these two stats into percentage output multipliers so scaling a character
up — and keeping content soloable — is a couple of numbers rather than a
spreadsheet of spell/mob edits.

## Background — how the engine treats these stats today

`Mob::GetActSpellDamage` / `GetActSpellHealing` / `GetActDoTDamage` apply SpellDmg
and HealAmt through `Mob::GetExtraSpellAmt`
([akk-stack/code/zone/effects.cpp:366](../../../akk-stack/code/zone/effects.cpp)).
Stock behavior — which is exactly the "impossible to scale" problem — is:

- the bonus is scaled **down by cast time** (an instant nuke gets only 25% of it);
- it is **hard-capped at +50% of the spell's base value**, no matter how much you
  stack;
- and it only applies to spells within **5 levels** of the caster.

Seven `Spells:*` rules change this behavior. On the live DB **all are at stock
defaults (off)** (verified 2026-09-08 against `rule_values`):

| Rule | Default | Effect when on |
|---|---|---|
| `Spells:ItemExtraSpellAmtCalcAsPercent` | off | SpellDmg/HealAmt applied as **percent of base** (`base * stat / 100`) instead of flat |
| `Spells:FlatItemExtraSpellAmt` | off | bypass the cast-time proportion **and** the +50%-of-base cap (early return in `GetExtraSpellAmt`) |
| `Spells:IgnoreSpellDmgLvlRestriction` | off | drop the 5-level spread; scale spells at any level |
| `Spells:DOTsScaleWithSpellDmg` | off | DoT ticks scale with SpellDmg |
| `Spells:HOTsScaleWithHealAmt` | off | HoT ticks scale with HealAmt |
| `Spells:DOTBonusDamageSplitOverDuration` | on | DoT bonus split across duration (keep — avoids front-loading) |
| `Spells:HOTBonusHealingSplitOverDuration` | on | HoT bonus split across duration (keep) |

`ItemExtraSpellAmtCalcAsPercent` + `FlatItemExtraSpellAmt` **together** yield the
clean result: `bonus = base * min(sum SpellDmg, cap) / 100`, uncapped by cast time
or the +50% rule. One rule pair covers both damage (`GetSpellDmg()`) and healing
(`GetHealAmt()`).

The summed item stat is clamped to `Character:ItemSpellDmgCap` /
`Character:ItemHealAmtCap` (both **250** today,
[ruletypes.h:96](../../../akk-stack/code/common/ruletypes.h)) **during bonus
accumulation**, gated to client/bot/merc
([bonuses.cpp:241](../../../akk-stack/code/zone/bonuses.cpp) and
`CalcCappedItemBonus` at :358). `Client::GetSpellDmg()`/`GetHealAmt()` then return
that already-clamped value ([client.h:692](../../../akk-stack/code/zone/client.h)).
So the cap is a true ceiling on the summed item stat for players — and NPCs sit
outside the clamp, reinforcing the NPC non-goal.

**Tier system.** Tier copies are pre-generated DB rows (base id + 200k/400k/600k
for Polished/Exalted/Ascended), created by
[eq-solo-gm/scripts/tiered_loot_setup.sql](../../../eq-solo-gm/scripts/tiered_loot_setup.sql).
`NPC::AddLootDrop` just rolls a chance and swaps in the higher-id copy
([loot.cpp:288](../../../akk-stack/code/zone/loot.cpp)). The generator already
lists `spelldmg`/`healamt` in its "offense" family — but as
`IF(spelldmg>0, ROUND(spelldmg*p_offn), spelldmg)`. Classic base items are 0, so
it multiplies zero: **tiers add no SpellDmg/HealAmt today.**

No client work is needed — RoF2 displays SpellDmg/HealAmt item stats natively.

## Design

### 1. Mechanism — rules (no C++)

Set on the live ruleset (idempotent `rule_values` upsert):

- `Spells:ItemExtraSpellAmtCalcAsPercent = true`
- `Spells:FlatItemExtraSpellAmt = true`
- `Spells:IgnoreSpellDmgLvlRestriction = true`
- `Spells:DOTsScaleWithSpellDmg = true`
- `Spells:HOTsScaleWithHealAmt = true`
- leave both `*SplitOverDuration` at their default `true`.

Result: SpellDmg/HealAmt become uncapped percent-of-base multipliers on all
direct spells, heals, DoTs, and HoTs.

### 2. Source — stamp onto tier gear (SQL)

Extend `gen_loot_tier` in `tiered_loot_setup.sql` to **add** a flat per-tier
SpellDmg and HealAmt to worn tier gear. Add one parameter, `p_spellstat`, and an
UPDATE that runs after the existing offense multiply (which stays, for the rare
base item that already carries these stats):

```sql
UPDATE tg SET
  spelldmg = spelldmg + p_spellstat,
  healamt  = healamt  + p_spellstat
  WHERE slots > 0;          -- worn gear only; never bags (bagslots-only rows)
```

Applied at the same three call sites, and mirrored into the Ascended-epic block
(`tge`, base+800000) with the Ascended value so quest epics stay consistent.

Both stats get the same per-tier value (a single dial per tier). It is stamped on
**all** worn tier gear regardless of class — harmless on pure-melee gear because
the percent only applies when the wearer actually casts.
`// ponytail: flat per-tier on all worn slots; restrict to caster-usable slots
only if melee-gear bloat becomes a real problem.`

### 3. Dials & calibration (cap-as-dial)

Effective output multiplier = `min(sum of equipped SpellDmg, ItemSpellDmgCap)` as
a percent; same for HealAmt. Two knobs, clear roles:

- **`ItemSpellDmgCap` / `ItemHealAmtCap` — the primary dial.** This is the ceiling
  on output and the number to move for "how strong is a fully-geared solo player."
- **Per-tier stamp — the ramp.** How fast gearing approaches the ceiling.

Per the approved lean, the cap is the main dial: stamp values are chosen so a
near-full top-tier set **saturates** the cap (so past full-gear you sit at the
ceiling, and the ceiling is what you tune), while lower tiers and partial sets
scale linearly beneath it.

**Starting calibration (tune in QA):**

| Knob | Start | Note |
|---|---|---|
| `ItemSpellDmgCap` / `ItemHealAmtCap` | 250 | +250% of base at cap (≈3.5× output). Lower if it trivializes; raise for more power. |
| Polished stamp | +5 / item | |
| Exalted stamp | +12 / item | |
| Ascended stamp (+ epics) | +20 / item | ~13 worn Ascended pieces ≈ 260 → saturates the 250 cap |

A fresh/naked character has 0 → vanilla Classic output. Only geared casters
approach the cap.

### 4. Scope / non-goals

- **In:** direct spell damage, direct heals, DoTs, HoTs — for players (and by
  extension bots/mercs, which read the same `GetSpellDmg()`/`GetHealAmt()`).
- **Out:** melee/ranged output. It uses different stats (weapon ratio, `SkillDmg`,
  ATK) and is its own future slice. A pure-melee character gains nothing from this
  slice — that remains an open gap, called out explicitly so it is not mistaken
  for done.
- **NPCs unaffected:** NPC spell output scales via a separate
  `GetSpellScale()`/`GetSpellFocusDMG()` path, untouched here.

### 5. Interactions & risks

- Percent scaling stacks **multiplicatively** with focus effects (Improved Damage,
  Cleric innate 5% heal focus) and additively/multiplicatively with crit doublers.
  The cap is the thing that bounds the blow-up — which is why calibration is
  "pick the cap," not "audit every focus."
- Confirm no `int64` overflow at max base × max percent (safe at these magnitudes:
  base spells are ≤ ~5 digits; ×3.5 stays well within int64).
- Multiclass: every character benefits when casting any of their held classes'
  spells; no class-gating needed.
- **Heroic INT/WIS also feed these stats** via
  `Character:HeroicIntelligenceIncreaseSpellDmgMultiplier` /
  `...WisdomIncreaseHealAmtMultiplier` ([bonuses.cpp:5824,5837](../../../akk-stack/code/zone/bonuses.cpp)),
  0 by default. Since Ascended gear grants heroic stats (item-tiers #8), verify in
  QA whether that contribution lands inside or outside the item cap before setting
  the multipliers non-zero — otherwise heroic could quietly bypass the cap-as-dial.
- The change is global (rules + regenerated items); it affects every existing
  character's geared output immediately on deploy.

## Testing & QA

This slice adds **no new C++ logic** — it configures the existing formula and
generates data — so verification is data assertion + in-game parse rather than new
unit code.

1. **SQL verification (runnable check).** After regeneration, assert:
   - a known caster item's Polished/Exalted/Ascended copies carry the expected
     `spelldmg`/`healamt` (base + per-tier stamp);
   - the base item (id < 200000) is unchanged (still 0);
   - no bag (`bagslots>0, slots=0`) received the stamp.
2. **In-game parse spike (test-promotion QA).** For a caster test character at
   each state — no tier gear (baseline), partial set, near-full set — at each tier:
   - parse a fixed nuke and a fixed heal; confirm output ≈ `base * (1 + effSpellDmg/100)`;
   - confirm the cap clamps once summed SpellDmg exceeds it;
   - confirm a DoT and a HoT scale (and are split across duration);
   - confirm a **melee-only** character's output is unchanged (scope guard).

## Rollout

Order (all reversible; take a manual PEQ backup first):

1. Edit `tiered_loot_setup.sql` (add `p_spellstat` param + UPDATE + epic mirror).
2. Set the five rules + confirm the two caps in `rule_values`.
3. Regenerate tiers: run the SQL, then `./bin/shared_memory`, then restart zones.
4. Run SQL verification; then the in-game parse spike on `dev`.

Reversibility: rules revert to `false`; re-run the generator with `p_spellstat=0`
to strip the stamp. No schema change, no binary change.

## Tracking

- New GitHub issue (own pillar; link this spec).
- Add a "Spell Damage / Healing scaling" section to
  `.claude/skills/eqemu/thj-blueprint.md` (currently unlisted THJ mechanic).
- Rules + SQL but gameplay-affecting → normal `dev → test → main` gate with a
  written in-game QA spike before `test`.
