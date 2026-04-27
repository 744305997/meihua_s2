import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import glob
from meihua.four_diagnosis_engine import FourDiagnosisEngine
from meihua.herb import HERB_LIBRARY
from datetime import datetime

# 设置中文字体，确保图例正常显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="四诊合参模拟器 · 二阶段原型", layout="wide")

# ---------- 全局常量 ----------
wuxing_names = ['木', '火', '土', '金', '水']
colors = ['green', 'red', 'orange', 'gray', 'black']

@st.cache_resource
def load_config(faction='default'):
    path = f'presets/{faction}_faction.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            "faction_name": faction,
            "symptom_mapping": {},
            "sixiang_clock": {"enabled": True, "phases": []},
            "constitution_baseline": {"平和质": [0.2]*5},
            "diagnosis_weights": {"望诊": 0.25, "闻诊": 0.25, "问诊": 0.25, "切诊": 0.25},
            "interaction_rules": [],
            "eight_principles_rules": {},
            "zangfu_rules": {},
            "six_meridian_rules": {},
            "engine_params": {"sheng_coeff": 0.05, "ke_coeff": 0.03, "decay": 0.92, "inject_energy": 0.15, "homeostasis": 0.0, "fluctuation": 0.0}
        }

# 扫描可用流派
faction_files = glob.glob('presets/*_faction.json')
available_factions = [os.path.basename(f).replace('_faction.json', '') for f in faction_files]
if not available_factions:
    available_factions = ['default']

if 'faction' not in st.session_state:
    st.session_state.faction = 'default'
config = load_config(st.session_state.faction)

if 'engine' not in st.session_state:
    st.session_state.engine = FourDiagnosisEngine(f'presets/{st.session_state.faction}_faction.json')
engine = st.session_state.engine

# ========== 侧边栏 ==========
with st.sidebar:
    st.header("📋 流派与体质")
    faction_names = available_factions
    current_faction = st.selectbox("当前流派", faction_names, index=faction_names.index(st.session_state.faction) if st.session_state.faction in faction_names else 0)
    if current_faction != st.session_state.faction:
        st.session_state.faction = current_faction
        engine.load_config(f'presets/{current_faction}_faction.json')
        st.rerun()

    constitution = st.selectbox("体质", 
        ["平和质","木旺质","火旺质","土虚质","金虚质","水虚质",
         "阳虚质","阴虚质","痰湿质","湿热质","血瘀质","气郁质"])
    age = st.slider("年龄", 0, 100, 35)
    gender = st.selectbox("性别", ["男","女"])

    st.header("⚙️ 引擎参数")
    sheng_coeff = st.slider("相生系数", 0.01, 0.2, engine.sheng_coeff, 0.01)
    ke_coeff = st.slider("相克系数", 0.01, 0.2, engine.ke_coeff, 0.01)
    decay = st.slider("衰减因子", 0.8, 1.0, engine.decay, 0.01)
    inject_energy = st.slider("灌注能量", 0.05, 0.5, engine.base_inject_energy, 0.01)
    use_clock = st.checkbox("四象时钟", value=True)

    engine.sheng_coeff = sheng_coeff
    engine.ke_coeff = ke_coeff
    engine.decay = decay
    engine.base_inject_energy = inject_energy
    engine.use_clock_modulation = use_clock

    if use_clock:
        st.subheader("四象时钟手动覆写")
        override_clock = st.checkbox("启用手动覆写", value=False)
        if override_clock:
            phases = config.get('sixiang_clock', {}).get('phases', [])
            combinations = []
            for phase in phases:
                enabled = st.checkbox(phase['name'], value=False)
                if enabled:
                    weight = st.slider(f"{phase['name']}权重", 0.0, 2.0, 1.0, 0.1)
                    combinations.append({"phase": phase['name'], "weight": weight})
            if combinations:
                engine.custom_sixiang = {'mode': 'manual', 'combinations': combinations}
            else:
                engine.custom_sixiang = None
        else:
            engine.custom_sixiang = None

    st.header("⏱️ 演化步数")
    total_steps = st.number_input("总步数", min_value=1, max_value=100, value=20)
    use_plan = st.checkbox("启用步骤计划（高级）", value=False)

    # 导出导入
    st.markdown("---")
    st.subheader("📦 配置包管理")
    export_data = engine.export_config()
    st.download_button(
        label="📥 导出当前流派配置",
        data=export_data,
        file_name=f"{st.session_state.faction}_faction.json",
        mime="application/json"
    )
    uploaded_file = st.file_uploader("📤 导入流派配置", type=['json'])
    if uploaded_file is not None:
        try:
            imported = json.load(uploaded_file)
            engine.import_config(uploaded_file.getvalue().decode('utf-8'))
            new_faction = imported.get('faction_name', 'imported')
            save_path = f'presets/{new_faction}_faction.json'
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(uploaded_file.getvalue().decode('utf-8'))
            st.success(f"配置包已导入为「{new_faction}」")
            st.rerun()
        except Exception as e:
            st.error(f"导入失败：{e}")

    # 医案保存/加载
    st.markdown("---")
    st.subheader("📋 医案存档")

    # 始终构建医案数据并显示导出按钮
    case_data = {
        'faction': st.session_state.faction,
        'constitution': constitution,
        'age': age,
        'gender': gender,
        'selected_symptoms': selected if 'selected' in dir() else {},
        'engine_params': {
            'sheng_coeff': sheng_coeff,
            'ke_coeff': ke_coeff,
            'decay': decay,
            'inject_energy': inject_energy,
            'use_clock': use_clock,
            'diagnosis_weights': engine.config.get('diagnosis_weights', {}),
            'total_steps': total_steps,
            'step_patches': st.session_state.get('step_patches', {})
        }
    }
    st.download_button("📥 导出当前医案", data=json.dumps(case_data, indent=2, ensure_ascii=False), file_name="case.json")

    uploaded_case = st.file_uploader("📤 加载医案文件", type=['json'], key='case_upload')
    if uploaded_case:
        try:
            case = json.load(uploaded_case)
            st.session_state.faction = case.get('faction', 'default')
            engine.load_config(f'presets/{st.session_state.faction}_faction.json')
            constitution = case.get('constitution', '平和质')
            age = case.get('age', 35)
            gender = case.get('gender', '男')
            selected = case.get('selected_symptoms', {})
            params = case.get('engine_params', {})
            for k, v in params.items():
                if k != 'step_patches' and hasattr(engine, k):
                    setattr(engine, k, v)
            st.success("医案已加载，参数已同步。请手动调整其余设置后推演。")
        except Exception as e:
            st.error(f"医案加载失败：{e}")

# ========== 主界面 ==========
st.title("🩺 四诊合参模拟器")
st.markdown("基于中医五行生克理论的四诊合参辨证推演平台 —— 仅供教学参考，不可用于临床诊断")

# ---------- 四诊面板 ----------
st.header("🌡️ 四诊信息采集")
col1, col2 = st.columns(2)

with col1:
    with st.expander("望诊", expanded=True):
        tongue_body = st.selectbox("舌质", [""] + list(config.get('symptom_mapping', {}).get('望诊', {}).get('舌象', {}).get('舌质', {}).keys()))
        tongue_coat = st.selectbox("舌苔", [""] + list(config.get('symptom_mapping', {}).get('望诊', {}).get('舌象', {}).get('舌苔', {}).keys()))
        face = st.selectbox("面色", [""] + list(config.get('symptom_mapping', {}).get('望诊', {}).get('面色', {}).keys()))
        body_shape = st.selectbox("形体", [""] + list(config.get('symptom_mapping', {}).get('望诊', {}).get('形体', {}).keys()))
    with st.expander("闻诊"):
        voice = st.selectbox("声音", [""] + list(config.get('symptom_mapping', {}).get('闻诊', {}).get('声音', {}).keys()))
        smell = st.selectbox("气味", [""] + list(config.get('symptom_mapping', {}).get('闻诊', {}).get('气味', {}).keys()))
    with st.expander("切诊"):
        pulse = st.selectbox("脉象", [""] + list(config.get('symptom_mapping', {}).get('切诊', {}).get('脉象', {}).keys()))

with col2:
    with st.expander("问诊（十问歌）"):
        cold_heat = st.radio("寒热", list(config.get('symptom_mapping', {}).get('问诊', {}).get('寒热', {}).keys()), index=0)
        pain_opts = st.multiselect("疼痛（可多选）", list(config.get('symptom_mapping', {}).get('问诊', {}).get('疼痛', {}).keys()))
        diet_opts = st.multiselect("饮食口味", list(config.get('symptom_mapping', {}).get('问诊', {}).get('饮食口味', {}).keys()))
        stool_opts = st.multiselect("二便", list(config.get('symptom_mapping', {}).get('问诊', {}).get('二便', {}).keys()))
        sleep_opts = st.multiselect("睡眠", list(config.get('symptom_mapping', {}).get('问诊', {}).get('睡眠', {}).keys()))
        sweat_opts = st.multiselect("汗出", list(config.get('symptom_mapping', {}).get('问诊', {}).get('汗出', {}).keys()))
        menstrual_opts = st.multiselect("经带（女性）", list(config.get('symptom_mapping', {}).get('问诊', {}).get('经带', {}).keys()))

# 构建选取症状
selected = {'望诊': [], '闻诊': [], '问诊': [], '切诊': []}
if tongue_body: selected['望诊'].append(f"舌象.舌质.{tongue_body}")
if tongue_coat: selected['望诊'].append(f"舌象.舌苔.{tongue_coat}")
if face: selected['望诊'].append(f"面色.{face}")
if body_shape: selected['望诊'].append(f"形体.{body_shape}")
if voice: selected['闻诊'].append(f"声音.{voice}")
if smell: selected['闻诊'].append(f"气味.{smell}")
if pulse: selected['切诊'].append(f"脉象.{pulse}")
selected['问诊'].append(f"寒热.{cold_heat}")
for p in pain_opts: selected['问诊'].append(f"疼痛.{p}")
for d in diet_opts: selected['问诊'].append(f"饮食口味.{d}")
for s in stool_opts: selected['问诊'].append(f"二便.{s}")
for s in sleep_opts: selected['问诊'].append(f"睡眠.{s}")
for s in sweat_opts: selected['问诊'].append(f"汗出.{s}")
for s in menstrual_opts: selected['问诊'].append(f"经带.{s}")

# ---------- 四诊权重 ----------
st.subheader("⚖️ 四诊权重调节")
col_w = st.columns(4)
weights = {}
with col_w[0]:
    weights['望诊'] = st.slider("望诊", 0.0, 1.0, engine.config.get('diagnosis_weights', {}).get('望诊', 0.25), 0.05)
with col_w[1]:
    weights['闻诊'] = st.slider("闻诊", 0.0, 1.0, engine.config.get('diagnosis_weights', {}).get('闻诊', 0.25), 0.05)
with col_w[2]:
    weights['问诊'] = st.slider("问诊", 0.0, 1.0, engine.config.get('diagnosis_weights', {}).get('问诊', 0.25), 0.05)
with col_w[3]:
    weights['切诊'] = st.slider("切诊", 0.0, 1.0, engine.config.get('diagnosis_weights', {}).get('切诊', 0.25), 0.05)
engine.config['diagnosis_weights'] = weights

# ---------- 交互规则编辑器（勾链器） ----------
with st.expander("🔗 交互规则编辑器（勾链器）"):
    st.markdown("**当前流派交互规则**")
    rules = engine.get_interaction_rules()
    if rules:
        for idx, rule in enumerate(rules):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{rule.get('name', '未命名')}**")
            with col2:
                st.write(f"触发：{rule.get('trigger', {}).get('symptoms', [])}")
            with col3:
                if st.button("删除", key=f"del_rule_{idx}"):
                    rules.pop(idx)
                    engine.update_interaction_rules(rules)
                    st.rerun()
    else:
        st.write("暂无交互规则")
    st.markdown("---")
    st.markdown("**添加新规则**")

    # 复用递归函数生成症状列表
    def get_all_symptom_paths(mapping, prefix=''):
        paths = []
        for key, value in mapping.items():
            current_path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and any(isinstance(v, (list, dict)) for v in value.values()):
                paths.extend(get_all_symptom_paths(value, current_path))
            elif isinstance(value, list) and len(value) == 5:
                paths.append(current_path)
        return paths

    all_symptoms = get_all_symptom_paths(config.get('symptom_mapping', {}))

    # 会话状态暂存新规则参数
    if 'new_rule' not in st.session_state:
        st.session_state.new_rule = {
            'name': '',
            'trigger_symptoms': [],
            'logic': 'AND',
            'effect_type': 'multiply',
            'factor': 1.3,
            'vector': [0.0]*5,
            'target_symptoms': []
        }

    nr = st.session_state.new_rule

    # 中英文映射
    logic_map = {'AND': 'AND（全部满足）', 'OR': 'OR（任一满足）', 'SINGLE': 'SINGLE（单一症状）'}
    effect_map = {'multiply': '倍数增强', 'append_vector': '追加扰动量', 'override': '覆盖替换'}
    reverse_effect_map = {v: k for k, v in effect_map.items()}

    rule_name = st.text_input("规则名称", value=nr['name'], key='rule_name_input')
    trigger_symptoms = st.multiselect("触发症状（可多选）", all_symptoms, default=nr['trigger_symptoms'], key='trigger_symptoms_select')
    
    logic_label = logic_map.get(nr.get('logic', 'AND'), logic_map['AND'])
    logic_choice = st.selectbox("触发逻辑", list(logic_map.values()), index=list(logic_map.values()).index(logic_label), key='logic_select')
    logic = list(logic_map.keys())[list(logic_map.values()).index(logic_choice)]

    effect_label = effect_map.get(nr.get('effect_type', 'multiply'), '倍数增强')
    effect_choice = st.selectbox("效果类型", list(effect_map.values()), index=list(effect_map.values()).index(effect_label), key='effect_type_select')
    effect_type = reverse_effect_map[effect_choice]

    factor = None
    vector = None
    target_symptoms = trigger_symptoms

    if effect_type == 'multiply':
        factor = st.number_input("增强倍数", min_value=0.1, max_value=5.0, value=float(nr.get('factor', 1.3)), step=0.1, key='factor_input')
    elif effect_type == 'append_vector':
        st.write("追加的五行扰动量：")
        cols = st.columns(5)
        vec = [0.0]*5
        for i, name in enumerate(wuxing_names):
            with cols[i]:
                vec[i] = st.number_input(name, value=float(nr.get('vector', [0.0]*5)[i]), step=0.01, key=f'append_vec_{i}')
        vector = vec
    elif effect_type == 'override':
        target_symptoms = st.multiselect("覆盖的目标症状", trigger_symptoms, default=nr.get('target_symptoms', []), key='override_target_select')
        st.write("覆盖后的五行扰动量：")
        cols = st.columns(5)
        vec = [0.0]*5
        for i, name in enumerate(wuxing_names):
            with cols[i]:
                vec[i] = st.number_input(name, value=float(nr.get('vector', [0.0]*5)[i]), step=0.01, key=f'override_vec_{i}')
        vector = vec

    # 更新会话状态
    st.session_state.new_rule = {
        'name': rule_name,
        'trigger_symptoms': trigger_symptoms,
        'logic': logic,
        'effect_type': effect_type,
        'factor': factor if factor is not None else 1.3,
        'vector': vector if vector is not None else [0.0]*5,
        'target_symptoms': target_symptoms
    }

    if st.button("✅ 确认添加规则"):
        if not rule_name:
            st.error("请填写规则名称")
        elif not trigger_symptoms:
            st.error("请至少选择一个触发症状")
        else:
            new_rule_obj = {
                "name": rule_name,
                "trigger": {"symptoms": trigger_symptoms, "logic": logic},
                "effect": {"type": effect_type}
            }
            if effect_type == 'multiply':
                new_rule_obj["effect"]["factor"] = factor
                new_rule_obj["effect"]["target_symptoms"] = trigger_symptoms
            elif effect_type == 'append_vector':
                new_rule_obj["effect"]["vector"] = vector
            elif effect_type == 'override':
                new_rule_obj["effect"]["vector"] = vector
                new_rule_obj["effect"]["target_symptoms"] = target_symptoms

            rules.append(new_rule_obj)
            engine.update_interaction_rules(rules)
            # 清空
            st.session_state.new_rule = {
                'name': '',
                'trigger_symptoms': [],
                'logic': 'AND',
                'effect_type': 'multiply',
                'factor': 1.3,
                'vector': [0.0]*5,
                'target_symptoms': []
            }
            st.success("规则已添加")
            st.rerun()
            
# ---------- 症状-五行映射编辑器 ----------
with st.expander("🎛️ 症状-五行映射编辑器"):
    st.caption("修改当前流派对每个症状的五行扰动值。")
    
    def get_all_symptom_paths(mapping, prefix=''):
        """递归遍历 symptom_mapping，返回所有叶子节点的完整路径"""
        paths = []
        for key, value in mapping.items():
            current_path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and any(isinstance(v, (list, dict)) for v in value.values()):
                paths.extend(get_all_symptom_paths(value, current_path))
            elif isinstance(value, list) and len(value) == 5:
                paths.append(current_path)
        return paths

    all_symptoms_list = get_all_symptom_paths(config.get('symptom_mapping', {}))
    
    if all_symptoms_list:
        selected_symptom_path = st.selectbox("选择要编辑的症状", all_symptoms_list)
        if selected_symptom_path:
            # 直接从引擎读取映射值（引擎已正确加载配置）
            current_vector = engine.map_symptom(selected_symptom_path)
            
            # 如果 map_symptom 仍返回全零，可能是症状路径不匹配，回退到直接读取配置
            if all(v == 0.0 for v in current_vector):
                keys = selected_symptom_path.split('.')
                mapping = config.get('symptom_mapping', {})
                for key in keys:
                    if isinstance(mapping, dict):
                        mapping = mapping.get(key, {})
                    else:
                        mapping = {}
                if isinstance(mapping, dict) and '木' in mapping:
                    current_vector = [mapping.get('木', 0), mapping.get('火', 0), mapping.get('土', 0), mapping.get('金', 0), mapping.get('水', 0)]
            
            cols = st.columns(5)
            new_vector = [0.0] * 5
            for i, name in enumerate(wuxing_names):
                with cols[i]:
                    new_vector[i] = st.number_input(
                        f"{name}",
                        min_value=-1.0, max_value=1.0,
                        value=float(current_vector[i]),
                        step=0.01,
                        key=f"edit_{selected_symptom_path}_{name}"
                    )
            if st.button("💾 保存修改"):
                keys = selected_symptom_path.split('.')
                mapping = engine.config['symptom_mapping']
                for key in keys[:-1]:
                    mapping = mapping.setdefault(key, {})
                mapping[keys[-1]] = {
                    '木': new_vector[0], '火': new_vector[1], '土': new_vector[2],
                    '金': new_vector[3], '水': new_vector[4]
                }
                st.success("映射已更新。")
    else:
        st.info("当前流派配置中尚未定义任何症状映射。请加载一个包含完整映射的流派，或手动添加症状。")

        # ---------- 步骤计划编辑器 ----------
if use_plan:
    st.header("📋 动态步骤计划")
    if 'step_patches' not in st.session_state:
        st.session_state.step_patches = {}
    for step in range(1, total_steps + 1):
        with st.expander(f"第 {step} 步", expanded=False):
            patch = st.session_state.step_patches.get(step, {})
            st.write("**五行扰动向量**")
            cols = st.columns(5)
            vec = patch.get('pulse_vector', [None]*5)
            new_vec = [0.0]*5
            for i, name in enumerate(wuxing_names):
                with cols[i]:
                    new_vec[i] = st.slider(f"{name}", -0.5, 0.5, float(vec[i]) if vec[i] is not None else 0.0, 0.01, key=f"step{step}_{name}")
            event = st.selectbox("情志冲击（可选）",
                ["无", "暴怒 (木+0.3,火+0.1,土-0.1)", "惊恐 (水+0.3,火-0.2)",
                 "思虑过度 (土+0.2,木-0.1,火-0.05)", "悲伤 (金+0.25,木-0.1)",
                 "大喜过望 (火+0.2,水-0.15)"],
                key=f"step{step}_event")
            if any(v != 0.0 for v in new_vec) or event != "无":
                new_patch = {'pulse_vector': new_vec}
                if event != "无": new_patch['event'] = event
                st.session_state.step_patches[step] = new_patch
            else:
                st.session_state.step_patches.pop(step, None)
else:
    if 'step_patches' in st.session_state:
        del st.session_state.step_patches

# ---------- 加载带功效的药剂列表 ----------
from meihua.herb import HERB_LIBRARY

herb_display_list = []
herb_display_to_name = {}
for name, (target, strength) in HERB_LIBRARY.items():
    act = '补' if strength > 0 else '泻'
    display = f"{name} ({act}{target} {strength:+.2f})"
    herb_display_list.append(display)
    herb_display_to_name[display] = name

# ---------- 脉象与药剂设置 ----------
st.header("🌊 脉象与药剂设置")

# 高级模式开关（控制次脉象等高级功能的显示）
use_advanced = st.checkbox("🪷 启用次脉象（复合脉象模拟）", value=False)

if use_advanced:
    col_pulse_main, col_pulse_sec = st.columns(2)
    with col_pulse_main:
        pulse_options = ['木 (弦脉)', '火 (洪脉)', '土 (缓脉)', '金 (浮脉)', '水 (沉脉)']
        default_pulse_display = pulse_options[0]
        if pulse and pulse in wuxing_names:
            for opt in pulse_options:
                if opt.startswith(pulse):
                    default_pulse_display = opt
                    break
        pulse_display = st.selectbox("主脉象", pulse_options, index=pulse_options.index(default_pulse_display))
        pulse_type = pulse_display.split(" ")[0]
        default_pulse = pulse_type

    with col_pulse_sec:
        sec_pulse_options = ['无'] + pulse_options
        sec_display = st.selectbox("次脉象", sec_pulse_options, index=0)
        if sec_display != '无':
            secondary_pulse = sec_display.split(" ")[0]
            secondary_strength = st.slider("次脉象强度", 0.1, 1.0, 0.5, 0.1, key='sec_strength_main')
        else:
            secondary_pulse = None
            secondary_strength = 0.0
else:
    # 未启用高级功能时，只显示主脉象
    pulse_options = ['木 (弦脉)', '火 (洪脉)', '土 (缓脉)', '金 (浮脉)', '水 (沉脉)']
    default_pulse_display = pulse_options[0]
    if pulse and pulse in wuxing_names:
        for opt in pulse_options:
            if opt.startswith(pulse):
                default_pulse_display = opt
                break
    pulse_display = st.selectbox("主脉象", pulse_options, index=pulse_options.index(default_pulse_display))
    pulse_type = pulse_display.split(" ")[0]
    default_pulse = pulse_type
    secondary_pulse = None
    secondary_strength = 0.0

# 药剂模式（与之前相同，略作调整以保留原有逻辑）
col_herb1, col_herb2 = st.columns([1, 3])
with col_herb1:
    herb_mode = st.radio("药剂模式", ["不使用药剂", "预设单味药", "自定义方剂向量"], index=0, horizontal=True)
herb_name = None
herb_dict = None
if herb_mode == "预设单味药":
    herb_display = st.selectbox("药剂", herb_display_list, key='herb_select_main')
    herb_name = herb_display_to_name[herb_display]
elif herb_mode == "自定义方剂向量":
    st.markdown("设定补泻值（正补负泻）")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        herb_mu = st.slider("木", -0.1, 0.1, 0.0, 0.01, key='herb_mu_main')
    with c2:
        herb_huo = st.slider("火", -0.1, 0.1, 0.0, 0.01, key='herb_huo_main')
    with c3:
        herb_tu = st.slider("土", -0.1, 0.1, 0.0, 0.01, key='herb_tu_main')
    with c4:
        herb_jin = st.slider("金", -0.1, 0.1, 0.0, 0.01, key='herb_jin_main')
    with c5:
        herb_shui = st.slider("水", -0.1, 0.1, 0.0, 0.01, key='herb_shui_main')
    herb_dict = {'木': herb_mu, '火': herb_huo, '土': herb_tu, '金': herb_jin, '水': herb_shui}

# ---------- 单步推演状态 ----------
if 'step_index' not in st.session_state:
    st.session_state.step_index = 0
if 'step_engine' not in st.session_state:
    st.session_state.step_engine = None

# ---------- 演化按钮 ----------
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("▶ 推演一步", key="step_btn"):
        if st.session_state.step_engine is None:
            engine = FourDiagnosisEngine(f'presets/{st.session_state.faction}_faction.json')
            engine.set_selected_symptoms(selected)
            baseline = config.get('constitution_baseline', {}).get(constitution, [0.2]*5)[:]
            if age <= 14: baseline[0] += 0.05; baseline[2] -= 0.05; baseline[4] -= 0.05
            elif 15 <= age <= 30: baseline[1] += 0.05; baseline[4] += 0.05
            elif 31 <= age <= 50: baseline[2] -= 0.03; baseline[3] -= 0.03
            elif 51 <= age <= 65: baseline[4] -= 0.08; baseline[0] -= 0.05
            else:
                for i in range(5): baseline[i] -= 0.05
            if gender == '男': baseline[4] += 0.03; baseline[1] -= 0.02
            else: baseline[0] += 0.03; baseline[1] += 0.02; baseline[2] -= 0.02
            engine.initial_energy = baseline
            engine.history = [baseline.copy()]
            engine.output_sequence = []
            engine.clock.reset()
            engine.sheng_coeff = sheng_coeff
            engine.ke_coeff = ke_coeff
            engine.decay = decay
            engine.base_inject_energy = inject_energy
            engine.use_clock_modulation = use_clock
            st.session_state.step_engine = engine
            st.session_state.step_index = 0

        eng = st.session_state.step_engine
        if st.session_state.step_index < total_steps:
            if herb_mode == "预设单味药" and herb_name:
                eng.step(default_pulse, herb=herb_name)
            elif herb_mode == "自定义方剂向量" and herb_dict:
                eng.step(default_pulse, herb_effect=herb_dict)
            else:
                if use_advanced and secondary_pulse:
                    if herb_mode == "预设单味药" and herb_name:
                        eng.step(default_pulse, secondary_input=secondary_pulse, secondary_strength=secondary_strength, herb=herb_name)
                    elif herb_mode == "自定义方剂向量" and herb_dict:
                        eng.step(default_pulse, secondary_input=secondary_pulse, secondary_strength=secondary_strength, herb_effect=herb_dict)
                    else:
                        eng.step(default_pulse, secondary_input=secondary_pulse, secondary_strength=secondary_strength)
                else:
                    if herb_mode == "预设单味药" and herb_name:
                        eng.step(default_pulse, herb=herb_name)
                    elif herb_mode == "自定义方剂向量" and herb_dict:
                        eng.step(default_pulse, herb_effect=herb_dict)
                    else:
                        eng.step(default_pulse)

            st.session_state.step_index += 1
            st.success(f"已推演至第 {st.session_state.step_index} 步")
        else:
            st.warning("已完成所有步骤")

with col_btn2:
    if st.button("▶️ 开始连续推演", type="primary", key="cont_btn"):
        st.session_state.step_engine = None
        st.session_state.step_index = 0

        engine_cont = FourDiagnosisEngine(f'presets/{st.session_state.faction}_faction.json')
        engine_cont.set_selected_symptoms(selected)
        baseline = config.get('constitution_baseline', {}).get(constitution, [0.2]*5)[:]
        if age <= 14: baseline[0] += 0.05; baseline[2] -= 0.05; baseline[4] -= 0.05
        elif 15 <= age <= 30: baseline[1] += 0.05; baseline[4] += 0.05
        elif 31 <= age <= 50: baseline[2] -= 0.03; baseline[3] -= 0.03
        elif 51 <= age <= 65: baseline[4] -= 0.08; baseline[0] -= 0.05
        else:
            for i in range(5): baseline[i] -= 0.05
        if gender == '男': baseline[4] += 0.03; baseline[1] -= 0.02
        else: baseline[0] += 0.03; baseline[1] += 0.02; baseline[2] -= 0.02
        engine_cont.initial_energy = baseline
        engine_cont.history = [baseline.copy()]
        engine_cont.output_sequence = []
        engine_cont.clock.reset()
        engine_cont.sheng_coeff = sheng_coeff
        engine_cont.ke_coeff = ke_coeff
        engine_cont.decay = decay
        engine_cont.base_inject_energy = inject_energy
        engine_cont.use_clock_modulation = use_clock

        for _ in range(total_steps):
            if use_advanced and secondary_pulse:
                if herb_mode == "预设单味药" and herb_name:
                    engine_cont.step(default_pulse, secondary_input=secondary_pulse, secondary_strength=secondary_strength, herb=herb_name)
                elif herb_mode == "自定义方剂向量" and herb_dict:
                    engine_cont.step(default_pulse, secondary_input=secondary_pulse, secondary_strength=secondary_strength, herb_effect=herb_dict)
                else:
                    engine_cont.step(default_pulse, secondary_input=secondary_pulse, secondary_strength=secondary_strength)
            else:
                if herb_mode == "预设单味药" and herb_name:
                    engine_cont.step(default_pulse, herb=herb_name)
                elif herb_mode == "自定义方剂向量" and herb_dict:
                    engine_cont.step(default_pulse, herb_effect=herb_dict)
                else:
                    engine_cont.step(default_pulse)

        # 连续推演结果展示
        st.success("推演完成")
        final_state = engine_cont.get_state()
        st.subheader("📊 最终五行能量")
        df = pd.DataFrame({'五行': wuxing_names, '能量': [final_state[n] for n in wuxing_names]})
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("📈 演化曲线")
        fig, ax = plt.subplots()
        for i, name in enumerate(wuxing_names):
            ax.plot(range(len(engine_cont.history)), [h[i] for h in engine_cont.history], label=name, color=colors[i])
        ax.legend(); ax.grid(True)
        st.pyplot(fig)

        st.subheader("📝 输出序列")
        st.text(' → '.join(engine_cont.output_sequence))

        diffs = [engine_cont.history[-1][i] - engine_cont.history[0][i] for i in range(5)]
        diagnosis = engine_cont.diagnose(diffs)
        st.header("🧠 辨证推演（基于预设规则）")
        st.warning("⚠️ 以下结论仅基于当前流派配置规则，不代表真实诊断。")
        if diagnosis.get('八纲'):
            st.subheader("八纲")
            for item in diagnosis['八纲']: st.markdown(f"- {item}")
        if diagnosis.get('脏腑'):
            st.subheader("脏腑")
            for item in diagnosis['脏腑']: st.markdown(f"- {item}")
        if diagnosis.get('六经'):
            st.subheader("六经")
            for item in diagnosis['六经']: st.markdown(f"- {item}")
        if not any([diagnosis.get('八纲'), diagnosis.get('脏腑'), diagnosis.get('六经')]):
            st.write("无明确结论")
        if diagnosis.get('溯源'):
            with st.expander("🔎 辨证溯源"):
                for item in diagnosis['溯源']:
                    st.write(item)

        st.markdown("<div style='background-color:#ffcccc;padding:15px;border-radius:10px;margin-top:20px'>"
                    "<b>⚠️ 所有输出取决于预设参数与规则，不代表真实生理状态，不可作为临床依据。</b></div>",
                    unsafe_allow_html=True)

with col_btn3:
    if st.button("🔄 重置", key="reset_btn"):
        st.session_state.step_engine = None
        st.session_state.step_index = 0
        st.rerun()

# 单步推演实时曲线显示（非阻塞）
if st.session_state.step_engine is not None:
    eng = st.session_state.step_engine
    st.subheader(f"📈 当前演化曲线 (已推演 {st.session_state.step_index} 步)")
    fig, ax = plt.subplots()
    for i, name in enumerate(wuxing_names):
        ax.plot(range(len(eng.history)), [h[i] for h in eng.history], label=name, color=colors[i])
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# ---------- 多流派对比 ----------
st.markdown("---")
st.header("⚖️ 多流派对比")
st.caption("选择两个已加载的流派，使用相同的四诊症状并行推演，对比辨证结论。")
col_a, col_b = st.columns(2)
with col_a:
    faction_a = st.selectbox("流派 A", available_factions, key='faction_a')
with col_b:
    faction_b = st.selectbox("流派 B", available_factions, key='faction_b', index=min(1, len(available_factions)-1))
if st.button("🔍 开始对比", key="compare_btn"):
    engine_a = FourDiagnosisEngine(f'presets/{faction_a}_faction.json')
    engine_b = FourDiagnosisEngine(f'presets/{faction_b}_faction.json')
    engine_a.set_selected_symptoms(selected)
    engine_b.set_selected_symptoms(selected)
    baseline = config.get('constitution_baseline', {}).get(constitution, [0.2]*5)[:]
    engine_a.initial_energy = baseline.copy(); engine_a.history = [baseline.copy()]; engine_a.output_sequence = []
    engine_b.initial_energy = baseline.copy(); engine_b.history = [baseline.copy()]; engine_b.output_sequence = []
    for eng in (engine_a, engine_b):
        eng.sheng_coeff = sheng_coeff; eng.ke_coeff = ke_coeff; eng.decay = decay; eng.base_inject_energy = inject_energy
    # 默认脉象
    default_pulse_comp = pulse if pulse else default_pulse
    for _ in range(total_steps):
        engine_a.step(default_pulse_comp); engine_b.step(default_pulse_comp)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"流派 A：{faction_a}")
        fig, ax = plt.subplots()
        for i, name in enumerate(wuxing_names):
            ax.plot(range(len(engine_a.history)), [h[i] for h in engine_a.history], label=name, color=colors[i])
        ax.legend(); ax.grid(True); st.pyplot(fig)
        diag_a = engine_a.diagnose([engine_a.history[-1][i] - engine_a.history[0][i] for i in range(5)])
        for cat in ['八纲','脏腑','六经']:
            if diag_a.get(cat):
                st.markdown(f"**{cat}**")
                for item in diag_a[cat]:
                    st.markdown(f"- {item}")
    with col2:
        st.subheader(f"流派 B：{faction_b}")
        fig, ax = plt.subplots()
        for i, name in enumerate(wuxing_names):
            ax.plot(range(len(engine_b.history)), [h[i] for h in engine_b.history], label=name, color=colors[i])
        ax.legend(); ax.grid(True); st.pyplot(fig)
        diag_b = engine_b.diagnose([engine_b.history[-1][i] - engine_b.history[0][i] for i in range(5)])
        for cat in ['八纲','脏腑','六经']:
            if diag_a.get(cat):
                st.markdown(f"**{cat}**")
                for item in diag_a[cat]:
                    st.markdown(f"- {item}")
