local addonName, addonTable     = ...
local LibRangeCheck             = LibStub:GetLibrary("LibRangeCheck-3.0", true)

local DEBUG                     = true
local scale                     = 3
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
    addonTable.MainFrame:SetSize(node_size * 68, node_size * 16)
    addonTable.MainFrame:SetFrameStrata("TOOLTIP")
    addonTable.MainFrame:SetFrameLevel(900)
    addonTable.MainFrame:Show()

    addonTable.MainFrameTexture = addonTable.MainFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MainFrameTexture:SetAllPoints()
    addonTable.MainFrameTexture:SetColorTexture(0, 0, 0, 1)
    addonTable.MainFrameTexture:Show()


    addonTable.PlayerBarFrame = CreateFrame("Frame", addonName .. "PlayerBarFrame", addonTable.MainFrame)
    addonTable.PlayerBarFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerBarFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -2 * node_size)
    addonTable.PlayerBarFrame:SetSize(10 * node_size, 4 * node_size)

    if DEBUG then
        addonTable.PlayerBarFrameTexture = addonTable.PlayerBarFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerBarFrameTexture:SetAllPoints()
        addonTable.PlayerBarFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerBarFrameTexture:Show()
    end

    addonTable.PlayerBuffFrame = CreateFrame("Frame", addonName .. "PlayerBuffFrame", addonTable.MainFrame)
    addonTable.PlayerBuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerBuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 12 * node_size, -2 * node_size)
    addonTable.PlayerBuffFrame:SetSize(54 * node_size, 2 * node_size)
    addonTable.PlayerBuffFrame:Show()

    if DEBUG then
        addonTable.PlayerBuffFrameTexture = addonTable.PlayerBuffFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerBuffFrameTexture:SetAllPoints()
        addonTable.PlayerBuffFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerBuffFrameTexture:Show()
    end

    addonTable.PlayerDebuffFrame = CreateFrame("Frame", addonName .. "PlayerDebuffFrame", addonTable.MainFrame)
    addonTable.PlayerDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 12 * node_size, -4 * node_size)
    addonTable.PlayerDebuffFrame:SetSize(28 * node_size, 2 * node_size)
    addonTable.PlayerDebuffFrame:Show()

    if DEBUG then
        addonTable.PlayerDebuffFrameTexture = addonTable.PlayerDebuffFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerDebuffFrameTexture:SetAllPoints()
        addonTable.PlayerDebuffFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerDebuffFrameTexture:Show()
    end

    addonTable.TargetDebuffFrame = CreateFrame("Frame", addonName .. "TargetDebuffFrame", addonTable.MainFrame)
    addonTable.TargetDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.TargetDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 40 * node_size, -4 * node_size)
    addonTable.TargetDebuffFrame:SetSize(26 * node_size, 2 * node_size)
    addonTable.TargetDebuffFrame:Show()

    if DEBUG then
        addonTable.TargetDebuffFrameTexture = addonTable.TargetDebuffFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.TargetDebuffFrameTexture:SetAllPoints()
        addonTable.TargetDebuffFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.TargetDebuffFrameTexture:Show()
    end


    addonTable.PlayerSpellCDFrame = CreateFrame("Frame", addonName .. "PlayerSpellCDFrame", addonTable.MainFrame)
    addonTable.PlayerSpellCDFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerSpellCDFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -6 * node_size)
    addonTable.PlayerSpellCDFrame:SetSize(24 * node_size, 2 * node_size)
    addonTable.PlayerSpellCDFrame:Show()

    if DEBUG then
        addonTable.PlayerSpellCDFrameTexture = addonTable.PlayerSpellCDFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerSpellCDFrameTexture:SetAllPoints()
        addonTable.PlayerSpellCDFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerSpellCDFrameTexture:Show()
    end

    addonTable.PlayerSpellChargeFrame = CreateFrame("Frame", addonName .. "PlayerSpellChargeFrame", addonTable.MainFrame)
    addonTable.PlayerSpellChargeFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerSpellChargeFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 26 * node_size, -6 * node_size)
    addonTable.PlayerSpellChargeFrame:SetSize(6 * node_size, 2 * node_size)
    addonTable.PlayerSpellChargeFrame:Show()
    if DEBUG then
        addonTable.PlayerChargeFrameTexture = addonTable.PlayerSpellChargeFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerChargeFrameTexture:SetAllPoints()
        addonTable.PlayerChargeFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerChargeFrameTexture:Show()
    end

    addonTable.MiscFrame = CreateFrame("Frame", addonName .. "MiscFrame", addonTable.MainFrame)
    addonTable.MiscFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.MiscFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 32 * node_size, -6 * node_size)
    addonTable.MiscFrame:SetSize(node_size * 25, node_size * 2)
    addonTable.MiscFrame:Show()

    if DEBUG then
        addonTable.MiscFrameTexture = addonTable.MiscFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.MiscFrameTexture:SetAllPoints()
        addonTable.MiscFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.MiscFrameTexture:Show()
    end

    addonTable.SpecFrame = CreateFrame("Frame", addonName .. "SpecFrame", addonTable.MainFrame)
    addonTable.SpecFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.SpecFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 57 * node_size, -6 * node_size)
    addonTable.SpecFrame:SetSize(node_size * 9, node_size * 2)
    addonTable.SpecFrame:Show()

    if DEBUG then
        addonTable.SpecFrameTexture = addonTable.SpecFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.SpecFrameTexture:SetAllPoints()
        addonTable.SpecFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.SpecFrameTexture:Show()
    end
    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)

        addonTable["PartyFrame" .. UnitKey] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey, addonTable.MainFrame)
        addonTable["PartyFrame" .. UnitKey]:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey]:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", (16 * i - 14) * node_size, -8 * node_size)
        addonTable["PartyFrame" .. UnitKey]:SetSize(node_size * 16, node_size * 6)
        addonTable["PartyFrame" .. UnitKey]:Show()

        if DEBUG then
            addonTable["PartyFrame" .. UnitKey .. "Texture"] = addonTable["PartyFrame" .. UnitKey]:CreateTexture(nil, "BACKGROUND")
            addonTable["PartyFrame" .. UnitKey .. "Texture"]:SetAllPoints()
            addonTable["PartyFrame" .. UnitKey .. "Texture"]:SetColorTexture(math.random(), math.random(), math.random(), 1)
            addonTable["PartyFrame" .. UnitKey .. "Texture"]:Show()
        end
    end

    logging("MainFrame created")
end

table.insert(FrameInitFuncs, InitializeMainFrame)

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
        local icon_frame = CreateFrame("Frame", addonName .. name_prefix .. "IconFrame" .. i, parent)
        icon_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (2 * i - 2) * node_size + padSize, 0 - padSize)
        icon_frame:SetFrameLevel(parent:GetFrameLevel() + 2)
        icon_frame:SetSize(innerSize, innerSize)
        icon_frame:Show()

        local icon_texture = icon_frame:CreateTexture(nil, "BACKGROUND")
        icon_texture:SetAllPoints(icon_frame)
        icon_texture:SetColorTexture(0, 0, 0, 1)
        icon_texture:Show()
        table.insert(iconTextures, icon_texture)

        local duration_frame = CreateFrame("Frame", addonName .. name_prefix .. "DurationFrame" .. i, parent)
        duration_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (2 * i - 2) * node_size + padSize, -node_size - padSize)
        duration_frame:SetFrameLevel(parent:GetFrameLevel() + 2)
        duration_frame:SetSize(innerSize, innerSize)
        duration_frame:Show()

        local duration_texture = duration_frame:CreateTexture(nil, "BACKGROUND")
        duration_texture:SetAllPoints(duration_frame)
        duration_texture:SetColorTexture(0, 0, 0, 1)
        duration_texture:Show()
        table.insert(durationTextures, duration_texture)

        local dispel_frame = CreateFrame("Frame", addonName .. name_prefix .. "DispelFrame" .. i, parent)
        dispel_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (2 * i - 1) * node_size + padSize, 0 - padSize)
        dispel_frame:SetFrameLevel(parent:GetFrameLevel() + 2)
        dispel_frame:SetSize(innerSize, innerSize)
        dispel_frame:Show()

        local dispel_texture = dispel_frame:CreateTexture(nil, "BACKGROUND")
        dispel_texture:SetAllPoints(dispel_frame)
        dispel_texture:SetColorTexture(0, 0, 0, 1)
        dispel_texture:Show()
        table.insert(dispelTextures, dispel_texture)

        local count_frame = CreateFrame("Frame", addonName .. name_prefix .. "CountFrame" .. i, parent)
        count_frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (2 * i - 1) * node_size + padSize, -node_size - padSize)
        count_frame:SetFrameLevel(parent:GetFrameLevel() + 2)
        count_frame:SetSize(innerSize, innerSize)
        count_frame:Show()

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
local function InitializeAuraFrame()
    CreateAuraSequence("player", "HELPFUL|PLAYER", 27, "PlayerBuff", addonTable.PlayerBuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("target", "HARMFUL|PLAYER", 13, "TargetDebuff", addonTable.TargetDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("player", "HARMFUL", 14, "PlayerDebuff", addonTable.PlayerDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
end
table.insert(FrameInitFuncs, InitializeAuraFrame)


local function InitializeSpellCDFrame()
    logging("InitializeSpellCDFrame")
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local MaxFrame = math.min(24, #addonTable.SpellCD)
    local iconTextrues = {}
    local cooldownTextrues = {}

    for i = 1, 24 do
        local iconFrame = CreateFrame("Frame", addonName .. "SpellCDIconFrame" .. i, addonTable.PlayerSpellCDFrame)
        iconFrame:SetPoint("TOPLEFT", addonTable.PlayerSpellCDFrame, "TOPLEFT", (i - 1) * node_size + padSize, 0 - padSize)
        iconFrame:SetFrameLevel(addonTable.PlayerSpellCDFrame:GetFrameLevel() + 1)
        iconFrame:SetSize(innerSize, innerSize)
        iconFrame:Show()

        local iconTexture = iconFrame:CreateTexture(nil, "BACKGROUND")
        iconTexture:SetAllPoints(iconFrame)
        iconTexture:SetColorTexture(0, 0, 0, 1)
        iconTexture:Show()
        table.insert(iconTextrues, iconTexture)

        local cooldownFrame = CreateFrame("Frame", addonName .. "SpellCDFrame" .. i, addonTable.PlayerSpellCDFrame)
        cooldownFrame:SetPoint("TOPLEFT", addonTable.PlayerSpellCDFrame, "TOPLEFT", (i - 1) * node_size + padSize, -1 * node_size - padSize)
        cooldownFrame:SetFrameLevel(addonTable.PlayerSpellCDFrame:GetFrameLevel() + 1)
        cooldownFrame:SetSize(innerSize, innerSize)
        cooldownFrame:Show()

        local cooldownFrameTexture = cooldownFrame:CreateTexture(nil, "BACKGROUND")
        cooldownFrameTexture:SetAllPoints(cooldownFrame)
        cooldownFrameTexture:SetColorTexture(0, 0, 0, 1)
        cooldownFrameTexture:Show()
        table.insert(cooldownTextrues, cooldownFrameTexture)
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
    local MaxFrame = math.min(6, #addonTable.SpellCharge)
    local iconTextrues = {}
    local chargeTextrues = {}

    for i = 1, 6 do
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
        status_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, 0)
        status_frame:SetSize(node_size * 2, node_size * 2)
        status_frame:Show()

        local debuff_frame = CreateFrame("Frame", frame_pre .. "DebuffFrame", parent_frame)
        debuff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        debuff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 2 * node_size, 0 * node_size)
        debuff_frame:SetSize(node_size * 14, node_size * 2)
        debuff_frame:Show()

        local buff_frame = CreateFrame("Frame", frame_pre .. "BuffFrame", parent_frame)
        buff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        buff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, -2 * node_size)
        buff_frame:SetSize(node_size * 16, node_size * 2)
        buff_frame:Show()


        local bar_frame = CreateFrame("Frame", frame_pre .. "BarFrame", parent_frame)
        bar_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        bar_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, -4 * node_size)
        bar_frame:SetSize(node_size * 16, node_size * 2)
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


        CreateAuraSequence(UnitKey, "HARMFUL|PLAYER", 7, UnitKey .. "Debuff", debuff_frame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
        CreateAuraSequence(UnitKey, "HELPFUL|PLAYER", 8, UnitKey .. "Buff", buff_frame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)

        local HealthBar = CreateWhiteBar(UnitKey .. "HealthBar", bar_frame, 0, 0, 8, 1)
        local PowerBar = CreateWhiteBar(UnitKey .. "PowerBar", bar_frame, 0, -1, 8, 1)
        local DamageAbsorbsBar = CreateWhiteBar(UnitKey .. "DamageAbsorbsBar", bar_frame, 8, 0, 8, 1)
        local HealAbsorbsBar = CreateWhiteBar(UnitKey .. "HealAbsorbsBar", bar_frame, 8, -1, 8, 1)


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

                local power = UnitPower(UnitKey)
                local maxPower = UnitPowerMax(UnitKey)
                PowerBar:SetMinMaxValues(0, maxPower)
                PowerBar:SetValue(power)

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
                PowerBar:SetValue(0)
                DamageAbsorbsBar:SetValue(0)
                HealAbsorbsBar:SetValue(0)
            end
        end

        table.insert(UpdateFuncs, UpdateUnitrame)
    end
    logging("PartyFrame created")
end

table.insert(FrameInitFuncs, InitializePartyFrame)

local function CreateMiscNode(x, y, title)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local nodeFrame = CreateFrame("Frame", addonName .. "Misc" .. title, addonTable.MiscFrame)
    nodeFrame:SetPoint("TOPLEFT", addonTable.MiscFrame, "TOPLEFT", x * node_size + padSize, -y * node_size - padSize)
    nodeFrame:SetFrameLevel(addonTable.MiscFrame:GetFrameLevel() + 1)
    nodeFrame:SetSize(innerSize, innerSize)
    nodeFrame:Show()
    local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
    nodeTexture:SetAllPoints(nodeFrame)
    nodeTexture:SetColorTexture(0, 0, 0, 1)
    nodeTexture:Show()
    return nodeTexture
end


local function InitializeMiscFrame()
    local x = 0
    local y = 0
    local player_in_combat = CreateMiscNode(x, y, "PlayerInCombat")
    x = 1
    local player_is_moving = CreateMiscNode(x, y, "PlayerIsMoving")
    x = 2
    local target_exist = CreateMiscNode(x, y, "TargetExist")
    x = 3
    local target_can_attack = CreateMiscNode(x, y, "TargetCanAttack")
    x = 4
    local target_is_self = CreateMiscNode(x, y, "TargetIsSelf")
    y = 1
    x = 0

    local player_is_empowered = CreateMiscNode(x, y, "PlayerIsEmpowered")
    x = 1
    local player_in_vehicle = CreateMiscNode(x, y, "PlayerInVehicle")
    x = 2
    local target_is_alive = CreateMiscNode(x, y, "TargetIsAlive")
    x = 3
    local target_in_combat = CreateMiscNode(x, y, "TargetInCombat")
    x = 4
    local target_in_range = CreateMiscNode(x, y, "TargetInRange")

    y = 0
    x = 5
    local target_cast_icon = CreateMiscNode(x, y, "TargetCastIcon")
    x = 6
    local target_cast_duration = CreateMiscNode(x, y, "TargetCastDuration")
    x = 7
    local target_cast_interruptible = CreateMiscNode(x, y, "TargetCastInterruptible")
    y = 1
    x = 5
    local target_channel_icon = CreateMiscNode(x, y, "TargetChannelIcon")
    x = 6
    local target_channel_duration = CreateMiscNode(x, y, "TargetChannelDuration")
    x = 7
    local target_channel_interruptible = CreateMiscNode(x, y, "TargetChannelInterruptible")



    function UpdateNode1()
        if UnitAffectingCombat("player") then
            player_in_combat:SetColorTexture(1, 1, 1, 1)
        else
            player_in_combat:SetColorTexture(0, 0, 0, 1)
        end

        local _, _, _, _, _, _, _, _, isEmpowered, _, _ = UnitChannelInfo("player")
        if isEmpowered then
            player_is_empowered:SetColorTexture(1, 1, 1, 1)
        else
            player_is_empowered:SetColorTexture(0, 0, 0, 1)
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

        if UnitExists("target") then
            target_exist:SetColorTexture(1, 1, 1, 1)

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
                local result = duration:EvaluateElapsedPercent(curve)
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
                local result = duration:EvaluateElapsedPercent(curve)
                target_channel_duration:SetColorTexture(result.r, result.g, result.b, 1)
            else
                target_channel_icon:SetColorTexture(0, 0, 0, 1)
                target_channel_duration:SetColorTexture(0, 0, 0, 1)
                target_channel_interruptible:SetColorTexture(0, 0, 0, 1)
            end
        else
            target_exist:SetColorTexture(0, 0, 0, 1)
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

    table.insert(UpdateFuncs, UpdateNode1)
end
table.insert(FrameInitFuncs, InitializeMiscFrame)












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


-- 设置游戏变量，确保插件正常运行
SetCVar("secretChallengeModeRestrictionsForced", 1)
SetCVar("secretCombatRestrictionsForced", 1)
SetCVar("secretEncounterRestrictionsForced", 1)
SetCVar("secretMapRestrictionsForced", 1)
SetCVar("secretPvPMatchRestrictionsForced", 1)
SetCVar("secretAuraDataRestrictionsForced", 1)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
