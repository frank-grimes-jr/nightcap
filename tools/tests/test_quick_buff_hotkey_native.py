"""Run real pinned RoF2 hotkey/reuse instructions in an isolated x86 test image."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
class NativeHotkey(unittest.TestCase):
    def test_pinned_hotkey_gate_and_immediate_reset(self):
        with tempfile.TemporaryDirectory(prefix='nightcap-hotkey-') as name:
            path=Path(name);source=ROOT/'eq-client-dll/tests/aa-reuse-native.cpp'
            (path/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 "'+str(source)+'" /Fe:native.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            built=subprocess.run(['cmd','/d','/c',str(path/'build.cmd')],cwd=path)
            self.assertEqual(built.returncode,0,(path/'build.log').read_text())
            result=subprocess.run([str(path/'native.exe'),'E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/eqgame.exe'],cwd=path,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            print(result.stdout.strip())
if __name__=='__main__':unittest.main()
