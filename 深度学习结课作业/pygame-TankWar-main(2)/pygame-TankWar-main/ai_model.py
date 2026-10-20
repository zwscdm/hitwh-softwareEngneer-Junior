import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import sys

"""
CNN + DQN 模型定义
结合视觉感知（CNN）和特征向量进行决策
"""

class CNNFeatureExtractor(nn.Module):
    """CNN特征提取器，用于处理游戏画面"""
    def __init__(self, input_channels=1, feature_dim=256):
        super(CNNFeatureExtractor, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        
        # 使用自适应池化来避免固定尺寸问题
        self.adaptive_pool = nn.AdaptiveAvgPool2d((7, 7))
        self.fc1 = nn.Linear(64 * 7 * 7, feature_dim)
        
    def forward(self, x):
        # x shape: (batch, channels, height, width)
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        # 使用自适应池化确保输出尺寸一致
        x = self.adaptive_pool(x)
        # 使用reshape代替view，更安全
        x = x.reshape(x.size(0), -1)  # Flatten
        x = F.relu(self.fc1(x))
        return x

class FeatureVectorProcessor(nn.Module):
    """特征向量处理器，用于处理数值特征"""
    def __init__(self, input_dim, hidden_dim=256, output_dim=256):
        super(FeatureVectorProcessor, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return x

class DQNNetwork(nn.Module):
    """完整的DQN网络，结合CNN和特征向量"""
    def __init__(self, 
                 visual_input_size=(84, 84),
                 visual_channels=1,
                 feature_vector_dim=85,  # 根据StateExtractor计算的特征维度：12+12+50+4+4+3=85
                 action_dim=9,  # 动作数量：上下左右移动(4) + 射击(4方向) + 等待(1)
                 hidden_dim=512):
        super(DQNNetwork, self).__init__()
        
        # 视觉特征提取器
        self.visual_extractor = CNNFeatureExtractor(
            input_channels=visual_channels,
            feature_dim=256
        )
        
        # 特征向量处理器
        self.feature_processor = FeatureVectorProcessor(
            input_dim=feature_vector_dim,
            hidden_dim=256,
            output_dim=256
        )
        
        # 融合层
        self.fusion = nn.Linear(256 + 256, hidden_dim)
        
        # Q值输出层
        self.fc1 = nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, action_dim)
        
    def forward(self, visual_state, feature_vector):
        """
        前向传播
        :param visual_state: (batch, channels, height, width) 游戏画面
        :param feature_vector: (batch, feature_dim) 特征向量
        :return: Q值 (batch, action_dim)
        """
        # 提取视觉特征
        visual_features = self.visual_extractor(visual_state)
        
        # 处理特征向量
        vector_features = self.feature_processor(feature_vector)
        
        # 融合特征
        combined = torch.cat([visual_features, vector_features], dim=1)
        combined = F.relu(self.fusion(combined))
        
        # 输出Q值
        x = F.relu(self.fc1(combined))
        q_values = self.fc2(x)
        
        return q_values

class DQNAgent:
    """DQN智能体"""
    def __init__(self,
                 visual_input_size=(84, 84),
                 visual_channels=1,
                 feature_vector_dim=85,
                 action_dim=9,
                 learning_rate=0.0001,
                 gamma=0.99,
                 epsilon_start=1.0,
                 epsilon_end=0.01,
                 epsilon_decay=0.995,
                 device='cuda' if torch.cuda.is_available() else 'cpu'):
        
        self.device = device
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.action_dim = action_dim
        
        # 主网络和目标网络
        self.q_network = DQNNetwork(
            visual_input_size=visual_input_size,
            visual_channels=visual_channels,
            feature_vector_dim=feature_vector_dim,
            action_dim=action_dim
        ).to(device)
        
        self.target_network = DQNNetwork(
            visual_input_size=visual_input_size,
            visual_channels=visual_channels,
            feature_vector_dim=feature_vector_dim,
            action_dim=action_dim
        ).to(device)
        
        # 初始化目标网络
        self.update_target_network()
        
        # 优化器
        self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
    def update_target_network(self):
        """更新目标网络"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def select_action(self, visual_state, feature_vector, training=True):
        """
        选择动作（epsilon-greedy策略）
        :param visual_state: 游戏画面
        :param feature_vector: 特征向量
        :param training: 是否在训练模式
        :return: 动作索引
        """
        if training and np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        with torch.no_grad():
            # 处理视觉状态：先转换维度再转为tensor
            if isinstance(visual_state, np.ndarray):
                # 如果visual_state是(H, W, C)格式，转换为(C, H, W)
                if len(visual_state.shape) == 3:
                    visual_state = np.transpose(visual_state, (2, 0, 1))
                    visual_state = visual_state[np.newaxis, ...]  # 添加batch维度
                elif len(visual_state.shape) == 4:
                    # (batch, H, W, C) -> (batch, C, H, W)
                    if visual_state.shape[-1] == 1 or visual_state.shape[3] == 1:
                        visual_state = np.transpose(visual_state, (0, 3, 1, 2))
                visual_state = torch.FloatTensor(visual_state).to(self.device)
            elif isinstance(visual_state, torch.Tensor):
                if len(visual_state.shape) == 3:
                    visual_state = visual_state.unsqueeze(0)  # 添加batch维度
                    if visual_state.shape[-1] == 1:
                        visual_state = visual_state.permute(0, 3, 1, 2)
                elif len(visual_state.shape) == 4:
                    if visual_state.shape[-1] == 1 or visual_state.shape[3] == 1:
                        visual_state = visual_state.permute(0, 3, 1, 2)
                visual_state = visual_state.to(self.device)
            
            # 处理特征向量
            if isinstance(feature_vector, np.ndarray):
                if len(feature_vector.shape) == 1:
                    feature_vector = feature_vector[np.newaxis, ...]  # 添加batch维度
                feature_vector = torch.FloatTensor(feature_vector).to(self.device)
            elif isinstance(feature_vector, torch.Tensor):
                if len(feature_vector.shape) == 1:
                    feature_vector = feature_vector.unsqueeze(0)
                feature_vector = feature_vector.to(self.device)
            
            q_values = self.q_network(visual_state, feature_vector)
            return q_values.argmax(1).item()
    
    def train_step(self, batch):
        """
        训练一步
        :param batch: 批次数据 (visual_states, feature_vectors, actions, rewards, next_visual_states, next_feature_vectors, dones)
        :return: 损失值
        """
        visual_states, feature_vectors, actions, rewards, next_visual_states, next_feature_vectors, dones = batch
        
        # 确保是numpy数组
        visual_states = np.array(visual_states)
        next_visual_states = np.array(next_visual_states)
        
        # 调整维度 (batch, H, W, C) -> (batch, C, H, W)
        # 状态提取器返回的是 (H, W, 1)，ReplayBuffer会变成 (batch, H, W, 1)
        if len(visual_states.shape) == 4:
            # 如果是 (batch, H, W, C) 格式，转换为 (batch, C, H, W)
            if visual_states.shape[3] == 1 or visual_states.shape[-1] == 1:
                visual_states = np.transpose(visual_states, (0, 3, 1, 2))
        elif len(visual_states.shape) == 3:
            # 如果是 (H, W, C)，添加batch维度并转换
            if visual_states.shape[2] == 1:
                visual_states = np.transpose(visual_states, (2, 0, 1))[np.newaxis, ...]
            else:
                visual_states = visual_states[np.newaxis, ...]
        
        if len(next_visual_states.shape) == 4:
            if next_visual_states.shape[3] == 1 or next_visual_states.shape[-1] == 1:
                next_visual_states = np.transpose(next_visual_states, (0, 3, 1, 2))
        elif len(next_visual_states.shape) == 3:
            if next_visual_states.shape[2] == 1:
                next_visual_states = np.transpose(next_visual_states, (2, 0, 1))[np.newaxis, ...]
            else:
                next_visual_states = next_visual_states[np.newaxis, ...]
        
        # 转换为tensor
        visual_states = torch.FloatTensor(visual_states).to(self.device)
        feature_vectors = torch.FloatTensor(feature_vectors).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_visual_states = torch.FloatTensor(next_visual_states).to(self.device)
        next_feature_vectors = torch.FloatTensor(next_feature_vectors).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # 确保维度正确: (batch, channels, height, width)
        # 检查并修正维度
        if len(visual_states.shape) == 4:
            # 如果是 (batch, H, W, C) 格式，转换为 (batch, C, H, W)
            if visual_states.shape[1] > visual_states.shape[3]:
                # 通道在最后，需要转换
                visual_states = visual_states.permute(0, 3, 1, 2)
        if len(next_visual_states.shape) == 4:
            if next_visual_states.shape[1] > next_visual_states.shape[3]:
                next_visual_states = next_visual_states.permute(0, 3, 1, 2)
        
        # 当前Q值
        current_q_values = self.q_network(visual_states, feature_vectors)
        current_q_values = current_q_values.gather(1, actions.unsqueeze(1))
        
        # 下一个状态的Q值（使用目标网络）
        with torch.no_grad():
            next_q_values = self.target_network(next_visual_states, next_feature_vectors)
            next_q_values = next_q_values.max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # 计算损失
        loss = F.mse_loss(current_q_values.squeeze(), target_q_values)
        
        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 10)
        self.optimizer.step()
        
        # 衰减epsilon
        if self.epsilon > self.epsilon_end:
            self.epsilon *= self.epsilon_decay
        
        return loss.item()
    
    def save(self, filepath):
        """保存模型"""
        torch.save({
            'q_network': self.q_network.state_dict(),
            'target_network': self.target_network.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
        }, filepath)
    
    def load(self, filepath):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.q_network.load_state_dict(checkpoint['q_network'])
        self.target_network.load_state_dict(checkpoint['target_network'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_end)
