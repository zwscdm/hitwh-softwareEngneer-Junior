import pygame
import numpy as np
import random
import os
import json
from collections import deque
from ai_model import DQNAgent
from ai_state_extractor import StateExtractor
from ai_training_env import TrainingEnvironment
import game_loader

"""
高层选项（advance/defend/flank）训练脚本
action_dim = 3，对应 0: advance, 1: defend, 2: flank
低层原语仍由本脚本内的简单启发式执行，作为高层动作的“技能”
"""


OPTION_ACTIONS = {0: "advance", 1: "defend", 2: "flank"}


class ReplayBuffer:
    def __init__(self, capacity=20000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        visual_states, feature_vectors, actions, rewards, next_visual_states, next_feature_vectors, dones = zip(
            *[(s[0], s[1], a, r, ns[0], ns[1], d) for (s, a, r, ns, d) in batch]
        )
        return (
            np.array(visual_states),
            np.array(feature_vectors),
            np.array(actions),
            np.array(rewards),
            np.array(next_visual_states),
            np.array(next_feature_vectors),
            np.array(dones),
        )

    def __len__(self):
        return len(self.buffer)


def nearest_enemy(env_game):
    tank = env_game.myTank_T2
    enemies = [e for e in env_game.allEnemyGroup if getattr(e, "flash", True)]
    if not enemies:
        return None
    enemies.sort(key=lambda e: abs(e.rect.centerx - tank.rect.centerx) + abs(e.rect.centery - tank.rect.centery))
    return enemies[0]


def home_center(env_game):
    hg = env_game.bgMap.homeGroup
    if hg and len(hg) > 0:
        h = list(hg)[0]
        return h.rect.centerx, h.rect.centery
    return None


def primitive_action_for_option(env_game, option):
    """
    将高层选项转成底层动作索引（0-8），用于训练时滚动执行。
    仅为训练用的简易策略，推理时由高层 DQN 决策，低层仍用游戏内逻辑。
    """
    tank = env_game.myTank_T2
    if tank.life <= 0:
        return 8  # wait
    enemy = nearest_enemy(env_game)
    home_pos = home_center(env_game)
    tx, ty = tank.rect.centerx, tank.rect.centery

    # 射击优先：同列/同行且近距离时开火
    if enemy:
        ex, ey = enemy.rect.centerx, enemy.rect.centery
        if abs(ex - tx) < 12:
            return 4 if ey < ty else 5  # shoot_up/down
        if abs(ey - ty) < 12:
            return 6 if ex < tx else 7  # shoot_left/right

    if option == "defend" and home_pos:
        hx, hy = home_pos
        if abs(hx - tx) > abs(hy - ty):
            return 3 if hx > tx else 2  # move_right/left
        return 1 if hy > ty else 0  # move_down/up

    if option == "flank" and enemy:
        ex, ey = enemy.rect.centerx, enemy.rect.centery
        dx, dy = ex - tx, ey - ty
        if abs(dx) > abs(dy):
            return 1 if dy > 0 else 0  # 先在次轴接近
        else:
            return 3 if dx > 0 else 2  # 侧向靠近

    # advance: 朝最近敌人前进
    if enemy:
        ex, ey = enemy.rect.centerx, enemy.rect.centery
        if abs(ex - tx) > abs(ey - ty):
            return 3 if ex > tx else 2
        else:
            return 1 if ey > ty else 0

    return random.choice([0, 1, 2, 3, 8])  # fallback


def train_option_dqn(checkpoint=1, is_endless=False, episodes=500, option_horizon=8, save_dir="models", visualize=False):
    """
    训练高层选项 DQN：action_dim=3 (advance/defend/flank)
    每个高层动作执行 option_horizon 步底层原语，期间累积奖励。
    """
    os.makedirs(save_dir, exist_ok=True)

    pygame.init()
    if visualize:
        screen = pygame.display.set_mode((750, 630))
        clock = pygame.time.Clock()
    else:
        pygame.display.set_mode((1, 1))
        screen = None
        clock = None

    game = game_loader.Game()
    # 与 ai_train 相同的默认地图设置
    map_num = [[0] * 26 for _ in range(26)]
    map_num[23][11:15] = [1, 1, 1, 1]
    map_num[24][11] = 1
    map_num[24][14] = 1
    map_num[25][11] = 1
    map_num[25][14] = 1
    game.bgMap.checkpoint(checkpoint, map_num)

    env = TrainingEnvironment(game, checkpoint, is_endless)
    extractor = StateExtractor()

    agent = DQNAgent(
        visual_input_size=(84, 84),
        visual_channels=1,
        feature_vector_dim=85,
        action_dim=3,  # advance / defend / flank
        learning_rate=0.0001,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=0.999  # 放慢衰减，避免早熟
    )

    buffer = ReplayBuffer(capacity=30000)
    batch_size = 32
    min_buffer = 2000
    update_target_freq = 200
    save_freq = 100

    episode_rewards = []
    episode_lengths = []

    print(f"[OPTION TRAIN] episodes={episodes}, horizon={option_horizon}, checkpoint={checkpoint}, endless={is_endless}")

    for ep in range(episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        ep_losses = []

        while True:
            if visualize:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

            # 选高层动作
            option_idx = agent.select_action(state[0], state[1], training=True)
            option_str = OPTION_ACTIONS.get(option_idx, "advance")

            # 执行 option_horizon 步底层原语
            acc_reward = 0
            done = False
            next_state = None
            for _ in range(option_horizon):
                low_action = primitive_action_for_option(env.game, option_str)
                next_state, reward, done, _info = env.step(low_action)
                acc_reward += reward
                steps += 1
                if done:
                    break

            buffer.push(state, option_idx, acc_reward, next_state, done)
            state = next_state
            total_reward += acc_reward

            # 训练
            if len(buffer) >= min_buffer:
                batch = buffer.sample(batch_size)
                loss = agent.train_step(batch)
                ep_losses.append(loss)

            if steps % update_target_freq == 0:
                agent.update_target_network()

            if visualize and screen is not None:
                # 仅保持 minimal tick
                clock.tick(30)

            if done:
                break

        episode_rewards.append(total_reward)
        episode_lengths.append(steps)

        # 打印进度
        avg_reward = np.mean(episode_rewards[-10:]) if len(episode_rewards) >= 10 else total_reward
        avg_loss = np.mean(ep_losses) if ep_losses else 0
        print(
            f"[EP {ep+1}/{episodes}] reward={total_reward:.1f} avg10={avg_reward:.1f} "
            f"steps={steps} loss={avg_loss:.4f} eps={agent.epsilon:.3f}"
        )

        # 保存
        if (ep + 1) % save_freq == 0:
            path = os.path.join(save_dir, f"option_model_episode_{ep+1}.pth")
            agent.save(path)
            print(f"[SAVE] {path}")

        # 最佳模型
        if ep == 0 or total_reward >= max(episode_rewards[:-1] if len(episode_rewards) > 1 else [total_reward]):
            best_path = os.path.join(save_dir, "option_model_best.pth")
            agent.save(best_path)

    final_path = os.path.join(save_dir, "option_model_final.pth")
    agent.save(final_path)
    print(f"[DONE] option model saved to {final_path}")

    stats = {
        "episode_rewards": episode_rewards,
        "episode_lengths": episode_lengths,
        "total_episodes": episodes,
        "final_epsilon": agent.epsilon,
    }
    with open(os.path.join(save_dir, "option_training_stats.json"), "w") as f:
        json.dump(stats, f)
    pygame.quit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="训练高层选项 DQN (advance/defend/flank)")
    parser.add_argument("--checkpoint", type=int, default=1, help="关卡编号")
    parser.add_argument("--endless", action="store_true", help="无尽模式")
    parser.add_argument("--episodes", type=int, default=500, help="训练轮数")
    parser.add_argument("--horizon", type=int, default=8, help="每个高层动作执行的底层步数")
    parser.add_argument("--save_dir", type=str, default="models", help="模型保存目录")
    parser.add_argument("--visualize", action="store_true", help="可视化训练（慢）")
    args = parser.parse_args()

    train_option_dqn(
        checkpoint=args.checkpoint,
        is_endless=args.endless,
        episodes=args.episodes,
        option_horizon=args.horizon,
        save_dir=args.save_dir,
        visualize=args.visualize,
    )

