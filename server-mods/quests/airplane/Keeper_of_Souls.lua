local dungeon = require("nightcap_dungeons")

-- Epic NPC -- Keeper_of_Souls

function event_spawn(e)
	if not dungeon.managed() then eq.set_timer("summit",1800000); end
end

function event_timer(e)
	if(e.timer == "summit") then
		eq.stop_timer("summit");
		if dungeon.managed() then return; end
		eq.depop();
	end
end

function event_death_complete(e)
	sirran= nil;
	eq.set_global(dungeon.key("sirran"),"4",3,"M20");
	if not dungeon.managed() then
		eq.spawn2(71058,0,0,-543,767,174,128); -- NPC: Sirran_the_Lunatic
	end
end

--Quest by: Solid11
-------------------------------------------------------------------------------------------------
-- Converted to .lua using MATLAB converter written by Stryd
-- Find/replace data for .pl --> .lua conversions provided by Speedz, Stryd, Sorvani and Robregen
-------------------------------------------------------------------------------------------------
