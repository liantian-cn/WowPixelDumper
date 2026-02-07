local addonName, addonTable             = ...

local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()

-- PriestDiscipline
if classFilename == "PRIEST" and currentSpec == 1 then
    -- table.insert(addonTable.Spell, { spellID = 47540, type = "charge" })    -- [苦修]
    -- table.insert(addonTable.Spell, { spellID = 194509, type = "charge" })   -- [真言术：耀]
    -- table.insert(addonTable.Spell, { spellID = 33206, type = "charge" })    --[痛苦压制]
    -- table.insert(addonTable.Spell, { spellID = 17, type = "cooldown" })     -- [真言术：盾]
    -- table.insert(addonTable.Spell, { spellID = 8092, type = "cooldown" })   --[心灵震爆]
    -- table.insert(addonTable.Spell, { spellID = 527, type = "cooldown" })    --[纯净术]
    -- table.insert(addonTable.Spell, { spellID = 32379, type = "cooldown" })  --[暗言术：灭]
    -- table.insert(addonTable.Spell, { spellID = 19236, type = "cooldown" })  --[绝望祷言]
    -- table.insert(addonTable.Spell, { spellID = 472433, type = "cooldown" }) --[福音]
    -- table.insert(addonTable.Spell, { spellID = 586, type = "cooldown" })    --[渐隐术]
end
