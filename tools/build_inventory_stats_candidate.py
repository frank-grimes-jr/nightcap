"""Send reviewed source-only delta to isolated local build container; never deploy."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts/heroic-stats'
CONTAINER='akk-stack-eqemu-server-1'
PAYLOAD='/tmp/nightcap-inventory-payload-20261112-v4'
OUTPUT='/tmp/nightcap-inventory-build-20261112-v4'


def main():
    paths=['server-mods/code/zone/client.h','server-mods/code/zone/command.cpp','server-mods/code/zone/gm_commands/nightcapui.cpp']
    patch=subprocess.check_output(['git','diff','--no-ext-diff','--unified=3','HEAD','--',*paths],cwd=ROOT)
    assert patch and b'inventory_stats_protocol.h' in patch
    (ART/'server.patch').write_bytes(patch)
    subprocess.run(['docker','exec',CONTAINER,'mkdir',PAYLOAD],check=True)
    for source,name in [(ART/'server.patch','server.patch'),
        (ROOT/'server-mods/code/common/inventory_stats_protocol.h','inventory_stats_protocol.h'),
        (ROOT/'docs/releases/heroic-stats-inventory-20261112/build_native.py','build_native.py')]:
        subprocess.run(['docker','cp',str(source),CONTAINER+':'+PAYLOAD+'/'+name],check=True)
    subprocess.run(['docker','exec',CONTAINER,'python3',PAYLOAD+'/build_native.py','--payload',PAYLOAD,'--output',OUTPUT],check=True)
    for source,name in [('native-build.json','native-build.json'),('candidate-zone.stripped','candidate-zone')]:
        subprocess.run(['docker','cp',CONTAINER+':'+OUTPUT+'/'+source,str(ART/name)],check=True)


if __name__=='__main__':main()
