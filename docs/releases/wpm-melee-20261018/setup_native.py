"""Prepare a separate local native diagnostic runtime, never the game runtime."""
import json
from pathlib import Path
import shutil

ROOT=Path('/tmp/nightcap-balance-wpm-20261018')
BASE=Path('/tmp/nightcap-balance-20260912')
INPUT=Path('/tmp/nightcap-wpm-test-input')


def main():
    ROOT.mkdir(exist_ok=False)
    config=json.loads((BASE/'eqemu_config.json').read_text())
    assert config['server']['database']['db']=='nightcap_balance_20260912'
    config['server']['database']['db']='nightcap_wpm_balance_20261018'
    config['server']['auto_database_updates']='false'
    (ROOT/'eqemu_config.json').write_text(json.dumps(config,indent=2))
    for name in ('quests','plugins','lua_modules','logs','shared'):(ROOT/name).mkdir()
    (ROOT/'maps').symlink_to(BASE/'maps',target_is_directory=True)
    for name in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h'):
        shutil.copyfile(INPUT/name,ROOT/name)
    for name in ('melee-fixed-pilot-inputs.json','pet-support-pilot-inputs.json','nagafen-inputs.json'):
        shutil.copyfile(BASE/name,ROOT/name)
    print(json.dumps({'runtime':str(ROOT),'database':config['server']['database']['db'],'status':'isolated_not_installed'}))


if __name__=='__main__':main()
