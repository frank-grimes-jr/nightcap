"""Execute the real rule-activation/reload functions with simulated transport failures."""
import ast,contextlib,io,json,tempfile,types,unittest
from pathlib import Path

SOURCE=Path(__file__).with_name('apply.py')
TREE=ast.parse(SOURCE.read_text())
FUNCTIONS=ast.Module(body=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in ('activate_rule','reload_and_verify')],type_ignores=[])

class ActivationTests(unittest.TestCase):
    def scenario(self,fault=None):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        out=Path(temp.name);before='1\tAA:PassiveExpPercent\t20\tnote\n';after=before.replace('\t20\tnote','\t40\tnote')
        state={'target':before,'extra':'untouched\n','reloads':0,'inverse':0}
        def sql(q):
            if 'FORWARD' in q:
                state['target']=after
                if fault=='external_same_value':return '0\n'
                if fault=='ambiguous_commit':raise RuntimeError('Lost response after commit')
                return '1\n'
            if 'ROLLBACK' in q:
                state['inverse']+=1;state['target']=before;return '1\n'
            return state['target']+state['extra'] if 'ORDER BY' in q else state['target']
        def reload(original):
            state['reloads']+=1
            if state['reloads']==1 and fault and fault!='ambiguous_commit':
                if fault=='external_rule':state['target']=before.replace('\t20\tnote','\t3\tnote')
                if fault=='unrelated_rule':state['extra']='other changed\n'
                raise RuntimeError('Injected reload failure')
            if fault=='recovery_reload':raise RuntimeError('Recovery reload failure')
            return {'processes_unchanged':True}
        ns={'json':json,'OUT':out,'NAME':'AA:PassiveExpPercent','FORWARD':'FORWARD','ROLLBACK':'ROLLBACK','sql':sql}
        exec(compile(FUNCTIONS,str(SOURCE),'exec'),ns);ns['reload_and_verify']=reload
        args=(before+'untouched\n',after+'untouched\n',before,{}, {'value':'40'})
        return ns,args,state,out

    def test_success(self):
        ns,args,state,out=self.scenario()
        result=ns['activate_rule'](*args)
        self.assertEqual(result['status'],'activated_verified');self.assertEqual(state['reloads'],1);self.assertEqual(state['inverse'],0)

    def test_reload_failure_reverts_only_owned_rule(self):
        for fault in ('reload','ambiguous_commit','unrelated_rule'):
            with self.subTest(fault=fault):
                ns,args,state,out=self.scenario(fault)
                with self.assertRaises(RuntimeError):ns['activate_rule'](*args)
                self.assertEqual(json.loads((out/'result.json').read_text())['status'],'rolled_back_verified')
                self.assertEqual(state['inverse'],1);self.assertEqual(state['target'],args[2])
                if fault=='unrelated_rule':self.assertEqual(state['extra'],'other changed\n')

    def test_external_target_change_preserved(self):
        ns,args,state,out=self.scenario('external_rule')
        with self.assertRaises(AssertionError):ns['activate_rule'](*args)
        self.assertEqual(state['inverse'],0);self.assertIn('\t3\t',state['target'])
        self.assertEqual(json.loads((out/'result.json').read_text())['status'],'recovery_pending')

    def test_failed_recovery_remains_pending(self):
        ns,args,state,out=self.scenario('recovery_reload')
        with self.assertRaises(RuntimeError):ns['activate_rule'](*args)
        self.assertEqual(state['target'],args[2]);self.assertEqual(state['inverse'],1)
        self.assertEqual(json.loads((out/'result.json').read_text())['status'],'recovery_pending')

    def test_noop_cannot_claim_another_writers_value(self):
        ns,args,state,out=self.scenario('external_same_value')
        with self.assertRaises(AssertionError):ns['activate_rule'](*args)
        self.assertEqual(state['inverse'],0);self.assertEqual(state['reloads'],0)
        self.assertIn('\t40\t',state['target'])
        result=json.loads((out/'result.json').read_text())
        self.assertEqual(result['status'],'recovery_pending');self.assertTrue(result['forward_not_applied'])

class ReloadTests(unittest.TestCase):
    def run_reload(self,missing=False,changed_pid=False):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        log=Path(temp.name)/'world.log';log.write_bytes(b'X'*199+b'\n')
        original={'1':{'name':'world','start':'10','logs':{str(log):100}}}
        fresh={'1':{'name':'world','start':'10','logs':{str(log):200}}}
        calls=[]
        def game(code):
            calls.append(code)
            if code=='snapshot':return json.dumps(fresh)
            if code=='reload':
                if changed_pid:fresh['1']['start']='11'
                if not missing:
                    with log.open('ab') as f:f.write(b'Loaded [1008] rules\n')
                return json.dumps({'world_broadcast_received':True})
            self.assertIn(': 200',code);self.assertNotIn(': 100',code)
            output=io.StringIO()
            with contextlib.redirect_stdout(output):exec(code,{})
            return output.getvalue()
        def run(args):return '\n'.join(json.dumps({'Service':s,'State':'running','Health':'healthy'}) for s in ('game','db','web','tunnel','gateway'))
        ns={'json':json,'game':game,'run':run,'SNAPSHOT':'snapshot','RELOAD_SOURCE':'reload','time':types.SimpleNamespace(sleep=lambda _:None)}
        exec(compile(FUNCTIONS,str(SOURCE),'exec'),ns)
        result=ns['reload_and_verify'](original)
        self.assertEqual(calls[:3],['snapshot','reload','snapshot'])
        return result

    def test_uses_fresh_offsets(self):self.assertTrue(self.run_reload()['processes_unchanged'])
    def test_missing_new_log_fails(self):
        with self.assertRaises(AssertionError):self.run_reload(missing=True)
    def test_process_change_fails(self):
        with self.assertRaises(AssertionError):self.run_reload(changed_pid=True)

if __name__=='__main__':unittest.main()
