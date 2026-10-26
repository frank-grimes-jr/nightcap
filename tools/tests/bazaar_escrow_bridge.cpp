// Bridge compiles the production transaction engine; Python supplies a real DB session.
#include "common/bazaar_escrow.h"
#include "common/bazaar_search_policy.h"
#include "common/equipment_race_policy.h"
#include <sstream>
#include <cstring>
using namespace NightcapBazaar;
extern "C" {
struct WireReply { int ok; unsigned long long affected, id; const char *rows; };
typedef void (*Callback)(const char *, WireReply *);
static Rows Parse(const char *text) {
 Rows rows; std::istringstream input(text ? text : ""); std::string line;
 while (std::getline(input,line)) {
  Row row; size_t start=0;
  for (;;) { auto end=line.find('\t',start); row.push_back(line.substr(start,end-start)); if(end==std::string::npos) break; start=end+1; }
  rows.push_back(row);
 }
 return rows;
}
#ifdef _WIN32
__declspec(dllexport)
#endif
const char *bazaar_run(Callback callback, unsigned op, unsigned character, unsigned listing,
 unsigned price, unsigned quantity, int stackable, const char *wallet, const char *cursor) {
 static thread_local std::string result;
 Request request{}; request.op=static_cast<Operation>(op); request.character=character;
 request.listing=listing; request.unit_price=price; request.quantity=quantity; request.stackable=stackable;
 auto w=Parse(wallet); if(w.size()==1 && w[0].size()==4) for(size_t i=0;i<4;++i) request.wallet[i]=std::stoull(w[0][i]);
 request.cursor=Parse(cursor);
 auto out=Execute([&](const std::string &sql) { WireReply w{}; callback(sql.c_str(),&w);
  return Reply{w.ok!=0,w.affected,w.id,Parse(w.rows)}; },request,Slots{33,6010,6209});
 result=std::to_string(static_cast<unsigned>(out.status))+"\t"+std::to_string(out.listing);
 for(auto value:out.wallet) result+="\t"+std::to_string(value);
 result+="\n";
 for(auto &row:out.items) { for(size_t i=0;i<row.size();++i) { if(i) result+='\t'; result+=row[i]; } result+='\n'; }
 return result.c_str();
}
}

extern "C" {
#ifdef _WIN32
__declspec(dllexport)
#endif
const char *bazaar_race_sql(unsigned bit) { static thread_local std::string sql; sql=NightcapBazaar::RacePredicate(bit); return sql.c_str(); }
#ifdef _WIN32
__declspec(dllexport)
#endif
unsigned bazaar_effective_races(unsigned races,unsigned classes,unsigned slots,unsigned augtype,unsigned itemclass) {
 struct Item {unsigned Races,Classes,Slots,AugType,ItemClass;};Item item{races,classes,slots,augtype,itemclass};
 NightcapEquipment::ApplyRacePolicy(item);return item.Races;
}
}
