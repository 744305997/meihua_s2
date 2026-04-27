"""
可视化工具：绘制能量演化曲线、输出能量分布等
"""

import matplotlib.pyplot as plt
from typing import List

def plot_energy_history(engine, title="五行能量演化"):
    """绘制引擎的完整历史能量曲线"""
    if not engine.history:
        print("无历史数据")
        return
    steps = len(engine.history)
    x = range(steps)
    for i, name in enumerate(engine.WUXING):
        y = [step[i] for step in engine.history]
        plt.plot(x, y, label=name)
    plt.xlabel("步数")
    plt.ylabel("能量")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.show()

def print_step_table(engine, start=0, end=None):
    """打印能量表格"""
    end = end or len(engine.history)
    header = "步数\t" + "\t".join(engine.WUXING) + "\t输出"
    print(header)
    for s in range(start, end):
        state = engine.history[s]
        out = engine.output_sequence[s] if s < len(engine.output_sequence) else "-"
        row = f"{s}\t" + "\t".join(f"{v:.3f}" for v in state) + f"\t{out}"
        print(row)