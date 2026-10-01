"""Run native explore/matching methods with generated journal objectives."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from epic05 import ROOT, load_catalog, task_rows
from test_gameplay_policies import function


class Epic05TaskCredit(unittest.TestCase):
    def test_native_movement_credits_only_correct_exploration_zone(self):
        base = Path(os.environ.get('EQEMU_SOURCE', 'E:/EQ_Local_Dev/akk-stack/code'))
        source = (base/'zone/task_client_state.cpp').read_text()
        common = (base/'common/tasks.h').read_text()
        enum = function(common, 'enum class TaskActivityType') + ';\n'
        check_zone = function(common, 'inline bool CheckZone(')
        native = '\n'.join(function(source, signature) for signature in (
            'bool ClientTaskState::CanUpdate(', 'void ClientTaskState::UpdateTasksOnExplore(',
            'void ClientTaskState::ProcessTaskProximities('))
        fixture = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#define LogTasks(...)
#define LogTasksDetail(...)
#define RuleB(...) true
namespace glm { struct vec4 { float x,y,z,w; vec4(float a=0,float b=0,float c=0,float d=0):x(a),y(b),z(c),w(d){} }; }
ENUM
constexpr int METHODQUEST=2, ActivityActive=1;
namespace Tasks { bool IsInMatchList(const std::string&a,const std::string&b){return a==b;}
bool IsInMatchListPartial(const std::string&a,const std::string&b){return b.find(a)!=std::string::npos;} }
struct Client { glm::vec4 pos;
 const glm::vec4& GetPosition() const{return pos;}
 float ProximityX(){return 0;} float ProximityY(){return 0;} float ProximityZ(){return 0;}
};
struct Mob { std::string GetName(){return "unused";} std::string GetCleanName(){return "unused";} int GetNPCTypeID(){return 0;} };
struct Zone { int id=0, version=0; int GetZoneID(){return id;} int GetInstanceVersion(){return version;} } z;
Zone* zone=&z;
struct ActivityInformation {
 int goal_method=0,dz_switch_id=0,zone_version=0; TaskActivityType activity_type{};
 bool has_area=false; float min_x=0,max_x=0,min_y=0,max_y=0,min_z=0,max_z=0;
 std::string item_id_list,npc_match_list; std::vector<int> zone_ids;
 CHECK_ZONE
};
struct ClientActivityInformation { int activity_state=ActivityActive,activity_id=0; };
struct TaskUpdateFilter { int method=0,dz_switch_id=0,item_id=0; TaskActivityType type{};
 bool ignore_area=false,use_pos=false; glm::vec4 pos; Mob* mob=nullptr; };
struct ClientTaskState {
 bool m_has_explore_task=true; int count=0; ActivityInformation activity; ClientActivityInformation state;
 bool CanUpdate(Client*,const TaskUpdateFilter&,int,const ActivityInformation&,const ClientActivityInformation&) const;
 void UpdateTasksOnExplore(Client*,const glm::vec4&);
 void ProcessTaskProximities(Client*,float,float,float);
 void UpdateTasks(Client*c,const TaskUpdateFilter&f) { if(CanUpdate(c,f,9500,activity,state)) ++count; }
};
void check(bool ok){if(!ok)throw std::runtime_error("native task credit mismatch");}
'''.replace('ENUM',enum).replace('CHECK_ZONE',check_zone)
        controls = ['int main(){try{ Client c; ClientTaskState t;']
        for row in task_rows(load_catalog())[1]:
            if row['taskid'] != 9500:
                continue
            controls.append(f't.activity.activity_type=static_cast<TaskActivityType>({row["activitytype"]}); t.activity.zone_ids={{{row["zones"]}}};')
            controls.append(f'z.id={row["zones"]}; z.version=0; t.count=0; t.ProcessTaskProximities(&c,15,20,30); check(t.count==1);')
            controls.append('z.version=1; t.ProcessTaskProximities(&c,15,20,30); check(t.count==1);')
            controls.append('z.version=0; z.id=22; t.ProcessTaskProximities(&c,15,20,30); check(t.count==1);')
        controls.append('std::cout<<"Native journal exploration passed"; }catch(const std::exception&e){std::cerr<<e.what();return 1;} }')
        with tempfile.TemporaryDirectory(prefix='nightcap-task-credit-') as folder:
            out = Path(folder)
            (out/'test.cpp').write_text(fixture + native + '\n'.join(controls))
            if os.name == 'nt':
                (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
                result = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
                self.assertEqual(result.returncode,0,(out/'build.log').read_text())
                exe = out/'test.exe'
            else:
                exe = out/'test'
                subprocess.run(['c++','-std=c++17','test.cpp','-o',str(exe)],cwd=out,check=True)
            result = subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__': unittest.main()
