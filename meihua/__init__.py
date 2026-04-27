"""
梅花超算 (MeiHua Engine) v2.0
基于五行四象八卦的符号动力学演化计算工具包
"""

from .engine import MeiHuaEngine
from .clock import SixiangClock
from .router import BaguaRouter
from .codec import (
    WUXING_TO_DIGIT, DIGIT_TO_WUXING,
    wuxing_sequence_to_binary, binary_to_wuxing_sequence
)
from .herb import HERB_LIBRARY
from .profile import compute_initial_energy
from .preset import PRESETS

__version__ = "2.0.0"
__all__ = [
    'MeiHuaEngine',
    'SixiangClock',
    'BaguaRouter',
    'HERB_LIBRARY',
    'compute_initial_energy',
    'PRESETS',
    'wuxing_sequence_to_binary',
    'binary_to_wuxing_sequence'
]