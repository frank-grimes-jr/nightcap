"""Shared bounded wire format and client freshness/identity/display policy."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]


class EquippedStatsProtocol(unittest.TestCase):
    def test_snapshot_extremes_replay_identity_expiry_and_labels(self):
        header=(ROOT/'eq-client-dll/src/equipped_stats_state.h').as_posix()
        source=r'''
#include <cassert>
#include <climits>
#include "HEADER"
using namespace NightcapStats;
int main(){
 Snapshot s; s.identity={1,29,39,0,500};s.sequence=100;
 s.values[ShieldBlock]=16;s.values[HuntBlock]=1;s.values[Dodge]=10;
 s.values[SpellHaste]=15;s.values[ManaBase]=1;s.values[ManaMax]=10;s.values[Faerune]=1;
 s.values[Heal]=92;s.values[HealCap]=780;s.values[SpellDamage]=29;s.values[SpellDamageCap]=770;
 Snapshot decoded;auto frame=Encode(s);assert(Decode(frame.c_str(),decoded));assert(decoded.values==s.values);
 nightcap::EquippedStatsState state;assert(state.Label(10200,s.identity,1000)=="--");
 state.Requested(s.identity,0);assert(state.Label(10400,s.identity,8000)=="Server totals unavailable");
 assert(state.Consume(frame.c_str(),s.identity,1000));assert(state.Label(10200,s.identity,1000)=="16%");
 assert(state.Label(10201,s.identity,1000)=="+1% max");
 assert(state.Label(10202,s.identity,1000)=="10% relative");
 assert(state.Label(10203,s.identity,1000)=="up to 15%*");
 assert(state.Label(10204,s.identity,1000)=="up to 10%*");
 assert(state.Label(10205,s.identity,1000)=="Active");
 assert(state.Label(10309,s.identity,1000)=="92/780");assert(state.Label(10310,s.identity,1000)=="29/770");
 assert(!state.Consume(frame.c_str(),s.identity,1001));s.sequence=99;
 assert(!state.Consume(Encode(s).c_str(),s.identity,1001));
 auto other=s.identity;other[1]++;assert(state.Label(10200,other,1000)=="--");
 assert(state.Label(10200,s.identity,9000)=="--");assert(state.Label(10200,s.identity,999)=="--");
 assert(!state.Consume(frame.c_str(),other,1000));
 s.sequence=101;s.values[ShieldBlock]=0;s.values[HuntBlock]=0;s.values[Faerune]=0;
 assert(state.Consume(Encode(s).c_str(),s.identity,1002));assert(state.Label(10200,s.identity,1002)=="0%");
 assert(state.Label(10205,s.identity,1002)=="None");
 s.identity.fill(UINT32_MAX);s.sequence=UINT32_MAX;s.values.fill(INT32_MAX);s.values[Faerune]=1;
 auto maximum=Encode(s);assert(maximum.size()<512);assert(Decode(maximum.c_str(),decoded));
 s.values[Dodge]=INT32_MIN;assert(Decode(Encode(s).c_str(),decoded));assert(decoded.values[Dodge]==INT32_MIN);
 std::string bad=maximum+"|1";assert(!Decode(bad.c_str(),decoded));
 assert(!Decode(maximum.substr(0,maximum.rfind('|')).c_str(),decoded));
 assert(!Decode(std::string(512,'x').c_str(),decoded));assert(!Decode(nullptr,decoded));
 bad=maximum;bad[8]='-';assert(!Decode(bad.c_str(),decoded));
 s.values[Faerune]=2;assert(!Decode(Encode(s).c_str(),decoded));
 s.values[Faerune]=1;s.values[HealCap]=-1;assert(!Decode(Encode(s).c_str(),decoded));
 state.Clear();assert(!state.Ready(s.identity,1000));
 s.values[HealCap]=780;s.sequence=UINT32_MAX-1;assert(state.Consume(Encode(s).c_str(),s.identity,1000));
 s.sequence=2;assert(state.Consume(Encode(s).c_str(),s.identity,1001));
}
'''.replace('HEADER',header)
        native.FreeTradeTests.compile_run(self,source)


if __name__=='__main__':unittest.main()
