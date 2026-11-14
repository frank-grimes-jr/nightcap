"""Swap the verified zone on the owner-local TEST stack, retaining the old executable."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0,str(ROOT / "docs/items/sympathetic-clicks/runtime"))
import activate_local as driver

STAGE = "/tmp/nightcap-thj-combat-20261113/local/"
ORIGINAL = "fa821145a3389e9f5f61d24f7699d32b7103c6a0d08f1318e5fd6c2fdfda7f33"
ART = ROOT / "artifacts/thj-combat-prod"


def write(path, value):
    path.write_bytes((json.dumps(value,indent=2)+"\n").encode())


def stopped():
    script = "import sys;sys.path.insert(0,sys.argv[1]);from local_state import processes;print(len(processes()))"
    return driver.inside("python3","-c",script,driver.R).strip() == b"0"


def backup(phase):
    path = "/tmp/thj-combat-20261113-before-" + phase + ".sql.gz"
    code = """
set -euo pipefail
umask 077
test ! -e "$1"
export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
mariadb-dump -uroot --single-transaction --quick --hex-blob --routines --events peq | gzip -1 > "$1"
gzip -t "$1"
sha256sum "$1"
"""
    digest, saved = driver.run("docker","exec",driver.DB,"bash","-c",code,"backup",path,timeout=900).decode().split()
    assert saved == path and len(digest) == 64
    return {"sha256":digest,"gzip_integrity":True}


def finish_stop():
    # Spire may terminate its Python caller before the suspended launcher gets
    # SIGCONT. All game workers must already have exited and the logged world
    # must have fully flushed before finishing this one supervisor transition.
    code = """
import os,signal,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from local_state import processes,S
logs=sorted((S/'logs').glob('world_*.log'),key=lambda p:p.stat().st_mtime,reverse=True)
assert logs and time.time()-logs[0].stat().st_mtime < 1800
tail=logs[0].read_text(errors='replace')[-80000:]
assert 'World main loop completed' in tail and 'total zone_count [0]' in tail and 'Caught signal [15]' in tail
p=processes()
if p:
    assert set(p)=={'spire-launcher'} and len(p['spire-launcher'])==1
    proc,=p['spire-launcher']
    assert (proc/'exe').resolve() in (S/'bin/spire',Path('/tmp/spire-launcher'))
    assert (proc/'status').read_text().split('State:',1)[1].lstrip().startswith('T')
    os.kill(int(proc.name),signal.SIGTERM)
    os.kill(int(proc.name),signal.SIGCONT)
    for _ in range(40):
        if not processes(): break
        time.sleep(0.25)
    else: raise RuntimeError('Launcher still running')
"""
    driver.inside("python3","-c",code,driver.R)
    assert stopped()


def local_install(phase, resume_stop):
    ART.mkdir(parents=True,exist_ok=True)
    receipt = HERE / ("local-" + phase + "-verified.json")
    assert not receipt.exists(), "Phase already completed"
    build = json.loads(driver.inside("cat",STAGE+phase+"/build.json"))
    old = ORIGINAL if phase == "bow" else json.loads((HERE/"local-bow-verified.json").read_bytes())["hashes"]["zone"]
    assert build["profile"] == "local" and build["baseline"] == ORIGINAL and build["zone"] != old
    before = ART / ("local-"+phase+"-before.json")
    if resume_stop:
        loaded = json.loads(before.read_bytes())
        assert not (ART / ("local-"+phase+"-backup.json")).exists()
        assert driver.inside("sha256sum",driver.S+"/bin/zone").decode().split()[0] == old
        finish_stop()
    else:
        assert not before.exists(), "Inspect existing maintenance receipts"
        loaded = driver.state("state")
        assert loaded["hashes"]["zone"] == old and loaded["players"] == 0 and not loaded["locked"]
        write(before,loaded)
        try:
            driver.stop()
        except (RuntimeError,subprocess.TimeoutExpired):
            finish_stop()
    assert loaded["hashes"]["zone"] == old and loaded["players"] == 0 and not loaded["locked"]
    assert stopped()
    try:
        saved = backup(phase)
        write(ART / ("local-"+phase+"-backup.json"),saved)
        swap = """
import sys,shutil,os
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from local_state import BIN,target,sha,processes
folder,old,new=Path(sys.argv[2]),sys.argv[3],sys.argv[4]
assert not processes() and target('zone').resolve()==BIN and sha(BIN)==old and sha(folder/'zone')==new
retained=folder/'previous-zone'
assert not retained.exists()
shutil.copy2(BIN,retained)
assert sha(retained)==old
candidate=BIN.with_name('zone.thj-combat.next')
assert not candidate.exists()
shutil.copy2(folder/'zone',candidate)
assert sha(candidate)==new
os.replace(candidate,BIN)
"""
        driver.inside("python3","-c",swap,driver.R,STAGE+phase,old,build["zone"],timeout=450)
    except BaseException:
        if stopped() and driver.inside("sha256sum",driver.S+"/bin/zone",timeout=180).decode().split()[0] == old:
            driver.start()
        raise
    driver.start()
    for i in range(80):
        try:
            now = driver.state("state")
            assert not now["locked"] and now["hashes"] == {**loaded["hashes"],"zone":build["zone"]}
            assert now["services"] == loaded["services"]
        except (RuntimeError,AssertionError,subprocess.TimeoutExpired):
            if i == 79:
                raise
            time.sleep(5)
            continue
        write(receipt,{**now,"old_zone":old,"backup":saved,"owner_gameplay_accepted":False})
        print(json.dumps(now),flush=True)
        return


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=("bow","combined"))
    parser.add_argument("--resume-stop",action="store_true")
    args=parser.parse_args()
    local_install(args.phase,args.resume_stop)
