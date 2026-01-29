local addonName, addonTable             = ...

local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()

if classFilename == "PRIEST" and currentSpec == 1 then
    table.insert(addonTable.SpellCharge, 47540)  -- [苦修]
    table.insert(addonTable.SpellCharge, 194509) -- [真言术：耀]
    table.insert(addonTable.SpellCD, 17)         -- [真言术：盾]
    table.insert(addonTable.SpellCD, 47540)      --[苦修]
    table.insert(addonTable.SpellCD, 8092)       --[心灵震爆]
    table.insert(addonTable.SpellCD, 527)        --[纯净术]
    table.insert(addonTable.SpellCD, 194509)     --[真言术：耀]
    table.insert(addonTable.SpellCD, 32379)      --[暗言术：灭]
    table.insert(addonTable.SpellCD, 19236)      --[绝望祷言]
    table.insert(addonTable.SpellCD, 472433)     --[福音]
    table.insert(addonTable.SpellCD, 586)        --[渐隐术]
    table.insert(addonTable.SpellCD, 33206)      --[痛苦压制]
end
