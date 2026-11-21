"""Restore the original Temple of Solusek Ro to the Classic zone gate."""
import gzip,json
from catalog import HERE,literal,field_literal
def row():
    rows=json.loads(gzip.decompress((HERE/'soltemple.json.gz').read_bytes()))['zones']
    assert len(rows)==1
    r=rows[0]
    assert (r['id'],r['zoneidnumber'],r['version'],r['short_name'],r['expansion'],r['bypass_expansion_check'])==(357,80,0,'soltemple',1,0)
    return r
def generate(action):
    if action not in ('before','forward','verify','rollback'):raise ValueError(action)
    r=row();old,new=(0,1) if action=='rollback' else (1,0)
    anchor=' AND '.join(('BINARY ' if isinstance(v,str) else '')+'`'+k+'` <=> '+field_literal('zone',k,v) for k,v in sorted(r.items()) if k!='expansion')
    allowed='`expansion`='+str(new if action=='verify' else old) if action in ('before','verify') else '`expansion` IN (0,1)'
    lines=['START TRANSACTION;','CREATE TEMPORARY TABLE classic_temple_guard(ok TINYINT NOT NULL CHECK(ok=1));','INSERT INTO classic_temple_guard SELECT COUNT(*)=1 FROM zone WHERE '+anchor+' AND '+allowed+' FOR UPDATE;']
    if action in ('forward','rollback'):
        lines+=['UPDATE zone SET expansion='+str(new)+' WHERE '+anchor+' AND expansion='+str(old)+';','INSERT INTO classic_temple_guard SELECT COUNT(*)=1 FROM zone WHERE '+anchor+' AND expansion='+str(new)+';']
    return '\n'.join(lines+['COMMIT;','DROP TEMPORARY TABLE classic_temple_guard;'])
