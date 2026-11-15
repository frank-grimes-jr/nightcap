"""Stopped backup, title-data preservation and safe predecessor recovery controls."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest

spec=importlib.util.spec_from_file_location('automatic_title_release',Path(__file__).with_name('release.py'))
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


class Controls(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root=Path(temp.name);self.active=root/'activation';self.active.mkdir()
        self.running=False;self.exit=0;self.counter='42\t100\t1\n';self.backups=0
        self.checks=[]
        def backup():self.backups+=1;return dict(gzip_integrity=True,path='backup',sha256='hash')
        def unavailable():raise RuntimeError('Stopped world RPC is unavailable')
        self.op=NS(ACTIVE=self.active,EVIDENCE=root,prior=NS(sql=lambda q:self.counter if 'counters' in q else ''),
            title_state=lambda:self.checks.append('title-state'),sha=lambda p:'hash',read=lambda p:json.loads(p.read_bytes()),
            p=NS(unchanged=lambda before,**kwargs:self.checks.append('base-unchanged'),
                save=lambda p,v:p.write_text(json.dumps(v)),a=NS(prior=NS(players=unavailable))),
            r=NS(database_backup=backup,state=lambda n:{'State':dict(Running=self.running,ExitCode=self.exit,OOMKilled=False)},
                 compact=lambda n:dict(running=self.running if n=='game' else False)))
        release.install_guards(self.op)
    def test_clean_stop_needs_no_rpc(self):
        self.op.r.database_backup();self.assertEqual(self.backups,1)
        self.op.p.unchanged({})
        self.assertIn('title-state',self.checks)
    def test_running_game_blocks_backup(self):
        self.running=True
        with self.assertRaises(AssertionError):self.op.r.database_backup()
        self.assertEqual(self.backups,0)
    def test_dirty_stop_blocks_backup(self):
        self.exit=1
        with self.assertRaises(AssertionError):self.op.r.database_backup()
    def test_closed_title_data_drift_rejected(self):
        self.op.r.database_backup();self.counter='42\t100\t2\n'
        with self.assertRaises(AssertionError):self.op.p.unchanged({})
    def test_open_activity_preserves_control_but_allows_earning(self):
        self.op.r.database_backup();self.counter='42\t100\t2\n'
        self.op.p.unchanged({},after_open=True)
        self.assertEqual(self.checks[-1],'title-state')
    def test_backup_replay_rejected(self):
        self.op.r.database_backup()
        with self.assertRaises(AssertionError):self.op.r.database_backup()
        self.assertEqual(self.backups,1)
    def test_recovery_uses_original_backup_and_stopped_proof(self):
        self.op.r.database_backup()
        self.op.recover_closed=lambda:(self.assertEqual(self.op.p.a.prior.players(),0),self.op.r.database_backup())
        release.recover_closed(self.op);self.assertEqual(self.backups,2)
    def test_running_recovery_checks_actual_players(self):
        self.running=True;self.op.p.a.prior.players=lambda:1
        with self.assertRaises(AssertionError):release.recover_closed(self.op)
    def test_opening_cannot_recover(self):
        (self.active/'opening.json').write_text('{}')
        with self.assertRaises(AssertionError):release.recover_closed(self.op)
    def test_actual_prior_normalization_is_removed(self):
        # Execute the actual frozen migration wrapper, avoiding its Linux-only
        # CLI imports; this catches its late-bound new-EVIDENCE path hazard.
        path=Path(__file__).parents[1]/'deployment-20261114/release-original.py'
        tree=ast.parse(path.read_text(encoding='utf8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='install_guards')
        old=self.active.parent/'old';old.mkdir()
        self.op.prior.sql=lambda q:''
        self.op.read=lambda p: [] if p.name=='commands-before.json' else ({'content':{'command_settings/all':'old-normalized'}} if p.name=='preflight.json' else {})
        self.op.p.a.content=lambda:{'command_settings/all':'actual-full-hash'}
        self.op.p.base=NS(saved_state=lambda:{'old':'saved'})
        schema=NS(TABLES=(),require_installed=lambda *args:None,commands=lambda sql:[],without_title=lambda rows:rows)
        namespace=dict(STAGE=old,Path=Path)
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
        namespace['install_guards'](self.op,schema)
        (self.active/'titles-sql-installed.json').write_text('{}')
        self.assertEqual(self.op.p.a.content()['command_settings/all'],'old-normalized')
        release.restore_title_migration(self.op)
        self.op.EVIDENCE=self.active.parent/'new'
        self.assertEqual(self.op.p.a.content()['command_settings/all'],'actual-full-hash')


if __name__=='__main__':unittest.main()
