import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import cv2

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def get_ground_truth():
    """
    获取真实标签（根据用户提供的实际图片内容）
    """
    ground_truth = {
        '1.jpg': '08904151832409',
        '2.jpg': '01122021112023',  # 01, 12, 2021, 11, 2023
        '3.jpg': '22011012022122023',  # 22, 011, 01, 2022, 12, 2023
        '4.jpg': '20222024',  # 2022, 2024
        '5.jpg': '248011',  # 248, 011
        '6.jpg': '2005220222023',  # 2, 0052, 2022, 2023
        '7.jpg': '2201042022032024',  # 2201, 04, 2022, 03, 2024
        '8.jpg': '206420222024',  # 2064, 2022, 2024
        '9.jpg': '2304102023092026',  # 2304, 10, 2023, 09, 2026
        '10.jpg': '0123456789',  # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
        '11.jpg': '0123456789',  # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
        '12.jpg': '0123456789',  # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
        '13.jpg': '7965432108',  # 7, 9, 6, 5, 4, 3, 2, 1, 0, 8
        '14.jpg': '0123456789'   # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
    }
    return ground_truth

def calculate_accuracy(predicted, ground_truth):
    """计算字符串级别的准确率（完全匹配）"""
    if predicted == ground_truth:
        return 1.0
    else:
        return 0.0

def calculate_character_accuracy(predicted, ground_truth):
    """计算字符级别的准确率（使用最长公共子序列算法）"""
    if len(ground_truth) == 0:
        return 0.0
    
    # 使用最长公共子序列算法计算匹配的字符数
    def lcs_length(s1, s2):
        """计算两个字符串的最长公共子序列长度"""
        m, n = len(s1), len(s2)
        # 创建DP表
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # 填充DP表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    # 计算最长公共子序列长度
    lcs_len = lcs_length(predicted, ground_truth)
    
    # 返回准确率：LCS长度 / 真实标签长度
    return lcs_len / len(ground_truth)

def analyze_results():
    """
    分析识别结果并生成详细报告
    """
    print("🔍 开始分析识别结果...")
    
    # 读取识别结果
    results_path = 'inference_outputs/results.csv'
    if not os.path.exists(results_path):
        print("❌ 找不到识别结果文件，请先运行 inference.py")
        return
    
    # 读取CSV文件
    results_data = []
    with open(results_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results_data.append(row)
    
    print(f"📊 读取到 {len(results_data)} 张图片的识别结果")
    
    # 获取真实标签
    ground_truth = get_ground_truth()
    
    # 创建详细结果表格
    detailed_results = []
    
    for row in results_data:
        image_name = row['image']
        true_label = ground_truth.get(image_name, "")
        
        result_row = {
            '图片': image_name,
            '真实标签': true_label,
            '字符数量': len(true_label)
        }
        
        # 计算每个模型的准确率
        for model_name in ['D1 (10%)', 'D2 (1%)', 'D3 (0.1%)']:
            if model_name in row:
                predicted = str(row[model_name])
                char_acc = calculate_character_accuracy(predicted, true_label)
                
                result_row[f'{model_name}_预测'] = predicted
                result_row[f'{model_name}_字符准确率'] = f"{char_acc:.2%}"
            else:
                result_row[f'{model_name}_预测'] = ""
                result_row[f'{model_name}_字符准确率'] = "0.00%"
        
        detailed_results.append(result_row)
    
    # 保存详细结果
    if detailed_results:
        fieldnames = detailed_results[0].keys()
        with open('detailed_results.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detailed_results)
        print("📁 详细结果已保存到: detailed_results.csv")
    
    # 计算总体统计
    print("\n" + "="*80)
    print("📈 总体识别结果统计")
    print("="*80)
    
    summary_stats = {}
    for model_name in ['D1 (10%)', 'D2 (1%)', 'D3 (0.1%)']:
        model_results = [r for r in detailed_results if r[f'{model_name}_预测'] != ""]
        
        if len(model_results) == 0:
            continue
            
        # 计算字符级别准确率
        char_accuracies = []
        total_chars = 0
        correct_chars = 0
        
        for row in model_results:
            true_label = row['真实标签']
            predicted = row[f'{model_name}_预测']
            
            # 字符准确率
            char_acc = calculate_character_accuracy(predicted, true_label)
            char_accuracies.append(char_acc)
            
            # 累计字符统计
            total_chars += len(true_label)
            correct_chars += sum(1 for p, g in zip(predicted, true_label) if p == g)
        
        avg_char_acc = correct_chars / total_chars if total_chars > 0 else 0
        
        summary_stats[model_name] = {
            '字符准确率': avg_char_acc,
            '处理图片数': len(model_results),
            '总字符数': total_chars,
            '正确字符数': correct_chars
        }
        
        print(f"\n{model_name}:")
        print(f"  字符级别准确率: {avg_char_acc:.2%}")
        print(f"  处理图片数: {len(model_results)}")
        print(f"  总字符数: {total_chars}")
        print(f"  正确字符数: {correct_chars}")
    
    # 生成HTML报告
    generate_html_report(detailed_results, summary_stats)
    
    # 生成可视化图表
    generate_visualization(summary_stats)
    
    return detailed_results, summary_stats

def generate_html_report(detailed_results, summary_stats):
    """生成HTML格式的详细报告"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>字符识别结果详细报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .summary {{ background-color: #e7f3ff; padding: 15px; margin: 20px 0; }}
            .model-section {{ margin: 20px 0; }}
            .accuracy-high {{ color: green; font-weight: bold; }}
            .accuracy-medium {{ color: orange; font-weight: bold; }}
            .accuracy-low {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>字符识别结果详细报告</h1>
        
        <div class="summary">
            <h2>总体统计</h2>
    """
    
    for model_name, stats in summary_stats.items():
        html_content += f"""
            <h3>{model_name}</h3>
            <p>字符级别准确率: <span class="accuracy-{'high' if stats['字符准确率'] > 0.8 else 'medium' if stats['字符准确率'] > 0.5 else 'low'}">{stats['字符准确率']:.2%}</span></p>
            <p>处理图片数: {stats['处理图片数']}</p>
            <p>总字符数: {stats['总字符数']}</p>
            <p>正确字符数: {stats['正确字符数']}</p>
        """
    
    html_content += """
        </div>
        
        <h2>详细结果</h2>
        <table>
            <tr>
                <th>图片</th>
                <th>真实标签</th>
                <th>字符数量</th>
                <th>D1 (10%) 预测</th>
                <th>D1 字符准确率</th>
                <th>D2 (1%) 预测</th>
                <th>D2 字符准确率</th>
                <th>D3 (0.1%) 预测</th>
                <th>D3 字符准确率</th>
            </tr>
    """
    
    for row in detailed_results:
        html_content += f"""
            <tr>
                <td>{row['图片']}</td>
                <td>{row['真实标签']}</td>
                <td>{row['字符数量']}</td>
                <td>{row['D1 (10%)_预测']}</td>
                <td>{row['D1 (10%)_字符准确率']}</td>
                <td>{row['D2 (1%)_预测']}</td>
                <td>{row['D2 (1%)_字符准确率']}</td>
                <td>{row['D3 (0.1%)_预测']}</td>
                <td>{row['D3 (0.1%)_字符准确率']}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    with open('recognition_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("📄 HTML报告已生成: recognition_report.html")

def generate_visualization(summary_stats):
    """生成可视化图表"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    models = list(summary_stats.keys())
    char_accs = [summary_stats[m]['字符准确率'] for m in models]
    
    # 字符准确率对比
    bars1 = ax1.bar(models, char_accs, color=['skyblue', 'lightgreen', 'salmon'])
    ax1.set_title('字符级别准确率对比')
    ax1.set_ylabel('准确率')
    ax1.set_ylim(0, 1)
    ax1.tick_params(axis='x', rotation=45)
    
    # 在柱子上显示数值
    for bar, acc in zip(bars1, char_accs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{acc:.2%}', ha='center', va='bottom')
    
    # 隐藏第二个子图
    ax2.set_visible(False)
    
    plt.tight_layout()
    plt.savefig('accuracy_comparison.png', dpi=200, bbox_inches='tight')
    plt.close()  # 关闭图形，避免显示问题
    
    print("📊 可视化图表已生成: accuracy_comparison.png")

def main():
    """主函数"""
    try:
        detailed_df, summary_stats = analyze_results()
        print("\n✅ 分析完成！")
        print("📁 生成的文件:")
        print("  - detailed_results.csv: 详细结果表格")
        print("  - recognition_report.html: HTML报告")
        print("  - accuracy_comparison.png: 准确率对比图")
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
