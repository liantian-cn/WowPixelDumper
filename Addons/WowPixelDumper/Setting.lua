local addonName, addonTable = ...

if WowPixelDumperDB == nil then
    WowPixelDumperDB = {}
end

addonTable.FPS = WowPixelDumperDB.FPS or 24
addonTable.RangeCheck = WowPixelDumperDB.RangeCheck or 40


local category = Settings.RegisterVerticalLayoutCategory(addonName)
Settings.RegisterAddOnCategory(category)

do
    local name = "刷新率"
    local tooltip = "设置每秒刷新速度，这将影响CPU占用，默认24"
    local variable = addonName .. "FPS"
    local defaultValue = addonTable.FPS
    local minValue = 10
    local maxValue = 60
    local step = 2
    local function GetValue()
        return addonTable.FPS
    end

    local function SetValue(value)
        addonTable.FPS = value
        WowPixelDumperDB.FPS = value
    end


    local setting = Settings.RegisterProxySetting(category, variable, type(defaultValue), name, defaultValue, GetValue, SetValue)
    local options = Settings.CreateSliderOptions(minValue, maxValue, step)
    options:SetLabelFormatter(MinimalSliderWithSteppersMixin.Label.Right);
    Settings.CreateSlider(category, setting, options, tooltip)
end


do
    local name = "距离检查值"
    local tooltip = "设置范围检查距离，请选择主力技能的范围"
    local variable = addonName .. "RangeCheck"
    local defaultValue = addonTable.RangeCheck
    local minValue = 8
    local maxValue = 42
    local step = 2
    local function GetValue()
        return addonTable.RangeCheck
    end

    local function SetValue(value)
        addonTable.RangeCheck = value
        WowPixelDumperDB.RangeCheck = value
    end


    local setting = Settings.RegisterProxySetting(category, variable, type(defaultValue), name, defaultValue, GetValue, SetValue)
    local options = Settings.CreateSliderOptions(minValue, maxValue, step)
    options:SetLabelFormatter(MinimalSliderWithSteppersMixin.Label.Right);
    Settings.CreateSlider(category, setting, options, tooltip)
end
