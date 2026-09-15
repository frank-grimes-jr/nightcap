-- One-time 2026-09-15 deployment repair, while PoK is offline.
-- Exact 17 non-corpse hub preimages are retained in the local deployment backup.
-- Preserve all other PoK state and all other instances. Do not run with --force.
-- Replace final COMMIT with ROLLBACK for the required rehearsal.
CREATE TEMPORARY TABLE hub_state_guard (
    ready TINYINT NOT NULL CHECK (ready = 1)
);
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
SELECT id FROM zone_state_spawns
WHERE zone_id=202 AND instance_id=0 AND id BETWEEN 54106 AND 54122
ORDER BY id FOR UPDATE;
SET @hub_state_ready = (
    (SELECT COUNT(*) FROM zone_state_spawns
     WHERE zone_id=202 AND instance_id=0 AND id BETWEEN 54106 AND 54122
       AND is_corpse=0 AND is_zone=0
       AND spawngroup_id IN (999220,999221,999222,999223,999224,999225,999226,
                            999234,999235,999236,999237,999238,999239)) = 17
    AND (SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 997900 AND 997915) = 16
    AND (SELECT COUNT(*) FROM spawn2 WHERE zone='poknowledge'
         AND spawngroupID=999226) = 1
);
INSERT INTO hub_state_guard VALUES (@hub_state_ready);
DELETE FROM zone_state_spawns
WHERE @hub_state_ready=1 AND zone_id=202 AND instance_id=0
  AND id BETWEEN 54106 AND 54122 AND is_corpse=0 AND is_zone=0;
SELECT ROW_COUNT() AS cleared_stale_custom_hub_states;
COMMIT;
