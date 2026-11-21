"""Run against a NEW throwaway MariaDB container on the local akk-stack network.

The target must have database/user cairnwright_qa and MYSQL_PASSWORD in its
environment. The source container is read only. Copy no player or account rows.
"""
import argparse
import json
from pathlib import Path
import subprocess

DB = "nightcap-cairnwright-qa-20261121"
SERVER = "akk-stack-eqemu-server-1"
ROOT = Path(__file__).resolve().parents[3]
TABLES = ("account character_data character_currency character_bind character_material "
          "character_languages character_skills character_leadership_abilities inventory name_filter "
          "char_create_combinations char_create_point_allocations start_zones starting_items "
          "items skill_caps zone variables").split()

def docker(*args, data=None):
    return subprocess.run(["docker", *args], input=data, stdout=subprocess.PIPE,check=True).stdout

def target(sql):
    return docker("exec","-i", DB, "sh", "-c",
                  'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -u cairnwright_qa -NB cairnwright_qa',data=sql)

def local_content_dump():
    local_dump = """import json, os, sys
with open('/home/eqemu/server/eqemu_config.json') as file:
    db = json.load(file)['server']['database']
assert (db['host'],db['db']) == ('mariadb','peq')
os.environ['MYSQL_PWD'] = db['password']
os.execvp('mysqldump',['mysqldump','-h','mariadb','-u',db['username'],*sys.argv[1:]])
"""
    return ["exec",SERVER,"python3","-c",local_dump,
          "--skip-triggers","--skip-comments","--skip-add-drop-table","--skip-lock-tables"]

def seed():
    assert target(b"SELECT DATABASE(); SHOW TABLES;").strip()==b"cairnwright_qa", "fixture must start empty"
    # Schema only for the account and player tables. Local dev public content is
    # copied with explicit predicates. The unique test name is reserved by world.
    dump = local_content_dump()
    target(docker(*dump,"--no-data","peq",*TABLES))
    for table, predicate in {
        "zone":"zoneidnumber IN (22,67)",
        "items":"id IN (6014,1060)",
        "char_create_combinations":"race=8 AND class=3 AND expansions_req=0",
        "char_create_point_allocations":"id=14",
        "start_zones":"player_race=8 AND player_class=3 AND player_deity=202 AND zone_id=22",
    }.items():
        target(docker(*dump,"--no-create-info","--where="+predicate,"peq",table))
    for file in ("cairnwright_starter_items.sql","cairnwright_creation.sql"):
        target((ROOT/"server-mods/sql"/file).read_bytes())

def run(work, mode):
    assert work.startswith("/tmp/cairnwright-") and ".." not in work
    directory=work+"/storage-qa"
    docker("exec",SERVER,"mkdir","-p",directory+"/shared")
    config=json.dumps({"server":{"world":{"shortname":"cairnqa","longname":"Cairnwright QA"},
                                 "directories":{"shared_memory":"shared/"},"auto_database_updates":"false"}}).encode()
    docker("exec","-i","-w",directory,SERVER,"sh","-c","cat > eqemu_config.json",data=config)
    # Pass only the new fixture credential to the matching process via stdin.
    credential=docker("exec",DB,"printenv","MYSQL_PASSWORD")
    output=docker("exec","-i","-w",directory,SERVER,work+"/world-candidate/world-storage-qa",mode,data=credential)
    print(output.decode(errors="replace")[-550:])

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("work",help="dedicated local Docker build directory")
    p.add_argument("action", choices=["seed","create","list"])
    args=p.parse_args()
    if args.action=="seed": seed()
    else: run(args.work,args.action)
