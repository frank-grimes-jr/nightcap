#include <cassert>
#include <iostream>
#include "../../server-mods/code/common/aa_recommendations.h"
#include "../src/ui_state.h"
using namespace nightcap::recommended_aa;
int main() {
    std::vector<Choice> rows;
    for (unsigned i=1;i<=15;++i) rows.push_back({i,i,1,1,0,static_cast<int>(i)});
    rows.push_back({99,99,1,1,2,-100}); // later must not crowd out useful now
    auto result=Select(rows); assert(result.size()==10 && result[0].rank==1 && result.back().rank==10);
    rows={{5,5,3,1,0,1},{5,5,3,2,0,2},{6,6,1,1,1,0}};
    result=Select(rows); assert(result.size()==2 && result[0].rank==5);
    assert(Reason(1)==std::string("More health")); assert(Reason(999).empty());
    nightcap::UIState state;
    assert(state.Consume("[NCUI1]S|1|42|63|0|7|3|1|7|Palwar"));
    assert(!state.RecommendationsReady());
    assert(state.Consume("[NCUI1]B|1|42|63|0|7|1"));
    assert(state.Consume("[NCUI1]R|1|42|63|0|7|100|1|0|3"));
    assert(!state.Recommended(100)); // no partially received list
    assert(!state.Consume("[NCUI1]R|1|43|63|0|7|101|1|0|3"));
    assert(!state.Consume("[NCUI1]R|1|42|63|0|7|101|99|0|3"));
    assert(state.Consume("[NCUI1]E|1|42|63|0|7"));
    assert(state.RecommendationsReady() && state.Recommended(100) && !state.Recommended(101));
    assert(state.Recommendation(100)=="More health (aim: 3)");
    assert(!state.Consume("[NCUI1]R|1|42|63|0|7|101|1|0|3"));
    assert(state.Consume("[NCUI1]B|1|42|63|0|7|1"));
    assert(state.Consume("[NCUI1]R|1|42|63|0|7|101|4|2|1"));
    assert(state.Recommended(100)); // old complete snapshot survives until commit
    assert(state.Consume("[NCUI1]E|1|42|63|0|7"));
    assert(!state.Recommended(100) && state.Recommended(101));
    assert(state.Recommendation(101).find("Later:")==0);
    assert(state.Consume("[NCUI1]S|2|42|63|0|7|3|1|0|Palwar"));
    assert(!state.RecommendationsReady() && !state.Recommended(101));
    assert(!state.Consume("[NCUI1]B|1|42|63|0|7|1"));
    assert(state.Consume("[NCUI1]B|2|42|63|0|7|0"));
    assert(state.Consume("[NCUI1]E|2|42|63|0|7"));
    assert(state.RecommendationsReady() && state.RecommendationCount()==0);
    assert(state.Consume("[NCUI1]B|2|42|63|0|7|2"));
    assert(state.Consume("[NCUI1]R|2|42|63|0|7|101|1|0|1"));
    assert(!state.Consume("[NCUI1]E|2|42|63|0|7")); // incomplete batch cannot replace the complete snapshot
    assert(state.RecommendationCount()==0);
    assert(!state.Consume("[NCUI1]B|2|42|63|0|7|11"));
    state.Clear(); assert(!state.RecommendationsReady());
    std::cout << "AA shortlist and atomic identity-scoped metadata checks passed\n";
}
