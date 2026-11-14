-- Run from the repository root with Lua 5.1, or pass the installed quest path.
dofile(arg[1] or "server-mods/quests/gukbottom/66171.lua")

local roll, calls, resumed
Random = {
    Roll = function(percent)
        calls = calls + 1
        return roll < percent -- EQ::Random::Roll uses Int(0, 99).
    end
}

local loot
local npc = {
    IsResumedFromZoneSuspend = function() return resumed end,
    AddItem = function(self, id, charges, equip)
        assert(id == 2469 and charges == 1 and equip == false)
        table.insert(loot, id)
    end
}

for _, stock in ipairs({2472, 7502}) do
    local successes = 0
    for n = 0, 99 do
        roll, calls, resumed = n, 0, false
        loot = {stock}
        event_spawn({self = npc})
        assert(calls == 1 and loot[1] == stock)
        assert(#loot == (n < 20 and 2 or 1))
        successes = successes + #loot - 1

        -- A zone resume must preserve both a prior hit and a prior miss.
        calls, resumed = 0, true
        local saved_count = #loot
        event_spawn({self = npc})
        assert(calls == 0 and #loot == saved_count)
    end
    assert(successes == 20)
end
print("PASS: 20 of 100 rolls alongside each stock item; saved loot preserved")
