#include "../src/runtime_config.h"
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
int main(int argc,char** argv) {
    if(argc!=2)return 3;
    std::ifstream file(argv[1],std::ios::binary);
    if(!file)return 3;
    std::string bytes((std::istreambuf_iterator<char>(file)),std::istreambuf_iterator<char>());
    nightcap::RuntimeConfig config;
    const char* reason=nullptr;
    const bool valid=nightcap::ParseRuntimeConfig(bytes.data(),bytes.size(),config,reason);
    printf("valid=%d mask=%u survey=%d reason=%s\n",valid,config.enabled_mask,config.mq2_survey,reason);
    return valid?0:2;
}
