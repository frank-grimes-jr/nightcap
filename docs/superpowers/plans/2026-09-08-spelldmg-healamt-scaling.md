# SpellDmg / HealAmt Master Output Scaling — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the item stats SpellDmg and HealAmt into percent-of-base output multipliers stamped onto tier gear, so caster/healer power (and content soloability) is tuned from an item-stat cap instead of per-spell/per-mob retuning.

**Architecture:** Flip five existing `Spells:*` rules (percent mode, no caps, level-agnostic, DoT/HoT) so the engine's existing `GetExtraSpellAmt` path applies these stats as clean percentage multipliers; extend the tier-item generator SQL to *add* a flat per-tier SpellDmg/HealAmt to worn tier gear (Classic base items are 0, so the current multiply is a no-op); leave the `Character:ItemSpellDmgCap`/`ItemHealAmtCap` (250) as the primary "cap-as-dial" knob. No C++ and no client change.

**Tech Stack:** MariaDB (PEQ schema), EQEmu rule_values, `tiered_loot_setup.sql` generator, EQEmu `shared_memory` regeneration, Docker (akk-stack).

Spec: [docs/superpowers/specs/2026-09-08-spelldmg-healamt-scaling-design.md](../specs/2026-09-08-spelldmg-healamt-scaling-design.md)

## Global Constraints

- Database: container `akk-stack-mariadb-1`, user `eqemu`, password `eqemu`, db `peq` (MariaDB on host port 3307; use the container, not host port).
- **No C++ and no client (`dinput8.dll`) changes.** Rules + SQL only.
- Scope: direct spells, heals, DoTs, HoTs only. Melee/ranged output is out of scope. NPCs must remain unaffected (they scale via a separate `SpellScale`/`FocusDMG` path).
- Take a manual PEQ backup before any DB apply: `powershell -NoProfile -ExecutionPolicy Bypass -File tools/backup-peq.ps1` (run from `E:\EQ_Local_Dev`).
- All SQL must be idempotent (upserts; the generator already `DELETE`s its id band before re-inserting).
- Reversibility: rules revert to `false`; re-run the generator with the stamp value `0` to strip the stat. No schema or binary change.
- Rule ruleset_id is `1` (matches the existing `Zone:LootTier*` rows).
- Per-tier stamp starting values (calibration, tune in QA): Polished **+5**, Exalted **+12**, Ascended (and Ascended epics) **+20**, applied to both SpellDmg and HealAmt. Cap starts at **250** each.
- Branch flow: `feature/spelldmg-healamt-scaling` → `dev` → `test` → `main`. A written in-game QA spike is required before promoting to `test`.
- Commit convention: `type(scope): subject`, footer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

## File Structure

- Create: `eq-solo-gm/scripts/spelldmg_healamt_scaling.sql` — the five rule flips + the two cap dials (idempotent upsert).
- Modify: `eq-solo-gm/scripts/tiered_loot_setup.sql` — add a `p_spellstat` param to `gen_loot_tier`, an UPDATE that adds SpellDmg/HealAmt to worn tier gear, the three CALL args, and the Ascended-epic mirror. Update the header comment.
- Create: `eq-solo-gm/scripts/verify_spelldmg_healamt.sql` — the runnable check: asserts rules set, tier worn gear stamped, bags untouched.
- Create: `docs/qa/2026-09-08-spelldmg-healamt-qa.md` — the in-game QA spike for the `test` promotion.
- Modify: `.claude/skills/eqemu/thj-blueprint.md` — add the "Spell Damage / Healing scaling" pillar.
- Modify: `CHANGES.md` — changelog entry.

---

## Task 1: Author the SQL (rules, tier stamp, verification)

**Files:**
- Create: `eq-solo-gm/scripts/spelldmg_healamt_scaling.sql`
- Modify: `eq-solo-gm/scripts/tiered_loot_setup.sql`
- Create: `eq-solo-gm/scripts/verify_spelldmg_healamt.sql`

**Interfaces:**
- Produces: `gen_loot_tier(p_off, p_hpmana, p_core, p_endur, p_offn, p_spellstat, p_heroic, p_tag, p_bagslot, p_bagwr, p_bagsize)` — note the new `p_spellstat INT` inserted after `p_offn`. Task 2 applies these files.

- [ ] **Step 1: Establish the red state (stat currently absent, rules off)**

Run (confirms the stamp isn't applied yet and the percent rule is off — the problem we're fixing). The check is the exact stamp pattern, not `spelldmg>0`: the full items table already has later-expansion base items carrying SpellDmg, so `>0` is not zero today — but no worn item has both `spelldmg=20` AND `healamt=20` until the stamp lands:

```bash
docker exec akk-stack-mariadb-1 mysql -ueqemu -peqemu peq --table -e "SELECT COUNT(*) AS ascended_base0_stamped_20 FROM items a JOIN items b ON b.id = a.id - 600000 WHERE a.id BETWEEN 600001 AND 799999 AND a.slots>0 AND b.spelldmg=0 AND b.healamt=0 AND a.spelldmg=20 AND a.healamt=20;"
```

Expected: `ascended_base0_stamped_20` = 0 before the change (base-0 items have unstamped tier copies); Task 2 Step 6 re-checks and expects > 1000 after.

- [ ] **Step 2: Create the rules file**

Create `eq-solo-gm/scripts/spelldmg_healamt_scaling.sql`:

```sql
-- =============================================================================
-- SpellDmg / HealAmt master output scaling — rules + dials
-- Run:  docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < spelldmg_healamt_scaling.sql
-- Then: apply tiered_loot_setup.sql, regenerate shared memory, restart zones.
-- Spec: docs/superpowers/specs/2026-09-08-spelldmg-healamt-scaling-design.md
--
-- Turns SpellDmg/HealAmt into uncapped percent-of-base multipliers on spells,
-- heals, DoTs and HoTs, and pins the item-stat caps as the primary "cap-as-dial"
-- soloability knob. Reverse by setting the five Spells rules back to 'false'.
-- =============================================================================
INSERT INTO rule_values (ruleset_id, rule_name, rule_value, notes) VALUES
 (1,'Spells:ItemExtraSpellAmtCalcAsPercent','true','SpellDmg/HealAmt applied as percent of base spell value'),
 (1,'Spells:FlatItemExtraSpellAmt','true','Bypass cast-time proportion and the +50%-of-base cap'),
 (1,'Spells:IgnoreSpellDmgLvlRestriction','true','Scale spells regardless of the 5-level spread'),
 (1,'Spells:DOTsScaleWithSpellDmg','true','DoT ticks scale with SpellDmg'),
 (1,'Spells:HOTsScaleWithHealAmt','true','HoT ticks scale with HealAmt'),
 (1,'Character:ItemSpellDmgCap','250','PRIMARY DIAL: ceiling on summed item SpellDmg (= percent at cap)'),
 (1,'Character:ItemHealAmtCap','250','PRIMARY DIAL: ceiling on summed item HealAmt (= percent at cap)')
ON DUPLICATE KEY UPDATE rule_value=VALUES(rule_value), notes=VALUES(notes);
```

- [ ] **Step 3: Add the `p_spellstat` parameter to the generator**

In `eq-solo-gm/scripts/tiered_loot_setup.sql`, change the `gen_loot_tier` signature. Find:

```sql
    IN p_offn    DECIMAL(4,2),  -- offense: damage/attack/accuracy/spelldmg/healamt/... (conservative)
    IN p_heroic  DECIMAL(4,2),  -- heroic = this fraction of the scaled stat (Ascended 0.25; else 0)  #8
```

Replace with:

```sql
    IN p_offn    DECIMAL(4,2),  -- offense: damage/attack/accuracy/... (conservative)
    IN p_spellstat INT,         -- flat SpellDmg/HealAmt ADDED to worn gear per tier (base is ~0)
    IN p_heroic  DECIMAL(4,2),  -- heroic = this fraction of the scaled stat (Ascended 0.25; else 0)  #8
```

- [ ] **Step 4: Add the stamp UPDATE inside the generator**

In the same procedure, find the end of the offense block:

```sql
      strikethrough=IF(strikethrough>0,ROUND(strikethrough*p_offn),strikethrough), damageshield=IF(damageshield>0,ROUND(damageshield*p_offn),damageshield);
```

Immediately after that statement, add:

```sql

    -- Master output scaling (spec 2026-09-08): ADD flat SpellDmg/HealAmt to worn
    -- tier gear. Base Classic items are ~0 so the offense multiply above is a
    -- no-op; this is the real source. Worn slots only (never bags).
    -- ponytail: flat on all worn slots regardless of class; percent only applies
    -- when the wearer actually casts, so it is harmless on pure-melee gear.
    UPDATE tg SET
      spelldmg = spelldmg + p_spellstat,
      healamt  = healamt  + p_spellstat
      WHERE slots > 0;
```

- [ ] **Step 5: Update the three CALL statements with the stamp values**

Find:

```sql
--                       hpmana core  endur offn  heroic tag             bag: slot wr size
CALL gen_loot_tier(200000, 1.45, 1.35, 1.07, 1.10, 0.00, ' (Polished)', 2,  25, 3);
CALL gen_loot_tier(400000, 1.90, 1.65, 1.13, 1.20, 0.00, ' (Exalted)',  4,  50, 4);
CALL gen_loot_tier(600000, 2.40, 2.00, 1.20, 1.35, 0.25, ' (Ascended)', 6, 100, 4);  -- = THJ Legendary (+25% heroic)
```

Replace with (note the new spellstat column 5/12/20 inserted after `offn`):

```sql
--                       hpmana core  endur offn  spellstat heroic tag             bag: slot wr size
CALL gen_loot_tier(200000, 1.45, 1.35, 1.07, 1.10,  5, 0.00, ' (Polished)', 2,  25, 3);
CALL gen_loot_tier(400000, 1.90, 1.65, 1.13, 1.20, 12, 0.00, ' (Exalted)',  4,  50, 4);
CALL gen_loot_tier(600000, 2.40, 2.00, 1.20, 1.35, 20, 0.25, ' (Ascended)', 6, 100, 4);  -- = THJ Legendary
```

- [ ] **Step 6: Mirror the stamp into the Ascended-epic block**

Find the end of the Ascended-epic offense UPDATE (the `tge` block):

```sql
  strikethrough=IF(strikethrough>0,ROUND(strikethrough*1.35),strikethrough), damageshield=IF(damageshield>0,ROUND(damageshield*1.35),damageshield);
```

Immediately after that statement, add:

```sql
-- Master output scaling: Ascended epics get the same +20 SpellDmg/HealAmt as T4 Ascended.
UPDATE tge SET spelldmg = spelldmg + 20, healamt = healamt + 20 WHERE slots > 0;
```

- [ ] **Step 7: Update the generator header comment**

Find the header line:

```sql
--   Offense (dmg/atk/acc/spelldmg/healamt/...): x1.10 / x1.20 / x1.35
```

Replace with:

```sql
--   Offense (dmg/atk/acc/...):  x1.10 / x1.20 / x1.35
--   SpellDmg / HealAmt: FLAT +5 / +12 / +20 ADDED to worn gear (spec 2026-09-08);
--     base Classic items are ~0 so a multiply is a no-op. Tuned so a near-full
--     top-tier set saturates Character:ItemSpellDmgCap (the primary dial).
```

- [ ] **Step 8: Create the verification script**

Create `eq-solo-gm/scripts/verify_spelldmg_healamt.sql`:

```sql
-- Verification for the SpellDmg/HealAmt scaling slice. Run AFTER applying both
-- scripts and regenerating tiers. Checks 1-2 confirm rules/caps; checks 3-5 prove
-- the STAMP by joining each tier copy to its base item (id - offset), so a
-- pre-existing offense-multiply coincidence cannot satisfy them. The Ascended
-- band (offset 600000) is the representative check.
SELECT 'rules_true (expect 5)' AS check_name, COUNT(*) AS result
FROM rule_values
WHERE rule_name IN ('Spells:ItemExtraSpellAmtCalcAsPercent','Spells:FlatItemExtraSpellAmt',
                    'Spells:IgnoreSpellDmgLvlRestriction','Spells:DOTsScaleWithSpellDmg',
                    'Spells:HOTsScaleWithHealAmt')
  AND rule_value='true';
SELECT 'caps_present (expect 2, both 250)' AS check_name,
       GROUP_CONCAT(CONCAT(rule_name,'=',rule_value) ORDER BY rule_name) AS result
FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap');
-- Causation: Ascended copies of base-ZERO worn items must be exactly 20/20.
-- Before the stamp these are 0 (count 0); after, thousands. Expect > 1000.
SELECT 'ascended_base0_stamped_20 (expect > 1000)' AS check_name, COUNT(*) AS result
FROM items a JOIN items b ON b.id = a.id - 600000
WHERE a.id BETWEEN 600001 AND 799999 AND a.slots > 0
  AND b.spelldmg = 0 AND b.healamt = 0
  AND a.spelldmg = 20 AND a.healamt = 20;
-- Completeness: NO base-zero worn Ascended copy may remain unstamped.
-- Before the stamp this equals every base-0 worn item (huge); after, expect 0.
SELECT 'ascended_base0_unstamped (expect 0)' AS check_name, COUNT(*) AS result
FROM items a JOIN items b ON b.id = a.id - 600000
WHERE a.id BETWEEN 600001 AND 799999 AND a.slots > 0
  AND b.spelldmg = 0 AND b.healamt = 0
  AND NOT (a.spelldmg = 20 AND a.healamt = 20);
-- Bags never received the stamp: a bag tier copy's stats must equal its base's.
-- Expect 0 changed (the stamp is guarded slots>0).
SELECT 'bags_stat_changed (expect 0)' AS check_name, COUNT(*) AS result
FROM items a JOIN items b ON b.id = a.id - 600000
WHERE a.id BETWEEN 600001 AND 799999 AND a.bagslots > 0 AND a.slots = 0
  AND (a.spelldmg <> b.spelldmg OR a.healamt <> b.healamt);
```

- [ ] **Step 9: Commit**

```bash
git add eq-solo-gm/scripts/spelldmg_healamt_scaling.sql eq-solo-gm/scripts/tiered_loot_setup.sql eq-solo-gm/scripts/verify_spelldmg_healamt.sql
git commit -m "feat(loot): stamp SpellDmg/HealAmt onto tier gear + enable percent scaling

Add p_spellstat to gen_loot_tier (flat +5/+12/+20 on worn tier gear + Ascended
epics), and a rules script flipping SpellDmg/HealAmt to uncapped percent-of-base
multipliers. Cap-as-dial via Character:ItemSpellDmgCap/ItemHealAmtCap (250).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Deploy to dev and verify

**Files:** none modified (applies Task 1's SQL to the dev DB and reloads the server).

**Interfaces:**
- Consumes: `spelldmg_healamt_scaling.sql`, `tiered_loot_setup.sql`, `verify_spelldmg_healamt.sql` from Task 1.

- [ ] **Step 1: Back up PEQ**

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File tools/backup-peq.ps1
```

Expected: a new `backups/peq_YYYYMMDD_HHMMSS.sql.gz` (~44 MB) and an `OK` line in `backups/backup.log`.

- [ ] **Step 2: Apply the rules script**

```bash
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < eq-solo-gm/scripts/spelldmg_healamt_scaling.sql
```

Expected: no error output (exit 0).

- [ ] **Step 3: Apply the tier generator (regenerates the tier id bands)**

```bash
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < eq-solo-gm/scripts/tiered_loot_setup.sql
```

Expected: no error output (exit 0). This re-DELETEs and re-INSERTs the +200k/+400k/+600k/+800k id bands.

- [ ] **Step 4: Regenerate shared memory**

```bash
docker exec --workdir /home/eqemu/server akk-stack-eqemu-server-1 ./bin/shared_memory
```

Expected: it prints loading progress and exits 0 (writes the items shared-memory file the zones read).

- [ ] **Step 5: Restart the zone server so it loads the new items + rules**

```bash
docker restart akk-stack-eqemu-server-1
```

Expected: container restarts; give it ~30s to boot world + zones before QA. (Equivalent sanctioned target: `make restart` from `akk-stack/`, which restarts all containers.)

- [ ] **Step 6: Run the verification script (the green check)**

```bash
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq --table < eq-solo-gm/scripts/verify_spelldmg_healamt.sql
```

Expected:
- `rules_true` = 5
- `caps_present` = 2, both `=250`
- `ascended_base0_stamped_20` > 1000
- `ascended_base0_unstamped` = 0
- `bags_stat_changed` = 0

If any row is off, stop and diagnose before Task 3. (No commit — this task's deliverable is the verified running state on dev.)

---

## Task 3: QA spike + tracking

**Files:**
- Create: `docs/qa/2026-09-08-spelldmg-healamt-qa.md`
- Modify: `.claude/skills/eqemu/thj-blueprint.md`
- Modify: `CHANGES.md`

- [ ] **Step 1: Write the in-game QA spike**

Create `docs/qa/2026-09-08-spelldmg-healamt-qa.md`:

```markdown
# SpellDmg / HealAmt Scaling QA Spike

Date: 2026-09-08
Spec: docs/superpowers/specs/2026-09-08-spelldmg-healamt-scaling-design.md

## Setup
- A caster test character able to cast one fixed direct-damage nuke and one fixed
  direct heal, plus one DoT and one HoT. Note each spell's base value.
- Have Polished / Exalted / Ascended gear available for that character's slots.

## Steps & expected results
1. **Baseline (no tier gear):** cast the nuke and the heal. Output should equal
   the vanilla base (SpellDmg/HealAmt = 0). `#showstats` shows SpellDmg 0.
2. **Partial Ascended set:** equip ~6 Ascended pieces (SpellDmg ~120). Nuke and
   heal should be ~2.2x base (1 + 120/100). Confirm `#showstats` SpellDmg ~120.
3. **Near-full Ascended set:** equip enough that summed SpellDmg exceeds 250.
   `#showstats` SpellDmg should read exactly **250** (cap clamps). Nuke/heal
   should be ~3.5x base and NOT increase past this even with more gear.
4. **DoT / HoT:** cast the DoT and HoT at the near-full set; total damage/healing
   over the full duration should scale by the same percent (split across ticks,
   not front-loaded).
5. **Scope guard:** on a pure-melee character (no casting), confirm melee auto-attack
   and combat-ability damage are unchanged by any of the above.
6. **NPC guard:** confirm an NPC's spell output is unchanged (no client cap path).

## Report
- Measured nuke/heal at each state vs the expected multiplier.
- The `#showstats` SpellDmg/HealAmt at partial vs near-full (cap clamp proof).
- Whether DoT/HoT scaled and stayed split over duration.
- Any melee/NPC output that changed (should be none).
- Whether the resulting solo kill speed feels right, or the cap needs a nudge.
```

- [ ] **Step 2: Add the THJ blueprint pillar**

In `.claude/skills/eqemu/thj-blueprint.md`, after the "## 2. Item tiers" section, add:

```markdown
## 2a. Spell Damage / Healing scaling

**THJ spec:** SpellDmg/HealAmt are the master output dials — applied as percentage
multipliers so caster/healer power (and soloability) scales from those stats
rather than per-spell/per-mob retuning.

**Nightcap status (2026-09-08, spec `2026-09-08-spelldmg-healamt-scaling`):**
Implemented via the existing `Spells:*` rules (percent mode, no caps, level-agnostic,
DoT/HoT on) + a flat per-tier SpellDmg/HealAmt stamp on worn tier gear in
`tiered_loot_setup.sql` (+5/+12/+20). Primary dial = `Character:ItemSpellDmgCap`/
`ItemHealAmtCap` (250). Spells+heals only; melee output unscaled (separate future
slice); NPCs unaffected.
**Gaps:** melee/ranged output scaling; final cap/stamp calibration pending QA;
heroic-INT/WIS → SpellDmg path (0 today) not yet reconciled with the cap.
```

- [ ] **Step 3: Add the CHANGES.md entry**

At the top of `CHANGES.md`, under `# CHANGES`, add:

```markdown
## 2026-09-08 - SpellDmg/HealAmt master output scaling

Made SpellDmg and HealAmt the caster/healer output dials. Flipped five Spells
rules (`ItemExtraSpellAmtCalcAsPercent`, `FlatItemExtraSpellAmt`,
`IgnoreSpellDmgLvlRestriction`, `DOTsScaleWithSpellDmg`, `HOTsScaleWithHealAmt`)
so these stats apply as uncapped percent-of-base multipliers on spells, heals,
DoTs and HoTs. Extended `gen_loot_tier` in `tiered_loot_setup.sql` with a
`p_spellstat` param that ADDS flat SpellDmg/HealAmt to worn tier gear
(+5/+12/+20 Polished/Exalted/Ascended, mirrored to Ascended epics) — Classic base
items are ~0, so the pre-existing offense multiply was a no-op. Soloability is
tuned via `Character:ItemSpellDmgCap`/`ItemHealAmtCap` (250 = +250% at cap).
Rules + SQL only; no C++, no client change; NPCs and melee output untouched.
Gotcha: heroic INT/WIS can also feed these stats via `Heroic*Increase*Multiplier`
(0 today) — verify vs the cap before enabling. Reverse: rules → false, re-run the
generator with `p_spellstat` 0.
```

- [ ] **Step 4: Create the tracking issue**

```bash
gh issue create --repo frank-grimes-jr/nightcap --title "SpellDmg/HealAmt master output scaling" --body "Spec: docs/superpowers/specs/2026-09-08-spelldmg-healamt-scaling-design.md. Plan: docs/superpowers/plans/2026-09-08-spelldmg-healamt-scaling.md. Turn SpellDmg/HealAmt into percent-of-base output multipliers stamped on tier gear; cap-as-dial. Spells+heals only; melee out of scope."
```

Expected: prints the new issue URL. (If `gh` is unauthenticated, note the issue as a manual follow-up rather than blocking.)

- [ ] **Step 5: Commit**

```bash
git add docs/qa/2026-09-08-spelldmg-healamt-qa.md .claude/skills/eqemu/thj-blueprint.md CHANGES.md
git commit -m "docs: QA spike + tracking for SpellDmg/HealAmt scaling

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Promotion to `test`

After Task 3, merge `feature/spelldmg-healamt-scaling` → `dev` (already deployed + verified there). Promote `dev` → `test` with the QA spike above as the in-game QA instructions, and wait for user sign-off before `main`.
