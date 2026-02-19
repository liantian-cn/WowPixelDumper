# EZPixelAddonX2 Wiki

## 文档目的

这份文档就聊一件事：在秘密值环境里，怎么把战斗信息稳稳地做成像素信号，让外部程序又快又稳地读出来。

## 为什么选择像素化

- 性能上：比通用视觉模型轻很多，跑起来更快。
- 风险上：比直接内存/解锁链路更像“看画面”，取证难度更高。
- 代价上：Nvidia 插帧、HDR、部分后处理会把颜色改坏，基本不兼容。

## 核心思路

1. 能拿对象就别拿裸数值（`AuraInstanceID`、`LuaDurationObject`、boolean 更稳）。
2. 连续量走 `CreateColorCurve`，开关量走 `EvaluateColorFromBoolean`。
3. 数值条用 `StatusBar`，层数用特殊字体，图标放固定网格。
4. 外部识别端照着固定坐标和协议去解码。

## 按游戏性分类怎么像素化

### 如何读取玩家 Buff 列表
说明：简单说，Aura 受限后就别纠结单条直读了，先拿 ID 列表，再按 ID 逐个取可显示信息。
```lua
local ids = C_UnitAuras.GetUnitAuraInstanceIDs("player", "HELPFUL", 32, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal) or {}
for i = 1, #ids do
    local aura = C_UnitAuras.GetAuraDataByAuraInstanceID("player", ids[i])
    if aura then BuffIcons[i]:SetTexture(aura.icon) end
end
```

### 如何读取玩家 Debuff 列表
说明：这块和 Buff 逻辑一样，区别就是筛选词和你给的显示槽位数量。
```lua
local ids = C_UnitAuras.GetUnitAuraInstanceIDs("player", "HARMFUL", 8, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal) or {}
for i = 1, #ids do
    local aura = C_UnitAuras.GetAuraDataByAuraInstanceID("player", ids[i])
    if aura then DebuffIcons[i]:SetTexture(aura.icon) end
end
```

### 如何读取目标的我方减益
说明：`HARMFUL|PLAYER` 这个过滤很关键，能把目标身上“我自己打上去”的效果单独拎出来。
```lua
local ids = C_UnitAuras.GetUnitAuraInstanceIDs("target", "HARMFUL|PLAYER", 16, Enum.UnitAuraSortRule.Expiration, Enum.UnitAuraSortDirection.Normal) or {}
for i = 1, #ids do
    local aura = C_UnitAuras.GetAuraDataByAuraInstanceID("target", ids[i])
    if aura then TargetDebuffIcons[i]:SetTexture(aura.icon) end
end
```

### 如何读取 Aura 剩余时间
说明：不要直接拿秒数硬算，走 `DurationObject -> 曲线颜色` 更稳，抗限制也更好。
```lua
local d = C_UnitAuras.GetAuraDuration(unit, auraInstanceID)
if d then
    local c = d:EvaluateRemainingDuration(remaining_curve)
    auraDurationTex:SetColorTexture(c:GetRGBA())
end
```

### 如何读取 Aura 层数（像素字体方案）
说明：`GetAuraApplicationDisplayCount` 也是秘密值，直接当普通文本用会翻车，所以要走特殊字体。  
说明：字符集固定 `0123456789*`，这 11 个字符分别做成 1~11 像素点，本质上是在用“字形宽度”传数字。
```lua
local count = C_UnitAuras.GetAuraApplicationDisplayCount(unit, auraInstanceID, 1, 9)
auraCountText:SetFont(fontFile, addonTable.nodeSize, "MONOCHROME")
auraCountText:SetText(count) -- 由特殊字体把字符映射到固定像素宽度
```

### 如何读取 Aura 是否永久
说明：布尔值最省心的方案就是黑白块，外部阈值判断几乎不费脑子。
```lua
local hasExpire = C_UnitAuras.DoesAuraHaveExpirationTime(unit, auraInstanceID)
local c = C_CurveUtil.EvaluateColorFromBoolean(hasExpire, COLOR.BLACK, COLOR.WHITE)
foreverTex:SetColorTexture(c:GetRGBA())
```

### 如何读取生命值百分比
说明：生命值建议全走曲线，经验上能做到接近最大生命值 `1/255` 的亮度步进精度。
```lua
local hp = UnitHealthPercent("player", true, curve)
playerHealthTex:SetColorTexture(hp:GetRGBA())
```

### 如何读取队友生命值
说明：队友也用同一套 `Percent + Curve`，这样外部识别端不用写两份逻辑。
```lua
if UnitExists(unitKey) then
    local hp = UnitHealthPercent(unitKey, true, curve)
    partyHealthTex:SetColorTexture(hp:GetRGBA())
end
```

### 如何读取伤害护盾
说明：护盾这块不能直接套 `CreateColorCurve`，最实用的是用 `StatusBar` 的长度来编码。
```lua
local maxHealth = UnitHealthMax("player")
DamageAbsorbBar:SetMinMaxValues(0, maxHealth)
DamageAbsorbBar:SetValue(UnitGetTotalAbsorbs("player"))
```

### 如何读取治疗吸收护盾
说明：治疗吸收最好单独一条，别和伤害护盾混在一起，后面解码会轻松很多。
```lua
local maxHealth = UnitHealthMax("player")
HealAbsorbBar:SetMinMaxValues(0, maxHealth)
HealAbsorbBar:SetValue(UnitGetTotalHealAbsorbs("player"))
```

### 如何读取施法进度
说明：施法进度直接吃 `UnitCastingDuration`，然后用曲线把低秒段精度拉高。
```lua
local d = UnitCastingDuration("player")
if d then
    local c = d:EvaluateElapsedPercent(curve)
    castDurationTex:SetColorTexture(c:GetRGBA())
end
```

### 如何读取引导进度
说明：引导和施法尽量统一成一套 Duration 协议，外部端分支越少越稳。
```lua
local d = UnitChannelDuration("player")
if d then
    local c = d:EvaluateElapsedPercent(curve)
    channelDurationTex:SetColorTexture(c:GetRGBA())
end
```

### 如何读取技能冷却与充能剩余
说明：不管是冷却还是充能，统一走 `DurationObject -> RemainingDuration`，维护成本最低。
```lua
local d = (spell.type == "charge") and C_Spell.GetSpellChargeDuration(spellID) or C_Spell.GetSpellCooldownDuration(spellID)
if d then
    local c = d:EvaluateRemainingDuration(remaining_curve)
    spellCooldownTex:SetColorTexture(c:GetRGBA())
end
```

### 如何读取技能可用性与高亮
说明：可用性/高亮/已学会这类状态，统一黑白化最实在，避免中间色误判。
```lua
local usable = C_Spell.IsSpellUsable(spellID)
local high = C_SpellActivationOverlay.IsSpellOverlayed(spellID)
spellUsableTex:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(usable, COLOR.WHITE, COLOR.BLACK):GetRGBA())
spellHighTex:SetColorTexture(C_CurveUtil.EvaluateColorFromBoolean(high, COLOR.WHITE, COLOR.BLACK):GetRGBA())
```

### 如何读取单位可攻击/存活/战斗态
说明：目标选择相关状态建议全黑白化，外部逻辑直接阈值判断就行。
```lua
local attackC = C_CurveUtil.EvaluateColorFromBoolean(UnitCanAttack("player", unit), COLOR.WHITE, COLOR.BLACK)
local aliveC = C_CurveUtil.EvaluateColorFromBoolean(not UnitIsDeadOrGhost(unit), COLOR.WHITE, COLOR.BLACK)
local combatC = C_CurveUtil.EvaluateColorFromBoolean(UnitAffectingCombat(unit), COLOR.WHITE, COLOR.BLACK)
unitCanAttackTex:SetColorTexture(attackC:GetRGBA())
unitAliveTex:SetColorTexture(aliveC:GetRGBA())
unitCombatTex:SetColorTexture(combatC:GetRGBA())
```

### 如何读取单位距离
说明：距离本质就是“在不在范围内”，做成黑白块非常合适。
```lua
local _, maxRange = LibRangeCheck:GetRange(unit)
local inRange = maxRange and (maxRange <= addonTable.RangeCheck)
local c = C_CurveUtil.EvaluateColorFromBoolean(inRange, COLOR.WHITE, COLOR.BLACK)
unitRangeTex:SetColorTexture(c:GetRGBA())
```

### 最小尺寸经验
说明：实战经验：图标框做到 `8x8` 基本就是极限了；受抗锯齿/采样影响，真正稳的识别区通常只有内部 `6x6`。  
说明：外部识别只采中心 `6x6`，边缘像素尽量别当特征。
```lua
local iconTex = CreatePixelNode(x, y, "SpellIcon", parent)
iconTex:SetSize(8 * addonTable.nodeSize, 8 * addonTable.nodeSize)
iconTex:SetTexture(iconID, "CLAMPTOBLACK", "CLAMPTOBLACK")
```

## 速查表

| 读取目标 | 不建议直读 | 建议像素化路径 |
| --- | --- | --- |
| Aura 列表 | 单个 Aura 直接索引链路 | `GetUnitAuraInstanceIDs -> AuraInstanceID` |
| Aura 时间 | 直接秒数 | `GetAuraDuration -> EvaluateRemainingDuration` |
| Aura 层数 | 直接数字 | `GetAuraApplicationDisplayCount + 特殊字体` |
| 生命值 | `UnitHealth` 裸数值 | `UnitHealthPercent + curve` |
| 护盾 | 直接数值传输 | `StatusBar` 长度编码 |
| 施法/引导 | 时间戳差值 | `UnitCastingDuration/UnitChannelDuration` |
| 冷却/充能 | 手动计算 | `GetSpellCooldownDuration/GetSpellChargeDuration` |
| 布尔状态 | 原值透传 | `EvaluateColorFromBoolean` 黑白编码 |

## 工程经验

- 生命值曲线：优先线性或低段加密曲线，把 `1/255` 量化误差压住。
- 护盾条长度：条越短精度越差，关键单位建议加宽。
- 布尔编码：统一白/黑，外部阈值判断会简单很多。
- 层数字体：`0123456789*` 这 11 个字符的字形必须固定，别让系统替换字体。
- 图标尺寸：`8x8` 是极限框，识别时只用内部 `6x6`。
- 渲染设置：HDR、插帧、锐化、动态色彩增强建议全关。

## 性能优化

思路不是“每帧把全部像素块重算一遍”，而是把更新拆成**事件驱动 + 高频轮询 + 低频轮询**三层：只在必须的时候做重活，其它时候只做轻量补偿。这样可以把 CPU 消耗压下来，同时保持像素信号的实时性。

### 具体做了哪些优化

- **单一 OnUpdate 调度器**：只挂一个 `OnUpdate`，内部统一分发 `OnUpdateFuncs_STD` 和 `OnUpdateFuncs_LOW`，避免多个 Frame 各自 `OnUpdate` 带来的调度开销。
- **双频率更新队列**：`FPS`（默认 15）跑战斗相关高频信息，`LowFrequencyFPS`（默认 5）跑职业/职责/距离/是否已学会等慢变量，重计算被主动降频。
- **事件优先，按需刷新**：`UNIT_AURA`、`UNIT_MAXHEALTH`、`SPELLS_CHANGED` 等事件触发时才更新对应数据，不把这类逻辑塞进每帧循环。
- **按单位分发事件**：Aura 与队伍最大生命值更新都按 `unit` 精确分发，避免一个单位变化导致全部单位模块重算。
- **Aura 增量更新**：缓存 `previousAuraInstanceIDs` 和 `previousDisplayCount`，仅在槽位变化时 `SetTexture` 图标；每帧只补刷新“仍在显示的 Aura 剩余时间”。
- **大量早返回与范围收缩**：例如 `previousDisplayCount == 0` 或 `not UnitExists(unit)` 直接退出；循环也只遍历有效槽位（如 `MaxFrame`、`previousDisplayCount`），不扫全量网格。
- **API 本地化减少查表开销**：把频繁调用的全局 API（如 `Unit*`、`C_Spell*`、`C_UnitAuras*`）缓存为局部变量，降低高频路径上的全局查找成本。


