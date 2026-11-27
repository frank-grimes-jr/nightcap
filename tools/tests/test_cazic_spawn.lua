-- Run from the repository root with Lua 5.1.
local managed = false
package.preload.nightcap_dungeons = function()
    return { managed = function() return managed end }
end
dofile("server-mods/quests/fearplane/Cazic_Thule.lua")

for _, private_zone in ipairs({false, true}) do
    managed = private_zone
    local removed, timers = {}, {}
    eq = { set_timer = function(name, delay) timers[name] = delay end }
    local npc = { RemoveAISpell = function(_, spell) table.insert(removed, spell) end }
    event_spawn({ self = npc })
    assert(#removed == 1 and removed[1] == 808)
    assert(timers.Shout == 600000)
    if private_zone then
        assert(timers.RepopZone == nil)
    else
        assert(timers.RepopZone == 5000)
    end
end
