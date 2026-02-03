
from rich import print
"""data 格式范例
{
        "timestamp": "2026-02-02 23:35:49",
        "misc": {
                "ac": "暗言术：痛"
        },
        "spec": {},
        "player": {
                "aura": {
                        "buff": [
                                {
                                        "title": "真言术：盾",
                                        "remaining": 12.5,
                                        "type": "MAGIC",
                                        "count": 0
                                },
                                {
                                        "title": "真言术：韧",
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0
                                },
                                {
                                        "title": "神圣庇护",
                                        "remaining": 5.5,
                                        "type": "NONE",
                                        "count": 0
                                },
                                {
                                        "title": "救赎",
                                        "remaining": 11.5,
                                        "type": "NONE",
                                        "count": 0
                                },
                                {
                                        "title": "911f684c98c1155e",
                                        "remaining": 375.0,
                                        "type": "NONE",
                                        "count": 0
                                },
                                {
                                        "title": "ee0cb68e7b26fb10",
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                },
                                {
                                        "title": "09234c9073840e62",
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                },
                                {
                                        "title": "1a6c2eab036f33ca",
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                },
                                {
                                        "title": "67a15142f8dcbf5d",
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0
                                },
                                {
                                        "title": "3d73eeae238b9f1e",
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                }
                        ],
                        "buff_dict": {
                                "真言术：盾": {
                                        "remaining": 12.5,
                                        "type": "MAGIC",
                                        "count": 0
                                },
                                "真言术：韧": {
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0
                                },
                                "神圣庇护": {
                                        "remaining": 5.5,
                                        "type": "NONE",
                                        "count": 0
                                },
                                "救赎": {
                                        "remaining": 11.5,
                                        "type": "NONE",
                                        "count": 0
                                },
                                "911f684c98c1155e": {
                                        "remaining": 375.0,
                                        "type": "NONE",
                                        "count": 0
                                },
                                "ee0cb68e7b26fb10": {
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                },
                                "09234c9073840e62": {
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                },
                                "1a6c2eab036f33ca": {
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                },
                                "67a15142f8dcbf5d": {
                                        "remaining": 375.0,
                                        "type": "MAGIC",
                                        "count": 0
                                },
                                "3d73eeae238b9f1e": {
                                        "remaining": null,
                                        "type": "NONE",
                                        "count": 0
                                }
                        },
                        "debuff": [],
                        "debuff_dict": {}
                },
                "spell_sequence": [
                        {
                                "title": "cd4802106d577575",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "苦修",
                                "remaining": 0,
                                "height": true,
                                "charge": 2
                        },
                        {
                                "title": "真言术：耀",
                                "remaining": 0,
                                "height": true,
                                "charge": 2
                        },
                        {
                                "title": "痛苦压制",
                                "remaining": 0,
                                "height": true,
                                "charge": 2
                        },
                        {
                                "title": "真言术：盾",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "心灵震爆",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "纯净术",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "暗言术：灭",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "绝望祷言",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "福音",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        {
                                "title": "630505db0d1fa352",
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        }
                ],
                "spell": {
                        "cd4802106d577575": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "苦修": {
                                "remaining": 0,
                                "height": true,
                                "charge": 2
                        },
                        "真言术：耀": {
                                "remaining": 0,
                                "height": true,
                                "charge": 2
                        },
                        "痛苦压制": {
                                "remaining": 0,
                                "height": true,
                                "charge": 2
                        },
                        "真言术：盾": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "心灵震爆": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "纯净术": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "暗言术：灭": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "绝望祷言": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "福音": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        },
                        "630505db0d1fa352": {
                                "remaining": 0,
                                "height": true,
                                "charge": null
                        }
                },
                "status": {
                        "damage_absorbs": 33.33333333333333,
                        "heal_absorbs": 0.0,
                        "health": 100.0,
                        "power": 100.0,
                        "in_combat": false,
                        "in_movement": false,
                        "in_vehicle": false,
                        "is_empowered": false,
                        "cast_icon": null,
                        "cast_duration": null,
                        "channel_icon": null,
                        "channel_duration": null,
                        "class": "PRIEST",
                        "role": "HEALER",
                        "deaded": false
                }
        },
        "target": {
                "aura": {
                        "debuff": [],
                        "debuff_dict": {}
                },
                "status": {
                        "exists": true,
                        "can_attack": false,
                        "is_self": true,
                        "alive": true,
                        "in_combat": false,
                        "in_range": true,
                        "health": 100.0,
                        "cast_icon": null,
                        "cast_duration": null,
                        "cast_interruptible": null,
                        "channel_icon": null,
                        "channel_duration": null,
                        "channel_interruptible": null
                }
        },
        "focus": {
                "aura": {
                        "debuff": [],
                        "debuff_dict": {}
                },
                "status": {
                        "exists": false
                }
        },
        "party": {
                "party1": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 100.0,
                                "class": "PALADIN",
                                "role": "TANK",
                                "selectd": false,
                                "damage_absorbs": 0.0,
                                "heal_absorbs": 0.0
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                },
                                "debuff": [],
                                "debuff_dict": {}
                        }
                },
                "party2": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 100.0,
                                "class": "HUNTER",
                                "role": "DPS",
                                "selectd": false,
                                "damage_absorbs": 0.0,
                                "heal_absorbs": 0.0
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                },
                                "debuff": [],
                                "debuff_dict": {}
                        }
                },
                "party3": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 100.0,
                                "class": "MAGE",
                                "role": "DPS",
                                "selectd": false,
                                "damage_absorbs": 16.666666666666664,
                                "heal_absorbs": 0.0
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                },
                                "debuff": [],
                                "debuff_dict": {}
                        }
                },
                "party4": {
                        "exists": true,
                        "status": {
                                "in_range": true,
                                "health": 100.0,
                                "class": "SHAMAN",
                                "role": "DPS",
                                "selectd": false,
                                "damage_absorbs": 0.0,
                                "heal_absorbs": 0.0
                        },
                        "aura": {
                                "buff": [
                                        {
                                                "title": "真言术：韧",
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                ],
                                "buff_dict": {
                                        "真言术：韧": {
                                                "remaining": 375.0,
                                                "type": "MAGIC",
                                                "count": 0
                                        }
                                },
                                "debuff": [],
                                "debuff_dict": {}
                        }
                }
        }
}
"""

high_damage_debuff = ["张三", "李四", "王五"]  # 高伤害debuff列表


def calculate_party_health_score(data):
    '''计算小队数据'''
    temp_members = []
    party_members = []
    player = data["player"]
    player["unit_id"] = "player"
    party = data["party"]
    temp_members.append(player)

    for k, v in party.items():
        if v["exists"]:
            v["unit_id"] = k
            temp_members.append(v)

    for member in temp_members:
        unit_id = member["unit_id"]
        m_class = member["status"]["class"]
        m_role = member["status"]["role"]
        m_health = member["status"]["health"]
        m_damage_absorbs = member["status"]["damage_absorbs"]  # 伤害吸收盾，吸收承受伤害的buff
        m_heal_absorbs = member["status"]["heal_absorbs"]  # 治疗吸收盾，吸收治疗效果的debuff
        healing_deficit = 100.0 - m_health + m_heal_absorbs  # 治疗缺口，即治疗效果的缺口，用于计算治疗倾向
        health_score = m_health + m_damage_absorbs - healing_deficit  # 健康分数，用于计算治疗倾向

        if m_role == "TANK":
            health_score = health_score * 1.10
            healing_deficit = min(healing_deficit - 0.2, 0.0)

        if m_role == "HEALER":
            health_score = health_score * 0.95

        shield_remaining = 0.0  # 真言术：盾 剩余时间
        if "真言术：盾" in member["aura"]["buff_dict"]:
            shield_remaining = member["aura"]["buff_dict"]["真言术：盾"]["remaining"]

        atonement_remaining = 0.0  # 救赎 剩余时间

        if "救赎" in member["aura"]["buff_dict"]:
            atonement_remaining = member["aura"]["buff_dict"]["救赎"]["remaining"]

        fortitude_remaining = 0.0  # 真言术：韧 剩余时间
        if "真言术：韧" in member["aura"]["buff_dict"]:
            fortitude_remaining = member["aura"]["buff_dict"]["真言术：韧"]["remaining"]

        dispel_list = [debuff["type"] for debuff in member["aura"]["debuff"] if debuff["type"] != "NONE"]  # 可驱散debuff类型列表

        damage_debuff_count = len([debuff for debuff in member["aura"]["debuff"] if debuff["title"] in high_damage_debuff])

        party_members.append({
            "unit_id": unit_id,  # 目标ID
            "class": m_class,  # 目标职业
            "role": m_role,  # 目标职责
            "health": m_health,  # 目标当前生命值
            "damage_absorbs": m_damage_absorbs,  # 伤害吸收盾，吸收承受伤害的buff
            "heal_absorbs": m_heal_absorbs,  # 治疗吸收盾，吸收治疗效果的debuff
            "healing_deficit": healing_deficit,  # 治疗缺口，即治疗效果的缺口，用于计算治疗倾向
            "health_score": health_score,  # 健康分数，用于计算治疗倾向
            "shield_remaining": shield_remaining,  # 真言术：盾 剩余时间
            "atonement_remaining": atonement_remaining,  # 救赎 剩余时间
            "fortitude_remaining": fortitude_remaining,  # 真言术：韧 剩余时间
            "dispel_list": dispel_list,  # 可驱散debuff类型列表
            "damage_debuff_count": damage_debuff_count,  # 高伤害debuff数量
        })

    party_members.sort(key=lambda x: x["health_score"], reverse=False)  # 按健康分数排序，从低到高

    return party_members


def idle(title):
    print(f"因为{title}而暂停")
    return f"因为{title}而暂停"


def cast(target, title):
    print(f"向{target}施放{title}")
    return "向{target}施放{title}"


def rotation(result):

    player = result["player"]
    player_status = player["status"]
    player_aura = player["aura"]

    party_members = calculate_party_health_score(result)

    print(party_members)

    if not player_status["in_combat"]:
        return idle("不在战斗中")

    if player_status["in_vehicle"]:
        return idle("在载具中")

    if player_status["cast_duration"] is not None and player_status["cast_duration"] < 95:
        return idle("在施法")

    if player_status["channel_duration"] is not None and player_status["channel_duration"] < 95:
        return idle("在通道法术")

    if player_status["health"] == 0:
        return idle("已死亡")

    if player_status["deaded"]:
        return idle("已死亡")

    if "食物：刀叉" in player_aura["buff_dict"]:
        return idle("食物")

    if "食物：面包" in player_aura["buff_dict"]:
        return idle("食物")

    if "食物：饮料" in player_aura["buff_dict"]:
        return idle("食物")

    return idle("无所事事")
