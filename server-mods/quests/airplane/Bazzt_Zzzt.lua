local dungeon = require("nightcap_dungeons")

function event_death_complete(e)
	eq.set_global(dungeon.key("sirran"),"6",3,"M20");
	if not dungeon.managed() then
		eq.spawn2(71058,0,0,234,-1078,812,384); --Sirran the Lunatic
	end
end
