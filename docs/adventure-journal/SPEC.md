# Adventure Journal and archetype Epic 0.5

Historical eight-task foundation. The current level20–50 implementation and
one-shot release package are in [release-20261107/README.md](release-20261107/README.md);
use [CAMPAIGN-QA.md](release-20261107/CAMPAIGN-QA.md) for current player testing.
Do not install this older prototype migration independently.


November 6: the owner requests a continuing story through Classic endgame and
useful armor with a coordinated appearance. [The Last Lantern](CAMPAIGN.md)
specifies the proposed expansion for review. It adds eight later shared chapters
and progressive armor; the implementation described here and in catalog.json
still has only the original eight quests. Expansion implementation, installation
and gameplay acceptance are not claimed.

Accepted intent: October 1, 2026. The owner approved an in-game adventure journal
whose first campaign earns an archetype Epic 0.5. This is a candidate, not a live
deployment or a record of manual acceptance.

## Player experience

The Ancient Chronicler in the East Commonlands tunnel offers **journal**. The
existing RoF2 Tasks window holds objectives, progress, preparation notes and
rewards. Three shared expeditions lead to five independently earnable paths:
Guardian, Striker, Arcanist, Warden and Binder. Starting class never determines
eligibility. Shared chapters start at levels 20, 25 and 30; paths start at 35.
The intended first completion is level 35–40, subject to measured balance QA.

The first campaign uses existing Classic dungeon encounters. Path objectives
progress through two field tests and a final named encounter. These are open-world
trials with native individual task credit (including normal group/pet credit),
not new instanced wave encounters. Hints emphasize different roles without
requiring a specific class, spell, damage source or optimized combination.
Named spawn waits remain possible; no random quest-proof drop is required.
Future bespoke wave trials are an extension, not represented as implemented here.

The reward is **Wayfarer's Oath [Epic 0.5]**, one no-trade, lore, all-class charm.
It has a modest common stat budget and five earned attunements. Finishing another
path unlocks a choice, not another simultaneously usable relic. The Chronicler
forges/replaces the charm and changes its attunement only in the public EC hub,
out of combat and with the shared cooldown ready. There is no item destruction
or exchange during attunement. A missing charm can be recovered from earned task
completion. Native lore checks protect recovery when it is banked or on a cursor.

## Candidate power budget

The charm grants 5 AC, 35 HP, 35 mana and 3 to the five classic resists, with no
heroics, regeneration, augment slots or random item-tier variants. It requires
level 35. Its equipped click invokes the active path on a shared 600-second
character cooldown, committed to the database before any effect. Relogging,
death, deleting/recovering the charm and changing classes cannot reset that clock.

- Guardian: 15% melee absorption, at most 200 damage, at most three server ticks.
- Striker: 6% melee damage modifier for at most three ticks.
- Arcanist: 5% spell damage focus, including direct damage and DoTs, at most three ticks.
- Warden: instant recovery; numerical effect is specified in the canonical catalog.
- Binder: empower one targeted owned pet, sharing the entire cooldown budget;
  there is no multiplication by pet count.

These are starting candidates, not claims of balanced live performance. Test
leveling, fresh 50 and developed 50 builds with the legal AA pool, equipment,
buffs and pets recorded. Compare with and without the relic. Preserve class
epics and encounter rewards. The global `era.json` policy remains authoritative.

## Persistence and failure behavior

Native task state owns objectives and completion; do not maintain parallel kill
flags. A small character table owns only active attunement and next-use time.
Parameterized conditional writes serialize activation and switching. Database
errors, absent native compatibility, missing content and disabled release gates
refuse abilities and new journal actions. Never retry an uncertain activation:
it can consume a cooldown without an effect, but cannot grant a free effect.

The release begins disabled. Paired content, quests, native duration exception
and staged client spells must pass verification before enablement. Existing
beneficial buffs remain permanent; only the reserved Epic 0.5 effects retain
bounded durations. Item clicks always intercept the harmless invocation spell.

Rollback disables offers and abilities and preserves all earned progress, owned
items and spell definitions. It must not delete a player's task history or leave
owned item references dangling. Original client files stay read-only.

## Build order and proof

1. Canonical campaign catalog, guarded additive SQL, retained-data rollback;
   validate live-read NPC identities, occupied IDs, schema and exact generated data.
2. Native task menus, earned-path checks, recovery, attunement and durable click;
   Perl behavior tests cover bypasses, pet ownership, cooldowns and failures.
3. Narrow native duration/compatibility contract and staged client spell export;
   compile the real policy and preserve unrelated spells byte-for-byte.
4. MariaDB rehearsal against copied content schemas and failure controls;
   independent code review, release guide, balance matrix and exact in-game QA.

Likely files: `docs/adventure-journal/`, `tools/epic05*.py`,
`tools/tests/*epic05*`, `server-mods/plugins/epic05*.pl`, the EC Chronicler,
one item quest, native `spells.cpp`/`perl_client.cpp` and a small shared header.
The riskiest boundary is durable cooldown versus transient spell application.
Five separate swappable rewards were rejected because they complicate recovery
and permit stacking; a new client journal window was rejected because native
tasks already provide persistent objectives.

## Acceptance

All eight journal adventures appear correctly in native RoF2. All five paths
can be earned by characters of any primary class. No unearned path activates;
only an equipped earned relic works. Switching and recovery cannot bypass the
shared cooldown. Foreign pets cannot be empowered. All timed effects expire.
Full inventories and database errors do not erase earned eligibility. Release
and rollback preserve unrelated game data. Native gameplay and balance QA precede
main promotion under the normal branch policy.
