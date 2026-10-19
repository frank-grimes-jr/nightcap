"""Verify/rehearse only the explicitly named synthetic combined database."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from prepare_native import DB,db_command
from thj_combined_content import original_items,after_companions,proposed_items,capture,item_changes,recovery_changes
from thj_item_migration import row_hash
from item_scaling_overrides import protected_bases

before=original_items();after=proposed_items(after_companions(before));columns=capture()['schemas']['items']['columns']
sql=[]
for name in ('disable','disable','enable','enable','forward'):
    sql.append((REL/'content'/f'rules-{name}.sql').read_text())
ids=','.join(map(str,sorted(after)))
expr="SHA2(CONCAT_WS('|',"+','.join("IFNULL(HEX(CAST(`"+c+"` AS CHAR CHARACTER SET utf8mb4)),'NULL')" for c in columns)+'),256)'
sql.append(f'SELECT id,{expr} FROM items WHERE id IN ({ids}) ORDER BY id;')
output=subprocess.check_output(db_command(DB),input='\n'.join(sql),text=True)
observed={int(line.split('\t')[0]):line.split('\t')[1] for line in output.splitlines()}
assert observed=={i:row_hash(r,columns) for i,r in after.items()},'Full afterimage drift'
report={'status':'passed','database':DB,'existing_definitions_verified':len(observed),'columns_per_row':len(columns),
    'changed_definitions':len(item_changes()),'numeric_recovery_definitions':len(recovery_changes()),
    'new_content':'pet/WPM non-gear forward applied twice during setup',
    'new_spell_rules':'disable twice, enable twice, original forward again; final enabled',
    'source_capture_sha256':hashlib.sha256((ROOT/'tools/fixtures/thj-combined-preimages-20261018.json.gz').read_bytes()).hexdigest(),
    'scope':'dedicated synthetic DB only; no live content/player changes'}
(REL/'evidence/content-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
