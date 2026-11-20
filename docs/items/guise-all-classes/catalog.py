"""Guard the complete four-row Guise preimage while widening class eligibility."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDS = (2469, 202469, 402469, 602469)

def changes():
    rows = json.loads((HERE / "before.json").read_bytes())["items"]
    assert tuple(int(row["id"]) for row in rows) == IDS
    assert all(row["classes"] == "384" and row["races"] == "65535" for row in rows)
    return {int(row["id"]): (row, (384,), (65535,)) for row in rows}

def matches(row):
    parts = []
    for field, value in row.items():
        assert field.replace("_", "").isalnum()
        literal = "NULL" if value is None else "CONVERT(X'" + value.encode().hex() + "' USING utf8mb4)"
        parts.append(f"BINARY CAST(`{field}` AS CHAR) <=> BINARY {literal}")
    return " AND ".join(parts)

def generate(action):
    if action not in ("before", "forward", "verify", "rollback"):
        raise ValueError(action)
    statements = ["START TRANSACTION;", "CREATE TEMPORARY TABLE guise_guard(ok TINYINT NOT NULL CHECK(ok=1));"]
    for key, (original, _, _) in changes().items():
        old, new = dict(original), dict(original, classes="65535")
        if action == "rollback":
            old, new = new, old
        before, after = matches(old), matches(new)
        allowed = after if action == "verify" else before if action == "before" else f"(({before}) OR ({after}))"
        statements.append(f"INSERT INTO guise_guard SELECT COUNT(*)=1 FROM items WHERE id={key} AND ({allowed}) FOR UPDATE;")
        if action in ("forward", "rollback"):
            statements.append(f"UPDATE items SET classes={new['classes']} WHERE id={key} AND ({before});")
            statements.append(f"INSERT INTO guise_guard SELECT COUNT(*)=1 FROM items WHERE id={key} AND ({after});")
    return "\n".join(statements + ["COMMIT;", "DROP TEMPORARY TABLE guise_guard;"])

if __name__ == "__main__":
    import sys
    print(generate(sys.argv[1]))

