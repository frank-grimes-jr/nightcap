"""Compile actual SetEXP along with the award methods; boundary services are fakes."""
import test_level_aa
h = test_level_aa.harness
source = (h.ROOT/'server-mods/code/zone/exp.cpp').read_text()
old = h.function(h.PRELUDE,'void Client::SetEXP(ExpSource,uint64 xp')
h.PRELUDE = h.PRELUDE.replace(old,'')
h.PRELUDE = h.PRELUDE.replace('using uint8=', 'using int8=int8_t;\nusing uint8=',1)
h.PRELUDE = h.PRELUDE.replace('enum { White,Red,Yellow };','enum { White,Red,Yellow,Experience };',1)
h.PRELUDE = h.PRELUDE.replace('struct EQApplicationPacket { uint32 size; void* pBuffer; };',r"""
struct ExpUpdate_Struct {uint32 exp;};
enum {OP_ExpUpdate=101};
struct EQApplicationPacket {
    uint32 size; void* pBuffer; bool owned=false;
    EQApplicationPacket(uint32 n,void* p):size(n),pBuffer(p){}
    EQApplicationPacket(int,size_t n):size(uint32(n)),pBuffer(new unsigned char[n]),owned(true){}
    ~EQApplicationPacket(){if(owned)delete[] static_cast<unsigned char*>(pBuffer);}
};
""")
extra=r"""
#define MAX_GROUP_MEMBERS 6
struct Group {void* members[6]={};};
enum {EVENT_AA_GAIN,EVENT_EXP_GAIN,EVENT_AA_EXP_GAIN};
struct Parser {bool PlayerHasQuestSub(int){return false;} template<class...T>void EventPlayer(T...){};} parser,*parse=&parser;
struct Queries {void SendQuery(std::string){}} queries,*QServ=&queries;
namespace AccountStatus {enum {GMAdmin=80};}
namespace EQ {namespace versions {enum {maskUFAndEarlier=1};}}
namespace PlayerEvent {enum {AA_GAIN};struct AAGainedEvent {uint32 gained;};}
struct Bot {template<class...T>static void LevelBotWithClient(T...){}};
template<class...T>std::string StringFormat(const char*,T...){return "";}
template<class T>char* ConvertArray(T,char* out){out[0]=0;return out;}
enum {REZ_REGAIN,GAIN_GROUPXP,GAIN_RAIDEXP,GAIN_XP,GAIN_SINGLE_AA_SINGLE_AA,GAIN_SINGLE_AA_MULTI_AA,GAIN_MULTI_AA_MULTI_AA,GAIN_LEVEL,CORPSE_ITEM_LOST,CORPSE_EXP_LOST,GM_GAINXP};
"""
h.PRELUDE=h.PRELUDE.replace('struct Client {',extra+'\nstruct Client {',1)
h.PRELUDE=h.PRELUDE.replace('    bool enabled=true;',r"""
    int admin=0;uint32 m_ClientVersionBit=0;
    const char* GetCleanName(){return "Test";}
    uint32 CharacterID(){return 1;}
    bool GetGM(){return false;}
    Group* GetGroup(){return nullptr;}
    bool IsRaidGrouped(){return false;}
    int GetMercenaryID(){return 0;}
    void UpdateMercLevel(){}
    void ProcessEvolvingItem(uint64,NPC*){}
    void SendSound(){}
    template<class...T>void RecordPlayerEventLog(T...){}
    void SetLevel(uint8 value,bool=false){level=value;}
    void FastQueuePacket(EQApplicationPacket** p){delete *p;*p=nullptr;}
    bool enabled=true;
""",1)
base_function=h.function
def extract(text,signature):
    body=base_function(text,signature)
    if signature=='void Client::AddLevelBasedExp':
        body+='\n'+base_function(source,'void Client::SetEXP(')
    return body
h.function=extract
h.CASES=r"""
void scaled() {
    reset();rules["AA:LevelBasedPointsPerLevel"]=20;rules["AA:PassiveExpPercent"]=10;
    rules["AA:ExpPerPoint"]=1000000;rules["Character:ExpMultiplier"]=1;
    rules["Character:MaxExpLevel"]=50;
}
Client at(int level) {Client c;c.level=level;c.m_pp.exp=c.GetEXPForLevel(level);return c;}
int main() {
    scaled();Client c=at(1);c.AddEXP(Quest,1000);
    check(c.GetLevel()==2 && c.GetEXP()==1000 && c.GetAAPoints()==2,"actual SetEXP advances level and awards passive AA");
    scaled();c=at(1);c.AddEXP(Quest,c.GetEXPForLevel(50));
    check(c.GetLevel()==50 && c.GetAAPoints()==98,"actual SetEXP handles continuous1to50 award");
    scaled();c=at(49);
    const uint64 top=c.GetEXPForLevel(51),cap_start=c.GetEXPForLevel(50),level49_start=c.GetEXP();
    c.AddEXP(Quest,cap_start-level49_start+1);
    check(c.GetLevel()==50 && c.GetEXP()==cap_start+1 && c.GetAAPoints()==2,"49to50 overflow uses both level spans");
    scaled();c=at(50);c.m_pp.exp=top;
    c.AddEXP(Quest,top-cap_start);
    check(c.GetLevel()==50 && c.GetEXP()==top && c.GetAAPoints()==2,"actual SetEXP clamps normal cap but retains passive AA");
    scaled();c=at(1);c.SetAAExperiencePercent(100);c.m_pp.expAA=170000;
    for(int i=0;i<10;++i)c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetLevel()==1 && c.GetEXP()==0 && c.GetAAPoints()==200 && c.GetAAXP()==170000,"repeated full focus never levels and keeps partial progress");
    scaled();c=at(1);c.SetAAExperiencePercent(100);rules["AA:UnusedAAPointCap"]=5;
    c.AddEXP(Quest,1000);c.AddEXP(Quest,1000);
    check(c.GetLevel()==1 && c.GetEXP()==0 && c.GetAAPoints()==5 && c.GetAAPercent()==100,"actual bank cap keeps leveling paused");
    scaled();c=at(1);c.SetAAExperiencePercent(50);c.AddEXP(Quest,16000);
    check(c.GetLevel()==3 && c.GetEXP()==8000 && c.GetAAPoints()==44,"actual partial-allocation multi-level conversion");
    scaled();c=at(2);c.m_pp.expAA=123456;c.SetEXP(Death,0,c.GetAAXP());
    check(c.GetLevel()==1 && c.GetAAXP()==123456 && c.GetAAPoints()==0,"actual delevel retains AA fraction without minting");
    std::cout<<checks<<" actual SetEXP integration checks, "<<failures<<" failures\n";
    return failures?1:0;
}
"""
if __name__ == '__main__':h.main()
