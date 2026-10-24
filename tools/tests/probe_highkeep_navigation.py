"""Offline route check using the retained native loader and FindRoute implementation."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from test_heal_targeting import function

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = 'akk-stack-eqemu-server-1'
SOURCE = '/tmp/nightcap-chapterhouse-v1/source/zone/pathfinder_nav_mesh.cpp'
NAV = '/home/eqemu/server/maps/nav/highkeep.nav'
LIB = '/home/eqemu/code/build/vcpkg_installed/x64-linux'


def main():
    native = subprocess.check_output(['docker', 'exec', CONTAINER, 'cat', SOURCE], text=True)
    selected = '\n'.join(function(native, s) for s in
        ('void PathfinderNavmesh::Load(', 'void PathfinderNavmesh::Clear(',
         'IPathfinder::IPath PathfinderNavmesh::FindRoute('))
    code = r'''
#include <glm/vec3.hpp>
#include <recastnavigation/DetourNavMesh.h>
#include <recastnavigation/DetourNavMeshQuery.h>
#include <recastnavigation/DetourAlloc.h>
#include <zlib.h>
#include <vector>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <string>
#include <cassert>
#include <cmath>
#define RuleI(a,b) 4096
#define LogInfo(...)
namespace EQ { uint32_t InflateData(char* in,uint32_t n,char* out,uint32_t capacity) {
 uLongf size=capacity;return uncompress(reinterpret_cast<Bytef*>(out),&size,reinterpret_cast<Bytef*>(in),n)==Z_OK?size:0;
}}
float DistanceSquared(const glm::vec3&a,const glm::vec3&b){auto d=a-b;return d.x*d.x+d.y*d.y+d.z*d.z;}
struct Node {glm::vec3 pos;bool teleport=false;Node(glm::vec3 p):pos(p){}Node(bool t):teleport(t){}};
struct IPathfinder {using IPath=std::vector<Node>;};
class PathfinderNavmesh:public IPathfinder {
 struct Implementation {dtNavMesh*nav_mesh=nullptr;dtNavMeshQuery*query=nullptr;} storage;
 Implementation*m_impl=&storage;
 public:
 void Load(const std::string&path);void Clear();
 IPath FindRoute(const glm::vec3&start,const glm::vec3&end,bool&partial,bool&stuck,int flags);
};
''' + selected + r'''
int main(){
 PathfinderNavmesh mesh;mesh.Load("/home/eqemu/server/maps/nav/highkeep.nav");
 const glm::vec3 points[]={{-546,-52,-10.13f},{-513,-3,-10.13f},{-306,31,-10.13f},{48,-28,3.75f},{88,-16,4}};
 printf("[");
 for(unsigned i=0;i<8;++i){
  const auto start=points[i%4+(i>=4)],end=points[i%4+(i<4)];
  bool partial=false,stuck=false;auto route=mesh.FindRoute(start,end,partial,stuck,65535 ^ 2048);
  assert(!partial&&!stuck&&route.size()>1);unsigned teleport=0;float length=0;
  for(unsigned n=0;n<route.size();++n){teleport+=route[n].teleport;if(n&&!route[n].teleport&&!route[n-1].teleport)length+=sqrt(DistanceSquared(route[n].pos,route[n-1].pos));}
  assert(teleport==0&&DistanceSquared(route.back().pos,end)<1);
  printf("%s{\"leg\":%u,\"nodes\":%zu,\"length\":%.2f,\"partial\":false,\"teleports\":%u}",i?",":"",i,route.size(),length,teleport);
 }
 printf("]\n");mesh.Clear();
}
'''
    binary = '/tmp/nightcap-highkeep-nav-' + uuid.uuid4().hex
    try:
        subprocess.run(['docker', 'exec', '-i', CONTAINER, 'g++', '-std=c++17', '-O0',
                        '-I' + LIB + '/include', '-x', 'c++', '-', '-o', binary,
                        '-L' + LIB + '/lib', '-lDetour', '-lz'], input=code, text=True, check=True)
        result = json.loads(subprocess.check_output(['docker', 'exec', CONTAINER, binary], text=True))
        digest = subprocess.check_output(['docker', 'exec', CONTAINER, 'sha256sum', NAV], text=True).split()[0]
        report = dict(status='native FindRoute connectivity passed', legs=result, nav_sha256=digest,
                      native_source_sha256=hashlib.sha256(native.encode()).hexdigest(),
                      limitation='Static navmesh route only; actual follow movement, doors and client visibility require gameplay QA.',
                      production_changed=False)
        (ROOT / 'docs/dungeons/highkeep-rescue/navigation.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    finally:
        subprocess.run(['docker', 'exec', CONTAINER, 'rm', '-f', binary], check=True)


if __name__ == '__main__':
    main()
