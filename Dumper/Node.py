"""像素节点和提取器模块 - 8x8像素节点类和数据提取器。"""

from typing import Any

import numpy as np
import xxhash

from Database import NodeTitleManager
from Utils import _ColorMap


####### 像素节点类 #######

class Node:
    """8x8像素节点 - 基本数据单元。

    游戏插件将各种状态信息编码为 8x8 像素的色块，通过颜色、亮度、
    哈希等特征传递数据。此类提供对这些特征的解析接口。

    节点结构：
    - full:  完整 8x8 区域，用于直接截取
    - middle: 左上 6x6 区域，用于纯色判断/取色/哈希/白字识别
    - inner:  中间 4x4 区域，用于计算平均亮度（value 值）
    """

    # 类级别的title_manager引用
    _title_manager: NodeTitleManager | None = None

    def __init__(self, x: int, y: int, img_array: np.ndarray) -> None:
        """初始化像素节点。

        Args:
            x: 节点在数据网格中的 X 坐标（以 8px 为单位）
            y: 节点在数据网格中的 Y 坐标（以 8px 为单位）
            img_array: 节点的 8x8 RGB 像素数组
        """
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = img_array
        self._hash_cache: str | None = None

    @classmethod
    def set_title_manager(cls, manager: NodeTitleManager) -> None:
        """设置全局的TitleManager。

        应在程序启动时调用，通常在MainWindow.__init__中
        """
        cls._title_manager = manager

    ####### 像素区域访问 #######

    @property
    def full(self) -> np.ndarray:
        """完整 8x8 像素区域。"""
        return self.pix_array

    @property
    def middle(self) -> np.ndarray:
        """中心 6x6 像素区域。

        用于：纯色判断、颜色采样、哈希计算、白色数字识别
        """
        return self.pix_array[1:7, 1:7]

    @property
    def inner(self) -> np.ndarray:
        """中间 4x4 像素区域。

        用于：计算平均亮度（value 值）
        """
        return self.pix_array[2:6, 2:6]

    ####### 亮度/数值计算 #######

    @property
    def mean_value(self) -> np.floating:
        """中间 4x4 区域的平均亮度值（0-255）。"""
        return np.mean(self.inner)

    @property
    def value_percent(self) -> np.floating:
        """亮度百分比（0-100%）。"""
        return self.mean_value / 255.0 * 100

    @property
    def value_decimal(self) -> np.floating:
        """亮度小数（0.0-1.0）。"""
        return self.mean_value / 255.0

    ####### 纯色判断 #######

    @property
    def is_pure(self) -> bool:
        """是否为纯色节点（4x4 区域颜色一致）。"""
        first_pixel: np.ndarray = self.inner[0, 0]
        return bool(np.all(self.inner == first_pixel))

    @property
    def is_not_pure(self) -> bool:
        """是否为非纯色节点（包含图案）。"""
        return not self.is_pure

    @property
    def is_black(self) -> bool:
        """是否为纯黑色节点。"""
        return self.is_pure and (tuple(self.color) == (0, 0, 0))

    @property
    def is_white(self) -> bool:
        """是否为纯白色节点（通常表示布尔值 True）。"""
        return self.is_pure and (tuple(self.color) == (255, 255, 255))

    ####### 颜色信息 #######

    @property
    def color(self) -> tuple[int, int, int]:
        """获取节点颜色（仅对纯色节点有效）。

        Returns:
            tuple[int, int, int]: RGB 颜色元组

        Raises:
            ValueError: 当节点非纯色时
        """
        if self.is_pure:
            return tuple(self.inner[0, 0])
        raise ValueError('非纯色节点没有统一颜色')

    @property
    def color_string(self) -> str:
        """颜色字符串表示（R,G,B），用于映射表查找。"""
        return f'{self.color[0]},{self.color[1]},{self.color[2]}'

    ####### 白色数字识别（定制字体） #######

    @property
    def white_count_raw(self) -> int:
        """6*6 区域中白色像素的数量。

        用于识别定制字体渲染的数字（层数/充能数）。
        """
        return int(np.count_nonzero(np.all(self.middle == (255, 255, 255), axis=2)))

    @property
    def count(self) -> int:
        """根据白色像素数量解析的实际数值。

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

    ####### 剩余时间计算（冷却/持续时间） #######

    @property
    def remaining(self) -> float:
        """从亮度值解码的剩余时间（秒）。

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
        y: int = int(self.mean_value)

        points: list[tuple[float, int]] = [(0.0, 0), (5.0, 100), (30.0, 150),
                                           (155.0, 200), (375.0, 255)]

        # 边界处理
        if y <= points[0][1]:
            return points[0][0]
        if y >= points[-1][1]:
            return points[-1][0]

        # 线性插值
        for i in range(len(points) - 1):
            x1: float
            y1: int
            x2: float
            y2: int
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            if y1 <= y <= y2:
                return x1 + (x2 - x1) * (y - y1) / (y2 - y1)
        return 0.0

    ####### 哈希与标题 #######

    @property
    def hash(self) -> str:
        """节点 6x6 区域的哈希值。

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
        """节点的可读标题。

        通过NodeTitleManager获取，支持：
        1. Hash直接匹配
        2. 余弦相似度匹配
        3. 返回hash（未匹配时）
        """
        if Node._title_manager is not None:
            return Node._title_manager.get_title(
                middle_hash=self.hash,
                middle_array=self.middle,
                full_array=self.full
            )
        return self.hash


####### 数据提取器类（原DataExtractor） #######

class NodeExtractor:
    """像素数据提取器 - 核心数据提取引擎。

    从截图中按照插件约定的数据布局，提取完整的游戏状态信息。
    数据布局与 PixelFrame.lua 中的 CreatePixelFrame 对应。

    数据区域结构（8x8 像素节点坐标）：

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
        """初始化像素数据提取器。

        Args:
            img_array: 裁剪后的像素数据区域 RGB 数组
        """
        self.pix_array: np.ndarray = img_array

    def node(self, x: int, y: int) -> Node:
        """获取指定坐标的像素节点。

        Args:
            x: 节点 X 坐标（以 8px 为单位）
            y: 节点 Y 坐标（以 8px 为单位）

        Returns:
            Node: 对应位置的像素节点对象

        Raises:
            ValueError: 当坐标超出范围时
        """
        start_x: int = x * 8
        start_y: int = y * 8
        end_x: int = start_x + 8
        end_y: int = start_y + 8

        max_x: int = self.pix_array.shape[1] // 8
        max_y: int = self.pix_array.shape[0] // 8

        if x >= max_x or y >= max_y:
            raise ValueError(f'节点坐标 ({x},{y}) 超出范围 (最大 {max_x},{max_y})')

        array: np.ndarray = self.pix_array[start_y:end_y, start_x:end_x]
        return Node(x, y, array)

    ####### 数据读取：通用组件 #######

    def read_health_bar(self, left: int, top: int, length: int) -> float:
        """读取白色进度条（吸收盾/血量条）。

        对应插件内的 CreateWhiteBar，统计指定区域内中间两行像素的
        白色像素占比来计算填充程度。

        Args:
            left:   起始节点 X 坐标
            top:    节点 Y 坐标
            length: 进度条长度（节点数）

        Returns:
            float: 白色像素占比（0.0-1.0）
        """
        # 收集所有节点的中间两行像素（8x8 节点的第 3-4 行）
        nodes_middle_pix: list[np.ndarray] = [
            self.node(x, top).full[3:5, :]
            for x in range(left, left + length)
        ]

        # 统计白色像素数量
        white_count = sum(
            np.count_nonzero(np.all(node == (255, 255, 255), axis=2))
            for node in nodes_middle_pix
        )

        # 计算总像素数
        total_count: int = sum(node.shape[0] * node.shape[1] for node in nodes_middle_pix)

        return white_count / total_count if total_count > 0 else 0.0

    def read_spell_sequence(self, left: int, top: int, length: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """读取技能序列信息。

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
            tuple[list[dict], dict]: (技能序列列表, 技能字典)
        """
        result_sequence: list[dict[str, Any]] = []
        result_dict: dict[str, dict[str, Any]] = {}

        for x in range(left, left + length):
            icon_node: Node = self.node(x, top)

            # 跳过空槽位（纯黑色）
            if icon_node.is_pure and icon_node.is_black:
                continue

            remain_node: Node = self.node(x, top + 1)
            height_node: Node = self.node(x, top + 2)
            charge_node: Node = self.node(x, top + 3)

            spell_title: str = icon_node.title

            # 冷却时间：非黑色节点表示有冷却
            spell_remaining: float = remain_node.remaining if not remain_node.is_black else 0.0

            # 高亮状态：非白色表示高亮可用
            spell_height: bool = height_node.is_white

            # 充能数：非黑色表示有充能信息
            spell_charge: int = int(charge_node.count) if not (charge_node.is_pure and charge_node.is_black) else 0

            spell_data: dict[str, Any] = {
                'title': spell_title,
                'remaining': spell_remaining,
                'height': spell_height,
                'charge': spell_charge,
            }

            result_sequence.append(spell_data)
            result_dict[spell_title] = spell_data

        return result_sequence, result_dict

    def read_aura_sequence(self, left: int, top: int, length: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """读取 Buff/Debuff 序列信息。

        对应插件内的 CreateAuraSequence，解析光环图标、剩余时间、类型、层数。

        节点布局（每个光环占 1 列 x 4 行）：
        - top:     图标（哈希识别）
        - top+1:   剩余时间（remaining）
        - top+2:   类型标识（纯色映射到 BuffType）
        - top+3:   层数（白色数字识别）

        Args:
            left:   起始节点 X 坐标
            top:    节点 Y 坐标
            length: 光环数量

        Returns:
            tuple[list[dict], dict]: (光环序列列表, 光环字典)
        """
        result_sequence: list[dict[str, Any]] = []
        result_dict: dict[str, dict[str, Any]] = {}

        for x in range(left, left + length):
            icon_node: Node = self.node(x, top)

            # 跳过空槽位
            if icon_node.is_pure and icon_node.is_black:
                continue

            remain_node: Node = self.node(x, top + 1)
            type_node: Node = self.node(x, top + 2)
            count_node: Node = self.node(x, top + 3)

            aura_title: str = icon_node.title

            # 剩余时间：黑色表示永久/无时间
            aura_remaining: float = 0.0 if remain_node.is_black else remain_node.remaining

            # 类型映射：使用ColorMap将颜色映射到BuffType
            aura_type: str = 'Unknown'
            if type_node.is_pure:
                aura_type = _ColorMap['BuffType'].get(type_node.color_string, 'Unknown')

            aura_data: dict[str, Any] = {
                'title': aura_title,
                'remaining': aura_remaining,
                'type': aura_type,
                'count': count_node.count,
            }

            result_sequence.append(aura_data)
            result_dict[aura_title] = aura_data

        return result_sequence, result_dict
