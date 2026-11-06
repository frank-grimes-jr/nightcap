#pragma once
#include "../../server-mods/code/common/equipped_stats_protocol.h"

namespace nightcap {
// Presentation cache only: no equipment/casting/action authority.
class EquippedStatsState {
    NightcapStats::Snapshot snapshot_{};
    uint64_t received_=0;
    bool valid_=false;
    NightcapStats::Identity requested_identity_{};
    uint64_t requested_since_=0;
    bool requested_=false;
public:
    void Clear(){snapshot_={};received_=0;valid_=false;requested_identity_={};requested_since_=0;requested_=false;}
    void Requested(const NightcapStats::Identity& identity,uint64_t now){
        if(!requested_||requested_identity_!=identity){requested_identity_=identity;requested_since_=now;requested_=true;}
    }
    bool Consume(const char* message,const NightcapStats::Identity& identity,uint64_t now){
        NightcapStats::Snapshot next;
        if(!NightcapStats::Decode(message,next)||next.identity!=identity)return false;
        if(valid_&&snapshot_.identity==identity&&static_cast<int32_t>(next.sequence-snapshot_.sequence)<=0)return false;
        snapshot_=next;received_=now;valid_=true;return true;
    }
    bool Ready(const NightcapStats::Identity& identity,uint64_t now)const{
        return valid_&&snapshot_.identity==identity&&now>=received_&&now-received_<8000;
    }
    std::string Label(int type,const NightcapStats::Identity& identity,uint64_t now)const{
        if(type==10400){
            if(Ready(identity,now))return "Server totals - updates automatically";
            return requested_&&requested_identity_==identity&&now>=requested_since_&&now-requested_since_>=8000?
                "Server totals unavailable":"Updating server totals...";
        }
        if(!Ready(identity,now))return "--";
        const auto& v=snapshot_.values;
        if(type>=10100 && type<10100+static_cast<int>(NightcapStats::Count))return std::to_string(v[type-10100]);
        if(type>=10300 && type<10313){const unsigned first=7+2*(type-10300);return std::to_string(v[first])+"/"+std::to_string(v[first+1]);}
        switch(type){
            case 10200:return std::to_string(v[NightcapStats::ShieldBlock])+"%";
            case 10201:return "+"+std::to_string(v[NightcapStats::HuntBlock])+"% max";
            case 10202:return std::to_string(v[NightcapStats::Dodge])+"% relative";
            case 10203:return v[NightcapStats::SpellHaste]?"up to "+std::to_string(v[NightcapStats::SpellHaste])+"%*":"None";
            case 10204:return v[NightcapStats::ManaMax]?"up to "+std::to_string(v[NightcapStats::ManaMax])+"%*":"None";
            case 10205:return v[NightcapStats::Faerune]?"Active":"None";
            default:return "--";
        }
    }
};
}
