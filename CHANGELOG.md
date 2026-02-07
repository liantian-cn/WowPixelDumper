# Changelog

## [2026.02.07] - 大量更新

##  较大改进点

### 一、Dumper的逻辑变化

原本的结构
`NodeExtractor` -> `Node` 
修改为
`NodeExtractor` -> `Node`  -> `PixelBlock`

PixelBlock是不包含坐标的像素块，承担计算任务。
Node是包含坐标的节点，`Node`的`full`、`middle`、`inner`、`sub`属性对应不同大小的`PixelBlock`对象。

### 二、新增布局 MixedNode 
-  将现有的8x8节点再次细分为4个4x4像素。
- 在lua内，使用CreateMixedNode创建
- 在Dumper内，使用`Node.mixNode`，返回4个`PixBlock`对象，每个`PixBlock`对象**仅包含4个像素**。

<img width="200" alt="5a8dc638-94f0-4118-8a6c-e8f4641c3098" src="https://github.com/user-attachments/assets/869196c6-0b03-4de4-8f6e-0d94d092a6ad" />

### 三、新增布局 FootnoteNode
- 仅在lua中生效，使用CreateFootnoteNode创建。
- 使用FootnoteNode将更容易分辨可驱散的buff。
- 玩家debuff、队友debuff使用这种类型的图标。

<img width="200"  alt="a2d60395-e062-495a-abdf-cffa29d57e04" src="https://github.com/user-attachments/assets/2df1417e-78ee-4459-bed1-e8f62ef6b80c" />

## 一般改进点

### 布局变化

<img width="720" alt="27a3cb9d-9c8b-43ea-959c-f242a96c1046" src="https://github.com/user-attachments/assets/e63400b8-39cc-4b40-a890-fcbcc8e64381" />

- 单个`Aura`的高度降低为3，采用了`MixedNode` ，额外提供了技能是否为永久aura的判断。
- 单个`Spell`的高度降低为3，采用了`MixedNode` ，额外提供是否学会和是否可用的判断。close #6  close #5 
- 增加了一个Signal(信号)区域，并且可以游戏内使用`/pd [1-8] [0-255] [0-255] [0-255] `，用于后面的循环编写。
- 数量变化
  - 目标Debuff扩列到16 close #4 
  - 队友的Debuff减少的6
 
### 功能改进

- 默认从系统的冷却管理器加载全部冷却技能，不再需要编写职业文件。 close #8 
- 技能图标加入刷新，这样技能覆盖就可以被观察到 close #7 

### 插件端的小变化
- 稍微优化了API的性能。

### Dumper变化
- 默认图标相似度阈值从0.95提高到0.97
- 修改因为相似度而引入的标题后，状态变为手工输入。





## [2026.02.07] - 大量更新

### 插件端 (Addons)

- **像素块(node)尺寸调整**：从 6×6 提高到 8×8
  - 原生像素缩放到 6×6 会产生差异，导致每次启动游戏特征值变化较大
  - 实际用于比较的是内部的 6×6，减少边缘模糊的影响
  
- **全新自制字体**：让层数显示更可靠

### 应用端 (Script)

- **像素比对方式变更**：
  - 不再基于 hash，而是基于已添加 title 的像素的余弦相似度
  - 为了性能，一旦确定 title，刷新还是基于 xxhash

- **数据存储迁移**：
  - 不再使用 `hashmap.json` 保存像素到 title 的映射
  - 改为使用 SQLite 数据库存储
  - 新增易于维护的 GUI 界面管理图标库

- **截图方式回退**：
  - `user32.PrintWindow` 产生了太多错误
  - 重新使用 `dxcam` 进行屏幕捕获

- **Web API 回归**：
  - Flask 的 API Server 被加回来了
  - Rotation 开发将会是独立的项目