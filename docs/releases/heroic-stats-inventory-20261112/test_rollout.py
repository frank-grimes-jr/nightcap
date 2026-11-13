"""Authenticate release binding and refuse mismatched paired client publication."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock,patch


class InventoryRollout(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('inventory_rollout',Path(__file__).with_name('rollout.py'))
        self.mod=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fcntl':types.SimpleNamespace()}):spec.loader.exec_module(self.mod)
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        m=self.mod;m.STAGE=Path(tmp.name);m.PRIOR=m.STAGE/'prior.py';m.PRIOR.write_text('pinned')
        data={'bin/zone':b'native','client/channel.json':b'signed','client/previous-channel.json':b'old'}
        data.update({'source/'+name:('reviewed '+name).encode() for name in m.SOURCE_DELTA})
        for name,value in data.items():
            p=m.STAGE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
        self.proof={'status':'PASS','baseline_reproduced':True,'source_delta':m.SOURCE_DELTA[:],
            'binary_sha256':{'baseline':'old','candidate':m.sha(m.STAGE/'bin/zone')},
            'source_sha256':{n:m.sha(m.STAGE/'source'/n) for n in m.SOURCE_DELTA}}
        self.signed={'release':2026111202,'changed_assets':3,'previous_channel_sha256':'client-old',
            'channel_sha256':m.sha(m.STAGE/'client/channel.json')}
        self.manifest={'owner_authorization':m.AUTHORIZATION,'prior_operator_sha256':m.sha(m.PRIOR),
            'base_image_id':'old-image','base_hashes':{'bin/zone':'old'},
            'binaries':{'zone':self.proof['binary_sha256']['candidate']},'client_release':2026111202,'client_channel_sha256':'client-old'}
        self.prior=types.SimpleNamespace(r=Mock(),m={'client_channel_sha256':'client-old'})
        self.prior.r.image_hashes.return_value={'bin/zone':'old'}
        parent=types.SimpleNamespace(initialize=Mock(return_value=self.prior))
        a=patch.object(m.importlib.util,'module_from_spec',return_value=parent);a.start();self.addCleanup(a.stop)
        a=patch.object(m.importlib.util,'spec_from_file_location',return_value=Mock());a.start();self.addCleanup(a.stop)
        self.persist()

    def persist(self):
        m=self.mod
        for name,value in [('native-build.json',self.proof),('client/verification.json',self.signed),('review.json',{'status':'PASS'})]:
            (m.STAGE/name).write_text(json.dumps(value))
        (m.STAGE/'release-checks.json').write_text(json.dumps({'status':'PASS','native_build_sha256':m.sha(m.STAGE/'native-build.json')}))
        self.manifest['files']={p.relative_to(m.STAGE).as_posix():m.sha(p) for p in m.STAGE.rglob('*') if p.is_file() and p.name not in ('prior.py','manifest.json')}
        (m.STAGE/'manifest.json').write_text(json.dumps(self.manifest))

    def test_binds_current_native_pair_and_retains_existing_operator(self):
        p=self.mod.initialize();self.assertIs(p,self.prior)
        self.assertEqual(p.STAGE,self.mod.STAGE);self.assertEqual(p.EVIDENCE,self.mod.STAGE/'evidence')
        self.assertEqual(p.m['base_hashes'],{'bin/zone':'old'})

    def test_refuses_payload_drift(self):
        (self.mod.STAGE/'bin/zone').write_bytes(b'drift')
        with self.assertRaises(AssertionError):self.mod.initialize()

    def test_refuses_unreviewed_source_addition(self):
        self.proof['source_delta']=self.proof['source_delta']+['zone/spells.cpp'];self.persist()
        with self.assertRaises(AssertionError):self.mod.initialize()

    def test_refuses_wrong_predecessor(self):
        self.prior.r.image_hashes.return_value={'bin/zone':'other'}
        with self.assertRaises(AssertionError):self.mod.initialize()

    def test_refuses_wrong_client_baseline(self):
        self.signed['previous_channel_sha256']='other';self.persist()
        with self.assertRaises(AssertionError):self.mod.initialize()

    def test_refuses_wrong_candidate_signature_receipt_pair(self):
        self.signed['channel_sha256']='other';self.persist()
        with self.assertRaises(AssertionError):self.mod.initialize()

    def test_refuses_modified_prior_operator(self):
        self.mod.PRIOR.write_text('other')
        with self.assertRaises(AssertionError):self.mod.initialize()

    def test_open_requires_hosted_signature_verification(self):
        p=Mock();p.m={'files':{'client/channel.json':'new'}}
        p.read.side_effect=[{'channel_sha256':'new'},{'release':2026111202,'hosted':False}]
        with self.assertRaises(AssertionError):self.mod.open_access(p)
        p.open_access.assert_not_called()

    def test_open_requires_verification_of_exact_published_channel(self):
        p=Mock();p.m={'files':{'client/channel.json':'new'}}
        p.read.side_effect=[{'channel_sha256':'new'},{'release':2026111202,'hosted':True,'channel_sha256':'other'}]
        with self.assertRaises(AssertionError):self.mod.open_access(p)
        p.open_access.assert_not_called()
