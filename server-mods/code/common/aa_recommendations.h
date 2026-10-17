#pragma once
#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

// Presentation policy only. Native class, era, ownership and purchase checks
// remain authoritative. Targets are advice, never new purchase/rank gates.
namespace nightcap { namespace recommended_aa {
enum Gate { Always, MonkSpecial, Mend, Backstab, Archery, Throwing, Pet };
struct Entry { int ability, target, reason, priority; Gate gate; };
inline constexpr Entry kEntries[] = {
    {28,3,1,0,Always}, {34,3,2,1,Always}, {33,3,3,2,Always},
    {30,3,4,3,Always}, {310,3,4,3,Always}, {311,3,4,3,Always},
    {23,3,5,4,Always}, {206,3,6,4,MonkSpecial},
    {18,3,7,5,Always}, {20,3,8,6,Always},
    {3512,3,9,3,Pet}, {3818,3,10,4,Pet},
    {248,3,11,5,Pet}, {266,3,11,5,Pet}, {278,3,11,5,Pet},
    {225,3,12,7,Always}, {13,3,13,8,Always},
    {90,3,14,3,Always}, {118,3,14,4,Always},
    {271,3,15,9,Always}, {274,3,16,10,MonkSpecial},
    {281,3,17,9,Backstab}, {82,3,18,9,Archery}, {367,3,19,9,Throwing},
    {97,3,20,9,Mend}, {19,3,21,11,Always}, {214,3,22,11,Always},
    {125,1,23,10,Pet}, {3202,1,23,10,Pet},
    // Specialization follows completion of these modest starter targets.
    {75,3,24,20,Always}, {114,3,5,20,Always}, {215,3,5,20,Always},
    {268,3,10,20,Pet}, {269,3,9,20,Pet}
};
inline std::string Reason(unsigned reason) {
    static const char* const names[]={"", "More health", "Avoid melee hits", "Improve armor defense",
        "Melee critical hits", "Spell critical hits", "Extra Monk attacks", "Stronger heals",
        "Cheaper spells", "More pet health", "Pet avoidance", "Pet critical hits",
        "Health recovery", "Faster movement", "Stronger songs", "Bypass melee avoidance",
        "Stronger kicks", "Extra backstabs", "Archery damage", "Throwing damage",
        "Improve Mend", "Critical heals", "Stronger lifetaps", "Pet control",
        "Damage against undead", "Needed prerequisite"};
    return reason < sizeof(names)/sizeof(names[0]) ? names[reason] : "";
}
struct Choice {
    uint32_t rank, ability, target, reason, status; // 0 useful now; 1 prereq; 2 supporting skill/pet
    int priority;
};
inline std::vector<Choice> Select(std::vector<Choice> choices) {
    std::stable_sort(choices.begin(),choices.end(),[](const Choice& a,const Choice& b) {
        if (a.status != b.status) return a.status < b.status;
        if (a.priority != b.priority) return a.priority < b.priority;
        return a.ability < b.ability;
    });
    std::vector<Choice> result;
    for (const auto& choice:choices) {
        if (std::any_of(result.begin(),result.end(),[&](const Choice& row){return row.ability==choice.ability;})) continue;
        result.push_back(choice);
        if (result.size()==10) break;
    }
    return result;
}
}}
