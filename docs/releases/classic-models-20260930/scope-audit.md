# Old-model objective: remaining coverage

The requested outcome is **OLD MODELS ONLY by default**, with modern visuals
requiring a manual INI edit. The current counterpart mapping is an interim
candidate. Its green structural/startup checks do not prove that full outcome.

## What the audit found

The pinned executable's observed constructor registry contains 731 race IDs.
The candidate addresses 13 original player races, 130 race IDs through pinned
classic registrations, and 97 observed race IDs through remake mappings. There
are 98 configured remakes: race 646 is also handled although it was absent from
the observed native constructor inventory.

The remaining 491 observed IDs follow the native lookup. This includes old
models, later creatures, props and invisible helpers; **491 does not mean 491
modern creatures**. Native passthrough cannot establish old-only appearance.
The captured inventory and full categorized results are retained under
`E:/EQ_Local_Dev/artifacts/classic-models-20260930/coverage-audit.json`.

Concrete later-only examples include Vah Shir (130), playable Froglok (330),
Drakkin (522), and the compact-hub model set (407, 411, 417, 419, 495). Availability
in this client is distinct from the server's legal race/era pool. No live-server
spawn or character inventory is claimed by this audit.

The audit also found four clear original counterparts that had been missed.
They are corrected in QA release 2026093003: Human2 → Human, Ogre2 → Ogre,
Erudite2 → Erudite, and scaled wolf → original WOF (race 42/gender 1). Humanoid
NPCs keep the original player actor names to preserve armor handling.

## Replacement decision

Later-only player races have no original player mesh. Two old-only approaches
are possible; neither should silently be presented as the original race model:

| Priority | Examples to review | Tradeoff |
|---|---|---|
| Closest creature appearance | Vah Shir → original Kerran; Froglok → original Froglok; Drakkin → original Iksar | NPC meshes can lose wearable armor presentation or expected player animations. |
| Classic playable meshes | Vah Shir → Human; Froglok → Gnome; Drakkin → Iksar | Preserves the classic player equipment system but changes racial appearance more substantially. |

Later-only NPCs need a curated classic substitute table too. Representative
proposals for the hub are Lightning Warrior → Giant, Pyrilen → fire elemental,
Gelidran → water elemental, Girplan → Gargoyle, and Scrykin → Gnome. These are
proposals, not active mappings or verified rendered results. Props, invisible
helpers and mounts need separate review so substitutions do not expose hidden
helpers or break interaction/animation.

## Completion remains unproven

- Manual INI opt-in, classic counterparts, signed delivery into an isolated copy,
  required-asset repair and startup have objective evidence.
- Full old-only coverage remains incomplete until the later-only replacement
  policy is implemented and checked against the relevant runtime models.
- Model appearance, equipment, animations and zoning still need owner in-game
  acceptance under AGENTS.md. Startup health is not rendered acceptance.
- Nothing in this candidate has been published to production. Do not promote it
  as completion of the full goal on the strength of the current checks.
