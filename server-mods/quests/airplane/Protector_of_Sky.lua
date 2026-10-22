local dungeon = require("nightcap_dungeons")

function event_death_complete(e)
	eq.set_global(dungeon.key("sirran"),"2",3,"M20");
	if not dungeon.managed() then
		eq.spawn2(71058,0,0,-531,-214,-322,256); -- NPC: Sirran_the_Lunatic
	end
end

-------------------------------------------------------------------------------------------------
-- Converted to .lua using MATLAB converter written by Stryd
-- Find/replace data for .pl --> .lua conversions provided by Speedz, Stryd, Sorvani and Robregen
-------------------------------------------------------------------------------------------------
