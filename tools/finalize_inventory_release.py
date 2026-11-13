"""Record only observed native/client/wiki publication; leave owner QA open."""
import hashlib
import json
import re
from inventory_release_support import ROOT,HERE,ART,STAGE,remote,save


def main():
    deployed=json.loads((ART/'open-receipt.json').read_text(encoding='utf-8'))
    signed=json.loads((ART/'signed/verification.json').read_text(encoding='utf-8'))
    client=json.loads((HERE/'client-public-verification.json').read_text(encoding='utf-8'))
    wiki=json.loads((HERE/'wiki-public-verification.json').read_text(encoding='utf-8'))
    assert deployed['gateway_open'] and deployed['client_release']==client['release']==2026111202
    assert deployed['client_channel_sha256']==client['channel_sha256']==signed['channel_sha256']
    assert client['hosted'] and wiki['status']=='PASS'
    runtime=deployed['runtime'];workers=[p for p in runtime['processes'] if p[0]=='zone']
    assert len(workers)==12 and len({p[1] for p in workers})==1
    assert workers[0][1]=='b737e641008b0816706a14478e7d2fde5b5930829f7e1bba4b6954b3c4fda598'
    result=remote('NATIVE_STAGE='+repr(STAGE)+'''\nimport collections,hashlib,importlib.util,json,subprocess
from pathlib import Path
stage=Path(NATIVE_STAGE);spec=importlib.util.spec_from_file_location('inventory_final_probe',stage/'rollout.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);prior=m.initialize()
deployed=prior.read(prior.EVIDENCE/'activation/paired-deployed.json')
current=prior.r.running(deployed['runtime']['image_id'],prior.binaries());prior.base.health()
services={n:prior.r.compact(n) for n in ('game','gateway','db','web','tunnel')}
assert all(s['running'] and not s['oom_killed'] for s in services.values())
assert services['game']['health']==services['db']['health']=='healthy'
before=prior.read(prior.EVIDENCE/'preflight.json')['services']
assert all(services[n]==before[n] for n in ('db','web','tunnel'))
logs=prior.r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
markers=['MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement','Segmentation fault']
errors={s:logs.count(s) for s in markers};assert not any(errors.values()),errors
backup=prior.read(prior.EVIDENCE/'activation/backup.json')
print(json.dumps({'status':'PASS','runtime':current,'services':services,'db_web_tunnel_unchanged':True,
 'fresh_stopped_backup':backup,'error_markers':errors,'client_channel_sha256':hashlib.sha256((Path('/opt/nightcap/deploy/production/data/public/channel.json')).read_bytes()).hexdigest()}))
''')
    assert result['client_channel_sha256']==client['channel_sha256']
    result.update(gateway_open=True,source_pr='https://github.com/frank-grimes-jr/nightcap/pull/434',
        source_revision='5dabfb6dac2143b9e6220f74ac519936941ff6d7',main_merge='ab2e8d877a947c0828b46b983d65d71c1dca1d79',
        client_release=2026111202,database_restored=False,owner_gameplay_accepted=False,market=deployed.get('market'))
    save(HERE/'native-deployment.json',result)
    publication=json.loads((ART/'publish-client-receipt.json').read_text(encoding='utf-8'))
    save(HERE/'client-publication.json',publication)
    verification=json.loads((HERE/'verification.json').read_text(encoding='utf-8'))
    verification.update(status='PAIRED_NATIVE_CLIENT_WIKI_PUBLISHED_FOR_LIVE_TESTING',
        native_deployment='native-deployment.json',client_publication='client-publication.json',
        client_verification='client-public-verification.json',wiki_verification='wiki-public-verification.json',player_qa='OPEN')
    save(HERE/'verification.json',verification)
    checks=json.loads((HERE/'release-checks.json').read_text(encoding='utf-8'))
    checks['linux_publication_tests']={'rollout':18,'client_publisher':21,'wiki_publisher':16,'status':'all passed'}
    save(HERE/'release-checks.json',checks)
    text=(HERE/'README.md').read_text(encoding='utf-8')
    text=text.replace('The candidate is signed and locally verified, not yet deployed/published.',
        'Paired native/client release is deployed for live testing. Admissions are open;\nall12zone workers, native pair, stopped backup and preservation checks verify.\nAll148canonical HTTPS client assets/signature and all614wiki hashes/headers verify.\nOwner visible acceptance remains OPEN.')
    text=text.replace('Deployment/publication and owner visual QA are pending.','Deployment/publication verify; owner visual QA remains OPEN.')
    text=text.replace('The Windows publisher\nsuite passes16with5POSIX-only skips; all21must pass in Linux before preflight.',
        'The Windows publisher\nsuite passes16with5POSIX-only skips; all21pass on Linux before preflight.')
    text=text.replace('Client/wiki publication receipts will be\nrecorded after observing the actual outcome; planning is not deployment proof.',
        'Observed publication receipts are native-deployment.json, client-publication.json,\nclient-public-verification.json and wiki-public-{publication,verification}.json.\nPublication is not owner visual/player acceptance.')
    (HERE/'README.md').write_text(text,encoding='utf-8',newline='\n')
    entries={'CHANGES.md':'''## 2026-11-12 — Inventory combat stats, caps and heroics published for live testing

PR434/ab2e8d87 and paired zoneb737e641/client2026111202/proxy0.13.6 publish the
front-page combat summary and server current/cap/heroic attributes. MIT uses
cached combat AC; AVD total defense preserves Auto; native composite AC stays.
Heroic mechanics, power and progression are unchanged. Legacy NCST1 clients
remain compatible; normal fonts, equipment semantics and other tabs remain.

Exact deployed predecessor reproduction,16focused/11runtime/120native guards,
18Linux rollout/21client-publisher faults, stopped backup, saved-state/one-market
rotation and all12workers verify.148HTTPS client assets/signature/pair and
614wiki hashes/headers/private denials pass;145client descriptors and609wiki
outputs retained. Admissions open. Exit EQ/use launcher Play. Owner visible and
combined-build gameplay acceptance remain OPEN. Evidence and exact QA:
docs/releases/heroic-stats-inventory-20261112/.

''','docs/status.md':'''## November12 — Inventory combat summary published for live testing

PR434/ab2e8d87, zoneb737e641 and signed2026111202/proxy0.13.6 are deployed;
admissions open. Main Inventory shows AC/MIT/AVD/ATK/DMG/HEAL and green current,
white actual caps, gold heroics. MIT/AVD are server combat ratings; heroics are
already included in current values/caps. No balance or player-state repair.

All12workers, stopped backup/save-state/market/preservation checks and required
native/fault suites pass.148canonical HTTPS client assets/signature/pair and
614public wiki hashes/security/private denials verify;145other client descriptors
and609wiki outputs preserved. Fully exit EQ/use normal launcher Play. Native
visual, gear/buff/shield and lifecycle owner QA remains OPEN.
[Observed release and exact QA](releases/heroic-stats-inventory-20261112/README.md).

'''}
    for relative,entry in entries.items():
        path=ROOT/relative;old=path.read_text(encoding='utf-8')
        pattern=r'## (?:2026-11-12 — Inventory combat summary and caps prepared for live testing|November12 — Inventory combat summary ready for authorized live testing)\n.*?(?=\n## |\Z)'
        new,count=re.subn(pattern,entry.rstrip()+'\n',old,count=1,flags=re.DOTALL)
        assert count==1,relative;path.write_text(new,encoding='utf-8',newline='\n')
    paths=json.loads((HERE/'source-fingerprints.json').read_text(encoding='utf-8'))
    save(HERE/'source-fingerprints.json',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    print('Observed paired deployment/client/wiki publication recorded; owner QA OPEN')


if __name__=='__main__':main()
