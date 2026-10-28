"""Execute candidate Lua and captured production helper in Lua 5.1 (lupa.lua51)."""
import json
from pathlib import Path
import unittest
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / 'docs/items/paladin-weapon-grip/balance/production-reference-complete.json'
PATHS = ['paw/v0/Brother_Hayle.lua', 'southkarana/#Brother_Hayle.lua', 'airplane/Inte_Akera.lua', 'fearplane/Irak_Altil.lua']

HARNESS = r'''
function ItemInst(id)
 local i={valid=id~=nil,id=id or 0,charges=7,attuned=true,metadata="nightcap_paladin_grip^1^"}
 function i:GetID() return self.id end
 function i:GetName() return NAMES[self.id] or "unrelated" end
 function i:GetCharges() return self.charges end
 function i:IsInstNoDrop() return self.attuned end
 function i:RemoveTaskDeliveredItems() return self.charges end
 return i
end
eq={get_item_name=function(id) return NAMES[id] or "" end,
 is_disc_tome=function() return false end,send_player_handin_event=function() end,
 depop=function() DEPOPS=DEPOPS+1 end,set_global=function() end}
package.preload.items=function() return assert(loadstring(HELPER))() end
function run(source,ids,faction)
 DEPOPS=0
 local c={summons={},returned={},xp=0,money=0,dings=0,factions={},variables={}}
 function c:SummonItem(id) table.insert(self.summons,id) end
 function c:PushItemOnCursor(i) table.insert(self.returned,i) end
 function c:AddEXP(n) self.xp=self.xp+n end
 function c:Ding() self.dings=self.dings+1 end
 function c:Faction(...) table.insert(self.factions,{...}) end
 function c:GetFaction() return faction end
 function c:GetModCharacterFactionLevel() return faction==1 and 750 or 749 end
 function c:HasItem() return false end
 function c:GetCleanName() return "test" end
 function c:SetEntityVariable(k,v) self.variables[k]=v end
 function c:AddMoneyToPP(cp,sp,gp,pp) self.money=self.money+cp+10*sp+100*gp+1000*pp end
 function c:QuestReward(actor,a,b,g,p,id,xp)
  if type(a)=="table" then self:SummonItem(a.itemid);self:AddEXP(a.exp)
  else self:SummonItem(id);self:AddEXP(xp);self:AddMoneyToPP(a,b,g,p) end
 end
 local n={Say=function() end,Emote=function() end,GetClass=function() return 1 end,GetPrimaryFaction=function() return 341 end}
 local trade={other=c,copper=3,silver=2,gold=1,platinum=0}
 local originals={}
 for i=1,4 do trade["item"..i]=ItemInst(ids[i]);originals[i]=trade["item"..i] end
 event_trade=nil;assert(loadstring(source))();assert(event_trade)({self=n,other=c,trade=trade})
 for _,i in ipairs(c.returned) do
  local same=false;for _,o in ipairs(originals) do if i==o then same=true end end
  assert(same and i.charges==7 and i.attuned and i.metadata=="nightcap_paladin_grip^1^")
 end
 c.depop=DEPOPS
 return c
end
'''


class PaladinQuestRewards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capture = json.loads(CAPTURE.read_text(encoding='utf-8'))

    def execute(self, path, ids, faction=1, baseline=False):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.globals().HELPER = self.capture['helpers']['lua_modules/items.lua']['source']
        lua.globals().NAMES = lua.table_from({r['id']: r['Name'] for r in self.capture['items']})
        lua.execute(HARNESS)
        candidate = ROOT/'server-mods/quests'/path
        source = self.capture['scripts'][path]['source'] if baseline or not candidate.exists() else candidate.read_text(encoding='utf-8')
        result = lua.globals().run(source, lua.table_from(ids), faction)
        return {'rewards': list(result.summons.values()), 'returned': [v.id for v in result.returned.values()],
                'xp': result.xp, 'money': result.money, 'depop': result.depop, 'dings': result.dings,
                'factions': [list(v.values()) for v in result.factions.values()]}

    def test_earned_rewards_are_ascended(self):
        for path, ids, reward in [(PATHS[0],[18937,13947,18828,12197],605504),
                                  (PATHS[1],[18937,13947,18828,12197],605504),
                                  (PATHS[2],[18033,18034,19073,1254],611050),
                                  (PATHS[3],[29010,611050],810099)]:
            for order in [ids,list(reversed(ids))]:
                with self.subTest(path=path,ids=order):
                    self.assertEqual(self.execute(path,order)['rewards'],[reward])

    def test_original_branches_and_failure_behavior_preserved(self):
        scenarios={PATHS[0]:[[18927],[18936],[18937,13947,18828,12197]],
                   PATHS[1]:[[18927],[18936],[18937,13947,18828,12197]],
                   PATHS[2]:[[5504],[605504],[5403],[605403],[18033,18034,19073,1254],[47100]], PATHS[3]:[[29010,11050],[29010,611050],[29010],[11050]]}
        for path,cases in scenarios.items():
            all_cases=[[],[99999]]+cases
            for ids in cases:
                all_cases.extend([ids[:i]+ids[i+1:] for i in range(len(ids))])
            for ids in all_cases:
                for faction in [1,2,3]:
                    with self.subTest(path=path,ids=ids,faction=faction):
                        before=self.execute(path,ids,faction,True)
                        before['rewards']=[{5504:605504,11050:611050,10099:810099}.get(i,i) for i in before['rewards']]
                        self.assertEqual(self.execute(path,ids,faction),before)

    def test_ascended_chain_acceptance_and_direct_ascended_defender(self):
        for offset in [0,200000,400000,600000]:
            self.assertEqual(self.execute(PATHS[2],[5504+offset])['rewards'],[18033])
            result=self.execute('fearplane/Irak_Altil.lua',[29010,11050+offset])
            self.assertEqual(result['rewards'],[810099])
            self.assertEqual(result['returned'],[])

    def test_source_edits_are_only_rewards_and_obsolete_heal_dialogue(self):
        for path in PATHS:
            expected=self.capture['scripts'][path]['source']
            expected=expected.replace('itemid = 5504,','itemid = 605504,').replace('SummonItem(5504)','SummonItem(605504)').replace('SummonItem(11050)','SummonItem(611050)').replace('SummonItem(10099)','SummonItem(810099)')
            expected=expected.replace('The power of the blade can be called upon to heal you if need be.','Right-click the blade to switch between one-handed and two-handed grips.')
            self.assertEqual((ROOT/'server-mods/quests'/path).read_text(encoding='utf-8'),expected)

    def test_later_epic_recognizes_ascended_defender(self):
        for item in [10099,810099,69913,99999]:
            lua=LuaRuntime(unpack_returned_tuples=True)
            lua.execute('''
string.findi=function(s,p) return s:lower():find(p:lower(),1,true) end
flag=nil
eq={get_qglobals=function() return {} end,say_link=function(s) return s end,
 set_global=function(k,v) flag=v end}
''')
            lua.execute((ROOT/'server-mods/quests/hohonora/#Irak_Altil.lua').read_text())
            lua.globals().owned=item
            lua.execute('''event_say({message="hail",self={Say=function() end},
 other={HasItem=function(s,id) return id==owned end,GetName=function() return "Test" end}})''')
            self.assertEqual(lua.globals().flag,None if item==99999 else '1')


if __name__ == '__main__':
    unittest.main()
