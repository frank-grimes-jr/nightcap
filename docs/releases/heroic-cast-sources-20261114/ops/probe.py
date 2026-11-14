"""Authenticate the actual game, content caches, client, admission and heroic rules."""
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREVIOUS = "thj-combat-20261113-v1"
STAGE = "heroic-cast-sources-20261114-v1"
ARTIFACTS = ROOT / "artifacts/heroic-cast-sources"
sys.path.insert(0, str(ROOT / "tools"))
from capture_lantern_content import SSH

LOAD = """
from pathlib import Path
import json, shutil, sys
parent = Path('/opt/nightcap/releases/thj-combat-20261113-v1')
sys.path.insert(0, str(parent))
import release as combat
combat.initialize()
prior = combat.prior
"""


def write(name, data):
    (HERE / name).write_bytes((json.dumps(data, indent=2) + "\n").encode())


def remote(code, timeout=900):
    result = subprocess.run(SSH, input=code, capture_output=True, text=True, encoding="utf8", timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-1800:])
    return result.stdout


def production():
    source = LOAD + """
dep = combat.read(combat.ACTIVE / 'deployed.json')
services = {n:combat.r.compact(n) for n in prior.SERVICES}
assert all(s['running'] for s in services.values()) and dep['gateway_open']
assert dep['image'] == services['game']['image_id']
native = combat.r.running(dep['image'],combat.p.binaries())
assert native['restart_count'] == 0 and native['started_at'] == dep['runtime']['started_at']
assert not any(native['errors'].values())
assert combat.sha(combat.ROOT/'data/public/channel.json') == dep['client_channel_sha256']
prior.base.health()
rules = prior.sql("SELECT ruleset_id, rule_name, rule_value FROM rule_values WHERE rule_name IN ('Spells:NightcapHeroicSpellScaling','Spells:NightcapTHJDamageScaling','Spells:NightcapTHJBehaviors','Character:HeroicIntelligenceIncreaseSpellDmgMultiplier','Character:HeroicWisdomIncreaseHealAmtMultiplier') ORDER BY rule_name,ruleset_id").splitlines()
print(json.dumps(dict(services=services,players=combat.p.a.prior.players(),rules=rules,
    base_hashes=combat.r.image_hashes(dep['image']),free=shutil.disk_usage(combat.ROOT).free,
    channel=dep['client_channel_sha256'],public_wiki=str((combat.ROOT/'data/public/wiki/current').readlink()),
    caches=combat.p.h.caches(),prior_operator=combat.sha(parent/'release.py'),
    prior_receipt=combat.sha(combat.ACTIVE/'deployed.json'),
    workers=sum(row[0]=='zone' for row in native['processes']),errors=native['errors'])))
"""
    got = json.loads(remote(source))
    old = json.loads((ROOT/"docs/releases/thj-combat-20261113/ops/production-verified.json").read_bytes())
    assert got["services"]["game"]["image_id"] == old["image"] and got["workers"] == 12
    assert got["base_hashes"]["bin/zone"] == old["binaries"]["zone"] and got["caches"] == old["caches"]
    assert got["prior_receipt"] == old["deployed_receipt"] and old["client_channel_sha256"] == got["channel"]
    write("production-before.json", got)
    print(json.dumps({k:got[k] for k in ("workers","players","rules","public_wiki","free")}))


def local():
    sys.path.insert(0,str(ROOT / "docs/items/sympathetic-clicks/runtime"))
    import activate_local
    state = activate_local.state("state")
    old = json.loads((ROOT/"docs/releases/thj-combat-20261113/ops/local-combined-verified.json").read_bytes())
    assert state["hashes"] == old["hashes"] and state["services"] == old["services"] and not state["locked"]
    rows = activate_local.sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name='Spells:NightcapHeroicSpellScaling';").decode().splitlines()
    write("local-before.json", dict(**state, heroic_rule_rows=rows))
    print("local zone",state["hashes"]["zone"],"players",state["players"],"heroic rule",rows)


if __name__ == "__main__":
    {"production":production, "local":local}[sys.argv[1]]()
