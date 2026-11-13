"""One-shot operator for the reviewed local TEST stack. No remote target option."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ART = Path("E:/EQ_Local_Dev/artifacts/sympathetic-classic-test-20261113")
GAME = "akk-stack-eqemu-server-1"
DB = "akk-stack-mariadb-1"
R = "/tmp/nightcap-sympathetic-local-test-20261113"
S = "/home/eqemu/server"
CONTROL = "/tmp/nightcap-stock-worn-atk-20261113/local_world.py"


def run(*args, data=None, timeout=180):
    result = subprocess.run(args, input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-600:])
    return result.stdout


def inside(*args, timeout=180):
    return run("docker", "exec", GAME, *args, timeout=timeout)


def state(mode):
    return json.loads(inside("python3", R + "/local_state.py", mode, timeout=450))


def control(action):
    return json.loads(inside("python3", CONTROL, action))


def sql(statement):
    cmd = 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot --default-character-set=utf8mb4 -NBr peq'
    return run("docker", "exec", "-i", DB, "sh", "-c", cmd, data=statement.encode())


def stop():
    # Preserve the eight workers' saved state. Suspend the identified launcher
    # while each worker exits, then use Spire's own stop command for its services.
    check = state("state")
    assert check["players"] == 0 and not check["locked"]
    control("lock")
    assert control("status") is True
    if control("count") != 0:
        control("unlock")
        raise RuntimeError("A player entered while acquiring the local admission hold")
    script = """
import os, pathlib, signal, subprocess, sys, time
sys.path.insert(0, sys.argv[1])
from local_state import processes, S, BIN
p = processes()
launcher, = p['spire-launcher']
identity = (launcher/'exe').resolve()
assert identity in (S/'bin/spire', pathlib.Path('/tmp/spire-launcher'))
assert all((z/'exe').resolve() == BIN for z in p['zone']) and len(p['zone']) == 8
def send(proc, path, sig):
    assert (proc/'exe').resolve() == path
    os.kill(int(proc.name), sig)
send(launcher, identity, signal.SIGSTOP)
try:
    for z in p['zone']:
        send(z, BIN, signal.SIGTERM)
    for _ in range(90):
        if 'zone' not in processes(): break
        time.sleep(1)
    else: raise RuntimeError('Zones still saving')
    # Spire terminates the launcher's process group; isolate this control child.
    subprocess.run([S/'bin/spire', 'eqemu-server:launcher', 'stop'], cwd=S, start_new_session=True, timeout=65)
finally:
    if (launcher/'exe').is_file() and (launcher/'exe').resolve() == identity:
        send(launcher, identity, signal.SIGCONT)
for _ in range(45):
    if not processes(): break
    time.sleep(1)
else: raise RuntimeError('Local game has still-running children')
"""
    inside("python3", "-c", script, R, timeout=225)


def save(name, result):
    (ART / name).write_text(json.dumps(result, indent=2) + "\n")


def start():
    run("docker", "exec", "-d", "-w", S, GAME, "./bin/spire", "eqemu-server:launcher", "start")


def backup(disabling=False):
    command = """
set -euo pipefail
umask 077
file="$1"
test ! -e "$file"
export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
mariadb-dump -uroot --single-transaction --quick --hex-blob --routines --events peq | gzip -1 > "$file"
gzip -t "$file"
sha256sum "$file"
"""
    suffix = "before-disable" if disabling else "before"
    path = f"/tmp/sympathetic-local-test-20261113-peq-{suffix}.sql.gz"
    return run("docker", "exec", DB, "bash", "-c", command, "backup", path, timeout=480).decode().strip()


def preflight():
    receipt = json.loads((HERE.parent / "content/rehearsal.json").read_bytes())
    migration = (ROOT / "eq-solo-gm/scripts/sympathetic-clicks.sql").read_bytes()
    assert receipt["status"] == "passed" and receipt["sql_sha256"] == hashlib.sha256(migration).hexdigest()
    expected = json.loads((ART / "local-before.json").read_bytes())
    assert state("state") == expected
    assert sql("SELECT COUNT(*) FROM spells_new WHERE id IN (44379,44380); "
               "SELECT COUNT(*) FROM db_str WHERE id IN (44379,44380) AND type=6; "
               "SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Expansion:CurrentExpansion'; "
               "SELECT COUNT(*) FROM variables WHERE varname='hotfix_name' AND value<>'';").splitlines() == [b"0",b"0",b"0",b"0"]
    assert inside("test", "-x", R + "/candidate/zone") == b""
    return migration


def main():
    if sys.argv[1:] == ["disable-after-review"]:
        assert (ART / "verified.json").is_file() and not (ART / "disabled.json").exists()
        verified = state("verify")
        assert verified["players"] == 0 and not verified["locked"]
        stop()
        save("disable-backup.json", {"sha256sum": backup(disabling=True)})
        sql((HERE.parent / "content/disable.sql").read_text())
        receipt = state("disable")
        start()
        for i in range(72):
            try:
                restored = state("state")
                assert not restored["locked"] and all(restored["hashes"][k] == v for k,v in receipt.items())
            except (RuntimeError, subprocess.TimeoutExpired):
                if i == 71:
                    raise
                time.sleep(5)
                continue
            save("disabled.json", restored)
            return
    assert sys.argv[1:] in (["install-after-review"], ["resume-verified-stop"])
    assert not any((ART / n).exists() for n in ("stopped.json", "db-backup.json", "installed-cache.json", "verified.json"))
    if sys.argv[1:] == ["resume-verified-stop"]:
        recovery = """
import sys
sys.path.insert(0, sys.argv[1])
from local_state import *
assert not processes() and all(sha(target(k)) == v for k,v in KNOWN.items())
log = (S/'logs/world_8775.log').read_text()
assert 'total zone_count [0]' in log and 'World main loop completed' in log and 'Caught signal [15]' in log
"""
        inside("python3", "-c", recovery, R)
        migration = (ROOT / "eq-solo-gm/scripts/sympathetic-clicks.sql").read_bytes()
        assert hashlib.sha256(migration).hexdigest() == json.loads((HERE.parent / "content/rehearsal.json").read_bytes())["sql_sha256"]
        assert sql("SELECT COUNT(*) FROM spells_new WHERE id IN (44379,44380);").strip() == b"0"
    else:
        migration = preflight()
        stop()
    save("stopped.json", {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "zones_saved": 8})
    save("db-backup.json", {"sha256sum": backup()})
    sql(migration.decode())
    expected = [b"610150\t44380\t4\t2000\t-1\t2349", b"610338\t44379\t4\t2000\t-1\t-1"]
    assert sql("SELECT id,clickeffect,clicktype,casttime,maxcharges,focuseffect FROM items "
               "WHERE id IN (610150,610338) ORDER BY id;").splitlines() == expected
    save("installed-cache.json", state("install"))
    start()
    for i in range(72):
        try:
            verified = state("verify")
        except (RuntimeError, subprocess.TimeoutExpired):
            if i == 71:
                raise
            time.sleep(5)
            continue
        save("verified.json", verified)
        print(json.dumps(verified), flush=True)
        return


if __name__ == "__main__":
    main()
