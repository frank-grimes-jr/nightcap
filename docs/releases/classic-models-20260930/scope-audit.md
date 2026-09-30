# Classic model policy and coverage

The requested outcome is **old models by default wherever an old counterpart
exists**, with a manual INI opt-in for modern versions. On September 30 the owner
clarified: "Races without old models use existing." The candidate already follows
this rule. Structural/startup checks pass; rendered acceptance remains open.

## What the audit found

The pinned executable's observed constructor registry contains 731 race IDs.
The candidate addresses 13 original player races, 130 race IDs through pinned
classic registrations, and 97 observed race IDs through remake mappings. There
are 98 configured remakes: race 646 is also handled although it was absent from
the observed native constructor inventory.

The remaining 491 observed IDs follow the native lookup. This includes old
models, later creatures, props and invisible helpers; **491 does not mean 491
modern creatures**. These counts alone do not prove that every available old
counterpart is selected correctly in game.
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

## Accepted fallback

Creatures and playable races without old counterparts keep their existing models
in both default and opt-in modes. This includes the later-only examples above.
The owner's clarification resolves the earlier replacement-choice question;
no substitute table or changes to the current binary/assets are required.

## Remaining acceptance

- Manual INI opt-in, classic counterparts, signed delivery into an isolated copy,
  required-asset repair and startup have objective evidence.
- The fallback policy is resolved and already implemented. In-game QA includes
  examples without old counterparts to confirm they retain their existing models.
- Model appearance, equipment, animations and zoning still need owner in-game
  acceptance under AGENTS.md. Startup health is not rendered acceptance.
- The owner subsequently authorized main/server publication. Signed production
  release 2026093004 is live; see [activation evidence](PRODUCTION.md). Deployment
  approval does not establish rendered acceptance.
