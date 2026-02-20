from rich import print
from EZPixelRotationX2 import RotationEngine, AttrDict, SliderConfig, ComboConfig
high_damage_debuff = ['张三', '李四', '王五']


class PriestDisciplineEngine(RotationEngine):

    def __init__(self):
        super().__init__()
        self._setup_config()
        self._setup_macros()

    def _setup_config(self):
        self.config.add_item(SliderConfig(key='self_heal_threshold', label='自我治疗阈值 (%)', description='低于此血量时使用自我治疗技能', min_value=20, max_value=80, step=2.5, default_value=45, value_transform=float))
        self.config.add_item(SliderConfig(key='tank_deficit_ignore_pct', label='TANK缺口忽略 (%)', description='TANK 视为满血的缺口比例（例如 20 代表 80% 视为满血）', min_value=0, max_value=100, step=5, default_value=20, value_transform=float))
        self.config.add_item(SliderConfig(key='tank_health_score_mul', label='TANK健康分数系数', description='用于调整TANK健康分数的加成系数', min_value=1.0, max_value=1.2, step=0.05, default_value=1.1, value_transform=float))
        self.config.add_item(SliderConfig(key='healer_health_score_mul', label='HEALER健康分数系数', description='用于调整HEALER健康分数的系数', min_value=0.8, max_value=1.0, step=0.05, default_value=0.95, value_transform=float))
        self.config.add_item(SliderConfig(key='fade_threshold', label='渐隐术阈值 (%)', description='低于此血量时使用渐隐术', min_value=50, max_value=100, step=2.5, default_value=85, value_transform=float))
        self.config.add_item(ComboConfig(key='dispel_logic', label='驱散逻辑', description='在什么情况下驱散', options=['黑名单', '白名单', '乱驱'], default_index=0, value_transform=str))
        self.config.add_item(ComboConfig(key='dispel_types', label='驱散类型', description='根据天赋选择可驱散的类型', options=['MAGIC|DISEASE', 'MAGIC'], default_index=0, value_transform=lambda s: s.split('|') if s else []))
        self.config.add_item(SliderConfig(key='need_heal_deficit_threshold', label='最小治疗缺口', description='治疗缺口大于该值时视为需要治疗', min_value=0, max_value=20, step=1, default_value=10, value_transform=float))
        self.config.add_item(SliderConfig(key='penance_heal_max_targets', label='进攻苦修群抬目标数', description='需要治疗人数不超过该值时对友方施放苦修', min_value=1, max_value=4, step=1, default_value=3, value_transform=float))
        self.config.add_item(SliderConfig(key='flash_heal_deficit_threshold', label='快速治疗阈值', description='治疗缺口超过该值时施放快速治疗', min_value=1, max_value=50, step=5, default_value=25, value_transform=float))
        self.config.add_item(ComboConfig(key='penance_logic', label='苦修逻辑', description='在什么情况下使用苦修', options=['攻守兼备', '仅治疗'], default_index=0, value_transform=str))
        self.config.add_item(ComboConfig(key='plea_logic', label='恳求逻辑', description='恳求是个高蓝耗, 低收益技能, 除了补救赎没有其他用途, 根据习惯调整。', options=['血量大于缺口无救赎', '任意情况补救赎', '不使用'], default_index=0, value_transform=str))
        self.config.add_item(ComboConfig(key='radiance_logic', label='耀逻辑', description='耀提供了治疗量，在全员满血时使用耀，还是有点浪费的。', options=['有缺口才使用', '满血使用'], default_index=0, value_transform=str))

    def _setup_macros(self):
        self.set_macro('target痛', 'ALT-NUMPAD1')
        self.set_macro('focus痛', 'ALT-NUMPAD2')
        self.set_macro('target灭', 'ALT-NUMPAD3')
        self.set_macro('focus灭', 'ALT-NUMPAD4')
        self.set_macro('target心灵震爆', 'ALT-NUMPAD5')
        self.set_macro('focus心灵震爆', 'ALT-NUMPAD6')
        self.set_macro('target惩击', 'ALT-NUMPAD7')
        self.set_macro('focus惩击', 'ALT-NUMPAD8')
        self.set_macro('player盾', 'ALT-NUMPAD9')
        self.set_macro('party1盾', 'ALT-NUMPAD0')
        self.set_macro('party2盾', 'SHIFT-NUMPAD1')
        self.set_macro('party3盾', 'SHIFT-NUMPAD2')
        self.set_macro('party4盾', 'SHIFT-NUMPAD3')
        self.set_macro('target苦修', 'SHIFT-NUMPAD4')
        self.set_macro('focus苦修', 'SHIFT-NUMPAD5')
        self.set_macro('player苦修', 'SHIFT-NUMPAD6')
        self.set_macro('party1苦修', 'SHIFT-NUMPAD7')
        self.set_macro('party2苦修', 'SHIFT-NUMPAD8')
        self.set_macro('party3苦修', 'SHIFT-NUMPAD9')
        self.set_macro('party4苦修', 'SHIFT-NUMPAD0')
        self.set_macro('player恳求', 'ALT-F2')
        self.set_macro('party1恳求', 'ALT-F3')
        self.set_macro('party2恳求', 'ALT-F5')
        self.set_macro('party3恳求', 'ALT-F6')
        self.set_macro('party4恳求', 'ALT-F7')
        self.set_macro('player纯净术', 'ALT-F8')
        self.set_macro('party1纯净术', 'ALT-F9')
        self.set_macro('party2纯净术', 'ALT-F10')
        self.set_macro('party3纯净术', 'ALT-F11')
        self.set_macro('party4纯净术', 'ALT-F12')
        self.set_macro('player快速治疗', 'SHIFT-F2')
        self.set_macro('party1快速治疗', 'SHIFT-F3')
        self.set_macro('party2快速治疗', 'SHIFT-F5')
        self.set_macro('party3快速治疗', 'SHIFT-F6')
        self.set_macro('party4快速治疗', 'SHIFT-F7')
        self.set_macro('any切换目标', 'SHIFT-F8')
        self.set_macro('any耀', 'SHIFT-F9')
        self.set_macro('any绝望祷言', 'SHIFT-F10')
        self.set_macro('any耐力', 'SHIFT-F11')
        self.set_macro('any渐隐术', 'SHIFT-F12')

    def calculate_party_health_score(self, data):
        temp_members = []
        party_members = []
        player = data.player
        party = data['party']
        temp_members.append(player)
        for k, v in party.items():
            if v['exists']:
                temp_members.append(v)
        dispel_type_list = self.config.dispel_types
        for unit in temp_members:
            unit_role = unit.status.unit_role
            unit_health = unit.status.unit_health
            unit_damage_absorbs = unit.status.unit_damage_absorbs
            unit_heal_absorbs = unit.status.unit_heal_absorbs
            base_missing = 100.0 - unit_health
            unit_heal_deficit = base_missing + unit_heal_absorbs
            if unit_role == 'TANK':
                unit_heal_deficit = max(base_missing - self.config.tank_deficit_ignore_pct, 0.0) + unit_heal_absorbs
            unit_health_score = unit_health + unit_damage_absorbs - unit_heal_deficit
            if unit_role == 'TANK':
                unit_health_score = unit_health_score * self.config.tank_health_score_mul
            if unit_role == 'HEALER':
                unit_health_score = unit_health_score * self.config.healer_health_score_mul
            unit_dict = AttrDict({'unitToken': unit.unitToken, 'unit_class': unit.status.unit_class, 'unit_role': unit_role, 'unit_health': unit_health, 'unit_damage_absorbs': unit_damage_absorbs, 'unit_heal_absorbs': unit_heal_absorbs, 'unit_heal_deficit': unit_heal_deficit, 'unit_health_score': unit_health_score, 'shield_remaining': unit.aura.buff['真言术：盾'].remaining or 0.0, 'atonement_remaining': unit.aura.buff['救赎'].remaining or 0.0,
                                 'fortitude_remaining': unit.aura.buff['真言术：韧'].remaining or 0.0, 'dispel_list': [debuff.type for debuff in unit.aura.debuff_sequence if debuff.type in dispel_type_list], 'damage_debuff_count': len([debuff for debuff in unit.aura.debuff_sequence if debuff.title in high_damage_debuff]), 'unit_in_range': unit.status.unit_in_range, 'selectd': unit.status.selectd})
            party_members.append(unit_dict)
        party_members.sort(key=lambda x: x.unit_health_score, reverse=False)
        return party_members

    def main_rotation(self, data):
        spell_queue_window = self.config.spell_queue_window
        player = data.player
        spell = player.spell
        gcd = spell.公共冷却时间
        gcd_ready = gcd.remaining <= spell_queue_window
        target = data.target
        focus = data.focus
        party_members = self.calculate_party_health_score(data)
        in_range_member = [unit for unit in party_members if unit.unit_in_range]
        if len(in_range_member) == 0:
            return self.idle('没有队友在视野内')
        if not player.status.unit_in_combat:
            return self.idle('不在战斗中')
        if player.status.on_chat:
            return self.idle('在聊天中')
        if player.status.unit_in_vehicle:
            return self.idle('在载具中')
        if player.status.unit_cast_icon != None and player.status.unit_cast_duration <= 95:
            return self.idle('在施法')
        if player.status.unit_channel_icon != None and player.status.unit_channel_duration <= 95:
            return self.idle('在通道法术')
        if player.status.unit_is_dead_or_ghost:
            return self.idle('已死亡')
        if player.aura.buff['食物和饮料']:
            return self.idle('食物')
        player_in_movement = player.status.unit_in_movement
        player_is_stand = not player_in_movement
        auto_target = None
        if focus.status.exists and focus.status.unit_in_range and focus.status.unit_can_attack and focus.status.unit_in_combat:
            auto_target = focus
        elif target.status.exists and target.status.unit_in_range and target.status.unit_can_attack and target.status.unit_in_combat:
            auto_target = target
        without_shield = [unit for unit in in_range_member if unit.shield_remaining <= spell_queue_window]
        without_atonement = [unit for unit in in_range_member if unit.atonement_remaining <= spell_queue_window]
        without_atonement_non_tank = [unit for unit in without_atonement if unit.unit_role != 'TANK']
        with_debuff_members = [unit for unit in in_range_member if len(unit.dispel_list) > 0]
        need_heal_member = [unit for unit in in_range_member if unit.unit_heal_deficit > self.config.need_heal_deficit_threshold]
        need_heal_member.sort(key=lambda x: x.unit_health_score, reverse=False)
        need_heal_without_atonement_member = [unit for unit in need_heal_member if unit.atonement_remaining <= spell_queue_window]
        if spell['绝望祷言'].remaining <= spell_queue_window:
            if player.status.unit_health < self.config.self_heal_threshold:
                return self.cast('any', '绝望祷言')
        if spell['渐隐术'].remaining <= spell_queue_window:
            if player.status.unit_health < self.config.fade_threshold:
                return self.cast('any', '渐隐术')
        radiance_ready = spell['真言术：耀'].charge == 2 and gcd_ready and player_is_stand
        radiance_logic_1 = self.config.radiance_logic == '有缺口才使用' and len(need_heal_without_atonement_member) >= 2
        radiance_logic_2 = self.config.radiance_logic == '满血使用' and len(without_atonement) >= 2
        if radiance_ready and (radiance_logic_1 or radiance_logic_2):
            return self.cast('any', '耀')
        if spell['纯净术'].charge >= 1 and gcd_ready:
            if len(with_debuff_members) > 0:
                return self.cast(with_debuff_members[0].unitToken, '纯净术')
        if player.aura.buff['祸福相倚'] and player.aura.buff['祸福相倚'].count >= 4 and gcd_ready:
            if spell['真言术：盾'].remaining <= spell_queue_window:
                if len(without_shield) > 0:
                    return self.cast(without_shield[0].unitToken, '盾')
                else:
                    return self.cast(in_range_member[0].unitToken, '盾')
        if auto_target and spell['心灵震爆'].remaining <= spell_queue_window and (not player.aura.buff['阴暗面之力']) and gcd_ready and player_is_stand:
            return self.cast(auto_target.unitToken, '心灵震爆')
        penance_logic_1 = self.config.penance_logic == '攻守兼备'
        penance_logic_2 = self.config.penance_logic == '仅治疗' and len(need_heal_member) > 0
        if spell['苦修'].charge >= 1 and gcd_ready and (penance_logic_1 or penance_logic_2):
            if len(need_heal_member) <= int(self.config.penance_heal_max_targets) and len(need_heal_member) > 0:
                return self.cast(need_heal_member[0].unitToken, '苦修')
            if auto_target:
                return self.cast(auto_target.unitToken, '苦修')
        can_cast_flash = player_is_stand or player.aura.buff['圣光涌动']
        if in_range_member and in_range_member[0].unit_heal_deficit > self.config.flash_heal_deficit_threshold and gcd_ready and can_cast_flash:
            return self.cast(in_range_member[0].unitToken, '快速治疗')
        plea_logic_1 = self.config.plea_logic == '血量大于缺口无救赎' and len(need_heal_without_atonement_member) > 0
        if plea_logic_1 and gcd_ready:
            return self.cast(need_heal_without_atonement_member[0].unitToken, '恳求')
        plea_logic_2 = self.config.plea_logic == '任意情况补救赎' and len(without_atonement) > 0
        if plea_logic_2 and gcd_ready:
            return self.cast(without_atonement[0].unitToken, '恳求')
        if not auto_target:
            return self.cast('any', '切换目标')
        if auto_target:
            if not auto_target.aura.debuff['痛'] and gcd_ready:
                return self.cast(auto_target.unitToken, '痛')
        if focus.status.exists and focus.status.unit_in_range and focus.status.unit_can_attack and focus.status.unit_in_combat:
            if not focus.aura.debuff['痛'] and gcd_ready:
                return self.cast(focus.unitToken, '痛')
        if target.status.exists and target.status.unit_in_range and target.status.unit_can_attack and target.status.unit_in_combat:
            if not target.aura.debuff['痛'] and gcd_ready:
                return self.cast(target.unitToken, '痛')
        if auto_target and auto_target.status.unit_health < 20 and (spell['暗言术：灭'].remaining <= spell_queue_window):
            return self.cast(auto_target.unitToken, '灭')
        if auto_target and gcd_ready:
            return self.cast(auto_target.unitToken, '惩击')
        if not gcd_ready:
            return self.idle('公共冷却时间')
        return self.idle('无所事事')


if __name__ == '__main__':
    engine = PriestDisciplineEngine()
    engine.run()
