"""
编解码器：五进制/四进制/八进制与二进制互转
"""

from typing import List

# 五行 <-> 五进制 <-> 3位二进制
WUXING_TO_DIGIT = {'水': 0, '木': 1, '火': 2, '土': 3, '金': 4}
DIGIT_TO_WUXING = {0: '水', 1: '木', 2: '火', 3: '土', 4: '金'}
WUXING_TO_BIN = {'木': '001', '火': '010', '土': '011', '金': '100', '水': '101'}
BIN_TO_WUXING = {'001': '木', '010': '火', '011': '土', '100': '金', '101': '水'}

# 四象 <-> 四进制 <-> 2位二进制
SIXIANG_TO_DIGIT = {'少阳': 0, '太阳': 1, '少阴': 2, '太阴': 3}
DIGIT_TO_SIXIANG = {0: '少阳', 1: '太阳', 2: '少阴', 3: '太阴'}
SIXIANG_TO_BIN = {'少阳': '00', '太阳': '01', '少阴': '10', '太阴': '11'}

# 八卦 <-> 八进制 <-> 3位二进制
BAGUA_TO_DIGIT = {'乾': 0, '坤': 1, '震': 2, '巽': 3, '坎': 4, '离': 5, '艮': 6, '兑': 7}
DIGIT_TO_BAGUA = {0: '乾', 1: '坤', 2: '震', 3: '巽', 4: '坎', 5: '离', 6: '艮', 7: '兑'}
BAGUA_TO_BIN = {'乾': '000', '坤': '001', '震': '010', '巽': '011', '坎': '100', '离': '101', '艮': '110', '兑': '111'}

def wuxing_sequence_to_binary(wuxing_list: List[str]) -> str:
    return ''.join(WUXING_TO_BIN[w] for w in wuxing_list)

def binary_to_wuxing_sequence(binary_str: str) -> List[str]:
    assert len(binary_str) % 3 == 0, "长度需为3的倍数"
    return [BIN_TO_WUXING[binary_str[i:i+3]] for i in range(0, len(binary_str), 3)]