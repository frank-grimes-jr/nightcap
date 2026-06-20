# Nightcap — Custom EverQuest Private Server

A heavily customized [EQEmu](https://www.eqemulator.org/) server built for small-group and solo play with friends. All content runs inside Docker via [akk-stack](https://github.com/akkadius/akk-stack). Includes a custom GM web tool (`eq-solo-gm`) for server management without requiring in-game GM commands.

---

## Major Deviations from Vanilla EverQuest

These are the intentional rule changes that differentiate Nightcap from a stock PEQ server.

---

### 1. Multiclass System

**The single largest departure from vanilla EQ.** Characters can adopt up to two additional class disciplines beyond their original class, turning every character into a 2- or 3-class hybrid.

#### How it works

Speak to **The Ancient Chronicler** in Plane of Knowledge. This NPC acts as the multiclass hub.

- **2nd Discipline** — Available at level 20. Choose any of the 16 EQ classes.
- **3rd Discipline** — Available at level 50. Choose a second additional class.

#### What applying a discipline does

When you adopt a new discipline:

1. **Spells** — All spells from the secondary class that are available in the current expansion are scribed to your spellbook. The class restriction in the spell table is patched so your base class can memorize them.
2. **Skills** — Your skill caps are expanded to include all skills from the adopted class, trained to maximum for your level.
3. **AAs** — The alternate advancement abilities for the adopted class become visible in your AA window and are purchasable immediately.

#### Releasing a discipline

You can revoke a secondary or tertiary discipline at any time through the same Chronicler NPC. Revocation removes exclusive spells from that class (spells not already available to your base class), resets the associated AA visibility, and clears the discipline from your character record.

#### Lore framing

> *"Long have the ancient paths of Norrath been sealed — the rigid walls between fighting forms and mystic arts. The Ancient Chronicler walks the forgotten roads between these disciplines. In exchange for dedication and mastery, he can teach a warrior the prayers of a cleric, or show a rogue the blade dances of a monk."*

---

### 2. Plane of Knowledge as Universal Starting Hub

**All new characters start in Plane of Knowledge**, regardless of race, class, or deity. In vanilla EQ, each race has a dedicated starting city. Here, PoK is the central hub for everything.

- Starting coordinates are set to PoK's safe zone point.
- Death-bind point for new characters is also set to PoK.
- The PoK expansion check is bypassed so the zone is always accessible even when the server is locked to Classic or Kunark content.

---

### 3. Ancient Attunement — Universal PoK Recall AA

Every character receives a free **Ancient Attunement** AA on login, regardless of level, class, or expansion.

- Teleports the character to Plane of Knowledge.
- Available from **level 1**.
- 10-minute recast timer.
- No AA points required to acquire or use.
- Granted automatically via `global_player.lua` on every connect.

This replaces the need for GM commands to return to the hub. Friends playing on the server can recall to PoK at any time.

---

### 4. Expansion-Gated PoK Portals

The portal doors inside Plane of Knowledge are locked to their appropriate expansion era. A character attempting to zone through a portal to Kunark content while the server is running Classic will receive a message and be returned to PoK.

- GMs bypass this check entirely.
- Portal locking is enforced via `player.pl` in the PoK quest script directory.
- The current expansion is read from the `Expansion:CurrentExpansion` server rule, which the GM tool manages.

---

### 5. AA Progression from Level 1

In vanilla EQ, Alternate Advancement abilities are locked behind level 51 (Shadows of Luclin release). On Nightcap:

- **All AA rank level requirements are set to 1** — any AA can be purchased as soon as you have the points.
- **`AA:ExpPerPoint` is tuned to 50,000** (vs. live EQ's ~24,000,000). This makes AAs accessible during normal leveling.
- XP rate is intentionally minimal at level 1 but scales with level. **Level 30 in Lower Guk is the designed sweet spot** — the combination of red-con mobs (XP bonus) and 3-class combat power makes it an efficient AA grind zone.
- AA visibility is still class-gated — only AAs for your active disciplines appear in the window.

---

### 6. Expansion Management System

The server can be locked to any EverQuest content era. Switching expansion changes:

- Maximum character level cap
- Which zones are accessible through PoK portals
- Which spells appear on the in-PoK spell vendors
- Which AAs are visible in the AA window (`Expansion:UseCurrentExpansionAAOnly = true`)

Expansion switching is handled through the **GM web tool** (see below). A single button press updates all relevant server rules and triggers a spell vendor refresh.

**Supported eras:**
| # | Expansion |
|---|-----------|
| 0 | Classic |
| 1 | Ruins of Kunark |
| 2 | Scars of Velious |
| 3 | Shadows of Luclin |
| 4 | Planes of Power |
| 5 | Lost Dungeons of Norrath |
| 6 | Gates of Discord |

---

### 7. Expansion-Filtered Spell Vendors

Three spell vendors are stationed in Plane of Knowledge, each serving a different class archetype. Spell inventory is automatically refreshed to only show spells from the current expansion when you change eras via the GM tool.

| Vendor | Classes |
|--------|---------|
| Arcane Tomes | Necromancer, Wizard, Magician, Enchanter |
| Sacred Rites | Cleric, Druid, Shaman |
| Martial Disciplines | Paladin, Ranger, Shadow Knight, Bard, Beastlord |

Spells sold as books require the appropriate class (or multiclass discipline) to use. Vendors are populated via the `POST /api/vendors/refresh` endpoint in the GM tool.

---

### 8. XP and Progression Tuning

| Setting | Value | Vanilla |
|---------|-------|---------|
| `Character:ExpMultiplier` | 0.65 | 1.0 |
| `Character:AAExpMultiplier` | 0.65 | 1.0 |
| `AA:ExpPerPoint` | 50,000 | ~24,000,000 |

The XP multiplier is slightly below live EQ rate, making leveling take a bit longer. AA experience is tuned to be nearly inaccessible at level 1 (intentional) and quite productive at level 30+ when grinding red-con mobs.

---

### 9. GM Web Tool (`eq-solo-gm`)

A custom web interface for server administration. Runs locally on **port 5173** (frontend) and **port 3001** (API).

**Features:**
- **Character Management** — Boost any character's level, grant AA points, set skills to max, add platinum/currency.
- **Expansion Control** — Switch the server's content era with one click. Automatically updates level cap, portal locks, and spell vendor inventory.
- **Server Rules** — Live-edit tracked server rules: XP multiplier, AA cost, loot rates, death penalty, etc.
- **Teleport** — Move any character to any zone.
- **Vendor Refresh** — Rebuild spell vendor inventories for the current expansion.

> **Note:** Database credentials in `api/server.cjs` are hardcoded to the default EQEmu values (`eqemu`/`eqemu` on `localhost:3307`). Change these if your setup differs.

---

## Repository Structure

`akk-stack` (the base Docker server) is a separate upstream project and is not included here. Install it first, then copy the files from this repo into place.

```
nightcap/
├── server/
│   └── quests/                 Custom and modified quest scripts
│       ├── global/
│       │   ├── global_player.lua   Ancient Attunement AA grant on login
│       │   └── global_player.pl    Perl fallback
│       └── poknowledge/
│           ├── The_Ancient_Chronicler.pl   Multiclass hub NPC
│           └── player.pl                   PoK portal expansion lock
├── eq-solo-gm/                 GM web tool (Vue3 + Express)
│   ├── api/
│   │   └── server.cjs          Express API server
│   ├── src/                    Vue3 frontend components
│   └── scripts/                SQL setup scripts
│       ├── multiclass_setup.sql        DB schema + NPC spawns for multiclass
│       ├── pok_attunement_setup.sql    Ancient Attunement spell + AA
│       ├── pok_start_zone.sql          Set PoK as universal start zone
│       └── aa_progression_setup.sql    AA level/XP tuning
└── README.md
```

---

## Setup

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Node.js 18+ (for the GM tool)
- A copy of the EverQuest Rain of Fear 2 client

### 1. Install and start akk-stack

```bash
git clone https://github.com/akkadius/akk-stack.git
cd akk-stack
make install     # first time only — downloads and configures everything
make up          # start all containers
```

### 2. Copy the custom quest scripts

From the nightcap repo root:

```bash
cp -r server/quests/global/* akk-stack/server/quests/global/
cp -r server/quests/poknowledge/* akk-stack/server/quests/poknowledge/
```

### 3. Run the custom SQL scripts

```bash
cd akk-stack
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < ../eq-solo-gm/scripts/multiclass_setup.sql
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < ../eq-solo-gm/scripts/pok_attunement_setup.sql
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < ../eq-solo-gm/scripts/pok_start_zone.sql
docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < ../eq-solo-gm/scripts/aa_progression_setup.sql
```

### 3. Start the GM tool

```bash
cd eq-solo-gm
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### 4. Reload the server

After running the SQL scripts, apply changes in-game:

```
#reloadworld
```

---

## After First Login

When you first log in with a new character:

1. You will spawn in **Plane of Knowledge**.
2. Open your **AA window** — the *Ancient Attunement* ability is already granted and ready.
3. Visit **The Ancient Chronicler** (somewhere in PoK — coordinates are placeholders until placed in-game) to select your character's disciplines.
4. Use `/loc` in-game to find good NPC placement spots, then update `spawn2` coordinates in the DB.

---

## NPC Placement (Required After Install)

The Chronicler and vendor NPCs use placeholder coordinates. After running `multiclass_setup.sql`:

1. Stand at your desired location in PoK.
2. Note the `/loc` output.
3. Run:
   ```sql
   UPDATE spawn2 SET x = ?, y = ?, z = ?
   WHERE spawngroupID IN (999220, 999221, 999222, 999223, 999224);
   ```
4. In-game: `#repop`

---

## Acknowledgements

- [EQEmulator](https://www.eqemulator.org/) — the open-source EverQuest server emulator
- [akk-stack](https://github.com/akkadius/akk-stack) — the Docker setup this server is built on
- [Project EQ](https://www.projecteq.net/) — quest scripts and database content
