import streamlit as st
import json
import random
import copy
import os
from typing import Dict, List

# 尝试导入引擎，但不强制
try:
    from meihua.four_diagnosis_engine import FourDiagnosisEngine
    ENGINE_OK = True
except ImportError:
    ENGINE_OK = False

# ========== 症状关键词库 ==========
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

# 中文趋势词映射
TREND_MAP = {
    "偏高": "high",
    "偏低": "low",
    "正常": "normal",
    "上升中": "rising",
    "下降中": "declining",
    "被克制": "suppressed",
    "恢复中": "recovering",
    "稳定": "stabilizing"
}

def trend_to_range(trend_cn: str):
    english = TREND_MAP.get(trend_cn, "normal")
    ranges = {
        "high": (0.55, 0.95),
        "low": (0.05, 0.2),
        "normal": (0.2, 0.35),
        "rising": (0.3, 0.7),
        "declining": (0.1, 0.4),
        "suppressed": (0.01, 0.15),
        "recovering": (0.15, 0.3),
        "stabilizing": (0.15, 0.35)
    }
    return ranges.get(english, (0.1, 0.5))

def symptoms_to_vector(text):
    vec = [0.0]*5
    for keyword, (path, v) in SYMPTOM_KEYWORDS.items():
        if keyword in text:
            for i in range(5):
                vec[i] += v[i]
    return vec

def compute_initial_energy(constitution, symptoms_text):
    base = CONSTITUTION_BASELINE.get(constitution, [0.2]*5)[:]
    vec = symptoms_to_vector(symptoms_text)
    for i in range(5):
        base[i] += vec[i]
    return [max(0.05, min(0.95, x)) for x in base]

def generate_targets_from_stages(stages, total_steps):
    targets = []
    for stage in stages:
        try:
            start, end = stage["step_range"]
            step = min(end, total_steps-1)
            if step < 0:
                continue
            trends = stage.get("expected_trends", {})
            expect = {}
            for elem in ["木","火","土","金","水"]:
                trend = trends.get(elem, "正常")
                low, high = trend_to_range(trend)
                expect[elem] = (low, high)
            targets.append({"step": step, "expect": expect})
        except Exception as e:
            st.warning(f"阶段 {stage.get('name','')} 格式有误: {e}")
    return targets

def run_real_evolution(params, initial_energy, total_steps, default_pulse):
    if not ENGINE_OK:
        return [[initial_energy[i] + random.uniform(-0.02,0.02) for i in range(5)] for _ in range(total_steps+1)], None
    engine = FourDiagnosisEngine('presets/default_faction.json')
    engine.sheng_coeff = params['sheng_coeff']
    engine.ke_coeff = params['ke_coeff']
    engine.decay = params['decay']
    engine.base_inject_energy = params['inject_energy']
    engine.use_clock_modulation = True
    engine.initial_energy = initial_energy.copy()
    engine.history = [initial_energy.copy()]
    engine.output_sequence = []
    engine.clock.reset()
    engine.random_fluctuation = 0.0
    engine.homeostasis_strength = 0.0
    for _ in range(total_steps):
        engine.step(default_pulse)
    return engine.history, engine.get_state()

def calc_deviation(history, targets):
    dev = 0.0
    for t in targets:
        step = t["step"]
        if step >= len(history):
            return float('inf')
        state = history[step]
        for elem, (low, high) in t["expect"].items():
            idx = {'木':0,'火':1,'土':2,'金':3,'水':4}[elem]
            val = state[idx]
            if val < low: dev += (low-val)**2
            elif val > high: dev += (val-high)**2
    return dev

def random_search(initial_energy, total_steps, targets, default_pulse='木', iterations=120):
    param_space = {
        'sheng_coeff': (0.02, 0.12),
        'ke_coeff': (0.01, 0.10),
        'decay': (0.80, 0.98),
        'inject_energy': (0.05, 0.30)
    }
    best = None
    best_err = float('inf')
    for _ in range(iterations):
        params = {k: random.uniform(*param_space[k]) for k in param_space}
        hist, _ = run_real_evolution(params, initial_energy, total_steps, default_pulse)
        if not hist:
            continue
        err = calc_deviation(hist, targets)
        if err < best_err:
            best_err = err
            best = params
    return best, best_err

def make_config(best_params, initial_energy, total_steps, faction_name, description):
    return {
        "faction_name": faction_name,
        "version": "0.1",
        "description": description,
        "engine_params": {
            "sheng_coeff": best_params['sheng_coeff'],
            "ke_coeff": best_params['ke_coeff'],
            "decay": best_params['decay'],
            "inject_energy": best_params['inject_energy'],
            "homeostasis": 0.0, "fluctuation": 0.0, "use_clock": True
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

# ========== 界面 ==========
st.set_page_config(page_title="医案校准器", layout="wide")
st.title("📝 医案填写与自动校准")
st.caption("根据临床医案的阶段变化，自动搜索最佳推演参数，生成流派配置包。所有数值仅为教学参考，不可用于临床。")

constitution = st.selectbox("体质", list(CONSTITUTION_BASELINE.keys()))
case_name = st.text_input("医案名称", value="肝郁化火案")
total_steps = st.number_input("总推演步数（对应病程）", min_value=5, max_value=100, value=30)
default_pulse = st.selectbox("主脉象", ["木", "火", "土", "金", "水"])

st.subheader("病程阶段")
st.markdown("请根据复诊记录，添加至少一个阶段。每个阶段包含**症状描述**和**五行变化趋势**。")
num_stages = st.number_input("阶段数量", min_value=1, max_value=6, value=3)

stages = []
trend_options = list(TREND_MAP.keys())
elements = ["木", "火", "土", "金", "水"]

for i in range(num_stages):
    with st.expander(f"阶段 {i+1}", expanded=True):
        name = st.text_input("阶段名称", value=f"阶段{i+1}", key=f"sname_{i}")
        c1, c2 = st.columns(2)
        with c1:
            step_start = st.number_input("起始步数", min_value=0, max_value=total_steps-1, value=i*10, key=f"start_{i}")
        with c2:
            step_end = st.number_input("结束步数", min_value=step_start+1, max_value=total_steps, value=min((i+1)*10, total_steps), key=f"end_{i}")
        symptoms = st.text_area("症状描述", value="", key=f"sym_{i}", placeholder="例如：脉弦数，舌红，口苦，失眠")
        st.write("五行变化趋势（选择该阶段结束时各行的预期状态）：")
        cols = st.columns(5)
        trends = {}
        # 第一阶段默认偏高，其余默认正常
        default_trends = ['偏高', '正常', '正常', '正常', '正常'] if i == 0 else ['正常']*5
        for j, elem in enumerate(elements):
            with cols[j]:
                trends[elem] = st.selectbox(elem, trend_options, 
                                           index=trend_options.index(default_trends[j]),
                                           key=f"trend_{i}_{j}")
        stages.append({
            "name": name,
            "step_range": [step_start, step_end],
            "expected_trends": trends,
            "symptoms": symptoms
        })

if st.button("🔍 开始自动校准"):
    if not stages:
        st.error("请至少添加一个阶段。")
    else:
        targets = generate_targets_from_stages(stages, total_steps)
        if not targets:
            st.error("未能从阶段信息中生成有效的能量目标。请检查步数范围和趋势选择是否完整。")
        else:
            initial_energy = compute_initial_energy(constitution, stages[0].get("symptoms",""))
            if not ENGINE_OK:
                st.warning("未连接到真实推演引擎，校准将使用模拟数据，结果仅供参考。")
            with st.spinner("正在随机搜索最优参数，请稍候..."):
                best_params, error = random_search(initial_energy, total_steps, targets, default_pulse, iterations=150)
            if best_params is None:
                st.error("搜索失败，请稍后再试。")
            else:
                st.success(f"校准完成！最优参数组合如下，误差值：{error:.4f}")
                st.json(best_params)
                config = make_config(best_params, initial_energy, total_steps, case_name, "由UI校准生成")
                st.download_button(
                    label="📥 下载校准配置包",
                    data=json.dumps(config, indent=2, ensure_ascii=False),
                    file_name=f"{case_name}_calibrated.json",
                    mime="application/json"
                )
