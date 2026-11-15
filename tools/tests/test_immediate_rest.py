"""Compile the actual aggro transitions and HP/mana recovery floor with controlled inputs."""
from pathlib import Path
import tempfile
import subprocess
from test_gameplay_policies import function
from test_aa_temporary_buffs import compile_native

ROOT=Path(__file__).resolve().parents[2]
zone=ROOT/'server-mods/code/zone'
source=(zone/'client.cpp').read_text(encoding='utf8')
types=r"""
#include <algorithm>
#include <cassert>
using uint32=unsigned;
using uint8=unsigned char;
#define RuleB(cat,name) true
#define RuleI(cat,name) 0
namespace EQ::versions {enum ClientVersion {SoF};}
struct EQApplicationPacket {unsigned char data[8]={}; unsigned char *pBuffer=data; EQApplicationPacket(int,int){}};
#define VARSTRUCT_ENCODE_TYPE(T,buf,val) ((void)(buf),(void)(val))
#define safe_delete(x) delete x
constexpr int OP_RestState=0;
struct Client{
 unsigned AggroCount=0; struct {unsigned RestTimer=0;} m_pp;
 struct {unsigned left=999;unsigned GetRemainingTime(){return left;} void Start(unsigned time){if(time)left=time;} void Trigger(){left=0;}} rest_timer;
 struct {void ClearSpend(){}} raid_augment;
 auto ClientVersion(){return EQ::versions::SoF;} void QueuePacket(EQApplicationPacket*){}
 void IncrementAggroCount(bool);void DecrementAggroCount();
};
"""
test=r"""
int main(){
 for(bool raid:{false,true}){
  Client c;c.IncrementAggroCount(raid);c.IncrementAggroCount(!raid);
  c.DecrementAggroCount();assert(c.AggroCount==1 && c.rest_timer.left==999);
  c.DecrementAggroCount();assert(!c.AggroCount && !c.m_pp.RestTimer && !c.rest_timer.left);
 }
 static_assert(NightcapRest::RecoveryFloor(6000,180)==218);
 static_assert(NightcapRest::RecoveryFloor(3000,180)==106);
 static_assert(NightcapRest::RecoveryFloor(3000,0)==106);
 static_assert(NightcapRest::RecoveryFloor(3000,60)==330);
}
"""
if __name__=='__main__':
    body='\n'.join(function(source,sig) for sig in ('void Client::IncrementAggroCount(', 'void Client::DecrementAggroCount('))
    with tempfile.TemporaryDirectory() as folder:
        exe=compile_native(Path(folder),'#include "'+(zone/'nightcap_rest.h').as_posix()+'"\n'+types+body+test)
        subprocess.run([str(exe)],check=True)
    print('Regular, raid, overlapping aggro and recovery floors passed.')
