import os
import torch
import matplotlib.pyplot as plt
import numpy as np
from data_utils import build_datasets
from torchvision import transforms

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def view_dataset_samples():
    """查看数据集的样本"""
    
    # 构建数据集
    train_loaders, test_loader = build_datasets(64, 1000)
    
    print("🔍 数据集样本查看")
    print("=" * 50)
    
    # 查看每个数据集的样本
    for name, loader in train_loaders.items():
        print(f"\n📊 {name} 数据集信息：")
        print(f"   总样本数：{len(loader.dataset)}")
        print(f"   批次数量：{len(loader)}")
        print(f"   批次大小：{loader.batch_size}")
        
        # 获取一个批次的样本
        data_iter = iter(loader)
        images, labels = next(data_iter)
        
        print(f"   样本形状：{images.shape}")
        print(f"   标签形状：{labels.shape}")
        print(f"   像素值范围：[{images.min():.3f}, {images.max():.3f}]")
        
        # 统计标签分布
        unique_labels, counts = torch.unique(labels, return_counts=True)
        print(f"   当前批次标签分布：")
        for label, count in zip(unique_labels, counts):
            print(f"     数字{label.item()}：{count.item()}个样本")

def visualize_samples():
    """可视化样本"""
    
    # 构建数据集
    train_loaders, test_loader = build_datasets(64, 1000)
    
    # 为每个数据集创建可视化
    for name, loader in train_loaders.items():
        print(f"\n🖼️ 可视化 {name} 样本")
        
        # 获取一个批次的样本
        data_iter = iter(loader)
        images, labels = next(data_iter)
        
        # 选择前16个样本进行可视化
        fig, axes = plt.subplots(4, 4, figsize=(10, 10))
        fig.suptitle(f'{name} 样本展示', fontsize=16)
        
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # 显示图像
            img = images[i].squeeze().numpy()
            axes[row, col].imshow(img, cmap='gray')
            axes[row, col].set_title(f'标签: {labels[i].item()}')
            axes[row, col].axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{name.replace(" ", "_").replace("%", "")}_samples.png', dpi=150)
        plt.show()

def analyze_data_distribution():
    """分析数据分布"""
    
    # 构建数据集
    train_loaders, test_loader = build_datasets(64, 1000)
    
    print("\n📈 数据分布分析")
    print("=" * 50)
    
    for name, loader in train_loaders.items():
        print(f"\n📊 {name} 数据分布：")
        
        # 统计所有样本的标签分布
        all_labels = []
        for _, labels in loader:
            all_labels.extend(labels.numpy())
        
        all_labels = np.array(all_labels)
        unique_labels, counts = np.unique(all_labels, return_counts=True)
        
        print(f"   各类别样本数量：")
        for label, count in zip(unique_labels, counts):
            print(f"     数字{label}：{count}个样本")
        
        # 计算类别平衡性
        mean_count = np.mean(counts)
        std_count = np.std(counts)
        cv = std_count / mean_count  # 变异系数
        
        print(f"   平均样本数：{mean_count:.1f}")
        print(f"   标准差：{std_count:.1f}")
        print(f"   变异系数：{cv:.3f} ({'平衡' if cv < 0.1 else '不平衡'})")

def view_preprocessing_effects():
    """查看预处理效果"""
    
    print("\n🔧 预处理效果查看")
    print("=" * 50)
    
    # 原始变换
    transform_original = transforms.Compose([
        transforms.ToTensor()
    ])
    
    # 标准化变换
    transform_normalized = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    # 加载原始数据
    from torchvision import datasets
    original_dataset = datasets.MNIST('./data/', train=True, download=True, transform=transform_original)
    normalized_dataset = datasets.MNIST('./data/', train=True, download=True, transform=transform_normalized)
    
    # 获取一个样本
    original_img, _ = original_dataset[0]
    normalized_img, _ = normalized_dataset[0]
    
    print(f"原始图像统计：")
    print(f"  形状：{original_img.shape}")
    print(f"  像素值范围：[{original_img.min():.3f}, {original_img.max():.3f}]")
    print(f"  均值：{original_img.mean():.3f}")
    print(f"  标准差：{original_img.std():.3f}")
    
    print(f"\n标准化后图像统计：")
    print(f"  形状：{normalized_img.shape}")
    print(f"  像素值范围：[{normalized_img.min():.3f}, {normalized_img.max():.3f}]")
    print(f"  均值：{normalized_img.mean():.3f}")
    print(f"  标准差：{normalized_img.std():.3f}")

if __name__ == "__main__":
    # 查看数据集样本
    view_dataset_samples()
    
    # 可视化样本
    visualize_samples()
    
    # 分析数据分布
    analyze_data_distribution()
    
    # 查看预处理效果
    view_preprocessing_effects()
