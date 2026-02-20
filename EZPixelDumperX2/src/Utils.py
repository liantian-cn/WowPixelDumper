"""图像处理工具模块 - 模板加载、模板匹配、边界查找、ColorMap配置。"""
import os
import sys
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


####### 路径常量 #######
# print(sys.argv[0])
app_dir: Path = Path(os.path.abspath(sys.argv[0])).resolve().parent


####### ColorMap配置加载 #######

_ColorMap: dict[str, dict[str, Any]] = {'IconType': {}}


def _load_colormap() -> None:
    """加载颜色映射配置。

    从ColorMap.json加载颜色到游戏状态标识的映射（职业、Buff类型、职责等）。
    """
    global _ColorMap
    colormap_path: Path = app_dir / 'ColorMap.json'
    with open(colormap_path, 'r', encoding='utf-8') as f:
        _ColorMap.update(json.load(f))


####### 模块加载时自动初始化配置 #######
_load_colormap()


####### 截图转换函数 #######

def screenshot_to_array(screenshot: Image.Image) -> np.ndarray:
    """将 PIL 截图对象转换为 numpy 数组。

    Args:
        screenshot: PIL 截图对象

    Returns:
        np.ndarray: RGB 格式的 numpy 数组，形状为 (height, width, 3)
    """
    if screenshot.mode != 'RGB':
        screenshot = screenshot.convert('RGB')

    screenshot_array: np.ndarray = np.array(screenshot)
    return screenshot_array


####### 模板加载函数 #######

def load_template(template_path: str) -> np.ndarray:
    """加载标记模板图片。

    用于定位游戏内像素数据区域的锚点标记。

    Args:
        template_path: 标记图片的路径

    Returns:
        np.ndarray: RGB 格式的 numpy 数组，形状为 (height, width, 3)
    """
    img: Image.Image = Image.open(template_path)

    if img.mode != 'RGB':
        img = img.convert('RGB')

    template_array: np.ndarray = np.array(img)
    return template_array


####### 模板匹配函数 #######

def find_all_matches(
    screenshot_array: np.ndarray,
    template_array: np.ndarray,
    threshold: float = 0.999
) -> list[tuple[int, int]]:
    """在截图中查找所有模板匹配位置。

    使用 OpenCV 模板匹配算法定位锚点标记。

    Args:
        screenshot_array: 截图的 numpy 数组，形状为 (height, width, 3)
        template_array: 标记模板的 numpy 数组
        threshold: 匹配阈值，范围 0-1，默认 0.999（高精度匹配）

    Returns:
        list[tuple[int, int]]: 所有匹配位置的左上角坐标列表，格式为 (x, y)
    """
    template_height: int
    template_width: int
    template_height, template_width = template_array.shape[:2]

    screenshot_height: int
    screenshot_width: int
    screenshot_height, screenshot_width = screenshot_array.shape[:2]

    # 模板大于截图时无法匹配
    if template_height > screenshot_height or template_width > screenshot_width:
        return []

    # TM_CCOEFF_NORMED 返回 -1 到 1 的值，1 表示完美匹配
    result: np.ndarray = cv2.matchTemplate(
        screenshot_array, template_array, cv2.TM_CCOEFF_NORMED
    )

    # 筛选匹配位置
    match_locations: tuple = np.where(result >= threshold)
    matches: list[tuple[int, int]] = [(int(x), int(y)) for y, x in zip(match_locations[0], match_locations[1])]
    matches.sort()

    return matches


####### 边界查找函数 #######

def find_template_bounds(
    screenshot_array: np.ndarray,
    template_path: str,
    threshold: float = 0.999
) -> tuple[int, int, int, int] | None:
    """根据模板标记计算像素数据区域的边界。

    通过两个锚点标记的位置确定整个数据区域的矩形边界。
    边界尺寸必须是 8 的倍数（因为数据以 8x8 像素节点为单位）。

    Args:
        screenshot_array: 截图的 numpy 数组
        template_path: 标记图片的路径
        threshold: 匹配阈值

    Returns:
        tuple[int, int, int, int] | None: 矩形边界 (left, top, right, bottom)，发生错误时返回 None
    """
    try:
        template_array: np.ndarray = load_template(template_path)
        template_height: int
        template_width: int
        template_height, template_width = template_array.shape[:2]

        matches: list[tuple[int, int]] = find_all_matches(screenshot_array, template_array, threshold)

        if len(matches) != 2:
            print(f'[find_template_bounds] 需要找到 2 个标记，但找到 {len(matches)} 个')
            return None

        # 计算两个标记构成的矩形边界
        x1: int
        y1: int
        x2: int
        y2: int
        x1, y1 = matches[0]
        x2, y2 = matches[1]

        right1: int = x1 + template_width
        bottom1: int = y1 + template_height
        right2: int = x2 + template_width
        bottom2: int = y2 + template_height

        left: int = int(min(x1, x2))
        top: int = int(min(y1, y2))
        right: int = int(max(right1, right2))
        bottom: int = int(max(bottom1, bottom2))

        width: int = right - left
        height: int = bottom - top

        # 验证边界尺寸是 8 的倍数（节点大小）
        if width % 8 != 0 or height % 8 != 0:
            print(f'[find_template_bounds] 边界尺寸必须是 8 的倍数，但得到 {width} x {height}')
            return None

        return (left, top, right, bottom)
    except Exception as e:
        print(f'[find_template_bounds] 发生错误: {e}')
        return None
