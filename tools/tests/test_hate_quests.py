"""Execute paired Hate scripts under Lua 5.1, exercising both zone scopes."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]


class HateQuests(unittest.TestCase):
    def test_managed_callbacks_cannot_spawn_newer_epic_encounters(self):
        sources={p.name:p.read_text() for p in (ROOT/'server-mods/quests/hateplaneb').glob('*.lua')}
        sources['module']=(ROOT/'server-mods/lua_modules/nightcap_dungeons.lua').read_text()
        script='local scripts={'+','.join('['+json.dumps(k)+']=[====['+v+']====]' for k,v in sources.items())+'}\n'
        script+=r'''
local loadcode=loadstring or load
for name,source in pairs(scripts)do assert(loadcode(source,name))end
local id='00000000-0000-4000-8000-000000000001'
local calls,spawns,timers=0,0,0
local globals={Fatestealer='1'}
MT={Yellow=1,Red=2}
eq={get_dungeon_run_id=function()return id end,
 load_encounter=function()calls=calls+1 end,
 get_qglobals=function()return globals end,
 set_global=function(k,v)globals[k]=v end,
 set_timer=function()timers=timers+1 end,
 stop_timer=function()timers=timers-1 end,
 spawn2=function()spawns=spawns+1 end,zone_emote=function()calls=calls+1 end}
package.preload.nightcap_dungeons=assert(loadcode(scripts.module))
local self={ClearCompassMark=function()calls=calls+1 end,Class=function()return 'Rogue' end,
 GetX=function()return 1 end,GetY=function()return 2 end,GetZ=function()return 3 end,GetHeading=function()return 0 end}
local event={self=self,item={GetID=function()return 52337 end},timer='s1'}
assert(loadcode(scripts['script_init.lua']))()
assert(loadcode(scripts['player.lua']))()
event_enter_zone(event);event_loot(event);event_timer(event)
assert(calls==0 and spawns==0 and timers==0 and globals.rogue_hate_chest==nil)
id='';assert(loadcode(scripts['script_init.lua']))();assert(calls==3)
event_enter_zone(event);assert(timers==3 and globals.hpb_zone_emote=='1')
event_loot(event);assert(spawns==1 and globals.rogue_hate_chest=='1')
event_loot(event);assert(spawns==1)
event_timer(event);assert(timers==2)
print('PASS: managed isolation and public encounter/epic behavior')
'''
        result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','lua','-'],input=script,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PASS:',result.stdout)


if __name__=='__main__':unittest.main()
