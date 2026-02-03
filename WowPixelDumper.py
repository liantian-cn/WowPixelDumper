import json
import time
import datetime
from typing import List, Tuple, Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QInputDialog, QApplication, QLabel, QPushButton, QComboBox
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import QThread, Signal, Qt, QUrl, QTimer
from PySide6.QtGui import QDesktopServices
import win32gui
import win32ui
from PIL import Image
import ctypes
import numpy as np
from Dumper import find_template_bounds, PixelDumper, save_user_input_hash, hashstr_used


# ============================================
# Win32 API 初始化
# ============================================
user32 = ctypes.WinDLL('user32', use_last_error=True)
PrintWindow = user32.PrintWindow
PrintWindow.restype = ctypes.c_bool
PrintWindow.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]

# 打印窗口的标志位
PW_CLIENTONLY = 1          # 仅客户区
PW_RENDERFULLCONTENT = 2   # 渲染完整内容（包括DWM）


def capture_window(
    hwnd: int,
    left: Optional[int] = None,
    top: Optional[int] = None,
    right: Optional[int] = None,
    bottom: Optional[int] = None
) -> Tuple[Optional[np.ndarray], str]:
    """
    捕获指定窗口的屏幕内容
    """
    # 检查句柄有效性
    if not hwnd:
        return None, "invalid_hwnd"

    try:
        # 获取窗口客户区矩形
        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
        client_width = client_right - client_left
        client_height = client_bottom - client_top

        # 检查窗口是否可见
        if client_width <= 0 or client_height <= 0:
            return None, "window_not_visible"

        # 确定捕获区域
        capture_left = left if left is not None else client_left
        capture_top = top if top is not None else client_top
        capture_right = right if right is not None else client_right
        capture_bottom = bottom if bottom is not None else client_bottom

        # 边界检查与限制
        capture_left = max(client_left, min(capture_left, client_right))
        capture_top = max(client_top, min(capture_top, client_bottom))
        capture_right = max(capture_left, min(capture_right, client_right))
        capture_bottom = max(capture_top, min(capture_bottom, client_bottom))

        # 计算实际捕获尺寸
        width = capture_right - capture_left
        height = capture_bottom - capture_top

        # 检查捕获区域有效性
        if width <= 0 or height <= 0:
            return None, "invalid_capture_region"

        # ============================================
        # Win32 GDI 资源初始化
        # ============================================
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        # 创建位图对象
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, client_width, client_height)
        saveDC.SelectObject(saveBitMap)

        # 调用PrintWindow捕获窗口
        result = PrintWindow(hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)

        # 检查捕获结果
        if not result:
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            return None, "print_window_failed"

        # 提取位图数据
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        # 转换为PIL图像
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # 裁剪指定区域
        if left is not None or top is not None or right is not None or bottom is not None:
            crop_left = capture_left - client_left
            crop_top = capture_top - client_top
            crop_right = crop_left + width
            crop_bottom = crop_top + height
            img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

        # 转换为numpy数组
        array = np.array(img)

        # ============================================
        # 清理GDI资源
        # ============================================
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return array, "ok"

    except Exception as e:
        return None, f"exception: {str(e)}"


class CameraWorker(QThread):
    """
    相机工作线程
    负责持续捕获游戏窗口画面
    """

    # 信号定义
    data_signal = Signal(np.ndarray, str)   # 图像数据信号
    log_signal = Signal(str)                 # 日志信号
    region_signal = Signal(int, int, int, int)  # 捕获区域更新信号

    def __init__(self, windows_handle: int, fps: int = 10) -> None:
        """
        初始化相机工作线程
        """
        super().__init__()

        # 运行状态标志
        self.running = False

        # 目标窗口句柄
        self.windows_handle = windows_handle

        # 帧率设置
        self.fps = fps

        # 捕获区域坐标
        self.left = 0
        self.top = 0

        # 获取屏幕尺寸作为默认右下边界
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.right = geometry.width()
        self.bottom = geometry.height()

        # FPS统计相关
        self._capture_count = 0
        self._last_log_time = 0

        # 连接区域更新信号
        self.region_signal.connect(self.update_region)

    # ============================================
    # 区域管理
    # ============================================

    def update_region(self, left: int, top: int, right: int, bottom: int) -> None:
        """
        更新捕获区域
        """
        self.left = left
        self.top = top

        # 确保右下边界有效
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.right = right if right > 0 else geometry.width()
        self.bottom = bottom if bottom > 0 else geometry.height()

    # ============================================
    # 线程生命周期
    # ============================================

    def run(self) -> None:
        """
        主循环：按指定FPS捕获窗口画面
        """
        self.running = True

        # 计算帧间隔
        interval = 1.0 / self.fps

        # 初始化时间记录
        last_capture_time = 0
        self._capture_count = 0
        self._last_log_time = time.time()

        while self.running:
            current_time = time.time()

            # 检查是否到达下一帧时间
            if current_time - last_capture_time >= interval:
                # 执行窗口捕获
                array, status = capture_window(
                    self.windows_handle,
                    self.left,
                    self.top,
                    self.right,
                    self.bottom
                )

                self._capture_count += 1

                # 发送数据信号
                if array is not None:
                    self.data_signal.emit(array, status)
                else:
                    self.data_signal.emit(np.array([]), status)

                last_capture_time = current_time

                # 每10秒输出一次FPS统计
                if current_time - self._last_log_time >= 10:
                    actual_fps = self._capture_count / 10.0
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log_signal.emit(f"[{timestamp}] 实际FPS: {actual_fps:.1f}, 抓取次数: {self._capture_count}")
                    self._capture_count = 0
                    self._last_log_time = current_time
            else:
                # 短暂休眠避免CPU占用过高
                time.sleep(0.01)

    def stop(self) -> None:
        """
        停止工作线程
        """
        self.running = False
        self.wait()


class MainWindow(QWidget):
    """
    主窗口类
    负责UI展示和用户交互
    """

    def __init__(self) -> None:
        """
        初始化主窗口
        """
        super().__init__()

        # 像素数据存储
        self.pixel_dump: Dict[str, Any] = {}

        # 对话框状态标志
        self.dialog_visible = False
        self.dialog_cooldown = False

        # 数据刷新开关
        self.data_refresh_enabled = True

        # 窗口基本设置
        self.setWindowTitle('WowPixelDumper')

        # 计算窗口尺寸（屏幕的80%）
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        self.resize(width, height)

        # 窗口居中
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        self.move(x, y)
        self.setFixedHeight(height)

        # 窗口句柄列表
        self.windows_handle_list: List[Tuple[int, str]] = []
        self.current_windows_handle: Optional[int] = None

        # 相机工作线程
        self.camera_worker: Optional[CameraWorker] = None
        self.camera_running = False
        self.current_fps = 10

        # 初始化UI
        self.init_ui()

        # 工作线程初始化标志
        self.workers_initialized = False

        # 初始刷新窗口列表
        self.refresh_windows()

    # ============================================
    # UI初始化
    # ============================================

    def init_ui(self) -> None:
        """
        初始化用户界面
        """
        main_layout = QVBoxLayout()

        # 创建第一层布局（控制栏）
        self.create_control_layout()
        main_layout.addLayout(self.l1_layout)

        # 创建第二层布局（数据显示区）
        self.create_display_layout()
        main_layout.addLayout(self.l2_layout)

        self.setLayout(main_layout)

    def create_control_layout(self) -> None:
        """
        创建第一层布局：控制按钮和设置
        """
        self.l1_layout = QHBoxLayout()
        self.l1_left_layout = QHBoxLayout()

        # 窗口选择下拉框
        self.window_label = QLabel('选择窗口：')
        self.window_combo = QComboBox()
        self.window_combo.currentIndexChanged.connect(self.on_window_selected)
        self.window_combo.setFixedWidth(200)

        # FPS设置
        self.fps_label = QLabel('FPS：')
        self.fps_input = QLineEdit()
        self.fps_input.setValidator(QIntValidator(1, 20))
        self.fps_input.setText('10')
        self.fps_input.setFixedWidth(60)
        self.fps_input.textChanged.connect(self.on_fps_changed)

        # 功能按钮
        self.refresh_windows_button = QPushButton('刷新窗口')
        self.refresh_windows_button.clicked.connect(self.refresh_windows)

        self.camera_toggle_button = QPushButton('启动')
        self.camera_toggle_button.clicked.connect(self.toggle_camera)

        self.refresh_button = QPushButton('暂停刷新日志')
        self.refresh_button.clicked.connect(self.on_refresh_button_clicked)

        # 左侧布局添加控件
        self.l1_left_layout.addWidget(self.window_label)
        self.l1_left_layout.addWidget(self.window_combo)
        self.l1_left_layout.addWidget(self.fps_label)
        self.l1_left_layout.addWidget(self.fps_input)
        self.l1_left_layout.addWidget(self.refresh_windows_button)
        self.l1_left_layout.addWidget(self.camera_toggle_button)
        self.l1_left_layout.addStretch()
        self.l1_left_layout.addWidget(self.refresh_button)

        # 右侧链接按钮
        self.l1_right_layout = QHBoxLayout()
        self.github_button = QPushButton('Github')
        self.github_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/liantian-cn/WowPixelDumper'))
        )
        self.discord_button = QPushButton('Discord')
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
        """
        创建第二层布局：数据显示和日志
        """
        self.l2_layout = QHBoxLayout()

        # 左侧数据显示区（75%宽度）
        self.l2l_layout = QVBoxLayout()
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.l2l_layout.addWidget(self.data_display)

        # 右侧日志显示区（25%宽度）
        self.l2r_layout = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.l2r_layout.addWidget(self.log_display)

        # 设置拉伸比例
        self.l2_layout.addLayout(self.l2l_layout, 3)
        self.l2_layout.addLayout(self.l2r_layout, 1)

    # ============================================
    # 事件处理：设置变更
    # ============================================

    def on_fps_changed(self, text: str) -> None:
        """
        FPS输入框变化处理
        """
        # 空值检查
        if text == "":
            return

        try:
            fps = int(text)

            # 范围检查
            if fps < 1 or fps > 20:
                return

            self.current_fps = fps

            # 记录日志
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] FPS 设置为 {fps}"
            self.log_display.append(log_message)

            # 实时更新运行中的工作线程
            if self.camera_worker and self.camera_running:
                self.camera_worker.fps = fps
                self.log_display.append(f"[{timestamp}] CameraWorker FPS 已更新")

        except ValueError:
            return

    def on_window_selected(self, index: int) -> None:
        """
        窗口选择变化处理
        """

        # 选择"无窗口"选项
        if index == 0:
            self.current_windows_handle = None

            # 如果相机正在运行，停止它
            if self.camera_worker and self.camera_running:
                self.log_display.append(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 选择无效窗口，CameraWorker 停止"
                )
                self.camera_worker.stop()
                self.camera_worker = None
                self.camera_running = False
                self.camera_toggle_button.setText('启动')

                # 解锁控件
                self.window_combo.setEnabled(True)
                self.refresh_windows_button.setEnabled(True)
            else:
                self.log_display.append(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未选择有效窗口"
                )
            return

        # 选择有效窗口
        if index > 0 and (index - 1) < len(self.windows_handle_list):
            hwnd = self.windows_handle_list[index - 1][0]
            self.current_windows_handle = hwnd
            self.log_display.append(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 选择窗口: {self.windows_handle_list[index - 1][1]} ({hwnd})"
            )

            # 如果相机正在运行，重启以更新句柄
            if self.camera_worker and self.camera_running:
                self.log_display.append(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 重新启动 CameraWorker 以更新窗口句柄"
                )
                self.camera_worker.stop()
                self.camera_worker = CameraWorker(self.current_windows_handle, self.current_fps)
                self.camera_worker.data_signal.connect(self.process_captured_frame)
                self.camera_worker.log_signal.connect(self.append_camera_log)
                self.camera_worker.start()
                self.camera_running = True

    def on_refresh_button_clicked(self) -> None:
        """
        暂停/恢复刷新按钮处理
        """
        self.data_refresh_enabled = not self.data_refresh_enabled

        if self.data_refresh_enabled:
            self.refresh_button.setText('暂停刷新日志')
            self.data_display.setText(json.dumps(self.pixel_dump, indent=2, ensure_ascii=False))
        else:
            self.refresh_button.setText('恢复刷新日志')

    # ============================================
    # 事件处理：相机控制
    # ============================================

    def toggle_camera(self) -> None:
        """
        切换相机启停状态
        """

        # 启动相机
        if not self.camera_running:
            # 检查窗口选择
            if self.current_windows_handle is None:
                self.log_display.append(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 请先选择一个窗口"
                )
                return

            # 先抓取全屏查找标记位置
            frame, status = capture_window(self.current_windows_handle)
            if frame is None:
                self.log_display.append(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 抓取窗口失败: {status}"
                )
                return

            # 查找模板标记
            bounds = find_template_bounds(frame, 'mark6.png')
            if bounds is None:
                self.log_display.append(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未找到标记"
                )
                return

            left, top, right, bottom = bounds
            self.log_display.append(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 找到标记位置: ({left}, {top}, {right}, {bottom})"
            )

            # 创建并启动工作线程
            self.camera_worker = CameraWorker(self.current_windows_handle, self.current_fps)
            self.camera_worker.data_signal.connect(self.process_captured_frame)
            self.camera_worker.log_signal.connect(self.append_camera_log)
            self.camera_worker.region_signal.emit(left, top, right, bottom)
            self.camera_worker.start()
            self.camera_running = True
            self.camera_toggle_button.setText('停止')

            # 锁定窗口选择相关控件
            self.window_combo.setEnabled(False)
            self.refresh_windows_button.setEnabled(False)

            self.log_display.append(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CameraWorker 启动，窗口句柄: {self.current_windows_handle}"
            )

        # 停止相机
        else:
            if self.camera_worker:
                self.camera_worker.stop()
                self.camera_worker = None
            self.camera_running = False
            self.camera_toggle_button.setText('启动')

            # 解锁控件
            self.window_combo.setEnabled(True)
            self.refresh_windows_button.setEnabled(True)

            self.log_display.append(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CameraWorker 停止"
            )

    # ============================================
    # 事件处理：相机数据与日志
    # ============================================

    def process_captured_frame(self, cropped_array: np.ndarray, camera_status: str) -> None:
        """
        处理相机捕获的图像数据
        解析像素数据并更新UI显示
        """
        if camera_status == "ok":
            # 检查是否应该输出日志（避免弹窗期间刷屏）
            should_log = not self.dialog_visible and not self.dialog_cooldown

            try:
                # 创建像素解析器
                dumper = PixelDumper(cropped_array)

                # 检查三个SI节点（用于技能图标识别）
                si_node_1 = dumper.get_node(1, 17)
                si_node_2 = dumper.get_node(15, 1)
                si_node_3 = dumper.get_node(54, 14)

                # 三个节点都非纯色且哈希相同，说明有新技能图标
                if si_node_1.is_not_pure and si_node_2.is_not_pure and si_node_3.is_not_pure:
                    if si_node_1.hash == si_node_2.hash == si_node_3.hash and (not hashstr_used(si_node_1.hash)):
                        # 提示用户输入技能名称
                        if should_log:
                            self.log_display.append(
                                f'SI节点1、2、3颜色相同，哈希值为: {si_node_1.hash}\n为这个hash值绑定什么技能？'
                            )
                        # 显示输入对话框
                        if not self.dialog_visible and (not self.dialog_cooldown):
                            self.show_hash_dialog(si_node_1.hash)

                # 提取所有像素数据
                dump_data = dumper.extract_all_data()
                self.pixel_dump.clear()
                self.pixel_dump.update(dump_data)

                # 更新数据显示（如果刷新未暂停）
                if self.data_refresh_enabled:
                    self.data_display.setText(json.dumps(self.pixel_dump, indent=8, ensure_ascii=False))

            except Exception as e:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f"[{timestamp}] 处理图像数据时发生错误: {str(e)}")
        else:
            # 捕获失败记录错误
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f"[{timestamp}] 抓取窗口失败: {camera_status}")

    def append_camera_log(self, log_message: str) -> None:
        """
        处理相机线程日志
        """
        self.log_display.append(log_message)

    # ============================================
    # 窗口管理
    # ============================================

    def refresh_windows(self) -> None:
        """
        刷新窗口列表
        """

        # 窗口枚举回调函数
        def callback(hwnd: int, windows: List[Tuple[int, str]]) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "魔兽世界" in title:
                    windows.append((hwnd, title))
            return True

        # 枚举所有窗口
        windows: List[Tuple[int, str]] = []
        win32gui.EnumWindows(callback, windows)

        # 更新窗口列表
        self.windows_handle_list = windows
        self.window_combo.clear()

        # 添加默认选项
        self.window_combo.addItem("无窗口", None)

        if windows:
            # 添加所有找到的窗口
            for hwnd, title in windows:
                self.window_combo.addItem(f"{title} ({hwnd})", hwnd)
            self.current_windows_handle = windows[0][0]
            self.window_combo.setCurrentIndex(1)
            log_message = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 找到 {len(windows)} 个魔兽世界窗口"
        else:
            self.current_windows_handle = None
            log_message = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未找到魔兽世界窗口"

        self.log_display.append(log_message)

    # ============================================
    # 对话框管理
    # ============================================

    def show_hash_dialog(self, hash_value: str) -> None:
        """
        显示技能哈希绑定对话框
        """
        self.dialog_visible = True
        self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 显示对话框")

        # 弹出输入对话框
        text, ok = QInputDialog.getText(self, '请输入Hash值对应的标题', f'标题({hash_value}):')

        # 处理用户输入
        if ok and text:
            save_user_input_hash(hash_value, text)
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户输入标题: {text}")
        elif ok:
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户未输入标题")
        else:
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户取消输入")

        # 关闭对话框并设置冷却
        self.dialog_visible = False
        self.dialog_cooldown = True
        QTimer.singleShot(3000, self.reset_dialog_cooldown)

    def reset_dialog_cooldown(self) -> None:
        """
        重置对话框冷却状态
        """
        self.dialog_cooldown = False
        self.log_display.append(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 对话框冷却已恢复"
        )

    # ============================================
    # 系统事件
    # ============================================

    def closeEvent(self, event) -> None:
        """
        窗口关闭事件
        """
        event.accept()


# ============================================
# 程序入口
# ============================================
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
