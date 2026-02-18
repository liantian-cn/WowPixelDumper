local addonName, addonTable = ...
local LibRangeCheck         = LibStub:GetLibrary("LibRangeCheck-3.0", true)

local DEBUG                 = false
local scale                 = 1
local fontFile              = "Interface\\Addons\\" .. addonName .. "\\Fonts\\CustomFont.ttf"

-- 日志输出函数
local logging               = function(msg)
    print("|cFFFFBB66[PixDumper]|r" .. tostring(msg))
end


-- 本地化提高性能
local CreateFrame = CreateFrame
local tostring = tostring
-- Unit
local UnitHealthPercent = UnitHealthPercent
local UnitPowerPercent = UnitPowerPercent
local UnitGetTotalHealAbsorbs = UnitGetTotalHealAbsorbs
local UnitGetTotalAbsorbs = UnitGetTotalAbsorbs
local UnitHealthMax = UnitHealthMax
local UnitClass = UnitClass
local UnitGroupRolesAssigned = UnitGroupRolesAssigned
local UnitIsUnit = UnitIsUnit
local UnitIsEnemy = UnitIsEnemy
local UnitIsDeadOrGhost = UnitIsDeadOrGhost
local UnitExists = UnitExists
local UnitCanAttack = UnitCanAttack
local UnitChannelDuration = UnitChannelDuration
local UnitCastingDuration = UnitCastingDuration
local UnitInVehicle = UnitInVehicle
local IsMounted = IsMounted
local GetUnitSpeed = GetUnitSpeed
local UnitAffectingCombat = UnitAffectingCombat
local UnitCastingInfo = UnitCastingInfo
local UnitChannelInfo = UnitChannelInfo
-- C_Spell
local IsSpellUsable = C_Spell.IsSpellUsable
local GetSpellTexture = C_Spell.GetSpellTexture
local GetSpellCharges = C_Spell.GetSpellCharges
local GetSpellChargeDuration = C_Spell.GetSpellChargeDuration
local GetSpellCooldownDuration = C_Spell.GetSpellCooldownDuration
local GetSpellLink = C_Spell.GetSpellLink
-- C_SpellBook
local IsSpellInSpellBook = C_SpellBook.IsSpellInSpellBook
-- C_CurveUtil
local CreateColorCurve = C_CurveUtil.CreateColorCurve
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean
-- C_UnitAuras
local GetUnitAuraInstanceIDs = C_UnitAuras.GetUnitAuraInstanceIDs
local GetAuraDataByAuraInstanceID = C_UnitAuras.GetAuraDataByAuraInstanceID
local GetAuraDuration = C_UnitAuras.GetAuraDuration
local GetAuraApplicationDisplayCount = C_UnitAuras.GetAuraApplicationDisplayCount
local GetAuraDispelTypeColor = C_UnitAuras.GetAuraDispelTypeColor
local DoesAuraHaveExpirationTime = C_UnitAuras.DoesAuraHaveExpirationTime
-- C_CooldownViewer
local GetCooldownViewerCategorySet = C_CooldownViewer.GetCooldownViewerCategorySet
local GetCooldownViewerCooldownInfo = C_CooldownViewer.GetCooldownViewerCooldownInfo
-- C_SpellActivationOverlay
local IsSpellOverlayed = C_SpellActivationOverlay.IsSpellOverlayed
-- C_AssistedCombat
local GetNextCastSpell = C_AssistedCombat.GetNextCastSpell
local GetCurrentKeyBoardFocus = GetCurrentKeyBoardFocus
local SpellIsTargeting = SpellIsTargeting



-- 颜色定义表
local COLOR = {
    RED = CreateColor(255 / 255, 0, 0, 1),
    GREEN = CreateColor(0, 255 / 255, 0, 1),
    BLUE = CreateColor(0, 0, 255 / 255, 1),
    ICONS = {
        MAGIC = CreateColor(60 / 255, 100 / 255, 220 / 255, 1),                     -- 魔法
        CURSE = CreateColor(100 / 255, 0, 120 / 255, 1),                            -- 诅咒
        DISEASE = CreateColor(160 / 255, 120 / 255, 60 / 255, 1),                   -- 疾病
        POISON = CreateColor(154 / 255, 205 / 255, 50 / 255, 1),                    -- 中毒
        ENRAGE = CreateColor(230 / 255, 120 / 255, 20 / 255, 1),                    -- 激怒
        BLEED = CreateColor(80 / 255, 0, 20 / 255, 1),                              -- 流血
        PLAYER_DEBUFF = CreateColor(255 / 255, 60 / 255, 60 / 255, 1),              -- 无分类减益
        PLAYER_BUFF = CreateColor(80 / 255, 220 / 255, 120 / 255, 1),               -- 友方增益
        PLAYER_SPELL = CreateColor(64 / 255, 158 / 255, 210 / 255, 1),              -- 友方施法
        ENEMY_SPELL_INTERRUPTIBLE = CreateColor(255 / 255, 255 / 255, 60 / 255, 1), -- 可打断
        ENEMY_SPELL_NOT_INTERRUPTIBLE = CreateColor(200 / 255, 0, 0, 1),            -- 不可打断
        ENEMY_DEBUFF = CreateColor(105 / 255, 105 / 255, 210 / 255, 1),             -- 敌方减益
        NONE = CreateColor(0, 0, 0, 0),                                             -- 无
    },
    NEAR_BLACK_1 = CreateColor(15 / 255, 25 / 255, 20 / 255, 1),                    -- 接近黑色
    NEAR_BLACK_2 = CreateColor(25 / 255, 15 / 255, 20 / 255, 1),                    -- 接近黑色
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
local curve = CreateColorCurve()
curve:SetType(Enum.LuaCurveType.Linear)
curve:AddPoint(0.0, CreateColor(0, 0, 0, 1))
curve:AddPoint(1.0, CreateColor(1, 1, 1, 1))

-- 反向颜色曲线定义
local curve_reverse = CreateColorCurve()
curve_reverse:SetType(Enum.LuaCurveType.Linear)
curve_reverse:AddPoint(0.0, CreateColor(1, 1, 1, 1))
curve_reverse:AddPoint(1.0, CreateColor(0, 0, 0, 1))

-- Debuff颜色曲线定义
local debuff_curve = CreateColorCurve()
debuff_curve:AddPoint(0, COLOR.ICONS.PLAYER_DEBUFF)
debuff_curve:AddPoint(1, COLOR.ICONS.MAGIC)
debuff_curve:AddPoint(2, COLOR.ICONS.CURSE)
debuff_curve:AddPoint(3, COLOR.ICONS.DISEASE)
debuff_curve:AddPoint(4, COLOR.ICONS.POISON)
debuff_curve:AddPoint(9, COLOR.ICONS.ENRAGE)
debuff_curve:AddPoint(11, COLOR.ICONS.BLEED)


local playerbuff_curve = CreateColorCurve()
playerbuff_curve:AddPoint(0, COLOR.ICONS.PLAYER_BUFF)
playerbuff_curve:AddPoint(1, COLOR.ICONS.MAGIC)
playerbuff_curve:AddPoint(2, COLOR.ICONS.CURSE)
playerbuff_curve:AddPoint(3, COLOR.ICONS.DISEASE)
playerbuff_curve:AddPoint(4, COLOR.ICONS.POISON)
playerbuff_curve:AddPoint(9, COLOR.ICONS.ENRAGE)
playerbuff_curve:AddPoint(11, COLOR.ICONS.BLEED)

local targetdebuff_curve = CreateColorCurve()
targetdebuff_curve:AddPoint(0, COLOR.ICONS.ENEMY_DEBUFF)
targetdebuff_curve:AddPoint(1, COLOR.ICONS.MAGIC)
targetdebuff_curve:AddPoint(2, COLOR.ICONS.CURSE)
targetdebuff_curve:AddPoint(3, COLOR.ICONS.DISEASE)
targetdebuff_curve:AddPoint(4, COLOR.ICONS.POISON)
targetdebuff_curve:AddPoint(9, COLOR.ICONS.ENRAGE)
targetdebuff_curve:AddPoint(11, COLOR.ICONS.BLEED)

-- 剩余时间颜色曲线定义
local remaining_curve = CreateColorCurve()
remaining_curve:SetType(Enum.LuaCurveType.Linear)
remaining_curve:AddPoint(0.0, COLOR.C0)
remaining_curve:AddPoint(5.0, COLOR.C100)
remaining_curve:AddPoint(30.0, COLOR.C150)
remaining_curve:AddPoint(155.0, COLOR.C200)
remaining_curve:AddPoint(375.0, COLOR.C255)

-- 框架初始化函数表
local FrameInitFuncs = {}
-- 更新函数表
local OnUpdateFuncs_STD    = {}
-- 低频更新函数表
local OnUpdateFuncs_LOW = {}
-- Aura 事件更新函数表（按 unit 分发）
local OnEventFunc_Aura = {}
-- 生命上限事件更新函数表（按 unit 分发）
local OnEventFunc_MaxHealth_Player = {}
local OnEventFunc_MaxHealth_Party = {}
-- 技能图标事件更新函数表
local OnEventFunc_Spell = {}
-- 技能表，每个技能有两种显示方式："cooldown"和"charge"
addonTable.Spell     = {}
-- 添加GCD技能到技能表



-- 创建主框架
local frame = CreateFrame("Frame")

function frame:PLAYER_ENTERING_WORLD()
    C_Timer.After(0, function()
        wipe(OnUpdateFuncs_STD)
        wipe(OnUpdateFuncs_LOW)
        wipe(OnEventFunc_Aura)
        wipe(OnEventFunc_MaxHealth_Player)
        wipe(OnEventFunc_MaxHealth_Party)
        wipe(OnEventFunc_Spell)
        for _, func in ipairs(FrameInitFuncs) do
            func()
        end
    end)
    self:UnregisterEvent("PLAYER_ENTERING_WORLD")
end

function frame:UNIT_AURA(unitTarget)
    for i = 1, #OnEventFunc_Aura do
        local updaterInfo = OnEventFunc_Aura[i]
        if updaterInfo.unit == unitTarget then
            updaterInfo.func()
        end
    end
end

function frame:UNIT_MAXHEALTH(unitTarget)
    if unitTarget == "player" then
        for i = 1, #OnEventFunc_MaxHealth_Player do
            OnEventFunc_MaxHealth_Player[i]()
        end
        return
    end

    for i = 1, #OnEventFunc_MaxHealth_Party do
        local updaterInfo = OnEventFunc_MaxHealth_Party[i]
        if updaterInfo.unit == unitTarget then
            updaterInfo.func()
        end
    end
end

function frame:SPELLS_CHANGED()
    for i = 1, #OnEventFunc_Spell do
        OnEventFunc_Spell[i]()
    end
end

function frame:SPELL_UPDATE_ICON()
    self:SPELLS_CHANGED()
end

function frame:PLAYER_TALENT_UPDATE()
    self:SPELLS_CHANGED()
end

function frame:ACTIVE_TALENT_GROUP_CHANGED()
    self:SPELLS_CHANGED()
end

-- 注册事件
frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:RegisterEvent("UNIT_AURA")
frame:RegisterEvent("UNIT_MAXHEALTH")
frame:RegisterEvent("SPELLS_CHANGED")
frame:RegisterEvent("SPELL_UPDATE_ICON")
frame:RegisterEvent("PLAYER_TALENT_UPDATE")
frame:RegisterEvent("ACTIVE_TALENT_GROUP_CHANGED")
frame:SetScript("OnEvent", function(self, event, ...)
    self[event](self, ...)
end)

-- 时间流逝变量
local timeElapsed = 0
local lowFrequencyTimeElapsed = 0
-- 钩子OnUpdate脚本，用于定时更新
frame:HookScript("OnUpdate", function(self, elapsed)
    local tickOffset = 1.0 / addonTable.FPS;
    local lowFrequencyTickOffset = 1.0 / addonTable.LowFrequencyFPS;
    timeElapsed      = timeElapsed + elapsed
    lowFrequencyTimeElapsed = lowFrequencyTimeElapsed + elapsed
    if timeElapsed > tickOffset then
        timeElapsed = 0
        for _, updater in ipairs(OnUpdateFuncs_STD) do
            updater()
        end
    end
    if lowFrequencyTimeElapsed > lowFrequencyTickOffset then
        lowFrequencyTimeElapsed = 0
        for _, updater in ipairs(OnUpdateFuncs_LOW) do
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


local function CreateStandardFrame(name, parent, x, y, w, h, debugColor)
    local node_size = addonTable.nodeSize
    local frame = CreateFrame("Frame", addonName .. name, parent)
    frame:SetFrameLevel(parent:GetFrameLevel() + 1)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * node_size, -1 * y * node_size)
    frame:SetSize(w * node_size, h * node_size)
    frame:Show()
    frame.bg = frame:CreateTexture(nil, "BACKGROUND")
    frame.bg:SetAllPoints()
    if DEBUG and debugColor then
        frame.bg:SetColorTexture(debugColor:GetRGBA())
    else
        frame.bg:SetColorTexture(0, 0, 0, 1)
    end
    frame.bg:Show()
    return frame
end


-- 初始化主框架
local function InitializeMainFrame()
    -- 计算UI元素尺寸
    addonTable.nodeSize = GetUIScaleFactor(8 * scale)
    -- addonTable.innerSize = GetUIScaleFactor(8 * scale)
    addonTable.padSize = GetUIScaleFactor(1 * scale)
    addonTable.fontSize = GetUIScaleFactor(6 * scale)
    addonTable.footnoteSize = GetUIScaleFactor(2 * scale)

    -- 创建主框架
    addonTable.MainFrame = CreateFrame("Frame", addonName .. "MainFrame", UIParent)
    addonTable.MainFrame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", 0, 0)
    addonTable.MainFrame:SetSize(addonTable.nodeSize * 52, addonTable.nodeSize * 18)
    addonTable.MainFrame:SetFrameStrata("TOOLTIP")
    addonTable.MainFrame:SetFrameLevel(900)
    addonTable.MainFrame:Show()

    -- 创建主框架背景
    addonTable.MainFrame.bg = addonTable.MainFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MainFrame.bg:SetAllPoints()
    addonTable.MainFrame.bg:SetColorTexture(0, 0, 0, 1)
    addonTable.MainFrame.bg:Show()

    -- 定义调试颜色
    local debugColors = {
        blue = CreateColor(91 / 255, 155 / 255, 213 / 255, 1),
        yellow = CreateColor(255 / 255, 192 / 255, 0 / 255, 1),
        gray = CreateColor(165 / 255, 165 / 255, 165 / 255, 1),
        orange = CreateColor(237 / 255, 125 / 255, 49 / 255, 1),
        green = CreateColor(84 / 255, 130 / 255, 53 / 255, 1),
        lightGreen = CreateColor(112 / 255, 173 / 255, 71 / 255, 1),
    }
    addonTable.PlayerSpellFrame = CreateStandardFrame("PlayerSpellFrame", addonTable.MainFrame, 2, 2, 36, 3, debugColors.green)
    -- 使用CreateStandardFrame创建子框架
    addonTable.PlayerBuffFrame = CreateStandardFrame("PlayerBuffFrame", addonTable.MainFrame, 2, 5, 32, 3, debugColors.blue)
    addonTable.PlayerDebuffFrame = CreateStandardFrame("PlayerDebuffFrame", addonTable.MainFrame, 2, 8, 8, 3, debugColors.yellow)
    addonTable.TargetDebuffFrame = CreateStandardFrame("TargetDebuffFrame", addonTable.MainFrame, 10, 8, 16, 3, debugColors.orange)
    addonTable.FocusDebuffFrame = CreateStandardFrame("FocusDebuffFrame", addonTable.MainFrame, 26, 8, 8, 3, debugColors.lightGreen)
    addonTable.PlayerStatusFrame = CreateStandardFrame("PlayerStatusFrame", addonTable.MainFrame, 38, 2, 8, 4, debugColors.gray)
    addonTable.TargetStatusFrame = CreateStandardFrame("TargetStatusFrame", addonTable.MainFrame, 38, 6, 8, 2, debugColors.blue)
    addonTable.FocusStatusFrame = CreateStandardFrame("FocusStatusFrame", addonTable.MainFrame, 38, 8, 8, 2, debugColors.yellow)
    addonTable.MiscFrame = CreateStandardFrame("MiscFrame", addonTable.MainFrame, 34, 5, 4, 3, debugColors.orange)
    addonTable.SpecFrame = CreateStandardFrame("SpecFrame", addonTable.MainFrame, 34, 8, 4, 3, debugColors.lightGreen)
    addonTable.SignalFrame = CreateStandardFrame("SignalFrame", addonTable.MainFrame, 38, 10, 8, 1, debugColors.blue)
    addonTable.FooterFrane = CreateStandardFrame("FooterFrane", addonTable.MainFrame, 3, 17, 46, 1, debugColors.blue)

    -- 创建队伍框架
    local partyDebugColor = CreateColor(127 / 255, 127 / 255, 127 / 255, 1)
    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)
        addonTable["PartyFrame" .. UnitKey] = CreateStandardFrame("PartyFrame" .. UnitKey, addonTable.MainFrame, 12 * i - 10, 11, 12, 5, partyDebugColor)
    end

    -- 创建方块函数
    local function create_square(x, y, color)
        local node_size = addonTable.nodeSize
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
    create_square(50, 16, COLOR.NEAR_BLACK_1)
    create_square(50, 17, COLOR.NEAR_BLACK_2)
    create_square(51, 16, COLOR.NEAR_BLACK_2)
    create_square(51, 17, COLOR.NEAR_BLACK_1)

    logging("MainFrame created")
end

-- 将初始化主框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeMainFrame)

-- 创建像素节点
local function CreatePixelNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    local nodeFrame = CreateFrame("Frame", addonName .. "Pixel" .. title, parent_frame)
    nodeFrame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size, -y * node_size)
    nodeFrame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    nodeFrame:SetSize(node_size, node_size)
    nodeFrame:Show()
    local nodeTexture = nodeFrame:CreateTexture(nil, "BACKGROUND")
    nodeTexture:SetAllPoints(nodeFrame)
    nodeTexture:SetColorTexture(0, 0, 0, 1)
    nodeTexture:Show()
    return nodeTexture
end
-- 一个包含四个小像素的节点。
local function CreateMixedNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    -- 主节点
    local main_frame = CreateFrame("Frame", addonName .. "Pixel" .. title, parent_frame)
    main_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size, -y * node_size)
    main_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    main_frame:SetSize(node_size, node_size)
    main_frame:Show()
    -- 左上节点
    local TOPLEFT_Frame = CreateFrame("Frame", addonName .. title .. "PixelTOPLEFT", main_frame)
    TOPLEFT_Frame:SetPoint("TOPLEFT", main_frame, "TOPLEFT", 0, 0)
    TOPLEFT_Frame:SetFrameLevel(main_frame:GetFrameLevel() + 1)
    TOPLEFT_Frame:SetSize(node_size / 2, node_size / 2)
    TOPLEFT_Frame:Show()
    local TOPLEFT_Texture = TOPLEFT_Frame:CreateTexture(nil, "BACKGROUND")
    TOPLEFT_Texture:SetAllPoints(TOPLEFT_Frame)
    TOPLEFT_Texture:SetColorTexture(0, 0, 0, 1)
    TOPLEFT_Texture:Show()

    -- 右上节点
    local TOPRIGHT_Frame = CreateFrame("Frame", addonName .. "PixelTOPRIGHT" .. title, main_frame)
    TOPRIGHT_Frame:SetPoint("TOPRIGHT", main_frame, "TOPRIGHT", 0, 0)
    TOPRIGHT_Frame:SetFrameLevel(main_frame:GetFrameLevel() + 1)
    TOPRIGHT_Frame:SetSize(node_size / 2, node_size / 2)
    TOPRIGHT_Frame:Show()
    local TOPRIGHT_Texture = TOPRIGHT_Frame:CreateTexture(nil, "BACKGROUND")
    TOPRIGHT_Texture:SetAllPoints(TOPRIGHT_Frame)
    TOPRIGHT_Texture:SetColorTexture(0, 0, 0, 1)
    TOPRIGHT_Texture:Show()

    -- 左下节点
    local BOTTOMLEFT_Frame = CreateFrame("Frame", addonName .. "PixelBOTTOMLEFT" .. title, main_frame)
    BOTTOMLEFT_Frame:SetPoint("BOTTOMLEFT", main_frame, "BOTTOMLEFT", 0, 0)
    BOTTOMLEFT_Frame:SetFrameLevel(main_frame:GetFrameLevel() + 1)
    BOTTOMLEFT_Frame:SetSize(node_size / 2, node_size / 2)
    BOTTOMLEFT_Frame:Show()
    local BOTTOMLEFT_Texture = BOTTOMLEFT_Frame:CreateTexture(nil, "BACKGROUND")
    BOTTOMLEFT_Texture:SetAllPoints(BOTTOMLEFT_Frame)
    BOTTOMLEFT_Texture:SetColorTexture(0, 0, 0, 1)
    BOTTOMLEFT_Texture:Show()

    -- 右下节点
    local BOTTOMRIGHT_Frame = CreateFrame("Frame", addonName .. "PixelBOTTOMRIGHT" .. title, main_frame)
    BOTTOMRIGHT_Frame:SetPoint("BOTTOMRIGHT", main_frame, "BOTTOMRIGHT", 0, 0)
    BOTTOMRIGHT_Frame:SetFrameLevel(main_frame:GetFrameLevel() + 1)
    BOTTOMRIGHT_Frame:SetSize(node_size / 2, node_size / 2)
    BOTTOMRIGHT_Frame:Show()
    local BOTTOMRIGHT_Texture = BOTTOMRIGHT_Frame:CreateTexture(nil, "BACKGROUND")
    BOTTOMRIGHT_Texture:SetAllPoints(BOTTOMRIGHT_Frame)
    BOTTOMRIGHT_Texture:SetColorTexture(0, 0, 0, 1)
    BOTTOMRIGHT_Texture:Show()

    if DEBUG then
        TOPLEFT_Texture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        TOPRIGHT_Texture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        BOTTOMLEFT_Texture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        BOTTOMRIGHT_Texture:SetColorTexture(math.random(), math.random(), math.random(), 1)
    end
    return TOPLEFT_Texture, TOPRIGHT_Texture, BOTTOMLEFT_Texture, BOTTOMRIGHT_Texture
end


-- 一个包含角标的节点
local function CreateFootnoteNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    local footnoteSize = addonTable.footnoteSize
    -- 主节点
    local main_frame = CreateFrame("Frame", addonName .. "Pixel" .. title, parent_frame)
    main_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size, -y * node_size)
    main_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    main_frame:SetSize(node_size, node_size)
    main_frame:Show()
    -- 主节点的图标
    local main_Texture = main_frame:CreateTexture(nil, "BACKGROUND")
    main_Texture:SetAllPoints(main_frame)
    main_Texture:SetColorTexture(0, 0, 0, 1)
    main_Texture:Show()

    local fn_frame = CreateFrame("Frame", addonName .. "PixelFootnote" .. title, main_frame)
    fn_frame:SetPoint("BOTTOMRIGHT", main_frame, "BOTTOMRIGHT", 0, 0)
    fn_frame:SetFrameLevel(main_frame:GetFrameLevel() + 2)
    fn_frame:SetSize(footnoteSize, footnoteSize)
    fn_frame:Show()
    local fn_Texture = fn_frame:CreateTexture(nil, "BACKGROUND")
    fn_Texture:SetAllPoints(fn_frame)
    fn_Texture:SetColorTexture(0, 0, 0, 0)
    fn_Texture:Show()

    if DEBUG then
        main_Texture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        fn_Texture:SetColorTexture(math.random(), math.random(), math.random(), 1)
    end
    return main_Texture, fn_Texture
end


-- 创建文字节点
local function CreateStringNode(x, y, title, parent_frame)
    local node_size = addonTable.nodeSize
    local padSize = addonTable.padSize
    local fontSize = addonTable.fontSize
    local nodeFrame = CreateFrame("Frame", addonName .. "String" .. title, parent_frame)
    nodeFrame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", x * node_size, -y * node_size)
    nodeFrame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
    nodeFrame:SetSize(node_size, node_size)
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
    logging("CreateAuraSequence[" .. unit .. "][" .. filter .. "]")
    sortRule = sortRule or Enum.UnitAuraSortRule.Default
    sortDirection = sortDirection or Enum.UnitAuraSortDirection.Normal

    local start_idx, end_idx = string.find(filter, "HELPFUL")
    local isBuff = false
    local isDebuff = false
    if start_idx then
        isBuff = true
    else
        isDebuff = true
    end


    local auraTextures = {}

    -- 创建光环序列元素
    for i = 1, maxCount do
        local iconTexture, fnTexture = CreateFootnoteNode((i - 1), 0, addonName .. name_prefix .. "IconFrame" .. i, parent)
        local durationTexture, dispelTexture, foreverTexture, _ = CreateMixedNode((i - 1), 1, addonName .. name_prefix .. "DurationFrame" .. i, parent)

        local countString = CreateStringNode((i - 1), 2, addonName .. name_prefix .. "CountFrame" .. i, parent)
        table.insert(auraTextures, {
            icon = iconTexture,
            dispel = dispelTexture,
            duration = durationTexture,
            count = countString,
            fn = fnTexture,
            forever = foreverTexture
        })
    end

    local previousDisplayCount = 0
    local previousAuraInstanceIDs = {}

    local function wipeTexture(index)
        local tex = auraTextures[index]
        tex.icon:SetColorTexture(0, 0, 0, 1)
        tex.duration:SetColorTexture(0, 0, 0, 1)
        tex.count:SetText("")
        tex.dispel:SetColorTexture(0, 0, 0, 1)
        tex.fn:SetColorTexture(0, 0, 0, 0)
        tex.forever:SetColorTexture(0, 0, 0, 1)
        previousAuraInstanceIDs[index] = nil
    end

    -- 清除纹理函数
    local function wipeTextures()
        for i = 1, maxCount do
            wipeTexture(i)
        end
        previousDisplayCount = 0
    end

    -- 更新纹理函数
    local function UpdateStatus_event_UNIT_AURA()
        if not UnitExists(unit) then
            if previousDisplayCount > 0 then
                for i = 1, previousDisplayCount do
                    wipeTexture(i)
                end
                previousDisplayCount = 0
            end
            return
        end

        local isEnemy = UnitIsEnemy("player", unit)
        local isPlayer = not isEnemy
        local auraInstanceIDs = GetUnitAuraInstanceIDs(unit, filter, maxCount, sortRule, sortDirection) or {}
        local displayIndex = 0
        for i = 1, #auraInstanceIDs do
            local auraInstanceID = auraInstanceIDs[i]
            local aura = GetAuraDataByAuraInstanceID(unit, auraInstanceID)
            if aura ~= nil then
                displayIndex = displayIndex + 1
                local auraTexture = auraTextures[displayIndex]
                local isSlotChanged = previousAuraInstanceIDs[displayIndex] ~= auraInstanceID
                previousAuraInstanceIDs[displayIndex] = auraInstanceID

                local duration = GetAuraDuration(unit, auraInstanceID)
                local foreverBoolen = DoesAuraHaveExpirationTime(unit, auraInstanceID)
                local count = GetAuraApplicationDisplayCount(unit, auraInstanceID, 1, 9)

                if isSlotChanged then
                    auraTexture.icon:SetTexture(aura.icon, "CLAMPTOBLACK", "CLAMPTOBLACK")
                end
                auraTexture.count:SetText(count)

                if duration ~= nil then
                    local result = duration:EvaluateRemainingDuration(remaining_curve)
                    auraTexture.duration:SetColorTexture(result:GetRGBA())
                else
                    auraTexture.duration:SetColorTexture(COLOR.BLACK:GetRGBA())
                end

                if foreverBoolen ~= nil then
                    local foreverColor = EvaluateColorFromBoolean(foreverBoolen, COLOR.BLACK, COLOR.WHITE) -- 白色是永久buff
                    auraTexture.forever:SetColorTexture(foreverColor:GetRGBA())
                else
                    auraTexture.forever:SetColorTexture(COLOR.BLACK:GetRGBA())
                end

                if isPlayer and isDebuff then
                    local dispelTypeColor = GetAuraDispelTypeColor(unit, auraInstanceID, debuff_curve)
                    auraTexture.fn:SetColorTexture(dispelTypeColor:GetRGBA())
                    auraTexture.dispel:SetColorTexture(dispelTypeColor:GetRGBA())
                end
                if isPlayer and isBuff then
                    local dispelTypeColor = GetAuraDispelTypeColor(unit, auraInstanceID, playerbuff_curve)
                    auraTexture.fn:SetColorTexture(COLOR.ICONS.PLAYER_BUFF:GetRGBA())
                    auraTexture.dispel:SetColorTexture(dispelTypeColor:GetRGBA())
                end
                if isEnemy and isDebuff then
                    local dispelTypeColor = GetAuraDispelTypeColor(unit, auraInstanceID, targetdebuff_curve)
                    auraTexture.fn:SetColorTexture(COLOR.ICONS.ENEMY_DEBUFF:GetRGBA())
                    auraTexture.dispel:SetColorTexture(dispelTypeColor:GetRGBA())
                end
            end
        end

        if displayIndex < previousDisplayCount then
            for i = displayIndex + 1, previousDisplayCount do
                wipeTexture(i)
            end
        end
        previousDisplayCount = displayIndex
    end

    local function UpdateStatus_freq_std()
        if previousDisplayCount == 0 then
            return
        end
        if not UnitExists(unit) then
            return
        end

        for i = 1, previousDisplayCount do
            local auraTexture = auraTextures[i]
            local auraInstanceID = previousAuraInstanceIDs[i]
            if auraInstanceID then
                local duration = GetAuraDuration(unit, auraInstanceID)
                if duration ~= nil then
                    local result = duration:EvaluateRemainingDuration(remaining_curve)
                    auraTexture.duration:SetColorTexture(result:GetRGBA())
                else
                    auraTexture.duration:SetColorTexture(COLOR.BLACK:GetRGBA())
                end
            else
                auraTexture.duration:SetColorTexture(COLOR.BLACK:GetRGBA())
            end
        end
    end

    wipeTextures()
    UpdateStatus_event_UNIT_AURA()
    table.insert(OnEventFunc_Aura, { unit = unit, func = UpdateStatus_event_UNIT_AURA })
    table.insert(OnUpdateFuncs_STD, UpdateStatus_freq_std)
    logging("CreateAuraSequence[" .. unit .. "]...Done")
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


-- 初始化光环框架
local function InitializeAuraFrame()
    logging("InitializeAuraFrame")
    CreateAuraSequence("player", "HELPFUL", 32, "PlayerBuff", addonTable.PlayerBuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("player", "HARMFUL", 8, "PlayerDebuff", addonTable.PlayerDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("target", "HARMFUL|PLAYER", 16, "TargetDebuff", addonTable.TargetDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)
    CreateAuraSequence("focus", "HARMFUL|PLAYER", 8, "FocusDebuff", addonTable.FocusDebuffFrame, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal)

    logging("InitializeAuraFrame...Done")
end

-- 将初始化光环框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeAuraFrame)

-- 初始化玩家状态框架
local function InitializePlayerStatusFrame()
    logging("InitializePlayerStatusFrame")
    local x = 0
    local y = 2
    local player_in_combat = CreatePixelNode(x, y, "PlayerInCombat", addonTable.PlayerStatusFrame)
    x = 1
    local player_is_moving = CreatePixelNode(x, y, "PlayerIsMoving", addonTable.PlayerStatusFrame)
    x = 2
    local player_in_vehicle = CreatePixelNode(x, y, "PlayerInVehicle", addonTable.PlayerStatusFrame)
    x = 3
    local player_is_empowered = CreatePixelNode(x, y, "PlayerIsEmpowered", addonTable.PlayerStatusFrame)
    x = 4
    local player_cast_icon, player_cast_fn = CreateFootnoteNode(x, y, "PlayerCastIcon", addonTable.PlayerStatusFrame)
    x = 5
    local player_cast_duration = CreatePixelNode(x, y, "PlayerCastDuration", addonTable.PlayerStatusFrame)
    y = 3
    x = 0
    local player_class = CreatePixelNode(x, y, "PlayerClass", addonTable.PlayerStatusFrame)
    x = 1
    local player_role = CreatePixelNode(x, y, "PlayerRole", addonTable.PlayerStatusFrame)
    x = 2
    local player_deaded = CreatePixelNode(x, y, "PlayerDeaded", addonTable.PlayerStatusFrame)
    x = 4
    local player_channel_icon, player_channel_fn = CreateFootnoteNode(x, y, "PlayerChannelIcon", addonTable.PlayerStatusFrame)
    x = 5
    local player_channel_duration = CreatePixelNode(x, y, "PlayerChannelDuration", addonTable.PlayerStatusFrame)


    y = 2
    x = 7
    local player_health = CreatePixelNode(x, y, "PlayerHealth", addonTable.PlayerStatusFrame)
    y = 3
    local player_power = CreatePixelNode(x, y, "PlayerPower", addonTable.PlayerStatusFrame)
    local powerType, _, _, _, _ = UnitPowerType("player")

    local PlayerDamageAbsorbsBar = CreateWhiteBar("PlayerDamageAbsorbsBar", addonTable.PlayerStatusFrame, 0, 0, 8, 1)
    local PlayerHealAbsorbsBar = CreateWhiteBar("PlayerHealAbsorbsBar", addonTable.PlayerStatusFrame, 0, 1, 8, 1)

    local function RegisterPlayerMaxHealthUpdateFunc(updater)
        table.insert(OnEventFunc_MaxHealth_Player, updater)
    end

    local function UpdateStatus_event_UNIT_MAXHEALTH()
        local maxHealth = UnitHealthMax("player")
        PlayerDamageAbsorbsBar:SetMinMaxValues(0, maxHealth)
        PlayerHealAbsorbsBar:SetMinMaxValues(0, maxHealth)
    end

    local function UpdateStatusStandard_freq_low()
        local _, classFilename, _ = UnitClass("player")
        if classFilename then
            player_class:SetColorTexture(COLOR.CLASS[classFilename]:GetRGBA())
        else
            player_class:SetColorTexture(0, 0, 0, 1)
        end
        local role = UnitGroupRolesAssigned("player")
        local roleColor = COLOR.ROLE[role] or COLOR.ROLE.NONE
        player_role:SetColorTexture(roleColor:GetRGBA())
    end

    -- 更新玩家状态函数
    local function UpdateStatus_freq_std()
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
            player_cast_fn:SetColorTexture(COLOR.ICONS.PLAYER_SPELL:GetRGBA())
        else
            player_cast_icon:SetColorTexture(0, 0, 0, 1)
            player_cast_duration:SetColorTexture(0, 0, 0, 1)
            player_cast_fn:SetColorTexture(0, 0, 0, 0)
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
            player_channel_fn:SetColorTexture(COLOR.ICONS.PLAYER_SPELL:GetRGBA())
        else
            player_channel_icon:SetColorTexture(0, 0, 0, 1)
            player_channel_duration:SetColorTexture(0, 0, 0, 1)
            player_channel_fn:SetColorTexture(0, 0, 0, 0)
        end

        if UnitIsDeadOrGhost("player") then
            player_deaded:SetColorTexture(1, 1, 1, 1)
        else
            player_deaded:SetColorTexture(0, 0, 0, 1)
        end

        PlayerDamageAbsorbsBar:SetValue(UnitGetTotalAbsorbs("player"))

        PlayerHealAbsorbsBar:SetValue(UnitGetTotalHealAbsorbs("player"))

        player_health:SetColorTexture(UnitHealthPercent("player", true, curve):GetRGBA())
        player_power:SetColorTexture(UnitPowerPercent("player", powerType, true, curve):GetRGBA())
    end
    UpdateStatus_event_UNIT_MAXHEALTH()
    RegisterPlayerMaxHealthUpdateFunc(UpdateStatus_event_UNIT_MAXHEALTH)
    UpdateStatusStandard_freq_low()
    table.insert(OnUpdateFuncs_LOW, UpdateStatusStandard_freq_low)
    table.insert(OnUpdateFuncs_STD, UpdateStatus_freq_std)
    logging("InitializePlayerStatusFrame...Done")
end

-- 将初始化玩家状态框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializePlayerStatusFrame)

-- 初始化技能框架
local function InitializeSpellFrame()
    logging("InitializeSpellFrame")
    table.insert(addonTable.Spell, { spellID = 61304, type = "cooldown" })

    local cooldownInfos = {}

    local cooldownIDs = GetCooldownViewerCategorySet(Enum.CooldownViewerCategory.Essential, true)
    for _, v in ipairs(GetCooldownViewerCategorySet(Enum.CooldownViewerCategory.Utility, true)) do
        table.insert(cooldownIDs, v)
    end
    for i = 1, #cooldownIDs do
        local cooldownID = cooldownIDs[i]
        local cooldownInfo = GetCooldownViewerCooldownInfo(cooldownID)
        table.insert(cooldownInfos, cooldownInfo)
    end

    --[[
    table.sort(cooldownInfos, function(a, b)
        -- true 排在 false 前面
        if a.isKnown ~= b.isKnown then
            return a.isKnown -- 当a为true且b为false时返回true
        end
        -- 如果isKnown相同，可以按其他字段排序，这里保持任意顺序
        return false
    end)

    ]]

    for i = #cooldownInfos, 1, -1 do
        local cooldownInfo = cooldownInfos[i]
        if (not cooldownInfo) or (not cooldownInfo.isKnown) then
            table.remove(cooldownInfos, i)
        end
    end

    for i = 1, #cooldownInfos do
        local cooldownInfo = cooldownInfos[i]
        if cooldownInfo.charges then
            table.insert(addonTable.Spell, { spellID = cooldownInfo.spellID, type = "charge" })
        else
            table.insert(addonTable.Spell, { spellID = cooldownInfo.spellID, type = "cooldown" })
        end
    end


    local MaxFrame = math.min(36, #addonTable.Spell)
    local spellTextrues = {}

    for i = 1, #addonTable.Spell do
        local SpellID = addonTable.Spell[i].spellID
        local spellLink = GetSpellLink(SpellID)
        logging("技能冷却[" .. i .. "]" .. spellLink .. ",类型:" .. addonTable.Spell[i].type)
    end


    -- 创建技能框架元素
    for i = 1, 36 do
        local iconTexture, fnTexture = CreateFootnoteNode(i - 1, 0, "SpellIconFrame" .. i, addonTable.PlayerSpellFrame)
        local cooldownTexture, usableTexture, highlightTexture, knownTexture = CreateMixedNode(i - 1, 1, "SpellMiscFrame" .. i, addonTable.PlayerSpellFrame)

        local charge_string = CreateStringNode(i - 1, 2, "SpellChargeFrame" .. i, addonTable.PlayerSpellFrame)

        table.insert(spellTextrues, {
            fn = fnTexture,
            icon = iconTexture,
            cooldown = cooldownTexture,
            usable = usableTexture,
            highlight = highlightTexture,
            charge = charge_string,
            known = knownTexture
        })
    end


    -- 更新节点纹理函数
    local function UpdateStatus_event_SPELLS_CHANGED()
        for i = 1, MaxFrame do
            local SpellID = addonTable.Spell[i].spellID
            local spellTex = spellTextrues[i]
            local iconID = GetSpellTexture(SpellID)
            if iconID then
                spellTex.icon:SetTexture(iconID)
                spellTex.fn:SetColorTexture(COLOR.ICONS.PLAYER_SPELL:GetRGBA())
            else
                spellTex.icon:SetColorTexture(0, 0, 0, 1)
                spellTex.fn:SetColorTexture(0, 0, 0, 0)
            end
        end
    end

    local function UpdateStatus_freq_std()
        for i = 1, MaxFrame do
            local SpellID = addonTable.Spell[i].spellID
            local spellTex = spellTextrues[i]


            -- spellTex.cooldown:SetColorTexture(cd_remaining:GetRGBA())
            if addonTable.Spell[i].type == "charge" then
                local duration = GetSpellChargeDuration(SpellID)
                local result = duration:EvaluateRemainingDuration(remaining_curve)
                spellTex.cooldown:SetColorTexture(result:GetRGBA())

                local chargeInfo = GetSpellCharges(SpellID)
                spellTex.charge:SetText(tostring(chargeInfo.currentCharges))
            else
                local duration = GetSpellCooldownDuration(SpellID)
                local result = duration:EvaluateRemainingDuration(remaining_curve)
                spellTex.cooldown:SetColorTexture(result:GetRGBA())
            end

            local isSpellOverlayed = IsSpellOverlayed(SpellID)
            -- print(isSpellOverlayed)
            local highlightValue = EvaluateColorFromBoolean(isSpellOverlayed, COLOR.WHITE, COLOR.BLACK) -- 高亮是
            spellTex.highlight:SetColorTexture(highlightValue:GetRGBA())

            local isUsable, insufficientPower = IsSpellUsable(SpellID)
            local usableValue = EvaluateColorFromBoolean(isUsable, COLOR.WHITE, COLOR.BLACK) -- 无法使用时是黑色，可用是白色。
            spellTex.usable:SetColorTexture(usableValue:GetRGBA())
        end
    end

    local function UpdateStatusStandard_freq_low()
        for i = 1, MaxFrame do
            local SpellID = addonTable.Spell[i].spellID
            local spellTex = spellTextrues[i]
            local isKnown = IsSpellInSpellBook(SpellID)
            local knownValue = EvaluateColorFromBoolean(isKnown, COLOR.WHITE, COLOR.BLACK) -- 不知道时是黑色，会这个技能是白色
            spellTex.known:SetColorTexture(knownValue:GetRGBA())
        end
    end
    UpdateStatus_event_SPELLS_CHANGED()
    table.insert(OnEventFunc_Spell, UpdateStatus_event_SPELLS_CHANGED)
    UpdateStatusStandard_freq_low()
    table.insert(OnUpdateFuncs_LOW, UpdateStatusStandard_freq_low)
    table.insert(OnUpdateFuncs_STD, UpdateStatus_freq_std)
    logging("InitializeSpellFrame...Done")
end

-- 将初始化技能框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeSpellFrame)

-- 初始化队伍框架
local function InitializePartyFrame()
    logging("InitializePartyFrame")
    local node_size = addonTable.nodeSize

    local function RegisterPartyMaxHealthUpdateFunc(unit, updater)
        table.insert(OnEventFunc_MaxHealth_Party, { unit = unit, func = updater })
    end

    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)
        local parent_frame = addonTable["PartyFrame" .. UnitKey]
        local frame_pre = addonName .. "PartyFrame" .. UnitKey

        -- 创建队伍Debuff框架
        local debuff_frame = CreateFrame("Frame", frame_pre .. "DebuffFrame", parent_frame)
        debuff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        debuff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, 0)
        debuff_frame:SetSize(node_size * 6, node_size * 3)
        debuff_frame:Show()
        CreateAuraSequence(UnitKey, "HARMFUL", 6, UnitKey .. "Debuff", debuff_frame, Enum.UnitAuraSortRule.Default, Enum.UnitAuraSortDirection.Normal)


        -- 创建队伍Buff框架
        local buff_frame = CreateFrame("Frame", frame_pre .. "BuffFrame", parent_frame)
        buff_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        buff_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 6 * node_size, 0)
        buff_frame:SetSize(node_size * 6, node_size * 3)
        buff_frame:Show()
        CreateAuraSequence(UnitKey, "HELPFUL|PLAYER", 7, UnitKey .. "Buff", buff_frame, Enum.UnitAuraSortRule.Default, Enum.UnitAuraSortDirection.Normal)


        -- 创建队伍条框架
        local bar_frame = CreateFrame("Frame", frame_pre .. "BarFrame", parent_frame)
        bar_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        bar_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 0, -3 * node_size)
        bar_frame:SetSize(node_size * 8, node_size * 2)
        bar_frame:Show()

        -- 创建队伍状态框架
        local status_frame = CreateFrame("Frame", frame_pre .. "StatusFrame", parent_frame)
        status_frame:SetFrameLevel(parent_frame:GetFrameLevel() + 1)
        status_frame:SetPoint("TOPLEFT", parent_frame, "TOPLEFT", 8 * node_size, -3 * node_size)
        status_frame:SetSize(node_size * 4, node_size * 2)
        status_frame:Show()

        -- 创建队伍状态节点
        local unit_exist = CreatePixelNode(0, 0, addonName .. "PartyExist" .. i, status_frame)
        local unit_in_range = CreatePixelNode(1, 0, addonName .. "PartyInRange" .. i, status_frame)
        local unit_health = CreatePixelNode(2, 0, addonName .. "PartyHealth" .. i, status_frame)
        local unit_class = CreatePixelNode(0, 1, addonName .. "PartyClass" .. i, status_frame)
        local unit_role = CreatePixelNode(1, 1, addonName .. "PartyRole" .. i, status_frame)
        local unit_select = CreatePixelNode(2, 1, addonName .. "PartySelect" .. i, status_frame)

        -- 创建队伍吸收条
        local DamageAbsorbsBar = CreateWhiteBar(UnitKey .. "DamageAbsorbsBar", bar_frame, 0, 0, 8, 1)
        local HealAbsorbsBar = CreateWhiteBar(UnitKey .. "HealAbsorbsBar", bar_frame, 0, 1, 8, 1)

        local function UpdateStatus_event_UNIT_MAXHEALTH()
            if UnitExists(UnitKey) then
                local maxHealth = UnitHealthMax(UnitKey)
                DamageAbsorbsBar:SetMinMaxValues(0, maxHealth)
                HealAbsorbsBar:SetMinMaxValues(0, maxHealth)
            else
                DamageAbsorbsBar:SetMinMaxValues(0, 100)
                HealAbsorbsBar:SetMinMaxValues(0, 100)
            end
        end

        -- 更新队伍框架函数
        local function UpdateStatus_freq_std()
            if UnitExists(UnitKey) then
                -- 检查是否存在
                unit_exist:SetColorTexture(1, 1, 1, 1)
                unit_health:SetColorTexture(UnitHealthPercent(UnitKey, true, curve):GetRGBA())

                if UnitIsUnit("target", UnitKey) then
                    unit_select:SetColorTexture(1, 1, 1, 1)
                else
                    unit_select:SetColorTexture(0, 0, 0, 1)
                end

                DamageAbsorbsBar:SetValue(UnitGetTotalAbsorbs(UnitKey))

                HealAbsorbsBar:SetValue(UnitGetTotalHealAbsorbs(UnitKey))
            else
                unit_exist:SetColorTexture(0, 0, 0, 1)
                unit_in_range:SetColorTexture(0, 0, 0, 1)
                unit_health:SetColorTexture(0, 0, 0, 1)
                unit_select:SetColorTexture(0, 0, 0, 1)

                DamageAbsorbsBar:SetValue(0)
                HealAbsorbsBar:SetValue(0)
            end
        end

        local function UpdateStatusStandard_freq_low()
            if UnitExists(UnitKey) then
                local _, maxRange = LibRangeCheck:GetRange(UnitKey)
                if maxRange and (maxRange <= addonTable.RangeCheck) then
                    unit_in_range:SetColorTexture(1, 1, 1, 1)
                else
                    unit_in_range:SetColorTexture(0, 0, 0, 1)
                end
                local _, classFilename, _ = UnitClass(UnitKey)
                if classFilename then
                    unit_class:SetColorTexture(COLOR.CLASS[classFilename]:GetRGBA())
                else
                    unit_class:SetColorTexture(0, 0, 0, 1)
                end
                local role = UnitGroupRolesAssigned(UnitKey)
                local roleColor = COLOR.ROLE[role] or COLOR.ROLE.NONE
                unit_role:SetColorTexture(roleColor:GetRGBA())
            else
                unit_in_range:SetColorTexture(0, 0, 0, 1)
                unit_class:SetColorTexture(0, 0, 0, 1)
                unit_role:SetColorTexture(0, 0, 0, 1)
            end
        end

        UpdateStatus_event_UNIT_MAXHEALTH()
        RegisterPartyMaxHealthUpdateFunc(UnitKey, UpdateStatus_event_UNIT_MAXHEALTH)
        UpdateStatusStandard_freq_low()
        table.insert(OnUpdateFuncs_LOW, UpdateStatusStandard_freq_low)
        table.insert(OnUpdateFuncs_STD, UpdateStatus_freq_std)
    end
    logging("InitializePartyFrame...Done")
end

-- 将初始化队伍框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializePartyFrame)

-- 初始化单位状态框架
local function InitializeUnitStatusFrame(unit, parent)
    logging("InitializeUnitStatusFrame[" .. unit .. "]")
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
    local unit_cast_icon, unit_cast_fn = CreateFootnoteNode(x, y, unit .. "CastIcon", parent)
    x = 1
    local unit_cast_duration = CreatePixelNode(x, y, unit .. "CastDuration", parent)
    x = 2
    local unit_cast_interruptible = CreatePixelNode(x, y, unit .. "CastInterruptible", parent)
    x = 3
    local unit_channel_icon, unit_channel_fn = CreateFootnoteNode(x, y, unit .. "ChannelIcon", parent)
    x = 4
    local unit_channel_duration = CreatePixelNode(x, y, unit .. "ChannelDuration", parent)
    x = 5
    local unit_channel_interruptible = CreatePixelNode(x, y, unit .. "ChannelInterruptible", parent)

    -- 更新单位状态函数
    local function UpdateStatus_freq_std()
        if UnitExists(unit) then
            unit_exist:SetColorTexture(1, 1, 1, 1)
            local can_attack = UnitCanAttack("player", unit) and UnitIsEnemy("player", unit)
            if can_attack then
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

            local _, _, CastTextureID, _, _, _, _, CastNotInterruptible, _, _ = UnitCastingInfo(unit)
            if CastTextureID then
                unit_cast_icon:SetTexture(CastTextureID)
                unit_cast_interruptible:SetColorTexture(EvaluateColorFromBoolean(CastNotInterruptible, COLOR.BLACK, COLOR.WHITE):GetRGBA())
                local duration = UnitCastingDuration(unit)
                local result = duration:EvaluateElapsedPercent(curve)
                unit_cast_duration:SetColorTexture(result:GetRGBA())
                if can_attack then
                    unit_cast_fn:SetColorTexture(EvaluateColorFromBoolean(CastNotInterruptible, COLOR.ICONS.ENEMY_SPELL_NOT_INTERRUPTIBLE, COLOR.ICONS.ENEMY_SPELL_INTERRUPTIBLE):GetRGBA())
                else
                    unit_cast_fn:SetColorTexture(COLOR.ICONS.PLAYER_SPELL:GetRGBA())
                end
            else
                unit_cast_icon:SetColorTexture(0, 0, 0, 1)
                unit_cast_duration:SetColorTexture(0, 0, 0, 1)
                unit_cast_interruptible:SetColorTexture(0, 0, 0, 1)
                unit_cast_fn:SetColorTexture(0, 0, 0, 0)
            end
            local _, _, textureID, _, _, _, ChannelNotInterruptible = UnitChannelInfo(unit)
            if textureID then
                unit_channel_icon:SetTexture(textureID)
                unit_channel_interruptible:SetColorTexture(EvaluateColorFromBoolean(ChannelNotInterruptible, COLOR.BLACK, COLOR.WHITE):GetRGBA())
                local duration = UnitChannelDuration(unit)
                local result = duration:EvaluateElapsedPercent(curve)
                unit_channel_duration:SetColorTexture(result:GetRGBA())
                if can_attack then
                    unit_channel_fn:SetColorTexture(EvaluateColorFromBoolean(ChannelNotInterruptible, COLOR.ICONS.ENEMY_SPELL_NOT_INTERRUPTIBLE, COLOR.ICONS.ENEMY_SPELL_INTERRUPTIBLE):GetRGBA())
                else
                    unit_channel_fn:SetColorTexture(COLOR.ICONS.PLAYER_SPELL:GetRGBA())
                end
            else
                unit_channel_icon:SetColorTexture(0, 0, 0, 1)
                unit_channel_duration:SetColorTexture(0, 0, 0, 1)
                unit_channel_interruptible:SetColorTexture(0, 0, 0, 1)
                unit_channel_fn:SetColorTexture(0, 0, 0, 0)
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
            unit_channel_fn:SetColorTexture(0, 0, 0, 0)
            unit_cast_fn:SetColorTexture(0, 0, 0, 0)
        end
    end

    local function UpdateStatusStandard_freq_low()
        if UnitExists(unit) then
            local _, maxRange = LibRangeCheck:GetRange(unit)
            if maxRange and (maxRange <= addonTable.RangeCheck) then
                unit_in_range:SetColorTexture(1, 1, 1, 1)
            else
                unit_in_range:SetColorTexture(0, 0, 0, 1)
            end
        else
            unit_in_range:SetColorTexture(0, 0, 0, 1)
        end
    end

    UpdateStatusStandard_freq_low()
    table.insert(OnUpdateFuncs_LOW, UpdateStatusStandard_freq_low)
    table.insert(OnUpdateFuncs_STD, UpdateStatus_freq_std)
    logging("InitializeUnitStatusFrame[" .. unit .. "]...Done")
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
    local assisted_combat, assisted_combat_fn = CreateFootnoteNode(x, y, "AssistedCombat", addonTable.MiscFrame)
    x = 1
    local on_chat = CreatePixelNode(x, y, "OnChat", addonTable.MiscFrame)
    x = 2
    local is_targeting = CreatePixelNode(x, y, "IsTargeting", addonTable.MiscFrame)
    x = 3
    local flash_node = CreatePixelNode(x, y, "FlashNode", addonTable.MiscFrame)
    local flash_value = true
    -- 更新杂项状态函数
    local function UpdateStatus_freq_std()
        local spellID = GetNextCastSpell(false)
        if spellID then
            local iconID, originalIconID = GetSpellTexture(spellID)
            assisted_combat:SetTexture(originalIconID)
            assisted_combat_fn:SetColorTexture(COLOR.ICONS.PLAYER_SPELL:GetRGBA())
        else
            assisted_combat:SetColorTexture(0, 0, 0, 1)
            assisted_combat_fn:SetColorTexture(0, 0, 0, 0)
        end

        local f = GetCurrentKeyBoardFocus()
        if f then
            on_chat:SetColorTexture(1, 1, 1, 1)
        else
            on_chat:SetColorTexture(0, 0, 0, 1)
        end

        if SpellIsTargeting() then
            is_targeting:SetColorTexture(1, 1, 1, 1)
        else
            is_targeting:SetColorTexture(0, 0, 0, 1)
        end

        if flash_value then
            flash_node:SetColorTexture(1, 1, 1, 1)
        else
            flash_node:SetColorTexture(0, 0, 0, 1)
        end
        flash_value = not flash_value
    end
    table.insert(OnUpdateFuncs_STD, UpdateStatus_freq_std)
    logging("InitializeMiscFrame...Done")
end

-- 将初始化杂项框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeMiscFrame)



local function InitializeFooterFrame()
    -- FooterFrane 一个无功能性的纯美化组件。
    logging("InitializeFooterFrame")
    local cooldownIDs = GetCooldownViewerCategorySet(Enum.CooldownViewerCategory.TrackedBuff, true)
    for _, v in ipairs(GetCooldownViewerCategorySet(Enum.CooldownViewerCategory.TrackedBar, true)) do
        table.insert(cooldownIDs, v)
    end
    for i = 1, math.min(46, #cooldownIDs) do
        local cooldownID = cooldownIDs[i]
        local cooldownInfo = GetCooldownViewerCooldownInfo(cooldownID)
        local iconID, originalIconID = GetSpellTexture(cooldownInfo.spellID)
        CreatePixelNode(i - 1, 0, "FooterFrane" .. i, addonTable.FooterFrane):SetTexture(iconID)
    end
    logging("InitializeFooterFrame...Done")
end
table.insert(FrameInitFuncs, InitializeFooterFrame)


-- 初始化配置框架
local function InitializeSignalFrame()
    logging("InitializeSignalFrame")
    local nodes = {}

    for i = 1, 8 do
        nodes[i] = CreatePixelNode(i - 1, 0, addonName .. "SignalFrame" .. tostring(i), addonTable.SignalFrame)
        local color = i * 32 - 1
        nodes[i]:SetColorTexture(color / 255, color / 255, color / 255, 1)
    end
    logging("使用 /pd [1-8] [0-255] [0-255] [0-255] 修改信号色块")

    SLASH_PD1 = "/pd"
    SlashCmdList["PD"] = function(msg)
        local arg1, arg2, arg3, arg4 = strsplit(" ", msg, 4)
        nodes[tonumber(arg1)]:SetColorTexture(tonumber(arg2) / 255, tonumber(arg3) / 255, tonumber(arg4 / 255), 1)
    end
    CreateStringNode(51, 3, addonName .. "num_0", addonTable.MainFrame):SetText("0")
    CreateStringNode(51, 4, addonName .. "num_1", addonTable.MainFrame):SetText("1")
    CreateStringNode(51, 5, addonName .. "num_2", addonTable.MainFrame):SetText("2")
    CreateStringNode(51, 6, addonName .. "num_3", addonTable.MainFrame):SetText("3")
    CreateStringNode(51, 7, addonName .. "num_4", addonTable.MainFrame):SetText("4")
    CreateStringNode(51, 8, addonName .. "num_5", addonTable.MainFrame):SetText("5")
    CreateStringNode(51, 9, addonName .. "num_6", addonTable.MainFrame):SetText("6")
    CreateStringNode(51, 10, addonName .. "num_7", addonTable.MainFrame):SetText("7")
    CreateStringNode(51, 11, addonName .. "num_8", addonTable.MainFrame):SetText("8")
    CreateStringNode(51, 12, addonName .. "num_9", addonTable.MainFrame):SetText("9")
    CreateStringNode(51, 13, addonName .. "num_star", addonTable.MainFrame):SetText("*")
    logging("InitializeSignalFrame...Done")
end

-- 将初始化配置框架函数添加到初始化函数表
table.insert(FrameInitFuncs, InitializeSignalFrame)

addonTable.macroList = {}
table.insert(addonTable.macroList, { title = "reloadUI", key = "CTRL-F12", text = "/reload" })
local function InitializeMacro()
    for _, macro in pairs(addonTable.macroList) do --输出2 test2, 6 test3, 4 test1
        local buttonName = addonName .. "Button" .. macro.title
        local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
        frame:SetAttribute("type", "macro")
        frame:SetAttribute("macrotext", macro.text)
        frame:RegisterForClicks("AnyDown", "AnyUp")
        SetOverrideBindingClick(frame, true, macro.key, buttonName)
        logging("InitializeMacro[" .. macro.title .. "] > " .. macro.key .. " > " .. macro.text)
    end
end
table.insert(FrameInitFuncs, InitializeMacro)


-- 设置游戏变量，确保插件正常运行
SetCVar("secretChallengeModeRestrictionsForced", 1)
SetCVar("secretCombatRestrictionsForced", 1)
SetCVar("secretEncounterRestrictionsForced", 1)
SetCVar("secretMapRestrictionsForced", 1)
SetCVar("secretPvPMatchRestrictionsForced", 1)
SetCVar("secretAuraDataRestrictionsForced", 1)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
