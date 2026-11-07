"""Execute the native saver with failing acknowledgements and dirty-state retries."""
from pathlib import Path
import re
import unittest
import test_free_trade as native
from test_gameplay_policies import function

ROOT=Path(__file__).resolve().parents[2]


class LanternTaskSaveTests(unittest.TestCase):
    def test_native_save_failure_retry_and_completed_watermark(self):
        source=(ROOT/'server-mods/code/zone/task_manager.cpp').read_text()
        actual=function(source,'bool TaskManager::SaveClientState(')
        fixture=r'''
#include <array>
#include <vector>
#include <set>
#include <map>
#include <string>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <iostream>
template<class... A> void LogTasks(const A&...){}template<class... A>void LogError(const A&...){}
bool RecordCompletedTasks=true,RecordCompletedOptionalActivities=true;
#define RuleB(category,name) name
std::string StringFormat(const char*format,...){char b[2048];va_list a;va_start(a,format);std::vsnprintf(b,sizeof(b),format,a);va_end(a);return b;}
enum class TaskType{Quest,Shared};constexpr int TASKSLOTEMPTY=0,ActivityCompleted=2;
struct Activity{bool updated=true;int done_count=1,activity_state=ActivityCompleted;};
struct Active{int task_id=9500,slot=1,accepted_time=100,was_rewarded=0;bool updated=true;std::array<Activity,2> activity;};
struct Completed{int task_id,completed_time=200;std::array<bool,2> activity_done{true,true};};
struct ClientTaskState{int m_active_task_count=1;Active m_active_task,m_active_shared_task;std::vector<Active>m_active_tasks{Active{}};std::vector<Completed>m_completed_tasks{{9500},{9501},{9502}};unsigned m_last_completed_task_loaded=0;};
struct Client{int CharacterID(){return 7;}};
struct Info{TaskType type=TaskType::Quest;int activity_count=2;struct Flag{bool optional=false;};std::array<Flag,2>activity_information;};
struct Reply{bool ok;bool Success(){return ok;}std::string ErrorMessage(){return "injected";}};
struct Database{
 int count=0,fail=0;std::set<std::string>history;
 Reply QueryDatabase(const std::string&q,bool retry){assert(!retry);++count;if(q.find("REPLACE INTO completed_tasks")==0)history.insert(q);return {count!=fail};}
}database;
struct TaskManager{std::map<int,Info>data;Info*GetTaskData(int id){auto i=data.find(id);return i==data.end()?nullptr:&i->second;}bool SaveClientState(Client*,ClientTaskState*);};
ACTUAL
int main(){
 TaskManager manager;manager.data[9500].activity_information[1].optional=true;
 manager.data[9501].type=TaskType::Shared;manager.data[9502]=Info{};Client c;
 ClientTaskState baseline;assert(manager.SaveClientState(&c,&baseline));const int queries=database.count;assert(queries==5&&database.history.size()==3);
 for(int fail=1;fail<=queries;++fail){
  database={};database.fail=fail;ClientTaskState state;
  assert(!manager.SaveClientState(&c,&state));
  assert(state.m_active_tasks[0].updated==(fail==1));
  assert(state.m_active_tasks[0].activity[0].updated==(fail==2));
  assert(state.m_last_completed_task_loaded==(fail<=2?3u:0u));
  database.fail=0;assert(manager.SaveClientState(&c,&state));
  assert(!state.m_active_tasks[0].updated&&!state.m_active_tasks[0].activity[0].updated);
  assert(state.m_last_completed_task_loaded==3&&database.history.size()==3);
 }
 database={};ClientTaskState missing;manager.data.erase(9502);assert(!manager.SaveClientState(&c,&missing));assert(missing.m_last_completed_task_loaded==0);
 assert(!manager.SaveClientState(nullptr,&missing));assert(!manager.SaveClientState(&c,nullptr));
 std::cout<<"Native task save failure, idempotent retry and completion-watermark controls passed\n";
}
'''.replace('ACTUAL',actual)
        native.FreeTradeTests.compile_run(self,fixture)



    def test_completion_checkpoint_is_saved_before_native_cancel(self):
        source=(ROOT/'server-mods/code/zone/task_client_state.cpp').read_text()
        block=function(source,'if (task_complete && info->task_id>=9500')
        start=source.index(block)
        self.assertLess(start,source.index('client->CancelTask(task_index, task_data->type)',start))
        self.assertLess(start,source.index('DispatchEventTaskComplete(client, *info, activity_id)',start))
        native.FreeTradeTests.compile_run(self,r"""
#include <cassert>
namespace Chat{constexpr int Yellow=1;}
struct Client{template<class...A>void Message(A...){}};
struct Manager{bool success=true;int writes=0;static Manager*Instance(){static Manager m;return &m;}bool SaveClientState(Client*,void*){++writes;return success;}};
using TaskManager=Manager;
struct State{int cancelled=0;struct Info{int task_id=9500;}data;
 int Finish(Client*client,bool task_complete){auto info=&data;int count=1;
BLOCK
 if(task_complete)++cancelled;return count;}
};
int main(){Client c;State s;auto m=Manager::Instance();m->success=false;s.Finish(&c,true);assert(!s.cancelled&&m->writes==1);
 m->success=true;s.Finish(&c,true);assert(s.cancelled==1&&m->writes==2);
 s.data.task_id=9500-1;m->success=false;s.Finish(&c,true);assert(s.cancelled==2&&m->writes==2);
 s.data.task_id=9516;s.Finish(&c,true);assert(s.cancelled==3&&m->writes==2);}
""".replace('BLOCK',block))


if __name__=='__main__':unittest.main()
