"""Operator boundary tests. No Docker, database, network or production writes.

Execute actual release functions with a stateful transport fixture. These tests
prove ordering/guards; SQL execution and native startup remain separate checks.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('rollout.py')

class Fixture:
    def __init__(self, root):
        spec = importlib.util.spec_from_file_location('aa_release_under_test', SOURCE)
        self.op = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'fcntl': types.SimpleNamespace()}):
            spec.loader.exec_module(self.op)
        o = self.op
        o.STAGE = root/'stage'; o.STAGE.mkdir()
        o.ROOT = root/'production'; o.ROOT.mkdir()
        o.EVIDENCE = o.STAGE/'evidence'; o.EVIDENCE.mkdir()
        (o.STAGE/'manifest.json').write_text('{}')
        (o.STAGE/'bin').mkdir()
        self.events = []; self.fail = None; self.held = False
        self.rows = [[1,'AA:ExpPerPoint','1000000','old cost'],
                     [1,'AA:PassiveExpPercent','10','passive'],
                     [1,'Character:AAExpMinLevel','1','minimum'],
                     [1,'Character:MaxLevel','50','era'],
                     [1,'Character:MaxExpLevel','50','era xp'],
                     [1,'AA:NormalizedAAEnabled','false','legacy'],
                     [1,'AA:ModernAAScalingEnabled','false','legacy'],
                     [2,'Unrelated:Value','keep','unaltered notes']]
        self.rows.sort()
        self.data = {'character_data':'player-current', 'character_alternate_abilities':'earned',
                     'inventory':'current-inventory', 'zone_state_spawns':{'rows':3,'sha256':'cache'}}
        self.cache = {'items':'items-hash','spells':'spells-hash'}
        self.pub = {'channel.json':'existing-client'}; self.scripts = {'quests/test.lua':'existing-script'}
        self.public = {'items','rule_values','nightcap_dungeon_spawns'}
        self.content = {n:n+'-hash' for n in self.public-{'rule_values'}}
        self.dungeon = {'nightcap_dungeon_state':'full-dungeon-state-hash'}
        self.market_before = ['1','1','10','0','1','1','before']
        self.market_after = None
        self.services = {s:{'id':s,'image_id':'sha256:base','running':True,'oom_killed':False,
                           'health':'healthy','restarts':0,'started_at':'old-start'}
                         for s in ('game','gateway','db','web','tunnel')}
        self.selected = 'sha256:base'
        self.base_hashes = {'bin/'+n:'old-'+n for n in o.NAMES}
        self.replacements = {n:'new-'+n for n in ('world','zone','shared_memory')}
        self.binary_hashes = {n:self.replacements.get(n,'old-'+n) for n in o.NAMES}
        self.m = {'base_image_id':'sha256:base','base_hashes':self.base_hashes,
                  'binaries':self.binary_hashes,'replacement_binaries':self.replacements,
                  'replacement_bytes':300,'rules_before':copy.deepcopy(self.rows)}
        for n in self.replacements:(o.STAGE/'bin'/n).write_text(n)
        self.tags = {}
        self.p = {'manifest_sha256':o.sha(o.STAGE/'manifest.json'),
                  'services':copy.deepcopy(self.services),'runtime':copy.deepcopy(self.scripts),
                  'public':copy.deepcopy(self.pub),'caches':copy.deepcopy(self.cache),
                  'content':{**self.content,**self.dungeon},'before':copy.deepcopy(self.rows),
                  'after':o.desired(copy.deepcopy(self.rows)),'image':'sha256:candidate',
                  'dungeon_state':copy.deepcopy(self.dungeon)}
        o.manifest = lambda:self.m
        o.save = self.save; o.sql = self.sql; o.caches = lambda:copy.deepcopy(self.cache)
        o.contract = lambda:self.event('contract') or {'schema':39,'content':499}
        o.r = types.SimpleNamespace(compact=self.compact,runtime=lambda:copy.deepcopy(self.scripts),
            public=lambda:copy.deepcopy(self.pub),compose=self.compose,state=self.state,
            database_backup=self.backup,select=self.select,running=self.running,
            closed_ports=lambda:self.event('closed_ports'),call=self.call,out=self.out,
            image_hashes=self.image_hashes)
        o.base = types.SimpleNamespace(PUBLIC=self.public,hashes=self.hashes,
            startup_guards=lambda:self.event('startup_guards'),saved_state=lambda:copy.deepcopy(self.data),
            market=lambda:copy.deepcopy(self.market_before),boot_state=self.boot_state,
            verify_market=self.verify_market,health=lambda:self.event('health'),hold=self.hold)
        o.shutil = types.SimpleNamespace(disk_usage=lambda _:types.SimpleNamespace(free=10*1024**3))
        o.time = types.SimpleNamespace(sleep=lambda _:None)
        self.save('preflight.json',self.p)

    def event(self, name):
        self.events.append(name)
        if self.fail == name:raise RuntimeError('injected '+name)

    def save(self, name, value):
        with (self.op.EVIDENCE/name).open('x') as f:json.dump(value,f)

    def hashes(self, tables):
        return {n:self.dungeon[n] if n in self.dungeon else self.content[n] for n in sorted(tables)}

    def sql(self, query, *args):
        if 'SELECT JSON_ARRAY(ruleset_id,rule_name,rule_value,notes)' in query:
            return '\n'.join(json.dumps(row) for row in self.rows)+'\n'
        if query.startswith('START TRANSACTION;'):
            self.event('rule_sql')
            assert not self.services['game']['running'] and not self.services['gateway']['running']
            assert (self.op.EVIDENCE/'backup.json').exists()
            self.rows = self.op.desired(self.rows)
            return ''
        if 'SELECT revision,enabled FROM nightcap_dungeon_state' in query:return '2026101601\t1\n'
        if 'information_schema.TRIGGERS' in query:return ''
        if 'SELECT ENGINE' in query:return 'InnoDB\n'
        if 'SELECT ruleset_id FROM rule_sets' in query:return '1\n'
        if 'SELECT name FROM rule_sets WHERE ruleset_id=1' in query:return 'default\n'
        if "SELECT value FROM variables WHERE varname='RuleSet'" in query:return ''
        raise AssertionError('Unmodeled SQL: '+query)

    def compact(self, service):return copy.deepcopy(self.services[service])

    def state(self, service):
        return {'State':{'Running':self.services[service]['running'],'ExitCode':0,'OOMKilled':False}}

    def compose(self, *args):
        service=args[-1]
        action='stop' if args[0]=='stop' else 'start'
        self.event(action+'_'+service)
        self.services[service]['running']=action=='start'
        if action=='start' and service=='game':
            self.services['game']['image_id']=self.selected
            self.services['game']['started_at']='new-start'
            self.market_after={'before':copy.deepcopy(self.market_before),'epoch':11}

    def backup(self):
        self.event('backup')
        assert not self.services['game']['running'] and not self.services['gateway']['running']
        return {'sha256':'fresh-backup','current_state':copy.deepcopy(self.data)}

    def select(self, image):self.event('select'); self.selected=image

    def running(self, image, binaries, *args):
        self.event('running')
        assert self.services['game']['running'] and self.services['game']['image_id']==image
        assert binaries==self.binary_hashes
        return {'image_id':image,'started_at':self.services['game']['started_at']}

    def boot_state(self, data):
        self.event('boot_state')
        expected=copy.deepcopy(data)
        self.save('expected-boot-state.json',expected)
        return expected

    def verify_market(self, before, started):
        self.event('verify_market')
        assert before==self.market_before and started=='new-start'
        return copy.deepcopy(self.market_after)

    def hold(self):
        self.events.append('hold');self.held=True
        self.services['gateway']['running']=self.services['game']['running']=False
        self.save('held-fixture.json',{'database_restored':False})

    def image_hashes(self, image):
        return self.base_hashes if image=='sha256:base' else {**self.base_hashes,**{'bin/'+n:h for n,h in self.replacements.items()}}

    def call(self, *args):
        self.events.append('call:'+':'.join(args[:3]))
        if args[:2]==('docker','tag'):
            self.tags[args[3]]=args[2]
        if args[:2]==('docker','build'):
            first=(self.op.STAGE/'Dockerfile').read_text().splitlines()[0]
            reference=first.removeprefix('FROM ')
            assert not reference.startswith('sha256:'),'Bare sha256 FROM repeats known BuildKit failure'
            assert self.tags[reference]=='sha256:base'

    def out(self, *args):
        if args[:3]==('docker','image','inspect'):
            image=args[-1]
            if '--format' in args:return self.tags.get(image,'sha256:candidate')+'\n'
            return json.dumps([{'RootFS':{'Layers':['baseline']+([] if image=='sha256:base' else ['candidate'])}}])
        if 'ldd' in args:return 'all dependencies found\n'
        raise AssertionError(args)

class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='aa-operator-')
        self.addCleanup(self.temp.cleanup)
        self.f=Fixture(Path(self.temp.name));self.o=self.f.op

    def test_desired_preserves_every_old_field_and_adds_one_exact_row(self):
        old=copy.deepcopy(self.f.rows); result=self.o.desired(old)
        self.assertEqual(old,self.f.rows)
        self.assertEqual([r for r in result if r[1]!=self.o.RULE],old)
        self.assertEqual([r for r in result if r[1]==self.o.RULE],[[1,self.o.RULE,'20',self.o.NOTES]])
        for ruleset in (1,2,10):
            with self.assertRaises(AssertionError):self.o.desired(old+[[ruleset,self.o.RULE,'0','unexpected']])

    def test_policy_rejects_changed_cost_passive_minimum_or_era(self):
        self.o.check_policy(self.f.rows)
        for name in ('AA:ExpPerPoint','AA:PassiveExpPercent','Character:AAExpMinLevel','Character:MaxLevel'):
            rows=copy.deepcopy(self.f.rows)
            next(r for r in rows if r[1]==name)[2]='unexpected'
            with self.assertRaises(AssertionError,msg=name):self.o.check_policy(rows)

    def test_database_guards_reject_engine_trigger_and_ruleset_drift(self):
        self.o.database_guards()
        original=self.o.sql
        for marker,bad in [('SELECT ENGINE','MyISAM\n'),('information_schema.TRIGGERS','new_trigger\n'),
                           ('SELECT name FROM rule_sets','other\n'),('SELECT value FROM variables','alternate\n')]:
            with self.subTest(marker=marker):
                self.o.sql=lambda q,m=marker,b=bad:b if m in q else original(q)
                with self.assertRaises(AssertionError):self.o.database_guards()
        self.o.sql=original

    def test_full_dungeon_state_drift_is_rejected(self):
        self.f.dungeon['nightcap_dungeon_state']='changed-unrelated-column'
        with self.assertRaisesRegex(AssertionError,'public content drift'):self.o.unchanged(self.f.p)

    def test_forward_sql_has_transactional_absence_and_affected_row_guards(self):
        q=self.o.forward_sql()
        self.assertTrue(q.startswith('START TRANSACTION;'))
        self.assertIn('CHECK(ok=1)',q)
        self.assertIn("SELECT COUNT(*)=0 FROM rule_values WHERE rule_name='"+self.o.RULE+"'",q)
        self.assertIn("VALUES(1,'"+self.o.RULE+"','20',CONVERT(0x"+self.o.NOTES.encode().hex(),q)
        self.assertLess(q.index('SELECT COUNT(*)=0'),q.index('INSERT INTO rule_values'))
        self.assertLess(q.index('SELECT ROW_COUNT()=1'),q.index('COMMIT;'))
        self.assertNotIn('DELETE ',q);self.assertNotIn('REPLACE ',q)

    def test_candidate_image_uses_authenticated_local_base_tag(self):
        self.assertEqual(self.o.build_image(self.f.m),'sha256:candidate')

    def test_activation_orders_stop_backup_rule_start_and_keeps_access_closed(self):
        self.o.activate()
        events=self.f.events
        chain=['stop_gateway','stop_game','backup','rule_sql','boot_state','select','start_game','verify_market']
        self.assertEqual(sorted(events.index(n) for n in chain),[events.index(n) for n in chain])
        self.assertNotIn('start_gateway',events)
        self.assertFalse(self.f.held)
        self.assertTrue((self.o.EVIDENCE/'verified-closed.json').exists())
        self.assertEqual(self.o.rules(),self.f.p['after'])

    def test_backup_failure_holds_before_rule_and_never_replays(self):
        self.f.fail='backup'
        with self.assertRaises(RuntimeError):self.o.activate()
        self.assertTrue(self.f.held)
        self.assertNotIn('rule_sql',self.f.events);self.assertNotIn('select',self.f.events)
        with self.assertRaises(AssertionError):self.o.activate()
        self.assertEqual(self.f.events.count('backup'),1)

    def test_rule_or_start_or_market_failure_never_reopens_or_restores(self):
        for failure in ('rule_sql','start_game','verify_market'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory(prefix='aa-fault-') as t:
                f=Fixture(Path(t));f.fail=failure
                with self.assertRaises(RuntimeError):f.op.activate()
                self.assertTrue(f.held)
                self.assertNotIn('start_gateway',f.events)
                self.assertFalse(f.services['game']['running'])
                self.assertEqual(f.data['character_alternate_abilities'],'earned')
                self.assertEqual(f.data['inventory'],'current-inventory')
                self.assertEqual(f.selected,'sha256:candidate' if failure in ('start_game','verify_market') else 'sha256:base')

    def test_boot_player_drift_holds_without_accepting_changed_state(self):
        original=self.f.running
        def running(*args):
            result=original(*args);self.f.data['character_data']='unexpected-write';return result
        self.o.r.running=running
        with self.assertRaisesRegex(AssertionError,'state drift'):self.o.activate()
        self.assertTrue(self.f.held);self.assertNotIn('start_gateway',self.f.events)
        self.assertEqual(self.f.data['character_data'],'unexpected-write')

    def test_open_rechecks_current_saved_state_before_gateway(self):
        self.o.activate();self.f.data['inventory']='new-drift'
        with self.assertRaises(AssertionError):self.o.open_access()
        self.assertTrue(self.f.held);self.assertNotIn('start_gateway',self.f.events)
        self.assertEqual(self.f.data['inventory'],'new-drift')

    def test_open_rejects_rule_cache_and_public_drift(self):
        for kind in ('rule','cache','public'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory(prefix='aa-open-') as t:
                f=Fixture(Path(t));f.op.activate()
                if kind=='rule':f.rows[0][3]='changed note'
                elif kind=='cache':f.cache['items']='changed'
                else:f.pub['channel.json']='different release'
                with self.assertRaises(AssertionError):f.op.open_access()
                self.assertNotIn('start_gateway',f.events);self.assertTrue(f.held)

    def test_separate_open_succeeds_once_and_records_no_restore(self):
        self.o.activate();self.o.open_access()
        receipt=self.o.read('deployed.json')
        self.assertTrue(receipt['gateway_open']);self.assertFalse(receipt['database_restored'])
        self.assertEqual(self.f.events.count('start_gateway'),1)
        with self.assertRaises(AssertionError):self.o.open_access()
        self.assertEqual(self.f.events.count('start_gateway'),1)

    def test_failed_gateway_open_holds_and_preserves_opening_receipt(self):
        self.o.activate();self.f.fail='start_gateway'
        with self.assertRaises(RuntimeError):self.o.open_access()
        self.assertTrue(self.f.held)
        self.assertTrue((self.o.EVIDENCE/'opening.json').exists())
        self.assertFalse((self.o.EVIDENCE/'deployed.json').exists())
        self.assertFalse(self.f.services['gateway']['running'])

    def test_existing_hold_blocks_open_without_replacing_receipts(self):
        self.o.activate();self.f.save('held-earlier.json',{'reason':'retain'})
        with self.assertRaises(AssertionError):self.o.open_access()
        self.assertNotIn('start_gateway',self.f.events)
        self.assertEqual(self.o.read('held-earlier.json'),{'reason':'retain'})

if __name__=='__main__':unittest.main()
