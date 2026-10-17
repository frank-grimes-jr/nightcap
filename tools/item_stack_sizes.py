"""Prepare a guarded item stack-size migration; never connects to a database.

Capture CAPTURE_SQL with a read-only MariaDB session, --batch --raw and
--skip-column-names. Keep the TSV and generated SQL with the stopped backup.
The SQL must run with player access closed and the game stopped. Once players
can form larger stacks, lowering limits requires a separate inventory audit.
"""
import argparse
import hashlib
import json
from pathlib import Path


MINIMUM = 100
CAPTURE_SQL = """SELECT id, stackable, stacksize FROM items
WHERE stackable=1 AND stacksize<100 ORDER BY id;"""


def read_snapshot(text):
    rows = []
    seen = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        values = line.split("\t")
        if len(values) != 3:
            raise ValueError("Expected id, stackable, stacksize TSV without a header")
        item_id, stackable, size = map(int, values)
        if not 0 < item_id <= 4294967295 or item_id in seen:
            raise ValueError("Invalid or duplicate item ID")
        if stackable != 1 or not 1 <= size < MINIMUM:
            raise ValueError("Snapshot must contain only valid stackable items below 100")
        rows.append((item_id, size))
        seen.add(item_id)
    if not rows:
        raise ValueError("No eligible items; verify existing limits before treating as applied")
    return sorted(rows)


def migration(snapshot):
    rows = read_snapshot(snapshot)
    inserts = []
    for offset in range(0, len(rows), 500):
        values = ",".join(f"({item_id},{size})" for item_id, size in rows[offset:offset + 500])
        inserts.append("INSERT INTO nightcap_stack_plan (id,old_size) VALUES " + values + ";")
    return """-- Nightcap item stack minimum 100. Requires stopped game and closed access.
-- Only items.stacksize changes. Do not use mariadb --force.
-- No automatic down migration: retain larger limits after any player access.
CREATE TEMPORARY TABLE nightcap_stack_plan (
 id INT UNSIGNED PRIMARY KEY, old_size INT NOT NULL
) ENGINE=InnoDB;
""" + "\n".join(inserts) + f"""
DELIMITER //
BEGIN NOT ATOMIC
 DECLARE n BIGINT;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 SELECT COUNT(*) INTO n FROM information_schema.TABLES
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='items' AND ENGINE='InnoDB';
 IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Items engine drift'; END IF;
 SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS
 WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='items';
 IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected items trigger'; END IF;
 SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
 START TRANSACTION;
 SELECT COUNT(*) INTO n FROM items WHERE stackable=1 AND stacksize<100 FOR UPDATE;
 IF n<>{len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Stack candidate count drift'; END IF;
 SELECT COUNT(*) INTO n FROM items i JOIN nightcap_stack_plan p ON p.id=i.id
 WHERE i.stackable=1 AND i.stacksize=p.old_size;
 IF n<>{len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Stack preimage drift'; END IF;
 UPDATE items i JOIN nightcap_stack_plan p ON p.id=i.id
 SET i.stacksize=100 WHERE i.stackable=1 AND i.stacksize=p.old_size;
 SET n=ROW_COUNT();
 IF n<>{len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Stack update count mismatch'; END IF;
 SELECT COUNT(*) INTO n FROM items WHERE stackable=1 AND stacksize<100;
 IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Stack minimum verification failed'; END IF;
 COMMIT;
END //
DELIMITER ;
DROP TEMPORARY TABLE nightcap_stack_plan;
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path, help="New output directory (never overwritten)")
    args = parser.parse_args()
    snapshot = args.snapshot.read_text(encoding="utf-8-sig")
    rows = read_snapshot(snapshot)
    sql = migration(snapshot)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "before.tsv").write_text(snapshot, encoding="utf-8", newline="\n")
    (args.output / "forward.sql").write_text(sql, encoding="utf-8", newline="\n")
    receipt = dict(minimum=MINIMUM, affected_items=len(rows),
                   snapshot_sha256=hashlib.sha256(snapshot.encode()).hexdigest(),
                   sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),
                   applied=False, requires_game_restart=True)
    (args.output / "plan.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
