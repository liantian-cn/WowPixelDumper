local addonName, addonTable = ...

if not EZAssistedX2DB then
    EZAssistedX2DB = {}
    EZAssistedX2DB.SpellMacro = {}
end

addonTable.FPS = EZAssistedX2DB.FPS or 24

-- 日志输出函数
local logging = function(msg)
    print("|cFFFFBB66[EZAssistedX2]|r" .. tostring(msg))
end

local debug = false

local gameBuildVersion, GameBuildNumber, _ = GetBuildInfo()
local fullVersion = gameBuildVersion .. "." .. GameBuildNumber
local addonVersion = C_AddOns.GetAddOnMetadata(addonName, "Version")

if addonVersion ~= fullVersion then
    logging("插件版本" .. addonVersion .. " 游戏版本" .. fullVersion)
    logging("插件版本与游戏版本不一致，可能会导致一些问题")
end

local KeyColorMap = {}
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD1", ["color"] = CreateColor(13 / 255, 255 / 255, 0 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD2", ["color"] = CreateColor(0 / 255, 255 / 255, 64 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD3", ["color"] = CreateColor(0 / 255, 255 / 255, 140 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD4", ["color"] = CreateColor(0 / 255, 255 / 255, 217 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD5", ["color"] = CreateColor(0 / 255, 217 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD6", ["color"] = CreateColor(0 / 255, 140 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD7", ["color"] = CreateColor(0 / 255, 64 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD8", ["color"] = CreateColor(13 / 255, 0 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD9", ["color"] = CreateColor(89 / 255, 0 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "SHIFT-NUMPAD0", ["color"] = CreateColor(166 / 255, 0 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD1", ["color"] = CreateColor(242 / 255, 0 / 255, 255 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD2", ["color"] = CreateColor(255 / 255, 0 / 255, 191 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD3", ["color"] = CreateColor(255 / 255, 0 / 255, 115 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD4", ["color"] = CreateColor(255 / 255, 0 / 255, 38 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD5", ["color"] = CreateColor(255 / 255, 38 / 255, 0 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD6", ["color"] = CreateColor(255 / 255, 115 / 255, 0 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD7", ["color"] = CreateColor(255 / 255, 191 / 255, 0 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD8", ["color"] = CreateColor(242 / 255, 255 / 255, 0 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD9", ["color"] = CreateColor(166 / 255, 255 / 255, 0 / 255, 1) })
table.insert(KeyColorMap, { ["key"] = "ALT-NUMPAD0", ["color"] = CreateColor(89 / 255, 255 / 255, 0 / 255, 1) })


local spellDict = {}

-- 本地化提高性能
local CreateFrame = CreateFrame

local UnitIsUnit = UnitIsUnit
local UnitIsDeadOrGhost = UnitIsDeadOrGhost
local UnitInVehicle = UnitInVehicle
local UnitAffectingCombat = UnitAffectingCombat

local GetSpellTexture = C_Spell.GetSpellTexture
local GetSpellLink = C_Spell.GetSpellLink
local GetSpellName = C_Spell.GetSpellName
local GetBaseSpell = C_Spell.GetBaseSpell
local GetSpellCooldown = C_Spell.GetSpellCooldown

local GetRotationSpells = C_AssistedCombat.GetRotationSpells
local GetSpecialization = C_SpecializationInfo.GetSpecialization




-- 颜色定义表
local COLOR = {
    RED = CreateColor(255 / 255, 0, 0, 1),
    GREEN = CreateColor(0, 255 / 255, 0, 1),
    BLUE = CreateColor(0, 0, 255 / 255, 1),
    BLACK = CreateColor(0, 0, 0, 1),
    WHITE = CreateColor(1, 1, 1, 1),
}


-- 框架初始化函数表
local AddonInitFuncs = {}
-- 更新函数表
local UpdateFuncs    = {}
-- 技能表，每个技能有两种显示方式："cooldown"和"charge"
addonTable.Spell     = {}
-- 添加GCD技能到技能表



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
        for _, func in ipairs(AddonInitFuncs) do
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


local function InitializeVariables()
    local specializationIndex = GetSpecialization()
    if not EZAssistedX2DB.SpellMacro[specializationIndex] then
        EZAssistedX2DB.SpellMacro[specializationIndex] = {}
    end
    addonTable.specializationIndex = specializationIndex
end

table.insert(AddonInitFuncs, InitializeVariables)

-- 初始化主框架
local function InitializePixelFrame()
    local nodeSize = GetUIScaleFactor(2)

    local PixelFrame = CreateFrame("Frame", addonName .. "PixelFrame", UIParent)
    PixelFrame:SetPoint("TOPLEFT", UIParent, "TOPLEFT", 0, 0)
    PixelFrame:SetSize(nodeSize * 6, nodeSize * 2)
    PixelFrame:SetFrameStrata("TOOLTIP")
    PixelFrame:SetFrameLevel(900)
    PixelFrame:Show()

    PixelFrame.bg = PixelFrame:CreateTexture(nil, "BACKGROUND")
    PixelFrame.bg:SetAllPoints()
    PixelFrame.bg:SetColorTexture(0, 0, 0, 1)
    PixelFrame.bg:Show()

    local function CreateNode(x, y, color)
        local nodeFrame = CreateFrame("Frame", addonName .. "Node" .. x .. y, PixelFrame)
        nodeFrame:SetPoint("TOPLEFT", PixelFrame, "TOPLEFT", x * nodeSize, -y * nodeSize)
        nodeFrame:SetFrameLevel(PixelFrame:GetFrameLevel() + 2)
        nodeFrame:SetSize(nodeSize, nodeSize)
        nodeFrame:Show()
        nodeFrame.bg = nodeFrame:CreateTexture(nil, "BACKGROUND")
        nodeFrame.bg:SetAllPoints(nodeFrame)
        nodeFrame.bg:SetColorTexture(color:GetRGBA())
        nodeFrame.bg:Show()
    end
    CreateNode(0, 0, COLOR.RED)
    CreateNode(1, 0, COLOR.GREEN)
    CreateNode(1, 1, COLOR.BLUE)

    CreateNode(4, 0, COLOR.RED)
    CreateNode(5, 0, COLOR.GREEN)
    CreateNode(5, 1, COLOR.BLUE)

    local centerFrame = CreateFrame("Frame", addonName .. "centerFrame", PixelFrame)
    centerFrame:SetPoint("TOPLEFT", PixelFrame, "TOPLEFT", 2 * nodeSize, 0)
    centerFrame:SetFrameLevel(PixelFrame:GetFrameLevel() + 2)
    centerFrame:SetSize(2 * nodeSize, 2 * nodeSize)
    centerFrame:Show()
    local centerTexture = centerFrame:CreateTexture(nil, "BACKGROUND")
    centerTexture:SetAllPoints(centerFrame)
    centerTexture:SetColorTexture(COLOR.WHITE:GetRGBA())
    centerTexture:Show()
    addonTable.PixelTexture = centerTexture
end

table.insert(AddonInitFuncs, InitializePixelFrame)

local function InitMacro()
    local spellIDs = GetRotationSpells()
    for i = 1, #spellIDs do
        local spellID = spellIDs[i]
        local spellName = GetSpellName(spellID)
        local baseSpellID = GetBaseSpell(spellID)
        local baseSpellName = GetSpellName(baseSpellID)
        if not EZAssistedX2DB.SpellMacro[addonTable.specializationIndex][spellID] then
            EZAssistedX2DB.SpellMacro[addonTable.specializationIndex][spellID] = "/cast [nochanneling] " .. spellName
        end
        if not EZAssistedX2DB.SpellMacro[addonTable.specializationIndex][baseSpellID] then
            EZAssistedX2DB.SpellMacro[addonTable.specializationIndex][baseSpellID] = "/cast [nochanneling] " .. baseSpellName
        end
    end
end
table.insert(AddonInitFuncs, InitMacro)




local function RegisterMacro()
    local macroTable = EZAssistedX2DB.SpellMacro[addonTable.specializationIndex]
    local i = 1
    for spellID, macroText in pairs(macroTable) do --输出2 test2, 6 test3, 4 test1
        local spellName = GetSpellName(spellID)
        local key = KeyColorMap[i]["key"]
        local color = KeyColorMap[i]["color"]
        if debug then
            logging(GetSpellLink(spellID) .. "Macro:" .. macroText .. " key:" .. key .. " color:" .. color:GetRGBA())
        end
        spellDict[spellID] = { key = key, color = color }

        local buttonName = addonName .. "Button" .. tostring(i)
        local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
        frame:SetAttribute("type", "macro")
        frame:SetAttribute("macrotext", macroText)
        frame:RegisterForClicks("AnyDown", "AnyUp")
        SetOverrideBindingClick(frame, true, key, buttonName)

        i = i + 1
    end
end
table.insert(AddonInitFuncs, RegisterMacro)






-- ============================================================
-- 技能宏编辑器框体
-- ============================================================
local EZCPFrame = nil

local function InitializeConfigFrame()
    -- 主框体 BasicFrameTemplateWithInset: 标准WoW对话框，自带标题栏、关闭按钮、Inset背景
    local mainFrame = CreateFrame("Frame", addonName .. "ConfigPanel", UIParent, "BasicFrameTemplateWithInset")
    mainFrame:SetSize(720, 360)
    mainFrame:SetPoint("CENTER")
    mainFrame:SetFrameStrata("DIALOG")
    mainFrame:SetMovable(true)
    mainFrame:EnableMouse(true)
    mainFrame:RegisterForDrag("LeftButton")
    mainFrame:SetScript("OnDragStart", mainFrame.StartMoving)
    mainFrame:SetScript("OnDragStop", mainFrame.StopMovingOrSizing)
    mainFrame:Show()

    mainFrame.TitleBg:SetHeight(30)
    mainFrame.title = mainFrame:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    mainFrame.title:SetPoint("TOPLEFT", mainFrame.TitleBg, "TOPLEFT", 5, -3)
    mainFrame.title:SetText(addonName)


    EZCPFrame = mainFrame

    -- local content = mainFrame.Inset
    local macroTable = EZAssistedX2DB.SpellMacro[addonTable.specializationIndex]
    local selectedSpellID = nil
    local selectedButton = nil

    -- -- ========== 左侧: 技能列表 ==========
    local listBg = CreateFrame("Frame", nil, mainFrame, "InsetFrameTemplate")
    listBg:ClearAllPoints()
    listBg:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 4, -32)
    listBg:SetPoint("BOTTOMLEFT", mainFrame, "BOTTOMLEFT", 4, 4)
    listBg:SetWidth(184)

    local listScroll = CreateFrame("ScrollFrame", addonName .. "ListScroll", listBg, "UIPanelScrollFrameTemplate")
    listScroll:ClearAllPoints()
    listScroll:SetPoint("TOPLEFT", 4, -4)
    listScroll:SetPoint("BOTTOMRIGHT", -26, 4)

    local listChild = CreateFrame("Frame", nil, listScroll)
    local listChildWidth = 150
    listChild:SetWidth(listChildWidth)
    listChild:SetHeight(1)
    listScroll:SetScrollChild(listChild)

    -- -- ========== 中间上方: 技能图标 ==========
    local iconFrame = CreateFrame("Frame", nil, mainFrame, "BackdropTemplate")
    iconFrame:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 200, -42)
    iconFrame:SetSize(64, 64)
    iconFrame:SetBackdrop({
        edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
        edgeSize = 12,
        insets = { left = 2, right = 2, top = 2, bottom = 2 },
    })
    iconFrame:SetBackdropBorderColor(0.6, 0.6, 0.6, 1)

    local spellIcon = iconFrame:CreateTexture(nil, "ARTWORK")
    spellIcon:SetPoint("TOPLEFT", 3, -3)
    spellIcon:SetPoint("BOTTOMRIGHT", -3, 3)
    spellIcon:SetTexture(134400) -- 问号图标

    -- -- ========== 中间上方右侧: 保存按钮  ==========
    local saveBtn = CreateFrame("Button", addonName .. "SaveBtn", mainFrame, "UIPanelButtonTemplate")
    saveBtn:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 280, -42)
    saveBtn:SetSize(128, 32)
    saveBtn:SetText("保存并重载")

    -- -- ========== 中间下方: 宏编辑框 ) ==========
    local editBg = CreateFrame("Frame", nil, mainFrame, "InsetFrameTemplate")
    editBg:ClearAllPoints()
    editBg:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 200, -116)
    editBg:SetSize(320, 220)

    local editScroll = CreateFrame("ScrollFrame", addonName .. "MacroEdit", editBg, "InputScrollFrameTemplate")
    editScroll:ClearAllPoints()
    editScroll:SetPoint("TOPLEFT", 6, -6)
    editScroll:SetPoint("BOTTOMRIGHT", -6, 6)
    editScroll.EditBox:SetFontObject("ChatFontNormal")
    editScroll.EditBox:SetWidth(296)
    editScroll.EditBox:SetAutoFocus(false)
    editScroll.CharCount:Hide()

    -- -- ========== 右侧: 说明区域 ==========
    local guideBg = CreateFrame("Frame", nil, mainFrame, "InsetFrameTemplate")
    guideBg:ClearAllPoints()
    guideBg:SetPoint("TOPLEFT", mainFrame, "TOPLEFT", 534, -42)
    guideBg:SetSize(166, 300)

    local guideText = guideBg:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    guideText:SetPoint("TOPLEFT", 8, -8)
    guideText:SetPoint("TOPRIGHT", -8, -8)
    guideText:SetJustifyH("LEFT")
    guideText:SetJustifyV("TOP")

    guideText:SetText("1.有些替换技能需要在宏中使用原技能。\n\n2.使用多个/cast来释放\n无GCD的防御技能。\n\n3.使用/castsequence reset=1 插入技能,原技能\n可以插入技能。")

    -- ========== 选中逻辑: 点击列表项 → 显示图标 + 加载宏文本 ==========
    local function SelectSpell(spellID, button)
        selectedSpellID = spellID
        if selectedButton then
            selectedButton:UnlockHighlight()
        end
        button:LockHighlight()
        selectedButton = button

        spellIcon:SetTexture(GetSpellTexture(spellID))
        editScroll.EditBox:SetText(macroTable[spellID] or "")
    end

    -- ========== 构建技能按钮列表 ==========
    local btnHeight = 20
    local btnIndex = 0

    for spellID, _ in pairs(macroTable) do
        local spellName = GetSpellName(spellID)
        local btn = CreateFrame("Button", nil, listChild)
        btn:SetSize(listChildWidth, btnHeight)
        btn:SetPoint("TOPLEFT", listChild, "TOPLEFT", 0, -btnIndex * btnHeight)
        btn:SetNormalFontObject("GameFontNormal")
        btn:SetHighlightFontObject("GameFontHighlight")
        btn:SetText(spellName or ("Spell#" .. spellID))
        btn:GetFontString():SetJustifyH("LEFT")
        btn:GetFontString():SetPoint("LEFT", btn, "LEFT", 4, 0)

        local hl = btn:CreateTexture(nil, "HIGHLIGHT")
        hl:SetAllPoints()
        hl:SetColorTexture(1, 1, 1, 0.2)
        btn:SetHighlightTexture(hl)

        local sid = spellID
        btn:SetScript("OnClick", function(self)
            SelectSpell(sid, self)
        end)

        btnIndex = btnIndex + 1
    end
    listChild:SetHeight(math.max(btnIndex * btnHeight, 1))

    -- ========== 保存按钮逻辑 ==========
    saveBtn:SetScript("OnClick", function()
        if selectedSpellID then
            EZAssistedX2DB.SpellMacro[addonTable.specializationIndex][selectedSpellID] = editScroll.EditBox:GetText()
        end
        C_UI.Reload()
    end)
    EZCPFrame:Hide()
    logging("使用/ez edit命令, 编辑一键辅助技能宏")
end

table.insert(AddonInitFuncs, InitializeConfigFrame)

-- ========== 斜杠命令: /ezcp toggle|hide|show ==========
SLASH_EZCP1 = "/ez"
SlashCmdList["EZCP"] = function(msg)
    msg = strlower(strtrim(msg))
    if msg == "show" then
        if EZCPFrame then EZCPFrame:Show() end
    elseif msg == "hide" then
        if EZCPFrame then EZCPFrame:Hide() end
    elseif msg == "edit" then
        if EZCPFrame then
            if EZCPFrame:IsShown() then
                EZCPFrame:Hide()
            else
                EZCPFrame:Show()
            end
        end
    end
end

local function GCDReady()
    local spellCooldownInfo = GetSpellCooldown(61304)
    if spellCooldownInfo.duration == 0 then
        return true
    else
        local remaining = spellCooldownInfo.startTime + spellCooldownInfo.duration - GetTime()
        return remaining < 0.3
    end
end

local lastestColor = COLOR.WHITE
local function changeColor(color)
    if color ~= lastestColor then
        addonTable.PixelTexture:SetColorTexture(color:GetRGBA())
        lastestColor = color
    end
end

local function RegisterRotation()
    local function RotationUpdater()
        if UnitIsDeadOrGhost("player") or (not UnitAffectingCombat("player")) or UnitInVehicle("player") or IsMounted() or UnitIsUnit("player", "target") or (not UnitExists("target")) or (not GCDReady()) then
            changeColor(COLOR.WHITE)
            return
        end
        local spellID = C_AssistedCombat.GetNextCastSpell(false)
        if type(spellID) == "nil" then
            changeColor(COLOR.WHITE)
        else
            local spellVars = spellDict[spellID]
            if spellVars == nil then
                local spellName = GetSpellName(spellID)
                EZAssistedX2DB.SpellMacro[addonTable.specializationIndex][spellID] = "/cast [nochanneling] " .. spellName
                local spellLink = GetSpellLink(spellID)
                logging("新技能: " .. spellLink .. "请/reload")
            else
                changeColor(spellVars.color)
            end
        end
    end
    table.insert(UpdateFuncs, RotationUpdater)
end
table.insert(AddonInitFuncs, RegisterRotation)


-- 设置游戏变量，确保插件正常运行
SetCVar("secretChallengeModeRestrictionsForced", 1)
SetCVar("secretCombatRestrictionsForced", 1)
SetCVar("secretEncounterRestrictionsForced", 1)
SetCVar("secretMapRestrictionsForced", 1)
SetCVar("secretPvPMatchRestrictionsForced", 1)
SetCVar("secretAuraDataRestrictionsForced", 1)
SetCVar("scriptErrors", 1);
SetCVar("doNotFlashLowHealthWarning", 1);
