import os
import csv
import json
import glob
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
from torchvision import transforms
from model import Net

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 目录设置
BASE_DIR = os.path.dirname(__file__)
PIC_DIR = os.path.join(BASE_DIR, 'pic')
OUT_DIR = os.path.join(BASE_DIR, 'improved_inference_outputs')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(OUT_DIR, exist_ok=True)

def improved_binarize_image(img_gray: np.ndarray, threshold_value: int = 190) -> np.ndarray:
    """
    改进的二值化方法：使用固定阈值
    参数:
        img_gray: 灰度图像
        threshold_value: 阈值，默认190
    返回:
        二值化后的图像
    """
    # 使用固定阈值进行二值化
    _, thresholded_img = cv2.threshold(img_gray, threshold_value, 255, cv2.THRESH_BINARY)
    
    # 确保白底黑字：统计黑白像素占比，若反了则取反
    black = np.sum(thresholded_img == 0)
    white = np.sum(thresholded_img == 255)
    if black < white:
        thresholded_img = 255 - thresholded_img
    
    return thresholded_img

def adaptive_binarize_image(img_gray: np.ndarray) -> np.ndarray:
    """
    自适应二值化：尝试多个阈值，选择最佳效果
    """
    best_result = None
    best_score = -1
    
    # 尝试不同的阈值
    thresholds = [150, 170, 190, 210, 230]
    
    for thresh in thresholds:
        _, binary = cv2.threshold(img_gray, thresh, 255, cv2.THRESH_BINARY)
        
        # 确保白底黑字
        black = np.sum(binary == 0)
        white = np.sum(binary == 255)
        if black < white:
            binary = 255 - binary
        
        # 计算连通域数量作为质量指标（字符应该形成独立的连通域）
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats((binary == 0).astype(np.uint8), connectivity=8)
        
        # 计算有效连通域数量（面积适中的）
        valid_regions = 0
        for i in range(1, num_labels):
            area = stats[i][4]
            if 20 < area < 1000:  # 合理的字符区域面积
                valid_regions += 1
        
        # 选择有效连通域数量最多的结果
        if valid_regions > best_score:
            best_score = valid_regions
            best_result = binary
    
    return best_result if best_result is not None else improved_binarize_image(img_gray, 190)

def segment_characters(bin_img: np.ndarray):
    """
    改进的字符分割：使用更精确的连通域分析
    """
    # 形态学操作去噪
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        (clean == 0).astype(np.uint8), connectivity=8)
    
    boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        
        # 更严格的过滤条件
        aspect_ratio = h / max(w, 1)
        
        # 面积过滤
        if area < 30 or area > 2000:
            continue
        
        # 尺寸过滤
        if h < 10 or w < 5:
            continue
            
        # 长宽比过滤
        if aspect_ratio < 0.3 or aspect_ratio > 5.0:
            continue
            
        boxes.append((x, y, w, h))
    
    # 按x坐标排序
    boxes.sort(key=lambda b: b[0])
    return boxes

def normalize_to_mnist(crop: np.ndarray) -> np.ndarray:
    """
    改进的MNIST规范化：更好的字符居中和对齐
    """
    h, w = crop.shape
    
    # 计算边界框
    rows = np.any(crop == 0, axis=1)
    cols = np.any(crop == 0, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        # 如果没有黑色像素，返回空白图像
        return np.ones((28, 28), dtype=np.uint8) * 255
    
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    # 裁剪到实际字符区域
    char_region = crop[y_min:y_max+1, x_min:x_max+1]
    
    # 计算缩放比例，保持纵横比
    char_h, char_w = char_region.shape
    scale = 20.0 / max(char_h, char_w)
    new_w, new_h = int(round(char_w * scale)), int(round(char_h * scale))
    
    # 调整大小
    resized = cv2.resize(char_region, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    # 居中放置到28x28画布上
    canvas = np.ones((28, 28), dtype=np.uint8) * 255
    y0 = (28 - new_h) // 2
    x0 = (28 - new_w) // 2
    canvas[y0:y0+new_h, x0:x0+new_w] = resized
    
    return canvas

# 张量变换与标准化（与训练一致）
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

def load_model(model_path: str) -> Net:
    model = Net()
    state = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state['model_state'])
    model.eval()
    return model

@torch.no_grad()
def predict_digit(model: Net, img28: np.ndarray) -> int:
    t = transform(img28)
    t = t.unsqueeze(0)
    logits = model(t)
    pred = logits.argmax(dim=1).item()
    return pred

def visualize_preprocessing(image_path: str, out_dir: str):
    """
    可视化预处理过程
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return
    
    gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    
    # 原始Otsu方法
    _, otsu_result = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    black = np.sum(otsu_result == 0)
    white = np.sum(otsu_result == 255)
    if black < white:
        otsu_result = 255 - otsu_result
    
    # 改进的固定阈值方法
    improved_result = improved_binarize_image(gray, 190)
    
    # 自适应方法
    adaptive_result = adaptive_binarize_image(gray)
    
    # 创建对比图
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].imshow(gray, cmap='gray')
    axes[0, 0].set_title('原始灰度图')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(otsu_result, cmap='gray')
    axes[0, 1].set_title('Otsu二值化')
    axes[0, 1].axis('off')
    
    axes[1, 0].imshow(improved_result, cmap='gray')
    axes[1, 0].set_title('固定阈值(190)二值化')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(adaptive_result, cmap='gray')
    axes[1, 1].set_title('自适应阈值二值化')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    
    # 保存对比图
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    comparison_path = os.path.join(out_dir, f'{base_name}_preprocessing_comparison.png')
    plt.savefig(comparison_path, dpi=200, bbox_inches='tight')
    plt.close()
    
    print(f"预处理对比图已保存: {comparison_path}")

def process_image_improved(image_path: str, models: dict, use_adaptive: bool = True):
    """
    改进的图像处理流程
    """
    img_color = cv2.imread(image_path)
    if img_color is None:
        return {}
    
    gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    
    # 选择二值化方法
    if use_adaptive:
        bin_img = adaptive_binarize_image(gray)
    else:
        bin_img = improved_binarize_image(gray, 190)
    
    # 字符分割
    boxes = segment_characters(bin_img)
    chars = []
    
    for (x, y, w, h) in boxes:
        crop = bin_img[y:y+h, x:x+w]
        norm = normalize_to_mnist(crop)
        chars.append({'box': (x, y, w, h), 'norm': norm})
    
    # 模型预测
    results = {}
    for model_name, model in models.items():
        seq = ''
        for ch in chars:
            pred = predict_digit(model, ch['norm'])
            seq += str(pred)
        results[model_name] = seq
    
    # 保存中间过程
    base = os.path.splitext(os.path.basename(image_path))[0]
    img_dir = os.path.join(OUT_DIR, base)
    os.makedirs(img_dir, exist_ok=True)
    
    # 保存二值图与分割可视化
    cv2.imwrite(os.path.join(img_dir, 'binarized.png'), bin_img)
    vis = img_color.copy()
    for (x, y, w, h) in boxes:
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 2)
    cv2.imwrite(os.path.join(img_dir, 'boxes.png'), vis)
    
    # 保存规范化字符
    for i, ch in enumerate(chars):
        cv2.imwrite(os.path.join(img_dir, f'char_{i:02d}.png'), ch['norm'])
    
    # 生成预处理对比图
    visualize_preprocessing(image_path, img_dir)
    
    return results

def main():
    """
    主函数：运行改进的推理流程
    """
    print("🚀 开始改进的字符识别流程...")
    
    # 载入模型
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
    
    # 处理所有图片
    image_paths = sorted(glob.glob(os.path.join(PIC_DIR, '*.jpg')))
    print(f"📸 找到 {len(image_paths)} 张图片")
    
    # 保存结果到CSV
    csv_path = os.path.join(OUT_DIR, 'improved_results.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['image'] + list(models.keys())
        writer.writerow(header)
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n处理图片 {i}/{len(image_paths)}: {os.path.basename(image_path)}")
            
            # 尝试两种预处理方法
            results_adaptive = process_image_improved(image_path, models, use_adaptive=True)
            results_fixed = process_image_improved(image_path, models, use_adaptive=False)
            
            # 保存自适应方法的结果
            row = [os.path.basename(image_path)] + [results_adaptive.get(k, '') for k in models.keys()]
            writer.writerow(row)
            
            # 打印结果
            for model_name in models.keys():
                adaptive_result = results_adaptive.get(model_name, '')
                fixed_result = results_fixed.get(model_name, '')
                print(f"  {model_name}: 自适应={adaptive_result}, 固定阈值={fixed_result}")
    
    print(f"\n✅ 改进的推理完成，结果已保存：{csv_path}")
    print(f"📁 详细输出保存在：{OUT_DIR}")

if __name__ == '__main__':
    main()
