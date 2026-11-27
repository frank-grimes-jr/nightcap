-- Run from the repository root with Lua 5.1.
package.preload.dragons_of_norrath = function()
    return { fix_invalid_faction_state = function() end }
end
Class = setmetatable({}, { __index = function(_, key) return key end })
dofile("server-mods/quests/global/global_player.lua")
grant_veteran_aa = function() end
MT = { Yellow = 1 }

local function login(owned, allow_grant, old_marker)
    local attempts, messages = 0, 0
    eq = {
        set_global = function(key, value, scope, duration)
            assert(key == "pok_attuned" and value == "1" and scope == 0 and duration == "F")
            old_marker = true
        end
    }
    local client = {
        GetAAByAAID = function(_, family) assert(family == 2220); return owned end,
        GrantAlternateAdvancementAbility = function(_, family, rank)
            assert(family == 2220 and rank == 1)
            attempts = attempts + 1
            if allow_grant then owned = 1 end
            return allow_grant
        end,
        Message = function(_, _, message)
            if message:find("Nightcap Recall", 1, true) then messages = messages + 1 end
        end,
        GetClass = function() return 17 end,
        GetClass2 = function() return 0 end,
        GetClass3 = function() return 0 end
    }
    event_connect({ self = client })
    return attempts, messages, old_marker
end

for _, marker in ipairs({false, true}) do
    local attempts, messages, marked = login(0, true, marker)
    assert(attempts == 1 and messages == 1 and marked)
    attempts, messages, marked = login(0, false, marker)
    assert(attempts == 1 and messages == 0 and marked == marker)
    attempts, messages = login(1, true, marker)
    assert(attempts == 0 and messages == 0)
end
