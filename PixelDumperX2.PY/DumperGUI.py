"""程序入口 - PixelDumper GUI应用程序。"""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from MainWindow import MainWindow
import ctypes


def main() -> int:
    """程序入口函数。

    Returns:
        int: 应用程序退出码
    """
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.show()
    return sys.exit(app.exec())


if __name__ == '__main__':

    mutex_name = "DumperGUI"
    # 创建或打开互斥锁
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)

    # 检查互斥锁的返回值
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        app = QApplication(sys.argv)
        QMessageBox.information(None, "提示", f"{mutex_name}已经在运行。")
        sys.exit()

    try:
        sys.exit(main())
    finally:
        ctypes.windll.kernel32.ReleaseMutex(mutex)
        ctypes.windll.kernel32.CloseHandle(mutex)
