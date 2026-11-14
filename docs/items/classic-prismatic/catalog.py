"""Install or verify the Classic augment release through a MariaDB session.

Emit SQL scoped to the nine recorded stock families, twelve scales and
three jewelcraft recipes. The client must stop on its first SQL error.
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATS = ("healamt", "spelldmg", "hp", "mana")
SLOTS = sum(1 << n for n in (2, 7, 9, 10, 12, 17, 18, 19))
SUFFIX = ("", " (Polished)", " (Exalted)", " (Ascended)")
FAMILIES = (
    (9607, "Healing", 3501, 11602, 10036),
    (9603, "Magic", 3513, 11622, 10033),
    (9602, "Dodging", 3889, 11602, 10032),
)


def value(v):
    if isinstance(v, str):
        return "CONVERT(X'" + v.encode().hex() + "' USING utf8mb4)"
    return str(int(v))


def insert(table, row):
    cols = ",".join(f"`{k}`" for k in row)
    return f"INSERT INTO {table} ({cols}) VALUES (" + ",".join(map(value, row.values())) + ");"


def scales():
    for base, specialty, effect, _, _ in FAMILIES:
        for tier, suffix in enumerate(SUFFIX):
            name = "Prismatic Scale of " + specialty
            row = dict(id=base + tier * 200000, Name=name + suffix, lore=name, itemclass=0,
                       itemtype=54, slots=SLOTS, classes=65535, races=65535, augtype=64,
                       augrestrict=1, reqlevel=50, magic=1, size=1, norent=1, nodrop=1,
                       nopet=1, icon={"Healing":966,"Magic":959,"Dodging":962}[specialty],
                       ac=(5, 8, 10, 10)[tier], hp=(60, 90, 120, 120)[tier],
                       mana=(60, 90, 120, 120)[tier])
            field = {"Healing":"healamt","Magic":"spelldmg","Dodging":"damageshield"}[specialty]
            row[field] = ((2, 3, 3, 5) if specialty == "Dodging" else (5, 5, 10, 10))[tier]
            if tier == 3:
                if specialty == "Dodging":
                    row.update(worneffect=effect, worntype=2)
                else:
                    row.update(focuseffect=effect, focustype=6)
            yield row


def generate(action):
    stock = json.loads((HERE/"stock.json").read_bytes())
    assert len(stock) == len({r["id"] for r in stock}) == 36
    sql = ["START TRANSACTION;", "CREATE TEMPORARY TABLE aug_guard (ok TINYINT NOT NULL CHECK(ok=1));"]
    def check(expr):
        sql.append(f"INSERT INTO aug_guard VALUES (IF(({expr}),1,0));")
    for row in stock:
        old, new = row["before"], row["after"]
        if action=="rollback":
            old, new = new, old
        key = f"id={row['id']} AND BINARY Name={value(row['name'])} AND itemtype=54 AND augtype=64"
        def matches(vals):
            return " AND ".join(f"{k}={v}" for k,v in zip(STATS,vals,strict=True))
        check(f"SELECT COUNT(*)=1 FROM items WHERE {key} AND (({matches(old)}) OR ({matches(new)})) FOR UPDATE")
        if action!="verify" and old!=new:
            sql.append("UPDATE items SET "+",".join(f"{k}={v}" for k,v in zip(STATS,new,strict=True))+f" WHERE {key} AND {matches(old)};")
        check(f"SELECT COUNT(*)=1 FROM items WHERE {key} AND {matches(new)}")
    for row in scales():
        key=f"id={row['id']}"
        sql.append("CREATE TEMPORARY TABLE aug_expected LIKE items;")
        sql.append(insert("aug_expected",row))
        # Compare all columns, including native defaults, except audit timestamps.
        sql.extend(["SET SESSION group_concat_max_len=131072;",
                    "SELECT GROUP_CONCAT(CONCAT('BINARY i.`',column_name,'` <=> BINARY x.`',column_name,'`') ORDER BY ordinal_position SEPARATOR ' AND ') INTO @cmp FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='items' AND column_name NOT IN ('created','updated','verified');",
                    "SET @stmt=CONCAT('SELECT COUNT(*) INTO @same FROM items i JOIN aug_expected x ON i.id=x.id WHERE ',@cmp);",
                    "PREPARE aug_stmt FROM @stmt; EXECUTE aug_stmt; DEALLOCATE PREPARE aug_stmt;"])
        check(f"SELECT COUNT(*)=@same FROM items WHERE {key} FOR UPDATE")
        if action=="forward":
            sql.append(f"INSERT INTO items SELECT * FROM aug_expected WHERE NOT EXISTS(SELECT 1 FROM items WHERE {key});")
        elif action=="verify":
            check("@same=1")
        else:
            sql.append(f"DELETE FROM items WHERE {key};")
        sql.append("DROP TEMPORARY TABLE aug_expected;")
    for i,(base,specialty,_,scale,gem) in enumerate(FAMILIES):
        rid=96920+i
        row=dict(id=rid,name="Prismatic Scale of "+specialty,tradeskill=68,skillneeded=0,trivial=0,nofail=1,
                 replace_container=0,must_learn=0,quest=0,enabled=1,min_expansion=0,max_expansion=-1)
        cond=" AND ".join(f"`{k}`={value(v)}" for k,v in row.items())
        check(f"SELECT COUNT(*)=0 FROM tradeskill_recipe WHERE (id={rid} OR BINARY name={value(row['name'])}) AND NOT ({cond}) FOR UPDATE")
        if action=="forward":
            sql.append(insert("tradeskill_recipe",row).replace(" VALUES ("," SELECT ")[:-2]+f" WHERE NOT EXISTS(SELECT 1 FROM tradeskill_recipe WHERE id={rid});")
        entries=[(scale,1,0,0),(gem,1,0,0),(base,0,1,0),(17912,0,0,1)]
        where=" OR ".join(f"(item_id={k} AND componentcount={c} AND successcount={n} AND iscontainer={t} AND failcount=0 AND salvagecount=0)" for k,c,n,t in entries)
        check(f"SELECT COUNT(*)=0 FROM tradeskill_recipe_entries WHERE recipe_id={rid} AND NOT ({where}) FOR UPDATE")
        for k,c,n,t in entries:
            sub=f"FROM tradeskill_recipe_entries WHERE recipe_id={rid} AND item_id={k}"
            check(f"SELECT COUNT(*)<=1 {sub} FOR UPDATE")
            if action=="forward":
                sql.append(f"INSERT INTO tradeskill_recipe_entries(recipe_id,item_id,componentcount,successcount,iscontainer) SELECT {rid},{k},{c},{n},{t} WHERE NOT EXISTS(SELECT 1 {sub});")
        if action=="rollback":
            sql.extend([f"DELETE FROM tradeskill_recipe_entries WHERE recipe_id={rid};",f"DELETE FROM tradeskill_recipe WHERE id={rid};"])
        else:
            check(f"SELECT COUNT(*)=1 FROM tradeskill_recipe WHERE {cond}")
            check(f"SELECT COUNT(*)=4 FROM tradeskill_recipe_entries WHERE recipe_id={rid} AND ({where})")
    sql.extend(["COMMIT;","DROP TEMPORARY TABLE aug_guard;"])
    return "\n".join(sql)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("forward","verify","rollback"))
    print(generate(cli.parse_args().action))
