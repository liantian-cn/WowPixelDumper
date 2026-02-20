import os
from datetime import datetime
from typing import List
from pathlib import Path
import shutil


def build_executable() -> None:
    """使用Nuitka将Python脚本编译为Windows可执行文件

    该函数配置Nuitka编译参数并执行编译过程，生成单文件可执行程序。
    """
    x = int((datetime.now() - datetime(2023, 7, 1)).days)
    now = datetime.now()

    args: List[str] = [
        "nuitka",
        "--standalone",
        "--show-memory",
        "--show-progress",
        "--assume-yes-for-downloads",
        "--windows-uac-admin",
        "--mingw64",
        "--enable-plugin=pyside6",
        "--windows-icon-from-ico=./icon.ico",
        "--windows-console-mode=disable",
        "--output-filename=DumperGUI.exe",
        "--output-dir=build",
        "DumperGUI.py",
    ]

    os.system(" ".join(args))


if __name__ == "__main__":
    build_executable()
    shutil.copy(Path("mark8.png"), Path("./build/DumperGUI.dist/mark8.png"))
    shutil.copy(Path("ColorMap.json"), Path("./build/DumperGUI.dist/ColorMap.json"))
    shutil.copy(Path("node_titles.db"), Path("./build/DumperGUI.dist/node_titles.db"))
