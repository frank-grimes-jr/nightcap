"""Fault controls for the production migration boundary; no remote access."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('titles_release_under_test',Path(__file__).with_name('release.py'))
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        release.STAGE=Path(self.temp.name);self.active=release.STAGE/'evidence/activation';self.active.mkdir(parents=True)
        self.commands=[dict(command='who',access=0,aliases='')]
        self.installed=False;self.running=False;self.players=0;self.backups=0;self.fail=False;self.enabled=1;self.activity=0
        self.schema=NS(TABLES=('nightcap_title_settings','nightcap_title_counters','nightcap_title_awards'),
            require_uninstalled=self.absent,require_installed=self.present,commands=lambda sql:self.commands,
            without_title=lambda rows:[r for r in rows if r['command']!='titles'],install=self.install)
        self.schema.structure=lambda sql:{}
        self.schema.settings=lambda sql:[dict(id=1,catalog_version=1,enabled=self.enabled)]
        (release.STAGE/'setup.sql').write_text('fixture')
        values={'schema-expected.json':{},'commands-before.json':self.commands,
                'preflight.json':{'content':{'command_settings/all':'old'}}}
        self.op=NS(ACTIVE=self.active,EVIDENCE=self.active.parent,m={'source_revision':'fixture'},
            prior=NS(sql=self.sql),read=lambda p:values[p.name],sha=lambda p:'backup-hash',
            p=NS(a=NS(content=lambda:{'command_settings/all':'new' if self.installed else 'old','other':'same'},prior=NS(players=lambda:self.players)),
                 base=NS(saved_state=lambda:{'old-player-state':'same','nightcap_title_awards':'new'}),
                 save=lambda p,v:p.write_text(json.dumps(v))),
            r=NS(database_backup=self.backup,compact=lambda n:{'running':self.running},
                 state=lambda n:{'State':{'Running':self.running,'ExitCode':0,'OOMKilled':False}}))
        release.install_guards(self.op,self.schema)

    def absent(self,sql):self.assertFalse(self.installed)
    def sql(self,q):
        if q.startswith('UPDATE nightcap_title_settings'):self.enabled=0;return '1'
        if q.startswith('DELETE FROM command_settings'):self.commands=self.schema.without_title(self.commands);return '1'
        if 'COUNT(*) FROM nightcap_title_' in q:return str(self.activity)
        if 'COUNT(*) FROM titles' in q:return '0'
        raise AssertionError(q)
    def present(self,sql,expected,enabled):self.assertTrue(self.installed);self.assertEqual(enabled,1)
    def backup(self):
        self.backups+=1
        return dict(gzip_integrity=True,path='fixture',sha256='backup-hash')
    def install(self,*args):
        self.assertEqual(self.backups,1);self.assertTrue((self.active/'titles-sql-started.json').exists())
        self.installed=True
        if self.fail:raise RuntimeError('uncertain SQL')
        self.commands=self.commands+[dict(command='titles',access=0,aliases='')]
    def test_install_after_verified_stopped_backup(self):
        self.op.r.database_backup();self.assertTrue(self.installed);self.op.title_state()
        self.assertEqual(self.op.p.a.content(),{'command_settings/all':'old','other':'same'})
    def test_old_saved_state_preserved(self):
        self.assertEqual(self.op.p.base.saved_state(),{'old-player-state':'same'})
    def test_running_game_blocks_write(self):
        self.running=True
        with self.assertRaises(AssertionError):self.op.r.database_backup()
        self.assertFalse(self.installed)
    def test_stopped_world_needs_no_player_rpc(self):
        def offline():raise RuntimeError('Stopped world has no RPC')
        self.op.p.a.prior.players=offline
        self.op.r.database_backup();self.assertTrue(self.installed)
    def test_uncertain_install_blocks_replay(self):
        self.fail=True
        with self.assertRaises(RuntimeError):self.op.r.database_backup()
        with self.assertRaises(AssertionError):self.op.title_state()
        self.assertFalse((self.active/'titles-sql-installed.json').exists())
    def test_completed_install_blocks_replay(self):
        self.op.r.database_backup()
        with self.assertRaises((AssertionError,FileExistsError)):self.op.r.database_backup()
    def test_unrelated_command_drift_blocks_normalization(self):
        self.op.r.database_backup();self.commands[0]=dict(command='who',access=255,aliases='')
        with self.assertRaises(AssertionError):self.op.p.a.content()
    def prepare_recovery(self):
        self.op.r.database_backup()
        (self.active/'started.json').write_text('{}')
        self.op.recover_closed=lambda:self.op.r.database_backup()
    def test_recovery_uses_fresh_backup_without_install(self):
        self.prepare_recovery();release.recover_closed(self.op)
        self.assertEqual(self.backups,2);self.assertTrue(self.installed);self.assertEqual(self.enabled,0)
        self.op.title_state();self.assertEqual(self.commands,[dict(command='who',access=0,aliases='')])
        with self.assertRaises(AssertionError):release.recover_closed(self.op)
    def test_recovery_rejects_player_activity(self):
        self.prepare_recovery();self.activity=1
        with self.assertRaises(AssertionError):release.recover_closed(self.op)
        self.assertEqual(self.enabled,1)
    def test_recovery_rejects_opening_boundary(self):
        self.prepare_recovery();(self.active/'opening.json').write_text('{}')
        with self.assertRaises(AssertionError):release.recover_closed(self.op)
        self.assertEqual(self.enabled,1)
    def test_recovery_stopped_world_needs_no_rpc(self):
        self.prepare_recovery()
        def offline():raise RuntimeError('Stopped world has no RPC')
        self.op.p.a.prior.players=offline
        self.op.recover_closed=lambda:self.assertEqual(self.op.p.a.prior.players(),0)
        release.recover_closed(self.op)
        self.assertIs(self.op.p.a.prior.players,offline)
    def test_recovery_running_world_still_checks_rpc(self):
        self.prepare_recovery();self.running=True;self.players=1
        # The gateway remains closed independently of the running game.
        self.op.r.compact=lambda n:{'running':n=='game'}
        with self.assertRaises(AssertionError):release.recover_closed(self.op)
        self.assertEqual(self.enabled,1)


if __name__=='__main__':unittest.main()
