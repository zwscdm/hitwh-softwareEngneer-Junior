# ==================== #
# 导入PyTorch深度学习库
# ==================== #
import torch
import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module):
    """
    卷积神经网络模型，用于MNIST手写数字识别
    网络结构：Conv2d -> Conv2d -> MaxPool2d -> Dropout -> Linear -> Dropout -> Linear
    """
    
    def __init__(self):
        super().__init__()
        
        # 第一个卷积层：1个输入通道 -> 32个输出通道，3x3卷积核
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        
        # 第二个卷积层：32个输入通道 -> 64个输出通道，3x3卷积核
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        
        # 最大池化层：2x2池化核，步长为2，将特征图尺寸减半
        self.pool = nn.MaxPool2d(2, 2)
        
        # Dropout层：随机丢弃25%的神经元，防止过拟合
        self.dropout = nn.Dropout(0.25)
        
        # 第一个全连接层：64*14*14=12544个输入 -> 128个输出
        self.fc1 = nn.Linear(64 * 14 * 14, 128)
        
        # 第二个全连接层：128个输入 -> 10个输出（对应10个数字类别）
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        """
        前向传播函数
        参数:
            x: 输入张量，形状为(batch_size, 1, 28, 28)
        返回:
            输出张量，形状为(batch_size, 10)，每个元素对应一个数字类别的log概率
        """
        # 第一个卷积块：卷积 -> ReLU激活
        x = F.relu(self.conv1(x))  # 输出：(batch_size, 32, 28, 28)
        
        # 第二个卷积块：卷积 -> ReLU激活 -> 最大池化
        x = self.pool(F.relu(self.conv2(x)))  # 输出：(batch_size, 64, 14, 14)
        
        # 应用Dropout防止过拟合
        x = self.dropout(x)
        
        # 将2D特征图展平为1D向量
        x = torch.flatten(x, 1)  # 输出：(batch_size, 64*14*14=12544)
        
        # 第一个全连接层：线性变换 -> ReLU激活
        x = F.relu(self.fc1(x))  # 输出：(batch_size, 128)
        
        # 再次应用Dropout
        x = self.dropout(x)
        
        # 第二个全连接层：线性变换（无激活函数）
        x = self.fc2(x)  # 输出：(batch_size, 10)
        
        # 应用log_softmax得到log概率分布
        return F.log_softmax(x, dim=1)  # 输出：(batch_size, 10)


