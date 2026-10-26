"""Compile the actual native pool-roll method against deterministic minimal fixtures."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile
from loot_model import drop_probability

PREAMBLE=r'''
#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <vector>
using uint32=uint32_t; using uint8=uint8_t;
#define LogLootDetail(...) ((void)0)
namespace EQ {struct ItemData {int ID;};template<class T>T ClampLower(T a,T b){return std::max(a,b);}}
struct Entry {int item_id;float chance;int multiplier;int npc_min_level=0;int npc_max_level=0;};
struct Random {std::mt19937 rng{98765};double Real(double a,double b){return std::uniform_real_distribution<double>(a,b)(rng);}};
struct Zone {Random random;std::vector<Entry> entries;struct Drop {int id;};Drop GetLootdrop(int){return {1};}auto GetLootdropEntries(int){return entries;}} zone_value;
Zone *zone=&zone_value;
struct Database {EQ::ItemData items[3]={{0},{1},{2}};const EQ::ItemData*GetItem(int id){return &items[id];}} database;
struct NPC {int hits=0;double quality=1;int level=50;void AddLootDropTable(uint32,uint8,uint8);
 bool MeetsLootDropLevelRequirements(Entry e,bool=false){return (!e.npc_min_level||level>=e.npc_min_level)&&(!e.npc_max_level||level<=e.npc_max_level);}
 void AddLootDrop(const EQ::ItemData*i,Entry){if(i->ID==1&&zone->random.Real(0,1)<quality)++hits;}
 void UpdateEquipmentLight(){}
};
'''
CASES=[([(.5,1,1)],0,0,100,1,4,1), # chance below overwritten below for clarity
       ([(10,1,1),(90,1,2)],1,1,100,1,1,1),
       ([(10,1,1),(10,1,2)],2,1,100,1,1,1),
       ([(50,3,1),(25,1,2)],2,0,50,1,4,.2),
       ([(100,1,1)],0,0,100,1,4,.01),
       ([(150,2,1),(50,1,2)],3,1,75,2,4,.05)]
CASES[0]=([(50,1,1)],0,0,100,1,4,1)


def check(source, compiler='g++'):
    text=Path(source).read_text(encoding='utf-8')
    method=text[text.index('void NPC::AddLootDropTable('):text.index('bool NPC::MeetsLootDropLevelRequirements(')]
    main=['int main(){NPC npc;const int samples=200000;std::cout<<std::setprecision(9);']
    expected=[]
    for rows,limit,minimum,probability,multiplier,global_multiplier,quality in CASES:
        entries=[dict(item_id=i,chance=c,multiplier=m) for c,m,i in rows]
        expected.append(drop_probability(entries,{1:quality},limit,minimum,probability,multiplier,global_multiplier))
        literal=','.join('{'+f'{i},{float(c)}f,{m}'+'}' for c,m,i in rows)
        main.append('zone->entries={'+literal+'};'+f'npc.quality={quality};'+'{int successes=0;for(int n=0;n<samples;++n){npc.hits=0;'+f'for(int j=0;j<{multiplier*global_multiplier};++j)if(zone->random.Real(0,100)<={probability})npc.AddLootDropTable(1,{limit},{minimum});'+'if(npc.hits)++successes;}std::cout<<double(successes)/samples<<"\\n";}')
    main.append('}')
    with tempfile.TemporaryDirectory(prefix='nightcap-native-loot-') as directory:
        path=Path(directory);(path/'check.cpp').write_text(PREAMBLE+method+'\n'.join(main))
        subprocess.run([compiler,'-O2','-std=c++17',str(path/'check.cpp'),'-o',str(path/'check')],check=True,capture_output=True,text=True)
        observed=list(map(float,subprocess.check_output([str(path/'check')],text=True).split()))
    if len(observed)!=len(expected) or any(abs(a-b)>.006 for a,b in zip(expected,observed)):
        raise AssertionError({'expected':expected,'observed':observed})
    return {'native_method_sha256':hashlib.sha256(method.encode()).hexdigest(),'samples_per_case':200000,
            'maximum_absolute_error':max(abs(a-b) for a,b in zip(expected,observed)),
            'cases':[{'expected':a,'observed':b} for a,b in zip(expected,observed)]}

if __name__=='__main__':
    import sys
    print(json.dumps(check(sys.argv[1]),indent=2))
