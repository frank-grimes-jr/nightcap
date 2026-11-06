#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace NightcapStats {
enum Field : unsigned {
    ShieldBlock, HuntBlock, Dodge, SpellHaste, ManaBase, ManaMax, Faerune,
    Shielding, ShieldingCap, SpellShield, SpellShieldCap, DamageShield, DamageShieldCap,
    DotShield, DotShieldCap, DamageShieldMitigation, DamageShieldMitigationCap,
    Avoidance, AvoidanceCap, Accuracy, AccuracyCap, StunResist, StunResistCap,
    Strikethrough, StrikethroughCap, Heal, HealCap, SpellDamage, SpellDamageCap,
    Clairvoyance, ClairvoyanceCap, CombatEffects, CombatEffectsCap, Count
};
using Identity=std::array<uint32_t,5>; // class generation, character, zone, instance, spawn
struct Snapshot { Identity identity{}; uint32_t sequence=0; std::array<int32_t,Count> values{}; };
constexpr size_t MaxMessage=512;
inline std::string Encode(const Snapshot& value) {
    std::string message="[NCST1]";
    for(auto id:value.identity) message+='|'+std::to_string(id);
    message+='|'+std::to_string(value.sequence);
    for(auto stat:value.values) message+='|'+std::to_string(stat);
    return message.size()<MaxMessage?message:std::string{};
}
inline bool Decode(const char* message,Snapshot& output) {
    if(!message)return false;
    size_t size=0;while(size<MaxMessage && message[size])++size;
    if(size==MaxMessage || size<9)return false;
    const std::string_view text(message,size);
    if(text.substr(0,8)!="[NCST1]|")return false;
    Snapshot result;
    size_t start=8;
    for(unsigned field=0;field<Count+6;++field) {
        const size_t end=text.find('|',start);
        const auto token=text.substr(start,end==std::string_view::npos?size-start:end-start);
        if(token.empty() || token.size()>11 || (field+1==Count+6)!=(end==std::string_view::npos))return false;
        const bool negative=token[0]=='-';
        if(negative && field<6)return false;
        size_t i=negative?1:0;if(i==token.size())return false;
        uint64_t number=0;
        const uint64_t limit=field<6?UINT32_MAX:negative?uint64_t(INT32_MAX)+1:INT32_MAX;
        for(;i<token.size();++i) {
            const char c=token[i];if(c<'0'||c>'9')return false;
            number=number*10+static_cast<unsigned>(c-'0');if(number>limit)return false;
        }
        if(field<5)result.identity[field]=static_cast<uint32_t>(number);
        else if(field==5)result.sequence=static_cast<uint32_t>(number);
        else result.values[field-6]=static_cast<int32_t>(negative?-static_cast<int64_t>(number):static_cast<int64_t>(number));
        start=end==std::string_view::npos?size:end+1;
    }
    if(!result.identity[0]||!result.identity[1]||!result.identity[2]||!result.identity[4])return false;
    for(unsigned i=ShieldingCap;i<Count;i+=2)if(result.values[i]<0)return false;
    if(result.values[Faerune]<0||result.values[Faerune]>1)return false;
    output=result;return true;
}
}
