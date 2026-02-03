# 注意

项目分Addons和Script两部分，两部分完全独立。任务只可能针对其中一部分，任何修改，仅限在一部分中修改，当无法理解时，询问用户。

# Addons

- **WowPixelDumper.toc** - 插件清单，定义加载顺序
- **WowPixelDumper.lua** - 主插件，创建像素UI框架，显示游戏状态（Buff/Debuff/技能/血量/队伍等）
- **Setting.lua** - 设置界面（FPS、距离检查）
- **class/Priest.lua** - 牧师技能配置（戒律牧）
- **class/Druid.lua** - 德鲁伊技能配置（预留）

# Script

- **WowPixelDumper.py** - GUI主程序，屏幕捕获 + Flask API服务
- **Dumper.py** - 图像处理核心，像素节点解析、数据提取
- **ColorMap.json** - 颜色映射（职业/Buff类型/职责）
- **HashMap.json** - 技能图标哈希映射
