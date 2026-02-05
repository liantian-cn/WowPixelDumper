# WowPixelDumper 项目规范

## 项目结构（重构后）

```
Dumper/
├── DumperGUI.py          # 程序入口
├── MainWindow.py         # 主窗口（集成日志功能）
├── Worker.py             # 工作线程（CameraWorker + WebServerWorker）
├── IconLibraryDialog.py  # 图标库对话框（集成图片委托类）
├── Node.py               # Node + NodeExtractor
├── NodeExtractorData.py  # extract_all_data + ColorMap加载
├── Utils.py              # 独立工具函数（图像处理、模板匹配）
├── Database.py           # NodeTitleManager
├── comment_deleter.py    # AST注释删除工具（通用工具）
└── test_script.py        # 功能测试脚本
```

## 代码风格规范

### 1. Import规范

**强制要求：所有import必须在文件头部**

```python
# 正确
import os
from pathlib import Path
import numpy as np

def process():
    pass

# 错误
def process():
    import numpy as np  # 禁止！
    pass
```

**import分组顺序：**
1. 标准库（os, sys, datetime等）
2. 第三方库（numpy, cv2, PIL等）
3. 项目内部模块（from Node import xxx）

### 2. 注释规范

**文件头docstring：极简单行**

```python
"""窗口捕获模块 - Win32 API窗口截图与相机工作线程。"""
```

**区域分隔注释：使用井号行**

```python
####### Win32 API初始化 #######

####### 像素区域访问 #######

####### 信号定义 #######
```

### 3. TypeHint规范

使用 Python 3.12+ 语法：

```python
def process_data(
    data: np.ndarray,
    threshold: float = 0.5,
    enabled: bool = True
) -> dict[str, Any] | None:
    """处理数据。"""
    pass

# 使用 | 替代 Optional 和 Union
def find_item() -> str | None:
    pass

# 使用内置泛型
def get_items() -> list[dict[str, Any]]:
    pass
```

### 4. 类与函数命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `CameraWorker`, `NodeTitleManager` |
| 函数/方法 | snake_case | `capture_window`, `get_title` |
| 常量 | UPPER_SNAKE_CASE | `SIMILARITY_THRESHOLD` |
| 私有方法 | _前缀 | `_init_database`, `_load_data` |
| 保护属性 | _前缀 | `self._hash_cache`, `self._running` |

## 模块职责说明

### Utils.py
- `app_dir`: 应用程序根目录 Path
- `screenshot_to_array()`: PIL截图转numpy数组
- `load_template()`: 加载模板图片
- `find_all_matches()`: OpenCV模板匹配
- `find_template_bounds()`: 查找模板边界

### Database.py
- `TitleRecord`: 标题记录数据类
- `cosine_similarity()`: 计算余弦相似度
- `NodeTitleManager`: 节点标题管理器（SQLite数据库、hash匹配、余弦相似度匹配）

### Node.py
- `Node`: 8x8像素节点类（颜色、亮度、哈希、标题解析）
- `NodeExtractor`: 像素数据提取器（原DataExtractor）
  - `node()`: 获取指定坐标节点（支持链式调用）
  - `read_health_bar()`: 读取白色进度条
  - `read_spell_sequence()`: 读取技能序列
  - `read_aura_sequence()`: 读取Buff/Debuff序列

### NodeExtractorData.py
- `_ColorMap`: 颜色映射配置（自动加载ColorMap.json）
- `extract_all_data(extractor)`: 提取完整游戏状态数据

### Worker.py
- `CameraWorker`: DXCam相机工作线程
- `WebServerWorker`: Flask HTTP服务器线程（端口65131）

### IconLibraryDialog.py
- `IconLibraryDialog`: 图标库管理对话框（4个Tab）
- `NodeImageDelegate`: 节点图片显示委托
- `HashDisplayDelegate`: Hash短格式显示委托
- `SimilarityDisplayDelegate`: 相似度彩色显示委托

### MainWindow.py
- `LogEmitter`: 日志信号发射器
- `LogRedirector`: 日志重定向器
- `MainWindow`: 主窗口类（UI展示、相机控制、数据处理）

### DumperGUI.py
- `main()`: 程序入口

### comment_deleter.py
- `delete_comments(input_file, output_file)`: 删除Python文件中的所有注释和docstring
- 支持命令行: `python comment_deleter.py input.py [output.py]`

## 数据流向

```
DumperGUI.py (入口)
    ↓
MainWindow.py (UI控制)
    ├── Worker.py (CameraWorker捕获)
    │       ↓
    ├── Utils.py (find_template_bounds定位)
    │       ↓
    ├── NodeExtractorData.py (extract_all_data提取)
    │       ↓
    ├── Node.py (Node解析)
    │       ↓
    ├── Database.py (NodeTitleManager标题匹配)
    │       ↓
    └── WebServerWorker (HTTP API输出)
```

## 关键变更点

1. **DataExtractor → NodeExtractor**: 类名变更，实例化改为 `extractor = NodeExtractor(frame)`

2. **get_node → node**: 方法名变更，支持链式调用如 `extractor.node(1, 17).is_black`

3. **NodeTitleManager 解耦**: 移除对Node类的直接引用，改为通过参数传递属性

4. **ColorMap 加载**: 从独立模块改为在NodeExtractorData.py中自动加载

5. **日志系统集成**: LogEmitter和LogRedirector并入MainWindow.py

6. **路径管理**: 使用 `app_dir = Path(__file__).resolve().parent` 统一管理资源路径

## 依赖要求

```
numpy>=1.24.0
Pillow>=9.0.0
PySide6>=6.4.0
opencv-python>=4.7.0
dxcam>=0.3.0
xxhash>=3.0.0
flask>=2.0.0
```

## 运行方式

```bash
cd Dumper
python DumperGUI.py
```

或

```bash
python Dumper/DumperGUI.py
```

## 测试

```bash
cd Dumper
python test_script.py