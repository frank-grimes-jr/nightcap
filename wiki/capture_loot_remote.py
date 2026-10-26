"""Owner-local read-only capture over the existing pinned production SSH profile."""
import gzip
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent

def main():
    command=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
             '-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
    p=subprocess.run(command,input=(HERE/'loot_capture.py').read_bytes(),capture_output=True,timeout=360)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace')[-1500:])
    data=json.loads(gzip.decompress(p.stdout))
    target=HERE.parent/'artifacts/wiki-loot/content.json.gz'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(p.stdout)
    print(json.dumps({'captured_at':data['captured_at'],'era':data['era_name'],
                      'rows':{k:len(v) for k,v in data.items() if isinstance(v,list)},'compressed_bytes':len(p.stdout)},indent=2))

if __name__=='__main__': main()
