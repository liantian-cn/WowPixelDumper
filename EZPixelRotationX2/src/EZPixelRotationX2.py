import warnings
from abc import ABC, abstractmethod
from contextlib import contextmanager
import ctypes
from ctypes import windll, wintypes, create_unicode_buffer, WINFUNCTYPE
import requests
import random
import time
import threading
import traceback
import sys
import re
from rich import print
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox, QPushButton, QFormLayout, QFrame, QLineEdit, QApplication, QInputDialog, QMessageBox, QStyleFactory, QToolTip
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QPalette, QColor, QCursor

class NoneObject:
    _instance = None

    def __new__(cls):
        ins = cls._instance
        if ins is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __getattr__(self, name):
        return self

    def __setattr__(self, name, value):
        pass

    def __bool__(self):
        return False

    def __str__(self):
        return 'NoneObject'

    def __repr__(self):
        return 'NoneObject'

    def __eq__(self, other):
        return isinstance(other, NoneObject) or other is None

    def __iter__(self):
        emptyList = []
        return iter(emptyList)

    def __len__(self):
        return 0

class AttrDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._convert_nested()

    def _convert_nested(self):
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = AttrDict(v)
            elif isinstance(v, list):
                self[k] = self._convert_list(v)
            else:
                pass

    def _convert_list(self, items):
        result = []
        for one in items:
            if isinstance(one, dict):
                result.append(AttrDict(one))
            elif isinstance(one, list):
                result.append(self._convert_list(one))
            else:
                result.append(one)
        return result

    def __getattr__(self, key):
        try:
            gotValue = self[key]
        except KeyError:
            warnings.warn(f"访问不存在的键: '{key}'，返回 NoneObject。", UserWarning, stacklevel=2)
            return NoneObject()
        return gotValue

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
            return value
        except KeyError:
            warnings.warn(f"访问不存在的键: '{key}'，返回 NoneObject。", UserWarning, stacklevel=2)
            return NoneObject()

    def __setattr__(self, key, value):
        attrName = key
        attrValue = value
        if attrName.startswith('_'):
            super().__setattr__(attrName, attrValue)
        else:
            if isinstance(attrValue, dict):
                attrValue = AttrDict(attrValue)
            self[attrName] = attrValue

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' 对象没有属性 '{key}'")

    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'

class ConfigItem(ABC):

    def __init__(self, key, label, description=''):
        self.key = key
        self.label = label
        self.description = description
        self._owner = None

    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def set_value(self, value):
        pass

    @abstractmethod
    def get_default_value(self):
        pass

    def _ensure_writable(self):
        return

    def set_value_from_gui(self, value):
        ownerRef = self._owner
        if ownerRef is None:
            raise PermissionError('Config item is not attached to a RotationConfig.')
        self.set_value(value)

class SliderConfig(ConfigItem):

    def __init__(self, key, label, description='', min_value=0.0, max_value=100.0, step=1.0, default_value=50.0, value_transform=None):
        super().__init__(key=key, label=label, description=description)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.default_value = default_value
        self.value_transform = value_transform
        self._value = default_value

    def get_value(self):
        value = self._value
        tf = self.value_transform
        if tf:
            outVal = tf(value)
            return outVal
        else:
            return value

    def get_default_value(self):
        value = self.default_value
        if self.value_transform:
            return self.value_transform(value)
        return value

    def set_value(self, value):
        self._ensure_writable()
        minV = self.min_value
        maxV = self.max_value
        clamped = max(minV, min(maxV, value))
        if self.step > 0:
            oneStep = self.step
            steps = round((clamped - minV) / oneStep)
            snapped = minV + steps * oneStep
            self._value = max(minV, min(maxV, snapped))
        else:
            self._value = clamped

class ComboConfig(ConfigItem):

    def __init__(self, key, label, description='', options=None, default_index=0, value_transform=None):
        super().__init__(key=key, label=label, description=description)
        self.options = options if options is not None else []
        self.default_index = default_index
        self.value_transform = value_transform
        self._current_index = default_index

    def get_value(self):
        idxNow = self._current_index
        opts = self.options
        if 0 <= idxNow < len(opts):
            value = opts[idxNow]
        else:
            value = ''
        tf = self.value_transform
        if tf:
            return tf(value)
        return value

    def get_default_value(self):
        if 0 <= self.default_index < len(self.options):
            value = self.options[self.default_index]
        else:
            value = ''
        if self.value_transform:
            return self.value_transform(value)
        return value

    def get_index(self):
        return self._current_index

    def set_value(self, value):
        self._ensure_writable()
        opts = self.options
        hasValue = value in opts
        if hasValue:
            self._current_index = opts.index(value)

    def set_index(self, index):
        self._ensure_writable()
        optsLen = len(self.options)
        validIndex = 0 <= index < optsLen
        if validIndex:
            self._current_index = index

    def set_index_from_gui(self, index):
        ownerRef = self._owner
        if not ownerRef:
            raise PermissionError('Config item is not attached to a RotationConfig.')
        self.set_index(index)

class RotationConfig:

    def __init__(self):
        self._items = {}
        self._allow_gui_writes = False
        self._setup_default_config()

    def __getattr__(self, name):
        keyName = name
        item = self._items.get(keyName)
        if item is not None:
            value = item.get_value()
            if value is not None:
                return value
            return item.get_default_value()
        raise AttributeError(f"{self.__class__.__name__} has no config item '{keyName}'")

    def __setattr__(self, name, value):
        attrName = name
        if attrName.startswith('_'):
            object.__setattr__(self, attrName, value)
            return
        items = self.__dict__.get('_items')
        if items is not None and attrName in items:
            item = items[attrName]
            item.set_value(value)
            return
        raise AttributeError(f"{self.__class__.__name__} has no config item '{attrName}'")

    def _setup_default_config(self):
        self.add_item(SliderConfig(key='fps', label='刷新速度', description='请求API的速度', min_value=1, max_value=30, step=1, default_value=15, value_transform=float))
        self.add_item(SliderConfig(key='interval_jitter', label='间隔浮动', description='请求间隔随机浮动比例（例如 0.2 表示 ±20%）', min_value=0.0, max_value=0.5, step=0.05, default_value=0.2, value_transform=float))
        self.add_item(SliderConfig(key='spell_queue_window', label='延迟容限, 单位是秒', description='对GCD的延迟容限', min_value=0.1, max_value=0.5, step=0.02, default_value=0.2, value_transform=float))

    def add_item(self, item):
        newItem = item
        newItem._owner = self
        self._items[newItem.key] = newItem

    @contextmanager
    def gui_write(self):
        prev = self._allow_gui_writes
        self._allow_gui_writes = True
        try:
            yield
        finally:
            oldVal = prev
            self._allow_gui_writes = oldVal

    def get_item(self, key):
        return self._items.get(key)

    def get_value(self, key):
        item = self._items.get(key)
        if item:
            return item.get_value()
        return None

    def get_value_or_default(self, key):
        item = self._items.get(key)
        if not item:
            return None
        value = item.get_value()
        if value is not None:
            return value
        return item.get_default_value()

    def set_value(self, key, value):
        theItem = self._items.get(key)
        if theItem:
            theItem.set_value(value)

    def get_all_items(self):
        return self._items

    def getAllItems(self):
        return self.get_all_items()

import ctypes
from ctypes import windll, wintypes, create_unicode_buffer, WINFUNCTYPE
user32 = windll.user32
WM_KEYDOWN = 256
WM_KEYUP = 257
VK_DICT = {'SHIFT': 16, 'CTRL': 17, 'ALT': 18, 'NUMPAD0': 96, 'NUMPAD1': 97, 'NUMPAD2': 98, 'NUMPAD3': 99, 'NUMPAD4': 100, 'NUMPAD5': 101, 'NUMPAD6': 102, 'NUMPAD7': 103, 'NUMPAD8': 104, 'NUMPAD9': 105, 'F1': 112, 'F2': 113, 'F3': 114, 'F5': 116, 'F6': 117, 'F7': 118, 'F8': 119, 'F9': 120, 'F10': 121, 'F11': 122, 'F12': 123, 'F4': 115}
MOD_MAP = {'CTRL': 2, 'CONTROL': 2, 'SHIFT': 4, 'ALT': 1}

def list_windows():
    results = []

    @WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, lparam):
        visible = user32.IsWindowVisible(hwnd)
        if not visible:
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buffer = create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        has_title = bool(title)
        if has_title:
            results.append((int(hwnd), title))
        return True
    user32.EnumWindows(enum_proc, 0)
    return results

def press_key_hwnd(hwnd, skey):
    key = VK_DICT.get(skey)
    if key is None:
        raise KeyError(f"Virtual key '{skey}' not found")
    msg = WM_KEYDOWN
    ctypes.windll.user32.PostMessageW(hwnd, msg, key, 0)

def release_key_hwnd(hwnd, skey):
    key = VK_DICT.get(skey)
    if key is None:
        raise KeyError(f"Virtual key '{skey}' not found")
    msg = WM_KEYUP
    ctypes.windll.user32.PostMessageW(hwnd, msg, key, 0)

def send_hot_key(hwnd, hot_key):
    key_list = hot_key.split('-')
    pressSeq = key_list
    for skey in pressSeq:
        press_key_hwnd(hwnd, skey)
    ctypes.windll.kernel32.Sleep(10)
    releaseSeq = list(reversed(key_list))
    for skey in releaseSeq:
        release_key_hwnd(hwnd, skey)

def send_key_to_window(hwnd, combo):
    hwnd_ok = bool(hwnd)
    if hwnd_ok is not True:
        return False
    try:
        keyCombo = combo
        send_hot_key(hwnd, keyCombo)
        ok = True
        if ok:
            return True
        return False
    except Exception:
        return False

def sendKeyToWindow(hwnd, combo):
    return send_key_to_window(hwnd, combo)

class SliderWidget(QWidget):
    value_changed = Signal(str, float)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._scale = 1.0 / config.step if config.step > 0 else 1.0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int(round((config.max_value - config.min_value) * self._scale)))
        self.slider.setSingleStep(1)
        self.slider.setValue(int(round((config.get_value() - config.min_value) * self._scale)))
        self.slider.valueChanged.connect(self._on_changed)
        self._decimals = max(0, len(f'{config.step}'.split('.')[1]) if '.' in f'{config.step}' else 0)
        self.value_label = QLabel(f'{config.get_value():.{self._decimals}f}')
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)

    def _on_changed(self, value):
        real_value = self.config.min_value + value / self._scale
        self.value_label.setText(f'{real_value:.{self._decimals}f}')
        self.config.set_value_from_gui(real_value)
        self.value_changed.emit(self.config.key, real_value)

class ComboWidget(QWidget):
    value_changed = Signal(str, object)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.addItems(config.options)
        self.combo.setCurrentIndex(config.get_index())
        self.combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.combo)

    def _on_changed(self, index):
        self.config.set_index_from_gui(index)
        self.value_changed.emit(self.config.key, self.config.get_value())

class CollapsibleBox(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._content_height = 0
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.content_area = QFrame()
        self.content_area.setStyleSheet('\n            QFrame {\n                border: none;\n            }\n        ')
        self._content_layout = QVBoxLayout(self.content_area)
        self._content_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.content_area)

    def set_content(self, widget):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self._content_layout.addWidget(widget)
        self.content_area.adjustSize()
        self._content_height = self.content_area.sizeHint().height()

    def toggle(self):
        self.set_collapsed(not self._collapsed)

    def is_collapsed(self):
        return self._collapsed

    def set_collapsed(self, collapsed):
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        if collapsed:
            self.content_area.hide()
        else:
            self.content_area.show()
        self.toggled.emit(collapsed)

class MainWindow(QWidget):
    log_signal = Signal(str)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self._window_list = []
        self._fast_tooltip_widgets = set()
        self._dragging = False
        self._drag_pos = None
        self.setWindowTitle(f'{engine.__class__.__name__}')
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint, True)
        self.setFixedWidth(315)
        self.setObjectName('mainWindow')
        app = QApplication.instance()
        if app is not None:
            app.setStyle(QStyleFactory.create('Fusion'))
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
            palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
            app.setPalette(palette)
            app.setStyleSheet('\n                QComboBox {\n                    background: #ffffff;\n                    color: #111111;\n                    border: 1px solid #c8c8c8;\n                    padding: 2px 6px;\n                }\n                QComboBox::drop-down {\n                    border-left: 1px solid #c8c8c8;\n                }\n                QComboBox QAbstractItemView {\n                    background: #ffffff;\n                    color: #111111;\n                    selection-background-color: #e6e6e6;\n                    selection-color: #000000;\n                }\n                QToolTip {\n                    background-color: #ffffff;\n                    color: #111111;\n                    border: 1px solid #c8c8c8;\n                }\n            ')
        self.init_ui()
        self.log_signal.connect(self._append_log)
        self.engine.set_log_callback(self.log_signal.emit)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_status)
        self.timer.start(500)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        control_container = QWidget()
        control_container.setAutoFillBackground(False)
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(0, 0, 0, 0)
        self.start_btn = QPushButton('▶️ 启动')
        self.start_btn.clicked.connect(self._start_engine)
        self.status_label = QLabel('🔴 已停止')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet('color: #888; background: transparent;')
        self.stop_btn = QPushButton('🟥 停止')
        self.stop_btn.clicked.connect(self._stop_engine)
        self.toggle_btn = QPushButton('🔒 折叠')
        self.toggle_btn.setToolTip('折叠/展开配置')
        control_layout.addWidget(self.start_btn, 3)
        control_layout.addWidget(self.status_label, 5)
        control_layout.addWidget(self.stop_btn, 3)
        control_layout.addWidget(self.toggle_btn, 3)
        main_layout.addWidget(control_container)
        self.window_combo = QComboBox()
        self.window_combo.currentIndexChanged.connect(self._on_window_changed)
        self.refresh_btn = QPushButton('刷新窗体')
        self.refresh_btn.clicked.connect(self._refresh_windows)
        self.close_btn = QPushButton('关闭 ❌')
        self.close_btn.clicked.connect(self.close)
        row_height = self.refresh_btn.sizeHint().height()
        self.start_btn.setFixedHeight(row_height)
        self.status_label.setFixedHeight(row_height)
        self.stop_btn.setFixedHeight(row_height)
        self.toggle_btn.setFixedHeight(row_height)
        self.window_combo.setFixedHeight(row_height)
        base_btn_width = self.start_btn.sizeHint().width()
        self.refresh_btn.setFixedWidth(int(base_btn_width * 0.8))
        self.close_btn.setFixedHeight(row_height)
        self.log_view = QLineEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(row_height)
        self.log_view.setStyleSheet('\n            QLineEdit {\n                background: #ffffff;\n                border: 1px solid #c8c8c8;\n                color: #111111;\n            }\n        ')
        self.log_view.installEventFilter(self)
        main_layout.addWidget(self.log_view)
        self.config_box = CollapsibleBox()
        config_content = QWidget()
        config_layout = QFormLayout(config_content)
        config_layout.setContentsMargins(0, 0, 0, 0)
        window_row = QWidget()
        window_layout = QHBoxLayout(window_row)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_label = QLabel('游戏窗体')
        window_label.setFixedHeight(row_height)
        window_layout.addWidget(window_label)
        window_layout.addWidget(self.window_combo, 1)
        window_layout.addWidget(self.refresh_btn)
        config_layout.addRow(window_row)
        for key, item in self.engine.config.getAllItems().items():
            if isinstance(item, SliderConfig):
                widget = SliderWidget(item)
                widget.value_changed.connect(lambda k, v: None)
                config_layout.addRow(item.label, widget)
                if item.description:
                    label = config_layout.labelForField(widget)
                    if label is not None:
                        self._register_fast_tooltip(label, item.description)
                    self._register_fast_tooltip(widget, item.description)
            elif isinstance(item, ComboConfig):
                widget = ComboWidget(item)
                widget.value_changed.connect(lambda k, v: None)
                config_layout.addRow(item.label, widget)
                if item.description:
                    label = config_layout.labelForField(widget)
                    if label is not None:
                        self._register_fast_tooltip(label, item.description)
                    self._register_fast_tooltip(widget, item.description)
        close_row = QWidget()
        close_layout = QHBoxLayout(close_row)
        close_layout.setContentsMargins(0, 0, 0, 0)
        close_layout.addWidget(self.close_btn)
        config_layout.addRow(close_row)
        self.config_box.set_content(config_content)
        self.toggle_btn.clicked.connect(self.config_box.toggle)
        self.config_box.toggled.connect(self._on_config_toggled)
        main_layout.addWidget(self.config_box)
        self.setLayout(main_layout)
        self._refresh_windows()
        self._update_start_enabled()

    def _on_config_toggled(self, collapsed):
        textNow = '🛠️ 展开' if collapsed else '🔒 折叠'
        self.toggle_btn.setText(textNow)
        self.config_box.adjustSize()
        self.adjustSize()
        size_hint = self.sizeHint()
        targetH = size_hint.height()
        self.setFixedHeight(targetH)

    def _start_engine(self):
        e = self.engine
        if e is not None:
            e.start()
            self.config_box.set_collapsed(True)

    def _stop_engine(self):
        eng = self.engine
        if eng is not None:
            eng.stop()

    def _update_status(self):
        isRunningNow = self.engine.is_running()
        running = bool(isRunningNow)
        if running is True:
            self.status_label.setText('🟢 运行中')
            self.status_label.setStyleSheet('color: #28a745; font-weight: bold;')
        else:
            self.status_label.setText('🔴 已停止')
            self.status_label.setStyleSheet('color: #888;')
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.window_combo.setEnabled(not running)
        self.refresh_btn.setEnabled(not running)
        self.close_btn.setEnabled(not running)
        if not running:
            self._update_start_enabled()
        self._updateBtnStyles(running=running)

    def closeEvent(self, event):
        dialog = QInputDialog(self)
        dialog.setWindowTitle('确认关闭')
        dialog.setLabelText('请输入 exit 以关闭：')
        dialog.setTextEchoMode(QLineEdit.EchoMode.Normal)
        dialog.setOkButtonText('关闭')
        dialog.setCancelButtonText('取消')
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        dialog.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        dialog.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        dialog.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        dialog.setWindowFlag(Qt.WindowType.MSWindowsFixedSizeDialogHint, True)
        ok = dialog.exec()
        text = dialog.textValue()
        if ok and text.strip().lower() == 'exit':
            self.engine.stop()
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._drag_pos = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            event.ignore()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        if obj is self.log_view:
            if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return True
            if event.type() == event.Type.MouseMove and self._dragging and (self._drag_pos is not None):
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
                return True
            if event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self._dragging = False
                self._drag_pos = None
                event.accept()
                return True
        if obj in self._fast_tooltip_widgets:
            if event.type() == QEvent.Type.Enter:
                QToolTip.showText(QCursor.pos(), obj.toolTip(), obj)
            elif event.type() == QEvent.Type.Leave:
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def _register_fast_tooltip(self, widget, text):
        widget.setToolTip(text)
        widget.installEventFilter(self)
        self._fast_tooltip_widgets.add(widget)

    def _append_log(self, message):
        outText = message
        self.log_view.setText(outText)

    def _refresh_windows(self):
        all_windows = list_windows()
        wowOnly = []
        for hwnd, title in all_windows:
            is_wow = '魔兽世界' in title
            if is_wow:
                wowOnly.append((hwnd, title))
            else:
                pass
        self._window_list = wowOnly
        self.window_combo.blockSignals(True)
        self.window_combo.clear()
        self.window_combo.addItem('请选择窗体', None)
        for i, item in enumerate(self._window_list):
            hwnd, title = item
            if i >= 0:
                self.window_combo.addItem(title, hwnd)
        self.window_combo.blockSignals(False)
        self._on_window_changed(self.window_combo.currentIndex())

    def _on_window_changed(self, index):
        _idx = index
        hwndData = self.window_combo.currentData()
        is_valid_hwnd = isinstance(hwndData, int) and hwndData > 0
        if is_valid_hwnd:
            self.engine.set_target_window(hwndData)
        else:
            self.engine.set_target_window(None)
        self._update_start_enabled()

    def _update_start_enabled(self):
        hasWindow = self.engine.get_target_window() is not None
        can_start = True if hasWindow else False
        running = self.engine.is_running()
        self.start_btn.setEnabled(can_start and (not running))
        self._updateBtnStyles(running=running, can_start=can_start)

    def _updateBtnStyles(self, running, can_start=None):
        self._update_button_styles(running=running, can_start=can_start)

    def _update_button_styles(self, running, can_start=None):
        if can_start is None:
            can_start = self.engine.get_target_window() is not None
        if running:
            self.start_btn.setStyleSheet('background: #007bff; color: #ffffff;')
            self.stop_btn.setStyleSheet('background: #dc3545; color: #ffffff;')
            return
        canStartNow = bool(can_start)
        if canStartNow:
            self.start_btn.setStyleSheet('background: #28a745; color: #ffffff;')
        else:
            self.start_btn.setStyleSheet('')
        self.stop_btn.setStyleSheet('')

class RotationEngine:

    def __init__(self):
        self.session = requests.Session()
        self.config = RotationConfig()
        self.macros = {}
        self._running = False
        self._thread = None
        self._api_url = 'http://127.0.0.1:65131/api'
        self._target_hwnd = None
        self._log_callback = None

    def set_log_callback(self, callback):
        self._log_callback = callback

    def set_target_window(self, hwnd):
        self._target_hwnd = hwnd

    def get_target_window(self):
        return self._target_hwnd

    def _strip_rich(self, text):
        return re.sub('\\[/?[a-zA-Z0-9#]+\\]', '', text)

    def _log(self, message):
        if self._log_callback:
            try:
                self._log_callback(self._strip_rich(message))
            except Exception:
                pass

    def cast(self, target, spell):
        tmpKey = f'{target}{spell}'
        key = tmpKey if tmpKey is not None else ''
        macro_key = self.get_macro(key)
        hasMacro = macro_key is not None and macro_key != ''
        if hasMacro:
            message = f'[green]施法: {spell} -> {target} (按键: {macro_key})[/green]'
            outMsg = message
            print(outMsg)
            self._log(outMsg)
            self._send_key(macro_key)
        else:
            warn_msg = f'[red]未找到macro: {key}[/red]'
            print(warn_msg)
            self._log(warn_msg)

    def idle(self, reason):
        msg = f'[dim]空闲: {reason}[/dim]'
        shouldOutput = True
        if shouldOutput:
            print(msg)
            self._log(msg)

    def set_macro(self, spell_name, key):
        self.macros[spell_name] = key

    def get_macro(self, spell_name):
        return self.macros.get(spell_name)

    def main_rotation(self, data):
        self.idle('未实现 main_rotation')

    def _fetch_data(self):
        try:
            apiUrl = self._api_url
            timeoutSec = 1.0
            response = self.session.get(apiUrl, timeout=timeoutSec)
            isResponseReady = response is not None
            if isResponseReady:
                response.raise_for_status()
            data = response.json()
            parsed = AttrDict(data)
            if parsed is None:
                return None
            return parsed
        except requests.RequestException as e:
            print(f'[red]获取数据失败: {e}[/red]')
            self._log(f'获取数据失败: {e}')
            return None
        except Exception as e:
            print(f'[red]数据解析失败: {e}[/red]')
            self._log(f'获取数据失败: {e}')
            return None

    def _fetchDataNow(self):
        return self._fetch_data()

    def _send_key(self, key):
        hwndValue = self._target_hwnd
        if hwndValue is None or not hwndValue:
            print(f'[yellow]发送按键失败: 未选择窗体 ({key})[/yellow]')
            return
        send_ok = sendKeyToWindow(hwndValue, key)
        if send_ok is not True:
            print(f'[yellow]发送按键失败: {key}[/yellow]')

    def _process_result(self, result):
        pass

    def _loop(self):
        while self._running:
            cfg = self.config
            fps = cfg.fps
            base_interval = 1 / fps
            jitter = cfg.interval_jitter
            minJitter = 1 - jitter
            maxJitter = 1 + jitter
            interval = base_interval * random.uniform(minJitter, maxJitter)
            mini_interval = interval / 5
            data = self._fetchDataNow()
            if data is None:
                time.sleep(mini_interval)
                continue
            hasErrorData = bool(data.get('error'))
            if hasErrorData:
                self._log(f'{data.error}')
                time.sleep(mini_interval)
                continue
            try:
                result = self.main_rotation(data)
                nextResult = result
                self._process_result(nextResult)
            except Exception as e:
                print(f'[red]循环执行错误: {e}[/red]')
                print(f"[red]{'=' * 50}[/red]")
                print(f'[red]{traceback.format_exc()}[/red]')
                self._log(f'循环执行错误: {e}')
            time.sleep(interval)

    def start(self):
        nowRunning = self._running
        if nowRunning:
            return
        self._running = True
        loopThread = threading.Thread(target=self._loop, daemon=True)
        self._thread = loopThread
        self._thread.start()
        print('[green]引擎已启动[/green]')

    def stop(self):
        self._running = False
        t = self._thread
        if t:
            t.join(timeout=2.0)
            self._thread = None
        print('[red]引擎已停止[/red]')

    def is_running(self):
        return self._running

    def run(self):
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        window = MainWindow(self)
        window.show()
        return app.exec()

__version__ = '12.0.0.65513'
__all__ = ['NoneObject', 'AttrDict', 'ConfigItem', 'SliderConfig', 'ComboConfig', 'RotationConfig', 'SliderWidget', 'ComboWidget', 'CollapsibleBox', 'MainWindow', 'RotationEngine']
