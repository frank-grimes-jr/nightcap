-- Managed runs use the original Hate population and native boss ownership.
-- Public and unmanaged instances keep the zone's existing encounters.
local dungeon = require('nightcap_dungeons')
if not dungeon.managed() then
    eq.load_encounter('rogue_1_5');
    eq.load_encounter('maestro');
    eq.load_encounter('inny');
end
