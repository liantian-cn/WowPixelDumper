"""程序入口 - PixelDumper GUI应用程序。"""

import sys

from PySide6.QtWidgets import QApplication

from MainWindow import MainWindow


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
    sys.exit(main())
