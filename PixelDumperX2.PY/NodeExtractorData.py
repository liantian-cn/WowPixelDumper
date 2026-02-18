"""数据提取函数模块 - extract_all_data函数。"""

from datetime import datetime
from typing import Any

from Node import Node, NodeExtractor
from Utils import _ColorMap


def read_std_node(node: Node) -> dict[str, Any]:
    """读取标准节点数据。"""
    if node.is_pure:
        return {
            'is_pure': True,
            'title': None,
            'color_string': node.color_string,
            'is_white': node.is_white,
            'percent': node.percent,
            'mean': node.mean,
            "decimal": node.decimal

        }
    else:
        return {
            'is_pure': False,
            'title': node.title,
            'hash': node.hash
        }


####### 数据提取主函数 #######

def extract_all_data(extractor: NodeExtractor) -> dict[str, Any]:
    """提取完整的游戏状态数据。

    按照插件约定的数据布局，从像素区域解析所有游戏状态信息，
    包括玩家、目标、Focus、队伍等所有数据。

    Args:
        extractor: NodeExtractor实例

    Returns:
        dict: 完整的游戏状态数据结构
    """
    data: dict[str, Any] = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'misc': {},
        'spec': {},
        'player': {'unitToken': "player"},
        'target': {'unitToken': "target"},
        'focus': {'unitToken': "focus"},
        'party': {},
        'signal': {}
    }

    try:
        # 护甲类型标识（节点 26,6）
        data['misc']['ac'] = extractor.node(34, 5).title
        data['misc']['on_chat'] = extractor.node(35, 5).is_white
        data['misc']['is_targeting'] = extractor.node(36, 5).is_white
        data['misc']['flash_node'] = extractor.node(37, 5).color_string

        ####### 玩家状态 #######

        data['player']['aura'] = {
            'buff_sequence': [],
            'buff': {},
            'debuff_sequence': [],
            'debuff': {}
        }

        data['player']['aura']['buff_sequence'], data['player']['aura']['buff'] = extractor.read_aura_sequence(left=2, top=5, length=32)

        data['player']['aura']['debuff_sequence'], data['player']['aura']['debuff'] = extractor.read_aura_sequence(left=2, top=8, length=8)

        # 技能序列
        data['player']['spell_sequence'], data['player']['spell'] = extractor.read_spell_sequence(left=2, top=2, length=36)

        # 玩家状态标志
        data['player']['status'] = {
            # 吸收盾进度条
            'unit_damage_absorbs': extractor.read_health_bar(left=38, top=2, length=8) * 100,
            'unit_heal_absorbs': extractor.read_health_bar(left=38, top=3, length=8) * 100,

            # 血量和能量（亮度百分比）
            'unit_health': extractor.node(45, 4).percent,
            'unit_power': extractor.node(45, 5).percent,

            # 布尔状态标志（白色=真）
            'unit_in_combat': extractor.node(38, 4).is_white,
            'unit_in_movement': extractor.node(39, 4).is_white,
            'unit_in_vehicle': extractor.node(40, 4).is_white,
            'unit_is_empowering': extractor.node(41, 4).is_white,

            # 施法信息
            'unit_cast_icon': None,
            'unit_cast_duration': None,

            # 引导技能信息
            'unit_channel_icon': None,
            'unit_channel_duration': None,

            # 职业和职责（颜色映射）
            'unit_class': 'NONE',
            'unit_role': 'NONE',

            # 死亡状态
            'unit_is_dead_or_ghost': extractor.node(40, 5).is_white,
            'unit_in_range': True  # 玩家总是在距离内，这条是方便计算小队状态。
        }

        # 施法信息
        cast_icon_node: Node = extractor.node(42, 4)
        if cast_icon_node.is_not_pure:
            data['player']['status']['unit_cast_icon'] = cast_icon_node.title
            data['player']['status']['unit_cast_duration'] = extractor.node(43, 4).percent

        # 引导技能信息
        channel_icon_node: Node = extractor.node(42, 5)
        if channel_icon_node.is_not_pure:
            data['player']['status']['unit_channel_icon'] = channel_icon_node.title
            data['player']['status']['unit_channel_duration'] = extractor.node(43, 5).percent

        # 职业和职责（颜色映射）
        class_node: Node = extractor.node(38, 5)
        if class_node.is_pure:
            data['player']['status']['unit_class'] = _ColorMap['Class'].get(class_node.color_string, 'NONE')

        role_node: Node = extractor.node(39, 5)
        if role_node.is_pure:
            data['player']['status']['unit_role'] = _ColorMap['Role'].get(role_node.color_string, 'NONE')

        # ####### 目标状态 #######

        data['target']['aura'] = {
            'debuff_sequence': [],
            'debuff': {}
        }

        data['target']['status'] = {
            'exists': extractor.node(38, 6).is_white
        }

        if data['target']['status']['exists']:
            # 目标 Debuff: x=47..53, y=2 (7个)
            data['target']['aura']['debuff_sequence'], data['target']['aura']['debuff'] = extractor.read_aura_sequence(left=10, top=8, length=16)

            # 目标基本状态
            data['target']['status'].update({
                'unit_can_attack': extractor.node(39, 6).is_white,
                'unit_is_self': extractor.node(40, 6).is_white,
                'unit_is_alive': extractor.node(41, 6).is_white,
                'unit_in_combat': extractor.node(42, 6).is_white,
                'unit_in_range': extractor.node(43, 6).is_white,
                'unit_health': extractor.node(45, 6).percent,

                # 施法和引导信息
                'unit_cast_icon': None,
                'unit_cast_duration': None,
                'unit_cast_interruptible': None,
                'unit_channel_icon': None,
                'unit_channel_duration': None,
                'unit_channel_interruptible': None
            })

            # 目标施法信息（节点 39-41, y=7）
            target_cast_node: Node = extractor.node(38, 7)
            if target_cast_node.is_not_pure:
                data['target']['status']['unit_cast_icon'] = target_cast_node.title
                data['target']['status']['unit_cast_duration'] = extractor.node(39, 7).percent
                data['target']['status']['unit_cast_interruptible'] = extractor.node(40, 7).is_white

            # 目标引导技能信息（节点 42-44, y=7）
            target_channel_node: Node = extractor.node(41, 7)
            if target_channel_node.is_not_pure:
                data['target']['status']['channel_icon'] = target_channel_node.title
                data['target']['status']['channel_duration'] = extractor.node(42, 7).percent
                data['target']['status']['unit_channel_interruptible'] = extractor.node(43, 7).is_white

        # ####### Focus 状态 #######

        data['focus']['aura'] = {
            'debuff_sequence': [],
            'debuff': {}
        }

        data['focus']['status'] = {
            'exists': extractor.node(38, 8).is_white
        }

        if data['focus']['status']['exists']:

            data['focus']['aura']['debuff_sequence'], data['focus']['aura']['debuff'] = extractor.read_aura_sequence(left=26, top=8, length=8)

            data['focus']['status'].update({
                'unit_can_attack': extractor.node(39, 8).is_white,
                'unit_is_self': extractor.node(40, 8).is_white,
                'unit_is_alive': extractor.node(41, 8).is_white,
                'unit_in_combat': extractor.node(42, 8).is_white,
                'unit_in_range': extractor.node(43, 8).is_white,
                'unit_health': extractor.node(45, 8).percent,

                'unit_cast_icon': None,
                'unit_cast_duration': None,
                'unit_cast_interruptible': None,
                'unit_channel_icon': None,
                'unit_channel_duration': None,
                'unit_channel_interruptible': None
            })

            focus_cast_node: Node = extractor.node(38, 9)
            if focus_cast_node.is_not_pure:
                data['focus']['status']['unit_cast_icon'] = focus_cast_node.title
                data['focus']['status']['unit_cast_duration'] = extractor.node(39, 9).percent
                data['focus']['status']['unit_cast_interruptible'] = extractor.node(40, 9).is_white

            focus_channel_node: Node = extractor.node(41, 9)
            if focus_channel_node.is_not_pure:
                data['focus']['status']['unit_channel_icon'] = focus_channel_node.title
                data['focus']['status']['unit_channel_duration'] = extractor.node(42, 9).percent
                data['focus']['status']['unit_channel_interruptible'] = extractor.node(43, 9).is_white

        # ####### 队伍状态（4个队友） #######

        for i in range(1, 5):
            party_key: str = f'party{i}'
            data['party'][party_key] = {
                'exists': False,
                'unitToken': party_key,
                'status': {},
                'aura': {}
            }

            party_exist: bool = extractor.node(12 * i - 2, 14).is_white
            data['party'][party_key]['exists'] = party_exist

            if party_exist:
                # 队友基础状态
                data['party'][party_key]['status'] = {
                    'unit_in_range': extractor.node(12 * i - 1, 14).is_white,
                    'unit_health': extractor.node(12 * i, 14).percent,
                    'selectd': extractor.node(12 * i, 15).is_white,

                    # 吸收盾
                    'unit_damage_absorbs': extractor.read_health_bar(left=12*i - 10, top=14, length=8) * 100,
                    'unit_heal_absorbs': extractor.read_health_bar(left=12*i - 10, top=15, length=8) * 100
                }

                # 职业和职责
                party_class_node: Node = extractor.node(12 * i - 2, 15)
                data['party'][party_key]['status']['unit_class'] = (
                    _ColorMap['Class'].get(party_class_node.color_string, 'NONE')
                    if party_class_node.is_pure else 'NONE'
                )

                party_role_node: Node = extractor.node(12 * i - 1, 15)
                data['party'][party_key]['status']['unit_role'] = (
                    _ColorMap['Role'].get(party_role_node.color_string, 'NONE')
                    if party_role_node.is_pure else 'NONE'
                )

                # 队友光环
                data['party'][party_key]['aura'] = {
                    'buff_sequence': [],
                    'buff': {},
                    'debuff_sequence': [],
                    'debuff': {}
                }

                data['party'][party_key]['aura']['buff_sequence'], data['party'][party_key]['aura']['buff'] = extractor.read_aura_sequence(left=12*i - 4, top=11, length=6)
                data['party'][party_key]['aura']['debuff_sequence'], data['party'][party_key]['aura']['debuff'] = extractor.read_aura_sequence(left=12*i - 10, top=11, length=6)
        # 信号

        singal_nodes = [extractor.node(x, 10) for x in range(38, 46)]
        data["signal"] = {i: read_std_node(node) for i, node in enumerate(singal_nodes, start=1)}
        spec_nodes = [extractor.node(x, y) for x in range(34, 38) for y in range(8, 11)]
        data["spec"] = {i: read_std_node(node) for i, node in enumerate(spec_nodes, start=1)}

    except Exception as e:
        import traceback
        print(f'[extract_all_data] 发生错误:\\n{traceback.format_exc()}')
        data['error'] = f'数据提取失败: {str(e)}'

    return data
