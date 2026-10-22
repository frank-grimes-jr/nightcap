-- Run from the checkout root. Uses the deployed Shakrn quest and actual shared helper.
package.path = 'server-mods/quests/lua_modules/?.lua;' .. package.path
local names = {[13737]='Aviak Charm', [213737]='Aviak Charm (Polished)',
  [413737]='Aviak Charm (Exalted)', [613737]='Aviak Charm (Ascended)',
  [813737]='Aviak Charm (Ascended)', [213738]='Aviak Charm (Polished)',
  [10032]='Star Ruby', [10035]='Ruby', [13743]='Fire Totem'}
local rewards, returns, money, events, exp = {}, {}, {}, {}, 0
local client = {}
function client:SetEntityVariable(k,v) events[k]=v end
function client:SummonItem(id) table.insert(rewards,id) end
function client:PushItemOnCursor(i) table.insert(returns,i) end
function client:AddMoneyToPP(c,s,g,p) money={c,s,g,p} end
function client:GetCleanName() return 'Player' end
function client:Ding() end
function client:AddEXP(n) exp=exp+n end
local npc = {Say=function() end, GetClass=function() return 1 end}
eq = {get_item_name=function(id) return names[id] or 'INVALID ITEM ID IN GETITEMNAME' end,
  is_disc_tome=function() return false end, send_player_handin_event=function() end}
function ItemInst(id, count)
  local i={valid=id~=nil, id=id, count=count or 1, attuned=true, custom='keep-me'}
  function i:GetID() return self.id or 0 end
  function i:GetName() return names[self.id] or 'Unrelated' end
  function i:GetCharges() return self.count end
  function i:IsInstNoDrop() return self.attuned end
  function i:RemoveTaskDeliveredItems() return self.count end
  return i
end
local function trade(a,b,c,d)
  return {item1=ItemInst(a),item2=ItemInst(b),item3=ItemInst(c),item4=ItemInst(d),
    other=client,copper=0,silver=0,gold=0,platinum=0}
end
local items=require('items')
dofile('tools/tests/fixtures/Shakrn_Meadowgreen.lua')
for _,id in ipairs({13737,213737,413737,613737}) do
  rewards,returns,events,exp={},{},{},0
  local t=trade(id,10032,10032,10035); local extra=t.item4
  event_trade({trade=t,other=client,self=npc})
  assert(#rewards==1 and rewards[1]==4178, 'Aviak tier rejected: '..id)
  assert(exp==25000 and #returns==1 and returns[1]==extra, 'wrong reward/leftovers')
  assert(extra.custom=='keep-me' and extra.attuned, 'return instance changed')
  assert(events.HANDIN_ITEMS:find(tostring(id),1,true), 'log lost actual tier ID')
end
for _,id in ipairs({213738,813737,940001,960001}) do
  rewards,returns={},{}
  event_trade({trade=trade(id,10032,10032),other=client,self=npc})
  assert(#rewards==0 and #returns==3, 'unrelated accepted or items lost')
end
rewards,returns={},{}
event_trade({trade=trade(213737,10032),other=client,self=npc})
assert(#rewards==0 and #returns==2 and returns[1]:GetID()==213737, 'missing ruby')
local t=trade(213737)
assert(not items.check_turn_in(t,{item1=13737,platinum=1}), 'missing money accepted')
assert(t.item1:GetID()==213737 and t.item1.valid, 'failed money check changed item')
assert(items.check_turn_in(t,{item1=13737}), 'later branch failed')
assert(not items.check_turn_in(t,{item1=13737}), 'same instance reused')
t=trade(213737,13737)
assert(items.check_turn_in(t,{item1=13737}), 'normal rejected')
assert(t.item1.valid and t.item1:GetID()==213737 and not t.item2.valid, 'exact item not preferred')
t=trade(213737,13737)
assert(items.check_turn_in(t,{item1=13737,item2=213737}), 'explicit tier not reserved')
t=trade(213737)
assert(not items.check_turn_in(t,{item1=13737,item2=213737}), 'one item counted twice')
assert(t.item1.valid, 'failed mixed requirement consumed item')
for _,id in ipairs({13737,413737,613737}) do
  assert(not items.check_turn_in(trade(id),{item1=213737}), 'explicit quality weakened')
end
t=trade(413737,613737)
assert(items.check_turn_in(t,{item1=13737,item2=13737}), 'mixed tiers did not combine')
t=trade(213737); t.platinum=2
assert(items.check_turn_in(t,{item1=13737,gold=15}), 'coin conversion failed')
assert(t.platinum==0 and t.gold==5, 'wrong change')
print('Lua quest hand-in regressions passed')
