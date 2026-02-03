local addonName, addonTable = ...
local LibRangeCheck         = LibStub:GetLibrary("LibRangeCheck-3.0", true)

local DEBUG                 = false
local scale                 = 1
local fontFile              = "Interface\\Addons\\" .. addonName .. "\\Fonts\\CustomFont.ttf"

-- 日志输出函数
local logging               = function(msg)
    print("|cFFFFBB66[" .. addonName .. "]|r", msg)
end

-- 颜色定义表
local COLOR                 = {
    RED = CreateColor(255 / 255, 0, 0, 1),
    GREEN = CreateColor(0, 255 / 255, 0, 1),
    BLUE = CreateColor(0, 0, 255 / 255, 1),
    DEBUFF = {
        MAGIC = CreateColor(0, 129 / 255, 255 / 255, 1),         -- 魔法
        CURSE = CreateColor(159 / 255, 6 / 255, 228 / 255, 1),   -- 诅咒
        DISEASE = CreateColor(241 / 255, 106 / 255, 9 / 255, 1), -- 疾病
        POISON = CreateColor(123 / 255, 199 / 255, 0, 1),        -- 中毒
        ENRAGE = CreateColor(255 / 255, 40 / 255, 0, 1),         -- 激怒 (深红色，代表愤怒和爆发)
        BLEED = CreateColor(184 / 255, 0, 15 / 255, 1),          -- 流血
        NONE = CreateColor(0, 0, 0, 1),                          -- 无debuff
    },
    NEAR_BLACK_1 = CreateColor(15 / 255, 25 / 255, 20 / 255, 1), -- 接近黑色
    NEAR_BLACK_2 = CreateColor(25 / 255, 15 / 255, 20 / 255, 1), -- 接近黑色
    BLACK = CreateColor(0, 0, 0, 1),
    WHITE = CreateColor(1, 1, 1, 1),
    C0 = CreateColor(0, 0, 0, 1),
    C100 = CreateColor(100 / 255, 100 / 255, 100 / 255, 1),
    C150 = CreateColor(150 / 255, 150 / 255, 150 / 255, 1),
    C200 = CreateColor(200 / 255, 200 / 255, 200 / 255, 1),
    C250 = CreateColor(250 / 255, 250 / 255, 250 / 255, 1),
    C255 = CreateColor(255 / 255, 255 / 255, 255 / 255, 1),
    ROLE = {
        TANK = CreateColor(180 / 255, 80 / 255, 20 / 255, 1),     -- 坦克
        HEALER = CreateColor(120 / 255, 200 / 255, 255 / 255, 1), -- 治疗
        DAMAGER = CreateColor(230 / 255, 200 / 255, 50 / 255, 1), -- 伤害输出
        NONE = CreateColor(0, 0, 0, 1),                           -- 无角色
    },
    CLASS = {
        WARRIOR = CreateColor(199 / 255, 86 / 255, 36 / 255, 1),       -- 战士
        PALADIN = CreateColor(245 / 255, 140 / 255, 186 / 255, 1),     -- 圣骑士
        HUNTER = CreateColor(163 / 255, 203 / 255, 66 / 255, 1),       -- 猎人
        ROGUE = CreateColor(255 / 255, 245 / 255, 105 / 255, 1),       -- 潜行者
        PRIEST = CreateColor(196 / 255, 207 / 255, 207 / 255, 1),      -- 牧师
        DEATHKNIGHT = CreateColor(125 / 255, 125 / 255, 215 / 255, 1), -- 死亡骑士
        SHAMAN = CreateColor(64 / 255, 148 / 255, 255 / 255, 1),       -- 萨满祭司
        MAGE = CreateColor(64 / 255, 158 / 255, 210 / 255, 1),         -- 法师
        WARLOCK = CreateColor(105 / 255, 105 / 255, 210 / 255, 1),     -- 术士
        MONK = CreateColor(0 / 255, 255 / 255, 150 / 255, 1),          -- 武僧
        DRUID = CreateColor(255 / 255, 125 / 255, 10 / 255, 1),        -- 德鲁伊
        DEMONHUNTER = CreateColor(163 / 255, 48 / 255, 201 / 255, 1),  -- 恶魔猎手
        EVOKER = CreateColor(108 / 255, 191 / 255, 246 / 255, 1)       -- 唤魔师
    }
}

-- 颜色曲线定义
local curve                 = C_CurveUtil.CreateColorCurve()
curve:SetType(Enum.LuaCurveType.Linear)
curve:AddPoint(0.0, CreateColor(0, 0, 0, 1))
curve:AddPoint(1.0, CreateColor(1, 1, 1, 1))

-- 反向颜色曲线定义
local curve_reverse = C_CurveUtil.CreateColorCurve()
curve_reverse:SetType(Enum.LuaCurveType.Linear)
curve_reverse:AddPoint(0.0, CreateColor(1, 1, 1, 1))
curve_reverse:AddPoint(1.0, CreateColor(0, 0, 0, 1))

-- Debuff颜色曲线定义
local debuff_curve = C_CurveUtil.CreateColorCurve()
debuff_curve:AddPoint(0, COLOR.DEBUFF.NONE)
debuff_curve:AddPoint(1, COLOR.DEBUFF.MAGIC)
debuff_curve:AddPoint(2, COLOR.DEBUFF.CURSE)
debuff_curve:AddPoint(3, COLOR.DEBUFF.DISEASE)
debuff_curve:AddPoint(4, COLOR.DEBUFF.POISON)
debuff_curve:AddPoint(9, COLOR.DEBUFF.ENRAGE)
debuff_curve:AddPoint(11, COLOR.DEBUFF.BLEED)

-- 剩余时间颜色曲线定义
local remaining_curve = C_CurveUtil.CreateColorCurve()
remaining_curve:SetType(Enum.LuaCurveType.Linear)
remaining_curve:AddPoint(0.0, COLOR.C0)
remaining_curve:AddPoint(5.0, COLOR.C100)
remaining_curve:AddPoint(30.0, COLOR.C150)
remaining_curve:AddPoint(155.0, COLOR.C200)
remaining_curve:AddPoint(375.0, COLOR.C255)

-- 框架初始化函数表
local FrameInitFuncs = {}
-- 更新函数表
local UpdateFuncs    = {}
-- 技能表，每个技能有两种显示方式："cooldown"和"charge"
addonTable.Spell     = {}
-- 添加GCD技能到技能表
table.insert(addonTable.Spell, { spellID = 61304, type = "cooldown" })

-- 创建主框架
local frame = CreateFrame("Frame")

-- 注册玩家进入世界事件
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

-- 时间流逝变量
local timeElapsed = 0
-- 钩子OnUpdate脚本，用于定时更新
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

-- 获取UI缩放因子
local function GetUIScaleFactor(pixelValue)
    local _, physicalHeight = GetPhysicalScreenSize()
    local logicalHeight = GetScreenHeight()
    return (pixelValue * logicalHeight) / physicalHeight
end

-- 初始化主框架
local function InitializeMainFrame()
    -- 计算UI元素尺寸
    addonTable.nodeSize = GetUIScaleFactor(6 * scale)
    addonTable.innerSize = GetUIScaleFactor(5 * scale)
    addonTable.padSize = GetUIScaleFactor(1 * scale)
    addonTable.fontSize = GetUIScaleFactor(6 * scale)
    local node_size = addonTable.nodeSize
    -- 创建主框架
    addonTable.MainFrame = CreateFrame("Frame", addonName .. "MainFrame", UIParent)
    addonTable.MainFrame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", 0, 0)
    addonTable.MainFrame:SetSize(node_size * 56, node_size * 18)
    addonTable.MainFrame:SetFrameStrata("TOOLTIP")
    addonTable.MainFrame:SetFrameLevel(900)
    addonTable.MainFrame:Show()

    -- 创建主框架背景
    addonTable.MainFrame.bg = addonTable.MainFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MainFrame.bg:SetAllPoints()
    addonTable.MainFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.MainFrame.bg:Show()

    -- 创建玩家Buff框架
    addonTable.PlayerBuffFrame = CreateFrame("Frame", addonName .. "PlayerBuffFrame", addonTable.MainFrame)
    addonTable.PlayerBuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerBuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -2 * node_size)
    addonTable.PlayerBuffFrame:SetSize(28 * node_size, 4 * node_size)
    addonTable.PlayerBuffFrame:Show()
    addonTable.PlayerBuffFrame.bg = addonTable.PlayerBuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerBuffFrame.bg:SetAllPoints()
    addonTable.PlayerBuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerBuffFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerBuffFrame.bg:SetColorTexture(91 / 255, 155 / 255, 213 / 255, 1)
    end

    -- 创建玩家Debuff框架
    addonTable.PlayerDebuffFrame = CreateFrame("Frame", addonName .. "PlayerDebuffFrame", addonTable.MainFrame)
    addonTable.PlayerDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 30 * node_size, -2 * node_size)
    addonTable.PlayerDebuffFrame:SetSize(7 * node_size, 4 * node_size)
    addonTable.PlayerDebuffFrame:Show()
    addonTable.PlayerDebuffFrame.bg = addonTable.PlayerDebuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerDebuffFrame.bg:SetAllPoints()
    addonTable.PlayerDebuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerDebuffFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerDebuffFrame.bg:SetColorTexture(255 / 255, 192 / 255, 0 / 255, 1)
    end

    -- 创建玩家状态框架
    addonTable.PlayerStatusFrame = CreateFrame("Frame", addonName .. "PlayerStatusFrame", addonTable.MainFrame)
    addonTable.PlayerStatusFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerStatusFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 37 * node_size, -2 * node_size)
    addonTable.PlayerStatusFrame:SetSize(10 * node_size, 4 * node_size)
    addonTable.PlayerStatusFrame:Show()
    addonTable.PlayerStatusFrame.bg = addonTable.PlayerStatusFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerStatusFrame.bg:SetAllPoints()
    addonTable.PlayerStatusFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerStatusFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerStatusFrame.bg:SetColorTexture(165 / 255, 165 / 255, 165 / 255, 1)
    end

    -- 创建目标Debuff框架
    addonTable.TargetDebuffFrame = CreateFrame("Frame", addonName .. "TargetDebuffFrame", addonTable.MainFrame)
    addonTable.TargetDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.TargetDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 47 * node_size, -2 * node_size)
    addonTable.TargetDebuffFrame:SetSize(7 * node_size, 4 * node_size)
    addonTable.TargetDebuffFrame:Show()
    addonTable.TargetDebuffFrame.bg = addonTable.TargetDebuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.TargetDebuffFrame.bg:SetAllPoints()
    addonTable.TargetDebuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.TargetDebuffFrame.bg:Show()
    if DEBUG then
        addonTable.TargetDebuffFrame.bg:SetColorTexture(237 / 255, 125 / 255, 49 / 255, 1)
    end

    -- 创建玩家技能框架
    addonTable.PlayerSpellFrame = CreateFrame("Frame", addonName .. "PlayerSpellFrame", addonTable.MainFrame)
    addonTable.PlayerSpellFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerSpellFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -6 * node_size)
    addonTable.PlayerSpellFrame:SetSize(24 * node_size, 4 * node_size)
    addonTable.PlayerSpellFrame:Show()
    addonTable.PlayerSpellFrame.bg = addonTable.PlayerSpellFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.PlayerSpellFrame.bg:SetAllPoints()
    addonTable.PlayerSpellFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.PlayerSpellFrame.bg:Show()
    if DEBUG then
        addonTable.PlayerSpellFrame.bg:SetColorTexture(84 / 255, 130 / 255, 53 / 255, 1)
    end

    -- 创建杂项框架
    addonTable.MiscFrame = CreateFrame("Frame", addonName .. "MiscFrame", addonTable.MainFrame)
    addonTable.MiscFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.MiscFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 26 * node_size, -6 * node_size)
    addonTable.MiscFrame:SetSize(node_size * 13, node_size * 2)
    addonTable.MiscFrame:Show()
    addonTable.MiscFrame.bg = addonTable.MiscFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MiscFrame.bg:SetAllPoints()
    addonTable.MiscFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.MiscFrame.bg:Show()
    if DEBUG then
        addonTable.MiscFrame.bg:SetColorTexture(237 / 255, 125 / 255, 49 / 255, 1)
    end

    -- 创建专精框架
    addonTable.SpecFrame = CreateFrame("Frame", addonName .. "SpecFrame", addonTable.MainFrame)
    addonTable.SpecFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.SpecFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 26 * node_size, -8 * node_size)
    addonTable.SpecFrame:SetSize(node_size * 13, node_size * 2)
    addonTable.SpecFrame:Show()
    addonTable.SpecFrame.bg = addonTable.SpecFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.SpecFrame.bg:SetAllPoints()
    addonTable.SpecFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.SpecFrame.bg:Show()
    if DEBUG then
        addonTable.SpecFrame.bg:SetColorTexture(112 / 255, 173 / 255, 71 / 255, 1)
    end

    -- 创建目标状态框架
    addonTable.TargetStatusFrame = CreateFrame("Frame", addonName .. "TargetStatusFrame", addonTable.MainFrame)
    addonTable.TargetStatusFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.TargetStatusFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 39 * node_size, -6 * node_size)
    addonTable.TargetStatusFrame:SetSize(8 * node_size, 2 * node_size)
    addonTable.TargetStatusFrame:Show()
    addonTable.TargetStatusFrame.bg = addonTable.TargetStatusFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.TargetStatusFrame.bg:SetAllPoints()
    addonTable.TargetStatusFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.TargetStatusFrame.bg:Show()
    if DEBUG then
        addonTable.TargetStatusFrame.bg:SetColorTexture(91 / 255, 155 / 255, 213 / 255, 1)
    end

    -- 创建焦点状态框架
    addonTable.FocusStatusFrame = CreateFrame("Frame", addonName .. "FocusStatusFrame", addonTable.MainFrame)
    addonTable.FocusStatusFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.FocusStatusFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 39 * node_size, -8 * node_size)
    addonTable.FocusStatusFrame:SetSize(8 * node_size, 2 * node_size)
    addonTable.FocusStatusFrame:Show()
    addonTable.FocusStatusFrame.bg = addonTable.FocusStatusFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.FocusStatusFrame.bg:SetAllPoints()
    addonTable.FocusStatusFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.FocusStatusFrame.bg:Show()
    if DEBUG then
        addonTable.FocusStatusFrame.bg:SetColorTexture(255 / 255, 192 / 255, 0 / 255, 1)
    end

    -- 创建焦点Debuff框架
    addonTable.FocusDebuffFrame = CreateFrame("Frame", addonName .. "FocusDebuffFrame", addonTable.MainFrame)
    addonTable.FocusDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.FocusDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 47 * node_size, -6 * node_size)
    addonTable.FocusDebuffFrame:SetSize(7 * node_size, 4 * node_size)
    addonTable.FocusDebuffFrame:Show()
    addonTable.FocusDebuffFrame.bg = addonTable.FocusDebuffFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.FocusDebuffFrame.bg:SetAllPoints()
    addonTable.FocusDebuffFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.FocusDebuffFrame.bg:Show()
    if DEBUG then
        addonTable.FocusDebuffFrame.bg:SetColorTexture(112 / 255, 173 / 255, 71 / 255, 1)
    end

    -- 创建队伍框架
    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)

        addonTable["PartyFrame" .. UnitKey] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey, addonTable.MainFrame)
        addonTable["PartyFrame" .. UnitKey]:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey]:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", (13 * i - 11) * node_size, -10 * node_size)
        addonTable["PartyFrame" .. UnitKey]:SetSize(node_size * 13, node_size * 6)
        addonTable["PartyFrame" .. UnitKey]:Show()
        addonTable["PartyFrame" .. UnitKey].bg = addonTable["PartyFrame" .. UnitKey]:CreateTexture(nil, "BACKGROUND")
        addonTable["PartyFrame" .. UnitKey].bg:SetAllPoints()
        addonTable["PartyFrame" .. UnitKey].bg:SetColorTexture(0, 0, 0, 1)
        addonTable["PartyFrame" .. UnitKey].bg:Show()
        if DEBUG then
            addonTable["PartyFrame" .. UnitKey].bg:SetColorTexture(127 / 255, 127 / 255, 127 / 255, 1)
        end
    end

    -- 创建方块函数
    local function create_square(x, y, color)
        local frame = CreateFrame("Frame", addonName .. "Frame" .. x .. y, addonTable.MainFrame)
        frame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 5)
        frame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", x * node_size, -y * node_size)
        frame:SetSize(node_size, node_size)
        frame:Show()
        frame.bg = frame:CreateTexture(nil, "BACKGROUND")
        frame.bg:SetAllPoints()
        frame.bg:SetColorTexture(color:GetRGBA())
        frame.bg:Show()
    end

    -- 创建角落方块
    create_square(0, 0, COLOR.NEAR_BLACK_1)
    create_square(1, 0, COLOR.NEAR_BLACK_2)
    create_square(0, 1, COLOR.NEAR_BLACK_2)
    create_square(1, 1, COLOR.NEAR_BLACK_1)
    create_square(54, 16, COLOR.NEAR_BLACK_1)
    create_square(54, 17, COLOR.NEAR_BLACK_2)
    create_square(55, 16, COLOR.NEAR_BLACK_2)
    create_square(55, 17, COLOR.NEAR_BLACK_1)

    logging("MainFrame created")
end

-- 将初始化主框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeMainFrame)

-- 创建像素节点
local function CreatePixelNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local nodeFrame = CreateFrame("Frame", addonName .. "Pixel" .. title, parent_frame)
    nodeFrame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size, -y * node_size)
    nodeFrame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    nodeFrame:SetSize(innerSize, innerSize)
    nodeFrame:Show()
    local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
    nodeTexture:SetAllPoints(nodeFrame)
    nodeTexture:SetColorTexture(0, 0, 0, 1)
    nodeTexture:Show()
    return nodeTexture
end

-- 创建文字节点
local function CreateStringNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local fontSize = addonTable.fontSize
    local nodeFrame = CreateFrame("Frame", addonName .. "String" .. title, parent_frame)
    nodeFrame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size, -y * node_size)
    nodeFrame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    nodeFrame:SetSize(innerSize, innerSize)
    nodeFrame:Show()
    local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
    nodeTexture:SetAllPoints(nodeFrame)
    nodeTexture:SetColorTexture(0, 0, 0, 1)
    nodeTexture:Show()


    local nodeString = nodeFrame:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    nodeString:SetAllPoints(nodeFrame)
    nodeString:SetJustifyH("CENTER")
    nodeString:SetJustifyV("MIDDLE")
    nodeString:SetFontObject(GameFontHighlight)
    nodeString:SetTextColor(1, 1, 1, 1)
    nodeString:SetFont(fontFile, fontSize, "MONOCHROME")
    nodeString:SetText("")
    nodeString:Show()
    return nodeString
end

-- 创建光环序列
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

    -- 创建光环序列元素
    for i = 1, maxCount do
        local icon_texture = CreatePixelNode((i - 1), 0, addonName .. name_prefix .. "IconFrame" .. i, parent)
        table.insert(iconTextures, icon_texture)

        local duration_texture = CreatePixelNode((i - 1), 1, addonName .. name_prefix .. "DurationFrame" .. i, parent)
        table.insert(durationTextures, duration_texture)

        local dispel_texture = CreatePixelNode((i - 1), 2, addonName .. name_prefix .. "DispelFrame" .. i, parent)
        table.insert(dispelTextures, dispel_texture)

        local count_string = CreateStringNode((i - 1), 3, addonName .. name_prefix .. "CountFrame" .. i, parent)
        table.insert(countTextures, count_string)
    end

    -- 清除纹理函数
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

    -- 更新纹理函数
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
            local result = duration:EvaluateRemainingDuration(remaining_curve)
            local dispelTypeColor = C_UnitAuras.GetAuraDispelTypeColor(unit, auraInstanceID, debuff_curve)
            local count = C_UnitAuras.GetAuraApplicationDisplayCount(unit, auraInstanceID, 1, 9)

            iconTextures[i]:SetTexture(aura.icon)
            durationTextures[i]:SetColorTexture(result:GetRGBA())
            dispelTextures[i]:SetColorTexture(dispelTypeColor:GetRGBA())
            countTextures[i]:SetText(count)
        end
    end
    table.insert(UpdateFuncs, updateTexture)
end

-- 创建白色条
local function CreateWhiteBar(name, parent, x, y, width, height)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize

    local frame = CreateFrame("Frame", addonName .. name, parent)
    frame:SetFrameLevel(parent:GetFrameLevel() + 1)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * node_size, -y * node_size - padSize)
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

-- 初始化配置框架
local function InitializeConfigFrame()
    local si_node1 = CreatePixelNode(1, 17, addonName .. "si_node1", addonTable.MainFrame)
    local si_node2 = CreatePixelNode(15, 1, addonName .. "si_node2", addonTable.MainFrame)
    local si_node3 = CreatePixelNode(54, 14, addonName .. "si_node3", addonTable.MainFrame)
    local enable_node = CreatePixelNode(3, 16, addonName .. "enable_node", addonTable.MainFrame)
    SLASH_SI1 = "/si"
    SlashCmdList["SI"] = function(msg)
        local icon = nil
        local spell_id = nil
        if tonumber(msg) then
            msg = tonumber(msg)
        end

        local spellInfo = C_Spell.GetSpellInfo(msg)
        if spellInfo then
            icon = spellInfo.iconID
            spell_id = spellInfo.spellID
        end

        if not icon then
            local iconID, originalIconID = C_Spell.GetSpellTexture(msg)
            icon = iconID
        end

        si_node1:SetTexture(icon)
        si_node2:SetTexture(icon)
        si_node3:SetTexture(icon)
        if spell_id then
            local spellLink = C_Spell.GetSpellLink(spell_id)
            logging(spellLink)
        end
        C_Timer.After(10, function()
            logging("SI reset")
            si_node1:SetColorTexture(0, 0, 0, 1)
            si_node2:SetColorTexture(0, 0, 0, 1)
            si_node3:SetColorTexture(0, 0, 0, 1)
        end)
    end
    CreateStringNode(54, 1, addonName .. "num_star", addonTable.MainFrame):SetText("*")
    CreateStringNode(54, 2, addonName .. "num_0", addonTable.MainFrame):SetText("0")
    CreateStringNode(54, 3, addonName .. "num_1", addonTable.MainFrame):SetText("1")
    CreateStringNode(54, 4, addonName .. "num_2", addonTable.MainFrame):SetText("2")
    CreateStringNode(54, 5, addonName .. "num_3", addonTable.MainFrame):SetText("3")
    CreateStringNode(54, 6, addonName .. "num_4", addonTable.MainFrame):SetText("4")
    CreateStringNode(54, 7, addonName .. "num_5", addonTable.MainFrame):SetText("5")
    CreateStringNode(54, 8, addonName .. "num_6", addonTable.MainFrame):SetText("6")
    CreateStringNode(54, 9, addonName .. "num_7", addonTable.MainFrame):SetText("7")
    CreateStringNode(54, 10, addonName .. "num_8", addonTable.MainFrame):SetText("8")
    CreateStringNode(54, 11, addonName .. "num_9", addonTable.MainFrame):SetText("9")
end

-- 将初始化配置框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeConfigFrame)

-- 初始化光环框架
local function InitializeAuraFrame()
    logging("InitializeAuraFrame")
    CreateAuraSequence("player", "HELPFUL", 28, "PlayerBuff", addonTable.PlayerBuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("player", "HARMFUL", 7, "PlayerDebuff", addonTable.PlayerDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("target", "HARMFUL|PLAYER", 7, "TargetDebuff", addonTable.TargetDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("focus", "HARMFUL|PLAYER", 7, "FocusDebuff", addonTable.FocusDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)

    logging("AuraFrame created")
end

-- 将初始化光环框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeAuraFrame)

-- 初始化玩家状态框架
local function InitializePlayerStatusFrame()
    local x = 0
    local y = 0
    local player_in_combat = CreatePixelNode(x, y, "PlayerInCombat", addonTable.PlayerStatusFrame)
    x = 1
    local player_is_moving = CreatePixelNode(x, y, "PlayerIsMoving", addonTable.PlayerStatusFrame)
    x = 2
    local player_in_vehicle = CreatePixelNode(x, y, "PlayerInVehicle", addonTable.PlayerStatusFrame)
    x = 3
    local player_is_empowered = CreatePixelNode(x, y, "PlayerIsEmpowered", addonTable.PlayerStatusFrame)
    x = 4
    local player_cast_icon = CreatePixelNode(x, y, "PlayerCastIcon", addonTable.PlayerStatusFrame)
    x = 5
    local player_cast_duration = CreatePixelNode(x, y, "PlayerCastDuration", addonTable.PlayerStatusFrame)
    x = 6
    local player_channel_icon = CreatePixelNode(x, y, "PlayerChannelIcon", addonTable.PlayerStatusFrame)
    x = 7
    local player_channel_duration = CreatePixelNode(x, y, "PlayerChannelDuration", addonTable.PlayerStatusFrame)

    y = 1
    x = 0
    local player_class = CreatePixelNode(x, y, "PlayerClass", addonTable.PlayerStatusFrame)
    x = 1
    local player_role = CreatePixelNode(x, y, "PlayerRole", addonTable.PlayerStatusFrame)
    x = 2
    local player_deaded = CreatePixelNode(x, y, "PlayerDeaded", addonTable.PlayerStatusFrame)

    y = 0
    x = 9
    local player_health = CreatePixelNode(x, y, "PlayerHealth", addonTable.PlayerStatusFrame)
    y = 1
    local player_power = CreatePixelNode(x, y, "PlayerPower", addonTable.PlayerStatusFrame)
    local powerType, _, _, _, _ = UnitPowerType("player")

    local PlayerDamageAbsorbsBar = CreateWhiteBar("PlayerDamageAbsorbsBar", addonTable.PlayerStatusFrame, 0, 2, 10, 1)
    local PlayerHealAbsorbsBar = CreateWhiteBar("PlayerHealAbsorbsBar", addonTable.PlayerStatusFrame, 0, 3, 10, 1)

    -- 更新玩家状态函数
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
            local result = duration:EvaluateElapsedPercent(curve)
            player_cast_duration:SetColorTexture(result:GetRGBA())
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
            local result = duration:EvaluateElapsedPercent(curve)
            player_channel_duration:SetColorTexture(result:GetRGBA())
        else
            player_channel_icon:SetColorTexture(0, 0, 0, 1)
            player_channel_duration:SetColorTexture(0, 0, 0, 1)
        end

        local _, classFilename, _ = UnitClass("player")
        -- local p = COLOR.CLASS[classFilename]
        -- local r, g, b, a = p:GetRGBA()
        -- logging("r" .. r * 255 .. ",g" .. g * 255 .. ",b" .. b * 255 .. ",a" .. a)
        player_class:SetColorTexture(COLOR.CLASS[classFilename]:GetRGBA())
        -- 检查角色
        local role = UnitGroupRolesAssigned("player")
        player_role:SetColorTexture(COLOR.ROLE[role]:GetRGBA())

        if UnitIsDeadOrGhost("player") then
            player_deaded:SetColorTexture(1, 1, 1, 1)
        else
            player_deaded:SetColorTexture(0, 0, 0, 1)
        end

        local maxHealth = UnitHealthMax("player")

        PlayerDamageAbsorbsBar:SetMinMaxValues(0, maxHealth)
        PlayerDamageAbsorbsBar:SetValue(UnitGetTotalAbsorbs("player"))

        PlayerHealAbsorbsBar:SetMinMaxValues(0, maxHealth)
        PlayerHealAbsorbsBar:SetValue(UnitGetTotalHealAbsorbs("player"))

        player_health:SetColorTexture(UnitHealthPercent("player", true, curve):GetRGBA())
        player_power:SetColorTexture(UnitPowerPercent("player", powerType, true, curve):GetRGBA())
    end
    table.insert(UpdateFuncs, UpdateStatus)
end

-- 将初始化玩家状态框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializePlayerStatusFrame)

-- 初始化技能框架
local function InitializeSpellFrame()
    logging("InitializeSpellFrame")
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    local MaxFrame = math.min(24, #addonTable.Spell)
    local iconTextrues = {}
    local cooldownTextrues = {}
    local highlightTextrues = {}
    local chargeStrings = {}

    -- 创建技能框架元素
    for i = 1, 24 do
        local iconTexture = CreatePixelNode(i - 1, 0, "SpellIconFrame" .. i, addonTable.PlayerSpellFrame)
        table.insert(iconTextrues, iconTexture)

        local cooldownTexture = CreatePixelNode(i - 1, 1, "SpellCooldownFrame" .. i, addonTable.PlayerSpellFrame)
        table.insert(cooldownTextrues, cooldownTexture)

        local highlightTexture = CreatePixelNode(i - 1, 2, "SpellHighlightFrame" .. i, addonTable.PlayerSpellFrame)
        table.insert(highlightTextrues, highlightTexture)

        local charge_string = CreateStringNode(i - 1, 3, "SpellChargeFrame" .. i, addonTable.PlayerSpellFrame)
        table.insert(chargeStrings, charge_string)
    end

    -- 设置技能图标
    for i = 1, MaxFrame do
        local SpellID = addonTable.Spell[i].spellID
        local iconID, _ = C_Spell.GetSpellTexture(SpellID)
        iconTextrues[i]:SetTexture(iconID)
        local spellLink = C_Spell.GetSpellLink(SpellID)
        logging("技能冷却[" .. i .. "]: 类型 " .. addonTable.Spell[i].type .. " 技能" .. spellLink)
    end

    -- 更新节点纹理函数
    local function UpdateNodeTexture()
        for i = 1, MaxFrame do
            local SpellID = addonTable.Spell[i].spellID

            if addonTable.Spell[i].type == "charge" then
                local duration = C_Spell.GetSpellChargeDuration(SpellID)
                local result = duration:EvaluateRemainingDuration(remaining_curve)
                cooldownTextrues[i]:SetColorTexture(result:GetRGBA())

                local chargeInfo = C_Spell.GetSpellCharges(SpellID)
                chargeStrings[i]:SetText(tostring(chargeInfo.currentCharges))
            else
                local duration = C_Spell.GetSpellCooldownDuration(SpellID)
                local result = duration:EvaluateRemainingDuration(remaining_curve)
                cooldownTextrues[i]:SetColorTexture(result:GetRGBA())
            end

            local isSpellOverlayed = C_SpellActivationOverlay.IsSpellOverlayed(SpellID)
            highlightTextrues[i]:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(isSpellOverlayed, COLOR.WHITE, COLOR.BLACK):GetRGBA())
        end
    end
    table.insert(UpdateFuncs, UpdateNodeTexture)
    logging("PlayerSpellFrame created")
end

-- 将初始化技能框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeSpellFrame)

-- 初始化队伍框架
local function InitializePartyFrame()
    logging("InitializePartyFrame")
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local innerSize = addonTable.innerSize
    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)
        local parent_frame = addonTable["PartyFrame" .. UnitKey]
        local frame_pre = addonName .. "PartyFrame" .. UnitKey

        -- 创建队伍Buff框架
        local buff_frame = CreateFrame("Frame", frame_pre .. "BuffFrame", parent_frame)
        buff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        buff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, 0)
        buff_frame:SetSize(node_size * 7, node_size * 4)
        buff_frame:Show()
        CreateAuraSequence(UnitKey, "HELPFUL|PLAYER", 7, UnitKey .. "Buff", buff_frame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)

        -- 创建队伍Debuff框架
        local debuff_frame = CreateFrame("Frame", frame_pre .. "DebuffFrame", parent_frame)
        debuff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        debuff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 7 * node_size, 0)
        debuff_frame:SetSize(node_size * 6, node_size * 4)
        debuff_frame:Show()
        CreateAuraSequence(UnitKey, "HARMFUL", 6, UnitKey .. "Debuff", debuff_frame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)

        -- 创建队伍条框架
        local bar_frame = CreateFrame("Frame", frame_pre .. "BarFrame", parent_frame)
        bar_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        bar_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, -4 * node_size)
        bar_frame:SetSize(node_size * 10, node_size * 3)
        bar_frame:Show()

        -- 创建队伍状态框架
        local status_frame = CreateFrame("Frame", frame_pre .. "StatusFrame", parent_frame)
        status_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        status_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 10 * node_size, -4 * node_size)
        status_frame:SetSize(node_size * 3, node_size * 2)
        status_frame:Show()

        -- 创建队伍状态节点
        local unit_exist = CreatePixelNode(0, 0, addonName .. "PartyExist" .. i, status_frame)
        local unit_in_range = CreatePixelNode(1, 0, addonName .. "PartyInRange" .. i, status_frame)
        local unit_health = CreatePixelNode(2, 0, addonName .. "PartyHealth" .. i, status_frame)
        local unit_class = CreatePixelNode(0, 1, addonName .. "PartyClass" .. i, status_frame)
        local unit_role = CreatePixelNode(1, 1, addonName .. "PartyRole" .. i, status_frame)
        local unit_select = CreatePixelNode(2, 1, addonName .. "PartySelect" .. i, status_frame)

        -- 创建队伍吸收条
        local DamageAbsorbsBar = CreateWhiteBar(UnitKey .. "DamageAbsorbsBar", bar_frame, 0, 0, 10, 1)
        local HealAbsorbsBar = CreateWhiteBar(UnitKey .. "HealAbsorbsBar", bar_frame, 0, 1, 10, 1)

        -- 更新队伍框架函数
        function UpdateUnitrame()
            if UnitExists(UnitKey) then
                -- 检查是否存在
                unit_exist:SetColorTexture(1, 1, 1, 1)
                -- -- 检查范围
                local _, maxRange = LibRangeCheck:GetRange(UnitKey)
                if maxRange and (maxRange <= addonTable.RangeCheck) then
                    unit_in_range:SetColorTexture(1, 1, 1, 1)
                else
                    unit_in_range:SetColorTexture(0, 0, 0, 1)
                end
                -- -- 检查职业
                local _, classFilename, _ = UnitClass(UnitKey)
                if classFilename then
                    unit_class:SetColorTexture(COLOR.CLASS[classFilename]:GetRGBA())
                else
                    unit_class:SetColorTexture(0, 0, 0, 1)
                end
                -- -- 检查角色
                local role = UnitGroupRolesAssigned(UnitKey)
                unit_role:SetColorTexture(COLOR.ROLE[role]:GetRGBA())

                unit_health:SetColorTexture(UnitHealthPercent(UnitKey, true, curve):GetRGBA())

                if UnitIsUnit("target", UnitKey) then
                    unit_select:SetColorTexture(1, 1, 1, 1)
                else
                    unit_select:SetColorTexture(0, 0, 0, 1)
                end

                local maxHealth = UnitHealthMax(UnitKey)
                DamageAbsorbsBar:SetMinMaxValues(0, maxHealth)
                DamageAbsorbsBar:SetValue(UnitGetTotalAbsorbs(UnitKey))

                HealAbsorbsBar:SetMinMaxValues(0, maxHealth)
                HealAbsorbsBar:SetValue(UnitGetTotalHealAbsorbs(UnitKey))
            else
                unit_exist:SetColorTexture(0, 0, 0, 1)
                unit_in_range:SetColorTexture(0, 0, 0, 1)
                unit_class:SetColorTexture(0, 0, 0, 1)
                unit_role:SetColorTexture(0, 0, 0, 1)
                unit_health:SetColorTexture(0, 0, 0, 1)
                unit_select:SetColorTexture(0, 0, 0, 1)

                DamageAbsorbsBar:SetValue(0)
                HealAbsorbsBar:SetValue(0)
            end
        end

        table.insert(UpdateFuncs, UpdateUnitrame)
    end
    logging("PartyFrame created")
end

-- 将初始化队伍框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializePartyFrame)

-- 初始化单位状态框架
local function InitializeUnitStatusFrame(unit, parent)
    local x = 0
    local y = 0
    local unit_exist = CreatePixelNode(x, y, unit .. "TargetExist", parent)
    x = 1
    local unit_can_attack = CreatePixelNode(x, y, unit .. "CanAttack", parent)
    x = 2
    local unit_is_self = CreatePixelNode(x, y, unit .. "IsSelf", parent)
    x = 3
    local unit_is_alive = CreatePixelNode(x, y, unit .. "IsAlive", parent)
    x = 4
    local unit_in_combat = CreatePixelNode(x, y, unit .. "InCombat", parent)
    x = 5
    local unit_in_range = CreatePixelNode(x, y, unit .. "InRange", parent)
    x = 7
    local unit_health = CreatePixelNode(x, y, unit .. "Health", parent)
    y = 1
    x = 0
    local unit_cast_icon = CreatePixelNode(x, y, unit .. "CastIcon", parent)
    x = 1
    local unit_cast_duration = CreatePixelNode(x, y, unit .. "CastDuration", parent)
    x = 2
    local unit_cast_interruptible = CreatePixelNode(x, y, unit .. "CastInterruptible", parent)
    x = 3
    local unit_channel_icon = CreatePixelNode(x, y, unit .. "ChannelIcon", parent)
    x = 4
    local unit_channel_duration = CreatePixelNode(x, y, unit .. "ChannelDuration", parent)
    x = 5
    local unit_channel_interruptible = CreatePixelNode(x, y, unit .. "ChannelInterruptible", parent)

    -- 更新单位状态函数
    local function UpdateStatus()
        if UnitExists(unit) then
            unit_exist:SetColorTexture(1, 1, 1, 1)

            if UnitCanAttack("player", unit) then
                unit_can_attack:SetColorTexture(1, 1, 1, 1)
            else
                unit_can_attack:SetColorTexture(0, 0, 0, 1)
            end

            if UnitIsUnit("player", unit) then
                unit_is_self:SetColorTexture(1, 1, 1, 1)
            else
                unit_is_self:SetColorTexture(0, 0, 0, 1)
            end

            if UnitAffectingCombat(unit) then
                unit_in_combat:SetColorTexture(1, 1, 1, 1)
            else
                unit_in_combat:SetColorTexture(0, 0, 0, 1)
            end

            if UnitIsDeadOrGhost(unit) then
                unit_is_alive:SetColorTexture(0, 0, 0, 1)
            else
                unit_is_alive:SetColorTexture(1, 1, 1, 1)
            end

            local _, maxRange = LibRangeCheck:GetRange(unit)
            if maxRange and (maxRange <= addonTable.RangeCheck) then
                unit_in_range:SetColorTexture(1, 1, 1, 1)
            else
                unit_in_range:SetColorTexture(0, 0, 0, 1)
            end

            local _, _, CastTextureID, _, _, _, _, CastNotInterruptible, _, _ = UnitCastingInfo(unit)
            if CastTextureID then
                unit_cast_icon:SetTexture(CastTextureID)
                unit_cast_interruptible:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(CastNotInterruptible, COLOR.BLACK, COLOR.WHITE):GetRGBA())
                local duration = UnitCastingDuration(unit)
                local result = duration:EvaluateElapsedPercent(curve)
                unit_cast_duration:SetColorTexture(result:GetRGBA())
            else
                unit_cast_icon:SetColorTexture(0, 0, 0, 1)
                unit_cast_duration:SetColorTexture(0, 0, 0, 1)
                unit_cast_interruptible:SetColorTexture(0, 0, 0, 1)
            end
            local _, _, textureID, _, _, _, ChannelNotInterruptible = UnitChannelInfo(unit)
            if textureID then
                unit_channel_icon:SetTexture(textureID)
                unit_channel_interruptible:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(ChannelNotInterruptible, COLOR.BLACK, COLOR.WHITE):GetRGBA())
                local duration = UnitChannelDuration(unit)
                local result = duration:EvaluateElapsedPercent(curve)
                unit_channel_duration:SetColorTexture(result:GetRGBA())
            else
                unit_channel_icon:SetColorTexture(0, 0, 0, 1)
                unit_channel_duration:SetColorTexture(0, 0, 0, 1)
                unit_channel_interruptible:SetColorTexture(0, 0, 0, 1)
            end

            unit_health:SetColorTexture(UnitHealthPercent(unit, true, curve):GetRGBA())
        else
            unit_exist:SetColorTexture(0, 0, 0, 1)
            unit_can_attack:SetColorTexture(0, 0, 0, 1)
            unit_is_self:SetColorTexture(0, 0, 0, 1)
            unit_in_combat:SetColorTexture(0, 0, 0, 1)
            unit_in_range:SetColorTexture(0, 0, 0, 1)
            unit_is_alive:SetColorTexture(0, 0, 0, 1)
            unit_cast_icon:SetColorTexture(0, 0, 0, 1)
            unit_cast_duration:SetColorTexture(0, 0, 0, 1)
            unit_cast_interruptible:SetColorTexture(0, 0, 0, 1)
            unit_channel_icon:SetColorTexture(0, 0, 0, 1)
            unit_channel_duration:SetColorTexture(0, 0, 0, 1)
            unit_channel_interruptible:SetColorTexture(0, 0, 0, 1)
            unit_health:SetColorTexture(0, 0, 0, 1)
        end
    end

    table.insert(UpdateFuncs, UpdateStatus)
end

-- 初始化目标和焦点状态框架
local function InitializeTargetAndFocusStatusFrame()
    InitializeUnitStatusFrame("target", addonTable.TargetStatusFrame)
    InitializeUnitStatusFrame("focus", addonTable.FocusStatusFrame)
end

-- 将初始化目标和焦点状态框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeTargetAndFocusStatusFrame)

-- 初始化杂项框架
local function InitializeMiscFrame()
    logging("InitializeMiscFrame")
    local x = 0
    local y = 0
    local assisted_combat = CreatePixelNode(x, y, "AssistedCombat", addonTable.MiscFrame)

    -- 更新杂项状态函数
    local function UpdateStatus()
        local spellID = C_AssistedCombat.GetNextCastSpell(false)
        if spellID then
            local iconID, originalIconID = C_Spell.GetSpellTexture(spellID)
            assisted_combat:SetTexture(originalIconID)
        else
            assisted_combat:SetColorTexture(0, 0, 0, 1)
        end
    end
    table.insert(UpdateFuncs, UpdateStatus)
    logging("MiscFrame created")
end

-- 将初始化杂项框架函数添加到初始化函数表
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
