# ==================== #
# 导入数据处理相关库
# ==================== #
import os
import json
import torchvision
from torch.utils.data import DataLoader, Subset
import numpy as np

def make_subset(dataset, ratio):
    """
    从原始数据集中按比例分层采样创建子集
    参数:
        dataset: 原始数据集
        ratio: 采样比例（0.0-1.0）
    返回:
        Subset: 采样后的数据集子集
    """
    targets = np.array(dataset.targets)  # 获取所有样本的标签
    indices = []  # 存储采样后的索引
    
    # 对每个数字类别（0-9）分别进行采样
    for i in range(10):
        cls_idx = np.where(targets == i)[0]  # 找到当前类别的所有样本索引
        n = int(len(cls_idx) * ratio)        # 计算当前类别需要采样的数量
        indices.extend(cls_idx[:n])          # 添加前n个样本的索引
    
    return Subset(dataset, indices)  # 返回采样后的数据集子集

def build_datasets(batch_size_train, batch_size_test):
    """
    构建训练和测试数据集
    参数:
        batch_size_train: 训练批次大小
        batch_size_test: 测试批次大小
    返回:
        train_loaders: 三种不同采样比例的训练数据加载器字典
        test_loader: 测试数据加载器
    """
    # 定义数据预处理管道
    transform = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),                    # 将PIL图像转换为PyTorch张量
        torchvision.transforms.Normalize((0.1307,), (0.3081,))  # 标准化：使用MNIST数据集的均值和标准差
    ])

    # 下载并加载MNIST数据集
    train_dataset = torchvision.datasets.MNIST('./data/', train=True, download=True, transform=transform)
    test_dataset = torchvision.datasets.MNIST('./data/', train=False, download=True, transform=transform)
    
    # 创建测试数据加载器
    test_loader = DataLoader(test_dataset, batch_size=batch_size_test, shuffle=False)

    # 创建三种不同采样比例的训练数据集
    D1 = make_subset(train_dataset, 0.1)    # 10%采样：每类约600个样本
    D2 = make_subset(train_dataset, 0.01)   # 1%采样：每类约60个样本
    D3 = make_subset(train_dataset, 0.001) # 0.1%采样：每类约6个样本

    # 创建训练数据加载器字典
    train_loaders = {
        'D1 (10%)': DataLoader(D1, batch_size=batch_size_train, shuffle=True),   # 训练时打乱数据
        'D2 (1%)': DataLoader(D2, batch_size=batch_size_train, shuffle=True),
        'D3 (0.1%)': DataLoader(D3, batch_size=batch_size_train, shuffle=True)
    }

    # 统计并输出每个数据集的样本分布
    print("✅ 数据集构建完成：")
    stats = {}
    for name, subset in zip(train_loaders.keys(), [D1, D2, D3]):
        # 获取当前数据集中每个类别的样本数量
        labels = [subset.dataset.targets[i].item() for i in subset.indices]
        counts = np.bincount(labels, minlength=10)  # 统计0-9每个数字的样本数
        print(f"{name} 每类样本数: {counts}")
        stats[name] = counts.tolist()

    # 保存数据集统计信息到JSON文件
    out_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'dataset_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return train_loaders, test_loader
