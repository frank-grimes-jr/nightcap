int physical(const EQ::InventoryProfile& inventory,uint32 id) {
 int total=inventory.bag?quantity(*inventory.bag,id):0;
 for(const auto& [slot,item]:inventory.general)if(item->data.ID==id)total+=item->IsStackable()?item->charges:1;
 return total;
}
int main(int argc,char** argv) {
 try {
  check(argc==3,"scenario required");const std::string scenario=argv[1];
  Client player,other;EQ::ItemInstance bag(999,1,false);bag.bag=true;player.inv.bag=&bag;
  EQ::ItemInstance replacement(888,1,false);replacement.bag=true;
  Object object;object.m_inst=&bag;object.user=&player;player.world=&object;
  RecipeAutoCombine_Struct request;
  player.inv.add(23,100,20);player.inv.add(24,200,20);
  bool accepted=scenario=="stacked"||scenario=="split"||scenario=="duplicate_enough"||scenario=="world_valid"||scenario=="world_edge"||
   scenario=="alchemy_valid"||scenario=="tinkering_valid"||scenario=="poison_valid"||scenario=="success_order"||scenario=="failure_order"||
   scenario=="output_stops"||scenario=="callback_output_stops";
  int take100=1,take200=1;
  if(scenario=="split") {bag.add(0,100,1);player.inv.GetItem(23)->charges=19;take100=2;take200=0;}
  if(scenario.starts_with("duplicate_")) {player.inv.GetItem(23)->charges=scenario=="duplicate_short"?3:4;take100=4;take200=0;}
  if(scenario=="charged") {player.inv.GetItem(23)->data.Stackable=false;take200=0;}
  if(scenario=="augmented")player.inv.GetItem(23)->augmented=true;
  if(scenario=="wrong_slot")request.unknown1=23;
  if(scenario=="wrong_id")request.some_id=888;
  if(scenario=="wrong_type")request.object_type=11;
  if(scenario=="not_bag")bag.bag=false;
  if(scenario=="missing_bag")player.inv.bag=nullptr;
  if(scenario.starts_with("world_")) {request.unknown1=EQ::invslot::SLOT_TRADESKILL_EXPERIMENT_COMBINE;request.some_id=0;bag.has_item=false;player.inv.bag=nullptr;}
  if(scenario=="world_closed")player.world=nullptr;
  if(scenario=="world_owner")object.user=&other;
  if(scenario=="world_type")object.m_type=11;
  if(scenario=="world_id")request.some_id=888;
  if(scenario=="world_range")player.z=20.01f;
  if(scenario=="world_edge")player.x=20.0f;
  if(scenario=="disconnected")player.connected=false;
  if(scenario=="unloaded")player.loaded=false;
  if(scenario=="zoning")player.zoning=true;
  if(scenario=="dead")player.dead=true;
  if(scenario=="engaged")player.engaged=true;
  if(scenario=="stunned")player.stunned=true;
  if(scenario=="mezzed")player.mezzed=true;
  if(scenario=="feared")player.feared=true;
  if(scenario=="ai")player.ai=true;
  if(scenario=="trading")player.trade_value.active=true;
  if(scenario=="cursor")player.inv.cursor=true;
  if(scenario=="recipe_missing")recipe_found_fixture=false;
  if(scenario=="unlearned") {recipe_fixture.must_learn=1;recipe_fixture.has_learnt=false;}
  if(scenario=="skill") {recipe_fixture.skill_needed=101;player.skill=100;}
  if(scenario.starts_with("alchemy_")) {recipe_fixture.tradeskill=EQ::skills::SkillAlchemy;player.profile.class_=Class::Shaman;}
  if(scenario=="alchemy_class")player.profile.class_=1;
  if(scenario=="alchemy_level")player.profile.level=24;
  if(scenario.starts_with("tinkering_"))recipe_fixture.tradeskill=EQ::skills::SkillTinkering;
  if(scenario=="tinkering_valid")player.profile.race=Race::Gnome;
  if(scenario.starts_with("poison_"))recipe_fixture.tradeskill=EQ::skills::SkillMakePoison;
  if(scenario=="poison_valid")player.profile.class_=Class::Rogue;
  if(scenario=="lore")player.lore=true;
  if(scenario=="replace_container")replace_container_fixture=true;
  if(scenario=="quest_denied") {parser.event=EVENT_COMBINE_VALIDATE;parser.result=1;}
  if(scenario.starts_with("callback_")||scenario=="world_callback_close") {
   parser.event=scenario=="callback_output_stops"?EVENT_COMBINE_SUCCESS:EVENT_COMBINE_VALIDATE;
   parser.action=[&](Client* p) {
    if(scenario=="callback_swap") {p->inv.bag=&replacement;bag.retired=true;}
    if(scenario=="callback_cursor"||scenario=="callback_output_stops")p->inv.cursor=true;
    if(scenario=="callback_missing")p->inv.erase(24);
    if(scenario=="callback_combat")p->engaged=true;
    if(scenario=="world_callback_close")p->world=nullptr;
   };
  }
  if(scenario=="success_order"||scenario=="failure_order"||scenario=="output_stops") {
   player.execution_success=scenario!="failure_order";
   parser.event=player.execution_success?EVENT_COMBINE_SUCCESS:EVENT_COMBINE_FAILURE;
  }
  if(scenario=="output_stops")player.push_output=true;
  const auto before100=physical(player.inv,100),before200=physical(player.inv,200);
  object.HandleAutoCombine(&player,&request);
  check(player.replies.size()==1&&player.markers.size()==1,"every auto request must have one native reply and one completion marker");
  if(accepted) {
   check(player.attempts==1,"valid automatic combine must execute once");
   check(physical(player.inv,100)==before100-take100&&physical(player.inv,200)==before200-take200,"automatic combine consumed wrong physical quantities");
   check(player.replies[0]==0&&player.markers[0]=="[NCTS1]|42|1|1","completed attempt must send attempted result even after skill failure");
   if(scenario=="success_order"||scenario=="failure_order"||scenario=="output_stops"||scenario=="callback_output_stops") {
    check(player.timeline==std::vector<std::string>({"execute","callback","ack","marker"}),"completion must follow output execution and result quest callback");
   }
   if(scenario=="output_stops"||scenario=="callback_output_stops") {
    object.HandleAutoCombine(&player,&request);
    check(player.attempts==1,"output on cursor must stop a subsequent automatic craft");
    check(physical(player.inv,100)==before100-1&&physical(player.inv,200)==before200-1,"blocked second attempt must preserve materials");
    check(player.replies.size()==2&&player.replies[1]!=0&&player.markers.back()=="[NCTS1]|42|1|0","blocked second request must report stopped completion");
   }
  } else {
   check(player.attempts==0,"invalid auto request must not execute");
   check(physical(player.inv,100)==before100,"rejected auto request consumed material100");
   check(physical(player.inv,200)==(scenario=="callback_missing"?0:before200),"rejected auto request consumed material200");
   check(player.replies[0]!=0&&player.markers[0]=="[NCTS1]|42|1|0","rejected request must report unattempted result");
  }
  std::cout<<"PASS "<<scenario<<std::endl;
 } catch(const std::exception& e) {std::cout<<"FAIL "<<e.what()<<std::endl;return 1;}
}
