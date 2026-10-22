local dungeon = require("nightcap_dungeons")

function event_death_complete(e)
	local qglobals = eq.get_qglobals();
	
	if dungeon.managed() or (qglobals[dungeon.key("sirran")] ~= "5" and not eq.get_entity_list():IsMobSpawnedByNpcTypeID(71009)) then
		eq.set_global(dungeon.key("sirran"),"5",3,"M20");
		if not dungeon.managed() then
			eq.spawn2(71058,0,0,955,-570,466,390); -- NPC: Sirran_the_Lunatic
		end
	end
	if not dungeon.managed() and (eq.get_entity_list():IsMobSpawnedByNpcTypeID(71013) or eq.get_entity_list():IsMobSpawnedByNpcTypeID(71009)) then
		eq.update_spawn_timer(2630,1000); --update to respawn in 1 sec if vanquisher or guardian are still up
	end
end
