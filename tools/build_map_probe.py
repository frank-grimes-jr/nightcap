"""Build a read-only geometry probe from the server's actual map loader/raycaster.

Run with container Python. No database, networking or live executable is used.
The generated harness retains native geometry transforms and collision code;
only diagnostic logging is replaced. JSON stdin selects a map and probe points.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path

HEADER=r'''
#include <cstdio>
#include <cstdint>
#include <cmath>
#include <map>
#include <memory>
#include <tuple>
#include <vector>
#include <iostream>
#include <glm/glm.hpp>
#include "common/json/json.hpp"
#include <zlib.h>
#include "raycast_mesh.h"
using uint32=uint32_t; using uint16=uint16_t; using uint8=uint8_t;
namespace EQ { uint32 InflateData(const char *data,uint32 size,char *out,uint32 cap) {
 uLongf n=cap; if(uncompress((Bytef*)out,&n,(const Bytef*)data,size)!=Z_OK || n!=cap) throw std::runtime_error("Invalid map compression"); return n;
} }
class Map {
 struct impl { RaycastMesh *rm=nullptr; }; impl *imp=nullptr;
 void RotateVertex(glm::vec3&,float,float,float); void ScaleVertex(glm::vec3&,float,float,float); void TranslateVertex(glm::vec3&,float,float,float);
public:
 bool LoadV1(FILE*); bool LoadV2(FILE*);
 ~Map(){if(imp){if(imp->rm)imp->rm->release();delete imp;}}
 bool ray(glm::vec3 a,glm::vec3 b,glm::vec3 &hit) {float distance;return imp->rm->raycast(&a.x,&b.x,&hit.x,nullptr,&distance);}
};
'''
MAIN=r'''
int main() {try {
 using json=nlohmann::json;json input;std::cin>>input;Map map;
 auto path=input.at("map").get<std::string>();FILE*f=fopen(path.c_str(),"rb");if(!f)throw std::runtime_error("Missing map");
 uint32 version=0;if(fread(&version,4,1,f)!=1)throw std::runtime_error("Missing header");
 bool loaded=version==0x02000000?map.LoadV2(f):version==0x01000000?map.LoadV1(f):false;fclose(f);
 if(!loaded)throw std::runtime_error("Map load failed");json output={{"map",path},{"points",json::array()}};
 for(auto p:input.at("points")) {
  float x=p.at("x"),y=p.at("y"),z=p.at("z");json samples=json::array();
  for(auto off:std::vector<glm::vec2>{{0,0},{4,0},{-4,0},{0,4},{0,-4}}) {
   glm::vec3 hit;bool ok=map.ray({x+off.x,y+off.y,z+8},{x+off.x,y+off.y,-99999},hit);
   json s={{"dx",off.x},{"dy",off.y},{"ground_hit",ok}};
   if(ok){s["ground_z"]=hit.z;glm::vec3 ceiling;bool up=map.ray({hit.x,hit.y,hit.z+1},{hit.x,hit.y,hit.z+80},ceiling);s["headroom"]=up?ceiling.z-hit.z:80;}
   samples.push_back(s);
  }
  p["samples"]=samples;output["points"].push_back(p);
 }
 output["segments"]=json::array();
 for(auto s:input.value("segments",json::array())) {
  auto a=s.at("from").get<std::vector<float>>(),b=s.at("to").get<std::vector<float>>();glm::vec3 hit;
  s["blocked"]=map.ray({a.at(0),a.at(1),a.at(2)},{b.at(0),b.at(1),b.at(2)},hit);output["segments"].push_back(s);
 }
 std::cout<<output.dump(2)<<"\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    code=(a.source/'zone/map.cpp').read_text()
    start=code.index('bool Map::LoadV1(FILE *f)');end=code.index('\n#ifdef USE_MAP_MMFS',code.index('void Map::TranslateVertex'))
    (a.output/'probe.cpp').write_text(HEADER+code[start:end]+MAIN)
    files=['zone/map.cpp','zone/raycast_mesh.cpp','zone/raycast_mesh.h','common/memory/ksm.hpp']
    for name in files[1:]:
        out=a.output/(name.removeprefix('zone/'));out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((a.source/name).read_bytes())
    (a.output/'common/eqemu_logsys.h').write_text('#pragma once\n#define LogInfo(...) ((void)0)\n#define LogKSM(...) ((void)0)\n#define LogKSMDetail(...) ((void)0)\n')
    subprocess.run(['clang++','-std=c++20','-O2','-Wno-unknown-pragmas','-I.','-I'+str(a.source),'-I/home/eqemu/code/build/vcpkg_installed/x64-linux/include','probe.cpp','raycast_mesh.cpp','-lz','-o','map-probe'],cwd=a.output,check=True)
    manifest={name:hashlib.sha256((a.source/name).read_bytes()).hexdigest() for name in files}
    manifest['probe_sha256']=hashlib.sha256((a.output/'map-probe').read_bytes()).hexdigest()
    (a.output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
if __name__=='__main__':main()
