"""Reuse the reviewed content-only publisher after title runtime verification."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from wiki import ART,BASE,HERE,PREVIOUS,RELEASE,ROOT,save,sha

sys.path.insert(0,str(ROOT/'tools'))
from quick_buff_remote import run as remote
from capture_lantern_content import SSH


def previous_module(name):
    folder=ROOT/'docs/releases/thj-combat-20261113/wiki'
    sys.path.insert(0,str(folder))
    spec=importlib.util.spec_from_file_location('retained_wiki_'+name,folder/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def publish():
    candidate=json.loads((HERE/'wiki-candidate.json').read_bytes())
    game=json.loads((HERE/'production-verified.json').read_bytes())
    assert game['result']=='PASS' and game['gateway_open'] and game['workers']==12 and game['restarts']==0 and game['title_catalog_enabled']
    before=json.loads((ROOT/'artifacts/titles-live-20261114/wiki-before.json').read_bytes())
    assert before['release']==PREVIOUS
    paths=[ART/(RELEASE+'.tar.gz'),ART/(RELEASE+'.tar.json')]
    assert [sha(p) for p in paths]==[candidate['package_sha256'],candidate['manifest_sha256']]
    paths.extend(BASE/'wiki-source/wiki'/n for n in ['deploy.py','update.py','test_deploy.py','test_update.py','nginx.conf'])
    values=dict(RELEASE=RELEASE,PREVIOUS=PREVIOUS,EXPECTED=before['manifest'],CONFIG=before['config_sha256'],
        GAME='titles-live-20261114-v1',RECEIPT=game['deployed_receipt'],UPLOAD='/home/ubuntu/wiki-'+RELEASE,
        PINS={p.name:sha(p) for p in paths},TITLE_OPERATOR=json.loads((HERE/'staged.json').read_bytes())['files']['release.py'])
    retained=previous_module('publish')
    script='\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+retained.GATES+TITLE_GUARD
    remote(script+'\ncheck_game()\ncheck_before()')
    subprocess.run(SSH[:-1]+['mkdir -m 700 '+values['UPLOAD']],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],*map(str,paths),SSH[-2]+':'+values['UPLOAD']+'/'],check=True,timeout=300)
    result=json.loads(remote(script+retained.PUBLISH,timeout=1200))
    save(HERE/'wiki-publication.json',result);print(json.dumps(result))


def verify():
    module=previous_module('verify_public')
    module.RELEASE=RELEASE;module.ART=ART;module.HERE=HERE
    module.save=lambda path,obj:save(HERE/'wiki-public-verification.json',obj)
    module.verify(False)


TITLE_GUARD="""
import sys
assert sha(release/'release.py')==TITLE_OPERATOR
spec=importlib.util.spec_from_file_location('title_publication_guard',release/'release.py')
title_module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=title_module
spec.loader.exec_module(title_module)
title_op=title_module.initialize()
original_check_game=check_game
def check_game():
    result=original_check_game()
    title_op.title_state()
    assert title_op.title_schema.settings(title_op.prior.sql)==[dict(id=1,catalog_version=1,enabled=1)]
    return result
"""


if __name__=='__main__':
    assert sys.argv[1:] in [['publish'],['verify']]
    publish() if sys.argv[1]=='publish' else verify()
