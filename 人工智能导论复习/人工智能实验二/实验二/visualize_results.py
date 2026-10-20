import os
import matplotlib
import matplotlib.pyplot as plt

# 设置中文字体与负号显示，避免中文标题/标签的警告
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def plot_results(results):
    plt.figure(figsize=(6, 4))
    plt.bar(results.keys(), results.values(), color=['skyblue', 'lightgreen', 'salmon'])
    plt.title('不同训练集比例的模型性能对比')
    plt.ylabel('Test Accuracy (%)')
    plt.ylim(0, 100)
    plt.grid(axis='y')
    # 保存到 pic 目录
    out_dir = os.path.join(os.path.dirname(__file__), 'pic')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'results.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.show()

    print("\n📊 最终结果对比：")
    for k, v in results.items():
        print(f"{k} -> 测试准确率: {v:.2f}%")
