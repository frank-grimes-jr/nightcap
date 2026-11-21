"""Plan statless ornament definitions from the target PEQ export and paired RoF2 files.

Use --query to export tab-separated rows with mariadb --batch --raw. Names are
hex-encoded so tabs, quotes and line breaks cannot change record boundaries.
"""
import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct
import zlib

from classic_model_archives import actor_names, DIRECTORY_CRC

ARMOR = 4 | 128 | 1536 | 4096 | 131072 | 262144 | 524288
HANDS = 8192 | 16384
RANGE = 2048
FIRST, LAST = 1000000, 1048575
MARKER = "Nightcap appearance ornament"
FIELDS = "id,hex(name) as label,itemclass,itemtype,slots,augtype,augrestrict,idfile,material,elitematerial,herosforgemodel,color,icon,bagtype,charmfile,augslot1type,augslot2type,augslot3type,augslot4type,augslot5type,augslot6type"
QUERY = f"SELECT {FIELDS} FROM items ORDER BY id"
RESTRICTION = {0:5, 1:9, 2:7, 3:6, 4:10, 5:12, 8:13, 35:11, 45:8}
MOLDS = {"1hp":7, "1hs":5, "2hb":10, "2hp":11, "2hs":9, "blunt":2,
         "1hb":6, "bow":12, "hth":8, "shield":13, "slashing":2}
ARMOR_MASKS = (4, 131072, 128, 1536, 4096, 262144, 524288, 131072)


def inflate(stream, entry):
    offset, size = entry
    stream.seek(offset)
    data = bytearray()
    while len(data) < size:
        packed, length = struct.unpack("<II", stream.read(8))
        block = zlib.decompress(stream.read(packed))
        if len(block) != length or not length:
            raise ValueError("Malformed equipment archive block")
        data.extend(block)
    if len(data) != size:
        raise ValueError("Malformed equipment archive entry")
    return bytes(data)


def models_in_archive(path):
    # Read the directory and filenames. EQG geometry and textures can be large
    # and need not be inflated to identify an actor. Classic S3D stores the
    # actor definitions inside its WLD, which does need to be read.
    with path.open("rb") as stream:
        directory, signature = struct.unpack("<I4s", stream.read(8))
        if signature != b"PFS ":
            return set()
        stream.seek(directory)
        count, = struct.unpack("<I", stream.read(4))
        entries = {crc: (offset, size) for crc, offset, size in
                   struct.iter_unpack("<III", stream.read(count * 12))}
        if DIRECTORY_CRC not in entries:
            return set()
        names = inflate(stream, entries[DIRECTORY_CRC])
        pos = 4
        models = set()
        for _ in range(struct.unpack_from("<I", names)[0]):
            length, = struct.unpack_from("<I", names, pos)
            name = names[pos + 4:pos + 4 + length - 1].decode("latin1").lower()
            pos += 4 + length
            model = re.fullmatch(r"it(\d+)\.(?:mod|mds)", name)
            if model:
                models.add(int(model[1]))
            elif name.endswith(".wld") and path.suffix.lower() == ".s3d":
                from classic_model_archives import crc_name
                actors = actor_names(inflate(stream, entries[crc_name(name)]))
                for actor in actors:
                    match = re.fullmatch(r"IT(\d+)_ACTORDEF", actor, re.I)
                    if match:
                        models.add(int(match[1]))
        return models


def client_catalog(client):
    # Named LoN, seasonal and armor packs often lack "equip" in the filename.
    files = set(client.glob("*.eqg")) | set(client.glob("*equip*.s3d")) | {client / "global_obj.s3d"}
    models = set().union(*(models_in_archive(p) for p in sorted(files)))
    tags = {}
    for line in (client / "Resources/NewArmorTagData.txt").read_text(encoding="latin1").splitlines():
        fields = line.partition("#")[0].split()
        if len(fields) >= 3 and fields[0].isdigit() and fields[2].isdigit():
            model = int(fields[0])
            if model % 100 < len(ARMOR_MASKS) and int(fields[2]) in models:
                tags[model] = ARMOR_MASKS[model % 100]
    if not models or not tags:
        raise ValueError("Missing held models or Hero's Forge tags")
    return models, tags


@dataclass(frozen=True, order=True)
class Look:
    socket: int
    slots: int
    restriction: int
    model: int
    material: int
    elite: int
    hero: int
    color: int
    icon: int


def classify(row, models, tags):
    kind, slots, aug = row["itemtype"], row["slots"], row["augtype"]
    armor = slots & ARMOR
    model_text = re.fullmatch(r"IT(\d+)", row["idfile"], re.I)
    model = int(model_text[1]) if model_text else 0
    restriction = RESTRICTION.get(kind, 0)
    mold = row["itemclass"] == 1 and row["bagtype"] == 55
    ornament = bool(aug & (3 << 19))
    if mold:
        restriction = MOLDS.get(row["charmfile"].lower().removeprefix("itemtransfig"))
        if restriction is None or model in (0, 63):
            return None
        slots = {12:RANGE, 13:16384, 9:8192, 10:8192, 11:8192}.get(restriction, HANDS)
    elif ornament:
        restriction = row["augrestrict"] if row["augrestrict"] <= 15 else 0
    elif row["itemclass"] or aug or kind == 54:
        return None
    if (aug & (1 << 20)) or (armor and not mold and not (slots & HANDS) and kind != 5):
        if not armor or (ornament and not (row["herosforgemodel"] or row["material"] or row["elitematerial"])):
            return None
        hero = row["herosforgemodel"]
        if hero and not any((tag == hero or (hero < 1000 and tag // 100 == hero)) and mask & armor
                            for tag, mask in tags.items()):
            return None
        return Look(21, armor, 0, 0, row["material"], row["elitematerial"], hero, row["color"], row["icon"])
    mask = slots & (HANDS | RANGE) if ornament or mold else (slots & RANGE if kind == 5 else slots & HANDS)
    if mask and model in models:
        return Look(20, mask, restriction, model, row["material"], row["elitematerial"], 0, row["color"], row["icon"])
    return None


def sql_text(value):
    return "CONVERT(X'" + value.encode("utf8").hex() + "' USING utf8mb4)"


def build(rows, models, tags):
    labels, donors, counts = {}, [], Counter()
    stock_labels = set()
    fingerprint = 0
    for raw in rows:
        row = {k: (v if k in {"idfile", "charmfile", "label"} else int(v)) for k, v in raw.items()}
        ident = row["id"]
        if FIRST <= ident <= LAST:
            continue
        fingerprint ^= zlib.crc32("|".join(raw.values()).encode("utf8"))
        counts["source_rows"] += 1
        visible = (row["itemclass"] == 0 and not row["augtype"] and row["itemtype"] != 54 and
                   row["slots"] & (ARMOR | HANDS | (RANGE if row["itemtype"] == 5 else 0)))
        if visible:
            counts["visible_hosts"] += 1
            if not any(row[f"augslot{i}type"] in (0,20,21) for i in range(1,7)):
                raise ValueError(f"No free ornament socket on item {ident}")
        look = classify(row, models, tags)
        stock = bool(row["augtype"] & (3 << 19)) or row["bagtype"] == 55
        if not look:
            if stock:
                counts["unsupported_stock_rows"] += 1
            continue
        name = bytes.fromhex(row["label"]).decode("utf8", errors="replace")
        if look not in labels or (stock and look not in stock_labels):
            labels[look] = name
        if stock:
            stock_labels.add(look)
        if not stock:
            donors.append((ident, look))
        counts["supported_stock_rows" if stock else "convertible_rows"] += 1
    # Include client-tagged armor even when PEQ has no ornament for that slot.
    covered = {(look.hero if look.hero >= 1000 else look.hero * 100 + slot)
               for look in labels if look.hero for slot, mask in enumerate(ARMOR_MASKS[:7]) if look.slots & mask}
    for tag, mask in tags.items():
        if tag not in covered:
            look = Look(21, mask, 0, 0, 0, 0, tag, 0, 646)
            slot = ("Helm", "Chest", "Arms", "Wrist", "Hands", "Legs", "Boots", "Robe")[tag % 100]
            labels[look] = f"Hero's Forge {slot} {tag}"
    if not donors or not any(look.socket == 20 for look in labels):
        raise ValueError("Incomplete PEQ export")
    counts["unique_designs"] = len(labels)
    counts["source_crc_xor"] = fingerprint
    return labels, donors, counts


def chunks(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def write_plan(path, labels, donors, counts):
    # A persistent key owns each item ID. Adding a model in a future client
    # cannot renumber an ornament already held in inventory.
    keys = {look: ":".join(str(v) for v in vars(look).values()) for look in labels}
    with path.open("w", encoding="utf8", newline="\n") as out:
        def emit(line):
            print(line, file=out)
        fields = [col.split(" as ")[0] for col in FIELDS.split(",")]
        expression = ",".join(f"COALESCE({col},'NULL')" for col in fields)
        emit(f"SET @expected_rows={counts['source_rows']}, @expected_checksum={counts['source_crc_xor']};")
        fingerprint_sql = f"SELECT COUNT(*),BIT_XOR(CRC32(CONCAT_WS('|',{expression}))) INTO @actual_rows,@actual_checksum FROM items WHERE id NOT BETWEEN {FIRST} AND {LAST};"
        emit("CREATE TABLE IF NOT EXISTS nightcap_ornament_design (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, visual VARCHAR(160) NOT NULL UNIQUE, active TINYINT NOT NULL DEFAULT 0) ENGINE=InnoDB AUTO_INCREMENT=1000000;")
        emit("CREATE TABLE IF NOT EXISTS nightcap_ornament_source (donor INT UNSIGNED PRIMARY KEY, ornament INT UNSIGNED NOT NULL) ENGINE=InnoDB;")
        emit("CREATE TEMPORARY TABLE designs (visual VARCHAR(160) PRIMARY KEY, label VARCHAR(64), socket INT, slots INT, restriction_id INT, model INT, mat INT, elite INT, hero INT, tint BIGINT UNSIGNED, icon INT);")
        emit("CREATE TEMPORARY TABLE donors (donor INT UNSIGNED PRIMARY KEY, visual VARCHAR(160));")
        for batch in chunks(sorted(labels)):
            values = []
            for look in batch:
                name = labels[look]
                label = name[:63] if "ornament" in name.lower() else name[:54] + " Ornament"
                values.append("(" + ",".join([sql_text(keys[look]), sql_text(label)] + [str(v) for v in vars(look).values()]) + ")")
            emit("INSERT INTO designs VALUES " + ",".join(values) + ";")
        for batch in chunks(donors):
            emit("INSERT INTO donors VALUES " + ",".join(f"({ident},'{keys[look]}')" for ident, look in batch) + ";")
        emit((Path(__file__).parent.parent / "docs/items/visible-ornaments/install.sql").read_text(encoding="utf8").replace("-- EXPORT_FINGERPRINT", fingerprint_sql))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--query", action="store_true")
    parser.add_argument("--client", type=Path)
    parser.add_argument("--items", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.query:
        print(QUERY + ";")
        return
    models, tags = client_catalog(args.client)
    with args.items.open(encoding="utf-8-sig", newline="") as data:
        labels, donors, counts = build(csv.DictReader(data, delimiter="\t", quoting=csv.QUOTE_NONE), models, tags)
    write_plan(args.output, labels, donors, counts)
    print(json.dumps(dict(counts, held_models=len(models), armor_tags=len(tags)), indent=2))


if __name__ == "__main__":
    main()
