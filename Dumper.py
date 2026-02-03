"""
Dumper 模块 - 像素数据解析核心

负责从游戏截图中提取结构化的游戏状态数据。
使用 6x6 像素节点作为基本数据单元，通过颜色、哈希、亮度等特征识别游戏元素。
"""

import json
from typing import List, Tuple
from datetime import datetime

import xxhash
import cv2
import numpy as np
from PIL import Image


# ============================================
# 全局配置数据
# ============================================

ColorMap = {"BuffType": {}}
HashMap = {}


# ============================================
# 配置加载函数
# ============================================

def load_hashmap() -> dict:
    """
    加载技能图标哈希映射配置

    从 HashMap.json 加载哈希到技能名称的映射，合并 Universal 和 UserInput 配置。
    初始化全局 HashMap["Used"] 作为实际使用的映射表。

    Returns:
        dict: 可用的哈希映射表
    """
    global HashMap

    with open("HashMap.json", "r", encoding="utf-8") as f:
        HashMap = json.load(f)

    # 移除旧的 Used 配置（将重新生成）
    if "Used" in HashMap:
        del HashMap["Used"]

    # 收集用户自定义配置项
    user_select_list = []
    for key in HashMap:
        if key not in ["Universal", "Used", "UserInput"]:
            user_select_list.append(key)

    # 重新构建 Used 映射：Universal 基础配置 + UserInput 用户配置
    HashMap["Used"] = {}
    HashMap["Used"].update(HashMap["Universal"])
    if "UserInput" in HashMap:
        HashMap["Used"].update(HashMap["UserInput"])

    return HashMap["Used"]


def load_colormap() -> None:
    """
    加载颜色映射配置

    从 ColorMap.json 加载颜色到游戏状态标识的映射（职业、Buff类型、职责等）。
    """
    global ColorMap

    with open("ColorMap.json", "r", encoding="utf-8") as f:
        ColorMap.update(json.load(f))


# 模块加载时自动初始化配置
load_hashmap()
load_colormap()


def save_user_input_hash(hash_str: str, title: str) -> None:
    """
    保存用户输入的技能哈希映射

    将新的哈希-技能名映射持久化到 HashMap.json 的 UserInput 段。

    Args:
        hash_str: 技能图标的哈希值
        title: 技能名称
    """
    global HashMap

    if "UserInput" not in HashMap:
        HashMap["UserInput"] = {}

    HashMap["UserInput"][hash_str] = title
    HashMap["Used"][hash_str] = title

    with open("HashMap.json", "w", encoding="utf-8") as f:
        json.dump(HashMap, f, ensure_ascii=False, indent=4)


def hashstr_used(hash_str: str) -> bool:
    """
    检查哈希是否已存在于映射表中

    Args:
        hash_str: 技能图标的哈希值

    Returns:
        bool: 如果哈希已存在返回 True，否则返回 False
    """
    return hash_str in HashMap["Used"]


# ============================================
# 图像处理工具函数
# ============================================

def load_template(template_path: str) -> np.ndarray:
    """
    加载标记模板图片

    用于定位游戏内像素数据区域的锚点标记。

    Args:
        template_path: 标记图片的路径

    Returns:
        np.ndarray: RGB 格式的 numpy 数组，形状为 (height, width, 3)
    """
    img = Image.open(template_path)

    if img.mode != "RGB":
        img = img.convert("RGB")

    template_array = np.array(img)
    return template_array


def screenshot_to_array(screenshot: Image.Image) -> np.ndarray:
    """
    将 PIL 截图对象转换为 numpy 数组

    Args:
        screenshot: PIL 截图对象

    Returns:
        np.ndarray: RGB 格式的 numpy 数组，形状为 (height, width, 3)
    """
    if screenshot.mode != "RGB":
        screenshot = screenshot.convert("RGB")

    screenshot_array = np.array(screenshot)
    return screenshot_array


def find_all_matches(
    screenshot_array: np.ndarray,
    template_array: np.ndarray,
    threshold: float = 0.999
) -> List[Tuple[int, int]]:
    """
    在截图中查找所有模板匹配位置

    使用 OpenCV 模板匹配算法定位锚点标记。

    Args:
        screenshot_array: 截图的 numpy 数组，形状为 (height, width, 3)
        template_array: 标记模板的 numpy 数组
        threshold: 匹配阈值，范围 0-1，默认 0.999（高精度匹配）

    Returns:
        List[Tuple[int, int]]: 所有匹配位置的左上角坐标列表，格式为 (x, y)
    """
    template_height, template_width = template_array.shape[:2]
    screenshot_height, screenshot_width = screenshot_array.shape[:2]

    # 模板大于截图时无法匹配
    if template_height > screenshot_height or template_width > screenshot_width:
        return []

    # TM_CCOEFF_NORMED 返回 -1 到 1 的值，1 表示完美匹配
    result = cv2.matchTemplate(
        screenshot_array, template_array, cv2.TM_CCOEFF_NORMED
    )

    # 筛选匹配位置
    match_locations = np.where(result >= threshold)
    matches = [(int(x), int(y)) for y, x in zip(match_locations[0], match_locations[1])]
    matches.sort()

    return matches


def find_template_bounds(
    screenshot_array: np.ndarray,
    template_path: str,
    threshold: float = 0.999
) -> Tuple[int, int, int, int]:
    """
    根据模板标记计算像素数据区域的边界

    通过两个锚点标记的位置确定整个数据区域的矩形边界。
    边界尺寸必须是 6 的倍数（因为数据以 6x6 像素节点为单位）。

    Args:
        screenshot_array: 截图的 numpy 数组
        template_path: 标记图片的路径
        threshold: 匹配阈值

    Returns:
        Tuple[int, int, int, int]: 矩形边界 (left, top, right, bottom)

    Raises:
        ValueError: 当找到的标记数量不是 2 个时
        ValueError: 当边界尺寸不是 6 的倍数时
    """
    template_array = load_template(template_path)
    template_height, template_width = template_array.shape[:2]

    matches = find_all_matches(screenshot_array, template_array, threshold)

    if len(matches) != 2:
        raise ValueError(f"需要找到 2 个标记，但找到 {len(matches)} 个")

    # 计算两个标记构成的矩形边界
    x1, y1 = matches[0]
    x2, y2 = matches[1]

    right1 = x1 + template_width
    bottom1 = y1 + template_height
    right2 = x2 + template_width
    bottom2 = y2 + template_height

    left = int(min(x1, x2))
    top = int(min(y1, y2))
    right = int(max(right1, right2))
    bottom = int(max(bottom1, bottom2))

    width = right - left
    height = bottom - top

    # 验证边界尺寸是 6 的倍数（节点大小）
    if width % 6 != 0 or height % 6 != 0:
        raise ValueError(f"边界尺寸必须是 6 的倍数，但得到 {width} x {height}")

    return (left, top, right, bottom)


# ============================================
# 像素节点类
# ============================================

class Node:
    """
    6x6 像素节点 - 基本数据单元

    游戏插件将各种状态信息编码为 6x6 像素的色块，通过颜色、亮度、
    哈希等特征传递数据。此类提供对这些特征的解析接口。

    节点结构：
    - full:  完整 6x6 区域，用于直接截取
    - middle: 左上 5x5 区域，用于纯色判断/取色/哈希/白字识别
    - inner:  中间 3x3 区域，用于计算平均亮度（value 值）
    """

    def __init__(self, x: int, y: int, img_array: np.ndarray) -> None:
        """
        初始化像素节点

        Args:
            x: 节点在数据网格中的 X 坐标（以 6px 为单位）
            y: 节点在数据网格中的 Y 坐标（以 6px 为单位）
            img_array: 节点的 6x6 RGB 像素数组
        """
        self.x = x
        self.y = y
        self.pix_array = img_array
        self._hash_cache = None

    # ----------------------------------------
    # 像素区域访问
    # ----------------------------------------

    @property
    def full(self) -> np.ndarray:
        """完整 6x6 像素区域"""
        return self.pix_array

    @property
    def middle(self) -> np.ndarray:
        """
        左上 5x5 像素区域

        用于：纯色判断、颜色采样、哈希计算、白色数字识别
        """
        return self.pix_array[0:5, 0:5]

    @property
    def inner(self) -> np.ndarray:
        """
        中间 3x3 像素区域

        用于：计算平均亮度（value 值）
        """
        return self.pix_array[1:4, 1:4]

    # ----------------------------------------
    # 亮度/数值计算
    # ----------------------------------------

    @property
    def mean_value(self) -> np.floating:
        """中间 3x3 区域的平均亮度值（0-255）"""
        return np.mean(self.inner)

    @property
    def value_percent(self) -> np.floating:
        """亮度百分比（0-100%）"""
        return self.mean_value / 255.0 * 100

    @property
    def value_decimal(self) -> np.floating:
        """亮度小数（0.0-1.0）"""
        return self.mean_value / 255.0

    # ----------------------------------------
    # 纯色判断
    # ----------------------------------------

    @property
    def is_pure(self) -> bool:
        """是否为纯色节点（5x5 区域颜色一致）"""
        first_pixel = self.middle[0, 0]
        return bool(np.all(self.middle == first_pixel))

    @property
    def is_not_pure(self) -> bool:
        """是否为非纯色节点（包含图案）"""
        return not self.is_pure

    @property
    def is_black(self) -> bool:
        """是否为纯黑色节点"""
        return self.is_pure and (tuple(self.color) == (0, 0, 0))

    @property
    def is_white(self) -> bool:
        """是否为纯白色节点（通常表示布尔值 True）"""
        return self.is_pure and (tuple(self.color) == (255, 255, 255))

    # ----------------------------------------
    # 颜色信息
    # ----------------------------------------

    @property
    def color(self) -> Tuple[int, int, int]:
        """
        获取节点颜色（仅对纯色节点有效）

        Returns:
            Tuple[int, int, int]: RGB 颜色元组

        Raises:
            ValueError: 当节点非纯色时
        """
        if self.is_pure:
            return tuple(self.middle[0, 0])
        raise ValueError("非纯色节点没有统一颜色")

    @property
    def color_string(self) -> str:
        """颜色字符串表示（R,G,B），用于映射表查找"""
        return f"{self.color[0]},{self.color[1]},{self.color[2]}"

    # ----------------------------------------
    # 白色数字识别（定制字体）
    # ----------------------------------------

    @property
    def white_count_raw(self) -> int:
        """
        5x5 区域中白色像素的数量

        用于识别定制字体渲染的数字（层数/充能数）。
        """
        return int(np.count_nonzero(np.all(self.middle == (255, 255, 255), axis=2)))

    @property
    def count(self) -> int:
        """
        根据白色像素数量解析的实际数值

        映射关系基于定制字体的像素特征：
        - 0-9:  直接对应（0-9 层）
        - 10:   表示 0 层（特殊映射）
        - >=11: 表示 20 层（上限值）

        Returns:
            int: 解析的数值（0, 1-9, 20）
        """
        if self.is_pure:
            return 0
        if self.white_count_raw <= 9:
            return self.white_count_raw
        if self.white_count_raw == 10:
            return 0
        if self.white_count_raw >= 11:
            return 20
        return 0

    # ----------------------------------------
    # 剩余时间计算（冷却/持续时间）
    # ----------------------------------------

    @property
    def remaining(self) -> float:
        """
        从亮度值解码的剩余时间（秒）

        游戏内使用 remaining_curve 将时间编码为亮度值，
        此属性执行反向查找，将亮度映射回时间。

        亮度-时间映射点（基于游戏内曲线）：
        - 0 亮度  -> 0.0 秒
        - 100 亮度 -> 5.0 秒
        - 150 亮度 -> 30.0 秒
        - 200 亮度 -> 155.0 秒
        - 255 亮度 -> 375.0 秒

        Returns:
            float: 剩余时间（秒）
        """
        y = int(self.mean_value)

        points = [(0.0, 0), (5.0, 100), (30.0, 150),
                  (155.0, 200), (375.0, 255)]

        # 边界处理
        if y <= points[0][1]:
            return points[0][0]
        if y >= points[-1][1]:
            return points[-1][0]

        # 线性插值
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            if y1 <= y <= y2:
                return x1 + (x2 - x1) * (y - y1) / (y2 - y1)
        return 0.0

    # ----------------------------------------
    # 哈希与标题
    # ----------------------------------------

    @property
    def hash(self) -> str:
        """
        节点 5x5 区域的哈希值

        用于识别技能图标、Buff/Debuff 图标等。
        使用 xxhash 算法保证性能。
        """
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(
                np.ascontiguousarray(self.middle), seed=0
            )
        return self._hash_cache

    @property
    def title(self) -> str:
        """
        节点的可读标题

        优先从 HashMap 查找已知的图标名称，
        未知图标返回哈希值本身。
        """
        if self.hash in HashMap["Used"]:
            return HashMap["Used"][self.hash]
        return self.hash

    # ----------------------------------------
    # 调试工具
    # ----------------------------------------

    def show(self) -> None:
        """用系统默认的图片查看器显示节点内容"""
        inner_img = Image.fromarray(self.middle)
        inner_img.show()


# ============================================
# 像素数据解析器
# ============================================

class PixelDumper:
    """
    像素数据解析器 - 核心数据提取引擎

    从截图中按照插件约定的数据布局，提取完整的游戏状态信息。
    数据布局与 WowPixelDumper.lua 中的 CreatePixelFrame 对应。

    数据区域结构（6x6 像素节点坐标）：

    玩家区域 (2,2) 开始：
    - Buff 序列:    x=2..29,  y=2 (28个)
    - Debuff 序列:  x=30..36, y=2 (7个)
    - 技能序列:     x=2..25,  y=6 (24个)
    - 状态标志:     x=37..46, y=2..5

    目标区域 (47,2) 开始：
    - Debuff 序列:  x=47..53, y=2 (7个)
    - 状态信息:     x=39..46, y=6..7

    Focus 区域 (47,6) 开始：
    - 结构与目标区域类似

    队伍区域 (12,10) 开始：
    - 4个队友，每个占 13 列宽度
    """

    def __init__(self, img_array: np.ndarray) -> None:
        """
        初始化像素解析器

        Args:
            img_array: 裁剪后的像素数据区域 RGB 数组
        """
        self.pix_array = img_array

    def get_node(self, x: int, y: int) -> Node:
        """
        获取指定坐标的像素节点

        Args:
            x: 节点 X 坐标（以 6px 为单位）
            y: 节点 Y 坐标（以 6px 为单位）

        Returns:
            Node: 对应位置的像素节点对象

        Raises:
            ValueError: 当坐标超出范围时
        """
        start_x = x * 6
        start_y = y * 6
        end_x = start_x + 6
        end_y = start_y + 6

        max_x = self.pix_array.shape[1] // 6
        max_y = self.pix_array.shape[0] // 6

        if x >= max_x or y >= max_y:
            raise ValueError(f"节点坐标 ({x},{y}) 超出范围 (最大 {max_x},{max_y})")

        array = self.pix_array[start_y:end_y, start_x:end_x]
        return Node(x, y, array)

    # ----------------------------------------
    # 数据读取：通用组件
    # ----------------------------------------

    def read_health_bar(self, left: int, top: int, length: int) -> float:
        """
        读取白色进度条（吸收盾/血量条）

        对应插件内的 CreateWhiteBar，统计指定区域内中间两行像素的
        白色像素占比来计算填充程度。

        Args:
            left:   起始节点 X 坐标
            top:    节点 Y 坐标
            length: 进度条长度（节点数）

        Returns:
            float: 白色像素占比（0.0-1.0）
        """
        # 收集所有节点的中间两行像素（6x6 节点的第 3-4 行）
        nodes_middle_pix = [
            self.get_node(x, top).full[2:4, :]
            for x in range(left, left + length)
        ]

        # 统计白色像素数量
        white_count = sum(
            np.count_nonzero(np.all(node == (255, 255, 255), axis=2))
            for node in nodes_middle_pix
        )

        # 计算总像素数
        total_count = sum(node.shape[0] * node.shape[1] for node in nodes_middle_pix)

        return white_count / total_count if total_count > 0 else 0.0

    def read_spell_sequence(self, left: int, top: int, length: int) -> Tuple[list[dict], dict[str, dict]]:
        """
        读取技能序列信息

        对应插件内的 SpellFrame，解析技能图标、冷却时间、高亮状态、充能数。

        节点布局（每个技能占 1 列 x 4 行）：
        - top:     技能图标（哈希识别）
        - top+1:   剩余冷却时间（remaining）
        - top+2:   高亮状态（非白色表示高亮）
        - top+3:   充能数（白色数字识别）

        Args:
            left:   起始节点 X 坐标
            top:    起始节点 Y 坐标
            length: 技能数量

        Returns:
            Tuple[list[dict], dict]: 
                - 技能序列列表（按位置排序）
                - 技能字典（以技能名为键）
        """
        result_sequence = []
        result_dict = {}

        for x in range(left, left + length):
            icon_node = self.get_node(x, top)

            # 跳过空槽位（纯黑色）
            if icon_node.is_pure and icon_node.is_black:
                continue

            remain_node = self.get_node(x, top + 1)
            height_node = self.get_node(x, top + 2)
            charge_node = self.get_node(x, top + 3)

            spell_title = icon_node.title

            # 冷却时间：非黑色节点表示有冷却
            spell_remaining = remain_node.remaining if not remain_node.is_black else 0

            # 高亮状态：非白色表示高亮可用
            spell_height = not height_node.is_white

            # 充能数：非黑色表示有充能信息
            spell_charge = charge_node.count if not (charge_node.is_pure and charge_node.is_black) else None

            spell_data = {
                "title": spell_title,
                "remaining": spell_remaining,
                "height": spell_height,
                "charge": spell_charge,
            }

            result_sequence.append(spell_data)
            result_dict[spell_title] = spell_data

        return result_sequence, result_dict

    def read_aura_sequence(self, left: int, top: int, length: int) -> Tuple[list[dict], dict[str, dict]]:
        """
        读取 Buff/Debuff 序列信息

        对应插件内的 CreateAuraSequence，解析光环图标、剩余时间、类型、层数。

        节点布局（每个光环占 1 列 x 4 行）：
        - top:     图标（哈希识别）
        - top+1:   剩余时间（remaining）
        - top+2:   类型标识（纯色映射到 BuffType）
        - top+3:   层数（白色数字识别）

        Args:
            left:   起始节点 X 坐标
            top:    起始节点 Y 坐标
            length: 光环数量

        Returns:
            Tuple[list[dict], dict]:
                - 光环序列列表（按位置排序）
                - 光环字典（以光环名为键）
        """
        result_sequence = []
        result_dict = {}

        for x in range(left, left + length):
            icon_node = self.get_node(x, top)

            # 跳过空槽位
            if icon_node.is_pure and icon_node.is_black:
                continue

            remain_node = self.get_node(x, top + 1)
            type_node = self.get_node(x, top + 2)
            count_node = self.get_node(x, top + 3)

            aura_title = icon_node.title

            # 剩余时间：黑色表示永久/无时间
            aura_remaining = None if remain_node.is_black else remain_node.remaining

            # 类型：从 ColorMap 查找颜色映射
            if type_node.is_pure and type_node.color_string in ColorMap["BuffType"]:
                aura_type = ColorMap["BuffType"][type_node.color_string]
            else:
                aura_type = "Unknown"

            aura_data = {
                "title": aura_title,
                "remaining": aura_remaining,
                "type": aura_type,
                "count": count_node.count,
            }

            result_sequence.append(aura_data)
            result_dict[aura_title] = aura_data

        return result_sequence, result_dict

    # ----------------------------------------
    # 数据读取：完整状态提取
    # ----------------------------------------

    def extract_all_data(self) -> dict:
        """
        提取完整的游戏状态数据

        按照插件约定的数据布局，从像素区域解析所有游戏状态信息，
        包括玩家、目标、Focus、队伍等所有数据。

        Returns:
            dict: 完整的游戏状态数据结构
        """
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "misc": {},
            "spec": {},
            "player": {},
            "target": {},
            "focus": {},
            "party": {}
        }

        # 护甲类型标识（节点 26,6）
        data["misc"]["ac"] = self.get_node(26, 6).title

        # ========================================
        # 玩家状态
        # ========================================

        data["player"]["aura"] = {
            # Buff: x=2..29 (28个)
            "buff": [],
            "buff_dict": {},
            # Debuff: x=30..36 (7个)
            "debuff": [],
            "debuff_dict": {}
        }

        data["player"]["aura"]["buff"], data["player"]["aura"]["buff_dict"] = \
            self.read_aura_sequence(left=2, top=2, length=28)

        data["player"]["aura"]["debuff"], data["player"]["aura"]["debuff_dict"] = \
            self.read_aura_sequence(left=30, top=2, length=7)

        # 技能序列: x=2..25, y=6 (24个)
        data["player"]["spell_sequence"], data["player"]["spell"] = \
            self.read_spell_sequence(left=2, top=6, length=24)

        # 玩家状态标志
        data["player"]["status"] = {
            # 吸收盾进度条
            "damage_absorbs": self.read_health_bar(left=37, top=4, length=10) * 100,
            "heal_absorbs": self.read_health_bar(left=37, top=5, length=10) * 100,

            # 血量和能量（亮度百分比）
            "health": self.get_node(46, 2).value_percent,
            "power": self.get_node(46, 3).value_percent,

            # 布尔状态标志（白色=真）
            "in_combat": self.get_node(37, 2).is_white,
            "in_movement": self.get_node(38, 2).is_white,
            "in_vehicle": self.get_node(39, 2).is_white,
            "is_empowered": self.get_node(40, 2).is_white,

            # 施法信息
            "cast_icon": None,
            "cast_duration": None,

            # 引导技能信息
            "channel_icon": None,
            "channel_duration": None,

            # 职业和职责（颜色映射）
            "class": "NONE",
            "role": "NONE",

            # 死亡状态
            "deaded": self.get_node(39, 3).is_white
        }

        # 施法信息（节点 41-42, y=2）
        cast_icon_node = self.get_node(41, 2)
        if cast_icon_node.is_not_pure:
            data["player"]["status"]["cast_icon"] = cast_icon_node.title
            data["player"]["status"]["cast_duration"] = self.get_node(42, 2).value_percent

        # 引导技能信息（节点 43-44, y=2）
        channel_icon_node = self.get_node(43, 2)
        if channel_icon_node.is_not_pure:
            data["player"]["status"]["channel_icon"] = channel_icon_node.title
            data["player"]["status"]["channel_duration"] = self.get_node(44, 2).value_percent

        # 职业和职责（颜色映射）
        class_node = self.get_node(37, 3)
        if class_node.is_pure:
            data["player"]["status"]["class"] = ColorMap["Class"].get(class_node.color_string, "NONE")

        role_node = self.get_node(38, 3)
        if role_node.is_pure:
            data["player"]["status"]["role"] = ColorMap["Role"].get(role_node.color_string, "NONE")

        # ========================================
        # 目标状态
        # ========================================

        data["target"]["aura"] = {
            "debuff": [],
            "debuff_dict": {}
        }

        data["target"]["status"] = {
            "exists": self.get_node(39, 6).is_white
        }

        if data["target"]["status"]["exists"]:
            # 目标 Debuff: x=47..53, y=2 (7个)
            data["target"]["aura"]["debuff"], data["target"]["aura"]["debuff_dict"] = \
                self.read_aura_sequence(left=47, top=2, length=7)

            # 目标基本状态
            data["target"]["status"].update({
                "can_attack": self.get_node(40, 6).is_white,
                "is_self": self.get_node(41, 6).is_white,
                "alive": self.get_node(42, 6).is_white,
                "in_combat": self.get_node(43, 6).is_white,
                "in_range": self.get_node(44, 6).is_white,
                "health": self.get_node(46, 6).value_percent,

                # 施法和引导信息
                "cast_icon": None,
                "cast_duration": None,
                "cast_interruptible": None,
                "channel_icon": None,
                "channel_duration": None,
                "channel_interruptible": None
            })

            # 目标施法信息（节点 39-41, y=7）
            target_cast_node = self.get_node(39, 7)
            if target_cast_node.is_not_pure:
                data["target"]["status"]["cast_icon"] = target_cast_node.title
                data["target"]["status"]["cast_duration"] = self.get_node(40, 7).value_percent
                data["target"]["status"]["cast_interruptible"] = self.get_node(41, 7).is_white

            # 目标引导技能信息（节点 42-44, y=7）
            target_channel_node = self.get_node(42, 7)
            if target_channel_node.is_not_pure:
                data["target"]["status"]["channel_icon"] = target_channel_node.title
                data["target"]["status"]["channel_duration"] = self.get_node(43, 7).value_percent
                data["target"]["status"]["channel_interruptible"] = self.get_node(44, 7).is_white

        # ========================================
        # Focus 状态
        # ========================================

        data["focus"]["aura"] = {
            "debuff": [],
            "debuff_dict": {}
        }

        data["focus"]["status"] = {
            "exists": self.get_node(39, 8).is_white
        }

        if data["focus"]["status"]["exists"]:
            # Focus Debuff: x=47..53, y=6 (7个)
            data["focus"]["aura"]["debuff"], data["focus"]["aura"]["debuff_dict"] = \
                self.read_aura_sequence(left=47, top=6, length=7)

            data["focus"]["status"].update({
                "can_attack": self.get_node(40, 8).is_white,
                "is_self": self.get_node(41, 8).is_white,
                "alive": self.get_node(42, 8).is_white,
                "in_combat": self.get_node(43, 8).is_white,
                "in_range": self.get_node(44, 8).is_white,
                "health": self.get_node(46, 8).value_percent,

                "cast_icon": None,
                "cast_duration": None,
                "cast_interruptible": None,
                "channel_icon": None,
                "channel_duration": None,
                "channel_interruptible": None
            })

            # Focus 施法信息（节点 39-41, y=9）
            focus_cast_node = self.get_node(39, 9)
            if focus_cast_node.is_not_pure:
                data["focus"]["status"]["cast_icon"] = focus_cast_node.title
                data["focus"]["status"]["cast_duration"] = self.get_node(40, 9).value_percent
                data["focus"]["status"]["cast_interruptible"] = self.get_node(41, 9).is_white

            # Focus 引导技能信息（节点 42-44, y=9）
            focus_channel_node = self.get_node(42, 9)
            if focus_channel_node.is_not_pure:
                data["focus"]["status"]["channel_icon"] = focus_channel_node.title
                data["focus"]["status"]["channel_duration"] = self.get_node(43, 9).value_percent
                data["focus"]["status"]["channel_interruptible"] = self.get_node(44, 9).is_white

        # ========================================
        # 队伍状态（4个队友）
        # ========================================

        for i in range(1, 5):
            party_key = f"party{i}"
            data["party"][party_key] = {
                "exists": False,
                "status": {},
                "aura": {}
            }

            # 队友存在标志（节点 13*i-1, y=14）
            party_exist = self.get_node(13 * i - 1, 14).is_white
            data["party"][party_key]["exists"] = party_exist

            if party_exist:
                # 队友基础状态
                data["party"][party_key]["status"] = {
                    "in_range": self.get_node(13 * i, 14).is_white,
                    "health": self.get_node(13 * i + 1, 14).value_percent,
                    "selectd": self.get_node(13 * i + 1, 15).is_white,

                    # 吸收盾
                    "damage_absorbs": self.read_health_bar(left=13*i - 11, top=14, length=10) * 100,
                    "heal_absorbs": self.read_health_bar(left=13*i - 11, top=15, length=10) * 100
                }

                # 职业和职责
                class_node = self.get_node(13 * i - 1, 15)
                data["party"][party_key]["status"]["class"] = (
                    ColorMap["Class"].get(class_node.color_string, "NONE")
                    if class_node.is_pure else "NONE"
                )

                role_node = self.get_node(13 * i, 15)
                data["party"][party_key]["status"]["role"] = (
                    ColorMap["Role"].get(role_node.color_string, "NONE")
                    if role_node.is_pure else "NONE"
                )

                # 队友光环
                data["party"][party_key]["aura"] = {
                    # Buff: 7个
                    "buff": [],
                    "buff_dict": {},
                    # Debuff: 6个
                    "debuff": [],
                    "debuff_dict": {}
                }

                data["party"][party_key]["aura"]["buff"], data["party"][party_key]["aura"]["buff_dict"] = \
                    self.read_aura_sequence(left=13*i - 11, top=10, length=7)

                data["party"][party_key]["aura"]["debuff"], data["party"][party_key]["aura"]["debuff_dict"] = \
                    self.read_aura_sequence(left=13*i - 4, top=10, length=6)

        return data
