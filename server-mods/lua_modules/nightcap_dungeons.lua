-- Paired with the native dungeon release. Never accept a run ID from chat.
local M = {}

function M.run_id()
    assert(type(eq.get_dungeon_run_id) == "function", "Matching dungeon binary is required")
    local id = eq.get_dungeon_run_id()
    assert(type(id) == "string", "Invalid native dungeon identity")
    if id ~= "" then
        assert(#id == 36 and id:match("^[%x]+%-%x+%-%x+%-%x+%-%x+$"), "Invalid native dungeon identity")
    end
    return id
end

function M.managed()
    return M.run_id() ~= ""
end

function M.key(name)
    assert(name == "sirran" or name == "keeper", "Unknown Sky quest key")
    local id = M.run_id()
    return id == "" and name or ("ncsky_" .. id .. "_" .. name)
end

return M
