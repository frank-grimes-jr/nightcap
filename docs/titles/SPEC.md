# Earned titles — November 12, 2026

Accepted intent: introduce earned cosmetic titles for slaying, dragons, expansion
completion, skill mastery and other meaningful accomplishments; publish a guide
with exact requirements. This implementation is a disabled candidate, not a live
release or a record of player acceptance.

## Contract

The reviewed catalog in `tools/earned_titles.py` generates 77 stable native title
definitions and `wiki/articles/titles.json`. IDs 1900000000–1900000999 are reserved
for this system. Any existing native title in that range suspends this system.
Never reuse an issued ID or silently change its requirement. Existing database
titles, title sets, AA titles and player choices are preserved.

Unlocks are per character and permanent. No stats, items, currency, faction,
experience or abilities are granted. Native Titles selection remains authorized
through `TitleManager::HasTitle`; knowing an ID is not sufficient. Titles support
prefix/suffix placement and can be changed or cleared. Awarding does not equip.

General kills: Hunter 100, Slayer 1,000, Vanquisher 10,000. Undead: 100/1,000/5,000;
giants: 100/1,000; dragons: 1/10/100. Native body types, not model/name guesses,
determine family. Named victories are exact zone/NPC pairs: Nagafen 32/32040,
Vox 73/73057, dracoliche 72/72090. Defeating both dragons earns Dragonslayer.

Only successfully finalized native deaths count. Ownership is captured before
charm fades. Exclude owned/charmed victims, merchants, chests, queued corpses,
non-spawn-point actors and Last Lantern/other transient campaign actors. Use
native normalized damage-credit owner and current native party. Each participant
must be an ordinary account (status 0, GM off), connected, loaded, alive, within
200 units in 3D in the same process/instance, and see the enemy as non-gray.
Pet/swarm kills follow existing native credit; final-blow ownership alone is not
required. An entity guard prevents repeated callbacks on the same NPC object.
Counters start on activation and saturate at 10,000. No historical totals are
invented. A failed/uncertain cosmetic write is logged and never replayed; it
cannot cancel an already committed death or alter loot/XP/respawn state.

Dungeon Delver requires one personal full Keeper clear in either mode. Dungeon
Conqueror requires full Raid clears in five distinct Keeper dungeons. Each of
the 21 Classic dungeons has its own full-Raid title. Conqueror of Classic requires
all 21 zones enumerated in `ClassicZones`; Chapterhouse and Ashen Compact cannot
substitute. Planar Conqueror requires full Raid clears in Fear, Hate and Sky.
`nightcap_dungeon_members.completed_at > 0`, joined to its actual run, authorizes
full clears. Normalize historical Hate76 to current186. Mere membership, global
objective rows, partial runs and another member's completion never count.
Existing personal boss ledger entries can recover named victories. They do not
add to general slayer totals. Future expansions need separate reviewed checklists;
this contract does not mean every original Classic quest or collection.

There are 34 individual skill titles. Be level50+ and reach the highest native
level50 cap among currently held classes. Use min(persisted raw, loaded raw);
cap0 never qualifies. Ignore equipment, spell and AA skill-cap bonuses. Existing
class/race acquisition, New Tanaan craft advancement and specialization policy
is unchanged. Master Artisan requires all seven general crafts simultaneously.
No specialization-school titles are issued. Saved awards survive class release.
Level50 earns Seasoned Adventurer; durable whole-task completion9515 earns suffix
“the Last Lantern”. Native task history remains the story authority.

Kills and successfully saved skill updates reconcile immediately. Opening the
native Titles list or `#titles [page]` reconciles other/current/historical goals
and displays six progress entries per page. Reconciliation is idempotent through
the `(character_id,title_id)` primary key. Counters use one atomic multi-row
upsert per participant. No destructive player/schema migration is included.

## Implementation plan and proof

1. Pure native policy/catalog with threshold, zero-cap, class/level, body-family,
   21-zone completeness and legacy-Hate controls.
2. Native title manager adapter, finalized death hook, saved skill hook and
   player command. Compile the actual changed translation units against retained
   November12 inputs; verify `titles.cpp` preimage SHA256
   `2f66a4b7b99247218423110d1259c08ea5a56c0b4e1f849fb9b72a67e3f76e5a`.
3. Three additive InnoDB tables, disabled control row, isolated MariaDB migration,
   idempotence, concurrency and persistence controls.
4. Generated wiki requirements, whole-site link/search checks and cross-guide
   impact review. Preserve Not released and historical refresh review gates.
5. Correctness, authorization/privacy and scope review; exact normal-player QA
   before promotion. No runtime/client/public-site deployment is authorized by
   this candidate implementation.

Using native Titles avoids a custom UI/client download. A quest-only grant was
rejected because it cannot reliably own finalized death ordering, native
multiclass caps or title-selection authorization. Expansion conquest uses the
existing full-clear ledger instead of a second parallel completion mask.
