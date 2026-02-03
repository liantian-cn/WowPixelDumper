import ctypes
import time

import win32gui

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

VK_DICT = {
    "NUMPAD0": 0x60,
    "NUMPAD1": 0x61,
    "NUMPAD2": 0x62,
    "NUMPAD3": 0x63,
    "NUMPAD4": 0x64,
    "NUMPAD5": 0x65,
    "NUMPAD6": 0x66,
    "NUMPAD7": 0x67,
    "NUMPAD8": 0x68,
    "NUMPAD9": 0x69,
    "SHIFT": 0x10,
    "CTRL": 0x11,
    "ALT": 0x12,
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7a,
    "F12": 0x7b,
}


def get_windows_by_title(title):
    windows = []
    win32gui.EnumWindows(lambda hwnd, _: windows.append((hwnd, win32gui.GetWindowText(hwnd))), None)
    return [hwnd for hwnd, window_title in windows if title.lower() in window_title.lower()]


def press_key_hwnd(hwnd, skey):
    key = VK_DICT.get(skey)
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYDOWN, key, 0)


def release_key_hwnd(hwnd, skey):
    key = VK_DICT.get(skey)
    ctypes.windll.user32.PostMessageW(hwnd, WM_KEYUP, key, 0)


def press_and_release_key_hwnd(hwnd, skey):
    press_key_hwnd(hwnd, skey)
    time.sleep(0.05)
    release_key_hwnd(hwnd, skey)


class Keyboard:
    def __init__(self):
        self.hwnd = None

    def find_window(self, title):
        windows = get_windows_by_title(title)
        if windows:
            self.hwnd = windows[0]
            return True
        else:
            return False

    def send_hot_key(self, hot_key):
        key_list = hot_key.split("-")
        for skey in key_list:
            press_key_hwnd(self.hwnd, skey)
        time.sleep(0.01)
        for skey in key_list:
            release_key_hwnd(self.hwnd, skey)


if __name__ == '__main__':
    a = Keyboard()
    a.find_window("魔兽世界")
    a.send_hot_key("CTRL-F5")
