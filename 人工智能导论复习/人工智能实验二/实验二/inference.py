import os
import csv
import json
import glob
import cv2
import numpy as np
import torch
from torchvision import transforms
from model import Net

# 目录设置
BASE_DIR = os.path.dirname(__file__)
PIC_DIR = os.path.join(BASE_DIR, 'pic')
OUT_DIR = os.path.join(BASE_DIR, 'inference_outputs')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(OUT_DIR, exist_ok=True)

# 预处理：灰度 -> 自适应阈值 -> 反色（白底黑字）
def binarize_image(img_gray: np.ndarray) -> np.ndarray:
    # Otsu 二值化
    _, th = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 确保白底黑字：统计黑白像素占比，若反了则取反
    black = np.sum(th == 0)
    white = np.sum(th == 255)
    if black < white:
        th = 255 - th
    return th

# 简单分割：按连通域找到候选字符框，并按 x 坐标排序

def segment_characters(bin_img: np.ndarray):
    # 开运算去噪
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=1)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats((clean == 255).astype(np.uint8), connectivity=8)
    boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        
        # 改进的过滤条件：过滤空心区域和噪声
        if area < 30:  # 面积太小
            continue
        
        # 计算连通域密度，过滤空心区域
        crop = bin_img[y:y+h, x:x+w]
        white_pixels = np.sum(crop == 255)
        density = white_pixels / (w * h)
        if density < 0.2:  # 密度太低，可能是空心区域
            continue
        
        # 长宽比过滤
        aspect = h / max(w, 1)
        if aspect < 0.3 or aspect > 5.0:  # 长宽比异常
            continue
        
        # 尺寸过滤
        if h < 8 or w < 4:  # 尺寸太小
            continue
            
        boxes.append((x, y, w, h))
    
    # 智能行优先排序：自动检测多行文本
    if not boxes:
        return boxes
    
    # 按y坐标分组，检测行
    boxes_with_y = [(x, y, w, h, y) for x, y, w, h in boxes]
    boxes_with_y.sort(key=lambda b: b[1])  # 先按y排序
    
    # 检测行：y坐标相近的字符归为一行
    rows = []
    current_row = [boxes_with_y[0]]
    y_threshold = 20  # y坐标差异阈值，用于判断是否在同一行
    
    for i in range(1, len(boxes_with_y)):
        if abs(boxes_with_y[i][1] - current_row[-1][1]) <= y_threshold:
            # 在同一行
            current_row.append(boxes_with_y[i])
        else:
            # 新的一行
            rows.append(current_row)
            current_row = [boxes_with_y[i]]
    
    # 添加最后一行
    if current_row:
        rows.append(current_row)
    
    # 按行优先排序：每行内按x坐标排序
    sorted_boxes = []
    for row in rows:
        row.sort(key=lambda b: b[0])  # 行内按x坐标排序
        sorted_boxes.extend([(x, y, w, h) for x, y, w, h, _ in row])
    
    return sorted_boxes

# 规范化为 MNIST 风格 28x28，保持纵横比并置中

def normalize_to_mnist(crop: np.ndarray) -> np.ndarray:
    h, w = crop.shape
    scale = 20.0 / max(h, w)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)
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


def process_image(image_path: str, models: dict):
    img_color = cv2.imread(image_path)
    if img_color is None:
        return []
    gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    bin_img = binarize_image(gray)

    boxes = segment_characters(bin_img)
    chars = []
    for (x, y, w, h) in boxes:
        crop = bin_img[y:y+h, x:x+w]
        norm = normalize_to_mnist(crop)
        chars.append({'box': (x, y, w, h), 'norm': norm})

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
        cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 1)
    cv2.imwrite(os.path.join(img_dir, 'boxes.png'), vis)
    # 保存规范化字符
    for i, ch in enumerate(chars):
        cv2.imwrite(os.path.join(img_dir, f'char_{i:02d}.png'), ch['norm'])

    return results


def main():
    # 载入三个模型（若不存在则跳过）
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
            except Exception:
                pass

    image_paths = sorted(glob.glob(os.path.join(PIC_DIR, '*.jpg')))
    csv_path = os.path.join(OUT_DIR, 'results.csv')
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['image'] + list(models.keys())
        writer.writerow(header)
        for p in image_paths:
            res = process_image(p, models)
            row = [os.path.basename(p)] + [res.get(k, '') for k in models.keys()]
            writer.writerow(row)

    print(f'推理完成，结果已保存：{csv_path}')


if __name__ == '__main__':
    main()
