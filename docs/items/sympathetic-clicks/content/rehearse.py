"""Execute the shipping SQL on an isolated typed copy of the local test content."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/"tools"))
import sympathetic_content as content


def run():
    db = "nightcap_sympathetic_" + uuid.uuid4().hex
    def sql(query, schema=db, check=True):
        client = ["docker", "exec", "-i", "akk-stack-mariadb-1", "sh", "-c",
                  'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot --default-character-set=utf8mb4 -B -r --skip-column-names "$1"',
                  "rehearsal", schema]
        record = subprocess.run(client, input=query.encode(), capture_output=True, timeout=120)
        if check and record.returncode:
            raise RuntimeError(record.stderr.decode()[-700:])
        return record

    ids = (10150, 210150, 410150, 610150, 10338, 210338, 410338, 610338, 1001)
    id_list = ",".join(map(str, ids))
    forward = content.BOOTSTRAP.read_text()
    disable = (content.CONTENT/"disable.sql").read_text()
    assert forward == content.migration() and disable == content.migration(True)
    assert (ROOT/"eq-solo-gm/scripts/tiered_loot_setup.sql").read_text().rstrip().endswith("SOURCE sympathetic-clicks.sql;")
    sql("CREATE DATABASE " + db, "information_schema")
    try:
        sql("CREATE TABLE items LIKE peq.items; CREATE TABLE spells_new LIKE peq.spells_new;"
            "CREATE TABLE db_str LIKE peq.db_str;"
            f"INSERT INTO items SELECT * FROM peq.items WHERE id IN ({id_list});"
            "INSERT INTO spells_new SELECT * FROM peq.spells_new WHERE id IN (12,44379,44380);"
            "INSERT INTO db_str SELECT * FROM peq.db_str WHERE id IN (12,44379,44380);")
        for table in (content.REFERENCE_FIELDS | content.SAVED_SPELL_FIELDS):
            if table not in ("items", "spells_new"):
                sql(f"CREATE TABLE {table} LIKE peq.{table};")
        columns = [s.decode() for s in sql("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema=DATABASE() AND TABLE_NAME='items' ORDER BY ORDINAL_POSITION").stdout.splitlines()]
        fields = ",".join("`"+k+"`" for k in columns)
        def all_items():
            result = sql("SELECT JSON_ARRAY("+fields+") FROM items ORDER BY id").stdout.splitlines()
            return {row["id"]: row for row in (dict(zip(columns,json.loads(s),strict=True)) for s in result)}
        def check_new():
            return sql("SELECT (SELECT COUNT(*) FROM spells_new WHERE id IN (44379,44380)),"
                       "(SELECT COUNT(*) FROM db_str WHERE type=6 AND id IN (44379,44380));").stdout.strip()
        # Also permit rehearsal after the guarded definitions have been installed.
        if check_new() == b"2\t2":
            sql(forward)
            sql(disable)
            sql("DELETE FROM db_str WHERE type=6 AND id IN (44379,44380); DELETE FROM spells_new WHERE id IN (44379,44380);")
        assert check_new() == b"0\t0"
        before = all_items()
        assert set(before) == set(ids)
        expected = {i: dict(r) for i,r in before.items()}
        for table,key,_,after in content.groups():
            if table == "items":
                expected[key["id"]].update(after[0])
        # Adjacent fields can evolve independently and survive replay/disable.
        for mode, query, image in (("forward",forward,expected), ("replay",forward,expected),
                                   ("disable",disable,before), ("disable replay",disable,before),
                                   ("reenable",forward,expected)):
            sql(query)
            assert all_items() == image, mode
            assert check_new() == b"2\t2"
        for sid, text in content.PREVIOUS_DESCRIPTIONS.items():
            sql(f"UPDATE db_str SET value={content.sql_value(text)} WHERE type=6 AND id={sid}")
        sql(forward)
        for sid, (_, text) in content.SPELLS.items():
            assert sql(f"SELECT value FROM db_str WHERE id={sid} AND type=6").stdout.rstrip() == text.encode()
        assert all_items() == expected
        sql(disable)
        sql("DELETE FROM db_str WHERE type=6 AND id IN (44379,44380); DELETE FROM spells_new WHERE id IN (44379,44380);")
        for mutation, undo in (
            ("UPDATE items SET Name=LOWER(Name) WHERE id=610150", "UPDATE items SET Name='Moonstone Ring (Ascended)' WHERE id=610150"),
            ("UPDATE items SET focuseffect=999 WHERE id=610150", "UPDATE items SET focuseffect=2349 WHERE id=610150"),
            ("UPDATE items SET clicktype=1 WHERE id=410338", "UPDATE items SET clicktype=0 WHERE id=410338"),
            ("INSERT INTO db_str VALUES (44380,6,'Existing description')", "DELETE FROM db_str WHERE id=44380 AND type=6"),
            ("INSERT INTO db_str VALUES (44380,6,"+content.sql_value(content.PREVIOUS_DESCRIPTIONS[44380])+")", "DELETE FROM db_str WHERE id=44380 AND type=6"),
            ("INSERT INTO spells_new (id,name) VALUES (44380,'Existing spell')", "DELETE FROM spells_new WHERE id=44380"),
            ("UPDATE items SET focuseffect=44379 WHERE id=1001", "UPDATE items SET focuseffect=-1 WHERE id=1001"),
            ("UPDATE spells_new SET effect_limit_value8=44380 WHERE id=12", "UPDATE spells_new SET effect_limit_value8=0 WHERE id=12"),
        ):
            sql(mutation)
            drifted, counts = all_items(), check_new()
            result = sql(forward, check=False)
            assert result.returncode and (b"preimage drift" in result.stderr or b"occupied reference" in result.stderr)
            assert all_items() == drifted and check_new() == counts
            sql(undo)
        sql("UPDATE items SET hp=hp+1 WHERE id=610338")
        changed = all_items()[610338]["hp"]
        sql(forward)
        assert all_items()[610338]["hp"] == changed
        sql("INSERT INTO character_buffs (character_id,slot_id,spell_id,caster_level,caster_name,"
            "ticsremaining,counters,numhits,melee_rune,magic_rune,persistent) "
            "VALUES (1,0,44380,50,'QA',-1000,0,0,0,0,0)")
        sql(forward)
        sql("INSERT INTO character_spells (id,slot_id,spell_id) VALUES (1,0,44379)")
        invalid_book = sql(forward, check=False)
        assert invalid_book.returncode and b"occupied reference: character_spells" in invalid_book.stderr
        sql("DELETE FROM character_spells WHERE id=1")
        sql(disable)
        assert all_items()[610338]["hp"] == changed
        sql("DELETE FROM spells_new WHERE id=44380")
        partial = sql(forward, check=False)
        assert partial.returncode and b"occupied reference: character_buffs" in partial.stderr
        assert check_new() == b"1\t2" and all_items()[610150]["clickeffect"] == -1
        return dict(status="passed", environment="isolated typed MariaDB clone of local PEQ",
                    item_rows=len(before), checked_columns_per_item=len(columns),
                    item_changed_fields=sorted(k for k in columns if expected[610338][k] != before[610338][k]),
                    controls=["forward", "exact replay", "disable with saved spell definitions", "disable replay",
                              "reenable", "case-sensitive item name drift", "worn focus drift", "lower tier drift",
                              "occupied description", "occupied spell", "late conflict transaction rollback",
                              "foreign orphan item focus", "foreign spell effect operand",
                              "active buff replay", "scribed reference on replay", "partial install with orphan saved buff",
                              "prior candidate description update", "prior description without owning spell refusal",
                              "unrelated stat survives forward and disable"],
                    sql_sha256=hashlib.sha256(content.BOOTSTRAP.read_bytes()).hexdigest())
    finally:
        sql("DROP DATABASE " + db, "information_schema")


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
