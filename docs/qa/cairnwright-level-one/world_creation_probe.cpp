// In-process RoF2 test transport. Only the scratch database and a synthetic
// authenticated account are used. World handles name approval, creation and list.
#include "world/client.h"
#include "world/world_config.h"
#include "world/worlddb.h"
#include "common/eq_stream_intf.h"
#include "common/opcodemgr.h"
#include "common/path_manager.h"
#include "common/skill_caps.h"
#include "common/zone_store.h"
#include "common/memory_mapped_file.h"
#include "common/item_data.h"
#include <deque>
#include <filesystem>
#include <iostream>
#include <stdexcept>

extern WorldDatabase database, content_db;
extern volatile bool RunLoops;

static void require(bool ok, const char* stage)
{
	if (!ok) { throw std::runtime_error(stage); }
}

class TestStream final : public EQStreamInterface {
public:
	std::deque<EQApplicationPacket*> incoming;
	bool approved = false;
	bool listed = false;

	void QueuePacket(const EQApplicationPacket* p, bool) override {
		if (p->GetOpcode() == OP_ApproveName) { approved = p->size == 1 && p->pBuffer[0] == 1; }
		if (p->GetOpcode() == OP_SendCharInfo) {
			auto* list = reinterpret_cast<const CharacterSelect_Struct*>(p->pBuffer);
			listed = list->CharCount == 1 && list->Entries[0].Class == 17 &&
				list->Entries[0].Level == 1 && list->Entries[0].Zone == 22 &&
				std::string(list->Entries[0].Name) == "Cairnproof";
		}
	}
	void FastQueuePacket(EQApplicationPacket** p, bool ack) override { QueuePacket(*p,ack); delete *p; *p=nullptr; }
	EQApplicationPacket* PopPacket() override {
		if (incoming.empty()) { return nullptr; }
		auto* p=incoming.front(); incoming.pop_front(); return p;
	}
	void Close() override {}
	void ReleaseFromUse() override {}
	void RemoveData() override {}
	std::string GetRemoteAddr() const override { return "127.0.0.1"; }
	uint32 GetRemoteIP() const override { return 0; }
	uint16 GetRemotePort() const override { return 0; }
	bool CheckState(EQStreamState state) override { return state == ESTABLISHED; }
	std::string Describe() const override { return "in-process QA"; }
	EQStreamState GetState() override { return ESTABLISHED; }
	void SetOpcodeManager(OpcodeManager**) override {}
	OpcodeManager* GetOpcodeManager() const override { static NullOpcodeManager manager; return &manager; }
	const EQ::versions::ClientVersion ClientVersion() const override { return EQ::versions::ClientVersion::RoF2; }
	Stats GetStats() const override { return {}; }
	void ResetStats() override {}
	EQStreamManagerInterface* GetManager() const override { return nullptr; }
};

int main(int argc, char** argv)
{
	require(argc==2 && (std::string(argv[1])=="create" || std::string(argv[1])=="list"), "mode");
	const bool create=std::string(argv[1])=="create";
	std::string password;
	require(bool(std::getline(std::cin,password)) && !password.empty(), "scratch credential missing");
	require(std::filesystem::current_path().filename()=="storage-qa", "scratch working directory");
	PathManager::Instance()->Init();
	require(WorldConfig::LoadConfig(), "scratch config");
	RunLoops=false;
	for (auto* db : {&database,&content_db}) {
		require(db->Connect("nightcap-cairnwright-qa-20261121","cairnwright_qa",password,"cairnwright_qa",3306),
			"scratch database connection");
	}
	ZoneStore::Instance()->LoadZones(content_db);
	RuleManager::Instance()->SetRule("World:SoFStartZoneID","22");
	RuleManager::Instance()->SetRule("World:StartZoneSameAsBindOnCreation","true");
	require(content_db.LoadCharacterCreateAllocations() && content_db.LoadCharacterCreateCombos(), "creation rows");
	SkillCaps::Instance()->SetContentDatabase(&content_db)->LoadSkillCaps();
	const std::string dir=PathManager::Instance()->GetSharedMemoryPath();
	require(std::filesystem::equivalent(dir,"shared"), "scratch cache path");
	if (create) {
		int32 count; uint32 max_id;
		content_db.GetItemsCount(count,max_id);
		require(count>0 && count<100 && max_id==998636, "scratch items");
		uint32 bytes=EQ::FixedMemoryHashSet<EQ::ItemData>::estimated_size(count,max_id);
		EQ::MemoryMappedFile file(dir+"/items",bytes);
		file.ZeroFile();
		content_db.LoadItems(file.Get(),bytes,count,max_id);
	}
	require(content_db.LoadItems("") && database.LoadItems(""), "scratch item cache");
	require(content_db.GetItem(998636) && content_db.GetItem(998616), "starter kit in cache");

	ServerClientList_Struct fixture{};
	fixture.AccountID=42;
	strcpy(fixture.AccountName,"Cairnqa");
	ClientListEntry account(1,nullptr,&fixture,CLE_Status::CharSelect);
	auto* stream=new TestStream;
	Client client(stream);
	client.SetCLE(&account);
	if (create) {
		require(database.GetCharacterID("Cairnproof")==0, "scratch name already exists");
		auto* approval=new EQApplicationPacket(OP_ApproveName,sizeof(NameApproval_Struct));
		auto* n=reinterpret_cast<NameApproval_Struct*>(approval->pBuffer);
		strcpy(n->name,"Cairnproof"); n->race_id=8; n->class_id=17;
		stream->incoming.push_back(approval);
		require(client.Process() && stream->approved, "world name approval");
		auto* creation=new EQApplicationPacket(OP_CharacterCreate,sizeof(CharCreate_Struct));
		auto* cc=reinterpret_cast<CharCreate_Struct*>(creation->pBuffer);
		cc->race=8; cc->class_=17; cc->deity=202; cc->start_zone=67;
		cc->STR=100; cc->STA=115; cc->DEX=90; cc->AGI=70; cc->INT=60; cc->WIS=88; cc->CHA=55;
		stream->incoming.push_back(creation);
		require(client.Process() && stream->listed, "world creation");
	} else {
		client.SendCharInfo();
		require(stream->listed, "fresh world character list");
	}
	auto rows=database.QueryDatabase("SELECT c.id FROM character_data c JOIN character_currency w ON w.id=c.id "
		"WHERE c.name='Cairnproof' AND c.account_id=42 AND c.class=17 AND c.level=1 AND c.zone_id=22 "
		"AND w.platinum=100 AND 2=(SELECT COUNT(*) FROM inventory i WHERE i.character_id=c.id "
		"AND (i.slot_id,i.item_id) IN ((17,998616),(13,998636)))");
	require(rows.Success() && rows.RowCount()==1, "persistent class, starter items and currency");
	std::cout << (create?"CREATED":"RELOADED") << " id=" << rows.begin()[0]
		<< " class=17 level=1 zone=22 kit=998616,998636" << std::endl;
}
