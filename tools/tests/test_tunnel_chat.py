"""Execute the same bounded name/auction formatter used by native zone chat."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class TunnelChat(unittest.TestCase):
    def test_native_formatting(self):
        header = (ROOT/'server-mods/code/common/tunnel_chat.h').as_posix()
        code = '''#include "HEADER"
#include <cassert>
#include <set>
int main() {
 using namespace NightcapTunnel;
 assert(FirstName("#Rellan_Ridgewalker000") == "Rellan");
 assert(FirstName("Khalure Ser`Tiras") == "Khalure");
 assert(FirstName("Trift007") == "Trift");
 assert(FirstName("").empty());
 std::vector<std::string> items = {"Sword 40pp", "Shield 35pp", "Boots 20pp"};
 std::set<std::string> variants;
 for(unsigned i=0;i<90;++i) {
  auto line=Auction(items,false,i);
  assert(line.find("Sword 40pp")!=std::string::npos);
  assert(line.find("Shield 35pp")!=std::string::npos);
  assert(line.find("Boots 20pp")!=std::string::npos);
  assert(line.size()<=400); variants.insert(line);
 }
 assert(variants.size()>=12);
 assert(Auction(items,false,0).find(" // ")!=std::string::npos);
 assert(Auction(items,false,1).find(" -- ")!=std::string::npos);
 assert(Auction(items,false,2).find(", ")!=std::string::npos);
 assert(Auction({},false,0).empty());
 assert(Auction(items,true,0).find("WTB")!=std::string::npos);
 // Never truncate a binary item link or exceed channel packet capacity.
 assert(Auction({std::string(380,'x'),"tail"},false,0).empty());
}
'''.replace('HEADER', header)
        with tempfile.TemporaryDirectory(prefix='nightcap-tunnel-chat-') as tmp:
            out = Path(tmp)
            (out/'test.cpp').write_text(code)
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            self.assertEqual(build.returncode,0,(out/'build.log').read_text())
            self.assertEqual(subprocess.run([str(out/'test.exe')]).returncode,0)


if __name__ == '__main__':
    unittest.main()
