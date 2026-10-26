#pragma once
#include "advanced_loot_protocol.h"
#include <algorithm>
#include <set>

// Display-only contract. Every mutation still uses the server escrow checks.
namespace NightcapBazaarPanel {
constexpr uint32_t PageSize = 8, MaxListings = 100;
struct Listing { uint32_t id=0, item=0, quantity=0, price=0; std::string name; };
struct Quote { std::string nonce; Listing item; };
struct Snapshot {
	uint32_t request=0, spawn=0, page=0, total=0;
	std::string name, message;
	bool enabled=false;
	uint64_t credit=0;
	Quote quote;
	std::vector<Listing> rows;
};
inline bool Unsigned(std::string_view text,uint64_t &out) {
	if(text.empty() || text.size()>20)return false;
	uint64_t n=0;
	for(char c:text){if(c<'0'||c>'9'||n>(UINT64_MAX-uint64_t(c-'0'))/10)return false;n=n*10+uint64_t(c-'0');}
	out=n;return true;
}
inline bool Nonce(std::string_view text) {
	return !text.empty() && text.size()<=64 && text.find_first_not_of("0123456789abcdefABCDEF-")==std::string_view::npos;
}
inline std::string Plain(std::string_view text,size_t limit) {
	std::string result;
	for(unsigned char c:text){if(result.size()==limit)break;result+=c>=32&&c<=126?char(c):'?';}
	return result.empty()?"-":result;
}
inline std::string RowFields(const Listing &r) {
	return std::to_string(r.item)+"|"+std::to_string(r.quantity)+"|"+std::to_string(r.price)+"|"+NightcapLoot::Hex(Plain(r.name,63));
}
inline std::vector<std::string> Encode(const Snapshot &s) {
	const auto prefix="|"+std::to_string(s.request)+"|";
	std::vector<std::string> out={"[NCBZ1]B"+prefix+std::to_string(s.spawn)+"|"+NightcapLoot::Hex(Plain(s.name,63))+"|"+
		std::to_string(s.enabled)+"|"+std::to_string(s.page)+"|"+std::to_string(s.total)+"|"+std::to_string(s.rows.size())+"|"+std::to_string(s.credit)};
	out.push_back("[NCBZ1]Q"+prefix+(s.quote.nonce.empty()?"-":s.quote.nonce)+"|"+RowFields(s.quote.item));
	for(const auto &r:s.rows)out.push_back("[NCBZ1]R"+prefix+std::to_string(r.id)+"|"+RowFields(r));
	out.push_back("[NCBZ1]M"+prefix+NightcapLoot::Hex(Plain(s.message,140)));
	out.push_back("[NCBZ1]E"+prefix+std::to_string(s.rows.size()));
	return out;
}
inline std::string Money(uint64_t copper) {
	return std::to_string(copper/1000)+" pp"+(copper%1000?" + "+std::to_string(copper%1000)+" copper":"");
}
}
