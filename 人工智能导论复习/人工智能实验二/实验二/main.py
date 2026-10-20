# ==================== #
# 导入必要的库
# ==================== #
import os
import json
import torch
import torchvision
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn.functional as F
import matplotlib.pyplot as plt
from data_utils import build_datasets
from model import Net
from visualize_results import plot_results

# ==================== #
# 超参数设置
# ==================== #
n_epochs = 5                    # 训练轮数，每个数据集训练5轮
batch_size_train = 64           # 训练时每批处理64个样本
batch_size_test = 1000          # 测试时每批处理1000个样本（提高测试效率）
learning_rate = 0.01            # 学习率，控制参数更新步长
momentum = 0.9                  # SGD优化器的动量参数，帮助跳出局部最优
log_interval = 10               # 每10个batch输出一次训练日志
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # 自动选择GPU或CPU

# 创建输出目录
out_models_dir = os.path.join(os.path.dirname(__file__), 'models')      # 模型保存目录
os.makedirs(out_models_dir, exist_ok=True)
out_reports_dir = os.path.join(os.path.dirname(__file__), 'outputs')   # 结果保存目录
os.makedirs(out_reports_dir, exist_ok=True)

# ==================== #
# 构建数据集（返回训练集字典与测试集 loader）
# ==================== #
# 构建三种不同采样比例的数据集：D1(10%), D2(1%), D3(0.1%)
train_loaders, test_loader = build_datasets(batch_size_train, batch_size_test)

# ==================== #
# 训练函数
# ==================== #
def train(model, device, train_loader, optimizer, epoch, losses):
    """
    训练一个epoch的函数
    参数:
        model: 神经网络模型
        device: 计算设备(CPU/GPU)
        train_loader: 训练数据加载器
        optimizer: 优化器
        epoch: 当前训练轮数
        losses: 损失值记录列表
    """
    model.train()  # 设置为训练模式，启用dropout和batch normalization
    
    # 遍历训练数据的所有批次
    for batch_idx, (data, target) in enumerate(train_loader):
        # 将数据移动到指定设备（GPU或CPU）
        data, target = data.to(device), target.to(device)
        
        # 清零梯度（重要：PyTorch会累积梯度）
        optimizer.zero_grad()
        
        # 前向传播：输入数据通过神经网络得到预测结果
        output = model(data)
        
        # 计算损失：使用负对数似然损失函数
        loss = F.nll_loss(output, target)
        
        # 反向传播：计算损失对参数的梯度
        loss.backward()
        
        # 参数更新：根据梯度更新网络参数
        optimizer.step()

        # 定期输出训练进度和损失值
        if batch_idx % log_interval == 0:
            print(f'Epoch {epoch} [{batch_idx * len(data)}/{len(train_loader.dataset)} '
                  f'({100. * batch_idx / len(train_loader):.0f}%)]\tLoss: {loss.item():.6f}')
            losses.append(loss.item())

# ==================== #
# 测试函数
# ==================== #
def test(model, device, test_loader):
    """
    在测试集上评估模型性能
    参数:
        model: 训练好的神经网络模型
        device: 计算设备(CPU/GPU)
        test_loader: 测试数据加载器
    返回:
        acc: 测试准确率
    """
    model.eval()  # 设置为评估模式，禁用dropout和batch normalization
    test_loss = 0  # 累计测试损失
    correct = 0    # 累计正确预测数量
    
    # 测试时不计算梯度，节省内存和计算时间
    with torch.no_grad():
        for data, target in test_loader:
            # 将数据移动到指定设备
            data, target = data.to(device), target.to(device)
            
            # 前向传播得到预测结果
            output = model(data)
            
            # 累计测试损失
            test_loss += F.nll_loss(output, target, reduction='sum').item()
            
            # 获取预测类别（概率最大的类别）
            pred = output.argmax(dim=1)
            
            # 统计正确预测的数量
            correct += pred.eq(target.view_as(pred)).sum().item()
    
    # 计算平均损失和准确率
    test_loss /= len(test_loader.dataset)
    acc = 100. * correct / len(test_loader.dataset)
    print(f'\nTest set: Avg. loss: {test_loss:.4f}, Accuracy: {correct}/{len(test_loader.dataset)} ({acc:.2f}%)\n')
    return acc

# ==================== #
# 主训练流程：训练三种不同采样比例的数据集
# ==================== #
results = {}  # 存储每个数据集的最终测试准确率

# 遍历三种数据集：D1(10%), D2(1%), D3(0.1%)
for name, loader in train_loaders.items():
    print(f"\n========== 开始训练 {name} ==========")
    
    # 为每个数据集创建新的模型实例（避免参数共享）
    model = Net().to(device)
    
    # 创建SGD优化器，使用动量和学习率
    optimizer = optim.SGD(model.parameters(), lr=learning_rate, momentum=momentum)
    
    train_losses = []  # 记录训练过程中的损失值

    # 训练指定轮数
    for epoch in range(1, n_epochs + 1):
        # 训练一个epoch
        train(model, device, loader, optimizer, epoch, train_losses)
        # 在测试集上评估模型性能
        acc = test(model, device, test_loader)

    # 记录最终测试准确率
    results[name] = acc
    
    # 保存训练好的模型
    save_safe_name = name.replace(' ', '_').replace('%', '')  # 处理文件名中的特殊字符
    model_path = os.path.join(out_models_dir, f'{save_safe_name}.pth')
    torch.save({
        'model_state': model.state_dict(),      # 模型参数
        'acc': acc,                            # 测试准确率
        'epochs': n_epochs,                    # 训练轮数
        'batch_size_train': batch_size_train,  # 训练批次大小
        'learning_rate': learning_rate,        # 学习率
        'momentum': momentum                   # 动量参数
    }, model_path)
    print(f"💾 已保存模型到: {model_path}")

# ==================== #
# 结果可视化和保存
# ==================== #
# 绘制三种数据集的性能对比图
plot_results(results)

# 保存结果到JSON文件，便于后续分析和报告
results_json_path = os.path.join(out_reports_dir, 'results.json')
with open(results_json_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"📁 结果JSON已保存: {results_json_path}")
