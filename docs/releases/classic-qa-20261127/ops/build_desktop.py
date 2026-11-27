"""Build the desktop from the current launcher sources with only its bundled preview replaced."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

from build_preview import OUT, ORIGINAL, WS

ROOT=Path(__file__).resolve().parents[4]
PREVIOUS=WS/'_worktrees/hailstone-opt-in/eq-launcher'
GO=WS/'artifacts/toolchains/go1.27.1/go/bin/go.exe'
WAILS=WS/'artifacts/toolchains/wails2.16.0/wails.exe'
SEED=WS/'artifacts/ovh-private-20260920/production.seed'
PUBLISH=OUT/'desktop-channel'
RELEASE='2026112702'


def build():
    parent=json.loads((ORIGINAL/'release.json').read_bytes())
    old=next((ORIGINAL/'launcher-publish/launcher').rglob('nightcap-desktop.exe'))
    old_bytes=old.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest()==parent['desktop']
    built=json.loads((OUT/'build.json').read_bytes())
    assert hashlib.sha256((OUT/'nightcap-hailstone.zip').read_bytes()).hexdigest()==built['nightcap-hailstone.zip']
    archive=subprocess.check_output(['git','archive','--format=zip','HEAD','eq-launcher'],cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        z.extractall(OUT)
    target=OUT/'eq-launcher'
    policy='internal/launcher/policy_production_generated.go'
    shutil.copy2(PREVIOUS/policy,target/policy)
    for file in (PREVIOUS/'frontend/dist').rglob('*'):
        if file.is_file():
            assert file.read_bytes() in old_bytes, f'Frontend content differs from shipping desktop: {file.name}'
    shutil.copytree(PREVIOUS/'frontend/dist',target/'frontend/dist',dirs_exist_ok=True)
    shutil.copyfile(OUT/'nightcap-hailstone.zip',target/'internal/hailstone/payload/nightcap-hailstone.zip')
    profile=ORIGINAL/'profile.json'
    info=json.loads(profile.read_bytes())
    config=target/'wails.json'
    cfg=json.loads(config.read_bytes())
    cfg['info'].update(productName='Nightcap Launcher',productVersion=info['version'],
                       comments='Private Nightcap launcher with signed updates and encrypted game transport.')
    config.write_text(json.dumps(cfg,indent=2))
    env=dict(os.environ,GOCACHE=str(WS/'artifacts/go-cache'),GOTOOLCHAIN='local')
    env['PATH']=str(GO.parent)+os.pathsep+env.get('PATH','')
    def go(*args):
        subprocess.run([str(GO),*args],env=env,cwd=target,check=True)
    go('test','-tags','production','./internal/hailstone','./internal/launcher')
    subprocess.run([str(WAILS),'build','-platform','windows/amd64','-tags','production','-o','nightcap-desktop.exe',
                    '-s','-m','-nosyncgomod'],env=env,cwd=target,check=True)
    exe=target/'build/bin/nightcap-desktop.exe'
    assert (OUT/'nightcap-hailstone.zip').read_bytes() in exe.read_bytes()
    go('run','./cmd/nightcap-package','-production-profile',str(profile),'-publish',str(PUBLISH),
       '-key',str(SEED),'-release',RELEASE,'-launcher-exe',str(exe))
    go('run','-tags','production','./cmd/nightcap-releasecheck','-launcher-channel',str(PUBLISH/'launcher-channel.json'))
    pins={'desktop':hashlib.sha256(exe.read_bytes()).hexdigest(),
          'channel':hashlib.sha256((PUBLISH/'launcher-channel.json').read_bytes()).hexdigest(),
          'source':built['nightcap-hailstone-source.zip']}
    (OUT/'release.json').write_text(json.dumps(pins,indent=2)+'\n')
    print(json.dumps(pins,indent=2))


if __name__=='__main__':
    build()

