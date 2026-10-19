"""Repair the four synthetic loadouts rejected by unchanged native Lore guards."""
import hashlib,json,subprocess
from extend_matrix import REL,STAGE,content,select_gear

path=REL/'native-matrix.json'
before=path.read_bytes();matrix=json.loads(before)
initial=json.loads((REL/'evidence/native-initial-fixture-failure.json').read_text())
failed={c['id'] for c in initial['cases'] if c['status']!='passed'}
assert failed=={f'parity-l{level}-observed-{suffix}' for level in (50,65) for suffix in ('ascended','legacy-spells')}
after=content.proposed_items(content.after_companions(content.original_items()))
targets=[after[r['id']] for r in content.thj_item_parity.catalog()['items']]
repairs=[]
for case in matrix['cases']:
    if case['id'] not in failed:continue
    build=case['input']['builds'][0];old=build['equipment']
    new=select_gear(targets,build['level'],sum(1<<(c-1) for c in build['classes']))
    assert old!=new
    seen=set()
    for entry in new:
        row=after[entry['id']];group=int(row['loregroup'])
        if group:
            key=(group,row['id'] if group==-1 else 0)
            assert key not in seen
            seen.add(key)
    build['equipment']=new
    repairs.append({'case':case['id'],'before':old,'after':new})
path.write_text(json.dumps(matrix,indent=2)+'\n')
(STAGE/'matrix.json').write_bytes(path.read_bytes())
(REL/'evidence/fixture-repair.json').write_text(json.dumps({
    'cause':'Highest-stat selection repeated Lore items in multiple compatible slots',
    'fix':'Selector tracks native LoreGroup and per-ID minus-one semantics',
    'scope':'four synthetic fixture loadouts only; no engine, item-definition or equipment-rule changes',
    'previous_matrix_sha256':hashlib.sha256(before).hexdigest(),
    'matrix_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'repairs':repairs},indent=2)+'\n')
subprocess.run(['docker','cp',str(path),'akk-stack-eqemu-server-1:/tmp/nightcap-balance-thj-parity-20261018/matrix.json'],check=True)
print(json.dumps({'repaired':len(repairs),'native_source_changed':False}))
