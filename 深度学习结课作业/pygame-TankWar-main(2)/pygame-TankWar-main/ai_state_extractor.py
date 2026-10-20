import pygame
import numpy as np
import cv2

"""
AI状态提取器
功能：从游戏状态中提取特征，包括视觉特征和数值特征
"""

class StateExtractor:
    def __init__(self, screen_width=630, screen_height=630, feature_size=84):
        """
        初始化状态提取器
        :param screen_width: 游戏屏幕宽度
        :param screen_height: 游戏屏幕高度
        :param feature_size: 特征图像大小（用于CNN输入）
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.feature_size = feature_size
        
    def extract_visual_state(self, screen):
        """
        提取视觉状态（游戏画面）
        :param screen: pygame Surface对象
        :return: 处理后的图像数组 (feature_size, feature_size, 3)
        """
        # 将pygame Surface转换为numpy数组
        screen_array = pygame.surfarray.array3d(screen)
        # 转置维度 (width, height, channels) -> (height, width, channels)
        screen_array = np.transpose(screen_array, (1, 0, 2))
        
        # 转换为灰度图（如果需要单通道）或保持RGB
        # 这里我们保持RGB，但可以转换为灰度图以减小输入维度
        if screen_array.shape[2] == 3:
            # 转换为灰度图以减小计算量
            gray = cv2.cvtColor(screen_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = screen_array[:, :, 0]
        
        # 调整大小到特征尺寸
        resized = cv2.resize(gray, (self.feature_size, self.feature_size))
        
        # 归一化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # 添加通道维度 (H, W) -> (H, W, 1)
        normalized = np.expand_dims(normalized, axis=2)
        
        return normalized
    
    def extract_feature_vector(self, game_state):
        """
        提取数值特征向量
        :param game_state: 游戏状态字典，包含所有游戏对象信息
        :return: 特征向量 (n_features,)
        """
        features = []
        
        # 玩家坦克1状态
        my_tank1 = game_state.get('myTank_T1', None)
        if my_tank1 and my_tank1.life > 0:
            # 位置（归一化到[0,1]）
            features.extend([
                my_tank1.rect.left / self.screen_width,
                my_tank1.rect.top / self.screen_height,
                my_tank1.dir_x,  # 方向x
                my_tank1.dir_y,  # 方向y
                my_tank1.level / 3.0,  # 等级（归一化）
                my_tank1.life / 3.0,  # 生命值（归一化）
                my_tank1.bullet.life,  # 是否有子弹
                my_tank1.bullet.strong,  # 子弹是否强化
            ])
            # 子弹位置（如果有）
            if my_tank1.bullet.life:
                features.extend([
                    my_tank1.bullet.rect.left / self.screen_width,
                    my_tank1.bullet.rect.top / self.screen_height,
                    my_tank1.bullet.dir_x,
                    my_tank1.bullet.dir_y,
                ])
            else:
                features.extend([0, 0, 0, 0])
        else:
            features.extend([0] * 12)  # 如果坦克不存在，填充0
        
        # 玩家坦克2状态（AI可能控制的坦克）
        my_tank2 = game_state.get('myTank_T2', None)
        if my_tank2 and my_tank2.life > 0:
            features.extend([
                my_tank2.rect.left / self.screen_width,
                my_tank2.rect.top / self.screen_height,
                my_tank2.dir_x,
                my_tank2.dir_y,
                my_tank2.level / 3.0,
                my_tank2.life / 3.0,
                my_tank2.bullet.life,
                my_tank2.bullet.strong,
            ])
            if my_tank2.bullet.life:
                features.extend([
                    my_tank2.bullet.rect.left / self.screen_width,
                    my_tank2.bullet.rect.top / self.screen_height,
                    my_tank2.bullet.dir_x,
                    my_tank2.bullet.dir_y,
                ])
            else:
                features.extend([0, 0, 0, 0])
        else:
            features.extend([0] * 12)
        
        # 敌方坦克信息（最多考虑最近的5个）
        all_enemy_group = game_state.get('allEnemyGroup', None)
        enemy_count = 0
        if all_enemy_group:
            enemies = list(all_enemy_group)
            # 按距离排序，取最近的5个
            if my_tank2 and my_tank2.life > 0:
                tank_pos = (my_tank2.rect.centerx, my_tank2.rect.centery)
                enemies.sort(key=lambda e: np.sqrt(
                    (e.rect.centerx - tank_pos[0])**2 + 
                    (e.rect.centery - tank_pos[1])**2
                ))
            
            for i, enemy in enumerate(enemies[:5]):
                if enemy.flash:  # 只考虑已经出现的敌人
                    features.extend([
                        enemy.rect.left / self.screen_width,
                        enemy.rect.top / self.screen_height,
                        enemy.dir_x,
                        enemy.dir_y,
                        enemy.life / 3.0,
                        enemy.kind / 4.0,  # 敌人类型（归一化）
                    ])
                    # 敌人子弹
                    if enemy.bullet.life:
                        features.extend([
                            enemy.bullet.rect.left / self.screen_width,
                            enemy.bullet.rect.top / self.screen_height,
                            enemy.bullet.dir_x,
                            enemy.bullet.dir_y,
                        ])
                    else:
                        features.extend([0, 0, 0, 0])
                    enemy_count += 1
            
            # 如果敌人少于5个，填充0
            for _ in range(5 - enemy_count):
                features.extend([0] * 10)
        else:
            features.extend([0] * 50)  # 5个敌人 * 10个特征
        
        # 道具信息
        prop = game_state.get('prop', None)
        if prop and prop.life:
            features.extend([
                prop.rect.left / self.screen_width,
                prop.rect.top / self.screen_height,
                prop.kind / 7.0,  # 道具类型
                1.0,  # 道具存在
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # 游戏状态信息
        features.extend([
            game_state.get('remaining_enemy', 0) / 20.0,  # 剩余敌人数量
            game_state.get('enemyNumber', 0) / 4.0,  # 当前敌人数量
            game_state.get('enemyCouldMove', True),  # 敌人是否可以移动
            game_state.get('invincible_T2', 0) / 200.0,  # 无敌时间（归一化）
        ])
        
        # 基地信息：坐标与存活标记
        home_group = game_state.get('homeGroup', None)
        if home_group and len(home_group) > 0:
            home = list(home_group)[0]
            features.extend([
                home.rect.centerx / self.screen_width,
                home.rect.centery / self.screen_height,
                1.0  # 基地存活
            ])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        return np.array(features, dtype=np.float32)
    
    def extract_full_state(self, screen, game_state):
        """
        提取完整状态（视觉 + 特征向量）
        :param screen: pygame Surface对象
        :param game_state: 游戏状态字典
        :return: (visual_state, feature_vector)
        """
        visual = self.extract_visual_state(screen)
        features = self.extract_feature_vector(game_state)
        return visual, features
