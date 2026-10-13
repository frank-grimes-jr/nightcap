int main(int argc,char** argv) {
 try {
  check(argc==3,"scenario and container mode required");std::string scenario=argv[1];bool world=std::string(argv[2])=="world";
  Client player;EQ::ItemInstance bag(999,1,false);bag.bag=true;player.inv.bag=&bag;
  Object object;object.m_inst=&bag;player.world=&object;NewCombine_Struct request;
  EQ::ItemInstance replacement(888,1,false);replacement.bag=true;replacement.add(0,100,20);replacement.add(1,200,20);
  if(world) {request.container_slot=EQ::invslot::SLOT_TRADESKILL_EXPERIMENT_COMBINE;bag.has_item=false;}
  if(scenario=="unstacked"||scenario=="replace_exact") {bag.add(0,100,1);bag.add(1,200,1);}
  else if(scenario=="exact_quantity") {bag.add(0,100,2);}
  else if(scenario=="two_from_stack"||scenario=="ambiguous_quantity"||scenario=="ambiguous_duplicate") {bag.add(0,100,20);}
  else if(scenario=="split_stacks") {bag.add(0,100,1);bag.add(1,100,19);}
  else if(scenario=="charged_single") {bag.add(0,100,20,false);}
  else {bag.add(0,100,20);if(scenario!="missing")bag.add(1,200,20);}
  if(scenario=="unrelated")bag.add(2,300,20);
  if(scenario=="augmented")bag.GetItem(0)->augmented=true;
  replace_container_fixture=scenario=="replace_surplus"||scenario=="replace_exact";
  if(scenario.starts_with("callback_")) {
   parser.event=scenario.starts_with("callback_combine_")?EVENT_COMBINE:EVENT_COMBINE_VALIDATE;
   parser.action=[&](Client* user) {
    if(scenario.ends_with("_swap")) {user->inv.bag=&replacement;bag.retired=true;}
    else if(scenario.ends_with("_missing"))bag.DeleteItem(1);
    else if(scenario.ends_with("_augmented"))bag.GetItem(0)->augmented=true;
    else if(scenario.ends_with("_close"))user->world=nullptr;
   };
  }
  for(const auto& [slot,inst]:bag.contents)database.items[inst->data.ID]=inst->data;
  database.saved=snapshot(&bag);player.displayed=snapshot(&bag);
  const auto before100=quantity(bag,100),before200=quantity(bag,200),before300=quantity(bag,300);
  object.HandleCombine(&player,&request,world?&object:nullptr);
  if(scenario=="repeat_until_empty") {
   for(int n=1;n<21;++n)object.HandleCombine(&player,&request,world?&object:nullptr);
   check(player.acks==21,"each repeated combine must acknowledge exactly once");
  } else check(player.acks==1,"combine must acknowledge exactly once");
  if(scenario=="stacked_pair") {
   check(player.attempts==1,"20/20 materials should allow one craft");
   check(quantity(bag,100)==19&&quantity(bag,200)==19,"one craft from 20/20 stacks must leave 19/19 materials");
   if(world) {
    check(database.saves==1&&database.saved==snapshot(&bag),"remaining world materials must be saved");
    check(player.displayed==snapshot(&bag),"world container resend must display remaining materials and quantities");
   }
  } else if(scenario=="two_from_stack"||scenario=="split_stacks") {
   check(player.attempts==1,"recipe requiring two of one material must combine from available stack quantities");
   check(quantity(bag,100)==18,"two-component craft from 20 materials must leave 18");
  } else if(scenario=="unstacked"||scenario=="replace_exact") {
   check(player.attempts==1,"ordinary unstacked recipe must continue working");
   check(bag.contents.empty(),"ordinary recipe must consume its two physical inputs");
   if(scenario=="replace_exact")check(player.inv.bag==nullptr,"exact replace-container recipe must replace its container");
  } else if(scenario=="exact_quantity") {
   check(player.attempts==1&&player.chosen==2,"unique exact quantity recipe must win over lower quantity alternatives");
   check(bag.contents.empty(),"exact quantity recipe must consume exact requirements");
  } else if(scenario=="repeat_until_empty") {
   check(player.attempts==20,"twenty pairs of materials must allow twenty crafts then reject the twenty-first");
   check(bag.contents.empty(),"twenty crafts must exhaust exactly twenty pairs of materials");
   if(world)check(database.saved.empty()&&player.displayed.empty(),"world saved and displayed container must empty at exhaustion");
  } else if(scenario.starts_with("callback_")) {
   check(player.attempts==0,"quest callback invalidation must prevent execution");
   check(quantity(bag,100)==20,"callback invalidation must preserve remaining material");
   check(quantity(bag,200)==(scenario.ends_with("_missing")?0:20),"combine changed material beyond quest callback action");
   check(quantity(replacement,100)==20&&quantity(replacement,200)==20,"replacement container materials must remain intact");
  } else {
   check(player.attempts==0,"invalid, incomplete, or ambiguous inputs must not choose and execute a recipe");
   check(quantity(bag,100)==before100&&quantity(bag,200)==before200&&quantity(bag,300)==before300,
         "rejected combine must preserve every material");
   if(scenario=="charged_single")check(bag.GetItem(0)->GetCharges()==20,"nonstack item charges must remain intact");
  }
  std::cout<<"PASS "<<scenario<<(world?" world":" bag")<<std::endl;
 } catch(const std::exception& e) {std::cout<<"FAIL "<<e.what()<<std::endl;return 1;}
}
