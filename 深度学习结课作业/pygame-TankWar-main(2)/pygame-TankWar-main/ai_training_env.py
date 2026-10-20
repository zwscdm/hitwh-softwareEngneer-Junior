import pygame
import numpy as np
from collections import deque
import random
from ai_state_extractor import StateExtractor
import enemyTank

"""
训练环境包装器
将游戏环境包装成适合强化学习训练的形式
"""

class TrainingEnvironment:
    """训练环境包装器"""
    def __init__(self, game_instance, checkpoint=1, is_endless=False):
        """
        初始化训练环境
        :param game_instance: Game类的实例
        :param checkpoint: 关卡编号
        :param is_endless: 是否无尽模式
        """
        self.game = game_instance
        self.checkpoint = checkpoint
        self.is_endless = is_endless
        self.state_extractor = StateExtractor()
        
        # 游戏状态跟踪
        self.prev_enemy_count = 0
        self.prev_life = 3
        self.prev_level = 0
        self.prev_green_life = 0
        self.base_hit_flag = False
        self.hit_enemy_flag = 0  # 本步命中敌人计数
        self.no_shoot_steps = 0  # 连续未射击计数（冷却好且无子弹也没开火）
        self.fired_this_step = False
        self.step_count = 0
        self.total_reward = 0
        
        # 动作历史（用于奖励计算）
        self.action_history = deque(maxlen=100)
        
    def reset(self):
        """重置环境"""
        # 重置游戏状态
        self.game.remaining_enemy = 20
        self.game.enemyNumber = 0
        self.game.overGameLoss = False
        self.game.overGameWin = False
        self.game.enemyCouldMove = True
        self.game.iron_time = 0
        
        # 重置玩家坦克
        self.game.myTank_T2.life = 3
        self.game.myTank_T2.level = 0
        self.game.myTank_T2.rect.left, self.game.myTank_T2.rect.top = 3 + 16 * 24, 3 + 24 * 24
        self.game.myTank_T2.bullet.life = False
        self.game.myTank_T2.bulletNotCooling = True
        self.game.myTank_T2.bullet.strong = False
        self.game.invincible_T2 = 200
        self.game.moving2 = 0
        # 训练时让循环认为在AI模式，便于复用定时器/冷却逻辑
        self.game.ai_mode = True
        
        # 重置玩家1坦克（如果存在）
        if self.game.myTank_T1:
            self.game.myTank_T1.bullet.life = False
        
        # 清空所有子弹
        self.game.enemyBulletGroup.empty()
        
        # 清空敌人
        enemies_to_remove = list(self.game.allEnemyGroup)
        for enemy in enemies_to_remove:
            self.game.allTankGroup.remove(enemy)
        self.game.allEnemyGroup.empty()
        self.game.redEnemyGroup.empty()
        self.game.greenEnemyGroup.empty()
        self.game.otherEnemyGroup.empty()
        
        # 重置地图 - 重新加载地图数据
        # 使用与训练开始时相同的地图数据
        map_num = [[0] * 26 for _ in range(26)]
        map_num[23][11:15] = [1, 1, 1, 1]  # 基地
        map_num[24][11] = 1
        map_num[24][14] = 1
        map_num[25][11] = 1
        map_num[25][14] = 1
        
        # 重新创建地图（清空并重建所有墙体）
        self.game.bgMap.brickGroup.empty()
        self.game.bgMap.ironGroup.empty()
        self.game.bgMap.riverGroup.empty()
        self.game.bgMap.iceGroup.empty()
        self.game.bgMap.treeGroup.empty()
        self.game.bgMap.homeGroup.empty()
        
        # 重新加载地图（使用checkpoint方法重建地图）
        self.game.bgMap.checkpoint(self.checkpoint, map_num)
        
        # 重置道具
        self.game.prop.life = False
        
        # 初始生成3个敌人（模拟游戏开始时的状态）
        for i in range(1, 4):
            enemy = enemyTank.EnemyTank(i)
            # 检查是否与现有坦克碰撞
            if not pygame.sprite.spritecollide(enemy, self.game.allTankGroup, False, None):
                self.game.allEnemyGroup.add(enemy)
                self.game.allTankGroup.add(enemy)
                self.game.enemyNumber += 1
                if enemy.isred:
                    self.game.redEnemyGroup.add(enemy)
                elif enemy.kind == 3:
                    self.game.greenEnemyGroup.add(enemy)
                else:
                    self.game.otherEnemyGroup.add(enemy)
        
        # 重置状态跟踪
        self.prev_enemy_count = 20
        self.prev_life = 3
        self.prev_level = 0
        self.prev_green_life = sum(e.life for e in self.game.greenEnemyGroup)
        self.hit_enemy_flag = 0
        self.no_shoot_steps = 0
        self.fired_this_step = False
        self.step_count = 0
        self.total_reward = 0
        self.action_history.clear()
        
        # 重置动画相关
        self.game.delay = 100
        self.game.switch_R1_R2_image = True
        
        # 获取初始状态
        game_state = self._get_game_state()
        visual_state, feature_vector = self.state_extractor.extract_full_state(
            self.game.screen, game_state
        )
        
        return visual_state, feature_vector
    
    def step(self, action):
        """
        执行一步动作
        :param action: 动作索引 (0-8)
        :return: (next_state, reward, done, info)
        """
        self.step_count += 1
        
        # 执行动作
        self._execute_action(action)
        
        # 运行游戏一帧
        self._game_step()
        
        # 计算奖励
        reward = self._calculate_reward()
        
        # 检查是否结束
        done = self._is_done()
        
        # 获取新状态
        game_state = self._get_game_state()
        visual_state, feature_vector = self.state_extractor.extract_full_state(
            self.game.screen, game_state
        )
        
        info = {
            'step': self.step_count,
            'total_reward': self.total_reward,
            'enemy_count': self.game.remaining_enemy,
            'life': self.game.myTank_T2.life
        }
        
        return (visual_state, feature_vector), reward, done, info
    
    def _execute_action(self, action):
        """执行动作"""
        tank = self.game.myTank_T2
        self.fired_this_step = False
        
        if action == 0:  # 上
            if not self.game.moving2:
                self.game.allTankGroup.remove(tank)
                if not tank.moveUp(self.game.allTankGroup, self.game.bgMap.brickGroup, 
                                  self.game.bgMap.ironGroup, self.game.bgMap.riverGroup):
                    self.game.moving2 = 7
                    self.game.movdir2 = 0
                self.game.allTankGroup.add(tank)
        elif action == 1:  # 下
            if not self.game.moving2:
                self.game.allTankGroup.remove(tank)
                if not tank.moveDown(self.game.allTankGroup, self.game.bgMap.brickGroup,
                                    self.game.bgMap.ironGroup, self.game.bgMap.riverGroup):
                    self.game.moving2 = 7
                    self.game.movdir2 = 1
                self.game.allTankGroup.add(tank)
        elif action == 2:  # 左
            if not self.game.moving2:
                self.game.allTankGroup.remove(tank)
                if not tank.moveLeft(self.game.allTankGroup, self.game.bgMap.brickGroup,
                                    self.game.bgMap.ironGroup, self.game.bgMap.riverGroup):
                    self.game.moving2 = 7
                    self.game.movdir2 = 2
                self.game.allTankGroup.add(tank)
        elif action == 3:  # 右
            if not self.game.moving2:
                self.game.allTankGroup.remove(tank)
                if not tank.moveRight(self.game.allTankGroup, self.game.bgMap.brickGroup,
                                     self.game.bgMap.ironGroup, self.game.bgMap.riverGroup):
                    self.game.moving2 = 7
                    self.game.movdir2 = 3
                self.game.allTankGroup.add(tank)
        elif action == 4:  # 向上射击
            if not tank.bullet.life:
                tank.dir_x, tank.dir_y = 0, -1
                tank.shoot()
                self.fired_this_step = True
        elif action == 5:  # 向下射击
            if not tank.bullet.life:
                tank.dir_x, tank.dir_y = 0, 1
                tank.shoot()
                self.fired_this_step = True
        elif action == 6:  # 向左射击
            if not tank.bullet.life:
                tank.dir_x, tank.dir_y = -1, 0
                tank.shoot()
                self.fired_this_step = True
        elif action == 7:  # 向右射击
            if not tank.bullet.life:
                tank.dir_x, tank.dir_y = 1, 0
                tank.shoot()
                self.fired_this_step = True
        # action == 8: 等待，不执行任何操作
    
    def _game_step(self):
        """运行游戏一帧（不渲染）"""
        # 重置友军误伤标记
        self.base_hit_flag = False
        # 用正式游戏的定时器/事件，减少分布差距
        self.game.clock.tick(60)  # 与正式游戏一致的帧率
        self.game.event_section()  # 包含子弹冷却、敌人生成、敌人移动控制等
        
        # 处理移动
        if self.game.moving2:
            self.game.moving2 -= 1
            tank = self.game.myTank_T2
            self.game.allTankGroup.remove(tank)
            if self.game.movdir2 == 0:
                tank.moveUp(self.game.allTankGroup, self.game.bgMap.brickGroup,
                           self.game.bgMap.ironGroup, self.game.bgMap.riverGroup)
            elif self.game.movdir2 == 1:
                tank.moveDown(self.game.allTankGroup, self.game.bgMap.brickGroup,
                             self.game.bgMap.ironGroup, self.game.bgMap.riverGroup)
            elif self.game.movdir2 == 2:
                tank.moveLeft(self.game.allTankGroup, self.game.bgMap.brickGroup,
                            self.game.bgMap.ironGroup, self.game.bgMap.riverGroup)
            elif self.game.movdir2 == 3:
                tank.moveRight(self.game.allTankGroup, self.game.bgMap.brickGroup,
                             self.game.bgMap.ironGroup, self.game.bgMap.riverGroup)
            self.game.allTankGroup.add(tank)
        
        # 更新子弹
        if self.game.myTank_T2.bullet.life:
            self.game.myTank_T2.bullet.move()
        
        # 更新敌人
        for each in self.game.allEnemyGroup:
            # 如果敌人还在出现动画中，继续倒计时
            if not each.flash:
                if each.times > 0:
                    each.times -= 1
                if each.times == 0:
                    each.flash = True
            
            # 如果敌人已经出现，更新移动和子弹
            if each.flash:
                if self.game.enemyCouldMove:
                    self.game.allTankGroup.remove(each)
                    each.move(self.game.allTankGroup, self.game.bgMap.brickGroup,
                             self.game.bgMap.ironGroup, self.game.bgMap.riverGroup)
                    self.game.allTankGroup.add(each)
                
                # 敌人射击（随机），移除冷却限制
                if not each.bullet.life and self.game.enemyCouldMove:
                    if np.random.random() < 0.1:  # 10%概率射击
                        each.shoot()
                
                # 更新敌人子弹移动（在碰撞检测之前）
                if each.bullet.life:
                    each.bullet.move()
                    # 检查子弹是否超出边界
                    if (each.bullet.rect.top < 3 or each.bullet.rect.bottom > 630 - 3 or
                        each.bullet.rect.left < 3 or each.bullet.rect.right > 630 - 3):
                        each.bullet.life = False
        
        # 碰撞检测（简化版，只检测关键碰撞）
        # 我方子弹碰撞敌人（简化版，但要支持重型坦克的多生命）
        if self.game.myTank_T2.bullet.life:
            # 红坦（掉道具）与普通坦克
            if pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                           self.game.redEnemyGroup, True, None):
                self.hit_enemy_flag += 1
                self.game.enemyNumber -= 1
                if not self.is_endless:
                    self.game.remaining_enemy -= 1
                self.game.myTank_T2.bullet.life = False
            elif pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                             self.game.otherEnemyGroup, True, None):
                self.hit_enemy_flag += 1
                self.game.enemyNumber -= 1
                if not self.is_endless:
                    self.game.remaining_enemy -= 1
                self.game.myTank_T2.bullet.life = False
            # 绿坦（重型，多血量）
            elif pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                             self.game.greenEnemyGroup, False, None):
                for each in list(self.game.greenEnemyGroup):
                    if pygame.sprite.collide_rect(self.game.myTank_T2.bullet, each):
                        # 三血 -> 二血 -> 一血
                        if each.life > 1:
                            each.life -= 1
                            # 按生命值切换贴图，与正式游戏保持一致
                            if each.life == 2:
                                each.tank = each.enemy_3_0
                            elif each.life == 1:
                                each.tank = each.enemy_3_2
                            self.hit_enemy_flag += 1
                        else:
                            # 最后一血被击毁
                            self.game.greenEnemyGroup.remove(each)
                            self.game.allEnemyGroup.remove(each)
                            self.game.allTankGroup.remove(each)
                            self.game.enemyNumber -= 1
                            if not self.is_endless:
                                self.game.remaining_enemy -= 1
                            self.hit_enemy_flag += 1
                self.game.myTank_T2.bullet.life = False
        
        # 敌方子弹碰撞检测
        for each in self.game.allEnemyGroup:
            if each.bullet.life:
                # 碰撞砖墙
                if pygame.sprite.spritecollide(each.bullet, self.game.bgMap.brickGroup, True, None):
                    each.bullet.life = False
                    continue
                
                # 碰撞铁墙
                if each.bullet.strong:
                    # 强化子弹可以摧毁铁墙
                    if pygame.sprite.spritecollide(each.bullet, self.game.bgMap.ironGroup, True, None):
                        each.bullet.life = False
                        continue
                else:
                    # 普通子弹不能摧毁铁墙，但会被阻挡
                    if pygame.sprite.spritecollide(each.bullet, self.game.bgMap.ironGroup, False, None):
                        each.bullet.life = False
                        continue
                
                # 碰撞基地
                if pygame.sprite.spritecollide(each.bullet, self.game.bgMap.homeGroup, True, None):
                    self.game.overGameLoss = True
                    each.bullet.life = False
                    continue
                
                # 碰撞我方坦克
                if pygame.sprite.collide_rect(each.bullet, self.game.myTank_T2):
                    if self.game.invincible_T2 <= 0:
                        self.game.myTank_T2.life -= 1
                        self.game.invincible_T2 = 200
                        # 重置位置
                        self.game.myTank_T2.rect.left, self.game.myTank_T2.rect.top = 3 + 16 * 24, 3 + 24 * 24
                        self.game.moving2 = 0
                        # 降级
                        for i in range(self.game.myTank_T2.level + 1):
                            self.game.myTank_T2.levelDown()
                    each.bullet.life = False
        
        # 子弹碰撞墙体
        if self.game.myTank_T2.bullet.life:
            if pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                          self.game.bgMap.brickGroup, True, None):
                self.game.myTank_T2.bullet.life = False
            # 碰撞铁墙
            if self.game.myTank_T2.bullet.strong:
                if pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                              self.game.bgMap.ironGroup, True, None):
                    self.game.myTank_T2.bullet.life = False
            else:
                if pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                              self.game.bgMap.ironGroup, False, None):
                    self.game.myTank_T2.bullet.life = False
            # 碰撞基地
            if pygame.sprite.spritecollide(self.game.myTank_T2.bullet,
                                          self.game.bgMap.homeGroup, True, None):
                self.base_hit_flag = True  # 记录友军误伤
                self.game.overGameLoss = True
        
        # 道具碰撞
        if self.game.prop.life and pygame.sprite.collide_rect(self.game.prop, self.game.myTank_T2):
            if self.game.prop.kind == 6:  # 升级
                self.game.myTank_T2.levelUp()
            elif self.game.prop.kind == 7:  # 生命+1
                if self.game.myTank_T2.life < 3:
                    self.game.myTank_T2.life += 1
            self.game.prop.life = False
        
        # 更新无敌时间
        if self.game.invincible_T2 > 0:
            self.game.invincible_T2 -= 1
    
    def _calculate_reward(self):
        """计算奖励"""
        reward = 0
        
        # 击杀敌人奖励
        enemy_killed = self.prev_enemy_count - self.game.remaining_enemy
        if enemy_killed > 0:
            reward += enemy_killed * 100
        
        # 重型坦克掉血奖励（逐血量）
        current_green_life = sum(e.life for e in self.game.greenEnemyGroup)
        green_life_diff = self.prev_green_life - current_green_life
        if green_life_diff > 0:
            reward += green_life_diff * 35  # 每掉一血奖励
        
        # 生命值变化
        life_lost = self.prev_life - self.game.myTank_T2.life
        if life_lost > 0:
            reward -= life_lost * 50
        
        # 升级奖励
        level_gained = self.game.myTank_T2.level - self.prev_level
        if level_gained > 0:
            reward += level_gained * 30
        
        # 存活奖励（鼓励存活）
        if self.game.myTank_T2.life > 0:
            reward += 0.1

        # 命中奖励：每次命中敌人给额外正反馈，鼓励开火
        if self.hit_enemy_flag > 0:
            reward += self.hit_enemy_flag * 15  # 命中（未必击杀）额外奖励
        
        # 不开火惩罚：无子弹且未开火时累计小惩罚
        if (not self.game.myTank_T2.bullet.life) and (not self.fired_this_step):
            self.no_shoot_steps += 1
            reward -= 0.2
        else:
            self.no_shoot_steps = 0
        
        # 惩罚长时间不行动（最近连续wait）
        if len(self.action_history) > 0 and self.action_history[-1] == 8:
            reward -= 0.5
            if len(self.action_history) >= 5 and all(a == 8 for a in list(self.action_history)[-5:]):
                reward -= 1.0

        # 友军误伤基地处罚
        if self.base_hit_flag:
            reward -= 100

        # 基地被摧毁重罚
        if self.game.overGameLoss:
            reward -= 500
        
        # 确保误伤/基地被毁时惩罚不被小正项抵消（至少-500）
        if self.game.overGameLoss or self.base_hit_flag:
            reward = min(reward, -500)
        
        # 更新历史状态
        self.prev_enemy_count = self.game.remaining_enemy
        self.prev_life = self.game.myTank_T2.life
        self.prev_level = self.game.myTank_T2.level
        self.prev_green_life = current_green_life
        self.hit_enemy_flag = 0
        self.fired_this_step = False
        
        self.total_reward += reward
        return reward
    
    def _is_done(self):
        """检查是否结束"""
        if self.game.overGameLoss or self.game.overGameWin:
            return True
        if self.game.myTank_T2.life <= 0:
            return True
        if not self.is_endless and self.game.remaining_enemy <= 0:
            return True
        if self.step_count >= 5000:  # 最大步数限制（降低到5000，避免无限循环）
            return True
        return False
    
    def _get_game_state(self):
        """获取游戏状态字典"""
        return {
            'myTank_T1': self.game.myTank_T1,
            'myTank_T2': self.game.myTank_T2,
            'allEnemyGroup': self.game.allEnemyGroup,
            'prop': self.game.prop,
            'homeGroup': self.game.bgMap.homeGroup,
            'remaining_enemy': self.game.remaining_enemy,
            'enemyNumber': self.game.enemyNumber,
            'enemyCouldMove': self.game.enemyCouldMove,
            'invincible_T2': self.game.invincible_T2,
        }
