"""Failure injection into a completed, isolated spell-scaling rehearsal only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tier_spell_scaling import migration_sql, plan

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--rehearsal',type=Path,required=True)
 a=p.parse_args()
 result=json.loads((a.rehearsal/'result.json').read_text())
 database=result['database']
 if not re.fullmatch(r'nightcap_spell_rehearsal_[0-9]{8}',database): raise ValueError('Not an isolated rehearsal')
 output=a.rehearsal/'faults.json'
 if output.exists(): raise ValueError('Fault evidence already exists')
 def sql(statement,check=True):
  r=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
   'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],
   input=f'USE `{database}`;\n'+statement,text=True,encoding='utf-8',capture_output=True)
  if check and r.returncode: raise RuntimeError(r.stderr[-2000:])
  return r
 items=[json.loads(line) for line in (a.rehearsal/'items.jsonl').read_text().splitlines()]
 rows=plan(items)[:2]
 assert len(rows)==2
 lookup={r['id']:r for r in items}
 ids=','.join(str(i) for i in sorted({r['id'] for r in rows}|{r['base_id'] for r in rows}))
 def snapshot(): return hashlib.sha256(sql(f'SELECT * FROM items WHERE id IN ({ids}) ORDER BY id;').stdout.encode()).hexdigest()
 before=snapshot()
 forward=migration_sql(rows); rollback=migration_sql(rows,True)
 checks=[]
 def reject(script,message):
  preimage=snapshot()
  r=sql(script,False)
  assert r.returncode and message in r.stderr,r.stderr
  assert snapshot()==preimage,'Rejected migration wrote item data'
  sql('DROP PROCEDURE nightcap_apply_spell_plan;')
 first=rows[0]; base=lookup[first['base_id']]; item=lookup[first['id']]
 sql(f"UPDATE items SET hp=hp+1 WHERE id={base['id']};")
 reject(forward,'Item preimage drift')
 sql(f"UPDATE items SET hp={base['hp']} WHERE id={base['id']};")
 checks.append('base formula drift rejected')
 sql(f"UPDATE items SET Name=CONCAT(Name,' drift') WHERE id={item['id']};")
 reject(forward,'Item preimage drift')
 name_hex=item['Name'].encode('utf-8').hex()
 sql(f"UPDATE items SET Name=CONVERT(0x{name_hex} USING utf8mb4) WHERE id={item['id']};")
 checks.append('target identity drift rejected')
 assert snapshot()==before
 # Force validation to fail only after the UPDATE has actually run.
 sql('CREATE TRIGGER nightcap_spell_fault BEFORE UPDATE ON items FOR EACH ROW SET NEW.healamt=NEW.healamt+1;')
 reject(forward,'Item afterimage mismatch')
 sql('DROP TRIGGER nightcap_spell_fault;')
 assert snapshot()==before
 checks.append('after-UPDATE failure rolled back both rows exactly')
 sql(forward)
 sql(f"UPDATE items SET healamt=healamt+1 WHERE id={first['id']};")
 reject(rollback,'Item preimage drift')
 sql(f"UPDATE items SET healamt={first['new'][1]} WHERE id={first['id']};")
 sql(rollback)
 assert snapshot()==before
 checks.append('stale rollback rejected; exact rollback passed after recovery')
 evidence=dict(database=database,checks=checks,item_ids=[r['id'] for r in rows],scope_sha256=before,
  generator_sha256=hashlib.sha256(Path(__file__).with_name('tier_spell_scaling.py').read_bytes()).hexdigest())
 output.write_text(json.dumps(evidence,indent=2)+'\n')
 print(json.dumps(evidence))

if __name__=='__main__': main()
