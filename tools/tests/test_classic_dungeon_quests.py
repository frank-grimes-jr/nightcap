"""Execute the actual paired Lua quests against isolated run-aware test doubles."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]

class PlaneQuests(unittest.TestCase):
    def test_actual_quests_isolate_runs_and_preserve_public_keys(self):
        paths=list((ROOT/'server-mods/quests/airplane').glob('*.lua'))
        paths+=list((ROOT/'server-mods/quests/fearplane').glob('*.lua'))
        sources={p.parent.name+'/'+p.name:p.read_text() for p in paths}
        sources['module']=(ROOT/'server-mods/lua_modules/nightcap_dungeons.lua').read_text()
        lua='local scripts={\n'+',\n'.join('['+json.dumps(k)+']=[====['+v+']====]' for k,v in sources.items())+'\n}\n'
        lua+=r'''
local loadcode=loadstring or load
for name,source in pairs(scripts) do assert(loadcode(source,name)) end
local id, globals, spawned, timers, conditions, grants, updates, depops = ""
local A="00000000-0000-4000-8000-000000000001"
local B="00000000-0000-4000-8000-000000000002"
local mobs={}
eq={get_dungeon_run_id=function()return id end,
 get_qglobals=function()return globals end,
 set_global=function(k,v)globals[k]=v end,delete_global=function(k)globals[k]=nil end,
 spawn2=function(n,...)table.insert(spawned,n) end,
 set_timer=function(k,v)timers[k]=v end,stop_timer=function(k)timers[k]=nil end,
 spawn_condition=function(...)table.insert(conditions,{...})end,depop=function()depops=depops+1 end,
 depop_with_timer=function()depops=depops+1 end,
 update_spawn_timer=function(...)table.insert(updates,{...})end,
 get_entity_list=function()return {IsMobSpawnedByNpcTypeID=function(_,n)return mobs[n] or false end}end}
package.preload.nightcap_dungeons=assert(loadcode(scripts.module))
package.preload.items=function()return {
 check_turn_in=function(trade,want)return want[1] or (want.item1~=nil and trade.item==want.item1) end,
 return_items=function()end}end
local d=require('nightcap_dungeons')
local e={self={GetX=function()return 1 end,GetY=function()return 2 end,
 GetZ=function()return 3 end,GetHeading=function()return 4 end,Say=function()end},
 other={SummonItem=function(_,n)table.insert(grants,n)end,GetName=function()return 'Tester' end},trade={}}
local function reset(run)
 id=run;globals={};spawned={};timers={};conditions={};grants={};updates={};mobs={};depops=0
end
local function script(name)assert(loadcode(scripts[name],name))()end
reset(A)
script('airplane/a_thunder_spirit_princess.lua');event_death_complete(e)
assert(globals[d.key('sirran')]=='1' and globals.sirran==nil)
id=B;script('airplane/Gorgalosk.lua');event_death_complete(e)
assert(globals[d.key('sirran')]=='3')
id=A;assert(globals[d.key('sirran')]=='1')
id='';assert(d.key('sirran')=='sirran' and d.key('keeper')=='keeper')
script('airplane/a_thunder_spirit_princess.lua');event_death_complete(e)
assert(globals.sirran=='1')

-- Canonical island key services are present independent of boss callbacks.
-- Early Lord death neither duplicates Sirran nor retries a retired Raid boss.
reset(A);mobs[71009]=true;mobs[71013]=true
script('airplane/The_Spiroc_Lord.lua');event_death_complete(e)
assert(#spawned==0 and #updates==0)
reset('');mobs[71009]=true;mobs[71013]=true
script('airplane/The_Spiroc_Lord.lua');event_death_complete(e)
assert(#spawned==0 and #updates==1)

-- A donation must not despawn the managed princess before objective credit.
for _,run in ipairs({A,''})do
 reset(run);script('airplane/a_thunder_spirit_princess.lua');e.gold=10;event_trade(e)
 assert(spawned[1]==71073 and depops==(run=='' and 1 or 0))
 if run~='' then mobs[71073]=true;event_trade(e);assert(#spawned==1 and depops==0) end
end

-- Canonical managed bosses are never recreated by timers/quest callbacks.
reset(A);script('airplane/Key_Master.lua');event_spawn(e)
for i=1,10 do e.signal=1;event_signal(e)end
e.signal=2;event_signal(e);e.timer='87';event_timer(e)
assert(#spawned==0 and next(timers)==nil and next(globals)==nil)
script('airplane/Bzzzt.lua');event_death_complete(e);assert(#spawned==0)
reset('');script('airplane/Key_Master.lua');event_spawn(e)
for i=1,10 do e.signal=1;event_signal(e)end
assert(spawned[1]==71059)
e.signal=2;event_signal(e);assert(timers['87'] and globals.keeper=='1')

-- Retain all eight native key exchanges in either scope.
for _,case in ipairs({{'Keeper_of_Souls.lua','summit',1800000},{'Sirran_the_Lunatic.lua','bye',1200000}})do
 reset(A);script('airplane/'..case[1]);event_spawn(e)
 assert(timers[case[2]]==nil);e.timer=case[2];event_timer(e);assert(depops==0)
 reset('');script('airplane/'..case[1]);event_spawn(e)
 assert(timers[case[2]]==case[3]);event_timer(e);assert(depops==1)
end
for _,run in ipairs({'',A})do
 reset(run);script('airplane/Sirran_the_Lunatic.lua')
 for item=20920,20927 do e.trade={item=item};event_trade(e)end
 for i=1,8 do assert(grants[i]==20910+i)end
 assert(#grants==8)
end

-- No managed callback, including a stale timer, can toggle public Fear.
reset(A);script('fearplane/Cazic_Thule.lua');event_spawn(e)
assert(timers.Shout and timers.RepopZone==nil)
e.timer='RepopZone';event_timer(e);assert(#conditions==0)
reset('');script('fearplane/Cazic_Thule.lua');event_spawn(e)
assert(timers.RepopZone==5000);e.timer='RepopZone';event_timer(e)
assert(#conditions==2 and conditions[1][2]==0 and conditions[2][2]==0)

reset('invalid');assert(not pcall(d.key,'sirran'))
eq.get_dungeon_run_id=nil;assert(not pcall(d.managed))
print('PASS: actual Lua syntax, concurrent run isolation, public behavior, early Lord death, canonical boss ownership, eight key routes and Fear isolation')
'''
        result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','lua','-'],input=lua,
                              text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PASS:',result.stdout)
        print(result.stdout.strip())

if __name__=='__main__':unittest.main()
