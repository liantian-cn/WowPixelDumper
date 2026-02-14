"""像素节点和提取器模块 - 8x8像素节点类和数据提取器。"""

from typing import Any

import numpy as np
import xxhash

from Database import NodeTitleManager
from Utils import _ColorMap


class PixelBlock:
    """
    像素块

    最基础的数据单元。

    像素块是一组数组，表示若干个像素。

    数据块没有坐标，承担最基础的计算任务。
    """

    def __init__(self, pix_array: np.ndarray):
        self.pix_array: np.ndarray = pix_array
        self._hash_cache: str | None = None

    @property
    def array(self) -> np.ndarray:
        return self.pix_array

    @property
    def hash(self) -> str:
        """节点的哈希值。"""
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(np.ascontiguousarray(self.pix_array), seed=0)
        return self._hash_cache

    ####### 亮度计算 #######
    @property
    def mean(self) -> np.floating:
        """亮度均值 (0-255) """
        result = np.mean(self.pix_array)
        return result

    @property
    def decimal(self) -> np.floating:
        """亮度小数(0.0-1.0) """
        return self.mean / 255.0

    @property
    def percent(self) -> np.floating:
        """亮度百分比 (0-100%) 。"""
        return self.mean / 255.0 * 100

    ####### 颜色计算 #######
    @property
    def is_pure(self) -> bool:
        """是否为纯色块 (所有像素颜色一致) 。"""
        first_pixel: np.ndarray = self.pix_array[0, 0]
        return bool(np.all(self.pix_array == first_pixel))

    @property
    def is_not_pure(self) -> bool:
        return not self.is_pure

    @property
    def color(self) -> tuple[int, int, int]:
        """获取节点颜色 (仅对纯色节点有效) 。
        """
        return tuple(self.pix_array[0, 0])

    @property
    def color_string(self) -> str:
        return f'{self.color[0]},{self.color[1]},{self.color[2]}'

    @property
    def is_black(self) -> bool:
        # 是否为纯黑色节点
        return self.is_pure and (tuple(self.color) == (0, 0, 0))

    @property
    def is_white(self) -> bool:
        # 是否为纯白色节点
        return self.is_pure and (tuple(self.color) == (255, 255, 255))

    @property
    def is_red(self) -> bool:
        # 是否为纯红色节点
        return self.is_pure and (tuple(self.color) == (255, 0, 0))

    @property
    def is_green(self) -> bool:
        # 是否为纯绿色节点
        return self.is_pure and (tuple(self.color) == (0, 255, 0))

    @property
    def is_blue(self) -> bool:
        # 是否为纯蓝色节点
        return self.is_pure and (tuple(self.color) == (0, 0, 255))

    ####### 特殊计算 #######
    @property
    def white_count(self) -> int:
        """白色像素的数量。 (搭配特殊字体使用) 
        """
        return int(np.count_nonzero(np.all(self.pix_array == (255, 255, 255), axis=2)))

    ####### 剩余时间计算 (冷却/持续时间)  #######

    @property
    def remaining(self) -> float:
        """从亮度值解码的剩余时间 (秒) 。

        游戏内使用 remaining_curve 将时间编码为亮度值，
        此属性执行反向查找，将亮度映射回时间。

        亮度-时间映射点 (基于游戏内曲线) ：
        - 0 亮度  -> 0.0 秒
        - 100 亮度 -> 5.0 秒
        - 150 亮度 -> 30.0 秒
        - 200 亮度 -> 155.0 秒
        - 255 亮度 -> 375.0 秒

        Returns:
            float: 剩余时间 (秒) 
        """
        y: int = int(self.mean)

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


class Node:
    """二级数据单元。

    节点是包含相对于画布横纵坐标的像素块。
    一个标准节点目前是8x8大小。

    节点可以按需求划分成如下数据块：
    - full:  完整 8x8 区域，用于直接截取
    - middle: 中间 6x6 区域, 用于计算哈希、获取标题、文字识别
    - inner:  中间 4x4 区域, 用于计算平均亮度、获取颜色，颜色计算。
    - sub: 现有node基础上, 再次切分四块, 并取各自中间2x2, 按左上、右上、左下、右下返回数据块信息, 由于只包含4个像素的信息, 只能用来计算颜色、亮度。
    - footnote: 右下2x2。
    """

    # 类级别的title_manager引用
    _title_manager: NodeTitleManager | None = None

    def __init__(self, x: int, y: int, img_array: np.ndarray) -> None:
        """初始化像素节点。

        Args:
            x: 节点在数据网格中的 X 坐标 (以 8px 为单位) 
            y: 节点在数据网格中的 Y 坐标 (以 8px 为单位) 
            img_array: 节点的 8x8 RGB 像素数组
        """
        self.x: int = x
        self.y: int = y
        self.pix_array: np.ndarray = img_array
        self._hash_cache: str | None = None
        self._full = None
        self._middle = None
        self._inner = None
        self._sub = None
        self._footnote = None

    @classmethod
    def set_title_manager(cls, manager: NodeTitleManager) -> None:
        """设置全局的TitleManager。

        应在程序启动时调用，通常在MainWindow.__init__中
        """
        cls._title_manager = manager

    ####### 像素区域访问 #######

    @property
    def full(self) -> PixelBlock:
        """完整 8x8 区域，用于直接截取。"""
        if self._full is None:
            self._full = PixelBlock(self.pix_array)
        return self._full

    @property
    def middle(self) -> PixelBlock:
        """中心 6x6 像素区域:  用于计算哈希、获取标题、文字识别"""
        if self._middle is None:
            self._middle = PixelBlock(self.pix_array[1:7, 1:7])
        return self._middle

    @property
    def inner(self) -> PixelBlock:
        """中间 4x4 区域, 用于计算平均亮度、获取颜色，颜色计算。"""
        if self._inner is None:
            self._inner = PixelBlock(self.pix_array[2:6, 2:6])
        return self._inner

    @property
    def subNode(self) -> tuple[PixelBlock, PixelBlock, PixelBlock, PixelBlock]:
        """现有node基础上, 再次切分四块, 并取各自中间2x2, 按左上、右上、左下、右下返回数据块信息, 由于只包含4个像素的信息, 只能用来计算颜色、亮度。
              0   1   2   3   4   5   6   7
            ┌───┬───┬───┬───┬───┬───┬───┬───┐
        0   │   │   │   │   │   │   │   │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        1   │   │ █ │ █ │   │   │ ▓ │ ▓ │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        2   │   │ █ │ █ │   │   │ ▓ │ ▓ │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        3   │   │   │   │   │   │   │   │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        4   │   │   │   │   │   │   │   │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        5   │   │ ░ │ ░ │   │   │ ▒ │ ▒ │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        6   │   │ ░ │ ░ │   │   │ ▒ │ ▒ │   │
            ├───┼───┼───┼───┼───┼───┼───┼───┤
        7   │   │   │   │   │   │   │   │   │
            └───┴───┴───┴───┴───┴───┴───┴───┘
    """

        if self._sub is None:
            self._sub = [PixelBlock(self.pix_array[1:3, 1:3]),
                         PixelBlock(self.pix_array[1:3, 5:7]),
                         PixelBlock(self.pix_array[5:7, 1:3]),
                         PixelBlock(self.pix_array[5:7, 5:7])]
        return (self._sub[0], self._sub[1], self._sub[2], self._sub[3])

    @property
    def mixNode(self) -> tuple[PixelBlock, PixelBlock, PixelBlock, PixelBlock]:
        "subNode的另一个命名, 符合lua内的CreateMixedNode"
        return self.subNode

    @property
    def footnote(self) -> PixelBlock:
        """右下2x2。"""

        if self._footnote is None:

            self._footnote = PixelBlock(self.pix_array[-2:, -2:])

        return self._footnote

    ####### 亮度/数值计算 #######

    @property
    def mean(self) -> np.floating:
        return self.inner.mean

    @property
    def mean_value(self) -> np.floating:
        return self.inner.mean

    @property
    def value_percent(self) -> np.floating:
        return self.inner.percent

    @property
    def percent(self) -> np.floating:
        return self.inner.percent

    @property
    def value_decimal(self) -> np.floating:
        return self.inner.decimal

    @property
    def decimal(self) -> np.floating:
        return self.inner.decimal

    ####### 纯色判断 #######

    @property
    def is_pure(self) -> bool:
        return self.inner.is_pure

    @property
    def is_not_pure(self) -> bool:
        return self.inner.is_not_pure

    @property
    def is_black(self) -> bool:
        return self.inner.is_black

    @property
    def is_white(self) -> bool:
        return self.inner.is_white

    @property
    def color(self) -> tuple[int, int, int]:
        return self.inner.color

    @property
    def color_string(self) -> str:
        return self.inner.color_string

    ####### 白色数字识别 (定制字体)  #######

    @property
    def white_count(self) -> int:
        """根据白色像素数量解析的实际数值。

        映射关系基于定制字体的像素特征：
        - 0-9:  直接对应 (0-9 层) 
        - 10:   表示 0 层 (特殊映射) 
        - >=11: 表示 20 层 (上限值) 

        Returns:
            int: 解析的数值 (0, 1-9, 20) 
        """
        if self.inner.is_pure:
            return 0
        white_count = self.middle.white_count
        if white_count <= 9:
            return white_count
        if white_count == 10:
            return 0
        if white_count >= 11:
            return 20
        return 0

    @property
    def remaining(self) -> float:
        return self.inner.remaining

    ####### 哈希与标题 #######

    @property
    def hash(self) -> str:
        return self.middle.hash

    @property
    def title(self) -> str:
        """节点的可读标题。

        通过NodeTitleManager获取，支持：
        1. Hash直接匹配
        2. 余弦相似度匹配
        3. 返回hash (未匹配时) 
        """
        if Node._title_manager is not None:
            return Node._title_manager.get_title(
                middle_hash=self.middle.hash,
                middle_array=self.middle.array,
                full_array=self.full.array
            )
        return self.hash

    @property
    def footnote_title(self) -> str:
        if self.footnote.is_pure:
            return _ColorMap['IconType'].get(self.footnote.color_string, 'Unknown')
        return 'Unknown'

####### 数据提取器类 (原DataExtractor)  #######


class NodeExtractor:
    """像素数据提取引擎。
    除了基础的node节点外, 针对组合节点, 还有一些特殊的提取方法。
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
            x: 节点 X 坐标 (以 8px 为单位) 
            y: 节点 Y 坐标 (以 8px 为单位) 

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

    def read_health_bar(self, left: int, top: int, length: int) -> float:
        """读取白色进度条 (吸收盾/血量条) 。

        对应插件内的 CreateWhiteBar，统计指定区域内中间两行像素的
        白色像素占比来计算填充程度。

        Args:
            left:   起始节点 X 坐标
            top:    节点 Y 坐标
            length: 进度条长度 (节点数) 

        Returns:
            float: 白色像素占比 (0.0-1.0) 
        """
        # 收集所有节点的中间两行像素 (8x8 节点的第 3-4 行)
        nodes_middle_pix: list[np.ndarray] = [
            self.node(x, top).full.array[3:5, :]
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

        节点布局 (每个技能占 1 列 x 3 行) ：
        - top:     技能图标 (哈希识别) 
        - top+1:   为一个mix节点，包含冷却时间、可用状态、是否高亮、是否学会
        - top+2:   充能数 (白色数字识别) 

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

            # 跳过空槽位 (纯黑色)
            if icon_node.is_pure and icon_node.is_black:
                continue

            mix_node: Node = self.node(x, top + 1)
            charge_node: Node = self.node(x, top + 2)
            cooldown_block, usable_block, height_block, known_block = mix_node.mixNode

            spell = {
                'title': icon_node.title,
                'remaining': cooldown_block.remaining,
                'height': height_block.is_white,
                'charge': int(charge_node.white_count) if not (charge_node.is_pure and charge_node.is_black) else 0,
                'known': known_block.is_white,
                'usable': usable_block.is_white
            }

            result_sequence.append(spell)
            result_dict[icon_node.title] = spell

        return result_sequence, result_dict

    def read_aura_sequence(self, left: int, top: int, length: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """读取 Buff/Debuff 序列信息。

        对应插件内的 CreateAuraSequence，解析光环图标、剩余时间、类型、层数。

        节点布局 (每个光环占 1 列 x 4 行) ：
        - top:     图标 (哈希识别) 
        - top+1:   为一个mix节点，包含剩余时间、类型、是否永久buff、一个占空位
        - top+2:   充能数 (白色数字识别) 

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

            mix_node: Node = self.node(x, top + 1)
            count_node: Node = self.node(x, top + 2)
            remain_block, type_block, forever_block, _empty = mix_node.mixNode

            aura = {
                'title': icon_node.title,
                'remaining': 0.0 if remain_block.is_black else remain_block.remaining,
                'type': _ColorMap['IconType'].get(type_block.color_string, 'Unknown'),
                'count': count_node.white_count,
                'forever': forever_block.is_white
            }

            result_sequence.append(aura)
            result_dict[icon_node.title] = aura

        return result_sequence, result_dict
