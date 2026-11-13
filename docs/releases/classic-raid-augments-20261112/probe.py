"""Capture only the live identities and public-content preimages needed for this release."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from capture_lantern_content import SSH

REMOTE = """
import hashlib, importlib.util, json, shutil
from pathlib import Path
prior = Path('/opt/nightcap/releases/dot-no-initial-damage-20261112-v2/rollout.py')
spec = importlib.util.spec_from_file_location('dot_operator', prior)
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)
p = op.initialize()
game = p.r.compact('game')
released = Path('/opt/nightcap/releases/inventory-combat-stats-20261112-v1/evidence/activation/paired-deployed.json')
assert released.is_file() and json.loads(released.read_text())['gateway_open'], 'Predecessor opening verification is still running'
report = dict(services={k:p.r.compact(k) for k in ('game','gateway','db','web','tunnel')}, base_hashes=p.r.image_hashes(game['image_id']), players=p.a.prior.players(), free=shutil.disk_usage(p.ROOT).free, prior_sha256=p.sha(prior), client_channel_sha256=p.sha(p.ROOT/'data/public/channel.json'), caches=p.h.caches(), public_wiki=str((p.ROOT/'data/public/wiki/current').readlink()), reserved_count=p.a.sql('SELECT COUNT(*) FROM items WHERE id BETWEEN 963200 AND 963215').strip(), procedure_count=p.a.sql("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME='nightcap_install_raid_augments'").strip())
print(json.dumps(report))
"""

def remote(source, timeout=600):
    result = subprocess.run(SSH, input=source, text=True, encoding="utf8", capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2200:])
    return result.stdout

if __name__ == "__main__":
    data = json.loads(remote(REMOTE))
    (HERE / 'production-before.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    print({k:data[k] for k in ('players','free','reserved_count','procedure_count','base_hashes','public_wiki')})
