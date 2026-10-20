"""
实验4完整版：药品管理OCR识别 - 改进版
基于inference.py的优秀实现进行重构
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import csv
import warnings
warnings.filterwarnings('ignore')

# 可选依赖
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("警告: OpenCV未安装，将使用基础图像处理功能")

# 结果目录
RESULTS_DIR = './results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# 三个模型路径
MODEL_PATHS = {
    'D1': 'model_d1.pth',  # 10%
    'D2': 'model_d2.pth',  # 1%
    'D3': 'model_d3.pth',  # 0.1%
}

# 网络结构定义（与训练一致）
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

class ImprovedOCR:
    """改进的OCR识别类 - 参考inference.py的优秀实现"""

    def __init__(self):
        """初始化OCR识别器"""
        self.models = self.load_models()
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])

    def load_models(self):
        """加载三个训练好的模型"""
        models = {}
        for name, path in MODEL_PATHS.items():
            try:
                model = Net()
                # 尝试不同的加载方式
                state_dict = torch.load(path, map_location='cpu')
                if 'model_state' in state_dict:
                    model.load_state_dict(state_dict['model_state'])
                else:
                    model.load_state_dict(state_dict)
                model.eval()
                models[name] = model
                print(f"[改进版] 模型 {name} 已从 {path} 加载")
            except Exception as e:
                models[name] = None
                print(f"[改进版] 警告: 模型 {name} 无法加载: {e}")
        return models

    def binarize_image(self, img_gray: np.ndarray) -> np.ndarray:
        """二值化图像 - 参考inference.py的实现"""
        # Otsu 二值化
        _, th = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 确保白底黑字：统计黑白像素占比，若反了则取反
        black = np.sum(th == 0)
        white = np.sum(th == 255)
        if black < white:
            th = 255 - th

        return th

    def segment_characters(self, bin_img: np.ndarray):
        """字符分割 - 优化版，专门处理点阵字体"""
        # 对于点阵字体，使用闭运算来连接字符内的点
        # 先进行闭运算连接字符内的点
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, close_kernel, iterations=2)
        
        # 再进行开运算去除噪声
        open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        clean = cv2.morphologyEx(closed, cv2.MORPH_OPEN, open_kernel, iterations=1)

        # 连通组件分析
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            (clean == 255).astype(np.uint8), connectivity=8)

        boxes = []
        for i in range(1, num_labels):  # 跳过背景
            x, y, w, h, area = stats[i]

            # 调整过滤条件，适应点阵字体
            if area < 50:  # 提高最小面积阈值
                continue

            # 计算连通域密度
            crop = bin_img[y:y+h, x:x+w]
            white_pixels = np.sum(crop == 255)
            density = white_pixels / (w * h)
            if density < 0.1:  # 降低密度阈值，适应点阵字体
                continue

            # 长宽比过滤 - 放宽限制
            aspect_ratio = h / max(w, 1)
            if aspect_ratio < 0.2 or aspect_ratio > 8.0:  # 放宽长宽比限制
                continue

            # 尺寸过滤 - 调整最小尺寸
            if h < 6 or w < 3:  # 降低最小尺寸要求
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

        # 后处理：合并可能被错误分割的字符
        merged_boxes = self.merge_fragmented_characters(sorted_boxes, bin_img)
        
        print(f"[改进版] 检测到 {len(rows)} 行，原始分割 {len(sorted_boxes)} 个，合并后 {len(merged_boxes)} 个字符")
        return merged_boxes

    def merge_fragmented_characters(self, boxes: list, bin_img: np.ndarray) -> list:
        """合并可能被错误分割的字符片段"""
        if len(boxes) <= 1:
            return boxes
        
        merged = []
        i = 0
        
        while i < len(boxes):
            current_box = boxes[i]
            x1, y1, w1, h1 = current_box
            
            # 查找需要合并的相邻框
            merged_box = current_box
            j = i + 1
            
            while j < len(boxes):
                next_box = boxes[j]
                x2, y2, w2, h2 = next_box
                
                # 检查是否应该合并
                should_merge = False
                
                # 条件1：水平距离很近且高度重叠
                horizontal_distance = x2 - (x1 + w1)
                vertical_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                height_overlap_ratio = vertical_overlap / min(h1, h2) if min(h1, h2) > 0 else 0
                
                if (horizontal_distance < 10 and  # 水平距离小于10像素
                    height_overlap_ratio > 0.3 and  # 高度重叠超过30%
                    horizontal_distance < min(w1, w2) * 0.5):  # 水平距离小于较小框宽度的一半
                    should_merge = True
                
                # 条件2：面积都很小且距离很近（可能是同一个字符的碎片）
                area1 = w1 * h1
                area2 = w2 * h2
                if (area1 < 200 and area2 < 200 and  # 两个框都很小
                    horizontal_distance < 15 and  # 距离很近
                    height_overlap_ratio > 0.2):  # 有一定重叠
                    should_merge = True
                
                if should_merge:
                    # 合并框
                    new_x = min(x1, x2)
                    new_y = min(y1, y2)
                    new_w = max(x1 + w1, x2 + w2) - new_x
                    new_h = max(y1 + h1, y2 + h2) - new_y
                    merged_box = (new_x, new_y, new_w, new_h)
                    x1, y1, w1, h1 = merged_box
                    j += 1
                else:
                    break
            
            merged.append(merged_box)
            i = j
        
        return merged

    def normalize_to_mnist(self, crop: np.ndarray) -> np.ndarray:
        """规范化为 MNIST 风格 28x28，保持纵横比并置中"""
        h, w = crop.shape

        # 如果图像太小，直接调整大小
        if h < 5 or w < 3:
            canvas = np.ones((28, 28), dtype=np.uint8) * 255
            return canvas

        scale = 20.0 / max(h, w)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))

        # 确保新尺寸不为0
        new_w = max(1, new_w)
        new_h = max(1, new_h)

        resized = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)
        canvas = np.ones((28, 28), dtype=np.uint8) * 255
        y0 = (28 - new_h) // 2
        x0 = (28 - new_w) // 2
        canvas[y0:y0+new_h, x0:x0+new_w] = resized
        return canvas

    def predict_digit(self, model: nn.Module, img28: np.ndarray) -> int:
        """预测单个数字"""
        with torch.no_grad():
            tensor = self.transform(img28).unsqueeze(0)
            logits = model(tensor)
            pred = logits.argmax(dim=1).item()
            return pred

    def visualize_process(self, image_path: str, gray_img: np.ndarray,
                         bin_img: np.ndarray, boxes: list, chars: list, output_dir: str):
        """可视化处理过程"""
        # 创建对比图
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))

        # 原始图像
        if os.path.exists(image_path):
            try:
                # 使用PIL读取图像（支持中文路径）
                pil_img = Image.open(image_path)
                original_rgb = np.array(pil_img)
                axes[0, 0].imshow(original_rgb)
                axes[0, 0].set_title('原始图像')
            except Exception as e:
                print(f"[改进版] 无法读取原始图像用于可视化: {e}")
                axes[0, 0].text(0.5, 0.5, '无法加载图像', ha='center', va='center')
                axes[0, 0].set_title('原始图像')

        # 灰度图像
        axes[0, 1].imshow(gray_img, cmap='gray')
        axes[0, 1].set_title('灰度图像')

        # 二值化图像
        axes[0, 2].imshow(bin_img, cmap='gray')
        axes[0, 2].set_title('二值化图像')

        # 分割结果
        vis_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2RGB)
        for i, (x, y, w, h) in enumerate(boxes):
            cv2.rectangle(vis_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(vis_img, str(i+1), (x, y-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        axes[1, 0].imshow(vis_img)
        axes[1, 0].set_title('字符分割')

        # 规范化字符预览
        if chars:
            preview_chars = min(6, len(chars))
            for i in range(preview_chars):
                row = 1
                col = 1 + i
                if col >= 3:
                    row = 2
                    col = i - 3
                if row < 2 and col < 3:
                    axes[row, col].imshow(chars[i], cmap='gray')
                    axes[row, col].set_title(f'字符{i+1}')
                    axes[row, col].axis('off')

        # 隐藏多余的子图
        for i in range(len(chars), 6):
            row = 1 + i // 3
            col = 1 + i % 3
            if row < 2 and col < 3:
                axes[row, col].axis('off')

        plt.tight_layout()

        # 保存图像
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        plt.savefig(os.path.join(output_dir, f'{base_name}_process.png'),
                   dpi=150, bbox_inches='tight')
        plt.close()

        # 保存单独的字符图像
        for i, char_img in enumerate(chars):
            cv2.imwrite(os.path.join(output_dir, f'char_{i+1:02d}.png'), char_img)

        print(f"[改进版] 处理过程可视化已保存到: {output_dir}")

    def extract_digits_from_filename(self, image_path: str) -> str:
        """根据图片文件名提取真实内容"""
        base = os.path.basename(image_path)
        stem = os.path.splitext(base)[0]

        # 真实内容映射
        true_content_map = {
            '1': '08904151832409',
            '2': '01122021112023',
            '3': '22011012022122023',
            '4': '20222024',
            '5': '248011',
            '6': '2005220222023',
            '7': '2201042022032024',
            '8': '206420222024',
            '9': '2304102023092026',
            '10': '0123456789',
            '11': '0123456789',
            '12': '0123456789',
            '13': '7965432108',
            '14': '0123456789'
        }

        # 提取数字作为键
        image_num = ''.join([c for c in stem if c.isdigit()])
        return true_content_map.get(image_num, ''.join([c for c in stem if c.isdigit()]))

    def test_single_image(self, image_path: str):
        """测试单张图片"""
        print(f"\n[改进版] 处理图片: {image_path}")

        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f"[改进版] 文件不存在: {image_path}")
            return None

        # 创建输出目录
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_dir = os.path.join(RESULTS_DIR, 'improved_segments', base_name)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 读取图像 - 使用numpy和PIL处理中文路径
            import numpy as np
            from PIL import Image
            
            # 使用PIL读取图像（支持中文路径）
            pil_img = Image.open(image_path)
            # 转换为OpenCV格式
            img_color = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            if img_color is None:
                print(f"[改进版] 无法读取图像: {image_path}")
                return None

            # 转换为灰度图
            gray_img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

            # 二值化
            bin_img = self.binarize_image(gray_img)

            # 字符分割
            boxes = self.segment_characters(bin_img)

            if not boxes:
                print("[改进版] 未检测到字符")
                # 尝试整体处理
                norm_img = self.normalize_to_mnist(bin_img)
                chars = [norm_img]
                boxes = [(0, 0, bin_img.shape[1], bin_img.shape[0])]
            else:
                # 提取和规范化字符
                chars = []
                for (x, y, w, h) in boxes:
                    crop = bin_img[y:y+h, x:x+w]
                    norm = self.normalize_to_mnist(crop)
                    chars.append(norm)

            print(f"[改进版] 成功分割 {len(chars)} 个字符")

            # 可视化处理过程
            self.visualize_process(image_path, gray_img, bin_img, boxes, chars, output_dir)

            # 获取真实值
            gt_digits = self.extract_digits_from_filename(image_path)

            # 模型识别
            results = {
                'image_path': image_path,
                'gt': gt_digits,
                'char_count': len(chars),
                'char_results': []
            }

            for model_name, model in self.models.items():
                if model is None:
                    results[f'{model_name}_pred'] = ''
                    results[f'{model_name}_acc'] = 0.0
                    continue

                predictions = []
                char_details = []

                for i, char_img in enumerate(chars):
                    try:
                        pred = self.predict_digit(model, char_img)
                        predictions.append(str(pred))

                        # 字符级结果
                        char_detail = {
                            'index': i + 1,
                            'prediction': str(pred),
                            'ground_truth': gt_digits[i] if i < len(gt_digits) else '?',
                            'correct': str(pred) == gt_digits[i] if i < len(gt_digits) else False
                        }
                        char_details.append(char_detail)
                    except Exception as e:
                        predictions.append('?')
                        print(f"[改进版] 字符{i+1}识别失败: {e}")

                pred_str = ''.join(predictions)

                # 计算准确率
                L = min(len(gt_digits), len(pred_str))
                correct_count = sum(1 for i in range(L) if gt_digits[i] == pred_str[i])
                accuracy = (correct_count / L * 100) if L > 0 else 0.0

                results[f'{model_name}_pred'] = pred_str
                results[f'{model_name}_acc'] = accuracy
                results[f'{model_name}_chars'] = char_details

                print(f"[改进版] {model_name}: {pred_str} | GT: {gt_digits} | 准确率: {accuracy:.1f}%")

            return results

        except Exception as e:
            print(f"[改进版] 处理图像时出错: {e}")
            return None

    def batch_test(self, image_folder: str):
        """批量测试"""
        print(f"\n=== 改进版批量测试开始: {image_folder} ===")

        # 查找图像文件
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
        image_files = []

        for ext in image_extensions:
            pattern = os.path.join(image_folder, ext)
            image_files.extend(glob.glob(pattern))
            image_files.extend(glob.glob(pattern.upper()))

        # 如果没找到文件，尝试直接列出目录中的文件
        if not image_files:
            try:
                files = os.listdir(image_folder)
                for file in files:
                    if any(file.lower().endswith(ext.replace('*', '')) for ext in image_extensions):
                        image_files.append(os.path.join(image_folder, file))
            except Exception as e:
                print(f"[改进版] 无法列出目录文件: {e}")

        if not image_files:
            print(f"[改进版] 在 {image_folder} 中未找到图像文件")
            return []

        print(f"[改进版] 找到 {len(image_files)} 个图像文件")

        results = []
        for image_path in image_files:
            result = self.test_single_image(image_path)
            if result is not None:
                results.append(result)

        return results

    def create_report(self, results: list):
        """创建测试报告"""
        if not results:
            print("[改进版] 没有结果可报告")
            return

        print("\n" + "="*80)
        print("改进版OCR识别 - 测试报告")
        print("="*80)

        # 创建报告目录
        report_dir = os.path.join(RESULTS_DIR, 'improved_report')
        os.makedirs(report_dir, exist_ok=True)

        # 总体统计
        print("\n【总体识别结果】")
        print("-" * 80)
        print(f"{'图像':<15} {'真实值':<20} {'D1预测':<20} {'D1准确率':<10} {'D2预测':<20} {'D2准确率':<10} {'D3预测':<20} {'D3准确率':<10}")
        print("-" * 80)

        # CSV文件
        csv_path = os.path.join(report_dir, 'improved_results.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['图像', '真实值', 'D1预测', 'D1准确率', 'D2预测', 'D2准确率', 'D3预测', 'D3准确率'])

            for result in results:
                image_name = os.path.basename(result['image_path'])
                gt = result['gt']

                d1_pred = result.get('D1_pred', '')
                d1_acc = f"{result.get('D1_acc', 0):.1f}%"
                d2_pred = result.get('D2_pred', '')
                d2_acc = f"{result.get('D2_acc', 0):.1f}%"
                d3_pred = result.get('D3_pred', '')
                d3_acc = f"{result.get('D3_acc', 0):.1f}%"

                print(f"{image_name:<15} {gt:<20} {d1_pred:<20} {d1_acc:<10} {d2_pred:<20} {d2_acc:<10} {d3_pred:<20} {d3_acc:<10}")

                writer.writerow([image_name, gt, d1_pred, result.get('D1_acc', 0),
                               d2_pred, result.get('D2_acc', 0), d3_pred, result.get('D3_acc', 0)])

        # 性能分析
        print("\n【性能分析】")
        print("-" * 80)

        accuracies = {}
        for model in ['D1', 'D2', 'D3']:
            accs = [r.get(f'{model}_acc', 0) for r in results]
            if accs:
                avg_acc = sum(accs) / len(accs)
                accuracies[model] = avg_acc
                print(f"{model}模型平均准确率: {avg_acc:.2f}%")

        if accuracies:
            best_model = max(accuracies.items(), key=lambda x: x[1])
            print(f"\n最佳模型: {best_model[0]} (平均准确率: {best_model[1]:.2f}%)")

        print(f"\n详细报告已保存到: {report_dir}")
        return report_dir

def main():
    """主函数"""
    print("=== 改进版药品管理OCR识别 ===")

    # 创建OCR识别器
    ocr = ImprovedOCR()

    # 检查模型
    if not any(ocr.models.values()):
        print("[改进版] 未检测到可用模型，请确保模型文件存在")
        return

    # 测试图片路径
    test_folder = r"D:\桌面\人工智能导论实验\test_images\场景数字图像"

    if not os.path.exists(test_folder):
        print(f"[改进版] 测试文件夹不存在: {test_folder}")
        # 尝试当前目录下的test_images
        test_folder = "./test_images/场景数字图像"
        if not os.path.exists(test_folder):
            print(f"[改进版] 备用测试文件夹也不存在: {test_folder}")
            return

    # 批量测试
    results = ocr.batch_test(test_folder)

    if results:
        # 创建报告
        report_dir = ocr.create_report(results)
        print(f"\n=== 改进版实验完成 ===")
        print(f"报告位置: {report_dir}")
        print(f"分割结果: {os.path.join(RESULTS_DIR, 'improved_segments')}")
    else:
        print("[改进版] 没有成功处理任何图像")

if __name__ == "__main__":
    main()