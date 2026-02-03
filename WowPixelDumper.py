import atexit
import json
import time
import random
import datetime
import threading
from typing import List, Tuple, Callable, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QInputDialog, QApplication, QLabel, QPushButton, QComboBox
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import QThread, Signal, Qt, QUrl, QTimer
from PySide6.QtGui import QDesktopServices
import win32gui
import win32ui
import win32con
from PIL import Image
import ctypes
import numpy as np
from Dumper import find_template_bounds, PixelDumper, save_user_input_hash, hashstr_used


user32 = ctypes.WinDLL('user32', use_last_error=True)
PrintWindow = user32.PrintWindow
PrintWindow.restype = ctypes.c_bool
PrintWindow.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]

PW_CLIENTONLY = 1
PW_RENDERFULLCONTENT = 2


def capture_window(hwnd: int, left: Optional[int] = None, top: Optional[int] = None, right: Optional[int] = None, bottom: Optional[int] = None) -> Tuple[Optional[np.ndarray], str]:
    if not hwnd:
        return None, "invalid_hwnd"

    try:
        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
        client_width = client_right - client_left
        client_height = client_bottom - client_top

        if client_width <= 0 or client_height <= 0:
            return None, "window_not_visible"

        capture_left = left if left is not None else client_left
        capture_top = top if top is not None else client_top
        capture_right = right if right is not None else client_right
        capture_bottom = bottom if bottom is not None else client_bottom

        capture_left = max(client_left, min(capture_left, client_right))
        capture_top = max(client_top, min(capture_top, client_bottom))
        capture_right = max(capture_left, min(capture_right, client_right))
        capture_bottom = max(capture_top, min(capture_bottom, client_bottom))

        width = capture_right - capture_left
        height = capture_bottom - capture_top

        if width <= 0 or height <= 0:
            return None, "invalid_capture_region"

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, client_width, client_height)
        saveDC.SelectObject(saveBitMap)

        result = PrintWindow(hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)
        if not result:
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            return None, "print_window_failed"

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        if left is not None or top is not None or right is not None or bottom is not None:
            crop_left = capture_left - client_left
            crop_top = capture_top - client_top
            crop_right = crop_left + width
            crop_bottom = crop_top + height
            img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

        array = np.array(img)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return array, "ok"

    except Exception as e:
        return None, f"exception: {str(e)}"


class CameraWorker(QThread):
    data_signal = Signal(np.ndarray, str)
    log_signal = Signal(str)
    region_signal = Signal(int, int, int, int)

    def __init__(self, windows_handle, fps=10):
        super().__init__()
        self.running = False
        self.windows_handle = windows_handle
        self.fps = fps
        self.left = 0
        self.top = 0
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.right = geometry.width()
        self.bottom = geometry.height()
        self._capture_count = 0
        self._last_log_time = 0
        self.region_signal.connect(self.update_region)

    def update_region(self, left: int, top: int, right: int, bottom: int):
        self.left = left
        self.top = top
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        self.right = right if right > 0 else geometry.width()
        self.bottom = bottom if bottom > 0 else geometry.height()

    def run(self):
        self.running = True
        interval = 1.0 / self.fps
        last_capture_time = 0
        self._capture_count = 0
        self._last_log_time = time.time()

        while self.running:
            current_time = time.time()

            if current_time - last_capture_time >= interval:
                array, status = capture_window(
                    self.windows_handle,
                    self.left,
                    self.top,
                    self.right,
                    self.bottom
                )

                self._capture_count += 1

                if array is not None:
                    self.data_signal.emit(array, status)
                else:
                    self.data_signal.emit(np.array([]), status)

                last_capture_time = current_time

                if current_time - self._last_log_time >= 10:
                    actual_fps = self._capture_count / 10.0
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.log_signal.emit(f"[{timestamp}] 实际FPS: {actual_fps:.1f}, 抓取次数: {self._capture_count}")
                    self._capture_count = 0
                    self._last_log_time = current_time
            else:
                time.sleep(0.01)

    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QWidget):
    """
    主窗口类
    包含所有 UI 组件和逻辑处理
    """

    def __init__(self):
        """
        初始化主窗口
        设置窗口属性、布局、工作线程等
        """
        super().__init__()
        self.pixel_dump = {}
        self.dialog_visible = False
        self.dialog_cooldown = False
        self.data_refresh_enabled = True
        self.setWindowTitle('WowPixelDumper')
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        self.resize(width, height)
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        self.move(x, y)
        self.setFixedHeight(height)
        self.windows_handle_list: List[Tuple[int, str]] = []
        self.current_windows_handle = None
        self.camera_worker = None
        self.camera_running = False
        self.current_fps = 10
        self.init_ui()
        self.workers_initialized = False
        self.refresh_windows()

    def init_ui(self):
        """
        初始化 UI 组件
        创建布局和控件
        """
        main_layout = QVBoxLayout()
        self.create_l1_layout()
        main_layout.addLayout(self.l1_layout)
        self.create_l2_layout()
        main_layout.addLayout(self.l2_layout)
        self.setLayout(main_layout)

    def create_l1_layout(self):
        """
        创建 L1Layout（第一层布局）
        包含刷新窗口按钮、暂停刷新日志按钮、窗口选择下拉框和启停按钮
        """
        self.l1_layout = QHBoxLayout()
        self.l1_left_layout = QHBoxLayout()

        # 窗口选择下拉框
        self.window_label = QLabel('选择窗口：')
        self.window_combo = QComboBox()
        self.window_combo.currentIndexChanged.connect(self.on_window_selected)
        # 设置下拉框固定宽度，避免挤压其他控件
        self.window_combo.setFixedWidth(200)

        # FPS 输入框
        self.fps_label = QLabel('FPS：')
        self.fps_input = QLineEdit()
        self.fps_input.setValidator(QIntValidator(1, 20))
        self.fps_input.setText('10')
        self.fps_input.setFixedWidth(60)
        self.fps_input.textChanged.connect(self.on_fps_changed)

        # 刷新窗口按钮
        self.refresh_windows_button = QPushButton('刷新窗口')
        self.refresh_windows_button.clicked.connect(self.refresh_windows)

        # 启停 CameraWorker 按钮
        self.camera_toggle_button = QPushButton('启动')
        self.camera_toggle_button.clicked.connect(self.toggle_camera)

        # 暂停刷新日志按钮
        self.refresh_button = QPushButton('暂停刷新日志')
        self.refresh_button.clicked.connect(self.on_refresh_button_clicked)

        # 添加到布局（按指定顺序）
        self.l1_left_layout.addWidget(self.window_label)
        self.l1_left_layout.addWidget(self.window_combo)
        self.l1_left_layout.addWidget(self.fps_label)
        self.l1_left_layout.addWidget(self.fps_input)
        self.l1_left_layout.addWidget(self.refresh_windows_button)
        self.l1_left_layout.addWidget(self.camera_toggle_button)
        self.l1_left_layout.addStretch()  # 添加分隔符（弹性空间）
        self.l1_left_layout.addWidget(self.refresh_button)

        self.l1_right_layout = QHBoxLayout()
        self.github_button = QPushButton('Github')
        self.github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/liantian-cn/WowPixelDumper')))
        self.discord_button = QPushButton('Discord')
        self.discord_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://discord.gg/DX77uHc9')))
        self.l1_right_layout.addWidget(self.github_button)
        self.l1_right_layout.addWidget(self.discord_button)
        self.l1_layout.addLayout(self.l1_left_layout)
        self.l1_layout.addStretch()
        self.l1_layout.addLayout(self.l1_right_layout)

    def create_l2_layout(self):
        """
        创建 L2Layout（第二层布局）
        包含左侧的数据显示框（75%）和右侧的日志框（25%）
        """
        self.l2_layout = QHBoxLayout()
        self.l2l_layout = QVBoxLayout()
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.l2l_layout.addWidget(self.data_display)
        self.l2r_layout = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.l2r_layout.addWidget(self.log_display)
        self.l2_layout.addLayout(self.l2l_layout, 3)
        self.l2_layout.addLayout(self.l2r_layout, 1)

    def on_fps_changed(self, text):
        """
        处理FPS输入框变化事件
        更新当前FPS值，并同步到正在运行的CameraWorker
        """
        if text == "":
            return
        try:
            fps = int(text)
            if fps < 1 or fps > 20:
                return
            self.current_fps = fps
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] FPS 设置为 {fps}"
            self.log_display.append(log_message)

            # 如果 CameraWorker 正在运行，更新其FPS
            if self.camera_worker and self.camera_running:
                self.camera_worker.fps = fps
                self.log_display.append(f"[{timestamp}] CameraWorker FPS 已更新")
        except ValueError:
            return

    def handle_camera_data(self, cropped_array, camera_statusuc):
        """
        处理 CameraWorker 返回的图像数据
        打印 frame 的长宽
        """
        if camera_statusuc == "ok":
            # 在弹窗或冷却期间，不输出日志
            should_log = not self.dialog_visible and not self.dialog_cooldown
            try:
                dumper = PixelDumper(cropped_array)
                si_node_1 = dumper.node(1, 17)
                si_node_2 = dumper.node(15, 1)
                si_node_3 = dumper.node(54, 14)
                if si_node_1.is_not_pure and si_node_2.is_not_pure and si_node_3.is_not_pure:
                    if si_node_1.hash == si_node_2.hash == si_node_3.hash and (not hashstr_used(si_node_1.hash)):
                        if should_log:
                            self.log_display.append(f'SI节点1、2、3颜色相同，哈希值为: {si_node_1.hash}\n为这个hash值绑定什么技能？')
                        if not self.dialog_visible and (not self.dialog_cooldown):
                            self.show_hash_dialog(si_node_1.hash)
                dump_data = dumper.dump_all()
                self.pixel_dump.clear()
                self.pixel_dump.update(dump_data)
                if self.data_refresh_enabled:
                    self.data_display.setText(json.dumps(self.pixel_dump, indent=8, ensure_ascii=False))
            except Exception as e:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.log_display.append(f"[{timestamp}] 处理图像数据时发生错误: {str(e)}")
        else:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_display.append(f"[{timestamp}] 抓取窗口失败: {camera_statusuc}")

    def show_hash_dialog(self, hash_value):
        """
        显示 Hash 值标题输入对话框
        让用户输入 Hash 值对应的标题，并更新 pixel_dump
        :param hash_value: 要绑定标题的 Hash 值
        """
        self.dialog_visible = True
        self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 显示对话框")
        text, ok = QInputDialog.getText(self, '请输入Hash值对应的标题', f'标题({hash_value}):')
        if ok and text:
            save_user_input_hash(hash_value, text)
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户输入标题: {text}")
        elif ok:
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户未输入标题")
        else:
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用户取消输入")
        self.dialog_visible = False
        self.dialog_cooldown = True
        QTimer.singleShot(3000, self.reset_dialog_cooldown)

    def refresh_windows(self):
        """
        刷新窗口列表，获取所有包含"魔兽世界"标题的可见窗口
        更新 windows_handle_list 和下拉框
        """
        def callback(hwnd: int, windows: List[Tuple[int, str]]) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "魔兽世界" in title:
                    windows.append((hwnd, title))
            return True

        windows: List[Tuple[int, str]] = []
        win32gui.EnumWindows(callback, windows)

        self.windows_handle_list = windows
        self.window_combo.clear()

        # 添加"无窗口"选项作为默认选项
        self.window_combo.addItem("无窗口", None)

        if windows:
            for hwnd, title in windows:
                self.window_combo.addItem(f"{title} ({hwnd})", hwnd)
            self.current_windows_handle = windows[0][0]
            self.window_combo.setCurrentIndex(1)  # 选择第一个有效窗口
            log_message = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 找到 {len(windows)} 个魔兽世界窗口"
        else:
            self.current_windows_handle = None
            log_message = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未找到魔兽世界窗口"

        self.log_display.append(log_message)

    def on_window_selected(self, index: int):
        """
        窗口选择下拉框变化事件
        更新当前选中的窗口句柄
        """
        # 处理"无窗口"选项 (index == 0)
        if index == 0:
            self.current_windows_handle = None

            # 如果 CameraWorker 正在运行，停止它
            if self.camera_worker and self.camera_running:
                self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 选择无效窗口，CameraWorker 停止")
                self.camera_worker.stop()
                self.camera_worker = None
                self.camera_running = False
                self.camera_toggle_button.setText('启动')
                # 解锁窗口选择下拉框和刷新窗口按钮
                self.window_combo.setEnabled(True)
                self.refresh_windows_button.setEnabled(True)
            else:
                self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未选择有效窗口")
            return

        # 处理实际窗口选项
        if index > 0 and (index - 1) < len(self.windows_handle_list):
            hwnd = self.windows_handle_list[index - 1][0]
            self.current_windows_handle = hwnd
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 选择窗口: {self.windows_handle_list[index - 1][1]} ({hwnd})")

            # 如果 CameraWorker 正在运行，需要重启以更新句柄
            if self.camera_worker and self.camera_running:
                self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 重新启动 CameraWorker 以更新窗口句柄")
                self.camera_worker.stop()
                self.camera_worker = CameraWorker(self.current_windows_handle, self.current_fps)
                self.camera_worker.data_signal.connect(self.handle_camera_data)
                self.camera_worker.log_signal.connect(self.handle_camera_log)
                self.camera_worker.start()
                self.camera_running = True

    def toggle_camera(self):
        """
        切换 CameraWorker 启停状态
        """
        if not self.camera_running:
            if self.current_windows_handle is None:
                self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 请先选择一个窗口")
                return

            # 先抓取全屏，查找标记位置
            frame, status = capture_window(self.current_windows_handle)
            if frame is None:
                self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 抓取窗口失败: {status}")
                return

            bounds = find_template_bounds(frame, 'mark6.png')
            if bounds is None:
                self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未找到标记")
                return False

            left, top, right, bottom = bounds
            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 找到标记位置: ({left}, {top}, {right}, {bottom})")

            self.camera_worker = CameraWorker(self.current_windows_handle, self.current_fps)
            self.camera_worker.data_signal.connect(self.handle_camera_data)
            self.camera_worker.log_signal.connect(self.handle_camera_log)
            # 设置截取区域
            self.camera_worker.region_signal.emit(left, top, right, bottom)
            self.camera_worker.start()
            self.camera_running = True
            self.camera_toggle_button.setText('停止')

            # 锁定窗口选择下拉框和刷新窗口按钮
            self.window_combo.setEnabled(False)
            self.refresh_windows_button.setEnabled(False)

            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CameraWorker 启动，窗口句柄: {self.current_windows_handle}")
        else:
            if self.camera_worker:
                self.camera_worker.stop()
                self.camera_worker = None
            self.camera_running = False
            self.camera_toggle_button.setText('启动')

            # 解锁窗口选择下拉框和刷新窗口按钮
            self.window_combo.setEnabled(True)
            self.refresh_windows_button.setEnabled(True)

            self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CameraWorker 停止")

    def handle_camera_log(self, log_message):
        """
        处理 CameraWorker 返回的日志
        更新日志显示框
        :param log_message: 日志消息
        """
        self.log_display.append(log_message)

    def reset_dialog_cooldown(self):
        """
        重置对话框冷却标志
        """
        self.dialog_cooldown = False
        self.log_display.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 对话框冷却已恢复")

    def on_refresh_button_clicked(self):
        """
        处理暂停/恢复刷新按钮点击事件
        切换刷新状态并更新按钮文本
        """
        self.data_refresh_enabled = not self.data_refresh_enabled
        if self.data_refresh_enabled:
            self.refresh_button.setText('暂停刷新日志')
            self.data_display.setText(json.dumps(self.pixel_dump, indent=2, ensure_ascii=False))
        else:
            self.refresh_button.setText('恢复刷新日志')

    def closeEvent(self, event):
        """
        窗口关闭事件
        停止所有工作线程
        :param event: 关闭事件
        """
        # self.camera_worker.stop()
        event.accept()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
