import pygame
import numpy as np
from collections import deque
import random
import os
import json
from datetime import datetime
from ai_model import DQNAgent
from ai_training_env import TrainingEnvironment
import game_loader
import maps

"""
DQN训练脚本
"""

def _render_game_frame(game, screen, font, episode, total_episodes, steps, 
                      reward, epsilon, buffer_size, loss):
    """渲染游戏画面和训练信息"""
    # 绘制游戏背景
    screen.blit(game.background_image, (0, 0))
    
    # 绘制地图元素
    for each in game.bgMap.brickGroup:
        screen.blit(each.image, each.rect)
    for each in game.bgMap.ironGroup:
        screen.blit(each.image, each.rect)
    for each in game.bgMap.riverGroup:
        screen.blit(each.image, each.rect)
    for each in game.bgMap.iceGroup:
        screen.blit(each.image, each.rect)
    for each in game.bgMap.homeGroup:
        screen.blit(each.image, each.rect)
    
    # 绘制坦克（使用正确的图片）
    if game.myTank_T2.life > 0:
        # 根据移动状态选择图片
        if game.running_T2:
            screen.blit(game.myTank_T2.tank_R0, (game.myTank_T2.rect.left, game.myTank_T2.rect.top))
            game.running_T2 = False
        else:
            screen.blit(game.myTank_T2.tank_R1, (game.myTank_T2.rect.left, game.myTank_T2.rect.top))
    
    # 绘制敌方坦克
    for each in game.allEnemyGroup:
        if each.flash:
            # 切换动画
            if game.switch_R1_R2_image:
                screen.blit(each.tank_R0, (each.rect.left, each.rect.top))
            else:
                screen.blit(each.tank_R1, (each.rect.left, each.rect.top))
    
    # 绘制子弹
    if game.myTank_T2.bullet.life:
        screen.blit(game.myTank_T2.bullet.bullet, game.myTank_T2.bullet.rect)
    for each in game.allEnemyGroup:
        if each.bullet.life:
            screen.blit(each.bullet.bullet, each.bullet.rect)
    
    # 绘制道具
    if game.prop.life:
        screen.blit(game.prop.image, game.prop.rect)
    
    # 绘制树（在表层）
    for each in game.bgMap.treeGroup:
        screen.blit(each.image, each.rect)
    
    # 绘制训练信息（在右侧，使用半透明背景）
    info_surface = pygame.Surface((120, 250))
    info_surface.set_alpha(200)
    info_surface.fill((0, 0, 0))
    screen.blit(info_surface, (630, 10))
    
    info_y = 15
    info_lines = [
        f"Episode: {episode + 1}/{total_episodes}",
        f"Steps: {steps}",
        f"Reward: {reward:.1f}",
        f"Epsilon: {epsilon:.3f}",
        f"Buffer: {buffer_size}",
        f"Life: {game.myTank_T2.life}",
        f"Enemies: {game.remaining_enemy}",
    ]
    if loss is not None:
        info_lines.append(f"Loss: {loss:.4f}")
    
    for i, line in enumerate(info_lines):
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (635, info_y + i * 25))
    
    # 绘制AI控制的提示
    ai_text = font.render("AI Training", True, (0, 255, 0))
    screen.blit(ai_text, (635, 240))
    
    pygame.display.flip()
    
    # 更新动画切换
    game.delay -= 1
    if game.delay <= 0:
        game.delay = 100
    if not (game.delay % 5):
        game.switch_R1_R2_image = not game.switch_R1_R2_image

class ReplayBuffer:
    """经验回放缓冲区"""
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """添加经验"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        """采样批次"""
        batch = random.sample(self.buffer, batch_size)
        visual_states, feature_vectors, actions, rewards, next_visual_states, next_feature_vectors, dones = zip(*[
            (
                s[0], s[1], a, r, ns[0], ns[1], d
            ) for (s, a, r, ns, d) in batch
        ])
        return (
            np.array(visual_states),
            np.array(feature_vectors),
            np.array(actions),
            np.array(rewards),
            np.array(next_visual_states),
            np.array(next_feature_vectors),
            np.array(dones)
        )
    
    def __len__(self):
        return len(self.buffer)

def train_dqn(checkpoint=1, is_endless=False, episodes=1000, save_dir='models', visualize=True):
    """
    训练DQN模型
    :param checkpoint: 关卡编号
    :param is_endless: 是否无尽模式
    :param episodes: 训练轮数
    :param save_dir: 模型保存目录
    :param visualize: 是否可视化训练过程
    """
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 初始化pygame
    pygame.init()
    if visualize:
        screen = pygame.display.set_mode((750, 630))
        pygame.display.set_caption("AI Training - Tank War")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)
    else:
        pygame.display.set_mode((750, 630))
        screen = None
        clock = None
        font = None
    
    # 创建游戏实例
    game = game_loader.Game()
    
    # 初始化地图
    map_num = [[0] * 26 for _ in range(26)]
    map_num[23][11:15] = [1, 1, 1, 1]
    map_num[24][11] = 1
    map_num[24][14] = 1
    map_num[25][11] = 1
    map_num[25][14] = 1
    
    game.bgMap.checkpoint(checkpoint, map_num)
    
    # 创建训练环境
    env = TrainingEnvironment(game, checkpoint, is_endless)
    
    # 创建DQN智能体
    agent = DQNAgent(
        visual_input_size=(84, 84),
        visual_channels=1,
            feature_vector_dim=85,
        action_dim=9,
        learning_rate=0.0001,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995
    )
    
    # 创建经验回放缓冲区
    replay_buffer = ReplayBuffer(capacity=10000)
    
    # 训练统计
    episode_rewards = []
    episode_lengths = []
    
    # 训练参数
    batch_size = 32
    update_target_freq = 100  # 每100步更新目标网络
    save_freq = 50  # 每50轮保存一次模型
    min_buffer_size = 1000  # 缓冲区最小大小
    
    print("开始训练DQN模型...")
    print(f"训练参数: episodes={episodes}, checkpoint={checkpoint}, is_endless={is_endless}")
    if visualize:
        print("训练过程可视化已启用（按ESC可退出）")
    
    for episode in range(episodes):
        # 重置环境
        state = env.reset()
        total_reward = 0
        steps = 0
        episode_loss = []
        
        while True:
            # 处理事件（用于退出）
            if visualize:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            print("训练被用户中断")
                            pygame.quit()
                            return
            
            # 选择动作
            action = agent.select_action(state[0], state[1], training=True)
            
            # 执行动作
            next_state, reward, done, info = env.step(action)
            
            # 存储经验
            replay_buffer.push(state, action, reward, next_state, done)
            
            state = next_state
            total_reward += reward
            steps += 1
            
            # 训练
            loss_value = None
            if len(replay_buffer) >= min_buffer_size:
                batch = replay_buffer.sample(batch_size)
                loss_value = agent.train_step(batch)
                episode_loss.append(loss_value)
            
            # 更新目标网络
            if steps % update_target_freq == 0:
                agent.update_target_network()
            
            # 可视化渲染
            if visualize and screen is not None:
                # 渲染游戏画面
                _render_game_frame(game, screen, font, episode, episodes, steps, 
                                 total_reward, agent.epsilon, len(replay_buffer), loss_value)
                clock.tick(30)  # 30 FPS，便于观察
            
            if done:
                break
        
        episode_rewards.append(total_reward)
        episode_lengths.append(steps)
        
        # 打印进度
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_length = np.mean(episode_lengths[-10:])
            avg_loss = np.mean(episode_loss) if episode_loss else 0
            print(f"Episode {episode + 1}/{episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Avg Length: {avg_length:.2f} | "
                  f"Avg Loss: {avg_loss:.4f} | "
                  f"Epsilon: {agent.epsilon:.3f}")
        
        # 保存模型
        if (episode + 1) % save_freq == 0:
            model_path = os.path.join(save_dir, f'dqn_model_episode_{episode + 1}.pth')
            agent.save(model_path)
            print(f"模型已保存: {model_path}")
        
        # 保存最佳模型
        if episode == 0 or total_reward > max(episode_rewards[:-1] if len(episode_rewards) > 1 else [0]):
            best_model_path = os.path.join(save_dir, 'dqn_model_best.pth')
            agent.save(best_model_path)
    
    # 保存最终模型
    final_model_path = os.path.join(save_dir, 'dqn_model_final.pth')
    agent.save(final_model_path)
    print(f"训练完成！最终模型已保存: {final_model_path}")
    
    # 保存训练统计
    stats = {
        'episode_rewards': episode_rewards,
        'episode_lengths': episode_lengths,
        'total_episodes': episodes,
        'final_epsilon': agent.epsilon
    }
    stats_path = os.path.join(save_dir, 'training_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(stats, f)
    print(f"训练统计已保存: {stats_path}")
    
    pygame.quit()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='训练DQN模型')
    parser.add_argument('--checkpoint', type=int, default=1, help='关卡编号')
    parser.add_argument('--endless', action='store_true', help='是否无尽模式')
    parser.add_argument('--episodes', type=int, default=1000, help='训练轮数')
    parser.add_argument('--save_dir', type=str, default='models', help='模型保存目录')
    parser.add_argument('--no-visualize', action='store_true', help='禁用可视化（加快训练速度）')
    
    args = parser.parse_args()
    
    train_dqn(
        checkpoint=args.checkpoint,
        is_endless=args.endless,
        episodes=args.episodes,
        save_dir=args.save_dir,
        visualize=not args.no_visualize
    )
