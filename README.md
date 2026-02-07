# WowPixelDumper 

**贼心不死，继续奋斗** 💪 

一个用于《魔兽世界》（World of Warcraft）的**游戏数据像素化插件**，通过将游戏内的可收集信息转换为屏幕角落的像素点，让外部程序可以轻松读取并解析为结构化数据。  

## 源起与目的

本项目诞生于一个简单的想法：**在12.0版本中，将秘密值通过像素化的方式传递给外部程序**。  

过去，WoW 的插件 API 提供了丰富的游戏数据，但在最新的游戏更新中，这些数据被限制为"秘密值"，无法被使用。但秘密值可以被编码为屏幕角落的彩色像素块，从而让外部程序通过屏幕捕获获取结构化信息。  

**这不是一个开箱即用的产品，而是一个技术示例。** 代码完全开源，意在展示"像素桥接"这一思路的可行性。如果你认同这个方向，建议在此基础上进行**个性化改造**——调整像素布局、修改数据结构、更换通信方式，让它成为你独有的实现。  

**如何开始？** 推荐使用 **vibe coding** 的方式：借助 AI 编程工具（如 Cline、Trae、Kimi Code、Qoder 等），让 AI 协助你理解代码逻辑并对本项目进行轻量级重构。即使你不是专业开发者，也可以通过自然语言描述需求，快速生成符合自己习惯的代码变体，从而消除本项目的可识别特征。  

项目采用 **Dumper + HTTP API** 的架构设计：Dumper 负责像素捕获与解析，通过本地 HTTP 服务（默认端口 65131）以 JSON 格式输出数据。这种解耦设计让你可以用任何熟悉的语言（Python、C#、Lua 等）独立开发后续的 Rotation 逻辑。  


---

## ⚠️ 免责声明⚠️

1. **切勿直接使用**：本项目的代码特征明显，如果大量用户使用完全相同的代码，极易被游戏反作弊系统检测并导致**账号封禁**。  
2. **必须个性化修改**：强烈建议您根据自身需求对代码进行修改和定制。调整像素布局、数据结构或通信方式，使其具备独特性。  
3. **抛砖引玉，非开箱即用**：本项目旨在展示"将游戏数据转换为像素块并通过外部程序解析"的技术思路，而非提供可直接投入使用的产品。  
4. **自行承担全部风险**：任何基于本项目的二次开发、修改或使用行为，均由您自行承担一切后果（包括但不限于账号封禁、数据损失等）。  
5. **禁止商用与损害公平**：不得将本项目用于任何商业用途，或开发损害游戏公平性的外挂/自动化工具。  


---

## ⚠️ Disclaimer⚠️

1. **Do Not Use Directly**: This project's code has distinctive characteristics; if a large number of users use exactly the same code, it is highly likely to be detected by the game's anti‑cheat system and result in **account suspension**.
2. **Personalization Required**: It is strongly recommended that you modify and customize the code according to your own needs. Adjust pixel layouts, data structures, or communication methods to make it unique.
3. **A Spark for Ideas, Not Out‑of‑the‑Box**: This project aims to demonstrate the technical concept of "converting game data into pixel blocks and parsing them via external programs," not to provide a ready‑to‑use product.
4. **Assume All Risks**: Any secondary development, modification, or use based on this project is entirely at your own risk (including but not limited to account suspension, data loss, etc.).
5. **No Commercial Use or Fair‑Play Harm**: This project must not be used for any commercial purposes, nor for developing cheats/automation tools that undermine game fairness.






# Changelog

## [2026.02.07]

###  较大改进点

#### 一、Dumper的逻辑变化

原本的结构
`NodeExtractor` -> `Node` 
修改为
`NodeExtractor` -> `Node`  -> `PixelBlock`

PixelBlock是不包含坐标的像素块，承担计算任务。
Node是包含坐标的节点，`Node`的`full`、`middle`、`inner`、`sub`属性对应不同大小的`PixelBlock`对象。

#### 二、新增布局 MixedNode 
-  将现有的8x8节点再次细分为4个4x4像素。
- 在lua内，使用CreateMixedNode创建
- 在Dumper内，使用`Node.mixNode`，返回4个`PixBlock`对象，每个`PixBlock`对象**仅包含4个像素**。

<img width="200" alt="5a8dc638-94f0-4118-8a6c-e8f4641c3098" src="https://github.com/user-attachments/assets/869196c6-0b03-4de4-8f6e-0d94d092a6ad" />

#### 三、新增布局 FootnoteNode
- 仅在lua中生效，使用CreateFootnoteNode创建。
- 使用FootnoteNode将更容易分辨可驱散的buff。
- 玩家debuff、队友debuff使用这种类型的图标。

<img width="200"  alt="a2d60395-e062-495a-abdf-cffa29d57e04" src="https://github.com/user-attachments/assets/2df1417e-78ee-4459-bed1-e8f62ef6b80c" />

### 一般改进点

#### 一、布局变化

<img width="720" alt="27a3cb9d-9c8b-43ea-959c-f242a96c1046" src="https://github.com/user-attachments/assets/e63400b8-39cc-4b40-a890-fcbcc8e64381" />

- 单个`Aura`的高度降低为3，采用了`MixedNode` ，额外提供了技能是否为永久aura的判断。
- 单个`Spell`的高度降低为3，采用了`MixedNode` ，额外提供是否学会和是否可用的判断。close #6  close #5 
- 增加了一个Signal(信号)区域，并且可以游戏内使用`/pd [1-8] [0-255] [0-255] [0-255] `，用于后面的循环编写。
- 数量变化
  - 目标Debuff扩列到16 close #4 
  - 队友的Debuff减少的6
 
#### 二、功能改进

- 默认从系统的冷却管理器加载全部冷却技能，不再需要编写职业文件。 close #8 
- 技能图标加入刷新，这样技能覆盖就可以被观察到 close #7 

#### 三、插件端的小变化
- 稍微优化了API的性能。

#### 四、Dumper变化
- 默认图标相似度阈值从0.95提高到0.97
- 修改因为相似度而引入的标题后，状态变为手工输入。

#### 五、增项
- ['misc']['on_chat'] 用于表示是否开启了输入法。
- ['misc']['is_targeting'] 用于表示是否正在选择目标。



## 示例

下面是dumper的输出示例

```json
{
        "timestamp": "2026-02-01 21:32:39",
        "misc": {
                "ac": "苦修",
                "on_chat": false,
                "is_targeting": false
        },
        "spec": {},
        "player": {
                "aura": {
                        "buff": [
                                {
                                        "title": "真言术：盾",
                                        "remaining": 9.0,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                },
                                {
                                        "title": "真言术：韧",
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                },
                                {
                                        "title": "神圣射线",
                                        "remaining": 1.0,
                                        "type": "NONE",
                                        "count": 9,
                                        "forever": false
                                },
                                {
                                        "title": "6bc065e7199557bb",
                                        "remaining": 1.6,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": false
                                },
                                {
                                        "title": "69fe891d3e8c3f69",
                                        "remaining": 10.5,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": false
                                },
                                {
                                        "title": "圣光涌动",
                                        "remaining": 10.5,
                                        "type": "NONE",
                                        "count": 1,
                                        "forever": false
                                },
                                {
                                        "title": "7fb1071718556026",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                {
                                        "title": "fb393a9e23530285",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                {
                                        "title": "19c20c6ee3a06d12",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                {
                                        "title": "141df3ca3735ee36",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                {
                                        "title": "奥术智慧",
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                },
                                {
                                        "title": "61111ee96361ef5f",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                }
                        ],
                        "buff_dict": {
                                "真言术：盾": {
                                        "title": "真言术：盾",
                                        "remaining": 9.0,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                },
                                "真言术：韧": {
                                        "title": "真言术：韧",
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                },
                                "神圣射线": {
                                        "title": "神圣射线",
                                        "remaining": 1.0,
                                        "type": "NONE",
                                        "count": 9,
                                        "forever": false
                                },
                                "6bc065e7199557bb": {
                                        "title": "6bc065e7199557bb",
                                        "remaining": 1.6,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": false
                                },
                                "69fe891d3e8c3f69": {
                                        "title": "69fe891d3e8c3f69",
                                        "remaining": 10.5,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": false
                                },
                                "圣光涌动": {
                                        "title": "圣光涌动",
                                        "remaining": 10.5,
                                        "type": "NONE",
                                        "count": 1,
                                        "forever": false
                                },
                                "7fb1071718556026": {
                                        "title": "7fb1071718556026",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                "fb393a9e23530285": {
                                        "title": "fb393a9e23530285",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                "19c20c6ee3a06d12": {
                                        "title": "19c20c6ee3a06d12",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                "141df3ca3735ee36": {
                                        "title": "141df3ca3735ee36",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                },
                                "奥术智慧": {
                                        "title": "奥术智慧",
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                },
                                "61111ee96361ef5f": {
                                        "title": "61111ee96361ef5f",
                                        "remaining": 0.0,
                                        "type": "NONE",
                                        "count": 0,
                                        "forever": true
                                }
                        },
                        "debuff": [
                                {
                                        "title": "13b0f20a40628634",
                                        "remaining": 3.3,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                }
                        ],
                        "debuff_dict": {
                                "13b0f20a40628634": {
                                        "title": "13b0f20a40628634",
                                        "remaining": 3.3,
                                        "type": "MAGIC",
                                        "count": 0,
                                        "forever": false
                                }
                        }
                },
                "spell_sequence": [
                        {
                                "title": "GCD",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "真言术：盾",
                                "remaining": 3.75,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "绝望祷言",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "渐隐术",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "天堂之羽",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 3,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "终极苦修",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "纯净术",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "心灵尖啸",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "群体驱散",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "信仰飞跃",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "痛苦压制",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 2,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "能量灌注",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "暗言术：灭",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "安抚心灵",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "真言术：耀",
                                "remaining": 15.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "心灵震爆",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "苦修",
                                "remaining": 4.15,
                                "height": false,
                                "charge": 10,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "福音",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        {
                                "title": "3affeda73fa73a06",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "统御意志",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "7666496670e45a56",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "a74fe159288e23e9",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "32cbf08f7aeb6c32",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "5e13a6c6e7fa4d11",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "8d54f8f83cec98aa",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 2,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "祸福相倚",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "5e13a6c6e7fa4d11",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "a811b9fa0ad4a9c3",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "ee24930072c64c95",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        {
                                "title": "真言术：障",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        }
                ],
                "spell": {
                        "GCD": {
                                "title": "GCD",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "真言术：盾": {
                                "title": "真言术：盾",
                                "remaining": 3.75,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "绝望祷言": {
                                "title": "绝望祷言",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "渐隐术": {
                                "title": "渐隐术",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "天堂之羽": {
                                "title": "天堂之羽",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 3,
                                "known": true,
                                "usable": false
                        },
                        "终极苦修": {
                                "title": "终极苦修",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "纯净术": {
                                "title": "纯净术",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        "心灵尖啸": {
                                "title": "心灵尖啸",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "群体驱散": {
                                "title": "群体驱散",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "信仰飞跃": {
                                "title": "信仰飞跃",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        "痛苦压制": {
                                "title": "痛苦压制",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 2,
                                "known": true,
                                "usable": false
                        },
                        "能量灌注": {
                                "title": "能量灌注",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "暗言术：灭": {
                                "title": "暗言术：灭",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        "安抚心灵": {
                                "title": "安抚心灵",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "真言术：耀": {
                                "title": "真言术：耀",
                                "remaining": 15.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        "心灵震爆": {
                                "title": "心灵震爆",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 1,
                                "known": true,
                                "usable": false
                        },
                        "苦修": {
                                "title": "苦修",
                                "remaining": 4.15,
                                "height": false,
                                "charge": 10,
                                "known": true,
                                "usable": false
                        },
                        "福音": {
                                "title": "福音",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": true,
                                "usable": false
                        },
                        "3affeda73fa73a06": {
                                "title": "3affeda73fa73a06",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "统御意志": {
                                "title": "统御意志",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "7666496670e45a56": {
                                "title": "7666496670e45a56",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "a74fe159288e23e9": {
                                "title": "a74fe159288e23e9",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "32cbf08f7aeb6c32": {
                                "title": "32cbf08f7aeb6c32",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "5e13a6c6e7fa4d11": {
                                "title": "5e13a6c6e7fa4d11",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "8d54f8f83cec98aa": {
                                "title": "8d54f8f83cec98aa",
                                "remaining": 0.0,
                                "height": false,
                                "charge": 2,
                                "known": false,
                                "usable": false
                        },
                        "祸福相倚": {
                                "title": "祸福相倚",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "a811b9fa0ad4a9c3": {
                                "title": "a811b9fa0ad4a9c3",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "ee24930072c64c95": {
                                "title": "ee24930072c64c95",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        },
                        "真言术：障": {
                                "title": "真言术：障",
                                "remaining": 0.3,
                                "height": false,
                                "charge": 0,
                                "known": false,
                                "usable": false
                        }
                },
                "status": {
                        "damage_absorbs": 1.5625,
                        "heal_absorbs": 0.0,
                        "health": 100.0,
                        "power": 90.19607843137256,
                        "in_combat": true,
                        "in_movement": true,
                        "in_vehicle": false,
                        "is_empowered": false,
                        "cast_icon": null,
                        "cast_duration": null,
                        "channel_icon": null,
                        "channel_duration": null,
                        "class": "PRIEST",
                        "role": "HEALER",
                        "deaded": false
                }
        },
        "target": {
                "aura": {
                        "debuff": [],
                        "debuff_dict": {}
                },
                "status": {
                        "exists": true,
                        "can_attack": false,
                        "is_self": false,
                        "alive": true,
                        "in_combat": true,
                        "in_range": true,
                        "health": 100.0,
                        "cast_icon": null,
                        "cast_duration": null,
                        "cast_interruptible": null,
                        "channel_icon": null,
                        "channel_duration": null,
                        "channel_interruptible": null
                }
        },
        "focus": {
                "aura": {
                        "debuff": [],
                        "debuff_dict": {}
                },
                "status": {
                        "exists": false
                }
        },
        "party": {
                "party1": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 100.0,
                                "selectd": true,
                                "damage_absorbs": 18.75,
                                "heal_absorbs": 0.0,
                                "class": "PALADIN",
                                "role": "TANK"
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "真言术：盾",
                                                "remaining": 19.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 18.0,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "ea1bcdf5faf4874c",
                                                "remaining": 0.05,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "a8869cea08bc48fe",
                                                "remaining": 2.2,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "47d85863db718fc4",
                                                "remaining": 1.15,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "真言术：盾": {
                                                "title": "真言术：盾",
                                                "remaining": 19.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "69fe891d3e8c3f69": {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 18.0,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "ea1bcdf5faf4874c": {
                                                "title": "ea1bcdf5faf4874c",
                                                "remaining": 0.05,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "a8869cea08bc48fe": {
                                                "title": "a8869cea08bc48fe",
                                                "remaining": 2.2,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "47d85863db718fc4": {
                                                "title": "47d85863db718fc4",
                                                "remaining": 1.15,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                },
                                "debuff": [
                                        {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "debuff_dict": {
                                        "13b0f20a40628634": {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                }
                        }
                },
                "party2": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 100.0,
                                "selectd": false,
                                "damage_absorbs": 12.5,
                                "heal_absorbs": 0.0,
                                "class": "MAGE",
                                "role": "DPS"
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 12.0,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "69fe891d3e8c3f69": {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 12.0,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                },
                                "debuff": [
                                        {
                                                "title": "50310157070e0238",
                                                "remaining": 0.0,
                                                "type": "CURSE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "50310157070e0238",
                                                "remaining": 11.0,
                                                "type": "CURSE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "debuff_dict": {
                                        "50310157070e0238": {
                                                "title": "50310157070e0238",
                                                "remaining": 11.0,
                                                "type": "CURSE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "13b0f20a40628634": {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                }
                        }
                },
                "party3": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 89.80392156862746,
                                "selectd": false,
                                "damage_absorbs": 0.0,
                                "heal_absorbs": 0.0,
                                "class": "HUNTER",
                                "role": "DPS"
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 10.5,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "69fe891d3e8c3f69": {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 10.5,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                },
                                "debuff": [
                                        {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "debuff_dict": {
                                        "13b0f20a40628634": {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                }
                        }
                },
                "party4": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 90.19607843137256,
                                "selectd": false,
                                "damage_absorbs": 0.0,
                                "heal_absorbs": 0.0,
                                "class": "SHAMAN",
                                "role": "DPS"
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 10.5,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "69fe891d3e8c3f69": {
                                                "title": "69fe891d3e8c3f69",
                                                "remaining": 10.5,
                                                "type": "NONE",
                                                "count": 0,
                                                "forever": false
                                        }
                                },
                                "debuff": [
                                        {
                                                "title": "50310157070e0238",
                                                "remaining": 9.0,
                                                "type": "CURSE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                ],
                                "debuff_dict": {
                                        "50310157070e0238": {
                                                "title": "50310157070e0238",
                                                "remaining": 9.0,
                                                "type": "CURSE",
                                                "count": 0,
                                                "forever": false
                                        },
                                        "13b0f20a40628634": {
                                                "title": "13b0f20a40628634",
                                                "remaining": 3.3,
                                                "type": "MAGIC",
                                                "count": 0,
                                                "forever": false
                                        }
                                }
                        }
                }
        },
        "signal": {
                "1": "31,31,31",
                "2": "63,63,63",
                "3": "95,95,95",
                "4": "127,127,127",
                "5": "159,159,159",
                "6": "191,191,191",
                "7": "223,223,223",
                "8": "255,255,255"
        }
}
```