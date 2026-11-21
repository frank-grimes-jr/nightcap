"""Generate local SQL rehearsals. All game tables are shadowed for this connection."""
import argparse
from pathlib import Path

def rehearsal(drift):
    migration = (Path(__file__).resolve().parents[3] / "server-mods/sql/cairnwright_creation.sql").read_text()
    kit = (Path(__file__).resolve().parents[3] / "server-mods/sql/cairnwright_starter_items.sql").read_text()
    # Copy SELECT results before shadowing each real table; copy the original
    # primary keys separately so replay exercises the same uniqueness checks.
    parts = []
    for name, predicate in (
        ("items", "id IN (1060,6014)"),
        ("char_create_point_allocations", "id=14"),
        ("char_create_combinations", "race=8 AND class=3"),
        ("start_zones", "player_race=8 AND player_class=3"),
    ):
        parts += [
            f"CREATE TEMPORARY TABLE crw_fixture LIKE {name};",
            f"INSERT INTO crw_fixture SELECT * FROM {name} WHERE {predicate};",
            f"CREATE TEMPORARY TABLE {name} LIKE crw_fixture;",
            f"INSERT INTO {name} SELECT * FROM crw_fixture;",
            "DROP TEMPORARY TABLE crw_fixture;",
        ]
    parts += [kit, kit, migration, migration, "CREATE TEMPORARY TABLE crw_result (ok INT CHECK (ok = 1));",
              "INSERT INTO crw_result SELECT COUNT(*)=2 FROM items WHERE classes=65536 AND id IN (998616,998636);",
              "INSERT INTO crw_result SELECT COUNT(*)=1 FROM char_create_combinations WHERE class=17;",
              "INSERT INTO crw_result SELECT COUNT(*)=1 FROM start_zones WHERE player_class=17 AND bind_id=22;",
              "SELECT 'PASS first application and replay';"]
    if drift:
        parts += ["UPDATE start_zones SET bind_id=1 WHERE player_class=17;", migration,
                  "SELECT 'ERROR drift was accepted';"]
    return "\n".join(parts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drift", action="store_true")
    print(rehearsal(parser.parse_args().drift))
