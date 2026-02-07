"""主窗口模块 - GUI主窗口，集成日志功能。"""

import datetime
import json
import re
import sys
from typing import Any

import dxcam
import numpy as np
from PySide6.QtCore import Qt, QUrl, Signal, QObject
from PySide6.QtGui import QClipboard, QDesktopServices, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QVBoxLayout, QWidget
)

from Database import NodeTitleManager
from IconLibraryDialog import IconLibraryDialog
from Node import Node
from NodeExtractorData import extract_all_data
from Utils import find_template_bounds, app_dir
from Worker import CameraWorker, WebServerWorker


####### 日志信号发射器 #######

class LogEmitter(QObject):
    """日志信号发射器 - 多线程环境下安全发送日志到主线程。"""

    log_signal = Signal(str)

    def __init__(self, log_display: QTextEdit) -> None:
        super().__init__()
        self.log_display: QTextEdit = log_display
        self.log_signal.connect(self._append_log)

    def _append_log(self, text: str) -> None:
        """在主线程中追加日志。"""
        self.log_display.append(text)

    def emit_log(self, text: str) -> None:
        """发射日志信号。"""
        self.log_signal.emit(text)


####### 日志重定向器 #######

class LogRedirector:
    """日志重定向器 - 将print输出重定向到QTextEdit控件。"""

    def __init__(self, log_emitter: LogEmitter) -> None:
        self.log_emitter: LogEmitter = log_emitter
        self.original_stdout = sys.stdout

    def write(self, text: str) -> None:
        # 同时输出到原始 stdout（console）
        self.original_stdout.write(text)
        if text.strip():  # 只处理非空内容
            # 添加时间戳
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_text: str = f'[{timestamp}] {text.rstrip()}'
            # 使用信号发射器（线程安全）
            self.log_emitter.emit_log(formatted_text)

    def flush(self) -> None:
        """刷新输出缓冲区。"""
        self.original_stdout.flush()


####### 主窗口类 #######

class MainWindow(QWidget):
    """主窗口类 - 负责UI展示和用户交互。"""

    def __init__(self) -> None:
        """初始化主窗口。"""
        super().__init__()

        # 像素数据存储
        self.pixel_dump: dict[str, Any] = {'error': '相机尚未启动'}

        # 数据刷新开关
        self.data_refresh_enabled: bool = True

        # 窗口基本设置
        self.setWindowTitle('PixelDumper')

        # 计算窗口尺寸（屏幕的80%）
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width: int = int(screen_geometry.width() * 0.8)
        height: int = int(screen_geometry.height() * 0.8)
        self.resize(width, height)

        # 窗口居中
        x: int = (screen_geometry.width() - width) // 2
        y: int = (screen_geometry.height() - height) // 2
        self.move(x, y)
        self.setFixedHeight(height)

        # DXCam相机对象
        self.camera: Any = None

        # 相机工作线程
        self.camera_worker: CameraWorker | None = None
        self.camera_running: bool = False
        self.current_fps: int = 10

        # 设备/显示器编号
        self.device_idx: int = 0
        self.output_idx: int = 0

        # 显示器列表 [(device_idx, output_idx, display_text), ...]
        self.monitor_list: list[tuple[int, int, str]] = []

        # 初始化NodeTitleManager并设置到Node类
        self.title_manager: NodeTitleManager = NodeTitleManager()
        Node.set_title_manager(self.title_manager)

        # Web服务器
        self.web_server: WebServerWorker | None = None

        # 图标库对话框
        self.icon_library_dialog: IconLibraryDialog | None = None

        # 初始化UI
        self.init_ui()

        # 启动Web服务器
        self._start_web_server()

        # 初始刷新显示器列表
        self.refresh_device_info()

    def _start_web_server(self) -> None:
        """启动Web服务器。"""
        self.web_server = WebServerWorker(self._get_pixel_dump)
        self.web_server.start()

    def _get_pixel_dump(self) -> dict[str, Any]:
        """获取当前像素数据的回调函数（供Web服务器使用）。"""
        return self.pixel_dump

    ####### UI初始化 #######

    def init_ui(self) -> None:
        """初始化用户界面。"""
        main_layout: QVBoxLayout = QVBoxLayout()

        # 创建第一层布局（控制栏）
        self.create_control_layout()
        main_layout.addLayout(self.l1_layout)

        # 创建第二层布局（数据显示区）
        self.create_display_layout()
        main_layout.addLayout(self.l2_layout)

        self.setLayout(main_layout)

    def create_control_layout(self) -> None:
        """创建第一层布局：控制按钮和设置。"""
        self.l1_layout: QHBoxLayout = QHBoxLayout()
        self.l1_left_layout: QHBoxLayout = QHBoxLayout()

        ####### API地址显示 #######
        self.api_label: QLabel = QLabel('API地址：')
        self.api_url_input: QLineEdit = QLineEdit()
        self.api_url_input.setText('http://127.0.0.1:65131')
        self.api_url_input.setReadOnly(True)
        self.api_url_input.setFixedWidth(180)
        self.api_url_input.selectionChanged.connect(self._on_api_url_selected)

        self.api_visit_button: QPushButton = QPushButton('访问API')
        self.api_visit_button.clicked.connect(self._on_visit_api_clicked)

        self.l1_left_layout.addWidget(self.api_label)
        self.l1_left_layout.addWidget(self.api_url_input)
        self.l1_left_layout.addWidget(self.api_visit_button)

        # 分隔
        self.l1_left_layout.addSpacing(20)

        # 显示器选择下拉框
        self.monitor_label: QLabel = QLabel('选择显示器：')
        self.monitor_combo: QComboBox = QComboBox()
        self.monitor_combo.setFixedWidth(400)
        self.monitor_combo.currentIndexChanged.connect(self.on_monitor_selected)

        # FPS设置
        self.fps_label: QLabel = QLabel('FPS：')
        self.fps_input: QLineEdit = QLineEdit()
        self.fps_input.setValidator(QIntValidator(1, 60))
        self.fps_input.setText('10')
        self.fps_input.setFixedWidth(60)
        self.fps_input.textChanged.connect(self.on_fps_changed)

        # 功能按钮
        self.refresh_info_button: QPushButton = QPushButton('刷新显示器列表')
        self.refresh_info_button.clicked.connect(self.refresh_device_info)

        self.camera_toggle_button: QPushButton = QPushButton('启动')
        self.camera_toggle_button.clicked.connect(self.toggle_camera)

        self.refresh_button: QPushButton = QPushButton('暂停刷新日志')
        self.refresh_button.clicked.connect(self.on_refresh_button_clicked)

        # 图标库管理按钮
        self.icon_library_button: QPushButton = QPushButton('管理图标库')
        self.icon_library_button.clicked.connect(self.open_icon_library)

        # 左侧布局添加控件
        self.l1_left_layout.addWidget(self.monitor_label)
        self.l1_left_layout.addWidget(self.monitor_combo)
        self.l1_left_layout.addWidget(self.fps_label)
        self.l1_left_layout.addWidget(self.fps_input)
        self.l1_left_layout.addWidget(self.refresh_info_button)
        self.l1_left_layout.addWidget(self.camera_toggle_button)
        self.l1_left_layout.addWidget(self.icon_library_button)
        self.l1_left_layout.addStretch()
        self.l1_left_layout.addWidget(self.refresh_button)

        # 右侧链接按钮
        self.l1_right_layout: QHBoxLayout = QHBoxLayout()
        self.github_button: QPushButton = QPushButton('Github')
        self.github_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/liantian-cn/PixelDumper'))
        )
        self.discord_button: QPushButton = QPushButton('Discord')
        self.discord_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://discord.gg/DX77uHc9'))
        )
        self.l1_right_layout.addWidget(self.github_button)
        self.l1_right_layout.addWidget(self.discord_button)

        # 合并到主布局
        self.l1_layout.addLayout(self.l1_left_layout)
        self.l1_layout.addStretch()
        self.l1_layout.addLayout(self.l1_right_layout)

    def create_display_layout(self) -> None:
        """创建第二层布局：数据显示和日志。"""
        self.l2_layout: QHBoxLayout = QHBoxLayout()

        # 左侧数据显示区（75%宽度）
        self.l2l_layout: QVBoxLayout = QVBoxLayout()
        self.data_display: QTextEdit = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.l2l_layout.addWidget(self.data_display)

        # 右侧日志显示区（25%宽度）
        self.l2r_layout: QVBoxLayout = QVBoxLayout()
        self.log_display: QTextEdit = QTextEdit()
        self.log_display.setReadOnly(True)
        self.l2r_layout.addWidget(self.log_display)

        # 设置拉伸比例
        self.l2_layout.addLayout(self.l2l_layout, 3)
        self.l2_layout.addLayout(self.l2r_layout, 1)

        # 重定向 print 输出到日志显示区
        log_emitter: LogEmitter = LogEmitter(self.log_display)
        sys.stdout = LogRedirector(log_emitter)
        self.data_display.setText(json.dumps(self.pixel_dump, indent=2, ensure_ascii=False))

    ####### 图标库管理 #######

    def open_icon_library(self) -> None:
        """打开图标库管理对话框。"""
        if self.icon_library_dialog is None or not self.icon_library_dialog.isVisible():
            self.icon_library_dialog = IconLibraryDialog(self.title_manager, self)
            self.icon_library_dialog.show()
        else:
            self.icon_library_dialog.raise_()
            self.icon_library_dialog.activateWindow()

    ####### 事件处理：设置变更 #######

    def on_monitor_selected(self, index: int) -> None:
        """显示器选择变化处理。"""
        if index < 0 or index >= len(self.monitor_list):
            return

        device_idx, output_idx, _ = self.monitor_list[index]
        self.device_idx = device_idx
        self.output_idx = output_idx

        timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_display.append(
            f'[{timestamp}] 选择显示器: Device[{device_idx}] Output[{output_idx}]'
        )

    def on_fps_changed(self, text: str) -> None:
        """FPS输入框变化处理。"""
        if text == '':
            return

        try:
            fps: int = int(text)

            # 范围检查
            if fps < 1 or fps > 60:
                return

            self.current_fps = fps

            # 记录日志
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message: str = f'[{timestamp}] FPS 设置为 {fps}'
            self.log_display.append(log_message)

        except ValueError:
            return

    def on_refresh_button_clicked(self) -> None:
        """暂停/恢复刷新按钮处理。"""
        self.data_refresh_enabled = not self.data_refresh_enabled

        if self.data_refresh_enabled:
            self.refresh_button.setText('暂停刷新日志')
            self.data_display.setText(json.dumps(self.pixel_dump, indent=2, ensure_ascii=False))
        else:
            self.refresh_button.setText('恢复刷新日志')

    ####### 事件处理：设备信息 #######

    def refresh_device_info(self) -> None:
        """刷新并显示DXCam设备信息，更新下拉框。"""
        try:
            output_info: str = dxcam.output_info()

            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f'[{timestamp}] DXCam 输出信息：')
            self.log_display.append(output_info)

            # 解析输出信息
            self.monitor_list = self._parse_output_info(output_info)

            # 更新下拉框
            self.monitor_combo.clear()
            for device_idx, output_idx, display_text in self.monitor_list:
                self.monitor_combo.addItem(display_text, (device_idx, output_idx))

            # 如果有显示器，默认选择第一个
            if self.monitor_list:
                self.device_idx = self.monitor_list[0][0]
                self.output_idx = self.monitor_list[0][1]
                self.log_display.append(
                    f'[{timestamp}] 找到 {len(self.monitor_list)} 个显示器'
                )
            else:
                self.log_display.append(f'[{timestamp}] 未找到显示器')

        except Exception as e:
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f'[{timestamp}] 设备信息获取失败: {e}')

    def _parse_output_info(self, output_info: str) -> list[tuple[int, int, str]]:
        """解析 dxcam.output_info() 的输出。

        Args:
            output_info: dxcam.output_info() 返回的字符串

        Returns:
            [(device_idx, output_idx, display_text), ...]
        """
        monitors: list[tuple[int, int, str]] = []

        # 解析每行，格式如: Device[0] Output[0]: Res:(1920, 1080) Rot:0 Primary:True
        pattern = r'Device\[(\d+)\]\s+Output\[(\d+)\]:\s+(.+)'
        for line in output_info.strip().split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                device_idx = int(match.group(1))
                output_idx = int(match.group(2))
                info = match.group(3).strip()
                display_text = f'Device[{device_idx}] Output[{output_idx}]: {info}'
                monitors.append((device_idx, output_idx, display_text))

        return monitors

    ####### 事件处理：相机控制 #######

    def toggle_camera(self) -> None:
        """切换相机启停状态。"""
        # 启动相机
        if not self.camera_running:
            # 检查是否选择了显示器
            if not self.monitor_list:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] 未检测到显示器，请先刷新显示器列表并选择')
                return

            # 创建DXCam相机对象
            try:
                self.camera = dxcam.create(
                    device_idx=self.device_idx,
                    output_idx=self.output_idx
                )
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(
                    f'[{timestamp}] DXCam 相机创建成功 '
                    f'(device={self.device_idx}, output={self.output_idx})'
                )
            except Exception as e:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] 相机初始化失败: {e}')
                return

            # 抓一张全屏图查找模板标记
            try:
                frame: np.ndarray | None = self.camera.grab()
                if frame is None:
                    timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log_display.append(f'[{timestamp}] 屏幕捕获失败，请检查显示器是否可用')
                    self._cleanup_camera()
                    return
            except Exception as e:
                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f'[{timestamp}] 屏幕捕获异常: {e}')
                self._cleanup_camera()
                return

            # 查找模板标记
            try:
                template_path = str(app_dir / 'mark8.png')
                bounds: tuple[int, int, int, int] | None = find_template_bounds(frame, template_path)
                if bounds is None:
                    timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log_display.append(f'[{timestamp}] 未检测到游戏标记，请确保游戏内插件已启用并可见')
                    self._cleanup_camera()
                    return
            except Exception as e:
                import traceback

                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                error_msg: str = f'[{timestamp}] 标记识别异常:\\n{traceback.format_exc()}'
                self.log_display.append(error_msg)
                self._cleanup_camera()
                return

            left, top, right, bottom = bounds
            self.log_display.append(
                f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] '
                f'找到标记位置: ({left}, {top}, {right}, {bottom})'
            )

            # 创建并启动工作线程
            self.camera_worker = CameraWorker(self.camera, self.current_fps, bounds)
            self.camera_worker.data_signal.connect(self.process_captured_frame)
            self.camera_worker.log_signal.connect(self.append_camera_log)
            self.camera_worker.start()
            self.camera_running = True
            self.camera_toggle_button.setText('停止')

            # 锁定控件
            self.monitor_combo.setEnabled(False)
            self.fps_input.setEnabled(False)
            self.refresh_info_button.setEnabled(False)

            self.log_display.append(
                f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] '
                f'CameraWorker 启动'
            )

        # 停止相机
        else:
            if self.camera_worker:
                self.camera_worker.stop()
                self.camera_worker = None

            self._cleanup_camera()

            self.camera_running = False
            self.camera_toggle_button.setText('启动')

            # 解锁控件
            self.monitor_combo.setEnabled(True)
            self.fps_input.setEnabled(True)
            self.refresh_info_button.setEnabled(True)

            # 更新pixel_dump为已停止状态
            self.pixel_dump = {'error': '已停止'}
            if self.data_refresh_enabled:
                self.data_display.setText(
                    json.dumps(self.pixel_dump, indent=2, ensure_ascii=False)
                )

            self.log_display.append(
                f'[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] CameraWorker 停止'
            )

    def _cleanup_camera(self) -> None:
        """清理相机资源。"""
        if self.camera is not None:
            try:
                self.camera.stop()
            except Exception:
                pass
            try:
                self.camera.release()
            except Exception:
                pass
            del self.camera
            self.camera = None

    ####### 事件处理：相机数据与日志 #######

    def process_captured_frame(self, frame: np.ndarray, camera_status: str) -> None:
        """处理相机捕获的图像数据。

        解析像素数据并更新UI显示。
        """
        if camera_status == 'ok':
            try:
                # 创建像素数据提取器
                from Node import NodeExtractor
                extractor: NodeExtractor = NodeExtractor(frame)

                ####### 遮挡检测 #######
                node_1_16 = extractor.node(1, 16)
                node_50_1 = extractor.node(50, 1)
                node_1_1 = extractor.node(1, 1)
                node_50_16 = extractor.node(50, 16)
                node_51_4 = extractor.node(51, 4)

                validation_errors: list[str] = []

                if not node_1_16.is_black:
                    validation_errors.append(f'(1,16)应为黑色')

                if not node_50_1.is_black:
                    validation_errors.append(f'(50,1)应为黑色')

                if not node_1_1.is_pure:
                    validation_errors.append(f'(1,1)应为纯色(参考色)')
                if not node_50_16.is_pure:
                    validation_errors.append(f'(50,16)应为纯色(参考色)')

                if node_1_1.is_pure and node_50_16.is_pure:
                    if node_1_1.color_string != node_50_16.color_string:
                        validation_errors.append(f'(1,1)和(50,16)颜色不匹配: {node_1_1.color_string} != {node_50_16.color_string}')
                if node_51_4.is_pure:
                    validation_errors.append(f'(51,4)应为非纯色(数据区)')

                if validation_errors:
                    self.pixel_dump.clear()
                    self.pixel_dump.update({
                        'error': '游戏窗口被遮挡或插件未加载，请检查游戏窗口是否可见',
                        'details': validation_errors,
                    })
                    # 更新数据显示（如果刷新未暂停）
                    if self.data_refresh_enabled:
                        self.data_display.setText(
                            json.dumps(self.pixel_dump, indent=8, ensure_ascii=False)
                        )
                    return

                # 提取所有像素数据
                dump_data: dict[str, Any] = extract_all_data(extractor)
                self.pixel_dump.clear()
                self.pixel_dump.update(dump_data)

                # 更新数据显示（如果刷新未暂停）
                if self.data_refresh_enabled:
                    self.data_display.setText(
                        json.dumps(self.pixel_dump, indent=8, ensure_ascii=False)
                    )

            except Exception as e:
                import traceback

                timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                error_msg: str = f'[{timestamp}] 数据处理异常:\\n{traceback.format_exc()}'
                self.log_display.append(error_msg)
        else:
            # 捕获失败记录错误
            timestamp: str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f'[{timestamp}] 捕获失败，状态: {camera_status}')

    def append_camera_log(self, log_message: str) -> None:
        """处理相机线程日志。"""
        self.log_display.append(log_message)

    ####### API相关事件处理 #######

    def _on_api_url_selected(self) -> None:
        """API地址输入框文本被选择时，自动复制到剪贴板。"""
        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setText(self.api_url_input.text())

    def _on_visit_api_clicked(self) -> None:
        """访问API按钮点击事件 - 用浏览器打开API地址。"""
        QDesktopServices.openUrl(QUrl(self.api_url_input.text()))

    def closeEvent(self, event: Any) -> None:
        """窗口关闭事件。"""
        # 停止相机线程
        if self.camera_worker:
            self.camera_worker.stop()
            self.camera_worker = None

        # 释放相机资源
        self._cleanup_camera()

        # 停止Web服务器
        if self.web_server:
            self.web_server.stop()
            self.web_server = None

        event.accept()
