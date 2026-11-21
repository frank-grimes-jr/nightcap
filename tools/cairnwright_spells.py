"""Build the RoF2 spell file and matching PEQ candidate SQL from the same overrides."""
import argparse
import hashlib
from pathlib import Path


# (RoF2 field number, PEQ column) for every modified value. Keep the 237-field
# client format intact. The paired class catalog owns class-17 eligibility.
FIELDS = {
    "id": 0, "name": 1, "cast_on_you": 6, "cast_on_other": 7,
    "cast_time": 13, "recast_time": 15, "mana": 19, "effect_base_value1": 20,
    "resisttype": 85, "effectid1": 86, "descnum": 155,
    **{f"classes{i}": 103 + i for i in range(1, 17)},
}
SPELLS = (
    (205, "True North", dict(id=44381, name="Strike Cairn", cast_time=1000,
                            recast_time=4000, mana=4, effectid1=254, effect_base_value1=0)),
    (205, "True North", dict(id=44382, name="Sound the Seam", cast_time=1000,
                            recast_time=6000, mana=5, effectid1=254, effect_base_value1=0)),
    (93, "Burst of Flame", dict(id=44383, name="Seam Fracture", cast_time=0,
                               recast_time=0, mana=0, resisttype=1, effect_base_value1=-5)),
)
TEMPLATE_HASHES = {
    93: "73075751db2aeb4ff6056da241f5af715102e388597c37527e82a148ee7311ef",
    205: "1dd8f0fdaf31e71cc7cdcac37bd9f9c65c876ce3b8f36d845f136064c166c5d6",
}


def variants():
    for base, name, fields in SPELLS:
        yield base, name, {
            **{f"classes{i}": 255 for i in range(1, 17)},
            "cast_on_you": "", "cast_on_other": "", "descnum": 0, **fields,
        }


def client_file(raw):
    templates = {}
    ids = {f["id"] for _, _, f in variants()}
    names = {f["name"].lower().encode() for _, _, f in variants()}
    parents = {base for base, _, _ in variants()}
    for line in raw.splitlines():
        head = line.split(b"^", 2)
        if len(head) < 2 or not head[0].isdigit():
            raise ValueError("Invalid RoF2 spell row")
        spell = int(head[0])
        if spell in ids or head[1].lower() in names:
            raise ValueError(f"Cairnwright spell collision at {spell}")
        if spell in parents:
            if spell in templates:
                raise ValueError(f"Duplicate template {spell}")
            if hashlib.sha256(line).hexdigest() != TEMPLATE_HASHES[spell]:
                raise ValueError(f"Unreviewed template {spell}")
            templates[spell] = line.split(b"^")
    additions = []
    for base, name, fields in variants():
        row = list(templates.get(base, ()))
        if len(row) != 237 or row[1] != name.encode():
            raise ValueError(f"Missing or incompatible RoF2 template {base}")
        for field, value in fields.items():
            row[FIELDS[field]] = str(value).encode("ascii")
        additions.append(b"^".join(row))
    newline = b"\r\n" if b"\r\n" in raw else b"\n"
    separator = b"" if raw.endswith(b"\n") else newline
    return raw + separator + newline.join(additions) + newline


def sql_value(value):
    if isinstance(value, int):
        return str(value)
    return "'" + value.replace("'", "''") + "'"


def server_sql():
    lines = [
        "CREATE TEMPORARY TABLE crw_new LIKE spells_new;",
        "CREATE TEMPORARY TABLE crw_check (ok INT NOT NULL CHECK (ok = 1));",
    ]
    for base, name, fields in variants():
        lines.append(f"INSERT INTO crw_new SELECT * FROM spells_new WHERE id={base} AND name={sql_value(name)};")
        assignments = ", ".join(f"`{k}`={sql_value(v)}" for k, v in fields.items())
        lines.append(f"UPDATE crw_new SET {assignments} WHERE id={base};")
    # Compare all columns of any existing rows before accepting a replay.
    # A conflicting concurrent insert also fails the primary-key constraint.
    lines += [
        "INSERT INTO crw_check SELECT COUNT(*) = 3 FROM crw_new;",
        "INSERT INTO crw_check SELECT COUNT(*) = 0 FROM spells_new s JOIN crw_new c ON s.name = c.name AND s.id <> c.id;",
        "INSERT INTO crw_check SELECT COUNT(*) = 0 FROM (SELECT s.* FROM spells_new s JOIN crw_new c ON s.id=c.id EXCEPT SELECT * FROM crw_new) changed;",
        "INSERT INTO spells_new SELECT c.* FROM crw_new c LEFT JOIN spells_new s ON s.id=c.id WHERE s.id IS NULL;",
        "DROP TEMPORARY TABLE crw_check, crw_new;",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path, help="New directory for the paired candidate")
    args = parser.parse_args()
    client = client_file(args.source.read_bytes())
    sql = server_sql()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "spells_us.txt").write_bytes(client)
    (args.output_dir / "spells_new.sql").write_text(sql, encoding="ascii")
