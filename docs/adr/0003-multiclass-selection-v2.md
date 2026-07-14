# ADR 0003: Multiclass selection v2 — plugin core, thin NPC UI, PoK Athenaeum

Date: 2026-07-14
Status: Accepted

## Context

The AA rework (see CHANGES.md 2026-07-13) made AA inheritance purely data-driven off `character_multiclass`; the Chronicler script is now just one possible front-end plus three side effects (spells_new patch, skill_caps expansion/training, guards) buried in NPC dialog code. The say-code UX (`say 200+class_id`) is hostile, previews don't exist, and the NPC models silently fell back to human (their model archives aren't in the RoF2 client's GlobalLoad.txt and PoK has no local copies). User requirement: PoK remains the hub; otherwise redesign freely, enhance the experience.

## Decision

1. **Core/UI split.** All multiclass mutations move to `quests/plugins/multiclass.pl` (`plugin::mc_get_classes / mc_preview / mc_apply_class / mc_revoke_slot`). NPC scripts become thin dialog layers; any future front-end (login flow, other NPCs, commands) calls the same plugin. qglobals (`mc_class2/3`) are dropped entirely — `character_multiclass` is the only state.
2. **UX: browse → preview → popup confirm.** Hail lists the 16 classes as saylinks grouped by archetype row (Tank/Healer/Melee/Caster). Clicking a class shows a *preview* (live DB counts: spells, skills, class AA lines it would grant) with flavor text. An explicit "embrace" saylink raises a confirmation popup; only the popup's Yes commits. Revoke keeps its confirm popups.
3. **Models from the proven-renders-in-PoK palette** (races already spawning in poknowledge, verified in DB — GlobalLoad.txt can't load classic archives like the evil eye): Chronicler = library guardian construct (330, the iconic PoK library golems), Arcane = clockwork (457), Divine = Herald of Druzzil Ro (495), Martial = werewolf (14), Stalwart = Drakkin (522), Packwell = Gigglegibber goblin (433), Forgemaster = fire elemental (75).

## Consequences

- Selection engagement is now swappable without touching game mechanics; the Chronicler is presentation only.
- Model races outside GlobalLoad.txt will *always* human-fallback in PoK — future NPC work must pick from races that render there (check `spawn2` joins or globalload).
- Preview counts are live queries per click — negligible at this scale (solo server).
- npc_types appearance changes need a PoK zone restart (cached at boot), not #repop.
