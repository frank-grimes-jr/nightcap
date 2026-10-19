"""Create the exclusive upload package and sign the paired client locally."""
import base64
import hashlib
import json
import shutil
import subprocess
import tarfile
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT.parent/'thj-parity-production-stage'
BUNDLE = ROOT.parent/'thj-parity-test-bundle'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    before = json.loads((HERE/'production-before.json').read_text())
    assert before['base_hashes']['bin/zone'] == '29b8093147ffbc4c0d387a4e3fa55a3a041dbb9ae7da731b493b21601a6dec2f'
    assert not before['stage_exists'] and not before['gm_maintenance']
    resume = sys.argv[1:] == ['--resume-before-signing']
    assert not (OUT/'client/channel.json').exists() and not (OUT/'manifest.json').exists()
    OUT.mkdir(exist_ok=resume)
    shutil.copytree(BUNDLE/'server/bin',OUT/'bin',dirs_exist_ok=resume)
    shutil.copytree(BUNDLE/'content',OUT/'content',dirs_exist_ok=resume)
    shutil.copytree(BUNDLE/'client-delta',OUT/'client/assets',dirs_exist_ok=resume)
    for name in ('rollout.py','production-before.json'):
        shutil.copyfile(HERE/name,OUT/name)
    shutil.copyfile(ROOT/'docs/releases/reforge-colors-20261018/rollout.py',OUT/'base_operator.py')
    shutil.copyfile(HERE/'prepare_client.py',OUT/'client/prepare.py')
    publisher = (ROOT/'docs/releases/client-zone-validation-20261018/stage/publish.py').read_text()
    publisher = publisher.replace('/opt/nightcap/releases/client-zone-validation-20261018',
                                  '/opt/nightcap/releases/thj-parity-20261018/client')
    publisher = publisher.replace('2026101801','2026101802').replace('2026101702','2026101801')
    (OUT/'client/publish.py').write_text(publisher)
    shutil.copyfile(OUT/'client/publish.py',HERE/'publish_client.py')
    raw = base64.b64decode(before['channel_base64'])
    (OUT/'client/previous-channel.json').write_bytes(raw)
    old = json.loads(base64.b64decode(json.loads(raw)['manifest']))
    history = [{'release':2026101802,'date':'2026-10-18','changes':[
        {'kind':'feature','text':'Ascended item values and spell scaling now follow reviewed THJ references. Starter quality upgrades stay modest, and dungeon gear remains a meaningful step up.'},
        {'kind':'feature','text':'Permanent pet equipment now supports full item instances and augments across three pages, with 15 Mage items or eight for other pet classes. Pet support spells and shared Spell Damage/Heal Amount caps are updated.'},
        {'kind':'feature','text':'Earned shield and melee AAs, heroic Strength scaling, weapon procs and support effects are updated for held classes. This balance release is open for in-game testing.'},
    ]}] + old['patch_notes']
    (ROOT/'eq-launcher/patch-notes.json').write_text(json.dumps(history,indent=2)+'\n')
    command = ROOT/'eq-launcher/cmd/thj-release-sign'
    command.mkdir(exist_ok=False)
    shutil.copyfile(HERE/'sign-client.go',command/'main.go')
    try:
        subprocess.run(['E:/EQ_Local_Dev/artifacts/toolchains/go1.27.1/go/bin/go.exe','run','./cmd/thj-release-sign','-assets',str(OUT/'client/assets'),
            '-previous',str(OUT/'client/previous-channel.json'),'-notes',str(ROOT/'eq-launcher/patch-notes.json'),
            '-key','E:/EQ_Local_Dev/artifacts/ovh-private-20260920/production.seed',
            '-output',str(OUT/'client/channel.json')],cwd=ROOT/'eq-launcher',check=True)
    finally:
        (command/'main.go').unlink(); command.rmdir()
    manifest = {'base_image_id':before['services']['game']['image_id'],
        'base_hashes':before['base_hashes'],'runtime_helper_sha256':before['runtime_helper_sha256'],
        'previous_channel_sha256':hashlib.sha256(raw).hexdigest(),
        'source_ref':'b80456eca59daef9cdcce5e4135fb8741ec8056f',
        'components':sorted(p.relative_to(OUT).as_posix() for p in (OUT/'content').glob('*.sql')),
        'files':{p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copyfile(OUT/'manifest.json',HERE/'manifest.json')
    package = ROOT.parent/'thj-parity-production.tar.gz'
    with tarfile.open(package,'w:gz') as archive:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():
                info = archive.gettarinfo(p,arcname=p.relative_to(OUT).as_posix())
                info.mode = 0o755 if p.parent == OUT/'bin' else 0o600
                with p.open('rb') as f:
                    archive.addfile(info,f)
    print(json.dumps({'package':str(package),'bytes':package.stat().st_size,'sha256':sha(package),'files':len(manifest['files'])}))


if __name__ == '__main__':
    main()
