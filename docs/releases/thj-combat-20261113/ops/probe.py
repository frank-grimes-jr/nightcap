"""Read the running services and native identities before a zone-only change."""
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from capture_lantern_content import SSH

PREVIOUS = "sympathetic-clicks-20261113-v1"
STAGE = "thj-combat-20261113-v1"
ARTIFACTS = ROOT / "artifacts/thj-combat-prod"
LOAD = """
from pathlib import Path
import json, sys, shutil
parent = Path('/opt/nightcap/releases/sympathetic-clicks-20261113-v1')
sys.path.insert(0, str(parent))
import release as prior
prior.initialize()
"""


def remote(code, timeout=600):
    result = subprocess.run(SSH, input=code, text=True, encoding="utf8",
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2400:])
    return result.stdout


def write(name, data):
    (HERE / name).write_bytes((json.dumps(data, indent=2) + "\n").encode())


def before():
    receipt = json.loads(remote(LOAD + """
dep = prior.read(prior.ACTIVE/'deployed.json')
services = {n:prior.r.compact(n) for n in prior.SERVICES}
assert dep['gateway_open'] and services['gateway']['running']
assert dep['image']==services['game']['image_id']
native = prior.r.running(dep['image'], prior.binaries(True))
assert native['restart_count']==0 and native['started_at']==dep['runtime']['started_at']
assert prior.h.caches()=={k:v['after'] for k,v in dep['cache'].items()}
assert prior.sha(prior.ROOT/'data/public/channel.json')==dep['client_channel_sha256']
prior.base.health()
print(json.dumps(dict(services=services,players=prior.a.prior.players(),
    base_hashes=prior.r.image_hashes(dep['image']),free=shutil.disk_usage(prior.ROOT).free,
    channel=dep['client_channel_sha256'],public_wiki=str((prior.ROOT/'data/public/wiki/current').readlink()),
    caches=prior.h.caches(),prior_operator=prior.sha(parent/'release.py'),
    prior_receipt=prior.sha(prior.ACTIVE/'deployed.json'),
    combat_rule_overrides=prior.sql("SELECT ruleset_id, rule_name, rule_value FROM rule_values WHERE rule_name IN ('Combat:ArcheryBonusLevelRequirement','Combat:ArcheryBonusRequiresStationary','Character:HeroicDexterityMultiplier','Character:HeroicDexterityMultiplierArchery') ORDER BY rule_name,ruleset_id").splitlines(),
    workers=sum(row[0]=='zone' for row in native['processes']),errors=native['errors'])))
"""))
    old = json.loads((ROOT / "docs/releases/sympathetic-clicks-20261113/ops/production-verified.json").read_bytes())
    assert receipt["base_hashes"]["bin/zone"] == old["binaries"]["zone"]
    assert receipt["services"]["game"]["image_id"] == old["image"] and receipt["workers"] == 12
    write("production-before.json", receipt)
    print(json.dumps({k: receipt[k] for k in ("workers","errors","players","free","public_wiki")}))


if __name__ == "__main__":
    before()
