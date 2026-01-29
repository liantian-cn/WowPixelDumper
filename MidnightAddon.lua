local addonName, addonTable     = ...
local LibRangeCheck             = LibStub:GetLibrary("LibRangeCheck-3.0", true)

local DEBUG                     = false
local scale                     = 1
local fontFile, _, _            = GameFontNormal:GetFont()

local logging                   = function(msg)
    print("|cFFFFBB66[" .. addonName .. "]|r", msg)
end

local DEBUFF_DISPLAY_COLOR_INFO = {
    -- [0] = DEBUFF_TYPE_NONE_COLOR,
    [0] = { r = 0, g = 0, b = 0, a = 1 },
    [1] = DEBUFF_TYPE_MAGIC_COLOR,
    [2] = DEBUFF_TYPE_CURSE_COLOR,
    [3] = DEBUFF_TYPE_DISEASE_COLOR,
    [4] = DEBUFF_TYPE_POISON_COLOR,
    [9] = DEBUFF_TYPE_BLEED_COLOR,
    [11] = DEBUFF_TYPE_BLEED_COLOR,
}

local roleColor                 = {
    TANK = C_ClassColor.GetClassColor("WARRIOR"),
    HEALER = C_ClassColor.GetClassColor("PRIEST"),
    DAMAGER = C_ClassColor.GetClassColor("MAGE"),
    NONE = { 0, 0, 0 }
}

local function InitCurve()
    local curve = C_CurveUtil.CreateColorCurve()
    curve:SetType(Enum.LuaCurveType.Linear)
    curve:AddPoint(0.0, CreateColor(0, 0, 0))
    curve:AddPoint(1.0, CreateColor(1, 1, 1))

    local curve_reverse = C_CurveUtil.CreateColorCurve()
    curve_reverse:SetType(Enum.LuaCurveType.Linear)
    curve_reverse:AddPoint(0.0, CreateColor(1, 1, 1))
    curve_reverse:AddPoint(1.0, CreateColor(0, 0, 0))

    local debuff_curve = C_CurveUtil.CreateColorCurve()
    if debuff_curve then
        debuff_curve:SetType(Enum.LuaCurveType.Step)
        for i, c in pairs(DEBUFF_DISPLAY_COLOR_INFO) do
            debuff_curve:AddPoint(i, c)
        end
    end
    return curve, curve_reverse, debuff_curve
end


local curve, curve_reverse, debuff_curve = InitCurve()


local FrameInitFuncs   = {}
local UpdateFuncs      = {}
addonTable.SpellCD     = {}
addonTable.SpellCharge = {}
table.insert(addonTable.SpellCD, 61304) -- GCD

local frame = CreateFrame("Frame")

frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:SetScript("OnEvent", function(self, event, isInitialLogin, isReloadingUi)
    -- 只在初次登录或重新加载 UI 时执行一次
    -- 使用 C_Timer.After(0) 是为了确保在事件循环的下一帧执行
    -- 这样可以给图形引擎留出最后的"握手时间"
    C_Timer.After(0, function()
        wipe(UpdateFuncs)
        for _, func in ipairs(FrameInitFuncs) do
            func()
        end
    end)

    -- 执行完后注销事件，避免反复进入副本时重复加载
    self:UnregisterEvent("PLAYER_ENTERING_WORLD")
end)



local timeElapsed = 0
frame:HookScript("OnUpdate", function(self, elapsed)
    local tickOffset = 1.0 / addonTable.FPS;
    timeElapsed      = timeElapsed + elapsed
    if timeElapsed > tickOffset then
        timeElapsed = 0
        for _, updater in ipairs(UpdateFuncs) do
            updater()
        end
    end
end)


local function GetUIScaleFactor(pixelValue)
    local _, physicalHeight = GetPhysicalScreenSize()
    local logicalHeight = GetScreenHeight()
    return (pixelValue * logicalHeight) / physicalHeight
end

local function InitializeMainFrame()
    -- 计算UI元素尺寸
    addonTable.nodeSize = GetUIScaleFactor(10 * scale)
    addonTable.innerSize = GetUIScaleFactor(8 * scale)
    addonTable.padSize = GetUIScaleFactor(1 * scale)
    local node_size = addonTable.nodeSize
    -- 创建主框架
    addonTable.MainFrame = CreateFrame("Frame", addonName .. "MainFrame", UIParent)
    addonTable.MainFrame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", 0, 0)
    addonTable.MainFrame:SetSize(node_size * 52, node_size * 18)
    addonTable.MainFrame:SetFrameStrata("TOOLTIP")
    addonTable.MainFrame:SetFrameLevel(900)
    addonTable.MainFrame:Show()

    addonTable.MainFrame.bg = addonTable.MainFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MainFrame.bg:SetAllPoints()
    addonTable.MainFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.MainFrame.bg:Show()

    addonTable.PlayerBuffFrame = CreateFrame("Frame", addonName .. "PlayerBuffFrame", addonTable.MainFrame)
    addonTable.PlayerBuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerBuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -2 * node_size)
    addonTable.PlayerBuffFrame:SetSize(48 * node_size, 2 * node_size)
    addonTable.PlayerBuffFrame:Show()
    addonTable.PlayerBuffFrame.bg = addonTable.PlayerBuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerBuffFrame.bg:SetAllPoints()
    addonTable.PlayerBuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerBuffFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerBuffFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end


    addonTable.PlayerBarFrame = CreateFrame("Frame", addonName .. "PlayerBarFrame", addonTable.MainFrame)
    addonTable.PlayerBarFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerBarFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -4 * node_size)
    addonTable.PlayerBarFrame:SetSize(10 * node_size, 4 * node_size)
    addonTable.PlayerBarFrame.bg = addonTable.PlayerBarFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerBarFrame.bg:SetAllPoints()
    addonTable.PlayerBarFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerBarFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerBarFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    addonTable.PlayerSpellCDFrame = CreateFrame("Frame", addonName .. "PlayerSpellCDFrame", addonTable.MainFrame)
    addonTable.PlayerSpellCDFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerSpellCDFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 12 * node_size, -4 * node_size)
    addonTable.PlayerSpellCDFrame:SetSize(23 * node_size, 2 * node_size)
    addonTable.PlayerSpellCDFrame:Show()
    addonTable.PlayerSpellCDFrame.bg = addonTable.PlayerSpellCDFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerSpellCDFrame.bg:SetAllPoints()
    addonTable.PlayerSpellCDFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerSpellCDFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerSpellCDFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    addonTable.PlayerSpellChargeFrame = CreateFrame("Frame", addonName .. "PlayerSpellChargeFrame", addonTable.MainFrame)
    addonTable.PlayerSpellChargeFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerSpellChargeFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 35 * node_size, -4 * node_size)
    addonTable.PlayerSpellChargeFrame:SetSize(5 * node_size, 2 * node_size)
    addonTable.PlayerSpellChargeFrame:Show()
    addonTable.PlayerSpellChargeFrame.bg = addonTable.PlayerSpellChargeFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerSpellChargeFrame.bg:SetAllPoints()
    addonTable.PlayerSpellChargeFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerSpellChargeFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerSpellChargeFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    addonTable.PlayerDebuffFrame = CreateFrame("Frame", addonName .. "PlayerDebuffFrame", addonTable.MainFrame)
    addonTable.PlayerDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 12 * node_size, -6 * node_size)
    addonTable.PlayerDebuffFrame:SetSize(14 * node_size, 2 * node_size)
    addonTable.PlayerDebuffFrame:Show()
    addonTable.PlayerDebuffFrame.bg = addonTable.PlayerDebuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerDebuffFrame.bg:SetAllPoints()
    addonTable.PlayerDebuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerDebuffFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerDebuffFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    addonTable.TargetDebuffFrame = CreateFrame("Frame", addonName .. "TargetDebuffFrame", addonTable.MainFrame)
    addonTable.TargetDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.TargetDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 26 * node_size, -6 * node_size)
    addonTable.TargetDebuffFrame:SetSize(14 * node_size, 2 * node_size)
    addonTable.TargetDebuffFrame:Show()
    addonTable.TargetDebuffFrame.bg = addonTable.TargetDebuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.TargetDebuffFrame.bg:SetAllPoints()
    addonTable.TargetDebuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.TargetDebuffFrame.bg:Show()
    if DEBUG then
        addonTable.TargetDebuffFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    addonTable.PlayerStatusFrame = CreateFrame("Frame", addonName .. "PlayerStatusFrame", addonTable.MainFrame)
    addonTable.PlayerStatusFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerStatusFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 40 * node_size, -4 * node_size)
    addonTable.PlayerStatusFrame:SetSize(10 * node_size, 2 * node_size)
    addonTable.PlayerStatusFrame:Show()
    addonTable.PlayerStatusFrame.bg = addonTable.PlayerStatusFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerStatusFrame.bg:SetAllPoints()
    addonTable.PlayerStatusFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerStatusFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerStatusFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end


    addonTable.TargetStatusFrame = CreateFrame("Frame", addonName .. "TargetStatusFrame", addonTable.MainFrame)
    addonTable.TargetStatusFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.TargetStatusFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 40 * node_size, -6 * node_size)
    addonTable.TargetStatusFrame:SetSize(10 * node_size, 3 * node_size)
    addonTable.TargetStatusFrame:Show()
    addonTable.TargetStatusFrame.bg = addonTable.TargetStatusFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.TargetStatusFrame.bg:SetAllPoints()
    addonTable.TargetStatusFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.TargetStatusFrame.bg:Show()
    if DEBUG then
        addonTable.TargetStatusFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end


    addonTable.MiscFrame = CreateFrame("Frame", addonName .. "MiscFrame", addonTable.MainFrame)
    addonTable.MiscFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.MiscFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -8 * node_size)
    addonTable.MiscFrame:SetSize(node_size * 20, node_size * 1)
    addonTable.MiscFrame:Show()
    addonTable.MiscFrame.bg = addonTable.MiscFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MiscFrame.bg:SetAllPoints()
    addonTable.MiscFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.MiscFrame.bg:Show()
    if DEBUG then
        addonTable.MiscFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    addonTable.SpecFrame = CreateFrame("Frame", addonName .. "SpecFrame", addonTable.MainFrame)
    addonTable.SpecFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.SpecFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 22 * node_size, -8 * node_size)
    addonTable.SpecFrame:SetSize(node_size * 18, node_size * 1)
    addonTable.SpecFrame:Show()
    addonTable.SpecFrame.bg = addonTable.SpecFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.SpecFrame.bg:SetAllPoints()
    addonTable.SpecFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.SpecFrame.bg:Show()
    if DEBUG then
        addonTable.SpecFrame.bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
    end

    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)

        addonTable["PartyFrame" .. UnitKey] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey, addonTable.MainFrame)
        addonTable["PartyFrame" .. UnitKey]:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey]:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", (12 * i - 10) * node_size, -9 * node_size)
        addonTable["PartyFrame" .. UnitKey]:SetSize(node_size * 12, node_size * 7)
        addonTable["PartyFrame" .. UnitKey]:Show()
        addonTable["PartyFrame" .. UnitKey].bg = addonTable["PartyFrame" .. UnitKey]:CreateTexture(nil, "BACKGROUND")
        addonTable["PartyFrame" .. UnitKey].bg:SetAllPoints()
        addonTable["PartyFrame" .. UnitKey].bg:SetColorTexture(0, 0, 0, 1)
        addonTable["PartyFrame" .. UnitKey].bg:Show()
        if DEBUG then
            addonTable["PartyFrame" .. UnitKey].bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
        end
    end


    addonTable.ConfigFrame = CreateFrame("Frame", addonName .. "ConfigFrame", addonTable.MainFrame)
    addonTable.ConfigFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.ConfigFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 0, -16 * node_size)
    addonTable.ConfigFrame:SetSize(node_size * 4, node_size * 2)
    addonTable.ConfigFrame:Show()
    addonTable.ConfigFrame.bg = addonTable.ConfigFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.ConfigFrame.bg:SetAllPoints()
    addonTable.ConfigFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.ConfigFrame.bg:Show()
    if DEBUG then
        addonTable.ConfigFrame.bg:SetColorTexture(0, 1, 1, 0.3)
    end

    logging("MainFrame created")
end

table.insert(FrameInitFuncs, InitializeMainFrame)


local function CreateMiscNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local nodeFrame = CreateFrame("Frame", addonName .. "Misc" .. title, parent_frame)
    nodeFrame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size + padSize, -y * node_size - padSize)
    nodeFrame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    nodeFrame:SetSize(innerSize, innerSize)
    nodeFrame:Show()
    local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
    nodeTexture:SetAllPoints(nodeFrame)
    nodeTexture:SetColorTexture(0, 0, 0, 1)
    nodeTexture:Show()
    return nodeTexture
end

local function CreateAuraSequence(unit, filter, maxCount, name_prefix, parent, sortRule, sortDirection)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    sortRule = sortRule or Enum.UnitAuraSortRule.Default
    sortDirection = sortDirection or Enum.UnitAuraSortDirection.Normal
    local iconTextures = {}
    local durationTextures = {}
    local dispelTextures = {}
    local countTextures = {}


    for i = 1, maxCount do
        local icon_texture = CreateMiscNode((2 * i - 2), 0, addonName .. name_prefix .. "IconFrame" .. i, parent)
        table.insert(iconTextures, icon_texture)


        local duration_texture = CreateMiscNode((2 * i - 2), 1, addonName .. name_prefix .. "DurationFrame" .. i, parent)
        table.insert(durationTextures, duration_texture)


        local dispel_texture = CreateMiscNode((2 * i - 1), 0, addonName .. name_prefix .. "DispelFrame" .. i, parent)
        table.insert(dispelTextures, dispel_texture)

        local count_frame = CreateFrame("Frame", addonName .. name_prefix .. "CountFrame" .. i, parent)
        count_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (2 * i - 1) * node_size + padSize, -node_size - padSize)
        count_frame:SetFrameLevel(parent:GetFrameLevel() + 2)
        count_frame:SetSize(innerSize, innerSize)
        count_frame:Show()

        local count_texture = count_frame:CreateTexture(nil, "BACKGROUND")
        count_texture:SetAllPoints(count_frame)
        count_texture:SetColorTexture(0, 0, 0, 1)
        count_texture:Show()

        local count_string = count_frame:CreateFontString(nil, "ARTWORK", "GameFontNormal")
        count_string:SetAllPoints(count_frame)
        count_string:SetJustifyH("CENTER")
        count_string:SetJustifyV("MIDDLE")

        count_string:SetFontObject(GameFontHighlight)
        count_string:SetTextColor(1, 1, 1, 1)
        count_string:SetFont(fontFile, node_size / 1.5, "MONOCHROME")
        count_string:SetText("")

        count_string:Show()
        table.insert(countTextures, count_string)
    end

    local function wipeTextures()
        for _, texture in ipairs(iconTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
        for _, texture in ipairs(durationTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
        for _, texture in ipairs(dispelTextures) do
            texture:SetColorTexture(0, 0, 0, 1)
        end
        for _, texture in ipairs(countTextures) do
            texture:SetText("")
        end
    end

    local function updateTexture()
        wipeTextures()
        if not UnitExists(unit) then
            return
        end
        local auraInstanceIDs = C_UnitAuras.GetUnitAuraInstanceIDs(unit, filter, maxCount, sortRule, sortDirection)
        for i = 1, #auraInstanceIDs do
            local auraInstanceID = auraInstanceIDs[i]
            local aura = C_UnitAuras.GetAuraDataByAuraInstanceID(unit, auraInstanceID)
            local duration = C_UnitAuras.GetAuraDuration(unit, auraInstanceID)
            local result = duration:EvaluateElapsedPercent(curve_reverse)
            local dispelTypeColor = C_UnitAuras.GetAuraDispelTypeColor(unit, auraInstanceID, debuff_curve)
            local count = C_UnitAuras.GetAuraApplicationDisplayCount(unit, auraInstanceID, 1, 9)

            iconTextures[i]:SetTexture(aura.icon)
            durationTextures[i]:SetColorTexture(result.r, result.g, result.b, 1)
            dispelTextures[i]:SetColorTexture(dispelTypeColor:GetRGBA())
            countTextures[i]:SetText(count)
        end
    end
    table.insert(UpdateFuncs, updateTexture)
end


local function CreateWhiteBar(name, parent, x, y, width, height)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize

    local frame = CreateFrame("Frame", addonName .. name, parent)
    frame:SetFrameLevel(parent:GetFrameLevel() + 1)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * node_size, y * node_size - padSize)
    frame:SetSize(width * node_size, height * node_size - 2 * padSize)
    frame:Show()

    local tex = frame:CreateTexture(nil, "BACKGROUND")
    tex:SetAllPoints(frame)
    tex:SetColorTexture(0, 0, 0, 1)


    local bar = CreateFrame("StatusBar", nil, frame)
    bar:SetAllPoints(frame)
    bar:SetStatusBarTexture("Interface\\Buttons\\WHITE8X8")
    bar:SetStatusBarColor(1, 1, 1, 1)
    bar:SetMinMaxValues(0, 100)
    bar:SetValue(50)
    return bar
end

local function InitializeConfigFrame()
    local si_node = CreateMiscNode(1, 0, addonName .. "ConfigFrame", addonTable.ConfigFrame)
    local enable_node = CreateMiscNode(3, 0, addonName .. "ConfigFrame", addonTable.ConfigFrame)
    SLASH_SI1 = "/si"
    SlashCmdList["SI"] = function(msg)
        local spellID = tonumber(msg)
        if not spellID then
            logging("Invalid spellID")
            return
        end
        local iconID, originalIconID = C_Spell.GetSpellTexture(spellID)
        if not iconID then
            logging("Invalid spellID")
            return
        end
        si_node:SetTexture(iconID)
        local spellLink = C_Spell.GetSpellLink(spellID)
        logging(spellLink)
        C_Timer.After(10, function()
            logging("SI reset")
            si_node:SetColorTexture(0, 0, 0, 1)
        end)
    end
end
table.insert(FrameInitFuncs, InitializeConfigFrame)

local function InitializeAuraFrame()
    logging("InitializeAuraFrame")
    CreateAuraSequence("player", "HELPFUL", 24, "PlayerBuff", addonTable.PlayerBuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("target", "HARMFUL|PLAYER", 7, "TargetDebuff", addonTable.TargetDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("player", "HARMFUL", 7, "PlayerDebuff", addonTable.PlayerDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    logging("AuraFrame created")
end
table.insert(FrameInitFuncs, InitializeAuraFrame)


local function InitializePlayerBarFrame()
    logging("InitializePlayerBarFrame")

    local PlayerHealthBar = CreateWhiteBar("PlayerHealthBar", addonTable.PlayerBarFrame, 0, 0, 10, 1)
    local PlayerPowerBar = CreateWhiteBar("PlayerPowerBar", addonTable.PlayerBarFrame, 0, -1, 10, 1)
    local PlayerDamageAbsorbsBar = CreateWhiteBar("PlayerDamageAbsorbsBar", addonTable.PlayerBarFrame, 0, -2, 10, 1)
    local PlayerHealAbsorbsBar = CreateWhiteBar("PlayerHealAbsorbsBar", addonTable.PlayerBarFrame, 0, -3, 10, 1)


    local function UpdatePlayerBar()
        local health = UnitHealth("player")
        local maxHealth = UnitHealthMax("player")
        PlayerHealthBar:SetMinMaxValues(0, maxHealth)
        PlayerHealthBar:SetValue(health)

        local power = UnitPower("player")
        local maxPower = UnitPowerMax("player")
        PlayerPowerBar:SetMinMaxValues(0, maxPower)
        PlayerPowerBar:SetValue(power)

        PlayerDamageAbsorbsBar:SetMinMaxValues(0, maxHealth)
        PlayerDamageAbsorbsBar:SetValue(UnitGetTotalAbsorbs("player"))

        PlayerHealAbsorbsBar:SetMinMaxValues(0, maxHealth)
        PlayerHealAbsorbsBar:SetValue(UnitGetTotalHealAbsorbs("player"))
    end

    table.insert(UpdateFuncs, UpdatePlayerBar)

    logging("PlayerBarFrame created")
end

table.insert(FrameInitFuncs, InitializePlayerBarFrame)







local function InitializeSpellCDFrame()
    logging("InitializeSpellCDFrame")
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local MaxFrame = math.min(23, #addonTable.SpellCD)
    local iconTextrues = {}
    local cooldownTextrues = {}

    for i = 1, 23 do
        local iconTexture = CreateMiscNode(i - 1, 0, "SpellCDIconFrame" .. i, addonTable.PlayerSpellCDFrame)
        table.insert(iconTextrues, iconTexture)

        local cooldownTexture = CreateMiscNode(i - 1, 1, "SpellCDCooldownFrame" .. i, addonTable.PlayerSpellCDFrame)
        table.insert(cooldownTextrues, cooldownTexture)
    end

    for i = 1, MaxFrame do
        local SpellID = addonTable.SpellCD[i]
        local iconID, _ = C_Spell.GetSpellTexture(SpellID)
        iconTextrues[i]:SetTexture(iconID)
    end


    local function UpdateNodeTexture()
        for i = 1, MaxFrame do
            local SpellID = addonTable.SpellCD[i]
            local duration = C_Spell.GetSpellCooldownDuration(SpellID)
            local result = duration:EvaluateRemainingPercent(curve_reverse)
            cooldownTextrues[i]:SetColorTexture(result.r, result.g, result.b, 1)
        end
    end
    table.insert(UpdateFuncs, UpdateNodeTexture)
    logging("PlayerSpellCDFrame created")
end
table.insert(FrameInitFuncs, InitializeSpellCDFrame)



local function InitializeSpellChargeFrame()
    logging("InitializeSpellChargeFrame")
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local MaxFrame = math.min(5, #addonTable.SpellCharge)
    local iconTextrues = {}
    local chargeTextrues = {}

    for i = 1, 5 do
        local iconFrame = CreateFrame("Frame", addonName .. "SpellChargeIconFrame" .. i, addonTable.PlayerSpellChargeFrame)
        iconFrame:SetPoint("TOPLEFT", addonTable.PlayerSpellChargeFrame, "TOPLEFT", (i - 1) * node_size + padSize, 0 - padSize)
        iconFrame:SetFrameLevel(addonTable.PlayerSpellChargeFrame:GetFrameLevel() + 1)
        iconFrame:SetSize(innerSize, innerSize)
        iconFrame:Show()

        local iconTexture = iconFrame:CreateTexture(nil, "BACKGROUND")
        iconTexture:SetAllPoints(iconFrame)
        iconTexture:SetColorTexture(0, 0, 0, 1)
        iconTexture:Show()
        table.insert(iconTextrues, iconTexture)

        local chargeFrame = CreateFrame("Frame", addonName .. "SpellChargeFrame" .. i, addonTable.PlayerSpellChargeFrame)
        chargeFrame:SetPoint("TOPLEFT", addonTable.PlayerSpellChargeFrame, "TOPLEFT", (i - 1) * node_size + padSize, -1 * node_size - padSize)
        chargeFrame:SetFrameLevel(addonTable.PlayerSpellChargeFrame:GetFrameLevel() + 1)
        chargeFrame:SetSize(innerSize, innerSize)
        chargeFrame:Show()

        local chargeFrameTexture = chargeFrame:CreateTexture(nil, "BACKGROUND")
        chargeFrameTexture:SetAllPoints(chargeFrame)
        chargeFrameTexture:SetColorTexture(0, 0, 0, 1)
        chargeFrameTexture:Show()
        table.insert(chargeTextrues, chargeFrameTexture)
    end


    for i = 1, MaxFrame do
        local SpellID = addonTable.SpellCharge[i]
        local iconID, _ = C_Spell.GetSpellTexture(SpellID)
        iconTextrues[i]:SetTexture(iconID)
    end


    local function UpdateNodeTexture()
        for i = 1, MaxFrame do
            local SpellID = addonTable.SpellCharge[i]
            local duration = C_Spell.GetSpellChargeDuration(SpellID)
            local result = duration:EvaluateRemainingPercent(curve_reverse)
            chargeTextrues[i]:SetColorTexture(result.r, result.g, result.b, 1)
        end
    end
    table.insert(UpdateFuncs, UpdateNodeTexture)

    logging("PlayerChargeCDFrame created")
end
table.insert(FrameInitFuncs, InitializeSpellChargeFrame)



local function InitializePartyFrame()
    logging("InitializePartyFrame")
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)
        local parent_frame = addonTable["PartyFrame" .. UnitKey]
        local frame_pre = addonName .. "PartyFrame" .. UnitKey
        local status_frame = CreateFrame("Frame", frame_pre .. "StatusFrame", parent_frame)
        status_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        status_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 10 * node_size, -4 * node_size)
        status_frame:SetSize(node_size * 2, node_size * 3)
        status_frame:Show()

        local debuff_frame = CreateFrame("Frame", frame_pre .. "DebuffFrame", parent_frame)
        debuff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        debuff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, -2 * node_size)
        debuff_frame:SetSize(node_size * 14, node_size * 2)
        debuff_frame:Show()

        local buff_frame = CreateFrame("Frame", frame_pre .. "BuffFrame", parent_frame)
        buff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        buff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, 0)
        buff_frame:SetSize(node_size * 16, node_size * 2)
        buff_frame:Show()


        local bar_frame = CreateFrame("Frame", frame_pre .. "BarFrame", parent_frame)
        bar_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        bar_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, -4 * node_size)
        bar_frame:SetSize(node_size * 10, node_size * 3)
        bar_frame:Show()


        local exist_frame = CreateFrame("Frame", frame_pre .. "ExistFrame", status_frame)
        exist_frame:SetPoint("TOPLEFT", status_frame, "TOPLEFT", 0 + padSize, 0 - padSize)
        exist_frame:SetFrameLevel(status_frame:GetFrameLevel() + 1)
        exist_frame:SetSize(innerSize, innerSize)
        exist_frame:Show()

        local exist_texture = exist_frame:CreateTexture(nil, "BACKGROUND")
        exist_texture:SetAllPoints(exist_frame)
        exist_texture:SetColorTexture(0, 1, 0, 1)
        exist_texture:Show()

        local inRange_frame = CreateFrame("Frame", frame_pre .. "InRangeFrame", status_frame)
        inRange_frame:SetPoint("TOPLEFT", status_frame, "TOPLEFT", node_size + padSize, 0 - padSize)
        inRange_frame:SetFrameLevel(status_frame:GetFrameLevel() + 1)
        inRange_frame:SetSize(innerSize, innerSize)
        inRange_frame:Show()

        local inRange_texture = inRange_frame:CreateTexture(nil, "BACKGROUND")
        inRange_texture:SetAllPoints(inRange_frame)
        inRange_texture:SetColorTexture(1, 0, 0, 1)
        inRange_texture:Show()

        local class_frame = CreateFrame("Frame", frame_pre .. "ClassFrame", status_frame)
        class_frame:SetPoint("TOPLEFT", status_frame, "TOPLEFT", 0 + padSize, -1 * node_size - padSize)
        class_frame:SetFrameLevel(status_frame:GetFrameLevel() + 1)
        class_frame:SetSize(innerSize, innerSize)
        class_frame:Show()

        local class_texture = class_frame:CreateTexture(nil, "BACKGROUND")
        class_texture:SetAllPoints(class_frame)
        class_texture:SetColorTexture(0, 0, 1, 1)
        class_texture:Show()

        local role_frame = CreateFrame("Frame", frame_pre .. "RoleFrame", status_frame)
        role_frame:SetPoint("TOPLEFT", status_frame, "TOPLEFT", node_size + padSize, -1 * node_size - padSize)
        role_frame:SetFrameLevel(status_frame:GetFrameLevel() + 1)
        role_frame:SetSize(innerSize, innerSize)
        role_frame:Show()

        local role_texture = role_frame:CreateTexture(nil, "BACKGROUND")
        role_texture:SetAllPoints(role_frame)
        role_texture:SetColorTexture(1, 1, 1, 1)
        role_texture:Show()


        CreateAuraSequence(UnitKey, "HARMFUL", 6, UnitKey .. "Debuff", debuff_frame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
        CreateAuraSequence(UnitKey, "HELPFUL|PLAYER", 6, UnitKey .. "Buff", buff_frame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)

        local HealthBar = CreateWhiteBar(UnitKey .. "HealthBar", bar_frame, 0, 0, 10, 1)
        local DamageAbsorbsBar = CreateWhiteBar(UnitKey .. "DamageAbsorbsBar", bar_frame, 0, -1, 10, 1)
        local HealAbsorbsBar = CreateWhiteBar(UnitKey .. "HealAbsorbsBar", bar_frame, 0, -2, 10, 1)


        function UpdateUnitrame()
            if UnitExists(UnitKey) then
                -- 检查是否存在
                exist_texture:SetColorTexture(1, 1, 1, 1)
                -- 检查范围
                local _, maxRange = LibRangeCheck:GetRange(UnitKey)
                if maxRange and (maxRange <= addonTable.RangeCheck) then
                    inRange_texture:SetColorTexture(1, 1, 1, 1)
                else
                    inRange_texture:SetColorTexture(0, 0, 0, 1)
                end
                -- 检查职业
                local _, classFilename, _ = UnitClass(UnitKey)
                local CLASS_COLOR = C_ClassColor.GetClassColor(classFilename)
                class_texture:SetColorTexture(CLASS_COLOR.r, CLASS_COLOR.g, CLASS_COLOR.b, 1)
                -- 检查角色
                local role = UnitGroupRolesAssigned(UnitKey)
                role_texture:SetColorTexture(roleColor[role].r, roleColor[role].g, roleColor[role].b, 1)

                local health = UnitHealth(UnitKey)
                local maxHealth = UnitHealthMax(UnitKey)
                HealthBar:SetMinMaxValues(0, maxHealth)
                HealthBar:SetValue(health)

                DamageAbsorbsBar:SetMinMaxValues(0, maxHealth)
                DamageAbsorbsBar:SetValue(UnitGetTotalAbsorbs(UnitKey))

                HealAbsorbsBar:SetMinMaxValues(0, maxHealth)
                HealAbsorbsBar:SetValue(UnitGetTotalHealAbsorbs(UnitKey))
            else
                exist_texture:SetColorTexture(0, 0, 0, 1)
                inRange_texture:SetColorTexture(0, 0, 0, 1)
                class_texture:SetColorTexture(0, 0, 0, 1)
                role_texture:SetColorTexture(0, 0, 0, 1)
                HealthBar:SetValue(0)
                DamageAbsorbsBar:SetValue(0)
                HealAbsorbsBar:SetValue(0)
            end
        end

        table.insert(UpdateFuncs, UpdateUnitrame)
    end
    logging("PartyFrame created")
end

table.insert(FrameInitFuncs, InitializePartyFrame)



local function InitializePlayerStatusFrame()
    local x = 0
    local y = 0
    local player_in_combat = CreateMiscNode(x, y, "PlayerInCombat", addonTable.PlayerStatusFrame)
    x = 1
    local player_is_moving = CreateMiscNode(x, y, "PlayerIsMoving", addonTable.PlayerStatusFrame)
    x = 2
    local player_in_vehicle = CreateMiscNode(x, y, "PlayerInVehicle", addonTable.PlayerStatusFrame)
    x = 3
    local player_is_empowered = CreateMiscNode(x, y, "PlayerIsEmpowered", addonTable.PlayerStatusFrame)
    x = 5
    local player_cast_icon = CreateMiscNode(x, y, "PlayerCastIcon", addonTable.PlayerStatusFrame)
    x = 6
    local player_cast_duration = CreateMiscNode(x, y, "PlayerCastDuration", addonTable.PlayerStatusFrame)
    x = 7
    local player_channel_icon = CreateMiscNode(x, y, "PlayerChannelIcon", addonTable.PlayerStatusFrame)
    x = 8
    local player_channel_duration = CreateMiscNode(x, y, "PlayerChannelDuration", addonTable.PlayerStatusFrame)



    local function UpdateStatus()
        if UnitAffectingCombat("player") then
            player_in_combat:SetColorTexture(1, 1, 1, 1)
        else
            player_in_combat:SetColorTexture(0, 0, 0, 1)
        end

        if GetUnitSpeed("player") > 0 then
            player_is_moving:SetColorTexture(1, 1, 1, 1)
        else
            player_is_moving:SetColorTexture(0, 0, 0, 1)
        end

        if UnitInVehicle("player") or IsMounted() then
            player_in_vehicle:SetColorTexture(1, 1, 1, 1)
        else
            player_in_vehicle:SetColorTexture(0, 0, 0, 1)
        end

        local _, _, CastTextureID, _, _, _, _, _, _, _ = UnitCastingInfo("player")
        if CastTextureID then
            player_cast_icon:SetTexture(CastTextureID)
            local duration = UnitCastingDuration("player")
            local result = duration:EvaluateElapsedPercent(curve_reverse)
            player_cast_duration:SetColorTexture(result.r, result.g, result.b, 1)
        else
            player_cast_icon:SetColorTexture(0, 0, 0, 1)
            player_cast_duration:SetColorTexture(0, 0, 0, 1)
        end


        local _, _, channelTextureID, _, _, _, _, _, isEmpowered, _, _ = UnitChannelInfo("player")
        if isEmpowered then
            player_is_empowered:SetColorTexture(1, 1, 1, 1)
        else
            player_is_empowered:SetColorTexture(0, 0, 0, 1)
        end

        if channelTextureID then
            player_channel_icon:SetTexture(channelTextureID)
            local duration = UnitChannelDuration("player")
            local result = duration:EvaluateElapsedPercent(curve_reverse)
            player_channel_duration:SetColorTexture(result.r, result.g, result.b, 1)
        else
            player_channel_icon:SetColorTexture(0, 0, 0, 1)
            player_channel_duration:SetColorTexture(0, 0, 0, 1)
        end
    end
    table.insert(UpdateFuncs, UpdateStatus)
end
table.insert(FrameInitFuncs, InitializePlayerStatusFrame)


local function InitializeTargetStatusFrame()
    local x = 0
    local y = 0
    local health_bar = CreateWhiteBar("TargetHealthBar", addonTable.TargetStatusFrame, 0, 0, 10, 1)
    y = 1
    local target_exist = CreateMiscNode(x, y, "TargetExist", addonTable.TargetStatusFrame)
    x = 1
    local target_can_attack = CreateMiscNode(x, y, "TargetCanAttack", addonTable.TargetStatusFrame)
    x = 2
    local target_is_self = CreateMiscNode(x, y, "TargetIsSelf", addonTable.TargetStatusFrame)
    x = 3
    local target_is_alive = CreateMiscNode(x, y, "TargetIsAlive", addonTable.TargetStatusFrame)
    x = 4
    local target_in_combat = CreateMiscNode(x, y, "TargetInCombat", addonTable.TargetStatusFrame)
    x = 5
    local target_in_range = CreateMiscNode(x, y, "TargetInRange", addonTable.TargetStatusFrame)
    y = 2
    x = 0
    local target_cast_icon = CreateMiscNode(x, y, "TargetCastIcon", addonTable.TargetStatusFrame)
    x = 1
    local target_cast_duration = CreateMiscNode(x, y, "TargetCastDuration", addonTable.TargetStatusFrame)
    x = 2
    local target_cast_interruptible = CreateMiscNode(x, y, "TargetCastInterruptible", addonTable.TargetStatusFrame)
    x = 3
    local target_channel_icon = CreateMiscNode(x, y, "TargetChannelIcon", addonTable.TargetStatusFrame)
    x = 4
    local target_channel_duration = CreateMiscNode(x, y, "TargetChannelDuration", addonTable.TargetStatusFrame)
    x = 5
    local target_channel_interruptible = CreateMiscNode(x, y, "TargetChannelInterruptible", addonTable.TargetStatusFrame)

    local function UpdateStatus()
        if UnitExists("target") then
            target_exist:SetColorTexture(1, 1, 1, 1)

            local health = UnitHealth("target")
            local maxHealth = UnitHealthMax("target")
            health_bar:SetMinMaxValues(0, maxHealth)
            health_bar:SetValue(health)

            if UnitCanAttack("player", "target") then
                target_can_attack:SetColorTexture(1, 1, 1, 1)
            else
                target_can_attack:SetColorTexture(0, 0, 0, 1)
            end

            if UnitIsUnit("player", "target") then
                target_is_self:SetColorTexture(1, 1, 1, 1)
            else
                target_is_self:SetColorTexture(0, 0, 0, 1)
            end

            if UnitAffectingCombat("target") then
                target_in_combat:SetColorTexture(1, 1, 1, 1)
            else
                target_in_combat:SetColorTexture(0, 0, 0, 1)
            end

            if UnitIsDeadOrGhost("target") then
                target_is_alive:SetColorTexture(0, 0, 0, 1)
            else
                target_is_alive:SetColorTexture(1, 1, 1, 1)
            end

            local _, maxRange = LibRangeCheck:GetRange("target")
            if maxRange and (maxRange <= addonTable.RangeCheck) then
                target_in_range:SetColorTexture(1, 1, 1, 1)
            else
                target_in_range:SetColorTexture(0, 0, 0, 1)
            end

            local _, _, CastTextureID, _, _, _, _, CastNotInterruptible, _, _ = UnitCastingInfo("target")
            if CastTextureID then
                target_cast_icon:SetTexture(CastTextureID)
                target_cast_interruptible:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(CastNotInterruptible, { r = 0, g = 0, b = 0, a = 1 }, { r = 1, g = 1, b = 1, a = 1 }):GetRGBA())
                local duration = UnitCastingDuration("target")
                local result = duration:EvaluateElapsedPercent(curve_reverse)
                target_cast_duration:SetColorTexture(result.r, result.g, result.b, 1)
            else
                target_cast_icon:SetColorTexture(0, 0, 0, 1)
                target_cast_duration:SetColorTexture(0, 0, 0, 1)
                target_cast_interruptible:SetColorTexture(0, 0, 0, 1)
            end
            local _, _, textureID, _, _, _, ChannelNotInterruptible = UnitChannelInfo("target")
            if textureID then
                target_channel_icon:SetTexture(textureID)
                target_channel_interruptible:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(ChannelNotInterruptible, { r = 0, g = 0, b = 0, a = 1 }, { r = 1, g = 1, b = 1, a = 1 }):GetRGBA())
                local duration = UnitChannelDuration("target")
                local result = duration:EvaluateElapsedPercent(curve_reverse)
                target_channel_duration:SetColorTexture(result.r, result.g, result.b, 1)
            else
                target_channel_icon:SetColorTexture(0, 0, 0, 1)
                target_channel_duration:SetColorTexture(0, 0, 0, 1)
                target_channel_interruptible:SetColorTexture(0, 0, 0, 1)
            end
        else
            target_exist:SetColorTexture(0, 0, 0, 1)
            health_bar:SetValue(0)
            target_can_attack:SetColorTexture(0, 0, 0, 1)
            target_is_self:SetColorTexture(0, 0, 0, 1)
            target_in_combat:SetColorTexture(0, 0, 0, 1)
            target_in_range:SetColorTexture(0, 0, 0, 1)
            target_is_alive:SetColorTexture(0, 0, 0, 1)
            target_cast_icon:SetColorTexture(0, 0, 0, 1)
            target_cast_duration:SetColorTexture(0, 0, 0, 1)
            target_cast_interruptible:SetColorTexture(0, 0, 0, 1)
            target_channel_icon:SetColorTexture(0, 0, 0, 1)
            target_channel_duration:SetColorTexture(0, 0, 0, 1)
            target_channel_interruptible:SetColorTexture(0, 0, 0, 1)
        end
    end

    table.insert(UpdateFuncs, UpdateStatus)
end
table.insert(FrameInitFuncs, InitializeTargetStatusFrame)



local function InitializeMiscFrame()
    return
end
table.insert(FrameInitFuncs, InitializeMiscFrame)















-- 设置游戏变量，确保插件正常运行
SetCVar("secretChallengeModeRestrictionsForced", 1)
SetCVar("secretCombatRestrictionsForced", 1)
SetCVar("secretEncounterRestrictionsForced", 1)
SetCVar("secretMapRestrictionsForced", 1)
SetCVar("secretPvPMatchRestrictionsForced", 1)
SetCVar("secretAuraDataRestrictionsForced", 1)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
