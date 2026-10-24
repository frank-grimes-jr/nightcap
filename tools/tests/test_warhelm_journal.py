"""Exercise the actual Ashen projection and capacity code against failure states."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]

class AshenJournal(unittest.TestCase):
    def test_recovery_capacity_and_receipt_gated_history(self):
        source=(ROOT/'server-mods/code/zone/warhelm_compact.inc').read_text()
        functions='\n'.join(native.body(source,s) for s in ('bool HasRoom(', 'bool HasJournalRoom(', 'void Project('))
        native.FreeTradeTests.compile_run(self,r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <set>
#include <string>
constexpr unsigned Task=9801;constexpr int MAXACTIVEQUESTS=19;
namespace Chat{constexpr int Yellow=15;}
namespace fmt{template<class...T>std::string format(const std::string&s,T...){return s;}}
struct Client;
struct State{
 std::set<unsigned> active;unsigned filled=0;int accepts=0,removed=0,histories=0;bool history_ok=false;
 std::array<int,14> counts{};
 bool IsTaskActive(unsigned task){return active.count(task)!=0;}
 unsigned GetActiveTaskID(int slot){return unsigned(slot)<filled?99:0;}
 void AcceptNewTask(Client*,unsigned task,int,unsigned accepted){assert(accepted==100);active.insert(task);++accepts;counts={};}
 int GetTaskActivityDoneCountFromTaskID(unsigned,unsigned i){return counts.at(i);}
 void UpdateTaskActivity(Client*,unsigned,unsigned i,int,bool){assert(i<13);++counts.at(i);}
 void ResetTaskActivity(Client*,unsigned,unsigned i){counts.at(i)=0;}
 bool RecordCompletedTaskFromLedger(Client*,unsigned task,unsigned completed){assert(task==Task&&completed==200);++histories;return history_ok;}
 void RemoveTaskByTaskID(Client*,unsigned task){active.erase(task);++removed;}
};
struct Client{State state;State*GetTaskState(){return &state;}unsigned CharacterID(){return 42;}template<class...T>void Message(int,const char*,T...){};};
struct Progress{unsigned mask=0,accepted=100,completed=0;std::string receipt="receipt";} progress;
Progress Read(unsigned){return progress;}bool Installed(bool){return true;}
std::string Q(const std::string&s){return s;}bool receipt_delivered=false;
struct Rows{unsigned RowCount(){return receipt_delivered?1:0;}};
Rows Query(const std::string&s){assert(s.find("character_advloot_claims")!=std::string::npos);assert(s.find("AND character_id=")!=std::string::npos);return {};}
'''+functions+r'''
int main(){
 Client c;c.state.filled=18;
 assert(!HasJournalRoom(&c,9745)); // one slot cannot hold both journals
 c.state.filled=17;assert(HasJournalRoom(&c,9745));
 progress.mask=3;Project(&c);assert(c.state.accepts==1&&c.state.counts[0]==1&&c.state.counts[1]==1);
 Project(&c);assert(c.state.accepts==1&&c.state.counts[0]==1); // reconnect idempotent
 c.state.counts[5]=9;Project(&c);assert(c.state.counts[5]==0); // ledger repairs stale UI
 c.state.active.clear();c.state.filled=19;Project(&c);assert(c.state.accepts==1); // progress survives full Tasks
 c.state.filled=18;Project(&c);assert(c.state.accepts==2&&c.state.counts[1]==1); // abandon/recover
 progress.mask=8191;progress.completed=200;Project(&c);
 assert(c.state.histories==0&&c.state.counts[12]==1&&c.state.counts[13]==0);
 c.state.active.clear();assert(!HasJournalRoom(&c,9745)); // entitled but undelivered still needs two slots
 receipt_delivered=true;assert(HasJournalRoom(&c,9745));
 Project(&c);assert(c.state.histories==1&&c.state.IsTaskActive(Task)&&c.state.removed==0); // failed history retains UI
 c.state.history_ok=true;Project(&c);assert(!c.state.IsTaskActive(Task)&&c.state.removed==1);
 Project(&c);assert(c.state.removed==1&&c.state.counts[13]==0); // no duplicate completion/reward
}
''')

if __name__=='__main__':unittest.main()
