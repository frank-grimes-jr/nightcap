"""Native-cache preservation, full-row guards and release failure boundaries."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch
import rollout as op


class RolloutTests(unittest.TestCase):
    def test_only_exact_augment_cache_set_may_change(self):
        with patch.object(op,'rows',[{'before':{'id':'5'}},{'before':{'id':'9'}}],create=True):
            result=op.compare_cache({1:'x',5:'a',9:'b'},{1:'x',5:'c',9:'d'})
            self.assertEqual(result['changed_augments'],2)
            self.assertEqual(result['unrelated_preserved'],1)
            for after in ({1:'z',5:'c',9:'d'},{1:'x',5:'a',9:'d'},{1:'x',5:'c',9:'d',12:'z'}):
                with self.assertRaises(AssertionError):op.compare_cache({1:'x',5:'a',9:'b'},after)

    def test_exact_preimage_guards_use_indexable_identity(self):
        row={'id':'940024','Name':"Xorbb's Gem",'hp':'6','updated':'NULL'}
        predicate=op.predicate(row,'id')
        self.assertTrue(predicate.startswith('`id`=940024 AND '))
        self.assertIn('BINARY `Name` <=> X',predicate)
        self.assertIn('BINARY `updated` <=> NULL',predicate)

    def test_no_contract_check_is_skipped_and_override_binds_original_sql(self):
        catalog={'content':[{'label':'one','sql':'SELECT 1','expected':'1'},{'label':'two','sql':'SELECT 2','expected':'2'}]}
        with patch.object(op,'contract_data',return_value=catalog),patch.object(op,'sql',return_value='1\n2\n'):
            self.assertEqual(op.contract(),{'content':2})
        delta={'content/two':{'before':'2','after':'3','sql_sha256':op.hashlib.sha256(b'SELECT 2').hexdigest()}}
        with patch.object(op,'contract_data',return_value=catalog),patch.object(op,'sql',return_value='1\n3\n'):
            self.assertEqual(op.contract(delta),{'content':2})
            delta['content/two']['sql_sha256']='wrong'
            with self.assertRaises(AssertionError):op.contract(delta)
        with patch.object(op,'contract_data',return_value=catalog),patch.object(op,'sql',return_value='0\n2\n'):
            with self.assertRaises(AssertionError):op.contract()

    def test_drift_before_transition_never_stops_services(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);(folder/'preflight.json').write_text(json.dumps({'manifest_sha256':'pin'}))
            runtime=SimpleNamespace(compose=Mock())
            with patch.object(op,'EVIDENCE',folder),patch.object(op,'sha',return_value='pin'),patch.object(op,'r',runtime,create=True),patch.object(op,'unchanged',side_effect=AssertionError('drift')):
                with self.assertRaises(AssertionError):op.activate()
            runtime.compose.assert_not_called()
            self.assertFalse((folder/'activation').exists())

    def test_sql_failure_holds_access_without_selecting_or_opening(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);evidence=root/'evidence';evidence.mkdir();(root/'forward.sql').write_text('FAIL SQL')
            (evidence/'preflight.json').write_text(json.dumps({'manifest_sha256':'pin','services':{},'image':'new','content':{},'rules':[]}))
            runtime=SimpleNamespace(compose=Mock(),state=lambda _: {'State':{'Running':False,'ExitCode':0,'OOMKilled':False}},database_backup=lambda:{'backup':'verified'},select=Mock())
            base=SimpleNamespace(saved_state=lambda:{'inventory':'unchanged'},EVIDENCE=None)
            hold=Mock()
            with patch.object(op,'STAGE',root),patch.object(op,'EVIDENCE',evidence),patch.object(op,'sha',return_value='pin'),patch.object(op,'m',{'files':{'forward.sql':'pin'}},create=True),patch.object(op,'r',runtime,create=True),patch.object(op,'base',base,create=True),patch.object(op,'h',SimpleNamespace(hold=hold),create=True),patch.object(op,'market_ops',SimpleNamespace(market=lambda:{}),create=True),patch.object(op,'startup',SimpleNamespace(startup_guards=lambda:None),create=True),patch.object(op,'unchanged'),patch.object(op,'owned'),patch.object(op,'contract'),patch.object(op.shutil,'disk_usage',return_value=SimpleNamespace(free=10**12)),patch.object(op,'sql',side_effect=RuntimeError('injected SQL failure')):
                with self.assertRaises(RuntimeError):op.activate()
            runtime.select.assert_not_called();hold.assert_called_once()
            self.assertEqual(runtime.compose.call_args_list[0].args,('stop','gateway'))
            self.assertFalse((evidence/'activation/opening.json').exists())

    def test_open_rejects_any_held_activation(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);activation=folder/'activation';activation.mkdir()
            (folder/'preflight.json').write_text('{}');(activation/'verified-closed.json').write_text('{}');(activation/'held-one.json').write_text('{}')
            with patch.object(op,'EVIDENCE',folder):
                with self.assertRaises(AssertionError):op.open_access()


if __name__=='__main__':unittest.main()
