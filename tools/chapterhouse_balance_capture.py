"""Read public combat definitions from production; restore only the named synthetic DB."""
import base64, datetime, gzip, hashlib, json, subprocess, tarfile
from chapterhouse_balance import DB, OUT, ROOT, sql, cache
from dungeon_migration import insert

TABLES = ('rule_sets','rule_values','aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs','spells_new','skill_caps')
CAPTURE = OUT/'balance-public-content.json.gz'

def capture():
    fixture_path=OUT/'calibration-catalog-input.json'
    if fixture_path.exists():fixture=json.loads(fixture_path.read_text())
    else:
        with tarfile.open(OUT/'native-combat-fixtures.tar.gz','r:gz') as archive:
            fixture=json.load(archive.extractfile('calibration-catalog-input.json'))
    ids={x['id'] for x in fixture['builds'][0]['equipment']}
    ids.update(a['id'] for x in fixture['builds'][0]['equipment'] for a in x.get('augments',[]))
    ids.update((5403,205403,405403,605403))
    for ident in list(ids):
        ids.update(ident%200000+200000*t for t in range(4))
    script='''import base64,datetime,gzip,json,subprocess
root='/opt/nightcap/deploy/production'
def q(statement):
    command=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick','--skip-column-names','--default-character-set=utf8mb4','peq']
    result=subprocess.run(command,cwd=root,input='SET SESSION max_session_mem_used=134217728; SET TRANSACTION READ ONLY; START TRANSACTION WITH CONSISTENT SNAPSHOT; '+statement+'; COMMIT;',text=True,capture_output=True,check=True,timeout=900)
    return result.stdout.splitlines()
result={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':'production read-only public combat definitions','tables':{}}
for table in TABLES+('items',):
    columns=[r.split('\\t')[0] for r in q('SHOW COLUMNS FROM `'+table+'`')]
    where=(' WHERE id IN ('+','.join(map(str,IDS))+')') if table=='items' else ''
    rows=[json.loads(r) for r in q('SELECT JSON_ARRAY('+','.join('`'+c+'`' for c in columns)+') FROM `'+table+'`'+where)]
    result['tables'][table]={'columns':columns,'rows':rows}
result['selected_ruleset']=q("SELECT value FROM variables WHERE varname='RuleSet'")
payload=gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0)
assert len(payload)<50000000
print(base64.b64encode(payload).decode())
'''.replace('TABLES',repr(TABLES)).replace('IDS',repr(sorted(ids)))
    command=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
    result=subprocess.run(command,input=script,text=True,capture_output=True,timeout=1000)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    data=base64.b64decode(result.stdout,validate=False)
    document=json.loads(gzip.decompress(data))
    CAPTURE.write_bytes(data)
    receipt=dict(captured_at=document['captured_at'],sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),tables={t:len(v['rows']) for t,v in document['tables'].items()},selected_ruleset=document['selected_ruleset'],production_changed=False)
    (OUT/'balance-public-content-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

def restore():
    assert DB=='nightcap_chapterhouse_balance_20261023'
    document=json.loads(gzip.decompress(CAPTURE.read_bytes()))
    if document['selected_ruleset'] not in ([],['default']):
        raise RuntimeError('Non-default production ruleset requires an explicit fixture review')
    for table,payload in document['tables'].items():
        assert table in TABLES+('items',)
        if table!='items':sql('DELETE FROM `'+table+'`;')
        rows=payload['rows']
        for start in range(0,len(rows),250):
            sql('\n'.join(insert(table,dict(zip(payload['columns'],row))).replace('INSERT INTO','REPLACE INTO',1) for row in rows[start:start+250]))
        print(table,len(rows),flush=True)
    cache()
    print('Refreshed public definitions in isolated synthetic database only',flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('capture','restore'));a=p.parse_args();globals()[a.stage]()
