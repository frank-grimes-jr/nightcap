"""Compile changed native units and rehearse the generated SQL in isolated local fixtures."""
import argparse
import concurrent.futures
import io
from pathlib import Path
import shlex
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
SERVER = "akk-stack-eqemu-server-1"
MARIA = "akk-stack-mariadb-1"
UNITS = ("common/item_instance.cpp", "common/patches/rof2.cpp", "world/worlddb.cpp",
         "zone/inventory.cpp", "zone/advanced_loot_inventory.cpp", "zone/trading.cpp",
         "zone/zone_hunt.cpp", "zone/attack.cpp", "zone/zone.cpp", "zone/client_packet.cpp")


def native():
    stage = "/tmp/ornament-build-" + uuid.uuid4().hex
    def shell(cmd, data=None):
        return subprocess.run(["docker", "exec", "-i", SERVER, "sh", "-ec", cmd],
                              input=data, check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    shell(f"mkdir {stage}; cd {stage}; for d in common world zone; do cp -as /home/eqemu/code/$d $d; done; ln -s /home/eqemu/code/libs libs; ln -s /home/eqemu/code/submodules submodules")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as archive:
        for path in (ROOT / "server-mods/code").rglob("*"):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(ROOT / "server-mods/code").as_posix())
    shell(f"cd {stage}; tar --unlink-first -xzf -", buf.getvalue())
    def compile_unit(unit):
        component = unit.split("/")[0]
        flags = shell(f"cat /home/eqemu/code/build/{component}/CMakeFiles/{component}.dir/flags.make")
        options = []
        for line in flags.splitlines():
            if line.startswith(("CXX_DEFINES =", "CXX_INCLUDES =", "CXX_FLAGS =")):
                options.extend(shlex.split(line.split("=", 1)[1]))
        if component == "zone":
            options.extend(["-include", stage + "/common/pch/app-pch.h", "-include", stage + "/common/pch/std-pch.h",
                            "-include", stage + "/zone/pch/pch.h"])
        cmd = shlex.join(["clang++", "-I" + stage, *options, "-c", stage + "/" + unit, "-o", stage + "/" + unit.replace("/", "_") + ".o"])
        shell(cmd)
        print("Compiled", unit, flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(compile_unit, UNITS))


def database(plan):
    db = "ornament_qa_" + uuid.uuid4().hex[:12]
    def sql(statement, schema=""):
        return subprocess.run(["docker", "exec", "-i", MARIA, "sh", "-ec",
                    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot --batch --skip-column-names ' + schema],
                    input=statement, check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    sql(f"CREATE DATABASE {db}".encode())
    try:
        setup = []
        for table, condition in (
                ("items", "1"),
                ("npc_types", "id=998946 OR name='Epic_Forgemaster'"),
                ("spawngroup", "name='nightcap_ornament_artisan' OR id IN (SELECT spawngroupID FROM peq.spawnentry WHERE npcID IN (SELECT id FROM npc_types))"),
                ("spawnentry", "npcID IN (SELECT id FROM npc_types)"),
                ("spawn2", "spawngroupID IN (SELECT id FROM spawngroup)")):
            setup += [f"CREATE TABLE {table} LIKE peq.{table}",
                      f"INSERT INTO {table} SELECT * FROM peq.{table} WHERE {condition}"]
        sql((";\n".join(setup) + ";").encode(), db)
        query = b"""SELECT COUNT(*),COALESCE(SUM(id),0) FROM nightcap_ornament_design WHERE active=1;
SELECT COUNT(*) FROM nightcap_ornament_source;
SELECT COUNT(*) FROM items WHERE lore='Nightcap appearance ornament' AND
(itemtype!=54 OR augtype NOT IN (524288,1048576) OR hp OR mana OR ac OR damage OR haste OR healamt OR spelldmg
OR clickeffect>0 OR proceffect>0 OR worneffect>0 OR focuseffect>0 OR bardeffect>0 OR scrolleffect>0);
SELECT COUNT(*) FROM spawn2 s JOIN spawnentry e ON e.spawngroupID=s.spawngroupID WHERE e.npcID=998946 AND s.zone='ecommons';"""
        data = plan.read_bytes()
        results = []
        for _ in range(2):
            sql(data, db)
            results.append(sql(query, db))
        assert results[0] == results[1], results
        lines = results[0].splitlines()
        assert int(lines[0].split()[0]) > 0 and int(lines[1]) > 0 and lines[2:] == ["0","1"], results
        first = int(sql(b"SELECT MIN(id) FROM nightcap_ornament_design", db))
        sql(f"UPDATE items SET hp=1 WHERE id={first}".encode(), db)
        try:
            sql(data, db)
        except subprocess.CalledProcessError:
            assert sql(query, db).splitlines()[2] == "1"
        else:
            raise AssertionError("A modified ornament gained stats without blocking reinstall")
        print(results[0], flush=True)
    finally:
        sql(f"DROP DATABASE {db}".encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--sql", type=Path)
    args = parser.parse_args()
    if args.native:
        native()
    if args.sql:
        database(args.sql)
