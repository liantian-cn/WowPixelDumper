"""数据提取函数模块 - extract_all_data函数。"""

from datetime import datetime
from typing import Any

from Node import Node, NodeExtractor
from Utils import _ColorMap


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
        'player': {},
        'target': {},
        'focus': {},
        'party': {}
    }

    try:
        # 护甲类型标识（节点 26,6）
        data['misc']['ac'] = extractor.node(26, 6).title

        ####### 玩家状态 #######

        data['player']['aura'] = {
            # Buff: x=2..29 (28个)
            'buff': [],
            'buff_dict': {},
            # Debuff: x=30..36 (7个)
            'debuff': [],
            'debuff_dict': {}
        }

        data['player']['aura']['buff'], data['player']['aura']['buff_dict'] = \
            extractor.read_aura_sequence(left=2, top=2, length=28)

        data['player']['aura']['debuff'], data['player']['aura']['debuff_dict'] = \
            extractor.read_aura_sequence(left=30, top=2, length=7)

        # 技能序列: x=2..25, y=6 (24个)
        data['player']['spell_sequence'], data['player']['spell'] = \
            extractor.read_spell_sequence(left=2, top=6, length=24)

        # 玩家状态标志
        data['player']['status'] = {
            # 吸收盾进度条
            'damage_absorbs': extractor.read_health_bar(left=37, top=4, length=10) * 100,
            'heal_absorbs': extractor.read_health_bar(left=37, top=5, length=10) * 100,

            # 血量和能量（亮度百分比）
            'health': extractor.node(46, 2).value_percent,
            'power': extractor.node(46, 3).value_percent,

            # 布尔状态标志（白色=真）
            'in_combat': extractor.node(37, 2).is_white,
            'in_movement': extractor.node(38, 2).is_white,
            'in_vehicle': extractor.node(39, 2).is_white,
            'is_empowered': extractor.node(40, 2).is_white,

            # 施法信息
            'cast_icon': None,
            'cast_duration': None,

            # 引导技能信息
            'channel_icon': None,
            'channel_duration': None,

            # 职业和职责（颜色映射）
            'class': 'NONE',
            'role': 'NONE',

            # 死亡状态
            'deaded': extractor.node(39, 3).is_white
        }

        # 施法信息（节点 41-42, y=2）
        cast_icon_node: Node = extractor.node(41, 2)
        if cast_icon_node.is_not_pure:
            data['player']['status']['cast_icon'] = cast_icon_node.title
            data['player']['status']['cast_duration'] = extractor.node(42, 2).value_decimal

        # 引导技能信息（节点 43-44, y=2）
        channel_icon_node: Node = extractor.node(43, 2)
        if channel_icon_node.is_not_pure:
            data['player']['status']['channel_icon'] = channel_icon_node.title
            data['player']['status']['channel_duration'] = extractor.node(44, 2).value_decimal

        # 职业和职责（颜色映射）
        class_node: Node = extractor.node(37, 3)
        if class_node.is_pure:
            data['player']['status']['class'] = _ColorMap['Class'].get(class_node.color_string, 'NONE')

        role_node: Node = extractor.node(38, 3)
        if role_node.is_pure:
            data['player']['status']['role'] = _ColorMap['Role'].get(role_node.color_string, 'NONE')

        ####### 目标状态 #######

        data['target']['aura'] = {
            'debuff': [],
            'debuff_dict': {}
        }

        data['target']['status'] = {
            'exists': extractor.node(39, 6).is_white
        }

        if data['target']['status']['exists']:
            # 目标 Debuff: x=47..53, y=2 (7个)
            data['target']['aura']['debuff'], data['target']['aura']['debuff_dict'] = \
                extractor.read_aura_sequence(left=47, top=2, length=7)

            # 目标基本状态
            data['target']['status'].update({
                'can_attack': extractor.node(40, 6).is_white,
                'is_self': extractor.node(41, 6).is_white,
                'alive': extractor.node(42, 6).is_white,
                'in_combat': extractor.node(43, 6).is_white,
                'in_range': extractor.node(44, 6).is_white,
                'health': extractor.node(46, 6).value_percent,

                # 施法和引导信息
                'cast_icon': None,
                'cast_duration': None,
                'cast_interruptible': None,
                'channel_icon': None,
                'channel_duration': None,
                'channel_interruptible': None
            })

            # 目标施法信息（节点 39-41, y=7）
            target_cast_node: Node = extractor.node(39, 7)
            if target_cast_node.is_not_pure:
                data['target']['status']['cast_icon'] = target_cast_node.title
                data['target']['status']['cast_duration'] = extractor.node(40, 7).value_decimal
                data['target']['status']['cast_interruptible'] = extractor.node(41, 7).is_white

            # 目标引导技能信息（节点 42-44, y=7）
            target_channel_node: Node = extractor.node(42, 7)
            if target_channel_node.is_not_pure:
                data['target']['status']['channel_icon'] = target_channel_node.title
                data['target']['status']['channel_duration'] = extractor.node(43, 7).value_decimal
                data['target']['status']['channel_interruptible'] = extractor.node(44, 7).is_white

        ####### Focus 状态 #######

        data['focus']['aura'] = {
            'debuff': [],
            'debuff_dict': {}
        }

        data['focus']['status'] = {
            'exists': extractor.node(39, 8).is_white
        }

        if data['focus']['status']['exists']:
            # Focus Debuff: x=47..53, y=6 (7个)
            data['focus']['aura']['debuff'], data['focus']['aura']['debuff_dict'] = \
                extractor.read_aura_sequence(left=47, top=6, length=7)

            data['focus']['status'].update({
                'can_attack': extractor.node(40, 8).is_white,
                'is_self': extractor.node(41, 8).is_white,
                'alive': extractor.node(42, 8).is_white,
                'in_combat': extractor.node(43, 8).is_white,
                'in_range': extractor.node(44, 8).is_white,
                'health': extractor.node(46, 8).value_percent,

                'cast_icon': None,
                'cast_duration': None,
                'cast_interruptible': None,
                'channel_icon': None,
                'channel_duration': None,
                'channel_interruptible': None
            })

            # Focus 施法信息（节点 39-41, y=9）
            focus_cast_node: Node = extractor.node(39, 9)
            if focus_cast_node.is_not_pure:
                data['focus']['status']['cast_icon'] = focus_cast_node.title
                data['focus']['status']['cast_duration'] = extractor.node(40, 9).value_decimal
                data['focus']['status']['cast_interruptible'] = extractor.node(41, 9).is_white

            # Focus 引导技能信息（节点 42-44, y=9）
            focus_channel_node: Node = extractor.node(42, 9)
            if focus_channel_node.is_not_pure:
                data['focus']['status']['channel_icon'] = focus_channel_node.title
                data['focus']['status']['channel_duration'] = extractor.node(43, 9).value_decimal
                data['focus']['status']['channel_interruptible'] = extractor.node(44, 9).is_white

        ####### 队伍状态（4个队友） #######

        for i in range(1, 5):
            party_key: str = f'party{i}'
            data['party'][party_key] = {
                'exists': False,
                'status': {},
                'aura': {}
            }

            # 队友存在标志（节点 13*i-1, y=14）
            party_exist: bool = extractor.node(13 * i - 1, 14).is_white
            data['party'][party_key]['exists'] = party_exist

            if party_exist:
                # 队友基础状态
                data['party'][party_key]['status'] = {
                    'in_range': extractor.node(13 * i, 14).is_white,
                    'health': extractor.node(13 * i + 1, 14).value_percent,
                    'selectd': extractor.node(13 * i + 1, 15).is_white,

                    # 吸收盾
                    'damage_absorbs': extractor.read_health_bar(left=13*i - 11, top=14, length=10) * 100,
                    'heal_absorbs': extractor.read_health_bar(left=13*i - 11, top=15, length=10) * 100
                }

                # 职业和职责
                party_class_node: Node = extractor.node(13 * i - 1, 15)
                data['party'][party_key]['status']['class'] = (
                    _ColorMap['Class'].get(party_class_node.color_string, 'NONE')
                    if party_class_node.is_pure else 'NONE'
                )

                party_role_node: Node = extractor.node(13 * i, 15)
                data['party'][party_key]['status']['role'] = (
                    _ColorMap['Role'].get(party_role_node.color_string, 'NONE')
                    if party_role_node.is_pure else 'NONE'
                )

                # 队友光环
                data['party'][party_key]['aura'] = {
                    # Buff: 7个
                    'buff': [],
                    'buff_dict': {},
                    # Debuff: 6个
                    'debuff': [],
                    'debuff_dict': {}
                }

                data['party'][party_key]['aura']['buff'], data['party'][party_key]['aura']['buff_dict'] = \
                    extractor.read_aura_sequence(left=13*i - 11, top=10, length=7)

                data['party'][party_key]['aura']['debuff'], data['party'][party_key]['aura']['debuff_dict'] = \
                    extractor.read_aura_sequence(left=13*i - 4, top=10, length=6)

    except Exception as e:
        import traceback
        print(f'[extract_all_data] 发生错误:\\n{traceback.format_exc()}')
        data['error'] = f'数据提取失败: {str(e)}'

    return data
