import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 读取实验结果
data = {
    '图像': ['1.jpg', '2.jpg', '3.jpg', '4.jpg', '5.jpg', '6.jpg', '7.jpg', '8.jpg', '9.jpg', '10.jpg', '11.jpg', '12.jpg', '13.jpg', '14.jpg'],
    'D1准确率': [0.0, 0.0, 20.0, 50.0, 100.0, 33.3, 66.7, 40.0, 25.0, 30.0, 20.0, 60.0, 0.0, 44.4],
    'D2准确率': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 10.0, 20.0, 16.7, 22.2],
    'D3准确率': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.2, 10.0, 0.0, 10.0, 0.0, 11.1]
}

df = pd.DataFrame(data)

# 创建图表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

# 图1：各图像上三个模型的准确率对比（柱状图）
x = np.arange(len(df['图像']))
width = 0.25

ax1.bar(x - width, df['D1准确率'], width, label='D1模型(10%数据)', color='blue', alpha=0.8)
ax1.bar(x, df['D2准确率'], width, label='D2模型(1%数据)', color='orange', alpha=0.8)
ax1.bar(x + width, df['D3准确率'], width, label='D3模型(0.1%数据)', color='green', alpha=0.8)

ax1.set_xlabel('测试图像')
ax1.set_ylabel('准确率 (%)')
ax1.set_title('不同数据量训练的模型在测试集上的性能对比')
ax1.set_xticks(x)
ax1.set_xticklabels(df['图像'], rotation=45)
ax1.legend()
ax1.grid(True, alpha=0.3)

# 图2：平均准确率对比（折线图）
models = ['D1模型\n(10%数据)', 'D2模型\n(1%数据)', 'D3模型\n(0.1%数据)']
avg_accuracies = [34.96, 5.63, 2.67]

ax2.plot(models, avg_accuracies, marker='o', linewidth=3, markersize=10, color='red')
ax2.set_ylabel('平均准确率 (%)')
ax2.set_title('不同数据量训练模型的平均准确率对比')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 40)

# 添加数值标签
for i, v in enumerate(avg_accuracies):
    ax2.annotate(f'{v:.2f}%', (i, v), textcoords="offset points", xytext=(0,10), ha='center')

plt.tight_layout()
plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

# 打印统计信息
print("=== 模型性能统计 ===")
print(f"D1模型(10%数据) - 平均准确率: {np.mean(df['D1准确率']):.2f}%")
print(f"D2模型(1%数据) - 平均准确率: {np.mean(df['D2准确率']):.2f}%")
print(f"D3模型(0.1%数据) - 平均准确率: {np.mean(df['D3准确率']):.2f}%")

print("\n=== 小样本学习问题分析 ===")
print("1. 数据量减少导致性能急剧下降")
print("2. D2和D3模型出现严重的模式崩塌现象")
print("3. 小样本下模型倾向于预测单一数字")
print("4. 泛化能力严重不足")
