"""Deploy only the reviewed zone and the Cairnwright name on the production QA world."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

root = Path("/opt/nightcap/deploy/production")
stage = Path(__file__).resolve().parent
base = "sha256:e5e3a8b8f294d15d9b5dd6d99da9e603f086368a82bf90d4a82dd3e5eec32e84"
parent_zone = "771122fc9f8b208eb9338f82df3c614288582a8ae9f5bd19ed7ed4c1b5665989"
world = "a641bef73c39fcc37192685bb077f1f5e9acf77dd4d79e7998ae899912eff521"
tag = "nightcap-game:hailstone-preview-20261122"
quest = root / "data/server/quests/global/global_player.lua"

def run(*args, data=None):
    return subprocess.check_output(args, input=data, cwd=root).decode().strip()

def compose(*args, data=None):
    return run("docker","compose",*args,data=data)

def image():
    return run("docker","inspect","--format","{{.Image}}",compose("ps","-q","game"))

def binary(name):
    return compose("exec","-T","game","sha256sum","/opt/nightcap/bin/"+name).split()[0]

def players():
    return json.loads(compose("exec","-T","game","python3","-",data=(stage/"world_count.py").read_bytes()))

def replace(path, data):
    stat = path.stat()
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as out:
        out.write(data)
        os.fchown(out.fileno(),stat.st_uid,stat.st_gid)
        os.fchmod(out.fileno(),stat.st_mode & 0o777)
        out.flush()
        os.fsync(out.fileno())
    os.replace(out.name,path)

def prepare(pin):
    assert image()==base and binary("zone")==parent_zone and binary("world")==world
    with (stage/"zone").open("rb") as f: assert hashlib.file_digest(f,"sha256").hexdigest()==pin
    (stage/"Dockerfile").write_text("FROM nightcap-game:cairnwright-testing-20261121\nCOPY --chmod=0755 zone /opt/nightcap/bin/zone\n")
    (stage/".dockerignore").write_text("*\n!Dockerfile\n!zone\n")
    assert run("docker","image","inspect","--format","{{.Id}}","nightcap-game:cairnwright-testing-20261121")==base
    run("docker","build","--network","none","--pull=false","-t",tag,str(stage))
    assert run("docker","run","--rm","--network","none","--entrypoint","sha256sum",tag,"/opt/nightcap/bin/zone").split()[0]==pin

def activate(pin):
    assert image()==base and binary("zone")==parent_zone and players()==0
    env = root/".env"
    old_env, old_lua = env.read_bytes(),quest.read_bytes()
    assert b'"Berserker"}' in old_lua
    pat = rb'(?m)^NIGHTCAP_GAME_IMAGE=nightcap-game:cairnwright-testing-20261121\r?$'
    new_env, n = re.subn(pat,b"NIGHTCAP_GAME_IMAGE="+tag.encode(),old_env)
    old_line = next(line for line in old_lua.splitlines() if line.startswith(b"local CLASS_NAMES = "))
    assert n==1 and old_line.endswith(b'"Berserker"}')
    new_lua = old_lua.replace(old_line,old_line[:-1]+b',"Cairnwright"}',1)
    assert run("docker","run","--rm","--network","none","--entrypoint","sha256sum",tag,"/opt/nightcap/bin/zone").split()[0]==pin
    (stage/"before-global_player.lua").write_bytes(old_lua)
    try:
        compose("stop","gateway")
        assert players()==0
        compose("stop","-t","90","game")
        replace(env,new_env)
        replace(quest,new_lua)
        compose("up","-d","--no-deps","--wait","--wait-timeout","300","game")
        assert binary("world")==world and binary("zone")==pin and players()==0
    except BaseException:
        replace(env,old_env)
        replace(quest,old_lua)
        compose("up","-d","--no-deps","--wait","--wait-timeout","300","game")
        raise
    finally:
        compose("up","-d","--no-deps","--wait","--wait-timeout","90","gateway")
    print(json.dumps({"world":binary("world"),"zone":binary("zone"),"image":image(),"players":players()}))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["prepare","activate"])
    p.add_argument("zone_sha")
    a=p.parse_args()
    assert re.fullmatch("[a-f0-9]{64}",a.zone_sha)
    with (root/".deployment.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        (prepare if a.mode=="prepare" else activate)(a.zone_sha)
