"""The continuation admits only its inspected pre-SQL stopped-world checkpoint."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest

spec=importlib.util.spec_from_file_location('title_resume',Path(__file__).with_name('resume.py'))
resume=importlib.util.module_from_spec(spec);spec.loader.exec_module(resume)


class Checkpoint(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        stage=Path(temp.name);resume.STAGE=stage;active=stage/'evidence/activation';active.mkdir(parents=True)
        self.active=active;self.running=False;self.saved={'old':'exact'}
        held=active/resume.HELD;held.write_text('{}');resume.HOLD_SHA=hashlib.sha256(held.read_bytes()).hexdigest()
        (stage/'manifest.json').write_text('{}')
        (active/'stopped-state.json').write_text(json.dumps(self.saved))
        (stage/'evidence/preflight.json').write_text(json.dumps({'manifest_sha256':resume.HOLD_SHA}))
        backup=active/'private-backup/peq-before.sql.gz';backup.parent.mkdir()
        with gzip.open(backup,'wb') as stream:stream.write(b'x'*1000001+b'-- Dump completed on')
        self.op=NS(ACTIVE=active,EVIDENCE=active.parent,m={'base_image_id':'old'},
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(),read=lambda p:json.loads(p.read_bytes()),title_state=lambda:None,
            r=NS(compact=lambda name:dict(running=self.running if name=='game' else False,image_id='old'),
                state=lambda name:{'State':dict(Running=self.running,ExitCode=0,OOMKilled=False)}),
            p=NS(a=NS(prior=NS(saved=lambda:self.saved)),unchanged=lambda before:None,startup=NS(startup_guards=lambda:None)))
    def test_exact_stopped_checkpoint_passes_without_rpc(self):resume.checkpoint(self.op)
    def test_running_game_rejected(self):
        self.running=True
        with self.assertRaises(AssertionError):resume.checkpoint(self.op)
    def test_saved_drift_rejected(self):
        self.saved={'old':'different'}
        with self.assertRaises(AssertionError):resume.checkpoint(self.op)
    def test_sql_started_rejected(self):
        (self.active/'titles-sql-started.json').write_text('{}')
        with self.assertRaises(AssertionError):resume.checkpoint(self.op)
    def test_other_hold_rejected(self):
        (self.active/'held-other.json').write_text('{}')
        with self.assertRaises(AssertionError):resume.checkpoint(self.op)
    def test_terminal_replay_rejected(self):
        (self.active/'resume-stopped-rpc').mkdir()
        with self.assertRaises(AssertionError):resume.checkpoint(self.op)
    def test_truncated_backup_rejected(self):
        with gzip.open(self.active/'private-backup/peq-before.sql.gz','wb') as stream:stream.write(b'truncated')
        with self.assertRaises(AssertionError):resume.checkpoint(self.op)


if __name__=='__main__':unittest.main()
