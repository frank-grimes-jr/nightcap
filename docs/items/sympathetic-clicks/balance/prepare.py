"""Prepare only the RAM-backed, task-owned MariaDB fixture and diagnostic directory."""
import gzip
import hashlib
import importlib.util
import json
import secrets
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DB = "nightcap_sympathetic_balance"
HOST = "nightcap-sympathetic-balance"
USER = "sympathetic_fixture"
SERVER = "akk-stack-eqemu-server-1"
R = "/tmp/nightcap-balance-sympathetic"
PRIOR = "/tmp/nightcap-balance-raid-augs-20261112"
BASE_SHA = "90679bea5517eaa7928876f8dc7c4f5fc9cd8494dc286479245735c6101c08a6"


def sql(statement):
    proc = subprocess.run(["docker", "exec", "-i", HOST, "mariadb", "--protocol=socket",
                           "-uroot", "--batch", "--raw", "-N", DB], input=statement.encode(),
                          capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode(errors="replace")[-400:])
    return proc.stdout.decode()


def main(backup, source):
    state = json.loads(subprocess.check_output(["docker", "inspect", HOST]))[0]
    assert state["Config"]["Labels"]["nightcap.fixture"] == "sympathetic-classic"
    assert "/var/lib/mysql" in state["HostConfig"]["Tmpfs"]
    assert not state["HostConfig"]["PortBindings"]
    assert hashlib.file_digest(backup.open("rb"), "sha256").hexdigest() == BASE_SHA
    prior = ROOT / "docs/items/classic-raid-augments/balance/prepare_fixture.py"
    spec = importlib.util.spec_from_file_location("synthetic_public_fixture", prior)
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    loader.DB, loader.MYSQL = DB, HOST
    loader.prepare(backup, source)
    content = ROOT / "docs/quests/camil-chapterhouse/balance-public-content.json.gz"
    for table, data in json.loads(gzip.decompress(content.read_bytes()))["tables"].items():
        if table == "items":
            continue
        columns = ",".join("`" + column + "`" for column in data["columns"])
        sql("DELETE FROM `" + table + "`")
        for start in range(0, len(data["rows"]), 500):
            def literal(value):
                return "NULL" if value is None else "'" + str(value).replace("'", "''") + "'"
            tuples = ["(" + ",".join(map(literal, row)) + ")" for row in data["rows"][start:start + 500]]
            sql("SET SESSION sql_mode='NO_BACKSLASH_ESCAPES'; INSERT INTO `" + table +
                "` (" + columns + ") VALUES " + ",".join(tuples))
    sql("DELETE FROM npc_spells_entries WHERE spellid IN (982,2859)")
    sql("INSERT INTO character_multiclass (character_id,class2,class3) VALUES (97102,2,12)")
    assert sql("SELECT COUNT(*) FROM account; SELECT COUNT(*) FROM character_data").splitlines() == ["0","0"]
    password = secrets.token_hex(30)
    sql(f"CREATE USER '{USER}'@'%' IDENTIFIED BY '{password}'; GRANT ALL ON {DB}.* TO '{USER}'@'%'")
    config = {"server": {"world": {"shortname": "sympathetic", "longname": "Isolated click test",
                          "tcp": {"ip": "127.0.0.1", "port": "1"}}, "auto_database_updates": "false",
                         "database": {"host": HOST, "port": "3306", "db": DB, "username": USER,
                                      "password": password},
                         "directories": {"quests": "quests", "plugins": "plugins", "lua_modules": "lua_modules",
                                         "logs": "logs", "maps": "maps", "shared_memory": "shared/",
                                         "patches": "/home/eqemu/server", "opcodes": "/home/eqemu/server"}}}
    init = """from pathlib import Path
import os,sys
r,prior=map(Path,sys.argv[1:])
r.mkdir(exist_ok=True)
for name in ('logs','quests','plugins','lua_modules','shared'):
    (r/name).mkdir(exist_ok=True)
if not (r/'maps').exists():
    (r/'maps').symlink_to(prior/'maps',target_is_directory=True)
os.umask(0o077)
(r/'eqemu_config.json').write_bytes(sys.stdin.buffer.read())
"""
    subprocess.run(["docker","exec","-i",SERVER,"python3","-c",init,R,PRIOR],
                   input=json.dumps(config).encode(),check=True)
    print(sql("SELECT id,name,level,hp,mindmg,maxdmg FROM npc_types WHERE id IN (32040,73057)"))

def candidate():
    assert sql("SELECT DATABASE()").strip()==DB
    assert sql("SELECT COUNT(*) FROM account; SELECT COUNT(*) FROM character_data").splitlines()==["0","0"]
    # Give every parallel seed an independent synthetic character, timers, and AA keys.
    rows=[(97102+100*i,2,12) for i in range(5)]+[(97104+100*i,11,10) for i in range(5)]
    sql("INSERT INTO character_multiclass (character_id,class2,class3) VALUES "+
        ",".join(str(row) for row in rows)+" ON DUPLICATE KEY UPDATE class2=VALUES(class2),class3=VALUES(class3)")
    sql((ROOT/"eq-solo-gm/scripts/sympathetic-clicks.sql").read_text())
    print(sql("SELECT id,name,clickeffect FROM items WHERE id IN (610338,610150); "
              "SELECT id,name,buffduration FROM spells_new WHERE id IN (44379,44380)"))
    subprocess.run(["docker","exec","-w",R,SERVER,
                    "/tmp/nightcap-classic-raid-augs-105a250f/build/bin/shared_memory"],check=True)


if __name__ == "__main__":
    if sys.argv[1:]==["candidate"]:candidate()
    else:main(*map(Path,sys.argv[1:]))
