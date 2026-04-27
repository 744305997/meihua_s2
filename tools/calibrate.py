#!/usr/bin/env python3
"""
参数自动校准器（独立脚本，完成版）
根据医案阶段描述文件（如 case.json），自动设置目标能量区间，
搜索最佳引擎参数，并生成可导入模拟器的流派配置文件。

用法:
    # 切换到项目根目录（包含 meihua/ 和 presets/）
    python tools/calibrate.py --case case_example.json

    # 无参数时进入交互式问答（可手动输入目标）
    python tools/calibrate.py
"""

import json
import random
import copy
import sys
import os
import argparse
from typing import Dict, List, Optional, Tuple

# 将项目根目录加入系统路径，方便导入 meihua 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from meihua.four_diagnosis_engine import FourDiagnosisEngine
    ENGINE_AVAILABLE = True
except ImportError:
    print("警告：未找到 meihua 引擎模块，将使用简化模拟（仅用于演示校准流程）。")
    ENGINE_AVAILABLE = False

# ========== 内置症状关键词库 ==========
SYMPTOM_KEYWORDS = {
    "脉浮": ("切诊.脉象.浮", [0, 0, 0, 0.08, 0]),
    "浮脉": ("切诊.脉象.浮", [0, 0, 0, 0.08, 0]),
    "脉沉": ("切诊.脉象.沉", [0, 0, 0, 0, 0.05]),
    "沉脉": ("切诊.脉象.沉", [0, 0, 0, 0, 0.05]),
    "脉迟": ("切诊.脉象.迟", [0, -0.03, 0, 0, 0.05]),
    "迟脉": ("切诊.脉象.迟", [0, -0.03, 0, 0, 0.05]),
    "脉数": ("切诊.脉象.数", [0, 0.10, 0, 0, -0.05]),
    "数脉": ("切诊.脉象.数", [0, 0.10, 0, 0, -0.05]),
    "脉弦": ("切诊.脉象.弦", [0.15, 0, -0.03, 0, 0]),
    "弦脉": ("切诊.脉象.弦", [0.15, 0, -0.03, 0, 0]),
    "脉滑": ("切诊.脉象.滑", [0, 0, -0.05, 0, 0.05]),
    "滑脉": ("切诊.脉象.滑", [0, 0, -0.05, 0, 0.05]),
    "脉细": ("切诊.脉象.细", [0, -0.03, 0, 0, -0.05]),
    "细脉": ("切诊.脉象.细", [0, -0.03, 0, 0, -0.05]),
    "脉涩": ("切诊.脉象.涩", [-0.08, -0.03, 0, 0, 0]),
    "涩脉": ("切诊.脉象.涩", [-0.08, -0.03, 0, 0, 0]),
    "脉洪": ("切诊.脉象.洪", [0, 0.12, 0, 0, 0]),
    "洪脉": ("切诊.脉象.洪", [0, 0.12, 0, 0, 0]),
    "脉弦数": ("切诊.脉象.弦", [0.15, 0, -0.03, 0.05, 0]),
    "脉弦滑": ("切诊.脉象.弦", [0.15, 0, -0.05, 0.03, 0]),
    "脉沉细": ("切诊.脉象.沉", [0, -0.03, 0, 0, 0.03]),
    "脉细数": ("切诊.脉象.细", [0, 0.05, 0, 0, -0.08]),
    "舌淡白": ("望诊.舌象.舌质.淡白", [0, -0.08, -0.05, 0, 0]),
    "舌淡": ("望诊.舌象.舌质.淡白", [0, -0.08, -0.05, 0, 0]),
    "舌红": ("望诊.舌象.舌质.红舌", [0, 0.10, 0, 0, -0.05]),
    "舌质红": ("望诊.舌象.舌质.红舌", [0, 0.10, 0, 0, -0.05]),
    "舌绛": ("望诊.舌象.舌质.绛舌", [0, 0.12, 0, 0, -0.08]),
    "舌紫暗": ("望诊.舌象.舌质.紫暗", [-0.08, -0.05, 0, 0, 0]),
    "舌紫": ("望诊.舌象.舌质.紫暗", [-0.08, -0.05, 0, 0, 0]),
    "舌有瘀斑": ("望诊.舌象.舌质.紫暗", [-0.08, -0.05, 0, 0, 0]),
    "舌裂纹": ("望诊.舌象.舌质.裂纹", [0, 0, 0, 0, -0.10]),
    "舌胖大": ("望诊.舌象.舌质.胖大", [0, 0, -0.08, 0, 0.05]),
    "舌胖": ("望诊.舌象.舌质.胖大", [0, 0, -0.08, 0, 0.05]),
    "舌瘦薄": ("望诊.舌象.舌质.瘦薄", [0, 0.03, 0, 0, -0.05]),
    "舌齿痕": ("望诊.舌象.舌质.齿痕", [0, 0, -0.08, 0, 0.03]),
    "舌芒刺": ("望诊.舌象.舌质.芒刺", [0, 0.10, 0, 0, -0.05]),
    "苔薄白": ("望诊.舌象.舌苔.薄白", [0, 0, 0, 0, 0]),
    "薄白苔": ("望诊.舌象.舌苔.薄白", [0, 0, 0, 0, 0]),
    "苔黄腻": ("望诊.舌象.舌苔.黄腻", [0, 0.05, -0.05, 0, 0.03]),
    "黄腻苔": ("望诊.舌象.舌苔.黄腻", [0, 0.05, -0.05, 0, 0.03]),
    "苔白腻": ("望诊.舌象.舌苔.白腻", [0, 0, -0.05, 0, 0.05]),
    "白腻苔": ("望诊.舌象.舌苔.白腻", [0, 0, -0.05, 0, 0.05]),
    "苔黄": ("望诊.舌象.舌苔.黄腻", [0, 0.05, -0.05, 0, 0.03]),
    "少苔": ("望诊.舌象.舌苔.少苔", [0, 0.03, 0, 0, -0.10]),
    "无苔": ("望诊.舌象.舌苔.光剥", [0, 0, 0, 0, -0.15]),
    "光剥苔": ("望诊.舌象.舌苔.光剥", [0, 0, 0, 0, -0.15]),
    "苔黄燥": ("望诊.舌象.舌苔.黄燥", [0, 0.08, 0, 0, -0.10]),
    "面色青": ("望诊.面色.青", [0.08, -0.03, 0, 0, 0]),
    "面色赤": ("望诊.面色.赤", [0, 0.10, 0, 0, -0.05]),
    "面红": ("望诊.面色.赤", [0, 0.10, 0, 0, -0.05]),
    "面色黄": ("望诊.面色.黄", [0, 0, -0.08, 0, 0.05]),
    "面色萎黄": ("望诊.面色.黄", [0, 0, -0.08, 0, 0.05]),
    "面色白": ("望诊.面色.白", [0, -0.05, 0, -0.08, 0]),
    "面色苍白": ("望诊.面色.白", [0, -0.05, 0, -0.08, 0]),
    "面色黑": ("望诊.面色.黑", [0, -0.05, 0, 0, -0.10]),
    "声高气粗": ("闻诊.声音.声高气粗", [0.03, 0.05, 0, 0, 0]),
    "声低气怯": ("闻诊.声音.声低气怯", [0, 0, -0.05, -0.05, 0]),
    "声低": ("闻诊.声音.声低气怯", [0, 0, -0.05, -0.05, 0]),
    "咳声重浊": ("闻诊.声音.咳声重浊", [0, 0, -0.03, 0.03, 0]),
    "干咳": ("闻诊.声音.干咳声短", [0, 0, 0, -0.05, -0.05]),
    "喉中痰鸣": ("闻诊.声音.喉中痰鸣", [0, 0, -0.05, -0.03, 0]),
    "痰鸣": ("闻诊.声音.喉中痰鸣", [0, 0, -0.05, -0.03, 0]),
    "善太息": ("闻诊.声音.善太息", [-0.03, 0, 0, 0, 0]),
    "太息": ("闻诊.声音.善太息", [-0.03, 0, 0, 0, 0]),
    "叹气": ("闻诊.声音.善太息", [-0.03, 0, 0, 0, 0]),
    "口臭": ("闻诊.气味.口臭", [0, 0.05, -0.03, 0, 0]),
    "口苦": ("闻诊.气味.口苦", [0.03, 0.05, 0, 0, 0]),
    "口甜": ("闻诊.气味.口甜腻", [0, 0, -0.05, 0, 0.03]),
    "口甜腻": ("闻诊.气味.口甜腻", [0, 0, -0.05, 0, 0.03]),
    "腥臭": ("闻诊.气味.腥臭", [0, 0.05, 0, -0.05, 0]),
    "恶寒发热": ("问诊.寒热.恶寒重发热轻", [0, 0, 0, 0.08, 0.05]),
    "恶寒重发热轻": ("问诊.寒热.恶寒重发热轻", [0, 0, 0, 0.08, 0.05]),
    "发热重恶寒轻": ("问诊.寒热.发热重恶寒轻", [0, 0.08, 0, 0.05, -0.05]),
    "寒热往来": ("问诊.寒热.恶寒发热交替", [0.05, 0.03, 0, 0, 0]),
    "但热不寒": ("问诊.寒热.但热不寒", [0, 0.10, 0, 0, -0.05]),
    "但寒不热": ("问诊.寒热.但寒不热", [0, -0.10, 0, 0, 0.08]),
    "五心烦热": ("问诊.寒热.五心烦热", [0, 0.08, 0, 0, -0.08]),
    "烦热": ("问诊.寒热.五心烦热", [0, 0.05, 0, 0, -0.05]),
    "头痛": ("问诊.疼痛.头痛", [0.05, 0.03, 0, 0, 0]),
    "头晕": ("问诊.疼痛.头痛", [0.03, 0.03, 0, 0, -0.03]),
    "胁痛": ("问诊.疼痛.胁痛", [0.08, 0, -0.05, 0, 0]),
    "胃脘痛": ("问诊.疼痛.胃脘痛", [0.05, 0, -0.08, 0, 0]),
    "胃痛": ("问诊.疼痛.胃脘痛", [0.05, 0, -0.08, 0, 0]),
    "腹痛": ("问诊.疼痛.胃脘痛", [0, 0, -0.06, 0, 0]),
    "刺痛": ("问诊.疼痛.刺痛固定", [-0.08, -0.03, 0, 0, 0]),
    "胀痛": ("问诊.疼痛.胀痛走窜", [0.08, 0, 0, 0, 0]),
    "食欲减退": ("问诊.饮食口味.食欲减退", [0, 0, -0.10, 0, 0]),
    "纳呆": ("问诊.饮食口味.食欲减退", [0, 0, -0.10, 0, 0]),
    "纳差": ("问诊.饮食口味.食欲减退", [0, 0, -0.08, 0, 0]),
    "消谷善饥": ("问诊.饮食口味.消谷善饥", [0, 0.08, 0, 0, -0.05]),
    "口苦": ("问诊.饮食口味.口苦", [0.05, 0.05, 0, 0, 0]),
    "口淡": ("问诊.饮食口味.口淡无味", [0, -0.03, -0.05, 0, 0]),
    "口淡无味": ("问诊.饮食口味.口淡无味", [0, -0.03, -0.05, 0, 0]),
    "口干喜冷": ("问诊.饮食口味.口干喜冷", [0, 0.05, 0, 0, -0.08]),
    "口干不欲饮": ("问诊.饮食口味.口干不欲饮", [0, 0, -0.05, 0, 0.05]),
    "口渴": ("问诊.饮食口味.口干喜冷", [0, 0.05, 0, 0, -0.05]),
    "便秘": ("问诊.二便.大便秘结", [0, 0.05, 0, 0, -0.05]),
    "便溏": ("问诊.二便.大便稀溏", [0, 0, -0.08, 0, 0.05]),
    "泄泻": ("问诊.二便.大便稀溏", [0, 0, -0.08, 0, 0.05]),
    "小便黄": ("问诊.二便.小便黄赤", [0, 0.05, 0, 0, -0.03]),
    "小便清长": ("问诊.二便.小便清长", [0, -0.05, 0, 0, 0.05]),
    "夜尿频多": ("问诊.二便.夜尿频多", [0, -0.08, 0, 0, 0.05]),
    "夜尿": ("问诊.二便.夜尿频多", [0, -0.05, 0, 0, 0.05]),
    "失眠": ("问诊.睡眠.失眠多梦", [0.03, 0.08, 0, 0, -0.05]),
    "不寐": ("问诊.睡眠.失眠多梦", [0.03, 0.08, 0, 0, -0.05]),
    "多梦": ("问诊.睡眠.失眠多梦", [0.02, 0.05, 0, 0, -0.03]),
    "嗜睡": ("问诊.睡眠.嗜睡", [0, 0, -0.05, 0, 0.08]),
    "困倦": ("问诊.睡眠.嗜睡", [0, 0, -0.03, 0, 0.05]),
    "自汗": ("问诊.汗出.自汗", [0, 0, -0.05, -0.05, 0]),
    "盗汗": ("问诊.汗出.盗汗", [0, 0.05, 0, 0, -0.10]),
    "月经先期": ("问诊.经带.经行先期", [0, 0.08, 0, 0, -0.05]),
    "月经后期": ("问诊.经带.经行后期", [0, -0.03, 0, 0, 0.05]),
    "带下黄": ("问诊.经带.带下黄稠", [0, 0.03, -0.05, 0, 0.05]),
    "耳鸣": ("问诊.疼痛.头痛", [0.03, 0.05, 0, 0, -0.05]),
    "腰酸": ("问诊.疼痛.胃脘痛", [0, 0, 0, 0, -0.08]),
    "腰膝酸软": ("问诊.疼痛.胃脘痛", [0, 0, 0, 0, -0.10]),
    "乏力": ("问诊.饮食口味.食欲减退", [0, 0, -0.05, -0.05, 0]),
    "神疲": ("问诊.饮食口味.食欲减退", [0, 0, -0.05, 0, 0]),
    "咳嗽": ("闻诊.声音.咳声重浊", [0, 0, 0, 0.05, 0]),
    "痰多": ("闻诊.声音.喉中痰鸣", [0, 0, -0.05, -0.03, 0]),
    "胸闷": ("问诊.疼痛.胁痛", [0.03, 0, -0.03, 0, 0]),
    "心悸": ("问诊.睡眠.失眠多梦", [0, 0.05, 0, 0, -0.03]),
    "水肿": ("问诊.二便.大便稀溏", [0, 0, -0.05, 0, 0.08]),
}

CONSTITUTION_BASELINE = {
    "平和质": [0.20, 0.20, 0.20, 0.20, 0.20],
    "气郁质": [0.35, 0.15, 0.15, 0.20, 0.15],
    "木旺质": [0.35, 0.20, 0.15, 0.15, 0.15],
    "火旺质": [0.20, 0.35, 0.20, 0.10, 0.15],
    "土虚质": [0.20, 0.15, 0.10, 0.25, 0.30],
    "金虚质": [0.25, 0.15, 0.25, 0.10, 0.25],
    "水虚质": [0.30, 0.20, 0.20, 0.20, 0.10],
    "阳虚质": [0.25, 0.25, 0.20, 0.15, 0.15],
    "阴虚质": [0.30, 0.25, 0.15, 0.15, 0.15],
    "痰湿质": [0.15, 0.15, 0.30, 0.20, 0.20],
    "湿热质": [0.20, 0.25, 0.25, 0.15, 0.15],
    "血瘀质": [0.25, 0.20, 0.20, 0.15, 0.20]
}

DEFAULT_SIXIANG = {
    "enabled": True,
    "phases": [
        {"name": "少阳", "duration": 5, "gain": {"木": 1.5, "火": 1.2, "土": 1.0, "金": 1.0, "水": 1.0}},
        {"name": "太阳", "duration": 5, "gain": {"木": 1.0, "火": 2.0, "土": 1.0, "金": 0.5, "水": 1.0}},
        {"name": "少阴", "duration": 5, "gain": {"木": 1.0, "火": 1.0, "土": 1.0, "金": 1.5, "水": 1.2}},
        {"name": "太阴", "duration": 5, "gain": {"木": 0.5, "火": 1.0, "土": 1.0, "金": 1.0, "水": 2.0}}
    ]
}

def extract_symptoms_from_text(text: str) -> Dict[str, List]:
    found = []
    for keyword, (path, _) in SYMPTOM_KEYWORDS.items():
        if keyword in text:
            found.append(path)
    classified = {"望诊": [], "闻诊": [], "问诊": [], "切诊": []}
    for path in found:
        exam = path.split('.')[0]
        if path not in classified[exam]:
            classified[exam].append(path)
    return classified

def symptoms_to_vector(text: str) -> List[float]:
    """将一段症状文本转换为五行扰动向量的累计"""
    vector = [0.0]*5
    classified = extract_symptoms_from_text(text)
    for exam, syms in classified.items():
        for s in syms:
            for keyword, (path, vec) in SYMPTOM_KEYWORDS.items():
                if path == s:
                    for i in range(5):
                        vector[i] += vec[i]
                    break
    return vector

def compute_initial_energy(constitution: str, symptoms_text: str,
                           base_offset: Optional[List[float]] = None) -> List[float]:
    base = copy.deepcopy(CONSTITUTION_BASELINE.get(constitution, [0.2]*5))
    if base_offset:
        for i in range(5):
            base[i] += base_offset[i]
    vec = symptoms_to_vector(symptoms_text)
    for i in range(5):
        base[i] += vec[i]
    return [max(0.05, min(0.95, x)) for x in base]

def trend_to_range(trend: str, element_idx: int, current_state: Optional[float] = None) -> Tuple[float, float]:
    """根据趋势词返回能量的大致区间 (low, high)"""
    # 默认范围
    if trend == 'high':
        return (0.55, 0.95)
    elif trend == 'low':
        return (0.05, 0.2)
    elif trend == 'normal':
        return (0.2, 0.35)
    elif trend == 'rising':
        # 希望比某个参考值上升，如果没有参考则给一个较宽的范围
        return (0.3, 0.7)  # 只要不极端
    elif trend == 'declining':
        return (0.1, 0.4)
    elif trend == 'suppressed':
        return (0.01, 0.15)
    elif trend == 'recovering':
        return (0.15, 0.3)
    elif trend == 'stabilizing':
        return (0.15, 0.35)
    else:
        return (0.1, 0.5)  # 宽泛

def auto_targets_from_stages(stages: List[Dict], total_steps: int) -> List[Dict]:
    """根据医案阶段描述自动生成优化目标列表"""
    targets = []
    for stage in stages:
        try:
            start, end = stage['step_range']
            symptoms = stage.get('symptoms', '')
            trends = stage.get('expected_trends', {})
            # 使用阶段末尾步作为目标步
            target_step = min(end, total_steps-1)
            if target_step < 0:
                continue
            expect = {}
            # 从症状文本推断大致能量范围？
            # 这里简单根据 trends 设定区间
            for elem, trend in trends.items():
                idx = {'木':0,'火':1,'土':2,'金':3,'水':4}[elem]
                low, high = trend_to_range(trend, idx)
                expect[elem] = (low, high)
            if expect:
                targets.append({"step": target_step, "expect": expect})
        except (KeyError, ValueError):
            pass
    return targets

def run_real_evolution(engine_params, initial_energy, total_steps, default_pulse,
                       interventions=None, clock_enabled=True):
    if not ENGINE_AVAILABLE:
        history = [[initial_energy[i] + random.uniform(-0.02, 0.02) for i in range(5)]
                   for _ in range(total_steps+1)]
        return history, history[-1]
    engine = FourDiagnosisEngine('presets/default_faction.json')
    engine.sheng_coeff = engine_params['sheng_coeff']
    engine.ke_coeff = engine_params['ke_coeff']
    engine.decay = engine_params['decay']
    engine.base_inject_energy = engine_params['inject_energy']
    engine.use_clock_modulation = clock_enabled
    engine.initial_energy = initial_energy.copy()
    engine.history = [initial_energy.copy()]
    engine.output_sequence = []
    engine.clock.reset()
    engine.random_fluctuation = 0.0
    engine.homeostasis_strength = 0.0
    for step in range(total_steps):
        if interventions and step in interventions:
            inter = interventions[step]
            if inter['type'] == 'herb':
                engine.inject_vector(inter['vector'])
            elif inter['type'] == 'emotion':
                engine.inject_event(inter['event'], inter.get('vector', [0]*5))
        engine.step(default_pulse)
    return engine.history, engine.get_state()

def calculate_energy_deviation(history, targets):
    deviation = 0.0
    for target in targets:
        step = target['step']
        expect = target['expect']
        if step >= len(history):
            return float('inf')
        state = history[step]
        for elem, (low, high) in expect.items():
            idx = {'木':0,'火':1,'土':2,'金':3,'水':4}[elem]
            val = state[idx]
            if val < low:
                deviation += (low - val) ** 2
            elif val > high:
                deviation += (val - high) ** 2
    return deviation

def random_search(initial_energy, total_steps, targets, default_pulse='木', iterations=200):
    param_space = {
        'sheng_coeff': (0.02, 0.12),
        'ke_coeff': (0.01, 0.10),
        'decay': (0.80, 0.98),
        'inject_energy': (0.05, 0.30)
    }
    best_params = None
    best_error = float('inf')
    for i in range(iterations):
        params = {k: random.uniform(v[0], v[1]) for k, v in param_space.items()}
        history, _ = run_real_evolution(params, initial_energy, total_steps, default_pulse)
        error = calculate_energy_deviation(history, targets)
        if error < best_error:
            best_error = error
            best_params = params
    return best_params, best_error

def generate_config(best_params, initial_energy, total_steps, faction_name, description):
    return {
        "faction_name": faction_name,
        "version": "0.1",
        "description": description,
        "engine_params": {
            "sheng_coeff": best_params['sheng_coeff'],
            "ke_coeff": best_params['ke_coeff'],
            "decay": best_params['decay'],
            "inject_energy": best_params['inject_energy'],
            "homeostasis": 0.0,
            "fluctuation": 0.0,
            "use_clock": True
        },
        "sixiang_clock": DEFAULT_SIXIANG,
        "constitution_baseline": {"自动校准": initial_energy},
        "diagnosis_weights": {"望诊":0.25,"闻诊":0.25,"问诊":0.25,"切诊":0.25},
        "symptom_mapping": {},
        "interaction_rules": [],
        "eight_principles_rules": {},
        "zangfu_rules": {},
        "six_meridian_rules": {}
    }

def main():
    parser = argparse.ArgumentParser(description="参数自动校准器")
    parser.add_argument('--case', type=str, help='医案目标文件 (JSON)')
    args = parser.parse_args()

    if args.case:
        # 文件模式
        with open(args.case, 'r', encoding='utf-8') as f:
            case = json.load(f)
        faction_name = case.get('case_name', os.path.splitext(os.path.basename(args.case))[0])
        description = f"根据医案文件 {args.case} 自动校准"
        constitution = case.get('constitution', '平和质')
        total_steps = case.get('total_steps', 30)
        default_pulse = case.get('default_pulse', '木')
        stages = case.get('stages', [])

        # 初始症状使用第一个阶段症状
        initial_symptoms = stages[0].get('symptoms', '') if stages else ''
        initial_energy = compute_initial_energy(constitution, initial_symptoms)
        targets = auto_targets_from_stages(stages, total_steps)

        if not targets:
            print("警告：未能从医案阶段中生成能量目标，将使用默认参数。")
            best_params = {'sheng_coeff': 0.05, 'ke_coeff': 0.03, 'decay': 0.92, 'inject_energy': 0.15}
        else:
            print("正在自动校准（使用真实引擎）..." if ENGINE_AVAILABLE else "引擎未找到，使用演示模拟...")
            best_params, error = random_search(initial_energy, total_steps, targets, default_pulse, iterations=200)
            print(f"最佳参数: {best_params}")
            print(f"误差: {error:.4f}")
    else:
        # 交互模式
        print("=" * 60)
        print("  参数自动校准器（交互模式）")
        faction_name = input("流派名称: ").strip() or "自动校准"
        constitution = input("体质 (如 气郁质): ").strip() or "平和质"
        symptoms_text = input("初始症状描述: ").strip()
        total_steps = int(input("总步数: ").strip() or "30")
        default_pulse = input("主脉象 (默认 木): ").strip() or "木"
        print("\n输入关键步骤的能量目标（直接回车结束）")
        targets = []
        while True:
            step_str = input("步数: ").strip()
            if not step_str:
                break
            step = int(step_str)
            expect = {}
            print("输入五行能量的最小最大值（如 木 0.5 0.7），每行一个，空行结束")
            while True:
                line = input().strip()
                if not line:
                    break
                parts = line.split()
                if len(parts) == 3:
                    elem, low, high = parts[0], float(parts[1]), float(parts[2])
                    expect[elem] = (low, high)
            if expect:
                targets.append({"step": step, "expect": expect})
        initial_energy = compute_initial_energy(constitution, symptoms_text)
        description = "手动校准的配置"
        if targets:
            best_params, error = random_search(initial_energy, total_steps, targets, default_pulse, iterations=200)
            print(f"最佳参数: {best_params}")
            print(f"误差: {error:.4f}")
        else:
            print("未输入目标，将使用默认参数。")
            best_params = {'sheng_coeff': 0.05, 'ke_coeff': 0.03, 'decay': 0.92, 'inject_energy': 0.15}

    config = generate_config(best_params, initial_energy, total_steps, faction_name, description)
    filename = f"{faction_name}_calibrated.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"配置文件已保存至 {filename}")
    print("可放入 presets/ 目录后，在四诊合参模拟器中加载。")

if __name__ == '__main__':
    main()
