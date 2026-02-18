local addonName, addonTable             = ...

local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()

if classFilename == "DRUID" and currentSpec == 1 then
    -- table.insert(addonTable.Spell, 8921)    -- [月火术]
    -- table.insert(addonTable.Spell, 78674)   --[星涌术]
    -- table.insert(addonTable.Spell, 88747)   --[野性蘑菇]
    -- table.insert(addonTable.Spell, 93402)   --[阳炎术]
    -- table.insert(addonTable.Spell, 190984)  --[愤怒]
    -- table.insert(addonTable.Spell, 191034)  --[星辰坠落]
    -- table.insert(addonTable.Spell, 194153)  --[星火术]
    -- table.insert(addonTable.Spell, 202770)  --[艾露恩之怒]
    -- table.insert(addonTable.Spell, 205636)  --[自然之力]
    -- table.insert(addonTable.Spell, 274281)  --[新月]
    -- table.insert(addonTable.Spell, 390414)  --[化身：艾露恩之眷]
    -- table.insert(addonTable.Spell, 391528)  --[万灵之召]
    -- table.insert(addonTable.Spell, 1233346) --[日蚀]


    -- table.insert(addonTable.SpellCharge, 88747) --[野性蘑菇]
end
