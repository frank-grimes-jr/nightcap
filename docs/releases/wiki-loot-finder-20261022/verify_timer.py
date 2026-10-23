"""Read-only proof of the recurring production timer and immutable public data."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / 'artifacts/wiki-loot'
REMOTE = r'''
import gzip,hashlib,json,pathlib,shutil,subprocess
from datetime import datetime,timezone
base=pathlib.Path('/opt/nightcap/deploy/production')
data=base/'data/public/wiki-data'
index=json.loads(gzip.decompress((data/'current/index.json.gz').read_bytes()))
def unit(name,properties):
 output=subprocess.check_output(['systemctl','show','--property='+properties,name],text=True)
 return dict(line.split('=',1) for line in output.splitlines() if '=' in line)
paths=[pathlib.Path('/opt/nightcap/wiki-loot')/name for name in ['loot_capture.py','loot_model.py','loot_refresh.py']]
paths += [pathlib.Path('/etc/systemd/system')/('nightcap-wiki-loot.'+suffix) for suffix in ['service','timer']]
print(json.dumps({
 'observed_at':datetime.now(timezone.utc).isoformat(),
 'service':unit('nightcap-wiki-loot.service','ActiveState,Result,ExecMainStatus,ExecMainStartTimestamp,ExecMainExitTimestamp'),
 'timer':unit('nightcap-wiki-loot.timer','ActiveState,UnitFileState,LastTriggerUSec,NextElapseUSecMonotonic,TimersMonotonic'),
 'snapshot':index['snapshot'],'captured_at':index['captured_at'],'items':len(index['items']),
 'index_sha256':hashlib.sha256(gzip.decompress((data/'current/index.json.gz').read_bytes())).hexdigest(),
 'installed_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
 'retained_snapshots':sorted(p.name for p in data.iterdir() if p.is_dir() and not p.is_symlink()),
 'free_bytes':shutil.disk_usage(base).free,
 'release':(base/'data/public/wiki/current').readlink().name,
 'recent_service_log':subprocess.check_output(['journalctl','--unit=nightcap-wiki-loot.service','--since=2026-10-23 01:22:00 UTC','--no-pager','--output=short-iso'],text=True)
}))
'''


def public(path):
    request = Request('https://wiki.nightcapgame.org/' + path, headers={
        'User-Agent': 'NightcapLauncher/0.6.0', 'Accept-Encoding': 'identity',
        'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=45) as response:
        assert response.status == 200
        body = response.read()
        return gzip.decompress(body) if response.headers.get('Content-Encoding') == 'gzip' else body


def main():
    result = subprocess.run(['ssh', '-i', str(Path.home()/'.ssh/nightcap_ovh'),
        '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
        'ubuntu@135.148.47.202', 'sudo -n python3 -'],
        input=REMOTE.encode(), capture_output=True, timeout=60, check=True)
    report = json.loads(result.stdout)
    assert report['service']['Result'] == 'success'
    assert report['service']['ExecMainStatus'] == '0'
    assert report['service']['ActiveState'] == 'inactive'
    assert report['timer']['ActiveState'] == 'active'
    assert report['timer']['UnitFileState'] == 'enabled'
    assert report['captured_at'] > '2026-10-23T01:39:00'
    assert report['snapshot'] != 'c7da22524ad022f9'
    assert report['release'] == '20261022-loot-finder-v2'
    expected = json.loads((ARTIFACTS/'staging.json').read_text(encoding='utf-8'))['hashes']
    assert all(expected[name] == digest for name,digest in report['installed_sha256'].items())
    body = public('loot-data/current/index.json?verify=scheduled-refresh')
    assert hashlib.sha256(body).hexdigest() == report['index_sha256']
    prior = json.loads(public('loot-data/c7da22524ad022f9/item-1365.json'))
    current = json.loads(public(f"loot-data/{report['snapshot']}/item-1365.json"))
    assert prior['id'] == current['id'] == 1365 and prior['sources'] == current['sources']
    report.update(result='PASS', public_index_matches_origin=True,
                  previous_immutable_item_readable=True, installed_sources_match=True)
    (ARTIFACTS/'timer-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items()
                     if key not in ('recent_service_log','installed_sha256')},indent=2))


if __name__ == '__main__':
    main()
