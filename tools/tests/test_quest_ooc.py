"""Exercise the real Perl adapter, including NPC timers without an initiator."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_gameplay_policies import ROOT, function


class QuestOOC(unittest.TestCase):
    def test_bound_adapter_delivers_real_ooc_without_format_expansion(self):
        source = (ROOT / 'server-mods/code/zone/embparser_api.cpp').read_text()
        self.assertTrue('package.add("ooc", &Perl__ooc);' in source, 'quest::ooc is not bound')
        body = function(source, 'void Perl__ooc(')
        fixture = r'''
#include <cassert>
#include <cstring>
#include <map>
#include <string>
enum { ChatChannel_OOC = 5 };
namespace Language { enum { CommonTongue = 0, MaxValue = 100 }; }
struct Mob { const char* GetCleanName() { return "Trift"; } };
struct Client {
 int count=0;
 void ChannelMessageSend(const char* from, const char* to, int channel,
     int language, int skill, const char* format, const char* text) {
  assert(strcmp(from,"Trift")==0 && !to && channel==5 && language==0 && skill==100);
  assert(strcmp(format,"%s")==0 && strcmp(text,"100% lost %s corpse")==0); ++count;
 }
};
struct Quest { Mob* owner=nullptr; Mob* GetOwner() { return owner; } } quest_manager;
struct Entities { std::map<int,Client*> clients;
 const std::map<int,Client*>& GetClientList() { return clients; }
} entity_list;
'''
        controls = r'''
int main() {
 Client a,b; Mob npc; entity_list.clients={{1,&a},{2,&b}};
 Perl__ooc("100% lost %s corpse"); assert(a.count==0);
 quest_manager.owner=&npc;
 Perl__ooc(nullptr); assert(a.count==0);
 Perl__ooc("100% lost %s corpse"); assert(a.count==1 && b.count==1);
 entity_list.clients.clear(); Perl__ooc("100% lost %s corpse");
}
'''
        with tempfile.TemporaryDirectory(prefix='nightcap-ooc-') as tmp:
            out = Path(tmp)
            (out/'test.cpp').write_text(fixture + body + controls)
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /WX /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            self.assertEqual(build.returncode,0,(out/'build.log').read_text())
            subprocess.run([out/'test.exe'],check=True)
