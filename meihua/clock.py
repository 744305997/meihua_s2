"""
四象时钟：全局时序调制器
"""

import math
from typing import Dict

class SixiangClock:
    SIXIANG_ORDER = ['少阳', '太阳', '少阴', '太阴']
    
    DEFAULT_MODULATION: Dict[str, Dict[str, float]] = {
        '少阳': {'木': 1.5, '火': 1.2, '土': 1.0, '金': 1.0, '水': 1.0},
        '太阳': {'木': 1.0, '火': 2.0, '土': 1.0, '金': 0.5, '水': 1.0},
        '少阴': {'木': 1.0, '火': 1.0, '土': 1.0, '金': 1.5, '水': 1.2},
        '太阴': {'木': 0.5, '火': 1.0, '土': 1.0, '金': 1.0, '水': 2.0},
    }
    
    def __init__(self, steps_per_cycle: int = 20, modulation: Dict = None):
        self.steps_per_cycle = steps_per_cycle
        self.modulation = modulation or self.DEFAULT_MODULATION
        self.step_count = 0
    
    def tick(self) -> str:
        phase_index = (self.step_count // (self.steps_per_cycle // 4)) % 4
        current = self.SIXIANG_ORDER[phase_index]
        self.step_count += 1
        return current
    
    def get_gains(self) -> Dict[str, float]:
        phase_index = (self.step_count // (self.steps_per_cycle // 4)) % 4
        current = self.SIXIANG_ORDER[min(phase_index, 3)]
        return self.modulation[current].copy()
    
    def reset(self):
        self.step_count = 0