local addonName, addonTable = ...

if PixelAddonX2DB == nil then
    PixelAddonX2DB = {}
end

addonTable.FPS = PixelAddonX2DB.FPS or 15
addonTable.RangeCheck = PixelAddonX2DB.RangeCheck or 40
addonTable.LowFrequencyFPS = PixelAddonX2DB.LowFrequencyFPS or 5


local category = Settings.RegisterVerticalLayoutCategory(addonName)
Settings.RegisterAddOnCategory(category)

do
    local name = "刷新率"
    local tooltip = "设置每秒刷新速度, 这将影响CPU占用, 默认24"
    local variable = addonName .. "FPS"
    local defaultValue = addonTable.FPS
    local minValue = 10
    local maxValue = 30
    local step = 5
    local function GetValue()
        return addonTable.FPS
    end

    local function SetValue(value)
        addonTable.FPS = value
        PixelAddonX2DB.FPS = value
    end


    local setting = Settings.RegisterProxySetting(category, variable, type(defaultValue), name, defaultValue, GetValue, SetValue)
    local options = Settings.CreateSliderOptions(minValue, maxValue, step)
    options:SetLabelFormatter(MinimalSliderWithSteppersMixin.Label.Right);
    Settings.CreateSlider(category, setting, options, tooltip)
end

do
    local name = "低频刷新率"
    local tooltip = "设置慢速刷新速度, 默认5"
    local variable = addonName .. "LowFrequencyFPS"
    local defaultValue = addonTable.LowFrequencyFPS
    local minValue = 1
    local maxValue = 15
    local step = 1
    local function GetValue()
        return addonTable.LowFrequencyFPS
    end

    local function SetValue(value)
        addonTable.LowFrequencyFPS = value
        PixelAddonX2DB.LowFrequencyFPS = value
    end

    local setting = Settings.RegisterProxySetting(category, variable, type(defaultValue), name, defaultValue, GetValue, SetValue)
    local options = Settings.CreateSliderOptions(minValue, maxValue, step)
    options:SetLabelFormatter(MinimalSliderWithSteppersMixin.Label.Right);
    Settings.CreateSlider(category, setting, options, tooltip)
end


do
    local name = "距离检查值"
    local tooltip = "设置范围检查距离, 请选择主力技能的范围"
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
        PixelAddonX2DB.RangeCheck = value
    end


    local setting = Settings.RegisterProxySetting(category, variable, type(defaultValue), name, defaultValue, GetValue, SetValue)
    local options = Settings.CreateSliderOptions(minValue, maxValue, step)
    options:SetLabelFormatter(MinimalSliderWithSteppersMixin.Label.Right);
    Settings.CreateSlider(category, setting, options, tooltip)
end
