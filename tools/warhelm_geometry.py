"""Probe every authored point against native server maps without editing client files."""
import hashlib,json,subprocess
from warhelm_content import OUT, HOST_SHORT, compile_rows

def main():
    rows=compile_rows();report={}
    for short in ('kael',HOST_SHORT):
        points=[]
        entries=rows['nightcap_dungeon_spawns'] if short=='kael' else [s for s in rows['spawn2'] if s['zone']==short]
        for s in entries:points.append(dict(label=str(s.get('spawn_id',s.get('id'))),**{k:s[k] for k in ('x','y','z')}))
        if short=='kael':
            guardian=next(s for s in entries if s['npc_id']==998867)
            for side in (-1,1):points.append(dict(label='vigil-wave-'+str(side),x=guardian['x']+8*side,y=guardian['y'],z=guardian['z']))
            warden=next(s for s in entries if s['npc_id']==998862)
            for side in (-1,1):points.append(dict(label='warden-add-'+str(side),x=warden['x']+8*side,y=warden['y'],z=warden['z']))
        path='/home/eqemu/server/maps/base/'+short+'.map'
        request=dict(map=path,points=points)
        r=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','/tmp/nightcap-map-probe-20260920/map-probe'],input=json.dumps(request),text=True,capture_output=True,check=True)
        result=json.loads(r.stdout)
        result['map_sha256']=subprocess.check_output(['docker','exec','akk-stack-eqemu-server-1','sha256sum',path],text=True).split()[0]
        result['rejected']=[]
        for p in result['points']:
            if not all(s['ground_hit'] and s['headroom']>=8 and abs(s['ground_z']-p['z'])<6 for s in p['samples']):
                result['rejected'].append(p['label'])
        report[short]=result
        print(short,'points',len(points),'rejected',result['rejected'])
    (OUT/'authored-geometry.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not any(r['rejected'] for r in report.values()),'Fix rejected geometry before activation'

if __name__=='__main__':main()
