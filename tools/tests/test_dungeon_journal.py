"""Execute the journal projection and durable history adapter from native source."""
from pathlib import Path
import hashlib
import json
import os
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]

class DungeonJournal(unittest.TestCase):
    def test_history_recovery_after_expiry_preserves_newer_and_ambiguous_runs(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        function=native.body(source,'void JournalHistory(')
        keeper=native.body(source,'bool Keeper(')
        self.assertLess(keeper.index('JournalHistory(c)'),keeper.index('if (native_managed && run.id.empty())'))
        native.FreeTradeTests.compile_run(self,r'''
#include <array>
#include <cassert>
#include <exception>
#include <stdexcept>
#include <string>
#include <vector>
#include "common/dungeon_catalog.h"
using namespace NightcapDungeon;
enum class TaskType{Quest=2};constexpr int MAXACTIVEQUESTS=19;
template<class...T>void LogError(const char*,T...){}
namespace Strings{unsigned ToUnsignedInt(const char*s){return std::stoul(s);}int ToInt(const char*s){return std::stoi(s);}}
namespace fmt{
inline std::string arg(const std::string &value){return value;}
template<class T>std::string arg(T value){return std::to_string(value);}
template<class...T>std::string format(std::string pattern,T...values){
 std::vector<std::string> args;((args.push_back(arg(values))),...);
 for(const auto&s:args){auto i=pattern.find("{}");assert(i!=std::string::npos);pattern.replace(i,2,s);}return pattern;
}}
struct Client;
unsigned history_zone=36,history_task=9701;
struct State{
 bool active=true,history_ok=true;int histories=0,removed=0;int start=100;
 int GetActiveTaskID(int slot){return active&&slot==0?history_task:0;}
 int GetTaskStartTime(TaskType,int){return start;}
 bool RecordCompletedTaskFromLedger(Client*,unsigned task,int time){assert(task==history_task&&time==200);++histories;return history_ok;}
 void RemoveTaskByTaskID(Client*,unsigned task){assert(task==history_task);active=false;++removed;}
};
struct Client{State state;State*GetTaskState(){return &state;}unsigned CharacterID(){return 29;}};
struct Row{std::array<std::string,3> values;const char*operator[](int i)const{return values[i].c_str();}};
struct Rows{
 std::vector<Row> values;
 struct It{Rows*rows;size_t i;Row operator*(){return rows->values[i];}const char*operator[](int j){return rows->values[i][j];}
 It&operator++(){++i;return *this;}bool operator!=(const It&r){return i!=r.i;}};
 size_t RowCount(){return values.size();}It begin(){return {this,0};}It end(){return {this,values.size()};}
};
bool fail_query=false,ambiguous=false;int match_queries=0;
Rows Query(const std::string&sql){
 if(fail_query)throw std::runtime_error("injected history failure");
 assert(sql.find("character_id=29")!=std::string::npos);
 if(sql.find("MAX(m.completed_at)")!=std::string::npos)return {{{{{std::to_string(history_zone),"1","200"}}}}};
 ++match_queries;assert(sql.find(history_zone==36?"r.zone_id=36 AND r.mode=1":"r.zone_id IN (76,186) AND r.mode=1")!=std::string::npos);
 assert(sql.find("CASE WHEN m.completed_at=0")!=std::string::npos);
 bool old=sql.find("r.instance_start=100")!=std::string::npos;
 return {{{{{old?"1":"0",ambiguous||!old?"1":"0",""}}}}};
}
'''+function+r'''
int main(){
 Client c;c.state.history_ok=false;JournalHistory(&c);
 assert(c.state.active && match_queries==0); // do not remove before durable history
 c.state.history_ok=true;c.state.start=300;JournalHistory(&c);
 assert(c.state.active && c.state.removed==0); // new run same task
 c.state.start=100;ambiguous=true;JournalHistory(&c);
 assert(c.state.active); // acceptedtime cannot distinguish same-second runs
 ambiguous=false;JournalHistory(&c);assert(!c.state.active&&c.state.removed==1);
 JournalHistory(&c);assert(c.state.removed==1); // reset/expiry repeated recovery
 fail_query=true;JournalHistory(&c); // display DB failure must not escape into connection handling
 fail_query=false;history_task=9739;
 for(unsigned layout:{76u,186u}){
  history_zone=layout;Client hate;ambiguous=true;
  JournalHistory(&hate);assert(hate.state.active && hate.state.removed==0);
  ambiguous=false;JournalHistory(&hate);assert(!hate.state.active && hate.state.removed==1);
 }
}
''')

    def test_actual_journal_preserves_runs_and_never_completes_native_sentinel(self):
        function=native.body((ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text(),'void JournalForRun(')
        native.FreeTradeTests.compile_run(self,r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <exception>
#include <map>
#include <set>
#include <string>
#include <vector>
#include "common/dungeon_catalog.h"
using namespace NightcapDungeon;
enum class Mode { Grind=0, Raid=1 };enum class TaskType{Quest=2};
constexpr int MAXACTIVEQUESTS=19;
namespace Chat {constexpr int Yellow=15;}
template<class...T>void LogError(const char*,T...){}
namespace Strings {unsigned ToUnsignedInt(const char *s){return std::stoul(s);}int ToInt(const char *s){return std::stoi(s);}}
namespace fmt {template<class... T>std::string format(const std::string &s,T...){return s;}}
struct Client;
struct State {
 bool active=false,history_ok=true;int accepts=0,removes=0,updates=0,histories=0;unsigned start=0;
 std::array<int,6> counts{};
 bool IsTaskActive(unsigned){return active;}
 void RemoveTaskByTaskID(Client*,unsigned){active=false;++removes;}
 void AcceptNewTask(Client*,unsigned,int,unsigned t){active=true;start=t;counts={};++accepts;}
 int GetActiveTaskID(int slot){return active&&slot==0?9701:0;}
 int GetTaskStartTime(TaskType,int){return start;}
 int GetTaskActivityDoneCountFromTaskID(unsigned,unsigned i){return counts.at(i);}
 void UpdateTaskActivity(Client*,unsigned,unsigned i,int,bool){assert(i<5);++counts.at(i);++updates;}
 void ResetTaskActivity(Client*,unsigned,unsigned i){counts.at(i)=0;}
 bool RecordCompletedTaskFromLedger(Client*,unsigned,int){++histories;return history_ok;}
};
struct Client {
 State state;std::map<std::string,std::string> vars;
 State *GetTaskState(){return &state;}unsigned CharacterID(){return 29;}
 std::string GetEntityVariable(const std::string &key){return vars[key];}
 void SetEntityVariable(const std::string &key,const std::string &v){vars[key]=v;}
 template<class...T>void Message(int,const char*,T...){}
};
struct Run {std::string id="first";unsigned start=100;uint64_t expiry=1000;Mode mode=Mode::Raid;const Dungeon *dungeon=&Dungeons[0];};
Run current;bool managed=true;bool Managed(){return managed;}uint64_t Now(){return 200;}
struct Zone{unsigned id=36;unsigned GetZoneID(){return id;}} z,*zone=&z;
Run Personal(unsigned,unsigned){return current;}std::string Q(const std::string &s){return s;}
struct Row{std::string value;const char *operator[](int)const{return value.c_str();}};
struct Rows {
 std::vector<Row> values;
 struct It{Rows *rows;size_t i;Row operator*(){return rows->values[i];}
  const char *operator[](int){return rows->values[i].value.c_str();}
  It &operator++(){++i;return *this;}bool operator!=(const It &r){return i!=r.i;}};
 size_t RowCount(){return values.size();}It begin(){return {this,0};}It end(){return {this,values.size()};}
};
int ledger_completed=0;std::set<unsigned> credits;bool enrolled=true;
Rows Query(const std::string &sql){
 Rows r;
 if(sql.find("SELECT completed_at")!=std::string::npos){if(enrolled)r.values.push_back({std::to_string(ledger_completed)});}
 else{for(unsigned id:credits)r.values.push_back({std::to_string(id)});}
 return r;
}
'''+function+r'''
void Journal(Client *c) { JournalForRun(c,nullptr); }
int main(){
 Client c;credits={1};Journal(&c);
 assert(c.state.accepts==1 && c.state.counts[0]==1 && c.state.counts[1]==0);
 Journal(&c);assert(c.state.accepts==1 && c.state.updates==1);
 c.vars.clear();Journal(&c); // reconnect with persisted active state
 assert(c.state.accepts==1 && c.state.removes==0 && c.state.updates==1);
 c.state.active=false;Journal(&c); // abandon only the display
 assert(c.state.accepts==2 && c.state.counts[0]==1);
 current.id="second";current.start=150;credits={};Journal(&c);
 assert(c.state.accepts==3 && c.state.removes==1 && c.state.counts[0]==0);
 credits={1,2,3,4,5};ledger_completed=180;c.state.history_ok=false;Journal(&c);
 assert(c.state.active && c.state.accepts==3); // failed history remains retryable
 c.state.history_ok=true;Journal(&c);
 assert(!c.state.active && c.state.accepts==3 && c.state.removes==2);
 c.vars.clear();Journal(&c);assert(!c.state.active && c.state.accepts==3);
 current.id="third";current.start=190;ledger_completed=0;credits={};Journal(&c);
 assert(c.state.active && c.state.accepts==4); // old completion never hides a new run
 enrolled=false;Journal(&c);assert(c.state.accepts==4);
 // A hub Keeper explicitly selects its destination run, never the host zone.
 enrolled=true;managed=false;z.id=22;Client hub;
 Run selected;selected.id="hate-from-commonlands";selected.dungeon=FindDungeon(76);
 JournalForRun(&hub,&selected);
 assert(hub.vars["nightcap:dungeon-journal-9739"]==selected.id);
 assert(hub.vars.count("nightcap:dungeon-journal-9701")==0);
}
''')

    def test_all_dungeon_objectives_are_visible_and_ledger_controlled(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        signature='void ConfigureJournalTask('
        function=native.body(source,signature) if signature in source else 'void ConfigureJournalTask(int, TaskInformation&) {}'
        base=Path(os.environ.get('EQEMU_SOURCE','E:/EQ_Local_Dev/akk-stack/code'))
        common=base/'common/tasks.h'
        manifest=json.loads((ROOT/'docs/dungeons/native-build-manifest.json').read_text())
        self.assertEqual(hashlib.sha256(common.read_bytes()).hexdigest(),manifest['source_files']['common/tasks.h'])
        active=native.body(common.read_text(),'ActiveElements GetActiveElements(')
        native.FreeTradeTests.compile_run(self,r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <limits>
#include <string>
#include <vector>
#include "common/dungeon_catalog.h"
enum class TaskType { Quest=2 };
enum class TaskActivityType { None=0, Kill=2 };
enum TaskMethodType { METHODSINGLEID=0, METHODQUEST=2 };
struct ActivityInformation {
 std::string zones;std::vector<int> zone_ids;
 TaskActivityType activity_type=TaskActivityType::None;
 TaskMethodType goal_method=METHODSINGLEID;
 std::string target_name,description_override;
 int step=0,req_activity_id=-1;bool optional=false;
};
struct TaskInformation {
 TaskType type=TaskType::Quest; int activity_count=0;
 std::string description,reward; ActivityInformation activity_information[20];
 std::vector<int> selector_ids;
};
constexpr int MAXACTIVITIESPERTASK=20,ActivityCompleted=2;
struct ActivityState{int activity_state=0;};
struct ActiveElements{bool is_task_complete;std::vector<int> active;};
// Retained upstream template compares integer task indexes with size_t.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4018)
#else
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsign-compare"
#endif
template<typename Td,typename Ts>
'''+active+r'''
#ifdef _MSC_VER
#pragma warning(pop)
#else
#pragma GCC diagnostic pop
#endif
namespace NightcapDungeon {
namespace Vigil { constexpr unsigned Task=9800;
'''+native.body((ROOT/'server-mods/code/zone/chapterhouse_vigil.inc').read_text(),'void Configure(')+r'''
}
namespace Ashen { constexpr unsigned Task=9801;
'''+native.body((ROOT/'server-mods/code/zone/warhelm_compact.inc').read_text(),'void Configure(')+r'''
}
'''+function+r'''
}
int main() {
 using namespace NightcapDungeon;
 for (const auto &d:Dungeons) for (int mode=0;mode<2;++mode) {
  TaskInformation task;task.activity_count=d.count+1;
  ActivityState states[20];
  auto original=GetActiveElements(task.activity_information,states,task.activity_count);
  assert(original.active.size()==1 && original.active[0]==0); // old all-zero sequence defect
  for(unsigned i=0;i<=d.count;++i) task.selector_ids.push_back(i);
  ConfigureJournalTask(9700+2*d.index+mode,task);
  if(d.index==19) for(unsigned i=0;i<=d.count;++i) {
   assert(task.activity_information[i].zones=="76;186");
   assert((task.activity_information[i].zone_ids==std::vector<int>{76,186}));
  }
  for(const auto &b:Bosses) if(b.zone==d.zone) {
   const auto &a=task.activity_information[b.objective-1];
   assert(a.activity_type==TaskActivityType::Kill);
   assert(a.goal_method==METHODQUEST);
   assert(a.target_name==b.name && a.description_override.find(b.name)!=std::string::npos);
   assert(a.step==0 && a.req_activity_id==-1);
  }
  assert(task.activity_information[d.count].goal_method==METHODQUEST);
  assert(task.activity_information[d.count].step==1);
  assert(task.selector_ids.size()==d.count);
  assert(task.description.find("Task Stage Completed")!=std::string::npos);
  assert(task.description.find("Completed")!=std::string::npos);
  auto visible=GetActiveElements(task.activity_information,states,task.activity_count);
  assert(!visible.is_task_complete && visible.active.size()==d.count);
  for(unsigned i=0;i<d.count;++i)assert(visible.active[i]==static_cast<int>(i));
  // Bosses may be credited out of order, with every remaining objective visible.
  for(unsigned i=d.count;i>0;--i){
   states[i-1].activity_state=ActivityCompleted;
   auto next=GetActiveElements(task.activity_information,states,task.activity_count);
   assert(!next.is_task_complete);
   if(i>1)assert(next.active.size()==i-1);
   else assert(next.active.size()==1 && next.active[0]==static_cast<int>(d.count));
  }
 }
 TaskInformation unrelated;unrelated.activity_count=6;unrelated.description="untouched";
 ConfigureJournalTask(9699,unrelated);ConfigureJournalTask(9700+2*DungeonCount,unrelated);
 assert(unrelated.description=="untouched");
 TaskInformation malformed;malformed.activity_count=2;malformed.description="malformed";
 ConfigureJournalTask(9701,malformed);assert(malformed.description=="malformed");
}
''')

    def test_history_write_failure_retry_ordering_and_no_task_rewards(self):
        source=(ROOT/'server-mods/code/zone/task_client_state.cpp').read_text()
        signature='bool ClientTaskState::RecordCompletedTaskFromLedger('
        function=native.body(source,signature) if signature in source else 'bool ClientTaskState::RecordCompletedTaskFromLedger(Client*,int,int) { return false; }'
        native.FreeTradeTests.compile_run(self,r'''
#include <algorithm>
#include <cassert>
#include <string>
#include <sstream>
#include <vector>
#include <iterator>
enum class TaskType { Quest=2 };
constexpr int MAXACTIVITIESPERTASK=20;
struct TaskInformation { TaskType type=TaskType::Quest;int activity_count=6; };
struct CompletedTaskInformation {int task_id=0,completed_time=0;bool activity_done[20]{};};
struct Client {int CharacterID(){return 29;}};
bool keep_one=true,record_enabled=true;
#define RuleB(category,rule) rule##_rule()
bool KeepOneRecordPerCompletedTask_rule(){return keep_one;}
bool RecordCompletedTasks_rule(){return record_enabled;}
namespace fmt {
template<class... T> std::string format(std::string pattern,T... values) {
 std::vector<std::string> args;((args.push_back(std::to_string(values))),...);
 for(const auto &s:args){auto i=pattern.find("{}");assert(i!=std::string::npos);pattern.replace(i,2,s);}
 return pattern;
}}
struct Result {bool ok;bool Success(){return ok;}};
struct Database {int fail_at=0,calls=0;std::vector<std::string> statements;
 Result QueryDatabase(const std::string &s){statements.push_back(s);++calls;return {calls!=fail_at};}
} database;
struct TaskManager {TaskInformation task;int sends=0;bool missing=false;
 static TaskManager *Instance(){static TaskManager m;return &m;}
 const TaskInformation *GetTaskData(int){return missing?nullptr:&task;}
 void SendCompletedTasksToClient(Client*,void*){++sends;}
};
struct ClientTaskState {
 std::vector<CompletedTaskInformation> m_completed_tasks;unsigned m_last_completed_task_loaded=0;
 bool RecordCompletedTaskFromLedger(Client*,int,int);
};
'''+function+r'''
int main() {
 Client c;ClientTaskState s;
 database.fail_at=1;
 assert(!s.RecordCompletedTaskFromLedger(&c,9701,100));
 assert(s.m_completed_tasks.empty()); // failed writes must not become accepted history
 database.fail_at=0;
 database.fail_at=database.calls+2; // REPLACE succeeds, pruning history fails
 assert(!s.RecordCompletedTaskFromLedger(&c,9701,100));
 assert(s.m_completed_tasks.empty());
 database.fail_at=0;
 assert(s.RecordCompletedTaskFromLedger(&c,9701,100));
 assert(s.m_completed_tasks.size()==1 && s.m_completed_tasks[0].completed_time==100);
 for(int i=0;i<6;++i)assert(s.m_completed_tasks[0].activity_done[i]);
 assert(s.RecordCompletedTaskFromLedger(&c,9701,100));
 assert(s.m_completed_tasks.size()==1); // duplicate journal/death refresh
 assert(s.RecordCompletedTaskFromLedger(&c,9703,300));
 assert(s.RecordCompletedTaskFromLedger(&c,9705,200));
 assert(s.m_completed_tasks[0].completed_time==100 && s.m_completed_tasks[1].completed_time==200);
 assert(s.m_completed_tasks[2].completed_time==300);
 assert(s.RecordCompletedTaskFromLedger(&c,9701,400));
 assert(s.m_completed_tasks.size()==3 && s.m_completed_tasks.back().completed_time==400);
 assert(s.RecordCompletedTaskFromLedger(&c,9701,100));
 assert(s.m_completed_tasks.size()==3 && s.m_completed_tasks.back().completed_time==400);
 assert(!s.RecordCompletedTaskFromLedger(&c,9701,0));
 record_enabled=false;assert(!s.RecordCompletedTaskFromLedger(&c,9701,500));record_enabled=true;
 TaskManager::Instance()->missing=true;assert(!s.RecordCompletedTaskFromLedger(&c,9701,500));
 TaskManager::Instance()->missing=false;
 ClientTaskState pending;
 pending.m_completed_tasks={{9703,300,{}}}; // native completion not yet saved
 assert(pending.RecordCompletedTaskFromLedger(&c,9701,100));
 assert(pending.m_last_completed_task_loaded==1 && pending.m_completed_tasks[1].task_id==9703);
 assert(pending.RecordCompletedTaskFromLedger(&c,9701,400));
 assert(pending.m_last_completed_task_loaded==0 && pending.m_completed_tasks[0].task_id==9703);
 keep_one=false;
 assert(s.RecordCompletedTaskFromLedger(&c,9701,500));
 assert(s.m_completed_tasks.size()==4);
 assert(s.RecordCompletedTaskFromLedger(&c,9701,500));
 assert(s.m_completed_tasks.size()==4);
 // Database writes are confined to history for the supplied character and task.
 for(const auto &q:database.statements){assert(q.find("completed_tasks")!=std::string::npos);assert(q.find("29")!=std::string::npos);}
 // No reward, quest-event, inventory or activity-update APIs exist in this fixture.
}
''')

if __name__=='__main__':unittest.main()
