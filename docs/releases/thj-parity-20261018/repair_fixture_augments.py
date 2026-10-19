"""Keep augment-only definitions out of the ordinary armor fixture selector."""
import hashlib,json,subprocess
from extend_matrix import REL,STAGE,content,select_gear

path=REL/'native-matrix.json';before=path.read_bytes();matrix=json.loads(before)
failure=json.loads((REL/'evidence/native-second-fixture-failure.json').read_text())
failed={c['id'] for c in failure['cases'] if c['status']!='passed'}
assert failed=={'parity-l50-observed-ascended','parity-l50-observed-legacy-spells'}
after=content.proposed_items(content.after_companions(content.original_items()))
targets=[after[r['id']] for r in content.thj_item_parity.catalog()['items']]
repairs=[]
for case in matrix['cases']:
    if case['id'] not in failed:continue
    b=case['input']['builds'][0];old=b['equipment']
    assert any(i['id']==651908 for i in old) and int(after[651908]['augtype'])!=0
    new=select_gear(targets,b['level'],sum(1<<(c-1) for c in b['classes']))
    assert old!=new and all(int(after[i['id']]['augtype'])==0 for i in new)
    b['equipment']=new;repairs.append({'case':case['id'],'before':old,'after':new})
path.write_text(json.dumps(matrix,indent=2)+'\n');(STAGE/'matrix.json').write_bytes(path.read_bytes())
(REL/'evidence/fixture-augment-repair.json').write_text(json.dumps({
    'cause':'Enchanted Werebone 651908 is an augment, not ordinary wearable armor',
    'fix':'Exclude nonzero augtype from the armor-only fixture selector',
    'scope':'two level-50 fixture loadouts only; no gameplay source/content changes',
    'previous_matrix_sha256':hashlib.sha256(before).hexdigest(),
    'matrix_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'repairs':repairs},indent=2)+'\n')
subprocess.run(['docker','cp',str(path),'akk-stack-eqemu-server-1:/tmp/nightcap-balance-thj-parity-20261018/matrix.json'],check=True)
print(json.dumps({'repaired':len(repairs),'native_source_changed':False}))
