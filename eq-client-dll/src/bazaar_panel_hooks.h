// Included inside nightcap::client_ui after AAChild and shared native helpers.
static BazaarPanelController bazaar_panel;
using BazaarFrame = int (__thiscall *)(void *);
using BazaarDestroy = void *(__thiscall *)(void *, unsigned);
static InventoryNotify original_bazaar_notify = nullptr;
static BazaarFrame original_bazaar_frame = nullptr;
static BazaarDestroy original_bazaar_destroy = nullptr;
static uint64_t bazaar_next_render = 0;
static bool bazaar_missing_reported = false;

inline bool BazaarVisible(void *window) {
	__try {return window && *reinterpret_cast<bool *>(static_cast<BYTE *>(window)+0x196);}
	__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
inline void *BazaarChild(void *window,const std::string &name){return AAChild(window,("NCBZ_"+name).c_str());}
inline void BazaarText(void *window,const std::string &name,const std::string &text){
	void *control=BazaarChild(window,name);if(!control||text.size()>256)return;
	EqString value{};reinterpret_cast<AssignString>(base+kUIStringAssignRva)(&value,text.c_str());
	using Text=void (__thiscall *)(void *,const EqString *);
	reinterpret_cast<Text>((*static_cast<void ***>(control))[0x124/4])(control,&value);
	reinterpret_cast<AssignString>(base+kUIStringAssignRva)(&value,"");
}
inline void BazaarEnable(void *window,const std::string &name,bool enabled){
	if(void *control=BazaarChild(window,name))*reinterpret_cast<bool *>(static_cast<BYTE *>(control)+0x1a)=enabled;
}
inline bool BazaarPrice(void *window,char (&output)[33]){
	void *control=AAChild(window,"NCBZ_Price");if(!control)return false;
	// Native CEditWnd stores either byte or UTF16 CXStr input. Capacity is bytes.
	// Accept bounded printable ASCII values in either representation; retain no pointer.
	__try {
		const auto rep=*reinterpret_cast<const BYTE **>(static_cast<BYTE *>(control)+0x1ec);
		if(!rep){output[0]=0;return true;}
		const auto length=*reinterpret_cast<const uint32_t *>(rep+8);
		const auto encoding=*reinterpret_cast<const uint32_t *>(rep+12);
		if(length>32||encoding>1)return false;
		const uint32_t stride=encoding?2:1;
		if(*reinterpret_cast<const uint32_t *>(rep+4)<(length+1)*stride)return false;
		for(uint32_t i=0;i<=length;++i){
			uint16_t character=rep[0x14+i*stride];
			if(encoding)character|=uint16_t(rep[0x15+i*stride])<<8;
			if(i==length){if(character)return false;}
			else {if(character<32||character>126)return false;output[i]=char(character);}
		}
		output[length]=0;return true;
	}__except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
inline bool BazaarControls(void *window){
	for(const char *name:{"Price","Post","ConfirmPost","Dismiss","Balance","Collect","Preview","Status","Page","Previous","Next","Cancel","Refresh"})
		if(!BazaarChild(window,name))return false;
	for(unsigned i=0;i<8;++i)if(!BazaarChild(window,"Row"+std::to_string(i)))return false;
	void *price=BazaarChild(window,"Price");
	*reinterpret_cast<int *>(static_cast<BYTE *>(price)+0x1e4)=32;
	*reinterpret_cast<int *>(static_cast<BYTE *>(price)+0x1e8)=32;
	return true;
}
inline void RenderBazaar(void *window){
	using namespace NightcapBazaarPanel;
	const auto &s=bazaar_panel.Current();const bool ready=bazaar_panel.Ready();
	BazaarText(window,"Status",bazaar_panel.Feedback());
	BazaarText(window,"Balance","Proceeds: "+Money(s.credit));
	BazaarText(window,"Page",std::to_string(s.total)+" listings | "+std::to_string(s.page+1)+" / "+std::to_string((std::max)(1u,(s.total+7)/8)));
	BazaarEnable(window,"Post",bazaar_panel.CanPost());BazaarEnable(window,"ConfirmPost",bazaar_panel.HasQuote());
	BazaarEnable(window,"Price",!bazaar_panel.Busy());BazaarEnable(window,"Collect",bazaar_panel.CanCollect());
	BazaarEnable(window,"Cancel",bazaar_panel.Selected()!=nullptr);BazaarText(window,"Cancel",bazaar_panel.Cancelling()?"Confirm Cancel":"Cancel Listing");
	BazaarEnable(window,"Refresh",bazaar_panel.CanRefresh());BazaarEnable(window,"Previous",ready&&s.page>0);
	BazaarEnable(window,"Next",ready&&(s.page+1)*PageSize<s.total);BazaarEnable(window,"Dismiss",!bazaar_panel.Busy());
	if(bazaar_panel.HasQuote()){
		const auto &q=s.quote.item;
		BazaarText(window,"Preview",q.name+" x"+std::to_string(q.quantity)+" | "+Money(q.price)+" EACH | "+Money(uint64_t(q.price)*q.quantity)+" TOTAL");
	}else BazaarText(window,"Preview","Pick up an item and click Post Item to review its exact quantity and total price.");
	for(size_t i=0;i<PageSize;++i){
		const std::string name="Row"+std::to_string(i);const bool exists=i<s.rows.size();
		BazaarEnable(window,name,ready&&exists);
		if(exists){const auto &r=s.rows[i];BazaarText(window,name,(bazaar_panel.SelectedID()==r.id?"> ":"")+r.name+" x"+std::to_string(r.quantity)+" | "+Money(r.price)+" EACH");}
		else BazaarText(window,name,"");
	}
}
inline bool UpdateBazaarContext(void *self){
	uint32_t spawn=0;char name[64]={};const bool context=ReadIdentity(spawn,name);
	const bool visible=context&&BazaarVisible(self)&&BazaarVisible(AAChild(self,"NCBZ_SellPage"));
	bazaar_panel.Pulse(GetTickCount64(),context?spawn:0,name,visible);return visible;
}
inline int __fastcall BazaarNotifyHook(void *self,void *,void *sender,uint32_t message,void *data){
	if(self&&sender){
		// Edit notifications are owned by this page; Enter never submits a sale.
		if(sender==BazaarChild(self,"Price"))return 1;
		for(const char *name:{"Post","ConfirmPost","Dismiss","Cancel","Collect","Refresh","Previous","Next"}){
			if(sender!=BazaarChild(self,name))continue;
			if(message==1&&UpdateBazaarContext(self)&&BazaarControls(self)){
				char price[33]={};
				if(!strcmp(name,"Post")){if(BazaarPrice(self,price))bazaar_panel.Post(price);else bazaar_panel.PriceUnavailable();}
				else if(!strcmp(name,"ConfirmPost")){if(BazaarPrice(self,price))bazaar_panel.ConfirmPost(price);else bazaar_panel.PriceUnavailable();}
				else if(!strcmp(name,"Dismiss"))bazaar_panel.Dismiss();
				else if(!strcmp(name,"Cancel"))bazaar_panel.Cancel();
				else if(!strcmp(name,"Collect"))bazaar_panel.Collect();
				else if(!strcmp(name,"Refresh"))bazaar_panel.Refresh();
				else bazaar_panel.Page(!strcmp(name,"Next"));
				bazaar_next_render=0;
			}
			return 1;
		}
		for(size_t i=0;i<8;++i)if(sender==BazaarChild(self,"Row"+std::to_string(i))){if(message==1&&UpdateBazaarContext(self)&&BazaarControls(self)){bazaar_panel.Select(i);bazaar_next_render=0;}return 1;}
	}
	return original_bazaar_notify(self,sender,message,data);
}
inline int __fastcall BazaarFrameHook(void *self,void *){
	// Native frame owns search and Find Trader timers; preserve its exact return.
	const int result=original_bazaar_frame(self);
	uint32_t spawn=0;char name[64]={};const auto now=GetTickCount64();
	const bool context=ReadIdentity(spawn,name);
	const bool visible=context&&BazaarVisible(self)&&BazaarVisible(AAChild(self,"NCBZ_SellPage"));
	if(visible&&!BazaarControls(self)){
		bazaar_panel.Close();
		if(!bazaar_missing_reported){LootNotice("Bazaar panel assets are missing. Close EQ and use launcher Play to update.");bazaar_missing_reported=true;}
		return result;
	}
	bazaar_panel.Pulse(now,context?spawn:0,name,visible);
	if(visible&&now>=bazaar_next_render){RenderBazaar(self);bazaar_next_render=now+100;}
	return result;
}
inline void *__fastcall BazaarDestroyHook(void *self,void *,unsigned flags){
	bazaar_panel.Close();bazaar_next_render=0;bazaar_missing_reported=false;
	return original_bazaar_destroy(self,flags);
}
inline bool ConsumeBazaarReply(const char *message){
	return message&&bazaar_panel.Consume(message,GetTickCount64());
}
inline bool PatchBazaarSlot(uintptr_t address,const BYTE (&preferred)[4],uintptr_t image_base,uintptr_t target,
	decltype(&VirtualProtect) protect=&VirtualProtect,decltype(&FlushInstructionCache) flush=&FlushInstructionCache){
	uint32_t original=0;memcpy(&original,preferred,4);original+=uint32_t(image_base)-0x400000u;
	const uint32_t replacement=static_cast<uint32_t>(target);
	return WriteVerifiedPatch(reinterpret_cast<BYTE *>(address),reinterpret_cast<BYTE *>(&original),reinterpret_cast<const BYTE *>(&replacement),4,protect,flush);
}
inline bool InstallBazaarPanel(){
	// Each specific slot is a verified HIGHLOW relocation; do not patch the
	// generic screen table or copy the frame's relative-CALL prologue.
	original_bazaar_notify=reinterpret_cast<InventoryNotify>(base+0x235990);
	original_bazaar_frame=reinterpret_cast<BazaarFrame>(base+0x2336f0);
	original_bazaar_destroy=reinterpret_cast<BazaarDestroy>(base+0x236e40);
	bazaar_panel.Bind(&ExecuteUIRequest);
	return PatchBazaarSlot(base+kBazaarNotifySlotRva,kExpectedBazaarNotifySlot,base,reinterpret_cast<uintptr_t>(&BazaarNotifyHook))&&
		PatchBazaarSlot(base+kBazaarFrameSlotRva,kExpectedBazaarFrameSlot,base,reinterpret_cast<uintptr_t>(&BazaarFrameHook))&&
		PatchBazaarSlot(base+kBazaarDestroySlotRva,kExpectedBazaarDestroySlot,base,reinterpret_cast<uintptr_t>(&BazaarDestroyHook));
}
