import os
import json
import csv
import glob
import cv2
import numpy as np
import pandas as pd
from inference import process_image, load_model

def calculate_accuracy(predicted, ground_truth):
    """计算字符串级别的准确率"""
    if len(predicted) != len(ground_truth):
        return 0.0
    correct = sum(1 for p, g in zip(predicted, ground_truth) if p == g)
    return correct / len(ground_truth) if len(ground_truth) > 0 else 0.0

def calculate_character_accuracy(predicted, ground_truth):
    """计算字符级别的准确率"""
    if len(predicted) != len(ground_truth):
        return 0.0
    correct = sum(1 for p, g in zip(predicted, ground_truth) if p == g)
    return correct / len(ground_truth) if len(ground_truth) > 0 else 0.0

def get_ground_truth():
    """获取真实标签（需要手动标注）"""
    # 这里需要根据实际图片内容手动标注真实标签
    ground_truth = {
        '1.jpg': '123456789',
        '2.jpg': '0',
        '3.jpg': '1',
        '4.jpg': '123',
        '5.jpg': '123456',
        '6.jpg': '2',
        '7.jpg': '3',
        '8.jpg': '4',
        '9.jpg': '5',
        '10.jpg': '1234567890',
        '11.jpg': '123456',
        '12.jpg': '123456789',
        '13.jpg': '12345678901234567',
        '14.jpg': '12'
    }
    return ground_truth

def analyze_recognition_results():
    """分析识别结果并生成报告"""
    BASE_DIR = os.path.dirname(__file__)
    PIC_DIR = os.path.join(BASE_DIR, 'pic')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    OUT_DIR = os.path.join(BASE_DIR, 'analysis_outputs')
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # 加载模型
    model_files = {
        'D1 (10%)': 'D1_(10).pth',
        'D2 (1%)': 'D2_(1).pth',
        'D3 (0.1%)': 'D3_(0.1).pth',
    }
    models = {}
    for k, fname in model_files.items():
        path = os.path.join(MODELS_DIR, fname)
        if os.path.exists(path):
            try:
                models[k] = load_model(path)
                print(f"✅ 成功加载模型: {k}")
            except Exception as e:
                print(f"❌ 加载模型失败 {k}: {e}")
    
    if not models:
        print("❌ 没有可用的模型")
        return
    
    # 获取真实标签
    ground_truth = get_ground_truth()
    
    # 处理所有图片
    image_paths = sorted(glob.glob(os.path.join(PIC_DIR, '*.jpg')))
    results = []
    
    print(f"\n开始处理 {len(image_paths)} 张图片...")
    
    for image_path in image_paths:
        image_name = os.path.basename(image_path)
        print(f"\n处理图片: {image_name}")
        
        # 处理图片
        recognition_results = process_image(image_path, models)
        
        # 获取真实标签
        true_label = ground_truth.get(image_name, "")
        
        # 计算每个模型的结果
        for model_name, predicted in recognition_results.items():
            string_accuracy = calculate_accuracy(predicted, true_label)
            char_accuracy = calculate_character_accuracy(predicted, true_label)
            
            results.append({
                'image': image_name,
                'model': model_name,
                'predicted': predicted,
                'ground_truth': true_label,
                'string_accuracy': string_accuracy,
                'character_accuracy': char_accuracy,
                'character_count': len(true_label)
            })
            
            print(f"  {model_name}: 预测='{predicted}', 真实='{true_label}', 字符串准确率={string_accuracy:.2f}, 字符准确率={char_accuracy:.2f}")
    
    # 保存详细结果到CSV
    df = pd.DataFrame(results)
    csv_path = os.path.join(OUT_DIR, 'detailed_results.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n📊 详细结果已保存到: {csv_path}")
    
    # 计算总体统计
    summary_stats = {}
    for model_name in models.keys():
        model_results = df[df['model'] == model_name]
        
        # 字符串级别准确率
        string_acc = model_results['string_accuracy'].mean()
        
        # 字符级别准确率（加权平均）
        total_chars = model_results['character_count'].sum()
        correct_chars = (model_results['character_accuracy'] * model_results['character_count']).sum()
        char_acc = correct_chars / total_chars if total_chars > 0 else 0
        
        summary_stats[model_name] = {
            'string_accuracy': string_acc,
            'character_accuracy': char_acc,
            'total_images': len(model_results),
            'total_characters': total_chars
        }
    
    # 保存统计结果
    stats_path = os.path.join(OUT_DIR, 'summary_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(summary_stats, f, ensure_ascii=False, indent=2)
    
    # 打印统计结果
    print("\n" + "="*60)
    print("📈 总体识别结果统计")
    print("="*60)
    
    for model_name, stats in summary_stats.items():
        print(f"\n{model_name}:")
        print(f"  字符串级别准确率: {stats['string_accuracy']:.2%}")
        print(f"  字符级别准确率: {stats['character_accuracy']:.2%}")
        print(f"  处理图片数: {stats['total_images']}")
        print(f"  总字符数: {stats['total_characters']}")
    
    # 生成HTML报告
    generate_html_report(df, summary_stats, OUT_DIR)
    
    return df, summary_stats

def generate_html_report(df, summary_stats, out_dir):
    """生成HTML格式的报告"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>字符识别结果报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .summary {{ background-color: #e7f3ff; padding: 15px; margin: 20px 0; }}
            .model-section {{ margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>字符识别结果报告</h1>
        
        <div class="summary">
            <h2>总体统计</h2>
    """
    
    for model_name, stats in summary_stats.items():
        html_content += f"""
            <h3>{model_name}</h3>
            <p>字符串级别准确率: {stats['string_accuracy']:.2%}</p>
            <p>字符级别准确率: {stats['character_accuracy']:.2%}</p>
            <p>处理图片数: {stats['total_images']}</p>
            <p>总字符数: {stats['total_characters']}</p>
        """
    
    html_content += """
        </div>
        
        <h2>详细结果</h2>
        <table>
            <tr>
                <th>图片</th>
                <th>模型</th>
                <th>预测结果</th>
                <th>真实标签</th>
                <th>字符串准确率</th>
                <th>字符准确率</th>
            </tr>
    """
    
    for _, row in df.iterrows():
        html_content += f"""
            <tr>
                <td>{row['image']}</td>
                <td>{row['model']}</td>
                <td>{row['predicted']}</td>
                <td>{row['ground_truth']}</td>
                <td>{row['string_accuracy']:.2%}</td>
                <td>{row['character_accuracy']:.2%}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    html_path = os.path.join(out_dir, 'recognition_report.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 HTML报告已生成: {html_path}")

if __name__ == '__main__':
    try:
        df, stats = analyze_recognition_results()
        print("\n✅ 分析完成！")
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
