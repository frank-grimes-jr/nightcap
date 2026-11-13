"""New Inventory transport must preserve combat ratings and legacy compatibility."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]


class InventoryStatsProtocol(unittest.TestCase):
    def test_bounds_identity_replay_expiry_sentinel_colors_and_legacy(self):
        header=(ROOT/'eq-client-dll/src/inventory_stats_state.h').as_posix()
        source=r'''
#include <cassert>
#include <climits>
#include "HEADER"
int main(){
 using namespace NightcapInventory;
 Snapshot s;s.identity={1,29,39,0,500};s.sequence=100;
 s.values[Mitigation]=916;s.values[Defense]=795;s.values[Attack]=1857;
 s.values[SpellDamage]=653;s.values[Heal]=532;
 s.values[Strength]=434;s.values[StrengthCap]=434;s.values[HeroicStrength]=104;
 Snapshot decoded;auto frame=Encode(s);assert(Decode(frame.c_str(),decoded));assert(decoded.values==s.values);
 NightcapStats::Snapshot old;assert(!NightcapStats::Decode(frame.c_str(),old));
 old.identity=s.identity;assert(!Decode(NightcapStats::Encode(old).c_str(),decoded));
 nightcap::InventoryStatsState state;assert(state.Label(10500,s.identity,1000)=="--");
 assert(state.Consume(frame.c_str(),s.identity,1000));
 assert(state.Label(10500,s.identity,1000)=="916");assert(state.Label(10501,s.identity,1000)=="795");
 assert(state.Label(10600,s.identity,1000)=="434");assert(state.Label(10800,s.identity,1000)=="/434");
 assert(state.Label(10700,s.identity,1000)=="+104");
 assert(state.Color(10500,s.identity,1000)==0xFF00FF00);
 assert(state.Color(10800,s.identity,1000)==0xFFFFFFFF);
 assert(state.Color(10700,s.identity,1000)==0xFFD6B228);
 assert(!state.Consume(frame.c_str(),s.identity,1001));s.sequence=99;
 assert(!state.Consume(Encode(s).c_str(),s.identity,1001));
 auto other=s.identity;other[1]++;assert(state.Label(10500,other,1000)=="--");
 assert(!state.Consume(frame.c_str(),other,1000));assert(state.Label(10500,s.identity,9000)=="--");
 assert(state.Color(10700,s.identity,9000)==0xFFAAAAAA);
 assert(state.Label(10500,s.identity,999)=="--");
 s.sequence=101;s.values[Defense]=-1;s.values[HeroicStrength]=0;
 assert(state.Consume(Encode(s).c_str(),s.identity,1002));assert(state.Label(10501,s.identity,1002)=="Auto");
 assert(state.Label(10700,s.identity,1002)=="+0");s.sequence++;
 s.values[HeroicStrength]=-3;assert(state.Consume(Encode(s).c_str(),s.identity,1003));
 assert(state.Label(10700,s.identity,1003)=="-3");
 s.identity.fill(UINT32_MAX);s.sequence=UINT32_MAX;s.values.fill(INT32_MAX);
 auto maximum=Encode(s);assert(maximum.size()<512);assert(Decode(maximum.c_str(),decoded));
 s.values[Strength]=INT32_MIN;assert(Decode(Encode(s).c_str(),decoded));assert(decoded.values[Strength]==INT32_MIN);
 assert(!Decode((maximum+"|1").c_str(),decoded));assert(!Decode(maximum.substr(0,maximum.rfind('|')).c_str(),decoded));
 assert(!Decode(std::string(512,'x').c_str(),decoded));assert(!Decode(nullptr,decoded));
 s.values[Defense]=-2;assert(!Decode(Encode(s).c_str(),decoded));
 s.values[Defense]=795;state.Clear();assert(!state.Ready(s.identity,1000));
 s.sequence=UINT32_MAX-1;assert(state.Consume(Encode(s).c_str(),s.identity,1000));
 s.sequence=2;assert(state.Consume(Encode(s).c_str(),s.identity,1001));
}
'''.replace('HEADER',header)
        native.FreeTradeTests.compile_run(self,source)
