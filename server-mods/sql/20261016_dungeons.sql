-- Additive candidate schema. Run once; refuse existing/unknown tables.
-- Activation is a separate guarded operation after catalogs and binaries match.
CREATE TABLE nightcap_dungeon_state (
 id TINYINT UNSIGNED PRIMARY KEY,
 revision BIGINT UNSIGNED NOT NULL,
 enabled TINYINT UNSIGNED NOT NULL DEFAULT 0,
 CHECK (id=1 AND enabled IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
INSERT INTO nightcap_dungeon_state VALUES (1,2026101601,0);

CREATE TABLE nightcap_dungeon_runs (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 instance_id SMALLINT UNSIGNED NOT NULL,
 instance_start BIGINT UNSIGNED NOT NULL,
 zone_id INT UNSIGNED NOT NULL,
 owner_id INT UNSIGNED NOT NULL,
 mode TINYINT UNSIGNED NOT NULL,
 seed BIGINT UNSIGNED NOT NULL,
 revision BIGINT UNSIGNED NOT NULL,
 expires_at BIGINT UNSIGNED NOT NULL,
 retired TINYINT UNSIGNED NOT NULL DEFAULT 0,
 final_killed_at BIGINT UNSIGNED NOT NULL DEFAULT 0,
 final_x FLOAT NOT NULL DEFAULT 0,
 final_y FLOAT NOT NULL DEFAULT 0,
 final_z FLOAT NOT NULL DEFAULT 0,
 loot_rights VARCHAR(100) NOT NULL DEFAULT '',
 UNIQUE KEY instance_generation(instance_id,instance_start),
 KEY owner_runs(owner_id,zone_id,expires_at),
 CHECK (mode IN (0,1) AND retired IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE nightcap_dungeon_members (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 character_id INT UNSIGNED NOT NULL,
 reward_item INT UNSIGNED NOT NULL,
 reward_drop_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 completed_at BIGINT UNSIGNED NOT NULL DEFAULT 0,
 inside_instance TINYINT UNSIGNED NOT NULL DEFAULT 0,
 PRIMARY KEY(run_id,character_id),
 UNIQUE KEY reward_receipt(reward_drop_id),
 KEY character_runs(character_id,completed_at),
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE nightcap_dungeon_kills (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 character_id INT UNSIGNED NOT NULL,
 boss_id INT UNSIGNED NOT NULL,
 PRIMARY KEY(run_id,character_id,boss_id),
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
-- character_id=0 records the shared objective; real IDs are personal credit.
CREATE TABLE nightcap_dungeon_deaths (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 spawn_id INT UNSIGNED NOT NULL,
 PRIMARY KEY(run_id,spawn_id),
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE nightcap_dungeon_loot (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 ordinal TINYINT UNSIGNED NOT NULL,
 item_id INT UNSIGNED NOT NULL,
 drop_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 PRIMARY KEY(run_id,ordinal),
 UNIQUE KEY physical_drop(drop_id),
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Grind timers belong to a run generation too. Millisecond wall-clock deadlines
-- are committed before publishing the death, alongside encounter credit.
CREATE TABLE nightcap_dungeon_respawns (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 spawn_id INT UNSIGNED NOT NULL,
 respawn_at BIGINT UNSIGNED NOT NULL,
 died_at BIGINT UNSIGNED NOT NULL,
 PRIMARY KEY(run_id,spawn_id),
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Copies of native spawn rows live here, never in public spawn2. CT uses only
-- these private rows. Other dungeons use them for objective selection overrides.
CREATE TABLE nightcap_dungeon_spawns (
 zone_id INT UNSIGNED NOT NULL,
 spawn_id INT UNSIGNED NOT NULL,
 npc_id INT UNSIGNED NOT NULL,
 group_id INT UNSIGNED NOT NULL,
 boss_id INT UNSIGNED NOT NULL DEFAULT 0,
 is_final TINYINT UNSIGNED NOT NULL DEFAULT 0,
 x FLOAT NOT NULL, y FLOAT NOT NULL, z FLOAT NOT NULL, heading FLOAT NOT NULL,
 respawn INT UNSIGNED NOT NULL,
 grid_id INT UNSIGNED NOT NULL DEFAULT 0,
 PRIMARY KEY(zone_id,spawn_id),
 CHECK(is_final IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Managed checkpoints are keyed by the permanent run UUID, never the recyclable
-- native instance number. Old zone processes can only update their own run.
CREATE TABLE nightcap_dungeon_checkpoints (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 payload LONGTEXT NOT NULL,
 saved_at BIGINT UNSIGNED NOT NULL,
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Written in the same transaction as every death. Stable physical IDs cover
-- every native and bonus item, plus currency. Wall-clock decay is irreversible.
CREATE TABLE nightcap_dungeon_corpses (
 run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 spawn_id INT UNSIGNED NOT NULL,
 corpse_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 payload LONGTEXT NOT NULL,
 expires_at BIGINT UNSIGNED NOT NULL,
 PRIMARY KEY(run_id,corpse_id),
 FOREIGN KEY(run_id) REFERENCES nightcap_dungeon_runs(run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Disable acquisition to roll back behavior. Preserve catalogs, definitions,
-- ledger and character_advloot_claims after any player access.
