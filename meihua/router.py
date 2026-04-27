"""
八卦路由：空间拓扑映射
"""

from typing import Dict, List

class BaguaRouter:
    BAGUA_MAP: Dict[str, tuple] = {
        '乾': ('金', '坤'),
        '坤': ('土', '乾'),
        '震': ('木', '巽'),
        '巽': ('木', '震'),
        '坎': ('水', '离'),
        '离': ('火', '坎'),
        '艮': ('土', '兑'),
        '兑': ('金', '艮'),
    }
    
    @classmethod
    def to_wuxing(cls, bagua: str) -> str:
        return cls.BAGUA_MAP[bagua][0]
    
    @classmethod
    def get_opposite(cls, bagua: str) -> str:
        return cls.BAGUA_MAP[bagua][1]
    
    @classmethod
    def route(cls, source_bagua: str) -> List[str]:
        return [source_bagua, cls.get_opposite(source_bagua)]