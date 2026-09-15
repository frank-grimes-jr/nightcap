-- Run with: lua test-pok-class-status.lua path/to/global_player.lua
local messages = {}
local dispatched = 0
local fixed = 0
MT = { Yellow = 15 }
Class = {}
for id, name in ipairs({'WARRIOR','CLERIC','PALADIN','RANGER','SHADOWKNIGHT','DRUID','MONK','BARD','ROGUE','SHAMAN','NECROMANCER','WIZARD','MAGICIAN','ENCHANTER','BEASTLORD','BERSERKER'}) do
    Class[name] = id
end
package.preload['dragons_of_norrath'] = function()
    return { fix_invalid_faction_state = function() fixed = fixed + 1 end }
end
eq = {
    DispatchCommands = function() dispatched = dispatched + 1; return 71 end,
    get_qglobals = function() return { pok_attuned = '1' } end,
    is_dragons_of_norrath_enabled = function() return false end,
}
assert(loadfile(arg[1]))()
local function client(base, second, third)
    return {
        GetClass = function() return base end,
        GetClass2 = function() return second end,
        GetClass3 = function() return third end,
        Message = function(_, _, text) messages[#messages + 1] = text end,
    }
end
local cases = 0
for base = 1, 16 do
    messages = {}
    local c = client(base, 0, 0)
    assert(event_command({self=c, command='classes', args={}}) == 1)
    assert(#messages == 2)
    assert(messages[1]:find('Not selected (Second)', 1, true))
    assert(messages[1]:find('Not selected (Third)', 1, true))
    assert(not messages[1]:find('Unknown', 1, true))
    cases = cases + 1
end
messages = {}
local c = client(1, 2, 12)
assert(event_say({self=c, message='  !CLASSES  '}) == 1)
assert(messages[1] == 'Your classes: Warrior (Primary) | Cleric (Second) | Wizard (Third)')
assert(event_say({self=c, message='I like !classes'}) == 0)
assert(#messages == 2)
assert(event_command({self=c, command='don'}) == 71)
assert(dispatched == 1)
messages = {}
event_connect({self=c})
assert(messages[1] == 'Your classes: Warrior (Primary) | Cleric (Second) | Wizard (Third)')
assert(fixed == 1)
messages = {}
event_connect({self=client(9,0,0)})
assert(messages[1] == 'Your classes: Rogue (Primary) | Not selected (Second) | Not selected (Third)')
assert(fixed == 2)
print('PASS: 16 primary classes, explicit empty slots, both status commands, login, and command delegation')
