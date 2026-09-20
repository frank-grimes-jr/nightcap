"""Run the existing native map probe against resident and ring coordinates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

def run(package,probe,verify_lavastorm_source=False):
    results=[]
    for path in sorted(package.glob('probe-*.json')):
        request=json.loads(path.read_text())
        configured=Path(request['map'])
        prerequisite=None
        if not configured.is_file():
            if not verify_lavastorm_source or configured.name!='lavastorm_v0.map':
                raise ValueError('Configured map is missing: '+str(configured))
            source=configured.with_name('lavastorm_orig.map')
            prerequisite=dict(configured_map=str(configured),verified_source=str(source),
                              source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),installed=False)
            request['map']=str(source)
        result=subprocess.run([str(probe)],input=json.dumps(request),text=True,capture_output=True,check=True)
        data=json.loads(result.stdout)
        if prerequisite:data['activation_prerequisite']=prerequisite
        for point in data['points']:
            center=point['samples'][0]
            point['ground_offset']=round(point['z']-center.get('ground_z',-99999),3)
            point['clear']=all(s['ground_hit'] and s.get('headroom',0)>=12 for s in point['samples']) and 0<=point['ground_offset']<=12
        results.append(data)
    (package/'geometry.json').write_text(json.dumps(results,indent=2)+'\n')
    for data in results:
        for point in data['points']:
            print(json.dumps({'map':data['map'],'label':point['label'],'clear':point['clear'],'ground_offset':point['ground_offset']}))
    if not all(p['clear'] for d in results for p in d['points']):
        raise AssertionError('Unsafe ground, landing height or headroom')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package',type=Path);p.add_argument('probe',type=Path)
    p.add_argument('--verify-lavastorm-source',action='store_true',help='Verify the existing Classic source map; does not install the missing configured alias')
    a=p.parse_args();run(a.package,a.probe,a.verify_lavastorm_source)
