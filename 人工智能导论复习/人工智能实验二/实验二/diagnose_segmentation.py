import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from inference import segment_characters, binarize_image, normalize_to_mnist

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def diagnose_image(image_path: str):
    """
    诊断单张图片的分割问题
    """
    print(f"\n🔍 诊断图片: {os.path.basename(image_path)}")
    
    # 读取图像
    img_color = cv2.imread(image_path)
    if img_color is None:
        print("❌ 无法读取图片")
        return
    
    gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    bin_img = binarize_image(gray)
    
    # 获取分割结果
    boxes = segment_characters(bin_img, use_filter=False)
    print(f"📊 检测到 {len(boxes)} 个连通域")
    
    # 分析每个连通域
    for i, (x, y, w, h) in enumerate(boxes):
        crop = bin_img[y:y+h, x:x+w]
        norm = normalize_to_mnist(crop)
        
        # 计算连通域特征
        area = w * h
        aspect_ratio = h / max(w, 1)
        black_pixels = np.sum(crop == 0)
        density = black_pixels / (w * h)
        
        print(f"  区域 {i}: 位置=({x},{y}), 尺寸={w}x{h}, 面积={area}, 长宽比={aspect_ratio:.2f}, 密度={density:.2f}")
        
        # 判断是否为空心区域
        if density < 0.3:  # 密度低可能是空心区域
            print(f"    ⚠️  可能是空心区域或噪声")
        elif area < 50:  # 面积小可能是噪声
            print(f"    ⚠️  可能是噪声点")
        elif aspect_ratio > 3 or aspect_ratio < 0.3:  # 长宽比异常
            print(f"    ⚠️  长宽比异常")
        else:
            print(f"    ✅ 看起来像正常字符")
    
    # 可视化结果
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # 原始图像
    axes[0, 0].imshow(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB))
    axes[0, 0].set_title('原始图像')
    axes[0, 0].axis('off')
    
    # 二值化图像
    axes[0, 1].imshow(bin_img, cmap='gray')
    axes[0, 1].set_title('二值化图像')
    axes[0, 1].axis('off')
    
    # 分割结果
    vis = img_color.copy()
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(vis, str(i), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    axes[0, 2].imshow(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
    axes[0, 2].set_title(f'分割结果 ({len(boxes)}个区域)')
    axes[0, 2].axis('off')
    
    # 显示前几个字符
    for i in range(min(3, len(boxes))):
        if i < len(boxes):
            x, y, w, h = boxes[i]
            crop = bin_img[y:y+h, x:x+w]
            norm = normalize_to_mnist(crop)
            axes[1, i].imshow(norm, cmap='gray')
            axes[1, i].set_title(f'字符 {i}')
            axes[1, i].axis('off')
    
    plt.tight_layout()
    
    # 保存诊断结果
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = f'diagnosis_{base_name}.png'
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.show()
    
    print(f"📁 诊断结果已保存: {output_path}")

def improved_segment_characters(bin_img: np.ndarray):
    """
    改进的字符分割：过滤空心区域和噪声
    """
    # 开运算去噪
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        (clean == 0).astype(np.uint8), connectivity=8)
    
    boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        
        # 计算连通域特征
        crop = bin_img[y:y+h, x:x+w]
        black_pixels = np.sum(crop == 0)
        density = black_pixels / (w * h)
        aspect_ratio = h / max(w, 1)
        
        # 改进的过滤条件
        if area < 30:  # 面积太小
            continue
        if density < 0.2:  # 密度太低（空心区域）
            continue
        if aspect_ratio < 0.2 or aspect_ratio > 5.0:  # 长宽比异常
            continue
        if w < 5 or h < 8:  # 尺寸太小
            continue
            
        boxes.append((x, y, w, h))
    
    boxes.sort(key=lambda b: b[0])
    return boxes

def compare_segmentation_methods(image_path: str):
    """
    对比不同分割方法的效果
    """
    print(f"\n🔄 对比分割方法: {os.path.basename(image_path)}")
    
    img_color = cv2.imread(image_path)
    gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    bin_img = binarize_image(gray)
    
    # 原始方法（无过滤）
    boxes_no_filter = segment_characters(bin_img, use_filter=False)
    
    # 原始方法（有过滤）
    boxes_with_filter = segment_characters(bin_img, use_filter=True)
    
    # 改进方法
    boxes_improved = improved_segment_characters(bin_img)
    
    print(f"无过滤: {len(boxes_no_filter)} 个区域")
    print(f"有过滤: {len(boxes_with_filter)} 个区域")
    print(f"改进方法: {len(boxes_improved)} 个区域")
    
    # 可视化对比
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    methods = [
        (boxes_no_filter, "无过滤"),
        (boxes_with_filter, "原始过滤"),
        (boxes_improved, "改进方法")
    ]
    
    for idx, (boxes, title) in enumerate(methods):
        vis = img_color.copy()
        for i, (x, y, w, h) in enumerate(boxes):
            cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(vis, str(i), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        axes[idx].imshow(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
        axes[idx].set_title(f'{title} ({len(boxes)}个区域)')
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = f'comparison_{base_name}.png'
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.show()
    
    print(f"📁 对比结果已保存: {output_path}")

def main():
    """
    主函数：诊断所有图片
    """
    pic_dir = 'pic'
    image_paths = [os.path.join(pic_dir, f'{i}.jpg') for i in range(1, 15)]
    
    print("🔍 开始诊断字符分割问题...")
    
    for image_path in image_paths:
        if os.path.exists(image_path):
            # 诊断单张图片
            diagnose_image(image_path)
            
            # 对比不同方法
            compare_segmentation_methods(image_path)
        else:
            print(f"❌ 图片不存在: {image_path}")

if __name__ == '__main__':
    main()
