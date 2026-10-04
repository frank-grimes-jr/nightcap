"""Adapt the previously fault-tested deployment to the changed item-cache ABI."""
from pathlib import Path
r=Path(__file__).parent
s=(r.parent/'blessing-lifetime-20261004/rollout.py').read_text()
s=s.replace('Two-binary blessing lifetime repair. No database writes, schema changes or quest replacement.',
            'Universal trading rollout: five binaries, one rule, regenerated item cache; no item/quest rewrites.')
s=s.replace("import argparse,fcntl,hashlib,json,os,re,subprocess,time", "import argparse,fcntl,gzip,hashlib,json,mmap,os,re,shutil,struct,subprocess,time")
s=s.replace('blessing-lifetime-server-20261004-r2','free-trade-20261004').replace('.env.blessing-lifetime-','.env.free-trade-')
s=s.replace("rows=sql('SELECT * FROM `'+table+'`;').splitlines()", "rows=sql('SELECT * FROM `'+table+'`'+(\" WHERE rule_name <> 'Items:FreeTrade'\" if table=='rule_values' else '')+';').splitlines()")
s=s.replace("EVIDENCE.mkdir(mode=0o700)", "EVIDENCE.mkdir(mode=0o700)\n    backup=database_backup()")
s=s.replace("'old_receipt_aware_image_verified':True", "'old_receipt_aware_image_verified':True,'backup':backup")
s=s.replace("assert not EVIDENCE.exists();closed_ports()", "assert not EVIDENCE.exists();closed_ports()\n    assert policy_rows()==[], 'Unexpected pre-existing FreeTrade rule; stop for rebaseline'")
s=s.replace("before=player_data();save('player-before.json',before)", "before=player_data();save('player-before.json',before)\n        content=content_data();save('content-before.json',content)\n        sql(\"INSERT INTO rule_values(ruleset_id,rule_name,rule_value) VALUES(1,'Items:FreeTrade','true');\")")
s=s.replace("    before=None", "    assert policy_rows()==[], 'FreeTrade rule changed since preflight'\n    before=None;content=None;rule_inserted=False")
s=s.replace("VALUES(1,'Items:FreeTrade','true');\")", "VALUES(1,'Items:FreeTrade','true');\")\n        rule_inserted=True")
s=s.replace("first=running(p['new_image_id'],m['binaries']);time.sleep(5);", "cache=verify_cache();save('hosted-cache.json',cache)\n        first=running(p['new_image_id'],m['binaries']);time.sleep(5);")
s=s.replace("assert player_data()==before,'Player/receipt/settings data changed while gateway closed';untouched(p)", "assert player_data()==before,'Player/receipt/settings data changed while gateway closed'\n        assert content_data()==content,'Content data drift';assert policy_rows()==['1\\ttrue'];untouched(p)")
s=s.replace("'database_restored':False,'gateway_open':True", "'database_restored':False,'gateway_open':True,'cache':cache,'content_preserved':content,'backup':p['backup']")
s=s.replace("select(m['old_image_id']);compose", "if rule_inserted:\n                assert policy_rows()==['1\\ttrue'], 'Owned rule changed; preserve it for investigation'\n                sql(\"DELETE FROM rule_values WHERE ruleset_id=1 AND rule_name='Items:FreeTrade' AND rule_value='true';\")\n            select(m['old_image_id']);compose")
s=s.replace("if before is not None:assert player_data()==before", "if before is not None:assert player_data()==before\n            if content is not None:assert content_data()==content\n            assert policy_rows()==[]\n            assert old_cache_valid(), 'Old-format cache was not restored'")
s=s.replace("print(json.dumps({'deployment':load('activated.json')", "assert policy_rows()==['1\\ttrue'];cache=verify_cache()\n    print(json.dumps({'cache':cache,'deployment':load('activated.json')")
extras='''
def policy_rows():
    return sql("SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='Items:FreeTrade' ORDER BY ruleset_id;").splitlines()

def content_data():
    rows=sql('CHECKSUM TABLE items EXTENDED; CHECKSUM TABLE spells_new EXTENDED; CHECKSUM TABLE npc_types EXTENDED; CHECKSUM TABLE spawn2 EXTENDED; CHECKSUM TABLE merchantlist EXTENDED;').splitlines()
    result=dict(row.split('\\t') for row in rows)
    assert len(result)==5 and all(v.isdigit() for v in result.values()), 'Missing content checksum'
    return result

def database_backup():
    directory=STAGE/'private-backup';directory.mkdir(mode=0o700)
    path=directory/'peq-before.sql.gz'
    cmd=['docker','compose','exec','-T','db','mariadb-dump','--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction','--routines','--events','--hex-blob','peq']
    with (directory/'dump.log').open('wb') as log:
        process=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
        with gzip.open(path,'xb',compresslevel=1) as dest:shutil.copyfileobj(process.stdout,dest)
        process.stdout.close();assert process.wait(timeout=180)==0, 'Database backup failed; see private log'
    size=0;tail=b''
    with gzip.open(path,'rb') as source:
        while chunk:=source.read(1024*1024):size+=len(chunk);tail=(tail+chunk)[-4096:]
    assert size>1000000 and b'-- Dump completed on' in tail, 'Truncated database backup'
    return {'path':str(path),'sha256':sha(path),'compressed_bytes':path.stat().st_size,'uncompressed_bytes':size,'gzip_integrity':'passed'}

def cache_header():
    path=ROOT/'data/server/shared/items'
    with path.open('rb') as source:return struct.unpack('<IIII',source.read(16)),path.stat().st_size

def old_cache_valid():
    (payload,count,maximum,current),length=cache_header()
    # The preserved production ItemData has no eight-byte policy prefix.
    return current==maximum and payload+8==length and length==20+4*count+1324*maximum

def verify_cache():
    assert policy_rows()==['1\\ttrue'], 'FreeTrade rule not active'
    rows=sql('SELECT id,nodrop,notransfer,attuneable,fvnodrop,price FROM items ORDER BY id;').splitlines()
    path=ROOT/'data/server/shared/items'
    with path.open('rb') as source, mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as mem:
        payload,count,maximum,current=struct.unpack_from('<IIII',mem,0)
        # MemoryMappedFile adds sizeof({uint32 size; byte data[1];}) == 8,
        # but data starts at offset 4; the allocation has four trailing bytes.
        assert payload+8==len(mem) and current==maximum==len(rows)
        assert len(mem)==20+4*count+1332*maximum, 'Unexpected cache layout'
        start=16+4*count;fixed_count=0
        offsets={'ID':440,'FreeTrade':0,'FixedSellPrice':4,'NoDrop':449,'NoTransfer':800,'Attuneable':796,'FVNoDrop':472,'Price':456}
        for row in rows:
            item_id,nodrop,no_transfer,attune,fv,price=map(int,row.split('\\t'))
            assert item_id<count
            index=struct.unpack_from('<I',mem,16+item_id*4)[0];assert index<current
            base=start+index*1332
            def read(n,f):return struct.unpack_from(f,mem,base+offsets[n])[0]
            fixed=1000 if nodrop==0 else 0
            assert read('ID','<I')==item_id
            assert read('FreeTrade','<B')==1 and read('FixedSellPrice','<I')==fixed,item_id
            assert read('NoDrop','<B')==255 and read('NoTransfer','<B')==0,item_id
            assert read('Attuneable','<B')==0 and read('FVNoDrop','<B')==0,item_id
            assert read('Price','<I')==max(price,fixed),item_id
            fixed_count+=bool(fixed)
        return {'items_checked':current,'fixed_payout_items':fixed_count,'all_items_tradable':True,'fixed_payout_copper':1000,'item_struct_bytes':1332,'cache_sha256':hashlib.sha256(mem).hexdigest(),'catalog_flags_sha256':hashlib.sha256('\\n'.join(rows).encode()).hexdigest()}

'''
s=s.replace("if __name__=='__main__':",extras+"if __name__=='__main__':")
(r/'rollout.py').write_text(s)
t=(r.parent/'blessing-lifetime-20261004/test_rollout.py').read_text().replace('two-binary rollout','five-binary and cache rollout')
t=t.replace("'runtime':{}}", "'runtime':{},'backup':{'verified':True}}")
t=t.replace("self.ports_changed=False", "self.ports_changed=False;self.rule=fault=='rule-drift';self.rule_deleted=False")
t=t.replace("'image_hashes':lambda i:self.m['old_hashes']}", "'image_hashes':lambda i:self.m['old_hashes'],'content_data':self.content,'policy_rows':lambda:['1\\ttrue'] if self.rule else [],'verify_cache':self.cache,'old_cache_valid':lambda:True,'sql':self.sql}")
t=t.replace("    def closed_ports(self):", "    def sql(self,q):\n        if q.startswith('INSERT'):\n            if self.fault=='insert':raise RuntimeError('Injected insert failure')\n            assert not self.rule;self.rule=True\n        elif q.startswith('DELETE'):\n            assert \"ruleset_id=1\" in q and \"rule_value='true'\" in q\n            self.rule=False;self.rule_deleted=True\n        return ''\n    def content(self):\n        if self.fault=='content':raise RuntimeError('Injected checksum capture failure')\n        return {'items':'same'}\n    def closed_ports(self):")
t=t.replace("    def closed_ports(self):", "    def cache(self):\n        if self.fault=='cache':raise RuntimeError('Injected cache mismatch')\n        return {'items_checked':300000}\n    def closed_ports(self):")
t=t.replace("('start','health','gateway')", "('start','health','gateway','cache','insert','content')")
t=t.replace("    def test_success_preserves_data_before_open(self):", "    def test_rule_drift_rejected_without_services_or_sql_changes(self):\n        s=Scenario('rule-drift')\n        with self.assertRaises(AssertionError):s.run()\n        self.assertTrue(s.rule and s.game_on and s.gateway_on)\n        self.assertFalse(s.rule_deleted);self.assertEqual(s.events,[])\n    def test_insert_failure_never_deletes_unowned_rule(self):\n        s=Scenario('insert')\n        with self.assertRaises(RuntimeError):s.run()\n        self.assertFalse(s.rule_deleted);self.assertTrue(s.gateway_on)\n    def test_success_preserves_data_before_open(self):")
(r/'test_rollout.py').write_text(t)
print('Prepared rollout and fault tests')
