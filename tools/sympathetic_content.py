"""Generate the two Classic click definitions and stage their paired RoF2 files."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path

from wpm_migration import equal_group, insert, predicate
from rabid_bear import sql_value


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "docs/items/sympathetic-clicks/content"
BOOTSTRAP = ROOT / "eq-solo-gm/scripts/sympathetic-clicks.sql"
RELEASE = 2026111202
MANIFEST = "e01559e2d90acf38af4ef14d62985bd0ac9d31907bbecf768c72c4b391f2bb35"
SPELLS = {
    44379: ("Sympathetic Strike I", "When a single-target direct damage spell costing at least 10 base mana lands, it deals one extra hit for 5% of its largest direct hit, rounded down to a maximum of 48 damage. Target defenses apply. This extra hit grants no lifetap healing."),
    44380: ("Sympathetic Healing I", "A single-target direct heal costing mana adds one heal on the same recipient for 5% of its largest direct heal before overheal, rounded down to a maximum of 48 health. Missing health limits the result. A successful worn sympathetic heal takes precedence."),
}
# A disposable encounter fixture used the earlier exact pair of descriptions.
PREVIOUS_DESCRIPTIONS = {
    44379: "Your landed single-target direct damage spells costing at least 10 base mana deal an additional 8 base damage once per cast. The extra hit cannot return health from a lifetap.",
    44380: "Your single-target direct healing spells costing mana heal the same recipient for an additional 12 base health once per cast. A successful worn sympathetic heal takes precedence.",
}
FAMILIES = {
    10338: ("Runed Lava Pendant", 32, -1, 44379),
    10150: ("Moonstone Ring", 98304, 2349, 44380),
}
CLICK = dict(clickeffect=-1, clicktype=0, clicklevel=0, clicklevel2=0,
            clickname="", casttime=0, casttime_=0, maxcharges=0, recastdelay=0, recasttype=0)

REFERENCE_FIELDS = {
    "items": ("clickeffect", "scrolleffect", "worneffect", "proceffect", "bardeffect", "focuseffect"),
    "spells_new": ("RecourseLink", "spellgroup", "descnum", *(
        f"{prefix}{slot}" for slot in range(1, 13)
        for prefix in ("effect_base_value", "effect_limit_value", "max"))),
    "aa_ranks": ("spell",), "aa_rank_effects": ("base1", "base2"),
    "npc_spells": ("attack_proc", "range_proc", "defensive_proc"),
    "npc_spells_entries": ("spellid",), "npc_spells_effects_entries": ("se_base", "se_limit", "se_max"),
    "auras": ("type", "spell_id"), "traps": ("effectvalue", "effectvalue2"),
    "blocked_spells": ("spellid",), "damageshieldtypes": ("spellid",),
    "ldon_trap_templates": ("spell_id",), "spell_buckets": ("spell_id",), "spell_globals": ("spellid",),
}
SAVED_SPELL_FIELDS = {
    "character_auras": ("spell_id",), "character_buffs": ("spell_id",),
    "character_memmed_spells": ("spell_id",), "character_pet_buffs": ("spell_id",),
    "character_pet_info": ("spell_id",), "character_spells": ("spell_id",),
    "merc_buffs": ("SpellId",),
}


def reference_check(table, columns, saved=False):
    """An absent spells_new row can still be referenced by another item or spell."""
    ids = ",".join(str(sid) for sid in SPELLS)
    clauses = []
    for column in columns:
        condition = f"`{column}` IN ({ids})"
        if table == "items" and column == "clickeffect":
            owners = " OR ".join(f"(id={base + 600000} AND clickeffect={sid})"
                                 for base, (_, _, _, sid) in FAMILIES.items())
            condition += " AND NOT (" + owners + ")"
        clauses.append("(" + condition + ")")
    where = "(" + " OR ".join(clauses) + ")"
    if table == "spells_new":
        # Candidate rows are independently compared across all 237 fields.
        where += f" AND id NOT IN ({ids})"
    if saved and table == "character_buffs":
        # Each saved buff needs its own installed spell. The 237-field checks
        # below verify that exact identity. Item clicks never become scribed
        # spells, auras, pet or merc buffs, even after a previous installation.
        where += " AND NOT EXISTS (SELECT 1 FROM spells_new s WHERE s.id=character_buffs.spell_id)"
    return f" IF EXISTS (SELECT 1 FROM {table} WHERE {where}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Classic sympathetic occupied reference: {table}'; END IF;"


def spell_rows():
    fixture = ROOT / "tools/fixtures/wpm-content-20261018.json.gz"
    catalog = json.loads(gzip.decompress(fixture.read_bytes()))
    template = next(r for r in catalog["tables"]["spells_new"] if r["id"] == 12)
    rows = []
    for sid, (name, _) in SPELLS.items():
        row = dict(template, id=sid, name=name, descnum=sid, spellgroup=sid,
                   targettype=6, range=0, mana=0, cast_time=2000, recovery_time=0,
                   recast_time=0, buffdurationformula=50, buffduration=1, short_buff_box=0,
                   effectid1=254, effect_base_value1=0, formula1=100, max1=0,
                   spell_fades=f"{name} fades.", cast_on_other="", cast_on_you=f"You gain {name}.",
                   SpellAffectIndex=-1, skill=18, typedescnum=0, effectdescnum=0,
                   npc_category=0, npc_usefulness=0, spell_category=-99)
        for index in range(1, 17):
            row[f"classes{index}"] = 255
        if sid == 44379:
            row.update(icon=2515, memicon=2052, new_icon=51, spellanim=276)
        if len(row) != 237:
            raise ValueError("Unexpected RoF2 spell schema")
        rows.append(row)
    return rows


def groups(disable=False):
    """Keep spell and text definitions on disable, including for saved buffs."""
    plans = []
    for row in spell_rows():
        sid = row["id"]
        description = dict(id=sid, type=6, value=SPELLS[sid][1])
        for table, key, after in (("spells_new", {"id": sid}, row),
                                  ("db_str", {"id": sid, "type": 6}, description)):
            plans.append((table, key, [after] if disable else [], [after]))
    for base, (name, slots, focus, sid) in FAMILIES.items():
        for tier, suffix in enumerate(("", " (Polished)", " (Exalted)", " (Ascended)")):
            item_id = base + 200000 * tier
            before = dict(id=item_id, Name=name + suffix, slots=slots, classes=65535, races=65535,
                          reqlevel=0, reclevel=0, deity=0, focuseffect=focus, worneffect=-1,
                          proceffect=-1, bardeffect=-1, **CLICK)
            after = dict(before)
            if tier == 3:
                after.update(clickeffect=sid, clicktype=4, clicklevel=1, clicklevel2=1,
                             clickname=SPELLS[sid][0], casttime=2000, casttime_=2000, maxcharges=-1)
            if disable:
                before, after = after, before
            plans.append(("items", {"id": item_id}, [before], [after]))
    return plans


def migration(disable=False):
    # MariaDB anonymous blocks leave no persistent procedure on failure.
    sql = ["-- Generated by tools/sympathetic_content.py", "DELIMITER //", "BEGIN NOT ATOMIC",
           " DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;",
           " SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;", " START TRANSACTION;"]
    for table in ("spells_new", "db_str", "items"):
        sql.append(f" IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected {table} storage'; END IF;")
    if not disable:
        sql.extend(reference_check(table, cols) for table, cols in REFERENCE_FIELDS.items())
        sql.extend(reference_check(table, cols, saved=True) for table, cols in SAVED_SPELL_FIELDS.items())
        # Upgrade only the prior candidate's exact description paired with its
        # already-installed, identical 237-field spell. A standalone stale or
        # unrelated text row must still abort the entire migration.
        for spell in spell_rows():
            sid = spell["id"]
            key = {"id": sid, "type": 6}
            previous = dict(key, value=PREVIOUS_DESCRIPTIONS[sid])
            sql.append(f" IF {equal_group('db_str', key, [previous])} AND {equal_group('spells_new', {'id': sid}, [spell])} THEN")
            sql.append(f"  UPDATE db_str SET value={sql_value(SPELLS[sid][1])} WHERE {predicate(key)};")
            sql.append(" END IF;")
    for table, key, before, after in groups(disable):
        matches = equal_group(table, key, after)
        sql.extend([f" IF NOT ({matches}) THEN",
                    f"  IF NOT ({equal_group(table, key, before)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Classic sympathetic {table} {key['id']} preimage drift'; END IF;"])
        if not before:
            sql.append("  " + insert(table, after[0]))
        else:
            changed = [f"`{k}`={sql_value(v)}" for k, v in after[0].items() if v != before[0][k]]
            if changed:
                sql.append(f"  UPDATE {table} SET {','.join(changed)} WHERE {predicate(key)};")
        sql.extend([f"  IF NOT ({matches}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Classic sympathetic {table} {key['id']} afterimage mismatch'; END IF;", " END IF;"])
    sql.extend([" COMMIT;", "END//", "DELIMITER ;", ""])
    return "\n".join(sql)


def overlay(raw, name):
    """Append only missing exact identities; preserve all previous asset bytes."""
    spells = name == "spells_us.txt"
    wanted = {
        (str(r["id"]).encode(),): "^".join("" if v is None else str(v) for v in r.values()).encode("ascii")
        for r in spell_rows()
    } if spells else {
        (str(sid).encode(), b"6"): f"{sid}^6^{desc}^0".encode("ascii") for sid, (_, desc) in SPELLS.items()
    }
    seen = set()
    for raw_line in raw.split(b"\n"):
        line = raw_line.removesuffix(b"\r")
        if not line:
            continue
        fields = line.split(b"^")
        if spells and len(fields) != 237:
            raise ValueError("Expected 237 RoF2 spell fields")
        key = tuple(fields[:1 if spells else 2])
        if key in wanted:
            if key in seen or line != wanted[key]:
                raise ValueError(f"Occupied or duplicate {name} identity {key}")
            seen.add(key)
    additions = [row for key, row in wanted.items() if key not in seen]
    if not additions:
        return raw
    ending = b"\r\n" if b"\r\n" in raw else b"\n"
    return raw + (b"" if raw.endswith(b"\n") else ending) + ending.join(additions) + ending


def stage(source, out):
    source = source.resolve(strict=True)
    out = out.resolve()
    if out == source or source in out.parents:
        raise ValueError("Stage outside the installed client")
    active = json.loads((source / ".nightcap/active.json").read_bytes())
    manifest_bytes = base64.b64decode(active["Manifest"], validate=True)
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST:
        raise ValueError("Unexpected launcher manifest digest")
    manifest = json.loads(manifest_bytes)
    if active["Release"] != RELEASE or manifest["release"] != RELEASE or active["ManifestDigest"] != MANIFEST:
        raise ValueError("Unexpected launcher release")
    files = {f["path"]: f for f in manifest["files"]}
    result, payload = {}, {}
    for name in ("spells_us.txt", "dbstr_us.txt"):
        raw = (source / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != files[name]["sha256"] or len(raw) != files[name]["size"]:
            raise ValueError(f"Installed {name} differs from signed release")
        candidate = overlay(raw, name)
        if not candidate.startswith(raw) or candidate == raw or overlay(candidate, name) != candidate:
            raise ValueError(f"Invalid append-only overlay for {name}")
        payload[name] = candidate
        result[name] = dict(source_sha256=digest, staged_sha256=hashlib.sha256(candidate).hexdigest(),
                            bytes_added=len(candidate)-len(raw), appended_rows=2)
    out.mkdir(parents=True, exist_ok=False)
    for name, data in payload.items():
        (out / name).write_bytes(data)
    receipt = dict(status="unsigned local test overlay", launcher_release=RELEASE,
                   source_manifest_sha256=MANIFEST, files=result)
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    command.add_parser("generate")
    command.add_parser("check")
    client = command.add_parser("stage-client")
    client.add_argument("--source", required=True, type=Path)
    client.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "stage-client":
        print(json.dumps(stage(args.source, args.out), indent=2))
        return
    for path, sql in ((BOOTSTRAP, migration()), (CONTENT/"disable.sql", migration(disable=True))):
        if args.command == "generate":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(sql, encoding="utf-8", newline="\n")
        elif path.read_text(encoding="utf-8") != sql:
            raise ValueError(f"Generated migration drift: {path}")


if __name__ == "__main__":
    main()
