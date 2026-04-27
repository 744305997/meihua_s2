"""
脉象五行演化推演器 - 高级引擎
整合复合脉象、稳态回归、情志冲击、多因素权重、动态方剂、随机扰动
"""

import random
from typing import List, Dict, Optional, Tuple
from .engine import MeiHuaEngine
from .clock import SixiangClock
from .herb import HERB_LIBRARY

class AdvancedEngine(MeiHuaEngine):
    """高级五行演化引擎"""
    
    def __init__(
        self,
        sheng_coeff: float = 0.05,
        ke_coeff: float = 0.03,
        decay: float = 0.92,
        inject_energy: float = 0.15,
        initial_energy: Optional[List[float]] = None,
        clock: Optional[SixiangClock] = None,
        use_clock_modulation: bool = True,
        # 高级参数
        homeostasis_strength: float = 0.0,      # 稳态回归力 (0=无，0.01-0.05推荐)
        random_fluctuation: float = 0.0,          # 随机扰动幅度 (0=无，0.005-0.02推荐)
        event_weight_multiplier: float = 1.0      # 事件权重全局倍数
    ):
        super().__init__(
            sheng_coeff=sheng_coeff,
            ke_coeff=ke_coeff,
            decay=decay,
            inject_energy=inject_energy,
            initial_energy=initial_energy,
            clock=clock,
            use_clock_modulation=use_clock_modulation
        )
        self.homeostasis_strength = homeostasis_strength
        self.random_fluctuation = random_fluctuation
        self.event_weight_multiplier = event_weight_multiplier
        
        # 高级状态
        self.initial_energy_baseline = self.energy.copy()  # 稳态基准
        self.event_log: List[Dict] = []  # 事件记录
        self.herb_schedule: Dict[int, Dict] = {}  # 步数->药剂映射
    
    def set_herb_schedule(self, schedule: Dict[int, Dict]):
        """设置动态方剂计划 {步数: herb_name 或 herb_effect}"""
        self.herb_schedule = schedule
    
    def inject_event(self, event_name: str, event_effects: Dict[str, float], weight: float = 1.0):
        """注入情志事件或瞬时冲击
        event_effects: {'木': +0.3, '火': +0.1, '土': -0.1} 等
        weight: 该事件的权重系数
        """
        effective_weight = weight * self.event_weight_multiplier
        for wuxing_name, delta in event_effects.items():
            if wuxing_name in self.WUXING_INDEX:
                i = self.WUXING_INDEX[wuxing_name]
                self.energy[i] += delta * effective_weight
                self.energy[i] = max(0.001, min(10.0, self.energy[i]))
        self.event_log.append({
            'step': len(self.history),
            'event': event_name,
            'effects': event_effects,
            'weight': weight
        })
    
    def step(
        self,
        input_wuxing: str,
        secondary_input: Optional[str] = None,
        secondary_strength: float = 0.5,
        herb: Optional[str] = None,
        herb_effect: Optional[Dict[str, float]] = None
    ) -> str:
        """执行一步演化，支持复合脉象"""
        current_step = len(self.history)
        
        # 0. 稳态回归（在灌注前施加，模拟人体自愈倾向）
        if self.homeostasis_strength > 0:
            for i in range(5):
                deviation = self.initial_energy_baseline[i] - self.energy[i]
                self.energy[i] += deviation * self.homeostasis_strength
        
        # 1. 主脉象灌注
        idx = self.WUXING_INDEX[input_wuxing]
        if self.use_clock_modulation:
            gains = self.clock.get_gains()
            self.clock.tick()
        else:
            gains = {w: 1.0 for w in self.WUXING}
        self.energy[idx] += self.base_inject_energy * gains[input_wuxing]
        
        # 1.5 次脉象灌注（复合脉象）
        if secondary_input and secondary_input in self.WUXING_INDEX:
            sec_idx = self.WUXING_INDEX[secondary_input]
            sec_energy = self.base_inject_energy * secondary_strength
            if self.use_clock_modulation:
                sec_energy *= gains[secondary_input]
            self.energy[sec_idx] += sec_energy
        
        # 2. 动态方剂（按步数查找）
        if current_step in self.herb_schedule:
            scheduled_herb = self.herb_schedule[current_step]
            if isinstance(scheduled_herb, dict):
                for wuxing_name, delta in scheduled_herb.items():
                    if wuxing_name in self.WUXING_INDEX:
                        i = self.WUXING_INDEX[wuxing_name]
                        self.energy[i] += delta
                        self.energy[i] = max(0.001, min(10.0, self.energy[i]))
            elif scheduled_herb in HERB_LIBRARY:
                target, strength = HERB_LIBRARY[scheduled_herb]
                i = self.WUXING_INDEX[target]
                self.energy[i] += strength
                self.energy[i] = max(0.001, min(10.0, self.energy[i]))
        elif herb_effect is not None:
            for wuxing_name, delta in herb_effect.items():
                if wuxing_name in self.WUXING_INDEX:
                    i = self.WUXING_INDEX[wuxing_name]
                    self.energy[i] += delta
                    self.energy[i] = max(0.001, min(10.0, self.energy[i]))
            self.herb_log.append(herb_effect)
        elif herb is not None and herb in HERB_LIBRARY:
            target, strength = HERB_LIBRARY[herb]
            i = self.WUXING_INDEX[target]
            self.energy[i] += strength
            self.energy[i] = max(0.001, min(10.0, self.energy[i]))
            self.herb_log.append(herb)
        else:
            self.herb_log.append(None)
        
        # 3. 相生传递（与基础版相同）
        sheng_transfer = [0.0] * 5
        for i, source in enumerate(self.WUXING):
            target = self.SHENG_MAP[source]
            target_idx = self.WUXING_INDEX[target]
            sheng_transfer[target_idx] += self.energy[i] * self.sheng_coeff
        for i in range(5):
            self.energy[i] += sheng_transfer[i]
        
        # 4. 相克抑制（与基础版相同）
        ke_suppress = [0.0] * 5
        for i, source in enumerate(self.WUXING):
            target = self.KE_MAP[source]
            target_idx = self.WUXING_INDEX[target]
            ke_suppress[target_idx] -= self.energy[i] * self.ke_coeff
        for i in range(5):
            self.energy[i] += ke_suppress[i]
        
        # 5. 自然衰减
        for i in range(5):
            self.energy[i] *= self.decay
        
        # 6. 随机扰动（最后施加，模拟不可控的微小波动）
        if self.random_fluctuation > 0:
            for i in range(5):
                fluctuation = random.uniform(-self.random_fluctuation, self.random_fluctuation)
                self.energy[i] += fluctuation
                self.energy[i] = max(0.001, min(10.0, self.energy[i]))
        
        # 7. 边界保护
        for i in range(5):
            self.energy[i] = max(0.001, min(10.0, self.energy[i]))
        
        # 8. 输出最强核
        max_idx = self.energy.index(max(self.energy))
        output = self.WUXING[max_idx]
        
        self.history.append(self.energy.copy())
        self.output_sequence.append(output)
        return output