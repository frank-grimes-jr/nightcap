-- a ghoul assassin. The stock loot table rolls once per GlobalLootMultiplier.
-- Roll the bonus once per fresh spawn, then let AddItem handle ordinary quality.
function event_spawn(e)
    if not e.self:IsResumedFromZoneSuspend() and Random.Roll(20) then
        e.self:AddItem(2469, 1, false) -- Guise of the Deceiver
    end
end
