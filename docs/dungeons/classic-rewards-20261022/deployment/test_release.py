"""Packaging and preservation checks runnable without production credentials."""
import ast,importlib.util,json,re,sys,tarfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepare',HERE/'prepare_local.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)

class Release(unittest.TestCase):
    def test_clone_includes_every_runtime_content_dependency(self):
        tree=ast.parse((HERE/'rollout.py').read_text())
        public=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='PUBLIC' for t in n.targets)))
        contract=json.loads((HERE.parents[3]/'docs/dungeons/runtime-contract.json').read_text())
        referenced={m.group(1) for c in contract['content'] for m in re.finditer(
            r'\b(?:FROM|JOIN)\s+`?([A-Za-z_][A-Za-z_0-9]*)',c['sql'],re.I)}
        self.assertFalse(referenced-public-{'nightcap_dungeon_state'},referenced-public)

    def test_windows_packaging_sets_executable_modes(self):
        for name in ('bin/zone','bin/world','bin/shared_memory','cache_check'):
            entry=tarfile.TarInfo(name);entry.mode=0o666
            self.assertEqual(prepare.tar_mode(entry).mode,0o755)
        self.assertEqual(prepare.tar_mode(tarfile.TarInfo('manifest.json')).mode,0o600)

    def test_whole_cache_allows_only_exact_magic_changes(self):
        source=(HERE/'rollout.py').read_text();tree=ast.parse(source)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compare_cache')
        namespace={}
        class Document:
            def read_text(self):return list(range(960000,960220))
        class Stage:
            def __truediv__(self,value):return Document()
        class Json:
            @staticmethod
            def loads(value):return value
        namespace.update(STAGE=Stage(),json=Json())
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'cache-policy','exec'),namespace)
        compare=namespace['compare_cache']
        before={i:bytes(1332) for i in range(960000,960330)};before[1]='old'
        after={**before,**{i:'new' for i in range(960330,960414)}}
        for i in range(960000,960220):after[i]=b'\x01'+bytes(1331)
        self.assertEqual(compare(before,after)['magic_only'],220)
        bad=dict(after);bad[1]='drift'
        with self.assertRaises(AssertionError):compare(before,bad)
        bad=dict(after);bad[960000]=b'\x01\x01'+bytes(1330)
        with self.assertRaises(AssertionError):compare(before,bad)
        bad=dict(after);bad.pop(960413)
        with self.assertRaises(AssertionError):compare(before,bad)

if __name__=='__main__':unittest.main()
