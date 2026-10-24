#pragma once
#include <cstdint>
#include <string>
namespace NightcapHighkeep {
constexpr uint32_t Revision=2026102401;
constexpr bool Eligible(unsigned zone,unsigned mode,bool enrolled) { return zone==6 && mode==1 && enrolled; }
struct Dialogue { unsigned step=0; uint64_t expires=0; };
inline bool Converse(Dialogue &d,const std::string &text,uint64_t now) {
	if (d.expires<now) { d={}; }
	if (text=="hail" || text.rfind("hail,",0)==0 || text.rfind("hail ",0)==0) { d={1,now+45}; }
	else if (d.step==1 && text=="relief detail") { d={2,now+45}; }
	else if (d.step==2 && text=="see osargen") { d={}; return true; }
	return false;
}
constexpr bool CanExtract(unsigned cleared,bool at_exit,bool together,bool safe) {
	return cleared==3 && at_exit && together && safe;
}
// Audited native keep guards and four raid captains; no name/faction guesses.
inline bool Guard(unsigned id) {
	switch(id) {
	case 6000:case 6001:case 6002:case 6003:case 6004:case 6005:case 6006:case 6007:case 6009:
	case 6011:case 6012:case 6013:case 6014:case 6015:case 6016:case 6017:case 6018:case 6019:
	case 6020:case 6021:case 6022:case 6023:case 6024:case 6025:case 6026:case 6027:
	case 6030:case 6031:case 6032:case 6033:case 6034:case 6042:case 6047:
	case 6079:case 6081:case 6083:case 6084:case 6085:case 6090:case 6099:
	case 6100:case 6101:case 6102:case 6103:case 6104:case 6105:case 6106:case 6107:case 6108:case 6109:
	case 6110:case 6112:case 6113:case 6114:case 6115:case 6117:case 6118:case 6121:case 6122:
	case 6123:case 6125:case 6127:case 6128:case 6129:case 6130:case 6131:case 6134:
	case 6145:case 6148:case 6151:case 6152:case 6154:case 6155:case 6158:case 6159:
	case 6160:case 6161:case 6162:case 6163:case 6164:case 6165:case 6166:case 6170:case 6171:
	case 6177:case 6178:case 6181:case 6188:return true;
	default:return false;
	}
}
struct Point { float x,y,z,h; };
constexpr Point Entrance{88,-16,4,0}, Gate{47,-1,3.75f,128}, Cell{-546,-52,-10.13f,437};
constexpr Point Boshinko{-108,-11,3.75f,128}, McCabe{-513,-3,-10.13f,128};
constexpr Point Checkpoints[]={{-513,-3,-10.13f,128},{-306,31,-10.13f,128},{48,-28,3.75f,128}};
}
