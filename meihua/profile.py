"""
个性化初始能量计算器
根据用户档案生成五行初始能量向量
"""

from typing import Dict, List

# 体质基础值（九种体质已扩展为12种）
CONSTITUTION_BASE = {
    "平和质": [0.20, 0.20, 0.20, 0.20, 0.20],
    "木旺质": [0.35, 0.20, 0.15, 0.15, 0.15],
    "火旺质": [0.20, 0.35, 0.20, 0.10, 0.15],
    "土虚质": [0.20, 0.15, 0.10, 0.25, 0.30],
    "金虚质": [0.25, 0.15, 0.25, 0.10, 0.25],
    "水虚质": [0.30, 0.20, 0.20, 0.20, 0.10],
    "阳虚质": [0.25, 0.25, 0.20, 0.15, 0.15],
    "阴虚质": [0.30, 0.25, 0.15, 0.15, 0.15],
    "痰湿质": [0.15, 0.15, 0.30, 0.20, 0.20],
    "湿热质": [0.20, 0.25, 0.25, 0.15, 0.15],
    "血瘀质": [0.25, 0.20, 0.20, 0.15, 0.20],
    "气郁质": [0.35, 0.15, 0.15, 0.20, 0.15],
}

def compute_initial_energy(profile: Dict = None) -> List[float]:
    """
    根据用户档案计算五核初始能量。
    档案可包含字段：
      - constitution: 体质名称（默认平和质）
      - age: 年龄
      - gender: 男/女
      - body_type: 瘦/胖/适中
      - region: 北方/南方/东部/西部/中部
      - occupation: 体力劳动/脑力劳动/久坐/倒班
      - exercise: 规律运动/无运动/过度运动
      - diet: 嗜甘/嗜辛辣/嗜寒凉/嗜咸/不规律
      - smoking: True/False
      - alcohol: True/False
      - sleep: 长期失眠/多梦易醒/嗜睡
      - emotion: 愤怒/喜乐过度/思虑过度/悲伤过度/恐惧惊吓
      - stress: 高/低
      - season: 春/夏/长夏/秋/冬
      - chronic_disease: 列表，如["高血压","糖尿病"]
      - medication: 列表，如["激素","抗生素"]
      - family_history: 列表，如["心脑血管"]
      - birth_year_tiangan: 出生年天干（可选，如"甲"）
    """
    if profile is None:
        profile = {}
    
    # 1. 体质
    constitution = profile.get("constitution", "平和质")
    base = CONSTITUTION_BASE.get(constitution, CONSTITUTION_BASE["平和质"])
    energy = list(base)
    
    # 辅助函数
    def add(idx, delta):
        energy[idx] += delta
    
    # 2. 年龄
    age = profile.get("age", 30)
    if age <= 14:
        add(0, 0.05)   # 木
        add(2, -0.05)  # 土
        add(4, -0.05)  # 水
    elif age <= 30:
        add(1, 0.05)   # 火
        add(4, 0.05)   # 水
    elif age <= 50:
        add(2, -0.03)  # 土
        add(3, -0.03)  # 金
    elif age <= 65:
        add(4, -0.08)  # 水
        add(0, -0.05)  # 木
    else:
        for i in range(5):
            energy[i] -= 0.05
    
    # 3. 性别
    gender = profile.get("gender", "男")
    if gender == "男":
        add(4, 0.03)   # 水
        add(1, -0.02)  # 火
    else:
        add(0, 0.03)   # 木
        add(1, 0.02)   # 火
        add(2, -0.02)  # 土
    
    # 4. 体型
    body = profile.get("body_type", "适中")
    if body == "瘦":
        add(4, -0.05)  # 水
        add(0, -0.03)  # 木
        add(1, 0.03)   # 火
    elif body == "胖":
        add(2, 0.05)   # 土
        add(1, -0.03)  # 火
        add(3, -0.03)  # 金
    
    # 5. 居住地域
    region = profile.get("region")
    if region == "北方":
        add(4, 0.03); add(1, -0.02)
    elif region == "南方":
        add(1, 0.03); add(4, -0.02)
    elif region == "东部":
        add(2, 0.03); add(0, -0.02)
    elif region == "西部":
        add(3, 0.03); add(4, -0.02)
    elif region == "中部":
        add(2, 0.03); add(1, -0.02)
    
    # 6. 职业
    occ = profile.get("occupation")
    if occ == "体力劳动":
        add(0, 0.03); add(2, 0.02)
    elif occ == "脑力劳动":
        add(1, 0.03); add(4, -0.03)
    elif occ == "久坐":
        add(2, -0.03); add(0, 0.02)
    elif occ == "倒班":
        add(4, -0.05); add(1, 0.03)
    
    # 7. 运动
    ex = profile.get("exercise")
    if ex == "规律运动":
        add(0, 0.03); add(3, 0.02)
    elif ex == "无运动":
        add(2, -0.03); add(0, -0.02)
    elif ex == "过度运动":
        add(4, -0.05); add(1, 0.03)
    
    # 8. 饮食偏嗜
    diet = profile.get("diet")
    if diet == "嗜甘油腻":
        add(2, 0.05); add(1, -0.02)
    elif diet == "嗜辛辣":
        add(1, 0.04); add(4, -0.02)
    elif diet == "嗜寒凉":
        add(1, -0.03); add(2, -0.03)
    elif diet == "嗜咸":
        add(4, -0.03); add(1, 0.02)
    elif diet == "不规律":
        add(2, -0.05)
    
    # 9. 烟酒
    if profile.get("smoking"):
        add(3, -0.05); add(1, 0.03)
    if profile.get("alcohol"):
        add(0, 0.05); add(2, -0.05); add(4, -0.03)
    
    # 10. 睡眠
    sleep = profile.get("sleep")
    if sleep == "长期失眠":
        add(1, 0.08); add(4, -0.05)
    elif sleep == "多梦易醒":
        add(0, 0.04); add(1, 0.03); add(2, -0.03)
    elif sleep == "嗜睡":
        add(2, 0.05); add(1, -0.03)
    
    # 11. 情绪
    emotion = profile.get("emotion")
    if emotion == "愤怒":
        add(0, 0.06); add(2, -0.03)
    elif emotion == "喜乐过度":
        add(1, 0.06); add(3, -0.03)
    elif emotion == "思虑过度":
        add(2, 0.04); add(1, -0.02)
    elif emotion == "悲伤过度":
        add(3, 0.06); add(0, -0.03)
    elif emotion == "恐惧惊吓":
        add(4, 0.06); add(1, -0.03)
    
    # 12. 压力
    stress = profile.get("stress")
    if stress == "高":
        add(0, 0.05); add(1, 0.03); add(2, -0.04); add(4, -0.03)
    
    # 13. 季节
    season = profile.get("season")
    if season == "春":
        add(0, 0.03); add(2, -0.02)
    elif season == "夏":
        add(1, 0.04); add(4, -0.03)
    elif season == "长夏":
        add(2, 0.04); add(0, -0.02)
    elif season == "秋":
        add(3, 0.03); add(0, -0.03)
    elif season == "冬":
        add(4, 0.04); add(1, -0.03)
    
    # 14. 慢性病（简单叠加）
    diseases = profile.get("chronic_disease", [])
    for d in diseases:
        if "高血压" in d:
            add(0, 0.05); add(4, -0.03)
        elif "糖尿病" in d:
            add(2, -0.05); add(4, -0.05)
        elif "冠心病" in d:
            add(1, -0.05); add(4, -0.03)
        elif "慢性胃炎" in d:
            add(2, -0.05); add(0, 0.03)
        elif "哮喘" in d or "COPD" in d:
            add(3, -0.05); add(4, -0.03)
    
    # 15. 长期用药
    meds = profile.get("medication", [])
    for m in meds:
        if "激素" in m:
            add(4, -0.05); add(1, 0.03)
        elif "抗生素" in m:
            add(2, -0.05); add(4, -0.03)
        # 中药方向可单独处理
    
    # 16. 家族史
    family = profile.get("family_history", [])
    for fh in family:
        if "心脑血管" in fh:
            add(1, 0.03); add(0, 0.03)
        elif "脾胃" in fh:
            add(2, -0.05)
        elif "肺" in fh:
            add(3, -0.05)
        elif "肾" in fh:
            add(4, -0.05)
        elif "肿瘤" in fh:
            add(2, -0.03); add(0, 0.03)
    
    # 17. 出生运气（简化，填天干即可）
    birth_tg = profile.get("birth_year_tiangan")
    if birth_tg in ("甲", "己"):
        add(0, 0.05); add(2, -0.05)   # 木运太过
    elif birth_tg in ("乙", "庚"):
        add(3, 0.05); add(0, -0.05)   # 金运太过
    elif birth_tg in ("丙", "辛"):
        add(4, 0.05); add(1, -0.05)   # 水运太过
    elif birth_tg in ("丁", "壬"):
        add(1, 0.05); add(3, -0.05)   # 火运太过
    elif birth_tg in ("戊", "癸"):
        add(2, 0.05); add(4, -0.05)   # 土运太过
    
    # 最终约束
    for i in range(5):
        energy[i] = round(max(0.05, min(0.50, energy[i])), 4)
    
    return energy