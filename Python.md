# Python 版本技术栈（`Dumper\`）

## 运行平台与语言

- Python 3（含类型注解，较多 `typing` 使用）。
- Windows 环境（依赖 DXCam、互斥锁调用 Win32 API）。

## UI 与交互

- `PySide6`：桌面 GUI（主窗体、对话框、信号槽、多线程 UI 通信）。

## 采集与图像处理

- `dxcam`：屏幕采集。
- `numpy`：像素数组与数值计算。
- `opencv-python (cv2)`：模板匹配。
- `Pillow (PIL)`：图片读取与格式转换。

## 数据服务与网络

- `Flask`：内置 HTTP API 服务（后台线程运行）。
- JSON：标准输出格式，面向轮询消费。

## 存储与匹配

- `sqlite3`：本地图标标题库持久化。
- `xxhash`：图标中间区域 hash。
- 余弦相似度：图标模糊匹配与自动补录。

## 工程与发布

- `Nuitka`：打包为 Windows 可执行文件（`deploy.py`）。
- `DumperGUI.cmd`：命令行快捷启动。
- `test_script.py`：模块级验证脚本。

