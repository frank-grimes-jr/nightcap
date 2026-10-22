-- Execute real quest handlers and the real items.lua helper with native boundaries faked.
-- lua5.1 quest_armor_rewards.lua QUEST_ROOT ITEMS_MODULE
-- Or use run_quest_armor_lua_tests.py for the installed local Docker Lua runtime.
local quest_root = assert(arg[1], "Expected quest root")
local items_path = assert(arg[2], "Expected actual lua_modules/items.lua path")
local source_files = QUEST_TEST_SOURCES or {}
local function load_source(path)
    local source = source_files[path]
    if source then return assert(loadstring(source, "@" .. path)) end
    return assert(loadfile(path))
end
package.preload.items = function() return load_source(items_path)() end
package.loaded.items = nil

local total, failures = 0, 0
local function equal(actual, expected, description)
    assert(actual == expected, description .. ": expected " .. tostring(expected) .. ", got " .. tostring(actual))
end
local function test(description, run)
    total = total + 1
    local ok, err = pcall(run)
    if not ok then failures = failures + 1 end
    print((ok and "ok " or "not ok ") .. total .. " - " .. description)
    if not ok then print("# " .. tostring(err):gsub("\n", "\n# ")) end
end

-- Only native EQEmu objects are faked. check_turn_in and return_items come from
-- the installed quest helper, including its whole-slot consumption semantics.
function ItemInst(id, charges, attuned)
    local item = {valid = id ~= nil, id = id or 0, charges = charges or 1,
                  attuned = attuned or false, custom_data = "retain-instance-data"}
    function item:GetID() return self.id end
    function item:GetCharges() return self.charges end
    function item:IsInstNoDrop() return self.attuned end
    function item:RemoveTaskDeliveredItems() return self.charges end
    return item
end
eq = {is_disc_tome = function() return false end, send_player_handin_event = function() end}

local function player()
    local client = {summons = {}, returned = {}, xp = 0, dings = 0, variables = {}, money = 0,
                    factions = {}, quest_rewards = {}}
    function client:SummonItem(id) self.summons[#self.summons + 1] = id end
    function client:PushItemOnCursor(item) self.returned[#self.returned + 1] = item end
    function client:Ding() self.dings = self.dings + 1 end
    function client:AddEXP(value) self.xp = self.xp + value end
    function client:Faction(id, amount) self.factions[#self.factions + 1] = {id, amount} end
    function client:QuestReward(actor, copper, silver, gold, platinum, id, xp)
        self.quest_rewards[#self.quest_rewards + 1] = {copper, silver, gold, platinum, id, xp}
        self:SummonItem(id)
        self:AddEXP(xp)
        self:AddMoneyToPP(copper, silver, gold, platinum)
    end
    function client:SetEntityVariable(key, value) self.variables[key] = value end
    function client:GetCleanName() return "Palwar" end
    function client:AddMoneyToPP(copper, silver, gold, platinum)
        self.money = self.money + copper + 10 * silver + 100 * gold + 1000 * platinum
    end
    return client
end
local function npc()
    local actor = {sayings = {}}
    function actor:Say(text) self.sayings[#self.sayings + 1] = text end
    function actor:GetClass() return 1 end
    return actor
end
local function trade_for(client, ids)
    local trade = {other = client, copper = 0, silver = 0, gold = 0, platinum = 0}
    for slot = 1, 4 do trade["item" .. slot] = ItemInst(ids[slot]) end
    return trade
end
local function handler(name)
    event_trade = nil
    load_source(quest_root .. "/" .. name .. ".lua")()
    return assert(event_trade, "Quest must define event_trade")
end
local function handin(run, client, trade)
    run({self = npc(), other = client, trade = trade})
end
local function no_reward(client)
    equal(#client.summons, 0, "no reward")
    equal(client.xp, 0, "no XP")
    equal(client.dings, 0, "no completion ding")
    equal(#client.factions, 0, "no faction reward")
end
local function returned_unchanged(client, originals)
    equal(#client.returned, #originals, "returned item count")
    for i, item in ipairs(originals) do
        equal(client.returned[i], item, "returned original instance " .. i)
        equal(client.returned[i].custom_data, "retain-instance-data", "custom instance data " .. i)
    end
end
local function success(client, reward, xp, dings, factions)
    equal(#client.summons, 1, "one armor reward")
    equal(client.summons[1], reward, "ordinary Ascended reward ID")
    equal(client.xp, xp, "original XP")
    equal(client.dings, dings, "original completion ding")
    equal(#client.factions, #(factions or {}), "original faction count")
    for i, faction in ipairs(factions or {}) do
        equal(client.factions[i][1], faction[1], "original faction ID")
        equal(client.factions[i][2], faction[2], "original faction amount")
    end
    if factions then
        equal(#client.quest_rewards, 1, "one native QuestReward")
        for i = 1, 4 do equal(client.quest_rewards[1][i], 0, "original coin reward " .. i) end
    end
end

-- Independent specifications, not generated from the implementation or reward catalog.
local crafted = {
    {"southkarana/Shakrn_Meadowgreen", "Crafted Helm", 604173, {13743, 10035}},
    {"southkarana/Shakrn_Meadowgreen", "Crafted Gauntlets", 604178, {13737, 10032, 10032}},
    {"southkarana/Shakrn_Meadowgreen", "Crafted Plate Boots", 604180, {13744, 10034, 10034}},
    {"southkarana/Shakrn_Meadowgreen", "Crafted Vambraces", 604176, {13739, 10033, 10033}},
    {"southkarana/Ulan_Meadowgreen", "Crafted Bracers", 604177, {14019, 10034}},
    {"southkarana/Ulan_Meadowgreen", "Crafted Greaves", 604179, {13742, 10032, 10032}},
    {"southkarana/Ulan_Meadowgreen", "Crafted Pauldron", 604175, {13698, 13699, 13738, 10033}},
    {"southkarana/Ulan_Meadowgreen", "Crafted Breastplate", 604174, {13746, 10035, 10035, 10035}},
    {"soltemple/Walthin_Fireweaver", "Lambent Boots", 604159, {2318, 10119, 10561}, 1000, 0, {{415,5}, {416,-5}}},
    {"soltemple/Walthin_Fireweaver", "Lambent Gauntlets", 604157, {2319, 10117, 4114}, 1000, 0, {{415,5}, {416,-5}}},
    {"soltemple/Walthin_Fireweaver", "Lambent Greaves", 604158, {4115, 10128, 4116}, 1000, 0, {{415,5}, {416,-5}}},
}

for _, spec in ipairs(crafted) do
    local name, label, reward, ids = unpack(spec)
    local xp, dings = spec[5] or 25000, spec[6] or 1
    local function expected_success(client) success(client, reward, xp, dings, spec[7]) end
    local run = handler(name)
    test(label .. " grants Ascended and retains XP", function()
        local client = player()
        local trade = trade_for(client, ids)
        handin(run, client, trade)
        expected_success(client)
        equal(#client.returned, 0, "all required inputs consumed")
        for slot = 1, 4 do equal(trade["item" .. slot].valid, false, "consumed slot " .. slot) end
    end)
    test(label .. " repeated completion requires a fresh full hand-in", function()
        local client = player()
        handin(run, client, trade_for(client, ids))
        handin(run, client, trade_for(client, {}))
        equal(#client.summons, 1, "empty repeat cannot grant armor")
        equal(client.xp, xp, "empty repeat cannot grant XP")
        handin(run, client, trade_for(client, ids))
        equal(#client.summons, 2, "fresh earned completion remains repeatable")
        equal(client.summons[1], reward, "first Ascended reward")
        equal(client.summons[2], reward, "repeat Ascended reward")
        equal(client.xp, 2 * xp, "two earned XP rewards")
        equal(client.dings, 2 * dings, "two earned completion dings")
        equal(#client.factions, 2 * #(spec[7] or {}), "two earned faction rewards")
    end)
    test(label .. " accepts unordered hand-in slots", function()
        local client, reversed = player(), {}
        for i = #ids, 1, -1 do reversed[#reversed + 1] = ids[i] end
        handin(run, client, trade_for(client, reversed))
        expected_success(client)
        equal(#client.returned, 0, "all reordered required inputs consumed")
    end)
    for missing = 1, #ids do
        test(label .. " partial hand-in missing slot " .. missing .. " returns original items", function()
            local client, partial, originals = player(), {}, {}
            for i, id in ipairs(ids) do if i ~= missing then partial[#partial + 1] = id end end
            local trade = trade_for(client, partial)
            for i = 1, #partial do
                local item = trade["item" .. i]
                item.attuned, item.charges = true, 7
                originals[#originals + 1] = item
            end
            handin(run, client, trade)
            no_reward(client)
            returned_unchanged(client, originals)
            for _, item in ipairs(client.returned) do
                equal(item.attuned, true, "returned attunement")
                equal(item.charges, 7, "returned charges")
            end
        end)
    end
    test(label .. " unrelated input cannot replace a requirement", function()
        local client, originals = player(), {}
        local trade = trade_for(client, ids)
        trade.item1 = ItemInst(999, 9, true)
        for i = 1, #ids do originals[#originals + 1] = trade["item" .. i] end
        handin(run, client, trade)
        no_reward(client)
        returned_unchanged(client, originals)
    end)
    test(label .. " excess currency is fully returned", function()
        local client = player()
        local trade = trade_for(client, ids)
        trade.copper, trade.silver, trade.gold, trade.platinum = 3, 2, 1, 1
        handin(run, client, trade)
        expected_success(client)
        equal(client.money, 1123, "original currency returned in copper units")
    end)
    test(label .. " retains existing whole-slot required-stack consumption", function()
        local client = player()
        local trade = trade_for(client, ids)
        trade.item1.charges = 3
        handin(run, client, trade)
        expected_success(client)
        equal(#client.returned, 0, "existing helper consumes the entire required slot")
    end)
    if #ids < 4 then
        test(label .. " excess unrelated item returns the original instance", function()
            local client = player()
            local trade = trade_for(client, ids)
            local extra = ItemInst(999, 9, true)
            trade["item" .. (#ids + 1)] = extra
            handin(run, client, trade)
            expected_success(client)
            returned_unchanged(client, {extra})
            equal(extra.charges, 9, "excess item charges")
            equal(extra.attuned, true, "excess item binding")
        end)
    end
    if #ids >= 3 and ids[2] == ids[3] then
        test(label .. " stacked gems do not bypass separate-slot requirements", function()
            local client, originals = player(), {}
            local trade = trade_for(client, {ids[1], ids[2]})
            trade.item2.charges = #ids - 1
            originals = {trade.item1, trade.item2}
            handin(run, client, trade)
            no_reward(client)
            returned_unchanged(client, originals)
            equal(trade.item2.charges, #ids - 1, "gem stack returned intact")
        end)
    end
end

print("1.." .. total)
print("# " .. (total - failures) .. " passed, " .. failures .. " failed")
os.exit(failures == 0 and 0 or 1)
