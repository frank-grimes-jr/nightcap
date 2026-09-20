---
name: eqemu
description: Use when working on EverQuest emulator server internals — zone/world C++, Perl/Lua quest scripts, PEQ database tables (items, spells_new, aa_ability, loot, npc_types), shared memory, "change not showing in game" problems, RoF2 client limits — or when designing/prioritizing Nightcap features against The Heroes' Journey (THJ) target spec.
---

# EQEmu / Nightcap Server Knowledge

## Overview

EQEmu is the open-source C++ EverQuest server emulator (MariaDB, PEQ schema). This repo runs it in Docker via akk-stack with the **RoF2 client**. This server ("Nightcap") is a solo/small-group server replicating **The Heroes' Journey (THJ)** — the target spec and gap roadmap live in [thj-blueprint.md](thj-blueprint.md).

Source of truth: C++ in `akk-stack/code/`, live quest scripts in `akk-stack/server/quests/` (git-mirrored to `server-mods/`), DB `peq` on host port **3307**. Operating the stack (containers, logs, rebuilds) is covered by the `run-akk-stack` skill.

## Process model

- Binaries: `world` (login/character select, zone orchestration), `zone` (one process per running zone), `ucs` (chat), `queryserv` (logging), `loginserver`, `shared_memory` (cache builder), `eqlaunch` (zone spawner).
- **Dynamic-pool zones run as bare `bin/zone` with no zone name in the command line.** Find which process serves a zone via its log filename: `logs/zone/<zone>_..._<PID>.log` — never `pgrep -f "zone <name>"`.
- A process runs whatever binary existed when it started. **After `make zone`, kill every `bin/zone` process** (eqlaunch respawns them). Verify: every process start time must be newer than the binary mtime. Partial kills = "intermittent" bugs that depend on which zone you're standing in.

## "Why isn't my change showing in game?"

| You changed | Cached in | To apply |
|---|---|---|
| `items`, `spells_new`, factions, loot tables, `skill_caps`, base data | shared memory files | run `./bin/shared_memory`, then restart zones. `#hotfix` works for edits to existing rows; **new rows need the full regen + restart** |
| `npc_types`, `merchantlist` | zone process at boot | zone **restart** — `#repop` is NOT enough |
| Perl/Lua quest scripts | zone process | `#reload quest` (or zone restart) |
| `aa_ability` / `aa_ranks` | zone process at boot | restart zones (loads per-zone from DB; no shared-mem regen needed) |
| `rule_values` | world/zone | `#reload rules` |
| `spawn2`, doors, ground spawns | zone | `#repop` (NEW spawn2 rows too) |
| Era / `Expansion:CurrentExpansion` | every zone process at boot | edit `era.json`, run `tools/apply-era.ps1` (kills all zones) — never set by hand |
| Instance content (script changed version/zone) | instance's own zone process, lives until idle-timeout | kill that specific process (PID in its log filename) — `#repop` won't |
| RoF2 client item stat display | client-side cache | player must camp/zone after inspecting an item |

## RoF2 client hard limits (server-side workarounds required)

- **Item ID cap for links: 1,048,575** (`0xFFFFF`). Links encode the id as `%05X & 0x000FFFFF` (`common/say_link.cpp`); higher ids wrap and link to the *wrong item*. Inventory/summon accept 32-bit ids — links are the binding constraint. Keep all custom item ids under the cap.
- **Spell access is per character in signed client/server release 2026092005**: guarded client hooks cover merchant masks, spell levels and the earlier scribe item gate. Both sides use `common/spell_class_catalog.h` from the pinned original spell file and current held classes. Never globally widen `spells_new.classes1–16`; `sync-spell-access.ps1` is retired. Deploy the matching client and server; unknown custom learnable spells require an explicit catalog entry. See `docs/releases/production-bugfixes-20260920.md`.
- **AA names are cached at zone boot** — per-player dynamic AA renaming is impossible without `#reload aa`; bake labels statically instead.
- **No per-item name color field**; rarity/quality must be shown via name text tags.
- Luclin-model races render invisible when players run classic models (race 86 sphinx is invisible; race 21 Xorbb works everywhere).
- An NPC is only shoppable if `npc_types.class = 41` (Merchant); `merchant_id` alone just links inventory.
- **Client "crash" zoning in?** Check `Client_RoF2_Dev\everquest_rof2\Logs\dbg.txt` FIRST — `Unable to find specified world file <zone>.s3d` means the client is missing that zone's geometry (this RoF2 package lost several classic `.s3d`/`_obj.s3d` files). Server-side the only symptom is `kicked, reason [Dropped by world CLE subsystem]` ~40s after connect with the zone process alive.
- **NPC shows as human?** The client needs the exact **race+gender+texture(+helmtexture) combo** loaded in that zone (zone `_chr.txt` + GlobalLoad.txt archives) — race alone proves nothing (race 330 = playable Froglok has NO gender-2 model → human fallback). Only safe method: copy the full appearance tuple from a native NPC of that zone (`spawn2`→`npc_types`); only size is free. QA-proven in PoK 2026-07-14.
- **Client confirmation prompts are client-side settings, not server behavior**: "Loot All" confirm = `eqclient.ini LootAllConfirm`; per-item NO TRADE loot confirm = `/lootnodrop never` (per-character). A "Lost D3D device" line in `Logs/dbg.txt` followed by endless `CBufferSet::AllocateVertices() failed` = black world with working UI, follows the client process across zones/relogs of other characters — restart eqgame.exe, prefer windowed/borderless.
- **Base class is the client's UI chassis**: WAR/MNK/ROG/BER get no spellbook/gems (can never memorize, whatever the server scribes); pure casters get no combat-abilities window. No server-side override — THJ solves it with client patches. Multiclass design must respect the base-class chassis.

## Key tables and traps

- **`aa_ability.id` ≠ `first_rank_id`.** Players' purchased AAs (`character_alternate_abilities`) reference rank ids via `first_rank_id`. Never join or sanity-check assuming they match.
- `spells_new.classesN` = min level for class N; `255` = unusable by that class.
- `character_multiclass` (custom Nightcap table) is the **authoritative** multiclass record. qglobals (`mc_class2/3`) are NOT reliably populated on NPCs — read the table, don't trust `%qglobals`.
- `items` has 285 columns — clone rows via `CREATE TEMPORARY TABLE ... SELECT`, never enumerate columns.
- `global_loot` injects drops server-wide by level/filter (used for ~1% Essence of the Legend on 55+).
- Multiclass AA access is granted **only** by the per-character mask (`m_multiclass_mask`, loaded in the ZoneEntry handler *before* `LoadAlternateAdvancement` — load order matters). Never OR class bits into `aa_ability.classes`; that mutation is global, irreversible cruft.

## Perl quest API (this build)

`$DB` is **not** injected and there is **no** `$db->do()` or `fetchrow_hashref()`. The exposed class is `Database`:

```perl
my $db  = Database->new();
my $sth = $db->prepare("SELECT class2, class3 FROM character_multiclass WHERE character_id = ?");
return unless $sth;                 # prepare returns undef on failure
$sth->execute($char_id);
my $row = $sth->fetch_hashref();    # fetch_hashref, NOT fetchrow_hashref
```

Methods: `prepare`, `execute(@params)`, `fetch`/`fetch_array`, `fetch_arrayref`, `fetch_hashref`, `num_rows`, `insert_id`, `rows_affected`. Writes also go through prepare+execute. Bindings: `akk-stack/code/zone/perl_database.cpp`.

**Method names come from the Perl bindings, NOT the C++ classes.** `$client->GetCharacterID()` dies (`Can't locate object method`); the binding is `CharacterID()`. Before calling any object method in a quest script, verify it: `grep '"MethodName"' akk-stack/code/zone/perl_*.cpp`. Note `Group::GetMember(i)` returns a `Client*` in Perl.

**Instances:** create with **version 0** — spawn2/doors rows are version 0, and a non-zero instance version loads NO content (empty zone, no doors). `quest::CreateInstance(zone, 0, seconds)`.

Lua runs alongside Perl (`global_player.lua` handles login grants via `event_connect`).

## Community / product context

- **PEQ** is the canonical content database (quests/spawns tracking live EQ eras). Expansion numbering: 0 Classic, 1 Kunark, 2 Velious, 3 Luclin, 4 PoP…
- Notable custom servers: Project 1999 (classic purist), Project Quarm (classic+, solo-self-found), EZ Server (custom progression), **THJ** (multiclass solo/duo — our target; see [thj-blueprint.md](thj-blueprint.md)).
- THJ's official wiki (`wiki.heroesjourneyemu.com`) and GitHub org block scraping/are private — the blueprint file is the durable local record; verify against the wiki manually in a browser when in doubt.

## Common mistakes

| Mistake | Reality |
|---|---|
| `#repop` after editing `npc_types`/merchants | Cached at zone boot — restart the zone |
| Testing after rebuild without killing all zones | Stale binaries serve old code per-zone |
| Item ids offset by +1,000,000 (THJ-style) | Breaks RoF2 links — stay under 1,048,575 |
| `$DB->prepare` / `fetchrow_hashref` in Perl | No `$DB`, no `fetchrow_*` — `Database->new()` + `fetch_hashref` |
| Reading `%qglobals` on an NPC for character state | Unreliable — read the authoritative table |
| Mutating `aa_ability.classes` per-player | Global + irreversible; use the multiclass mask |
| C++ method names in Perl (`GetCharacterID`) | Use binding names (`CharacterID`) — grep `perl_*.cpp` |
| Creating instances with version 1+ | Empty shell — version 0 inherits base-zone spawns/doors |
| Assuming a committed SQL script ran on the live DB | Verify rows exist; and prove ID ranges free in EVERY table before insert (plain INSERT, never `INSERT IGNORE`/`ON DUPLICATE` in setup scripts) |
| Setting era rules by hand | `era.json` + `tools/apply-era.ps1` is the source of truth (drift-checked nightly) |

CHANGES.md at repo root is the chronological audit trail behind all of the above; check its recent entries before touching multiclass, loot tiers, or AA code.
