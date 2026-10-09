"""Exercise generated migrations and actual native forge SQL in disposable schemas."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import zone_hunt

def run(release,output):
    checks=[]
    def verify(condition,label):
        if not condition: raise AssertionError(label)
        checks.append(label)
    def sql(schema,source,check=True):
        command=['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
                 'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names']
        result=subprocess.run(command,input=(f'USE `{schema}`;\n' if schema else '')+source,
                              text=True,encoding='utf-8',capture_output=True,timeout=90)
        if check and result.returncode: raise RuntimeError(result.stderr[-2500:])
        return result
    generated=release/'generated'
    ddl=(generated/'install.sql').read_text()
    preimages=json.loads((generated/'socket-preimages.json').read_text())
    trace=json.loads((release/'inventory-native.json').read_text())['forge_queries']
    for drift in (False,True):
        schema='nightcap_zone_hunt_test_'+secrets.token_hex(6)
        assert re.fullmatch(r'nightcap_zone_hunt_test_[0-9a-f]{12}',schema)
        sql(None,f'CREATE DATABASE `{schema}`;')
        try:
            sql(schema,'CREATE TABLE items LIKE peq.items; ALTER TABLE items ENGINE=InnoDB; CREATE TABLE inventory LIKE peq.inventory; ALTER TABLE inventory ENGINE=InnoDB;')
            seed=[]
            for image in preimages:
                row={k:v if k=='Name' else int(v) for k,v in image['before'].items()}
                seed.append(zone_hunt.insert('items',row))
            sql(schema,'\n'.join(seed))
            if drift:
                changed=preimages[-1]['id']
                sql(schema,f"UPDATE items SET Name=CONCAT(Name,'!') WHERE id={changed};")
                verify(sql(schema,ddl,False).returncode!=0,'socket preimage drift rejects installation')
                verify(sql(schema,'SELECT COUNT(*) FROM items WHERE id BETWEEN 940000 AND 940999; SELECT COUNT(*) FROM nightcap_zone_hunt_state;').stdout.strip()=='0\n0','failed migration rolls back every inserted item and state row')
                verify(sql(schema,'SELECT COUNT(*) FROM items WHERE 22 IN (augslot1type,augslot2type,augslot3type,augslot4type,augslot5type,augslot6type);').stdout.strip()=='0','failed late socket edit rolls back earlier socket changes')
                continue
            sql(schema,ddl)
            verify(sql(schema,'SELECT COUNT(*) FROM items WHERE id BETWEEN 940000 AND 940999; SELECT COUNT(*) FROM nightcap_zone_hunt_zones WHERE enabled=1; SELECT COUNT(*) FROM nightcap_zone_hunt_sources;').stdout.strip()=='448\n48\n6056','448 exact variants, 48 audited zones and 6056 native source pairs installed')
            verify(sql(schema,'SELECT enabled FROM nightcap_zone_hunt_state;').stdout.strip()=='0','installation leaves acquisition disabled until matching runtime activation')
            verify(sql(schema,ddl,False).returncode!=0,'migration replay refuses existing feature ownership')
            sql(schema,(generated/'activate.sql').read_text())
            seed_inventory='\n'.join(f'INSERT INTO inventory(character_id,slot_id,item_id,charges,guid,instnodrop) VALUES(77,{slot},940024,1,{700+slot},{int(slot==24)});' for slot in (23,24,25))
            def fingerprint():
                return hashlib.sha256(sql(schema,'SELECT * FROM inventory ORDER BY character_id,slot_id; SELECT * FROM nightcap_zone_hunt_forges ORDER BY request_id;').stdout.encode()).hexdigest()
            sql(schema,seed_inventory)
            before=fingerprint()
            for index,query in enumerate(trace):
                if not query.startswith(('DELETE FROM inventory','INSERT INTO inventory','INSERT INTO nightcap_zone_hunt_forges')): continue
                sql(schema,';\n'.join(trace[:index+1])+';\nROLLBACK;')
                verify(fingerprint()==before,f'rollback after native write {index} restores inputs and removes output/receipt')
            sql(schema,';\n'.join(trace)+';')
            verify(sql(schema,'SELECT slot_id,item_id,charges,instnodrop FROM inventory; SELECT COUNT(*) FROM nightcap_zone_hunt_forges;').stdout.strip()=='23\t940025\t1\t1\n1','actual native SQL commits one bound upgrade and one receipt')
            committed=fingerprint()
            verify(sql(schema,';\n'.join(trace)+';',False).returncode!=0 and fingerprint()==committed,'duplicate forge receipt cannot grant another output')
            sql(schema,(generated/'rollback.sql').read_text())
            verify(fingerprint()==committed,'operational rollback preserves awarded inventory and forge receipts')
            verify(sql(schema,'SELECT enabled FROM nightcap_zone_hunt_state; SELECT COUNT(*) FROM items WHERE id BETWEEN 940000 AND 940999;').stdout.strip()=='0\n448','operational rollback disables acquisition and retains item definitions')
        finally:
            assert re.fullmatch(r'nightcap_zone_hunt_test_[0-9a-f]{12}',schema)
            sql(None,f'DROP DATABASE `{schema}`;')
    evidence=dict(status='passed',scope='Disposable MariaDB schemas; production and player rows untouched',
                  install_sha256=hashlib.sha256(ddl.encode()).hexdigest(),checks=checks)
    output.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(status='passed',checks=len(checks))))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--release',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.release,a.output)
