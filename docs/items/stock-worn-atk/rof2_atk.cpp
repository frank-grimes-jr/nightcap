#include "common/item_instance.h"
#include "common/item_data.h"
#include "common/memory_buffer.h"
#include "common/eq_packet_structs.h"
#include "common/patches/rof2_structs.h"
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
namespace RoF2 { void SerializeItem(EQ::OutBuffer&, const EQ::ItemInstance*, int16,uint8,ItemPacketType); }
int main(int argc,char** argv) {
 if(argc==1){std::cout<<sizeof(EQ::ItemData)<<" "<<offsetof(EQ::ItemData,ID)<<" "<<offsetof(EQ::ItemData,Attack)<<" "<<sizeof(EQ::ItemData::Attack)<<"\n";return 0;}
 std::ifstream f(argv[1],std::ios::binary); uint32 header[4];f.read((char*)header,sizeof header);
 uint32 id=0;while(std::cin>>id){
  assert(id<header[1]);uint32 idx;f.seekg(16+4*id);f.read((char*)&idx,4);assert(idx<header[3]);
  EQ::ItemData item{};f.seekg(16+4*header[1]+size_t(idx)*sizeof(item));f.read((char*)&item,sizeof item);
  assert(f && item.ID==id && !item.EvolvingItem);
  EQ::ItemInstance inst(&item,1);EQ::OutBuffer out;RoF2::SerializeItem(out,&inst,9,0,ItemPacketViewLink);
  auto packet=out.str();using namespace RoF2::structs;size_t pos=sizeof(ItemSerializationHeader);
  auto skip=[&](){auto end=packet.find('\0',pos);assert(end!=std::string::npos);pos=end+1;};skip();skip();
  pos+=sizeof(ItemSerializationHeaderFinish);assert(packet.compare(pos,strlen(item.Name)+1,item.Name,strlen(item.Name)+1)==0);
  skip();skip();skip();skip();ItemBodyStruct body{};memcpy(&body,packet.data()+pos,sizeof body);assert(body.id==id);
  pos+=sizeof body;skip();pos+=sizeof(ItemSecondaryBodyStruct);skip();ItemTertiaryBodyStruct tertiary{};
  assert(pos+sizeof tertiary<=packet.size());memcpy(&tertiary,packet.data()+pos,sizeof tertiary);assert(tertiary.atk==item.Attack);
  std::cout<<id<<" "<<int(item.Attack)<<" "<<int(tertiary.atk)<<"\n";
 }
}
