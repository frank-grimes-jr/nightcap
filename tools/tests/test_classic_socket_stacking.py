"""Exercise the shipping socket predicates for legal insertion and replacement."""
from pathlib import Path
import subprocess
import tempfile

from test_aa_temporary_buffs import compile_native
from test_gameplay_policies import function

root = Path(__file__).resolve().parents[2] / 'server-mods/code'
common = (root/'common/item_instance.cpp').read_text(encoding='utf8')
packet = (root/'zone/client_packet.cpp').read_text(encoding='utf8')
handler = function(packet, 'void Client::Handle_OP_AugmentItem(')
start = handler.index('tobe_auged->IsAugmentSlotCompatible(')
stop = handler.index('\n\t\t\t\t\t) {', start)
policy = handler[start:stop]
assert handler.index('in_augment->augment_index > EQ::invaug::SOCKET_END') < handler.index('tobe_auged->GetAugment(')
fixture = r"""
#include "common/visible_ornaments.h"
#include <cassert>
#include <cstdint>
using int32=int32_t; using uint8=uint8_t;
bool allow_hidden=false, enforce=true;
#define RuleB(cat,rule) rule
#define AugmentItemAllowInvisibleAugments allow_hidden
#define EnforceAugmentRestriction enforce
namespace EQ {
namespace invaug { constexpr int SOCKET_BEGIN=0, SOCKET_END=5; }
struct Data {
 int AugSlotType[6]={7,0,22}; bool AugSlotVisible[6]={true,false,true}; int Slots=1,ItemType=10,ItemClass=0,AugType=0;
 bool IsClassCommon()const{return true;}
};
struct ItemInstance {
 Data data; const Data *m_item=&data; bool occupied=false; int type=64;
 const Data *GetItem()const{return &data;}
 const Data *GetItem(int i)const{return occupied && i==0 ? &data : nullptr;}
 const Data *GetAugment(int i)const{return GetItem(i);}
 int GetAugmentType()const{return type;} int GetAugmentRestriction()const{return 1;}
 int GetItemType()const{return 10;}
 bool AvailableWearSlot(int slots)const{return slots & data.Slots;}
 bool IsAugmentSlotAvailable(int32,uint8)const;bool IsAugmentSlotCompatible(int32,int32)const;
};
}
enum class AugmentActions {Insert,Swap};
struct Request{int augment_index;AugmentActions augment_action;};
bool IsAugmentRestricted(int,int){return false;}
"""
body = '\n'.join(function(common, key) for key in (
    'bool EQ::ItemInstance::IsAugmentSlotAvailable(', 'bool EQ::ItemInstance::IsAugmentSlotCompatible('))
entry = 'bool allowed(EQ::ItemInstance *tobe_auged, EQ::ItemInstance *new_aug, Request *in_augment){return '+policy+';}'
tests = r"""
int main(){
 EQ::ItemInstance host,scale;
 Request in{0,AugmentActions::Insert},swap{0,AugmentActions::Swap};
 assert(allowed(&host,&scale,&in) && !allowed(&host,&scale,&swap));
 host.occupied=true;
 assert(!allowed(&host,&scale,&in) && allowed(&host,&scale,&swap));
 assert(!host.IsAugmentSlotAvailable(64,0));
 assert(host.IsAugmentSlotCompatible(64,0));
 host.occupied=false;
 assert(!host.IsAugmentSlotCompatible(64,2));
 assert(host.IsAugmentSlotCompatible(1<<21,2));
 assert(!host.IsAugmentSlotCompatible(64,6));
 host.data.AugSlotVisible[0]=false; assert(!allowed(&host,&scale,&in));
 allow_hidden=true;assert(allowed(&host,&scale,&in));
}
"""
if __name__=='__main__':
    with tempfile.TemporaryDirectory() as tmp:
        exe=compile_native(Path(tmp),fixture.replace("common/visible_ornaments.h", (root/"common/visible_ornaments.h").as_posix())+body+entry+tests)
        subprocess.run([str(exe)],check=True)
    print('Native socket compatibility, occupancy, replacement and visibility checks passed.')
