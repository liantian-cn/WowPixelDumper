import json
from typing import List, Tuple
from datetime import datetime

import xxhash
import cv2
import numpy as np
from PIL import Image


ColorMap = {"BuffType": {}}

HashMap = {}


def load_hashmap() -> None:
    global HashMap
    with open("HashMap.json", "r", encoding="utf-8") as f:
        HashMap = json.load(f)
    if "Used" in HashMap:
        del HashMap["Used"]

    user_select_list = []
    for key in HashMap:
        if not key in ["Universal", "Used", "UserInput"]:
            user_select_list.append(key)

    HashMap["Used"] = {}

    HashMap["Used"].update(HashMap["Universal"])
    if "UserInput" in HashMap:
        HashMap["Used"].update(HashMap["UserInput"])
    return HashMap["Used"]


def load_colormap() -> None:
    global ColorMap
    with open("ColorMap.json", "r", encoding="utf-8") as f:
        ColorMap.update(json.load(f))


load_hashmap()
load_colormap()


def save_user_input_hash(hash_str, title) -> None:
    global HashMap
    if not "UserInput" in HashMap:
        HashMap["UserInput"] = {}
    HashMap["UserInput"][hash_str] = title
    HashMap["Used"][hash_str] = title
    with open("HashMap.json", "w", encoding="utf-8") as f:
        json.dump(HashMap, f, ensure_ascii=False, indent=4)


def hashstr_used(hash_str: str) -> bool:
    return hash_str in HashMap["Used"]


def load_template(template_path: str) -> np.ndarray:
    """加载标记模板图片并转换为 numpy array

    Args:
        template_path (str): 标记图片的路径

    Returns:
        numpy.ndarray: 标记图片的 RGB 格式 numpy array，形状为 (height, width, 3)
    """
    # 使用 PIL 读取图片
    img = Image.open(template_path)

    # 转换为 RGB 格式（如果原图是 RGBA 或其他格式）
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 转换为 numpy array
    template_array = np.array(img)
    return template_array


def screenshot_to_array(screenshot: Image.Image) -> np.ndarray:
    """将 PIL 截图对象转换为 numpy array

    Args:
        screenshot (PIL.Image): 截图对象

    Returns:
        numpy.ndarray: 截图的 RGB 格式 numpy array，形状为 (height, width, 3)
    """
    # 转换为 RGB 格式
    if screenshot.mode != "RGB":
        screenshot = screenshot.convert("RGB")

    # 转换为 numpy array
    screenshot_array = np.array(screenshot)

    return screenshot_array


def find_all_matches(
    screenshot_array: np.ndarray, template_array: np.ndarray, threshold: float = 0.999
) -> List[Tuple[int, int]]:
    """在截图中查找所有标记模板的位置

    Args:
        screenshot_array (numpy.ndarray): 截图的 numpy array，形状为 (height, width, 3)
        template_array (numpy.ndarray): 标记模板的 numpy array，形状为 (template_height, template_width, 3)
        threshold (float): 匹配阈值，范围 0-1，默认 0.999

    Returns:
        list: 所有匹配位置的坐标列表，每个坐标格式为 (x, y)，表示标记左上角的位置
    """
    # 获取模板的宽高
    template_height, template_width = template_array.shape[:2]

    # 获取截图的宽高
    screenshot_height, screenshot_width = screenshot_array.shape[:2]

    # 如果模板比截图大，直接返回空列表
    if template_height > screenshot_height or template_width > screenshot_width:
        return []

    # 使用 OpenCV 的模板匹配方法
    # TM_CCOEFF_NORMED 方法返回 -1 到 1 之间的值，1 表示完美匹配
    result = cv2.matchTemplate(
        screenshot_array, template_array, cv2.TM_CCOEFF_NORMED)

    # 找到所有匹配位置（值大于等于阈值）
    match_locations = np.where(result >= threshold)

    # 将匹配位置转换为坐标列表
    matches = []
    for y, x in zip(match_locations[0], match_locations[1]):
        matches.append((x, y))

    # 按坐标排序（先按 x，再按 y）
    matches.sort()

    return matches


def find_template_bounds(
    screenshot_array: np.ndarray, template_path: str, threshold: float = 0.999
) -> Tuple[int, int, int, int]:
    """根据模板文件在画面中寻找区域并返回标记构成的矩形边界

    Args:
        screenshot_array (numpy.ndarray): 截图的 numpy array，形状为 (height, width, 3)，RGB格式
        template_path (str): 标记图片的路径
        threshold (float): 匹配阈值，范围 0-1，默认 0.999

    Returns:
        tuple: 矩形边界 (left, top, right, bottom)，表示左上角和右下角坐标

    Raises:
        ValueError: 当找到的标记数量不是 2 个时
    """
    # 加载模板
    template_array = load_template(template_path)
    template_height, template_width = template_array.shape[:2]

    # 直接使用传入的 numpy array，无需转换
    # 查找所有匹配
    matches = find_all_matches(screenshot_array, template_array, threshold)

    # 检查匹配数量
    if len(matches) != 2:
        raise ValueError(f"需要找到 2 个标记，但找到 {len(matches)} 个")

    # 计算两个标记的边界
    x1, y1 = matches[0]
    x2, y2 = matches[1]

    # 计算标记的右下角坐标
    right1 = x1 + template_width
    bottom1 = y1 + template_height
    right2 = x2 + template_width
    bottom2 = y2 + template_height

    # 计算整体矩形的边界
    left = int(min(x1, x2))
    top = int(min(y1, y2))
    right = int(max(right1, right2))
    bottom = int(max(bottom1, bottom2))

    # 计算边界尺寸
    width = right - left
    height = bottom - top

    # 检查尺寸是否为6的倍数
    if width % 6 != 0 or height % 6 != 0:
        raise ValueError(f"边界尺寸必须是6的倍数，但得到 {width} x {height}")

    return (left, top, right, bottom)


class Node:
    def __init__(self, x: int, y: int, img_array: np.ndarray) -> None:
        self.x = x
        self.y = y
        self.pix_array = img_array
        self._hash_cache = None

    @property
    def full(self) -> np.ndarray:
        """完整节点 6x6，用于直接截取区域"""
        return self.pix_array

    @property
    def middle(self) -> np.ndarray:
        """左上5x5区域，用于纯色判断/取色/哈希/白字识别"""
        return self.pix_array[0:5, 0:5]

    @property
    def inner(self) -> np.ndarray:
        """中间3x3区域，用于计算平均亮度（value值）"""
        return self.pix_array[1:4, 1:4]

    @property
    def mean_value(self) -> np.floating:
        return np.mean(self.inner)

    @property
    def value_percent(self) -> np.floating:
        return self.mean_value / 255.0 * 100

    @property
    def value_decimal(self) -> np.floating:
        return self.mean_value / 255.0

    @property
    def is_pure(self) -> bool:
        first_pixel = self.middle[0, 0]
        return bool(np.all(self.middle == first_pixel))

    @property
    def is_not_pure(self) -> bool:
        return not self.is_pure

    @property
    def color(self) -> Tuple[int, int, int]:
        if self.is_pure:
            return tuple(self.middle[0, 0])
        raise ValueError("非纯色节点没有颜色")

    @property
    def white_count_raw(self) -> int:
        # 计算middle(5x5)区域中白色像素的数量，用于数字识别
        return int(np.count_nonzero(np.all(self.middle == (255, 255, 255), axis=2)))

    @property
    def count(self) -> int:
        # 根据定制字体转化后的白色像素数量计算实际值
        if self.is_pure:
            return 0
        if self.white_count_raw <= 9:
            return self.white_count_raw
        if self.white_count_raw == 10:
            return 0
        if self.white_count_raw >= 11:
            return 20
        return 0

    @property
    def color_string(self) -> str:
        return f"{self.color[0]},{self.color[1]},{self.color[2]}"

    @property
    def is_black(self) -> bool:
        return self.is_pure and (self.color == (0, 0, 0))

    @property
    def is_white(self) -> bool:
        return self.is_pure and (self.color == (255, 255, 255))

    @property
    def remaining(self) -> float:
        """
        当游戏内使用remaining_curve时，这个像素块代表的时间。
        """
        y = int(self.mean_value)

        points = [(0.0, 0), (5.0, 100), (30.0, 150),
                  (155.0, 200), (375.0, 255)]
        # 边界情况处理
        if y <= points[0][1]:
            return points[0][0]
        if y >= points[-1][1]:
            return points[-1][0]
        # 线性插值查找
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            if y1 <= y <= y2:
                return x1 + (x2 - x1) * (y - y1) / (y2 - y1)
        return 0.0

    @property
    def hash(self) -> str:
        if self._hash_cache is None:
            self._hash_cache = xxhash.xxh3_64_hexdigest(
                np.ascontiguousarray(self.middle), seed=0
            )
        return self._hash_cache

    @property
    def title(self) -> str:
        # 尝试从HashMap["Used"]中获取标题，否则返回hash值
        if self.hash in HashMap["Used"]:
            return HashMap["Used"][self.hash]
        return self.hash

    def show(self) -> None:
        """
        用画图程序显示当前node的像素块
        """
        inner_img = Image.fromarray(self.middle)
        inner_img.show()


class PixelDumper:
    def __init__(self, img_array: np.ndarray) -> None:
        self.pix_array = img_array

    def node(self, x: int, y: int) -> Node:
        start_x = x * 6
        start_y = y * 6
        end_x = start_x + 6
        end_y = start_y + 6

        if x >= self.pix_array.shape[1] // 6 or y >= self.pix_array.shape[0] // 6:
            raise ValueError(f"node索引 ({x},{y}) 超出范围")

        array = self.pix_array[start_y:end_y, start_x:end_x]

        node = Node(x, y, array)
        return node

    def read_health_bar(self, left: int, top: int, length: int) -> float:
        """
        对应插件内的CreateWhiteBar，读取区域内的计时条信息
        方法，统计范围内所有色块(node)中第3和第4行(6x6节点中间2行)的白色像素占比
        """
        # 先取出所有node的中间2行像素
        nodes_middle_pix = [self.node(x, top).full[2:4, :] for x in range(left, left + length)]
        # 统计第五行和第六行的白色像素数量
        white_count = sum(np.count_nonzero(np.all(node == (255, 255, 255), axis=2)) for node in nodes_middle_pix)
        # 计算总像素数：动态计算每个node的像素数，避免硬编码
        # 对于每个node，计算其高度×宽度（不包括颜色通道维度）
        total_count = sum(node.shape[0] * node.shape[1] for node in nodes_middle_pix)
        # 计算结果
        result = white_count / total_count
        return result

    def read_spell_sequence(self, left: int, top: int, length: int) -> Tuple[list[dict], dict[str, dict]]:
        """
        对应插件内的SpellFrame，读取区域内的技能冷却信息

        """
        result_sequence = []
        result_dict = {}

        for x in range(left, left + length):
            icon_node = self.node(x, top)
            if icon_node.is_pure and icon_node.is_black:
                # 如果是纯色，且是黑色，跳过
                continue
            remain_node = self.node(x, top + 1)
            height_node = self.node(x, top + 2)
            charge_node = self.node(x, top + 3)
            spell_title = icon_node.title
            if not remain_node.is_black:
                spell_remaining = remain_node.remaining
            else:
                spell_remaining = 0
            if not height_node.is_white:
                spell_height = True
            else:
                spell_height = False

            if charge_node.is_pure and charge_node.is_black:
                spell_charge = None
            else:
                spell_charge = charge_node.count

            result_sequence.append(
                {
                    "title": spell_title,
                    "remaining": spell_remaining,
                    "height": spell_height,
                    "charge": spell_charge,
                }
            )
            result_dict[spell_title] = {
                "remaining": spell_remaining,
                "height": spell_height,
                "charge": spell_charge,
            }

        return result_sequence, result_dict

    def read_aura_sequence(self, left: int, top: int, length: int) -> Tuple[list[dict], dict[str, dict]]:
        """
        对应插件内的CreateAuraSequence函数，读取区域内的Buff/Debuff信息

        """
        result_sequence = []
        result_dict = {}
        for x in range(left, left + length):
            icon_node = self.node(x, top)
            if icon_node.is_pure and icon_node.is_black:
                # 如果是纯色，且是黑色，跳过
                continue
            remain_node = self.node(x, top + 1)
            type_node = self.node(x, top + 2)
            count_node = self.node(x, top + 3)

            aura_title = icon_node.title
            if not remain_node.is_black:
                aura_remaining = remain_node.remaining
            else:
                aura_remaining = None
            if type_node.is_pure and type_node.color_string in ColorMap["BuffType"]:
                aura_type = ColorMap["BuffType"][type_node.color_string]
            else:
                aura_type = "Unknown"

            result_sequence.append(
                {
                    "title": aura_title,
                    "remaining": aura_remaining,
                    "type": aura_type,
                    "count": count_node.count,
                }
            )
            result_dict[aura_title] = {
                "remaining": aura_remaining,
                "type": aura_type,
                "count": count_node.count,
            }

        return result_sequence, result_dict

    def dump_all(self) -> dict:
        data = {}
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["misc"] = {}
        data["misc"]["ac"] = self.node(26, 6).title

        data["spec"] = {}
        data["player"] = {}
        data["target"] = {}
        data["focus"] = {}
        data["player"]["aura"] = {}
        data["target"]["aura"] = {}
        data["focus"]["aura"] = {}

        data["player"]["aura"]["buff"], data["player"]["aura"]["buff_dict"] = self.read_aura_sequence(left=2, top=2, length=28)
        data["player"]["aura"]["debuff"], data["player"]["aura"]["debuff_dict"] = self.read_aura_sequence(left=30, top=2, length=7)
        data["target"]["aura"]["debuff"], data["target"]["aura"]["debuff_dict"] = self.read_aura_sequence(left=47, top=2, length=7)
        data["focus"]["aura"]["debuff"], data["focus"]["aura"]["debuff_dict"] = self.read_aura_sequence(left=47, top=6, length=7)
        #
        data["player"]["spell_sequence"], data["player"]["spell"] = self.read_spell_sequence(left=2, top=6, length=24)
        # 读取伤害吸收和治疗吸收
        data["player"]["status"] = {}
        data["player"]["status"]["damage_absorbs"] = self.read_health_bar(left=37, top=4, length=10) * 100
        data["player"]["status"]["heal_absorbs"] = self.read_health_bar(left=37, top=5, length=10) * 100
        data["player"]["status"]["health"] = self.node(46, 2).value_percent
        data["player"]["status"]["power"] = self.node(46, 3).value_percent

        data["player"]["status"]["in_combat"] = self.node(37, 2).is_white
        data["player"]["status"]["in_movement"] = self.node(38, 2).is_white
        data["player"]["status"]["in_vehicle"] = self.node(39, 2).is_white
        data["player"]["status"]["is_empowered"] = self.node(40, 2).is_white

        data["player"]["status"]["cast_icon"] = None
        data["player"]["status"]["cast_duration"] = None
        if self.node(41, 2).is_not_pure:
            data["player"]["status"]["cast_icon"] = self.node(41, 2).title
            data["player"]["status"]["cast_duration"] = self.node(42, 2).value_percent

        data["player"]["status"]["channel_icon"] = None
        data["player"]["status"]["channel_duration"] = None
        if self.node(43, 2).is_not_pure:
            data["player"]["status"]["channel_icon"] = self.node(43, 2).title
            data["player"]["status"]["channel_duration"] = self.node(44, 2).value_percent
        if self.node(37, 3).is_pure:
            data["player"]["status"]["class"] = ColorMap["Class"].get(self.node(37, 3).color_string, "NONE")
        if self.node(38, 3).is_pure:
            data["player"]["status"]["role"] = ColorMap["Role"].get(self.node(38, 3).color_string, "NONE")

        data["player"]["status"]["deaded"] = self.node(39, 3).is_white

        data["target"]["status"] = {}
        data["target"]["status"]["exists"] = self.node(39, 6).is_white
        if data["target"]["status"]["exists"]:
            data["target"]["status"]["can_attack"] = self.node(40, 6).is_white
            data["target"]["status"]["is_self"] = self.node(41, 6).is_white
            data["target"]["status"]["alive"] = self.node(42, 6).is_white
            data["target"]["status"]["in_combat"] = self.node(43, 6).is_white
            data["target"]["status"]["in_range"] = self.node(44, 6).is_white
            data["target"]["status"]["health"] = self.node(46, 6).value_percent

            data["target"]["status"]["cast_icon"] = None
            data["target"]["status"]["cast_duration"] = None
            data["target"]["status"]["cast_interruptible"] = None
            if self.node(39, 7).is_not_pure:
                data["target"]["status"]["cast_icon"] = self.node(39, 7).title
                data["target"]["status"]["cast_duration"] = self.node(40, 7).value_percent
                data["target"]["status"]["cast_interruptible"] = self.node(41, 7).is_white

            data["target"]["status"]["channel_icon"] = None
            data["target"]["status"]["channel_duration"] = None
            data["target"]["status"]["channel_interruptible"] = None
            if self.node(42, 7).is_not_pure:
                data["target"]["status"]["channel_icon"] = self.node(42, 7).title
                data["target"]["status"]["channel_duration"] = self.node(43, 7).value_percent
                data["target"]["status"]["channel_interruptible"] = self.node(44, 7).is_white
        data["focus"]["status"] = {}
        data["focus"]["status"]["exists"] = self.node(39, 8).is_white
        if data["focus"]["status"]["exists"]:
            data["focus"]["status"]["can_attack"] = self.node(40, 8).is_white
            data["focus"]["status"]["is_self"] = self.node(41, 8).is_white
            data["focus"]["status"]["alive"] = self.node(42, 8).is_white
            data["focus"]["status"]["in_combat"] = self.node(43, 8).is_white
            data["focus"]["status"]["in_range"] = self.node(44, 8).is_white
            data["focus"]["status"]["health"] = self.node(46, 8).value_percent

            data["focus"]["status"]["cast_icon"] = None
            data["focus"]["status"]["cast_duration"] = None
            data["focus"]["status"]["cast_interruptible"] = None
            if self.node(39, 9).is_not_pure:
                data["focus"]["status"]["cast_icon"] = self.node(39, 9).title
                data["focus"]["status"]["cast_duration"] = self.node(40, 9).value_percent
                data["focus"]["status"]["cast_interruptible"] = self.node(41, 9).is_white

            data["focus"]["status"]["channel_icon"] = None
            data["focus"]["status"]["channel_duration"] = None
            data["focus"]["status"]["channel_interruptible"] = None
            if self.node(42, 9).is_not_pure:
                data["focus"]["status"]["channel_icon"] = self.node(42, 9).title
                data["focus"]["status"]["channel_duration"] = self.node(43, 9).value_percent
                data["focus"]["status"]["channel_interruptible"] = self.node(44, 9).is_white
        data["party"] = {}
        for i in range(1, 5):
            data["party"][f"party{i}"] = {}
            party_exist = self.node(13*i-1, 14).is_white

            data["party"][f"party{i}"]["exists"] = party_exist
            if party_exist:
                data["party"][f"party{i}"]["status"] = {}
                data["party"][f"party{i}"]["aura"] = {}
                data["party"][f"party{i}"]["status"]["in_range"] = self.node(13*i, 14).is_white
                data["party"][f"party{i}"]["status"]["health"] = self.node(13*i+1, 14).value_percent
                class_node = self.node(13*i-1, 15)
                data["party"][f"party{i}"]["status"]["class"] = ColorMap["Class"].get(class_node.color_string, "NONE") if class_node.is_pure else "NONE"
                role_node = self.node(13*i, 15)
                data["party"][f"party{i}"]["status"]["role"] = ColorMap["Role"].get(role_node.color_string, "NONE") if role_node.is_pure else "NONE"
                data["party"][f"party{i}"]["status"]["selectd"] = self.node(13*i+1, 15).is_white
                data["party"][f"party{i}"]["status"]["damage_absorbs"] = self.read_health_bar(left=13*i+-11, top=14, length=10) * 100
                data["party"][f"party{i}"]["status"]["heal_absorbs"] = self.read_health_bar(left=13*i+-11, top=15, length=10) * 100

                data["party"][f"party{i}"]["aura"]["buff"], data["party"][f"party{i}"]["aura"]["buff_dict"] = self.read_aura_sequence(left=13*i+-11, top=10, length=7)
                data["party"][f"party{i}"]["aura"]["debuff"], data["party"][f"party{i}"]["aura"]["debuff_dict"] = self.read_aura_sequence(left=13*i+-4, top=10, length=6)

        return data
