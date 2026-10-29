"""Offline final verification checks; no production connectivity."""
import base64
import contextlib
import hashlib
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import test_rollout as harness
import verify_live as verify


@contextlib.contextmanager
def fixture():
    with harness.lifecycle() as f, contextlib.ExitStack() as stack:
        op = harness.op
        f.runtime.image = 'candidate'
        stack.enter_context(patch.object(verify,'IMAGE','candidate'))
        stack.enter_context(patch.object(verify,'MANIFEST_SHA','digest'))
        stack.enter_context(patch.object(verify,'CHANNEL_SHA','new-client'))
        stack.enter_context(patch.object(verify,'authenticate'))
        stack.enter_context(patch.object(verify,'runtime_files',return_value=8))
        stack.enter_context(patch.object(verify,'publications',return_value={'wiki_files':499,'client_release':2026102901}))
        stack.enter_context(patch.object(op,'contract',return_value={'schema':51,'content':650}))
        f.public['channels']['channel.json']='new-client'
        f.public['wiki']=str(Path('releases')/verify.WIKI)
        f.runtime.quest_tree.update(f.manifest['files'])
        runtime={'image_id':'candidate','started_at':'opened','restart_count':0,
                 'processes':[['zone','hash']]*12+[[n,'hash'] for n in ('world','ucs','loginserver')]}
        stack.enter_context(patch.object(f.runtime,'running',return_value=runtime))
        state={name:{'Id':name,'Image':name,'RestartCount':0,
                    'State':{'Running':True,'StartedAt':'opened','OOMKilled':False,'Health':{'Status':'healthy'}}}
               for name in ('game','gateway','db','web','tunnel')}
        stack.enter_context(patch.object(f.runtime,'state',side_effect=lambda name:state[name]))
        guard={'verified':True,'owner_gameplay_accepted':False,
               'runtime_receipt':str(f.evidence/'activation/deployed.json'),'runtime_receipt_sha256':'receipt-pin',
               'client_receipt':str(verify.CLIENT_RECEIPT),'client_receipt_sha256':'client-pin','channel_sha256':'new-client',
               'services_after':{name:{**{k:v[k] for k in ('Id','Image','RestartCount')},'state':{k:v['State'][k] for k in ('Running','StartedAt','OOMKilled')}} for name,v in state.items()}}
        deployed={'runtime':runtime,'gateway_open':True,'database_restored':False,'owner_gameplay_accepted':False}
        client={'release':2026102901,'channel_sha256':'new-client'}
        def read(path):
            if path.name=='preflight.json':return f.plan
            if path.name=='wiki-activation-guard.json':return guard
            if path.name=='deployed.json':return deployed
            if path==verify.CLIENT_RECEIPT:return client
            raise AssertionError(path)
        stack.enter_context(patch.object(op,'read',side_effect=read))
        f.base.saved_state.side_effect=AssertionError('Dynamic player state must not be sampled')
        yield types.SimpleNamespace(op=op,f=f,guard=guard,runtime=runtime,state=state,deployed=deployed)


class VerifyTests(unittest.TestCase):
    def test_success_does_not_mutate_or_compare_dynamic_player_state(self):
        with fixture() as x:
            result=verify.verify(x.op,'guard-pin')
            self.assertEqual(result['content_checks'],650)
            self.assertEqual(result['schema_checks'],51)
            self.assertEqual(result['native_zone_workers'],12)
            self.assertFalse(result['owner_gameplay_accepted'])
            self.assertFalse(result['dynamic_player_state_compared'])
            x.f.base.saved_state.assert_not_called()
            x.op.public_preflight.assert_not_called()
            self.assertEqual(x.f.runtime.events,[])

    def test_receipt_worker_service_and_scope_drift_rejected(self):
        for fault in ('closed','qa','image','workers','service','contract','publication','content','guard'):
            with self.subTest(fault=fault),fixture() as x,contextlib.ExitStack() as stack:
                if fault=='closed':x.deployed['gateway_open']=False
                elif fault=='qa':x.deployed['owner_gameplay_accepted']=True
                elif fault=='image':x.deployed['runtime']['image_id']='wrong'
                elif fault=='workers':x.runtime['processes'].pop(0)
                elif fault=='service':x.state['gateway']['State']['StartedAt']='restarted'
                elif fault=='contract':x.op.contract.return_value={'schema':51,'content':649}
                elif fault=='publication':x.f.public['wiki']='other'
                elif fault=='content':x.op.content.return_value={}
                else:stack.enter_context(patch.object(verify,'authenticate',side_effect=AssertionError('guard')))
                with self.assertRaises(AssertionError):verify.verify(x.op,'guard-pin')
                x.f.base.saved_state.assert_not_called()
                self.assertEqual(x.f.runtime.events,[])

    def test_runtime_file_hash_check_executes_only_reading_code(self):
        runtime=types.SimpleNamespace(state=Mock(return_value={'Id':'game-id'}),out=Mock(return_value='{"bin/zone":"pin"}'))
        self.assertEqual(verify.runtime_files(types.SimpleNamespace(r=runtime),{'bin/zone':'pin'}),1)
        command=runtime.out.call_args.args
        self.assertEqual(command[:6],('docker','exec','game-id','python3','-B','-c'))
        self.assertIn('read_bytes()',command[6])
        runtime.out.return_value='{"bin/zone":"wrong"}'
        with self.assertRaises(AssertionError):verify.runtime_files(types.SimpleNamespace(r=runtime),{'bin/zone':'pin'})

    def test_publication_exact_assets_inventory_pointer_and_config(self):
        with tempfile.TemporaryDirectory() as directory,contextlib.ExitStack() as stack:
            root=Path(directory).resolve();public=root/'data/public';public.mkdir(parents=True)
            asset_dir=public/'release/2026102901';asset_dir.mkdir(parents=True)
            files=[]
            for name in verify.ASSETS:
                path=asset_dir/name;path.write_bytes(name.encode())
                files.append({'path':name,'url':'https://play.nightcapgame.org/release/2026102901/'+name,'size':path.stat().st_size,'sha256':verify.sha(path)})
            encoded=base64.b64encode(json.dumps({'release':2026102901,'files':files}).encode()).decode()
            (public/'channel.json').write_text(json.dumps({'manifest':encoded}))
            stack.enter_context(patch.object(verify,'CHANNEL_SHA',verify.sha(public/'channel.json')))
            wiki=public/'wiki/releases'/verify.WIKI;wiki.mkdir(parents=True)
            manifest={}
            for i in range(499):
                path=wiki/(str(i)+'.html');path.write_text(str(i));manifest[path.name]=verify.sha(path)
            (public/'wiki/current').symlink_to(Path('releases')/verify.WIKI,target_is_directory=True)
            history=root/'website-history'/verify.WIKI;history.mkdir(parents=True)
            (history/'manifest.json').write_text(json.dumps(manifest))
            canonical=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
            stack.enter_context(patch.object(verify,'WIKI_INVENTORY_SHA',hashlib.sha256(canonical).hexdigest()))
            (root/'nginx.conf').write_text('unchanged')
            stack.enter_context(patch.object(verify,'WEB_CONFIG_SHA',verify.sha(root/'nginx.conf')))
            op=types.SimpleNamespace(ROOT=root)
            self.assertEqual(verify.publications(op)['wiki_files'],499)
            for target in (asset_dir/'hateplaneb.s3d',wiki/'1.html',root/'nginx.conf'):
                original=target.read_bytes();target.write_bytes(b'drift')
                with self.assertRaises(AssertionError):verify.publications(op)
                target.write_bytes(original)
            (wiki/'extra.html').write_text('unexpected')
            with self.assertRaises(AssertionError):verify.publications(op)


if __name__=='__main__':unittest.main(verbosity=2)
