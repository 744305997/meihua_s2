"""
梅花超算核心引擎 v2.0
整合五行生克演化、四象时钟调制、自定义药剂注入
"""

from typing import List, Dict, Optional, Union
from .clock import SixiangClock
from .herb import HERB_LIBRARY

class MeiHuaEngine:
    """五行演化引擎"""
    
    WUXING = ['木', '火', '土', '金', '水']
    WUXING_INDEX = {name: i for i, name in enumerate(WUXING)}
    
    SHENG_MAP = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    KE_MAP = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    
    def __init__(
        self,
        sheng_coeff: float = 0.05,
        ke_coeff: float = 0.03,
        decay: float = 0.92,
        inject_energy: float = 0.15,
        initial_energy: Optional[List[float]] = None,
        clock: Optional[SixiangClock] = None,
        use_clock_modulation: bool = True
    ):
        self.sheng_coeff = sheng_coeff
        self.ke_coeff = ke_coeff
        self.decay = decay
        self.base_inject_energy = inject_energy
        self.clock = clock or SixiangClock()
        self.use_clock_modulation = use_clock_modulation
        
        # 初始能量
        if initial_energy is None:
            initial_energy = [0.2] * 5
        self.energy = initial_energy.copy()
        
        # 历史记录
        self.history: List[List[float]] = [self.energy.copy()]
        self.output_sequence: List[str] = []
        self.herb_log: List[Union[str, Dict, None]] = []
    
    def step(
        self,
        input_wuxing: str,
        herb: Optional[str] = None,
        herb_effect: Optional[Dict[str, float]] = None
    ) -> str:
        """执行一步演化，可附带药剂干预"""
        idx = self.WUXING_INDEX[input_wuxing]
        
        # 1. 能量灌注（含四象时钟调制）
        if self.use_clock_modulation:
            gains = self.clock.get_gains()
            self.clock.tick()
        else:
            gains = {w: 1.0 for w in self.WUXING}
        self.energy[idx] += self.base_inject_energy * gains[input_wuxing]
        
        # 2. 药剂注入
        if herb_effect is not None:
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
        
        # 3. 相生传递
        sheng_transfer = [0.0] * 5
        for i, source in enumerate(self.WUXING):
            target = self.SHENG_MAP[source]
            target_idx = self.WUXING_INDEX[target]
            sheng_transfer[target_idx] += self.energy[i] * self.sheng_coeff
        for i in range(5):
            self.energy[i] += sheng_transfer[i]
        
        # 4. 相克抑制
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
        
        # 6. 边界保护
        for i in range(5):
            self.energy[i] = max(0.001, min(10.0, self.energy[i]))
        
        # 7. 输出最强核
        max_idx = self.energy.index(max(self.energy))
        output = self.WUXING[max_idx]
        
        self.history.append(self.energy.copy())
        self.output_sequence.append(output)
        return output
    
    def run(
        self,
        input_sequence: List[str],
        herbs: Optional[List[Union[str, Dict, None]]] = None
    ) -> List[str]:
        """运行输入序列，可选同步药剂列表"""
        if herbs is None:
            herbs = [None] * len(input_sequence)
        for wuxing, herb in zip(input_sequence, herbs):
            if isinstance(herb, dict):
                self.step(wuxing, herb_effect=herb)
            elif isinstance(herb, str):
                self.step(wuxing, herb=herb)
            else:
                self.step(wuxing)
        return self.output_sequence
    
    def apply_herb(self, herb: Union[str, Dict[str, float]]):
        """单独使用药剂（不伴随脉象输入）"""
        if isinstance(herb, dict):
            for wuxing_name, delta in herb.items():
                if wuxing_name in self.WUXING_INDEX:
                    i = self.WUXING_INDEX[wuxing_name]
                    self.energy[i] += delta
                    self.energy[i] = max(0.001, min(10.0, self.energy[i]))
            self.herb_log.append(herb)
        elif herb in HERB_LIBRARY:
            target, strength = HERB_LIBRARY[herb]
            i = self.WUXING_INDEX[target]
            self.energy[i] += strength
            self.energy[i] = max(0.001, min(10.0, self.energy[i]))
            self.herb_log.append(herb)
        # 记录状态（作为历史但无脉象输入）
        self.history.append(self.energy.copy())
    
    def get_state(self) -> Dict[str, float]:
        """返回当前五核能量字典"""
        return {name: self.energy[i] for i, name in enumerate(self.WUXING)}
    
    def get_state_summary(self) -> str:
        lines = []
        for name, val in zip(self.WUXING, self.energy):
            bar = '█' * max(0, int(val * 20))
            lines.append(f"  {name}: {val:.4f} {bar}")
        return '\n'.join(lines)
    
    def get_statistics(self) -> Dict:
        from collections import Counter
        if not self.output_sequence:
            return {}
        counter = Counter(self.output_sequence)
        total = len(self.output_sequence)
        return {
            'total_steps': total,
            'distribution': {w: counter.get(w, 0) for w in self.WUXING},
            'frequencies': {w: counter.get(w, 0)/total for w in self.WUXING},
            'is_locked': any(c > total * 0.9 for c in counter.values())
        }
    
    def reset(self):
        self.energy = [0.2] * 5
        self.history = [self.energy.copy()]
        self.output_sequence = []
        self.herb_log = []
        if self.clock:
            self.clock.reset()