"""Publish only after the automatic title binary and active catalog verify live."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from wiki import ART,BASE,HERE,ROOT,PREVIOUS,RELEASE,save

sys.path.insert(0,str(ROOT/'tools'))
from quick_buff_remote import run as remote
from capture_lantern_content import SSH
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def old(name):
    folder=ROOT/'docs/releases/thj-combat-20261113/wiki';sys.path.insert(0,str(folder))
    spec=importlib.util.spec_from_file_location('automatic_wiki_'+name,folder/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


TITLE_GUARD="""
import sys
title_release=release.parent/'titles-automatic-suffix-20261114-v1'
assert sha(title_release/'release.py')==TITLE_OPERATOR
spec=importlib.util.spec_from_file_location('automatic_title_publication_guard',title_release/'release.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
title_op=module.initialize()
original_check_game=check_game
def check_game():
    result=original_check_game()
    runtime=title_op.r.running(result['image'],RUNTIME_BINARIES)
    assert runtime['started_at']==RUNTIME_STARTED and runtime['restart_count']==0
    assert not any(runtime['errors'].values()) and sum(x[0]=='zone' for x in runtime['processes'])==12
    title_op.title_state()
    assert title_op.title_schema.settings(title_op.prior.sql)==[dict(id=1,catalog_version=1,enabled=1)]
    return result
"""

RUNTIME_GUARD="""
def check_game():
    assert sha(receipt)==RECEIPT
    game=json.loads(receipt.read_bytes())
    assert game['gateway_open'] and sha(root/'data/public/channel.json')==CHANNEL
    manifest=json.loads((release/'manifest.json').read_bytes())
    if GAME=='classic-augment-stacking-20261114-v1':
        assert sha(release/'manifest.json')==SUCCESSOR_MANIFEST
        assert manifest['channel']==CHANNEL and manifest['base_hashes']['bin/zone']==TITLE_ZONE
        assert manifest['binaries']['zone']==RUNTIME_ZONE
    else:
        assert GAME=='titles-automatic-suffix-20261114-v1' and game['client_channel_sha256']==CHANNEL
    info=json.loads(subprocess.check_output(['docker','inspect','nightcap-production-game-1','nightcap-production-gateway-1']))
    assert info[0]['Image']==game['image'] and info[0]['State']['Health']['Status']=='healthy'
    assert all(r['State']['Running'] for r in info)
    game.update(client_release=CLIENT_RELEASE,client_channel_sha256=CHANNEL)
    return game
"""


def publish():
    candidate=json.loads((HERE/'wiki-candidate.json').read_bytes())
    game=json.loads((HERE/'production-verified.json').read_bytes())
    build=json.loads((HERE/'shipping-candidate.json').read_bytes())
    assert game['result']=='PASS' and game['gateway_open'] and game['workers']==12 and game['restarts']==0
    successor=json.loads((HERE/'successor.json').read_bytes()) if game.get('runtime_stage') else None
    assert game['binaries']['zone']==(successor['zone'] if successor else build['zone'])
    previous=json.loads((ROOT/'docs/titles/deployment-20261114/wiki-publication.json').read_bytes())
    assert previous['result']=='PASS' and previous['release']==PREVIOUS
    paths=[ART/(RELEASE+'.tar.gz'),ART/(RELEASE+'.tar.json')]
    assert [sha(p) for p in paths]==[candidate['package_sha256'],candidate['manifest_sha256']]
    paths.extend(BASE/'wiki-source/wiki'/n for n in ['deploy.py','update.py','test_deploy.py','test_update.py','nginx.conf'])
    values=dict(RELEASE=RELEASE,PREVIOUS=PREVIOUS,EXPECTED=json.loads((BASE/(PREVIOUS+'.tar.json')).read_bytes()),
        CONFIG=previous['config_sha256'],GAME=game.get('runtime_stage','titles-automatic-suffix-20261114-v1'),RECEIPT=game['deployed_receipt'],
        UPLOAD='/home/ubuntu/wiki-'+RELEASE,PINS={p.name:sha(p) for p in paths},
        TITLE_OPERATOR=json.loads((HERE/'staged.json').read_bytes())['files']['release.py'],
        CHANNEL=game['client_channel_sha256'],CLIENT_RELEASE=game['client_release'],TITLE_ZONE=build['zone'],
        RUNTIME_ZONE=game['binaries']['zone'],SUCCESSOR_MANIFEST=successor['manifest_sha256'] if successor else None,
        RUNTIME_BINARIES=game['binaries'],RUNTIME_STARTED=game['started_at'])
    publisher=old('publish')
    script='\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+publisher.GATES+RUNTIME_GUARD+TITLE_GUARD
    remote(script+'\ncheck_game()\ncheck_before()')
    subprocess.run(SSH[:-1]+['mkdir -m 700 '+values['UPLOAD']],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],*map(str,paths),SSH[-2]+':'+values['UPLOAD']+'/'],check=True,timeout=300)
    result=json.loads(remote(script+publisher.PUBLISH,timeout=1200))
    save(HERE/'wiki-publication.json',result);print(json.dumps(result))


def verify():
    module=old('verify_public');module.RELEASE=RELEASE;module.ART=ART;module.HERE=HERE
    module.save=lambda path,obj:save(HERE/'wiki-public-verification.json',obj)
    module.verify(False)


if __name__=='__main__':
    assert sys.argv[1:] in [['publish'],['verify']]
    publish() if sys.argv[1]=='publish' else verify()
