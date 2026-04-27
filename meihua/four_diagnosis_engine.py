import json
from typing import Dict, List
from meihua.advanced_engine import AdvancedEngine

class FourDiagnosisEngine(AdvancedEngine):
    """四诊合参演化引擎"""
    
    def __init__(self, config_path: str = None):
        super().__init__()
        self.config = {}
        self.plan = {}
        self.selected_symptoms: Dict[str, List[str]] = {}
        
        if config_path:
            self.load_config(config_path)
    
    # ========== 配置管理 ==========
    def load_config(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self._apply_config()
    
    def _apply_config(self):
        eng = self.config.get('engine_params', {})
        self.sheng_coeff = eng.get('sheng_coeff', 0.05)
        self.ke_coeff = eng.get('ke_coeff', 0.03)
        self.decay = eng.get('decay', 0.92)
        self.base_inject_energy = eng.get('inject_energy', 0.15)
        self.homeostasis_strength = eng.get('homeostasis', 0.0)
        self.random_fluctuation = eng.get('fluctuation', 0.0)
    
    def export_config(self) -> str:
        return json.dumps(self.config, indent=2, ensure_ascii=False)
    
    def import_config(self, json_str: str):
        self.config = json.loads(json_str)
        self._apply_config()
    
    # ========== 症状映射与融合 ==========
    def set_selected_symptoms(self, symptoms: Dict[str, List[str]]):
        self.selected_symptoms = symptoms
    
    def map_symptom(self, full_path: str) -> List[float]:
        """
        从当前流派配置中读取症状的五行扰动向量。
        full_path 格式: "望诊.舌象.舌质.红舌" 或 "切诊.脉象.弦"
        """
        keys = full_path.split('.')
        mapping = self.config.get('symptom_mapping', {})
    
        for key in keys:
            if isinstance(mapping, dict) and key in mapping:
                mapping = mapping[key]
            else:
                return [0.0, 0.0, 0.0, 0.0, 0.0]
    
        # 兼容字典格式：{'木': 0, '火': 0.10, ...}
        if isinstance(mapping, dict) and all(k in mapping for k in ['木', '火', '土', '金', '水']):
            return [mapping['木'], mapping['火'], mapping['土'], mapping['金'], mapping['水']]
    
        # 兼容列表格式：[木, 火, 土, 金, 水]
        if isinstance(mapping, list) and len(mapping) == 5:
            return mapping
    
        # 格式不对，返回零向量
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    
    def apply_interactions(self, base_vector: List[float]) -> List[float]:
        rules = self.config.get('interaction_rules', [])
        if not rules or not self.selected_symptoms:
            return base_vector
        
        selected_set = set()
        for exam, syms in self.selected_symptoms.items():
            for s in syms:
                selected_set.add(s if '.' in s else f"{exam}.{s}")
        
        final = base_vector.copy()
        for rule in rules:
            trigger = rule.get('trigger', {})
            symptoms_req = trigger.get('symptoms', [])
            logic = trigger.get('logic', 'AND')
            
            triggered = False
            if logic == 'AND':
                triggered = all(s in selected_set for s in symptoms_req)
            elif logic == 'OR':
                triggered = any(s in selected_set for s in symptoms_req)
            elif logic == 'SINGLE' and len(symptoms_req) == 1:
                triggered = symptoms_req[0] in selected_set
            
            if not triggered:
                continue
            
            effect = rule.get('effect', {})
            etype = effect.get('type', '')
            if etype == 'multiply':
                factor = effect.get('factor', 1.0)
                targets = effect.get('target_symptoms', symptoms_req)
                for t in targets:
                    if t in selected_set:
                        orig = self.map_symptom(t)
                        for i in range(5):
                            final[i] += orig[i] * (factor - 1.0)
            elif etype == 'append_vector':
                vec = effect.get('vector', [0]*5)
                for i in range(5):
                    final[i] += vec[i]
        return final
    
    def fuse_diagnosis(self) -> List[float]:
        weights = self.config.get('diagnosis_weights', 
            {'望诊': 0.25, '闻诊': 0.25, '问诊': 0.25, '切诊': 0.25})
        total = [0.0] * 5
        
        for exam, syms in self.selected_symptoms.items():
            if exam not in weights:
                continue
            exam_vec = [0.0] * 5
            for s in syms:
                full = s if '.' in s else f"{exam}.{s}"
                vec = self.map_symptom(full)
                for i in range(5):
                    exam_vec[i] += vec[i]
            w = weights[exam]
            for i in range(5):
                total[i] += exam_vec[i] * w
        
        return self.apply_interactions(total)
    
    # ========== 交互规则管理 ==========
    def get_interaction_rules(self):
        return self.config.get('interaction_rules', [])
    
    def update_interaction_rules(self, rules: list):
        self.config['interaction_rules'] = rules
    
    # ========== 步骤计划 ==========
    def set_plan(self, plan: dict):
        self.plan = plan
    
    def get_patch(self, step_id: int) -> dict:
        if not self.plan:
            return {}
        for step in self.plan.get('steps', []):
            if step.get('step_id') == step_id:
                return step.get('patch', {})
        return {}
    
    def inject_vector(self, vector: List[float]):
        for i in range(5):
            self.energy[i] += vector[i]
            self.energy[i] = max(0.001, min(10.0, self.energy[i]))
    
    # ========== 辨证推理 ==========
    def diagnose(self, diffs):
        results = {'八纲': [], '脏腑': [], '溯源': []}
        
        rules = self.config.get('eight_principles_rules', {})
        for name, rule in rules.items():
            if 'symptoms_required' in rule:
                req = rule['symptoms_required']
                selected_flat = [s.split('.')[-1] for lst in self.selected_symptoms.values() for s in lst]
                if all(r in selected_flat for r in req):
                    results['八纲'].append(name)
                    results['溯源'].append(f"八纲·{name}：症状匹配 {req}")
            if 'energy_condition' in rule:
                cond = rule['energy_condition']
                fire_ratio = self.history[-1][1] / self.history[0][1] if self.history[0][1] > 0 else 0
                water_ratio = self.history[-1][4] / self.history[0][4] if self.history[0][4] > 0 else 0
                if fire_ratio > cond.get('fire_ratio', 1.2) and water_ratio < cond.get('water_ratio', 0.8):
                    results['八纲'].append(name)
                    results['溯源'].append(f"八纲·{name}：火行↑{fire_ratio:.1f}倍，水行↓{water_ratio:.1f}倍")
        
        zangfu = self.config.get('zangfu_rules', {})
        for name, rule in zangfu.items():
            cond = rule.get('condition', {})
            match = True
            details = []
            for elem, thresh in cond.items():
                idx = {'木':0,'火':1,'土':2,'金':3,'水':4}[elem]
                if diffs[idx] > abs(thresh) and thresh > 0:
                    details.append(f"{elem}↑{diffs[idx]:.3f}")
                elif diffs[idx] < -abs(thresh) and thresh < 0:
                    details.append(f"{elem}↓{diffs[idx]:.3f}")
                else:
                    match = False
            if match:
                results['脏腑'].append(name)
                results['溯源'].append(f"脏腑·{name}：{', '.join(details)}")

        # 六经辨证
        six_meridian_rules = self.config.get('six_meridian_rules', {})
        selected_flat = [s.split('.')[-1] for lst in self.selected_symptoms.values() for s in lst]
        for name, rule in six_meridian_rules.items():
            required = rule.get('required', [])
            threshold = rule.get('threshold', 1)
            matched_count = sum(1 for r in required if r in selected_flat)
            if matched_count >= threshold:
                results['六经'] = results.get('六经', []) + [f"{name} (匹配 {matched_count}/{len(required)})"]
                results['溯源'].append(f"六经·{name}：匹配 {matched_count}/{len(required)} 条")
        
        return results
