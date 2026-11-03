# No NPC Death Touch — 2026-11-03

Owner request: remove Death Touch from every NPC.

## Change

- **Spell lists:** `remove.sql` deletes every `npc_spells_entries` row for Cazic Touch
  (982, 3087, 7477) and Touch of Vinitras (2859, which the server already treats as
  Death Touch), after copying them to `nightcap_death_touch_backup_20261103`.
  Local DB: 17 rows (982 ×15, 2859 ×2) across 17 lists used by 25 NPC types, e.g.
  Keeper of Souls, The Spiroc Lord, Overseer of Air, the Hand/Eye of Veeshan,
  Bazzt Zzzt, Sister of the Spire, a greater sphinx (Plane of Sky), Iron Mike,
  Master Yael, Jaled Dar's shade, Vyzh`dra, Shei Vinitras and the "Generic Death
  Touch" list. Production must be counted at apply time (it was not readable here).
- **Quest scripts** (`akk-stack/server/quests`, no spell-list involvement): removed the
  scripted casts in Anguish (AMV, OMM), Misty encounter, Prince Thirneg, Plane of
  Mischief `Life`, Rallos Zek out-of-arena check and both Uqua gas-chamber cheater
  traps. All are outside the Classic era.
- **Kept:** `tutorialb/kobold_siege_supplies.pl` casts Cazic Touch II on *itself* as
  the barrel explosion, then calls `Kill()`; it never targets players.
- Removed safeguards: Uqua's gas-chamber trap and Rallos Zek's out-of-arena DT were
  anti-skip/anti-pull mechanics. Players can now bypass them.

## Apply

1. Back up (`tools/backup-peq.ps1` locally; verified stopped backup on OVH).
2. `remove.sql` → expect `remaining = 0`. A second run fails on the existing backup table.
3. Restart **all** zones (`npc_spells` loads at zone boot). Deploy the quest files and
   `#reload quest`.

Rollback: `rollback.sql`, restart zones, revert the quest files.

## Evidence (local, 2026-11-03)

Manual backup `backups/peq_20261103_055440.sql.gz`; remove → `17 / 0`; rollback
restored 17; reapply `17 / 0`; double-run refused (ERROR 1050). The five sampled Plane
of Sky NPCs have 0 DT entries. All 8 zone processes restarted after the change.
Edited Perl passes `perl -c`; Lua edits only delete lines inside blocks.
Production: **not applied** (read access was blocked by auto mode).

## In-game QA

1. Plane of Sky: pull Keeper of Souls and The Spiroc Lord, and fight until each would
   normally cast it, for at least 3 minutes. Expected:
   no "Cazic Touch" cast message and no instant death. Their other spells still land.
2. `#npcstat`/`#showspells` on Keeper of Souls: no spell 982 in its list.
3. Any other Plane of Sky caster still casts its non-DT spells normally.

## Wiki impact

Player-facing: Death Touch is a major departure from Classic and belongs on the wiki
Features page and Recent changes once production is applied. Not published.
