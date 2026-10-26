"""Actual C++ escrow engine against an isolated MariaDB schema.

Requires PyMySQL and the owner's local akk-stack DB. Credentials stay in memory.
Uses the cached MariaDB image in a disposable tmpfs container. Live peq supplies
inventory/currency column definitions only; no player rows are read or written.
"""
import concurrent.futures
import ctypes
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import unittest
import sys
import time

# Optional task-local dependency directory, outside the repository.
if os.environ.get('NIGHTCAP_TEST_DEPS'):
    sys.path.insert(0, os.environ['NIGHTCAP_TEST_DEPS'])
import pymysql

ROOT = Path(__file__).resolve().parents[2]
COMMITTED, REJECTED, UNCERTAIN = 1, 0, 2
POST, BUY, CANCEL, COLLECT = range(4)
COLUMNS = ['character_id','slot_id','item_id','charges','color','augment_one','augment_two',
           'augment_three','augment_four','augment_five','augment_six','instnodrop','custom_data',
           'ornament_icon','ornament_idfile','ornament_hero_model','guid']
SELECT = ','.join('HEX(COALESCE(custom_data,\'\'))' if c == 'custom_data' else c for c in COLUMNS)
TABLES = ['nightcap_bazaar_receipts','nightcap_bazaar_items','nightcap_bazaar_listings',
          'nightcap_bazaar_credits','inventory','character_currency']

class WireReply(ctypes.Structure):
    _fields_ = [('ok',ctypes.c_int),('affected',ctypes.c_ulonglong),('id',ctypes.c_ulonglong),('rows',ctypes.c_char_p)]
CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.POINTER(WireReply))

class EscrowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='nightcap-bazaar-')
        out = Path(cls.temp.name)
        source = ROOT / 'tools/tests/bazaar_escrow_bridge.cpp'
        includes = ROOT / 'server-mods/code'
        if os.name == 'nt':
            cls.library = out / 'engine.dll'
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                f'cl /nologo /EHsc /W4 /std:c++17 /LD /I"{includes}" "{source}" /Fe:engine.dll >build.log 2>&1\nexit /b %errorlevel%\n')
            build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            if build.returncode:
                raise AssertionError((out/'build.log').read_text())
        else:
            cls.library = out / 'engine.so'
            subprocess.run(['c++','-std=c++17','-shared','-fPIC','-I',str(includes),str(source),'-o',str(cls.library)],check=True)
        cls.lib = ctypes.CDLL(str(cls.library))
        cls.lib.bazaar_run.argtypes = [CALLBACK]+[ctypes.c_uint]*5+[ctypes.c_int,ctypes.c_char_p,ctypes.c_char_p]
        cls.lib.bazaar_run.restype = ctypes.c_char_p
        cls.lib.bazaar_view.argtypes=[CALLBACK,ctypes.c_uint,ctypes.c_uint];cls.lib.bazaar_view.restype=ctypes.c_char_p
        cls.lib.bazaar_race_sql.argtypes=[ctypes.c_uint];cls.lib.bazaar_race_sql.restype=ctypes.c_char_p
        cls.lib.bazaar_effective_races.argtypes=[ctypes.c_uint]*5;cls.lib.bazaar_effective_races.restype=ctypes.c_uint
        inspected = subprocess.run(['docker','inspect','akk-stack-mariadb-1'],capture_output=True,text=True,check=True)
        env = dict(x.split('=',1) for x in json.loads(inspected.stdout)[0]['Config']['Env'] if '=' in x)
        password = env.get('MARIADB_ROOT_PASSWORD') or env.get('MYSQL_ROOT_PASSWORD')
        if not password: raise RuntimeError('Local test database credential unavailable')
        original = pymysql.connect(host='127.0.0.1',port=3307,user='root',password=password,autocommit=True)
        try:
            with original.cursor() as cur:
                definitions=[]
                for table in ['inventory','character_currency']:
                    cur.execute('SHOW CREATE TABLE peq.'+table)
                    definitions.append(cur.fetchone()[1])
        finally: original.close()
        # Local bind-mounted MariaDB cannot TRUNCATE fresh InnoDB tables (error
        # 194). Use the exact cached image with an ephemeral Linux tmpfs datadir.
        # This also keeps all test mutations outside the development database.
        cls.container='nightcap-bazaar-test-'+secrets.token_hex(5)
        secret=secrets.token_hex(24)
        envrun=os.environ.copy();envrun['MYSQL_ROOT_PASSWORD']=secret
        image=json.loads(inspected.stdout)[0]['Image']
        subprocess.run(['docker','run','--detach','--rm','--name',cls.container,'--tmpfs','/var/lib/mysql',
                        '--env','MYSQL_ROOT_PASSWORD','-p','127.0.0.1::3306',image],env=envrun,check=True,capture_output=True)
        cls.addClassCleanup(lambda: subprocess.run(['docker','stop',cls.container],capture_output=True,check=False))
        details=json.loads(subprocess.run(['docker','inspect',cls.container],capture_output=True,text=True,check=True).stdout)[0]
        port=int(details['NetworkSettings']['Ports']['3306/tcp'][0]['HostPort'])
        cls.settings=dict(host='127.0.0.1',port=port,user='root',password=secret,charset='utf8mb4',autocommit=True)
        cls.schema='nightcap_bazaar_test_'+secrets.token_hex(6)
        for attempt in range(60):
            try:
                cls.admin=pymysql.connect(**cls.settings)
                break
            except pymysql.MySQLError:
                if attempt==59:raise RuntimeError('Disposable MariaDB did not become ready') from None
                time.sleep(1)
        with cls.admin.cursor() as cur:
            cur.execute('CREATE DATABASE '+cls.schema)
            cur.execute('USE '+cls.schema)
            for definition in definitions: cur.execute(definition)
            migration = (ROOT/'server-mods/sql/2026-10-24-bazaar-escrow.sql').read_text()
            sql = '\n'.join(line for line in migration.splitlines() if not line.startswith('--'))
            for statement in sql.split(';'):
                if statement.strip(): cur.execute(statement)
        cls.settings['database'] = cls.schema

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,'admin'):
            with cls.admin.cursor() as cur:
                cur.execute('DROP DATABASE '+cls.schema)
            cls.admin.close()
        # DLL remains loaded until process exit on Windows. Keep TemporaryDirectory
        # cleanup from disguising test results with a locked-library error.
        if os.name == 'nt':
            import _ctypes
            _ctypes.FreeLibrary(cls.lib._handle)
        cls.temp.cleanup()

    def setUp(self):
        self.db = pymysql.connect(**self.settings)
        self.addCleanup(self.db.close)
        for table in TABLES: self.sql('TRUNCATE TABLE '+table)
        self.sql('UPDATE nightcap_bazaar_state SET enabled=1')
        for who in (1,2,3): self.sql('INSERT INTO character_currency(id,platinum) VALUES(%s,100)',(who,))
        self.errors=[]

    def sql(self,query,args=None):
        with self.db.cursor() as cur:
            cur.execute(query,args)
            return cur.fetchall()

    def item(self,who=1,charges=1,slot=33,item=1001,custom='tag^rare^',**fields):
        values=dict(character_id=who,slot_id=slot,item_id=item,charges=charges,color=123,augment_one=201,
                    instnodrop=1,custom_data=custom,ornament_icon=72,ornament_idfile=73,ornament_hero_model=-7,guid=123456)
        values.update(fields)
        self.sql('INSERT INTO inventory('+','.join(values)+') VALUES('+','.join(['%s']*len(values))+')',tuple(values.values()))
        return self.cursor(who)

    def cursor(self,who):
        return [[str(x) for x in row] for row in self.sql('SELECT '+SELECT+' FROM inventory WHERE character_id=%s ORDER BY slot_id',(who,))]

    def run_engine(self,op,who=1,listing=0,price=1000,quantity=1,stackable=False,wallet=(100,0,0,0),cursor=(),fault=None,db=None):
        connection = db or self.db
        buffers=[]; trace=[]; fired=False
        @CALLBACK
        def execute(raw,reply):
            nonlocal fired
            sql=raw.decode(); trace.append(sql)
            try:
                target = fault and not fired and fault[0] in sql
                if target: fired=True
                if target and fault[1]=='before': raise RuntimeError('injected failure')
                with connection.cursor() as cur:
                    affected=cur.execute(sql)
                    rows=cur.fetchall()
                    reply.contents.affected=affected
                    reply.contents.id=cur.lastrowid or 0
                if target and fault[1]=='after': raise RuntimeError('injected lost acknowledgment')
                text=''.join('\t'.join(str(x) for x in row)+'\n' for row in rows).encode()
                buffers.append(ctypes.create_string_buffer(text))
                reply.contents.rows=ctypes.cast(buffers[-1],ctypes.c_char_p)
                reply.contents.ok=1
            except Exception as e:
                self.errors.append((sql,type(e).__name__,str(e)))
                reply.contents.ok=0
        if op==4:
            raw=self.lib.bazaar_view(execute,who,listing)
            lines=raw.decode().splitlines();status,enabled,total,page,credit=map(int,lines[0].split('\t'))
            return dict(status=status,enabled=enabled,total=total,page=page,credit=credit,rows=[list(map(int,x.split('\t'))) for x in lines[1:]],trace=trace,fired=fired)
        raw=self.lib.bazaar_run(execute,op,who,listing,price,quantity,int(stackable),
             '\t'.join(map(str,wallet)).encode(),''.join('\t'.join(row)+'\n' for row in cursor).encode())
        lines=raw.decode().splitlines()
        status,identity,*money=map(int,lines[0].split('\t'))
        return dict(status=status,id=identity,wallet=money,items=[line.split('\t') for line in lines[1:]],trace=trace,fired=fired)

    def post(self,**kwargs):
        cursor=kwargs.pop('cursor',None)
        if cursor is None: cursor=self.item(charges=kwargs.get('quantity',1))
        result=self.run_engine(POST,cursor=cursor,**kwargs)
        self.assertEqual(result['status'],COMMITTED,self.errors)
        return result['id']

    def snapshot(self):
        return {t:self.sql('SELECT * FROM '+t+' ORDER BY 1,2') for t in TABLES}

    def test_panel_view_is_owner_scoped_paged_and_non_mutating(self):
        ids=[self.post() for _ in range(10)]
        self.post(who=2,cursor=self.item(who=2))
        self.sql('INSERT INTO nightcap_bazaar_credits VALUES(1,1234)')
        before=self.snapshot();view=self.run_engine(4)
        self.assertEqual((view['status'],view['total'],view['page'],view['credit']),(COMMITTED,10,0,1234))
        self.assertEqual([r[0] for r in view['rows']],ids[:8])
        page=self.run_engine(4,listing=12)
        self.assertEqual(page['page'],1);self.assertEqual([r[0] for r in page['rows']],ids[8:])
        self.assertEqual(self.snapshot(),before);self.assertEqual(self.sql('SELECT @@in_transaction'),((0,),))

    def test_panel_disabled_market_still_exposes_recoverable_ownership(self):
        listing=self.post();self.sql('UPDATE nightcap_bazaar_state SET enabled=0')
        view=self.run_engine(4);self.assertEqual(view['status'],COMMITTED);self.assertFalse(view['enabled'])
        self.assertEqual(view['rows'][0][0],listing)
        self.assertEqual(self.run_engine(4,who=3)['rows'],[])

    def test_panel_read_failures_never_leak_partial_snapshot_or_leave_locks(self):
        self.post();before=self.snapshot();healthy=self.run_engine(4)
        for query in healthy['trace']:
            with self.subTest(query=query):
                out=self.run_engine(4,fault=(query,'before'))
                self.assertNotEqual(out['status'],COMMITTED);self.assertEqual(out['rows'],[])
                self.assertEqual(self.snapshot(),before)
                self.sql('ROLLBACK')
        out=self.run_engine(4,fault=('ROLLBACK','after'))
        self.assertEqual(out['status'],UNCERTAIN);self.assertEqual(out['rows'],[])

    def test_disabled_post_preserves_item(self):
        cursor=self.item(); self.sql('UPDATE nightcap_bazaar_state SET enabled=0'); before=self.snapshot()
        self.assertEqual(self.run_engine(POST,cursor=cursor)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_offline_seller_exact_instance_and_collection(self):
        original=self.item(); listing=self.post(cursor=original)
        self.assertEqual(self.cursor(1),[])
        self.assertEqual(self.sql('SELECT platinum FROM character_currency WHERE id=1'),((100,),))
        bought=self.run_engine(BUY,who=2,listing=listing)
        self.assertEqual(bought['status'],COMMITTED,self.errors)
        expected=[list(original[0])]; expected[0][0]='2'
        self.assertEqual(self.cursor(2),expected)
        self.assertEqual(self.sql('SELECT copper FROM nightcap_bazaar_credits WHERE character_id=1'),((1000,),))
        self.assertEqual(self.sql('SELECT platinum FROM character_currency WHERE id=1'),((100,),))
        self.assertEqual(self.run_engine(COLLECT)['wallet'],[101,0,0,0])
        self.assertEqual(self.run_engine(COLLECT,wallet=(101,0,0,0))['status'],REJECTED)

    def test_partial_stack_and_cancel_remainder(self):
        listing=self.post(quantity=20,stackable=True,price=1200)
        bought=self.run_engine(BUY,who=2,listing=listing,price=1200,quantity=7)
        self.assertEqual(bought['status'],COMMITTED,self.errors)
        self.assertEqual(self.cursor(2)[0][3],'7')
        self.assertEqual(bought['wallet'],[91,6,0,0])
        self.sql('UPDATE nightcap_bazaar_state SET enabled=0')
        cancelled=self.run_engine(CANCEL,listing=listing)
        self.assertEqual(cancelled['status'],COMMITTED,self.errors)
        self.assertEqual(self.cursor(1)[0][3],'13')
        self.assertEqual(self.run_engine(COLLECT)['wallet'],[108,4,0,0])

    def test_bag_rows_and_binary_custom_data_preserved(self):
        self.item(custom='quote\'\nslash\\tab\t',augment_one=0)
        self.item(slot=6010,item=1002,charges=9,custom='child^yes^')
        original=self.cursor(1); listing=self.post(cursor=original)
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing)['status'],COMMITTED,self.errors)
        for row in original: row[0]='2'
        self.assertEqual(self.cursor(2),original)

    def test_wrong_owner_cannot_cancel_or_buy_self(self):
        listing=self.post(); before=self.snapshot()
        self.assertEqual(self.run_engine(CANCEL,who=2,listing=listing)['status'],REJECTED)
        self.assertEqual(self.run_engine(BUY,listing=listing)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_stale_wallet_rolls_back_delivery_credit_and_listing(self):
        listing=self.post(); self.sql('UPDATE character_currency SET platinum=99 WHERE id=2'); before=self.snapshot()
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_stale_price_quantity_and_missing_listing(self):
        listing=self.post(); before=self.snapshot()
        for changes in [dict(price=1001),dict(quantity=2),dict(quantity=0),dict(listing=listing+1)]:
            args=dict(who=2,listing=listing);args.update(changes)
            self.assertEqual(self.run_engine(BUY,**args)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_stale_instance_rejected_but_regenerated_runtime_guid_allowed(self):
        cursor=self.item(); cursor[0][16]='888888'
        bad=[list(cursor[0])];bad[0][5]='202'
        self.assertEqual(self.run_engine(POST,cursor=bad)['status'],REJECTED)
        listing=self.post(cursor=cursor)
        self.assertEqual(self.sql('SELECT guid FROM nightcap_bazaar_items WHERE listing_id=%s',(listing,)),((123456,),))

    def test_cursor_queue_or_destination_blocks_without_loss(self):
        listing=self.post(); self.item(who=2,slot=6011)
        before=self.snapshot()
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_two_buyers_only_one_commits(self):
        listing=self.post()
        def buy(who):
            connection=pymysql.connect(**self.settings)
            try:return self.run_engine(BUY,who=who,listing=listing,db=connection)['status']
            finally:connection.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(buy,(2,3)))
        self.assertEqual(sorted(outcomes),[REJECTED,COMMITTED],self.errors)
        self.assertEqual(self.sql('SELECT SUM(copper) FROM nightcap_bazaar_credits'),((1000,),))
        self.assertEqual(self.sql('SELECT COUNT(*) FROM inventory'),((1,),))

    def test_cancel_races_purchase_only_one_owner(self):
        listing=self.post()
        def run(op):
            connection=pymysql.connect(**self.settings)
            try:return self.run_engine(op,who=1 if op==CANCEL else 2,listing=listing,db=connection)['status']
            finally:connection.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(run,(BUY,CANCEL)))
        self.assertEqual(sorted(outcomes),[REJECTED,COMMITTED],self.errors)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM inventory'),((1,),))

    def test_lost_commit_acknowledgment_never_replays_item(self):
        listing=self.post()
        result=self.run_engine(BUY,who=2,listing=listing,fault=('COMMIT','after'))
        self.assertTrue(result['fired']);self.assertEqual(result['status'],UNCERTAIN)
        self.assertEqual(len(self.cursor(2)),1)
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing,wallet=(99,0,0,0))['status'],REJECTED)
        self.assertEqual(self.sql('SELECT copper FROM nightcap_bazaar_credits'),((1000,),))

    def test_failure_at_each_purchase_query_preserves_state(self):
        listing=self.post()
        probe=self.run_engine(BUY,who=2,listing=listing)
        self.assertEqual(probe['status'],COMMITTED)
        trace=probe['trace']
        for query in trace:
            if query=='SELECT @@in_transaction' or query.startswith(('SHOW COLUMNS','SELECT COUNT(*) FROM information_schema')):continue
            with self.subTest(query=query):
                self.setUp();listing=self.post();before=self.snapshot()
                result=self.run_engine(BUY,who=2,listing=listing,fault=(query,'before'))
                self.assertTrue(result['fired'],query)
                self.assertEqual(result['status'],UNCERTAIN)
                self.assertEqual(self.snapshot(),before)
                self.assertEqual(result['trace'][-1],'ROLLBACK')

    def test_partial_collection_preserves_credit_above_wallet_capacity(self):
        self.sql('INSERT INTO nightcap_bazaar_credits VALUES(1,5000)')
        self.sql('UPDATE character_currency SET platinum=2147483647,copper=998 WHERE id=1')
        result=self.run_engine(COLLECT,wallet=(2147483647,0,0,998))
        self.assertEqual(result['status'],COMMITTED,self.errors)
        self.assertEqual(result['wallet'],[2147483647,9,9,9])
        self.assertEqual(self.sql('SELECT copper FROM nightcap_bazaar_credits'),((4999,),))

    def test_schema_trigger_prevents_transaction(self):
        cursor=self.item()
        self.sql("CREATE TRIGGER bazaar_bad BEFORE INSERT ON nightcap_bazaar_receipts FOR EACH ROW SET NEW.copper=0")
        try:
            before=self.snapshot()
            result=self.run_engine(POST,cursor=cursor)
            self.assertEqual(result['status'],REJECTED)
            self.assertNotIn('START TRANSACTION',result['trace'])
            self.assertEqual(self.snapshot(),before)
        finally:self.sql('DROP TRIGGER bazaar_bad')

    def test_nontransactional_table_prevents_transaction(self):
        cursor=self.item()
        self.sql('ALTER TABLE nightcap_bazaar_receipts ENGINE=MyISAM')
        try:
            result=self.run_engine(POST,cursor=cursor)
            self.assertEqual(result['status'],REJECTED)
            self.assertNotIn('START TRANSACTION',result['trace'])
            self.assertEqual(self.cursor(1),cursor)
        finally:self.sql('ALTER TABLE nightcap_bazaar_receipts ENGINE=InnoDB')

    def test_disabled_market_rejects_buy_but_allows_recovery(self):
        listing=self.post();self.sql('UPDATE nightcap_bazaar_state SET enabled=0')
        before=self.snapshot()
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(self.run_engine(CANCEL,listing=listing)['status'],COMMITTED)

    def test_insufficient_funds_and_credit_overflow_preserve_ownership(self):
        listing=self.post(price=101000);before=self.snapshot()
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing,price=101000)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)
        self.sql('UPDATE nightcap_bazaar_listings SET unit_price=1000')
        self.sql('INSERT INTO nightcap_bazaar_credits VALUES(1,9223372036854775807)')
        before=self.snapshot()
        self.assertEqual(self.run_engine(BUY,who=2,listing=listing)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_listing_limit_has_no_item_loss(self):
        for i in range(100):
            self.sql('INSERT INTO nightcap_bazaar_listings(seller_id,unit_price,quantity,remaining,stackable) VALUES(1,1000,1,1,0)')
        cursor=self.item();before=self.snapshot()
        self.assertEqual(self.run_engine(POST,cursor=cursor)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

    def test_reconnect_after_post_can_buy_and_collect(self):
        listing=self.post()
        other=pymysql.connect(**self.settings)
        try:
            self.assertEqual(self.run_engine(BUY,who=2,listing=listing,db=other)['status'],COMMITTED)
        finally:other.close()
        other=pymysql.connect(**self.settings)
        try:
            self.assertEqual(self.run_engine(COLLECT,db=other)['status'],COMMITTED)
        finally:other.close()

    def test_search_race_projection_matches_actual_cache_policy(self):
        # Includes raw Bronze Knuckles mask62219 and non-player/zero sentinels.
        cases=[(62219,65535,4096,0,0),(1,1,0,1,0),(1,1,0,0,0),(0,1,4096,0,0),
               (1,0,4096,0,0),(1,1,4096,0,1),(65536,1,4096,0,0),(1,1,1<<23,0,0)]
        for races,classes,slots,augtype,itemclass in cases:
            effective=self.lib.bazaar_effective_races(races,classes,slots,augtype,itemclass)
            for race in range(16):
                bit=1<<race
                predicate=self.lib.bazaar_race_sql(bit).decode()
                result=self.sql('SELECT COUNT(*) FROM (SELECT %s AS races,%s AS classes,%s AS slots,%s AS augtype,%s AS itemclass) items WHERE TRUE'+predicate,
                                (races,classes,slots,augtype,itemclass))[0][0]
                self.assertEqual(bool(result),bool(effective&bit),(cases,race))

    def test_price_and_stack_wire_overflow_rejected(self):
        cursor=self.item(charges=2);before=self.snapshot()
        self.assertEqual(self.run_engine(POST,price=4294967295,quantity=2,stackable=True,cursor=cursor)['status'],REJECTED)
        self.assertEqual(self.snapshot(),before)

if __name__=='__main__':unittest.main(verbosity=2)
