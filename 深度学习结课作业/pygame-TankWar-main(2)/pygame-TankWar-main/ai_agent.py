import numpy as np
from ai_state_extractor import StateExtractor
from ai_model import DQNAgent

"""
AI代理类 - 用于游戏中的AI控制
"""

class TankAIAgent:
    """坦克AI代理"""
    def __init__(self, model_path=None, option_model_path=None, device='cuda' if __import__('torch').cuda.is_available() else 'cpu'):
        """
        初始化AI代理
        :param model_path: 模型文件路径（如果为None，则使用随机策略）
        :param option_model_path: 高层选项策略模型路径（可选，未提供则使用启发式）
        :param device: 计算设备
        """
        self.state_extractor = StateExtractor()
        self.device = device
        self.option_agent = None
        self.option_action_map = {0: 'advance', 1: 'defend', 2: 'flank'}
        
        if model_path:
            # 加载训练好的模型
            import os
            if not os.path.exists(model_path):
                print(f"[AI WARNING] 模型文件不存在: {model_path}")
                self.agent = None
            else:
                print(f"[AI INIT] 正在加载模型: {model_path}")
                try:
                    self.agent = DQNAgent(
                        visual_input_size=(84, 84),
                        visual_channels=1,
                        feature_vector_dim=85,  # 新增基地信息：12+12+50+4+4+3=85
                        action_dim=9,
                        device=device
                    )
                    self.agent.load(model_path)
                    self.agent.epsilon = 0.0  # 推理时不使用随机探索
                    print(f"[AI INIT] ✓ 模型加载成功，epsilon={self.agent.epsilon}")
                except Exception as e:
                    print(f"[AI ERROR] 模型加载失败: {e}")
                    import traceback
                    traceback.print_exc()
                    self.agent = None
        else:
            print("[AI WARNING] 未提供模型路径，AI将使用随机策略")
            self.agent = None

        # 高层选项策略（可选）
        if option_model_path:
            import os
            if not os.path.exists(option_model_path):
                print(f"[AI WARNING] 选项模型文件不存在: {option_model_path}")
            else:
                try:
                    self.option_agent = DQNAgent(
                        visual_input_size=(84, 84),
                        visual_channels=1,
                        feature_vector_dim=85,
                        action_dim=3,  # advance / defend / flank
                        device=device
                    )
                    self.option_agent.load(option_model_path)
                    self.option_agent.epsilon = 0.0
                    print("[AI INIT] ✓ 选项策略模型加载成功")
                except Exception as e:
                    print(f"[AI ERROR] 选项策略加载失败: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 动作映射：0-3: 上下左右移动, 4-7: 上下左右射击, 8: 等待
        self.action_map = {
            0: 'move_up',
            1: 'move_down',
            2: 'move_left',
            3: 'move_right',
            4: 'shoot_up',
            5: 'shoot_down',
            6: 'shoot_left',
            7: 'shoot_right',
            8: 'wait'
        }
        
        # 当前动作状态
        self.current_action = None
        self.action_counter = 0
        self.action_duration = 7  # 每个动作持续7帧（与游戏中的moving参数一致）
        
        # 统计连续wait次数，如果太多则强制移动
        self.wait_count = 0
        self.max_wait_before_force_move = 30  # 连续30次wait后强制移动
        
    def get_action(self, screen, game_state):
        """
        获取AI动作
        :param screen: pygame Surface对象
        :param game_state: 游戏状态字典
        :return: 动作字符串
        """
        if self.agent is None:
            # 如果没有模型，返回随机动作（用于测试）
            import random
            action = random.choice(['move_up', 'move_down', 'move_left', 'move_right', 'wait'])
            print(f"[AI DEBUG] 无模型，随机动作: {action}")
            return action
        
        # 提取状态
        try:
            visual_state, feature_vector = self.state_extractor.extract_full_state(screen, game_state)
        except Exception as e:
            print(f"[AI ERROR] 状态提取错误: {e}")
            import traceback
            traceback.print_exc()
            return 'wait'
        
        # 选择动作
        try:
            action_idx = self.agent.select_action(visual_state, feature_vector, training=False)
            action = self.action_map.get(action_idx, 'wait')
            
            # 如果连续多次wait，强制选择移动动作
            if action == 'wait':
                self.wait_count += 1
                if self.wait_count >= self.max_wait_before_force_move:
                    import random
                    # 强制选择一个移动动作
                    action_idx = random.choice([0, 1, 2, 3])  # 上下左右
                    action = self.action_map[action_idx]
                    print(f"[AI] 连续{self.wait_count}次wait，强制选择移动: {action} (idx={action_idx})")
                    self.wait_count = 0
            else:
                self.wait_count = 0  # 重置计数
            
            # 打印所有动作选择，特别是射击动作
            if action_idx < 4:  # 0-3是移动动作
                print(f"[AI] 模型选择移动动作: {action} (idx={action_idx})")
            elif action_idx < 8:  # 4-7是射击动作
                print(f"[AI] ✓ 模型选择射击动作: {action} (idx={action_idx})")
            else:  # 8是等待
                print(f"[AI] 模型选择等待动作: {action} (idx={action_idx})")
        except Exception as e:
            print(f"[AI ERROR] AI动作选择错误: {e}")
            import traceback
            traceback.print_exc()
            action = 'wait'
        
        return action
    
    def execute_action(self, screen, game_state, tank):
        """
        执行动作并返回游戏操作
        :param screen: pygame Surface对象
        :param game_state: 游戏状态字典
        :param tank: 要控制的坦克对象
        :return: (move_dir, should_shoot, shoot_dir)
        """
        action = self.get_action(screen, game_state)
        
        move_dir = None
        should_shoot = False
        shoot_dir = None
        is_model_shot = False  # 标记是否是模型选择的射击动作

        # 高层选项（防守/推进/绕后）
        option = self._select_option_learned(screen, game_state, tank) or self._select_option(game_state, tank)

        # 如果场上没有敌人，避免盲目射击（防止开局朝基地乱射）
        has_enemy = bool(game_state.get('allEnemyGroup')) if game_state else False
        if not has_enemy and action.startswith("shoot"):
            action = 'wait'
        
        # 优先检查：如果有敌人可以射击，优先射击而不是移动
        # 这确保AI会朝敌人方向射击，即使模型选择了移动
        if (not tank.bullet.life) and has_enemy:
            nearest = self._nearest_enemy(game_state, tank)
            if nearest:
                dx = nearest.rect.centerx - tank.rect.centerx
                dy = nearest.rect.centery - tank.rect.centery
                distance = abs(dx) + abs(dy)
                
                # 如果敌人很近（<180像素），优先射击
                if distance < 180:
                    # 检查是否可以朝敌人方向射击
                    shoot_candidates = []
                    # 同列：垂直射击
                    if abs(dx) < 36:  # 放宽到36像素（1.5个格子）
                        if dy < 0:
                            shoot_candidates.append((0, -1, abs(dy)))  # 向上
                        else:
                            shoot_candidates.append((0, 1, abs(dy)))  # 向下
                    # 同行：水平射击
                    if abs(dy) < 36:
                        if dx < 0:
                            shoot_candidates.append((-1, 0, abs(dx)))  # 向左
                        else:
                            shoot_candidates.append((1, 0, abs(dx)))  # 向右
                    
                    # 选择最近的射击方向
                    if shoot_candidates:
                        # 按距离排序，选择最近的
                        shoot_candidates.sort(key=lambda x: x[2])
                        for dx_cand, dy_cand, dist in shoot_candidates:
                            cand_dir = (dx_cand, dy_cand)  # 构建方向元组
                            # 检查是否安全（不指向基地，路径上无铁墙）
                            if not self._base_in_line(game_state, tank, cand_dir, dist):
                                if not self._aiming_home(game_state, tank, cand_dir):
                                    if not self._shoot_blocked_iron_only(game_state, tank, cand_dir):
                                        should_shoot = True
                                        shoot_dir = cand_dir
                                        is_model_shot = False
                                        print(f"[AI] 优先射击: 检测到敌人距离={distance}, 选择方向={cand_dir}, 敌人位置=({dx}, {dy})")
                                        # 如果选择了射击，取消移动动作
                                        action = 'wait'
                                        break
        
        if action == 'move_up':
            move_dir = 0  # 对应游戏中的movdir
        elif action == 'move_down':
            move_dir = 1
        elif action == 'move_left':
            move_dir = 2
        elif action == 'move_right':
            move_dir = 3
        elif action == 'shoot_up':
            should_shoot = True
            shoot_dir = (0, -1)
            is_model_shot = True  # 模型选择的射击
        elif action == 'shoot_down':
            should_shoot = True
            shoot_dir = (0, 1)
            is_model_shot = True
        elif action == 'shoot_left':
            should_shoot = True
            shoot_dir = (-1, 0)
            is_model_shot = True
        elif action == 'shoot_right':
            should_shoot = True
            shoot_dir = (1, 0)
            is_model_shot = True
        # wait 动作不需要做任何事
        
        # 规则：如果有子弹直冲过来，优先侧向规避
        dodge_move = self._incoming_bullet(game_state, tank)
        if dodge_move is not None:
            move_dir = dodge_move
            should_shoot = False
            shoot_dir = None
        
        # 启发：在安全且无躲避需求时，尝试朝最近敌人对齐行/列
        if move_dir is None and tank is not None and tank.life > 0:
            align_move = self._align_towards_enemy(game_state, tank)
            if align_move is not None:
                move_dir = align_move

        # 选项层对低层动作进行微调
        if option == 'defend' and move_dir is None:
            defend_move = self._move_towards_home(game_state, tank)
            if defend_move is not None:
                move_dir = defend_move
            # 防守策略：降低射击意愿，除非敌人在基地方向且很近
            if should_shoot:
                if not self._enemy_in_line(game_state, tank, shoot_dir, corridor=16, max_distance=180):
                    should_shoot = False
                    shoot_dir = None
        elif option == 'flank' and move_dir is None:
            # 绕后：尝试向敌人侧面移动
            flank_move = self._flank_enemy(game_state, tank)
            if flank_move is not None:
                move_dir = flank_move
        
        # 简单启发：如果前方有近距离敌人且冷却好，强制开火（作为备用）
        # 注意：启发式触发的射击，is_model_shot保持False
        if (not should_shoot) and (not tank.bullet.life):
            nearest = self._nearest_enemy(game_state, tank)
            if nearest:
                dx = nearest.rect.centerx - tank.rect.centerx
                dy = nearest.rect.centery - tank.rect.centery
                distance = abs(dx) + abs(dy)
                print(f"[AI DEBUG] 启发式检查: 最近敌人距离=({dx}, {dy}), 总距离={distance}")
                # 判定同列/同行（宽容 12 像素），近身优先
                if abs(dx) < 12:
                    cand_dir = (0, -1) if dy < 0 else (0, 1)
                    if not self._base_in_line(game_state, tank, cand_dir, abs(dy)):
                        should_shoot = True
                        shoot_dir = cand_dir
                        is_model_shot = False  # 明确标记为启发式触发
                        print(f"[AI DEBUG] 启发式触发射击: 同列敌人, 方向={cand_dir}")
                elif abs(dy) < 12:
                    cand_dir = (-1, 0) if dx < 0 else (1, 0)
                    if not self._base_in_line(game_state, tank, cand_dir, abs(dx)):
                        should_shoot = True
                        shoot_dir = cand_dir
                        is_model_shot = False  # 明确标记为启发式触发
                        print(f"[AI DEBUG] 启发式触发射击: 同行敌人, 方向={cand_dir}")
                # 若距离很近（<120），按主方向尝试开火
                elif abs(dx) + abs(dy) < 120:
                    if abs(dx) > abs(dy):
                        cand_dir = (-1, 0) if dx < 0 else (1, 0)
                        if not self._base_in_line(game_state, tank, cand_dir, abs(dx)) and not self._aiming_home(game_state, tank, cand_dir):
                            should_shoot = True
                            shoot_dir = cand_dir
                            is_model_shot = False  # 明确标记为启发式触发
                            print(f"[AI DEBUG] 启发式触发射击: 近距离敌人(水平), 方向={cand_dir}")
                    else:
                        cand_dir = (0, -1) if dy < 0 else (0, 1)
                        if not self._base_in_line(game_state, tank, cand_dir, abs(dy)) and not self._aiming_home(game_state, tank, cand_dir):
                            should_shoot = True
                            shoot_dir = cand_dir
                            is_model_shot = False  # 明确标记为启发式触发
                            print(f"[AI DEBUG] 启发式触发射击: 近距离敌人(垂直), 方向={cand_dir}")
        
        # 规则：若射击方向不安全或无明确目标，取消射击
        if should_shoot and shoot_dir is not None:
            enemy_inline = self._enemy_in_line(game_state, tank, shoot_dir)
            aiming_home = self._aiming_home(game_state, tank, shoot_dir)
            
            # 检查是否有非常近的敌人（挨着的情况）
            nearest = self._nearest_enemy(game_state, tank)
            very_close_enemy = False
            enemy_distance = 9999  # 默认值
            if nearest:
                dx = nearest.rect.centerx - tank.rect.centerx
                dy = nearest.rect.centery - tank.rect.centery
                enemy_distance = abs(dx) + abs(dy)
                # 如果敌人非常近（小于48像素，约2个格子），且方向大致正确
                if enemy_distance < 48:
                    # 检查方向是否大致朝向敌人
                    if shoot_dir == (0, -1) and dy < 0 and abs(dx) < 24:  # 向上
                        very_close_enemy = True
                    elif shoot_dir == (0, 1) and dy > 0 and abs(dx) < 24:  # 向下
                        very_close_enemy = True
                    elif shoot_dir == (-1, 0) and dx < 0 and abs(dy) < 24:  # 向左
                        very_close_enemy = True
                    elif shoot_dir == (1, 0) and dx > 0 and abs(dy) < 24:  # 向右
                        very_close_enemy = True
            
            # 如果敌人非常近，只检查是否指向基地或铁墙，忽略边界和其他阻挡
            if very_close_enemy:
                # 只检查最危险的情况：指向基地或铁墙
                aiming_home_strict = self._aiming_home(game_state, tank, shoot_dir)
                blocked_iron_only = self._shoot_blocked_iron_only(game_state, tank, shoot_dir)
                if aiming_home_strict or blocked_iron_only:
                    if aiming_home_strict:
                        print(f"[AI DEBUG] 近距离射击被阻止: 指向基地 (方向={shoot_dir}, 敌人距离={enemy_distance})")
                    if blocked_iron_only:
                        print(f"[AI DEBUG] 近距离射击被阻止: 路径上有铁墙 (方向={shoot_dir}, 敌人距离={enemy_distance})")
                    should_shoot = False
                    shoot_dir = None
                else:
                    print(f"[AI DEBUG] 近距离敌人强制射击: 方向={shoot_dir}, 敌人距离={enemy_distance}")
            else:
                # 正常距离的敌人，使用完整的安全检查
                blocked = self._shoot_blocked(game_state, tank, shoot_dir)
                # 放宽限制：
                # 1. 如果路径被阻挡或指向基地，绝对禁止
                # 2. 如果是模型选择的射击，即使没有明确敌人也允许（可能是预判）
                # 3. 如果是启发式触发的射击，必须有敌人才允许
                if blocked or aiming_home:
                    # 添加调试信息
                    if blocked:
                        print(f"[AI DEBUG] 射击被阻止: 路径被阻挡 (方向={shoot_dir}, 模型选择={is_model_shot})")
                    if aiming_home:
                        print(f"[AI DEBUG] 射击被阻止: 指向基地 (方向={shoot_dir}, 模型选择={is_model_shot})")
                    should_shoot = False
                    shoot_dir = None
                elif not enemy_inline:
                    # 如果方向上没有敌人
                    if is_model_shot:
                        # 模型选择的射击，允许尝试（可能是预判或探索）
                        print(f"[AI DEBUG] 模型选择射击，允许尝试: 方向={shoot_dir} (即使没有明确敌人)")
                    else:
                        # 启发式触发的射击，理论上应该有敌人，但可能检测失败
                        # 放宽限制：如果启发式触发了，即使_enemy_in_line返回False也允许射击
                        # 因为启发式规则本身已经检查了敌人位置
                        print(f"[AI DEBUG] 警告: 启发式触发射击但_enemy_in_line未检测到敌人 (方向={shoot_dir})，但仍允许射击")
                        # 不阻止，允许射击（启发式规则已经验证过）
                else:
                    print(f"[AI DEBUG] 射击通过安全检查: 方向={shoot_dir}, 有敌人={enemy_inline}, 指向基地={aiming_home}, 被阻挡={blocked}, 模型选择={is_model_shot}")
        
        return move_dir, should_shoot, shoot_dir

    def _nearest_enemy(self, game_state, tank):
        enemies = list(game_state.get('allEnemyGroup', [])) if game_state else []
        if not enemies or tank is None or tank.life <= 0:
            return None
        enemies = [e for e in enemies if getattr(e, "flash", True)]  # 只考虑已出现的
        if not enemies:
            return None
        # 以曼哈顿距离为准，找最近的敌人
        enemies.sort(key=lambda e: abs(e.rect.centerx - tank.rect.centerx) + abs(e.rect.centery - tank.rect.centery))
        return enemies[0]

    def _base_in_line(self, game_state, tank, direction, dist_limit):
        """检查射击方向上是否有基地且更近（避免友军误伤）"""
        home_group = game_state.get('homeGroup') if game_state else None
        if not home_group or len(home_group) == 0 or tank is None:
            return False
        home = list(home_group)[0]
        dx = home.rect.centerx - tank.rect.centerx
        dy = home.rect.centery - tank.rect.centery
        if direction == (0, -1) or direction == (0, 1):
            if abs(dx) < 12:
                if (direction[1] < 0 and dy < 0) or (direction[1] > 0 and dy > 0):
                    if abs(dy) <= dist_limit + 4:
                        return True
        if direction == (-1, 0) or direction == (1, 0):
            if abs(dy) < 12:
                if (direction[0] < 0 and dx < 0) or (direction[0] > 0 and dx > 0):
                    if abs(dx) <= dist_limit + 4:
                        return True
        return False

    def _incoming_bullet(self, game_state, tank, danger_distance=90):
        """
        若有敌方子弹直线逼近，返回一个侧向躲避的move_dir（0-3），否则None。
        规则简单：只检测同列/同行且朝向坦克的子弹，忽略障碍物。
        """
        enemies = list(game_state.get('allEnemyGroup', [])) if game_state else []
        if tank is None or tank.life <= 0 or not enemies:
            return None
        
        tx, ty = tank.rect.centerx, tank.rect.centery
        for enemy in enemies:
            bullet = getattr(enemy, "bullet", None)
            if bullet is None or not bullet.life:
                continue
            bx, by = bullet.rect.centerx, bullet.rect.centery
            dx, dy = tx - bx, ty - by
            dir_x, dir_y = getattr(bullet, "dir_x", 0), getattr(bullet, "dir_y", 0)
            
            # 水平直线射来
            if dir_x != 0 and abs(dy) < 12 and ((dir_x > 0 and dx > 0) or (dir_x < 0 and dx < 0)):
                if abs(dx) <= danger_distance:
                    # 侧向躲避：优先远离上边界
                    return 0 if ty > self.state_extractor.screen_height / 2 else 1  # 上 or 下
            # 垂直直线射来
            if dir_y != 0 and abs(dx) < 12 and ((dir_y > 0 and dy > 0) or (dir_y < 0 and dy < 0)):
                if abs(dy) <= danger_distance:
                    # 侧向躲避：优先远离左边界
                    return 2 if tx > self.state_extractor.screen_width / 2 else 3   # 左 or 右
        return None

    def _shoot_blocked(self, game_state, tank, direction, step=24):
        """
        判断射击方向是否被不可破坏墙体(iron)或基地阻挡。
        已移除边界检查：允许向边界方向射击。
        只阻挡铁墙、基地和基地附近的砖墙，普通砖墙可以射击（会被破坏）。
        """
        if tank is None or tank.life <= 0:
            return True
        
        iron_group = game_state.get('ironGroup') if game_state else None
        brick_group = game_state.get('brickGroup') if game_state else None
        home_group = game_state.get('homeGroup') if game_state else None
        home = list(home_group)[0] if home_group and len(home_group) > 0 else None
        x, y = tank.rect.centerx, tank.rect.centery
        dx, dy = direction
        # 避免除零
        if dx == 0 and dy == 0:
            return True

        # 只检查前几步，避免过度扫描
        check_steps = min(15, int(max(self.state_extractor.screen_width, self.state_extractor.screen_height) / step) + 2)
        for i in range(1, check_steps + 1):
            cx = x + dx * step * i
            cy = y + dy * step * i
            # 已移除边界检查，允许向边界方向射击
            
            # 不可破坏墙判定：若铁墙在路径上，则阻挡
            if iron_group:
                for iron in iron_group:
                    if iron.rect.collidepoint(cx, cy):
                        print(f"[AI DEBUG] 射击被铁墙阻挡: 位置=({cx}, {cy}) (方向={direction}, 坦克位置=({x}, {y}), 步数={i})")
                        return True
            # 基地判定
            if home and home.rect.collidepoint(cx, cy):
                print(f"[AI DEBUG] 射击被基地阻挡: 位置=({cx}, {cy}) (方向={direction}, 坦克位置=({x}, {y}), 步数={i})")
                return True
            # 基地周围砖墙保护（距离基地中心一定范围内的砖墙）
            if home and brick_group:
                for brick in brick_group:
                    # 只过滤基地附近的砖墙，半径约 120 像素
                    if abs(brick.rect.centerx - home.rect.centerx) <= 120 and abs(brick.rect.centery - home.rect.centery) <= 120:
                        if brick.rect.collidepoint(cx, cy):
                            print(f"[AI DEBUG] 射击被基地附近砖墙阻挡: 位置=({cx}, {cy}) (方向={direction}, 坦克位置=({x}, {y}), 步数={i})")
                            return True
        # 普通砖墙和边界不阻挡（可以被子弹破坏或子弹会自然消失）
        return False

    def _shoot_blocked_iron_only(self, game_state, tank, direction, step=24):
        """
        只检查铁墙阻挡，用于近距离敌人时的快速检查。
        忽略边界和砖墙，只检查不可破坏的铁墙。
        """
        if tank is None or tank.life <= 0:
            return True
        
        iron_group = game_state.get('ironGroup') if game_state else None
        if not iron_group:
            return False
        
        x, y = tank.rect.centerx, tank.rect.centery
        dx, dy = direction
        if dx == 0 and dy == 0:
            return True

        # 只检查前几步（近距离敌人）
        check_steps = 3
        for i in range(1, check_steps + 1):
            cx = x + dx * step * i
            cy = y + dy * step * i
            # 只检查铁墙
            for iron in iron_group:
                if iron.rect.collidepoint(cx, cy):
                    return True
        return False

    def _enemy_in_line(self, game_state, tank, direction, corridor=36, max_distance=360):
        """
        判断射击方向上是否有敌人（同列/同行且在一定距离内）。
        放宽容差到36像素（1.5个格子），确保能检测到同列/同行的敌人。
        忽略被障碍物遮挡的情况，仅避免明显的"朝空地打"。
        """
        enemies = list(game_state.get('allEnemyGroup', [])) if game_state else []
        if not enemies or tank is None or tank.life <= 0:
            return False
        tx, ty = tank.rect.centerx, tank.rect.centery
        dx, dy = direction
        for enemy in enemies:
            if not getattr(enemy, "flash", True):
                continue
            ex, ey = enemy.rect.centerx, enemy.rect.centery
            if dx == 0 and dy != 0:
                # 垂直方向：x 基本重合，且敌人在前方
                x_diff = abs(ex - tx)
                y_diff = abs(ey - ty)
                if x_diff <= corridor and ((dy > 0 and ey > ty) or (dy < 0 and ey < ty)):
                    if y_diff <= max_distance:
                        print(f"[AI DEBUG] _enemy_in_line: 检测到垂直方向敌人 (x差={x_diff}, y差={y_diff}, 方向={direction})")
                        return True
            elif dy == 0 and dx != 0:
                # 水平方向：y 基本重合，且敌人在前方
                x_diff = abs(ex - tx)
                y_diff = abs(ey - ty)
                if y_diff <= corridor and ((dx > 0 and ex > tx) or (dx < 0 and ex < tx)):
                    if x_diff <= max_distance:
                        print(f"[AI DEBUG] _enemy_in_line: 检测到水平方向敌人 (x差={x_diff}, y差={y_diff}, 方向={direction})")
                        return True
        print(f"[AI DEBUG] _enemy_in_line: 未检测到敌人 (方向={direction}, 容差={corridor})")
        return False

    def _align_towards_enemy(self, game_state, tank, corridor=12, max_distance=240):
        """
        朝最近敌人对齐行/列的启发式：
        - 若当前已同列/同行则不强制移动。
        - 优先缩小游戏在 x 或 y 的偏差（取绝对值更大的轴）。
        - 避开正在该轴方向逼近的敌方子弹；必要时靠近掩体。
        """
        enemy = self._nearest_enemy(game_state, tank)
        if not enemy:
            return None
        
        tx, ty = tank.rect.centerx, tank.rect.centery
        ex, ey = enemy.rect.centerx, enemy.rect.centery
        dx = ex - tx
        dy = ey - ty
        
        # 已经同列/同行则不做对线移动
        if abs(dx) <= corridor or abs(dy) <= corridor:
            return None
        
        # 选择主轴：谁偏差更大就往那轴移动
        move_dir = None
        if abs(dx) > abs(dy):
            # 想水平对线
            if not self._axis_threatened_by_bullet(game_state, tank, axis='y'):
                move_dir = 3 if dx > 0 else 2  # 右 or 左
        else:
            # 想垂直对线
            if not self._axis_threatened_by_bullet(game_state, tank, axis='x'):
                move_dir = 1 if dy > 0 else 0  # 下 or 上
        
        if move_dir is None:
            return None
        
        # 估算目标位置（单步）并确认不暴露在近距离子弹线且有一定掩体
        step = 6  # 坦克单步近似
        nx, ny = tx, ty
        if move_dir == 0:
            ny -= step
        elif move_dir == 1:
            ny += step
        elif move_dir == 2:
            nx -= step
        elif move_dir == 3:
            nx += step
        
        # 若对线后被近距离敌方子弹直线威胁，且附近无掩体，则放弃
        if self._position_threatened_by_bullet(game_state, (nx, ny), danger_distance=max_distance / 2):
            if not self._has_cover_nearby(game_state, (nx, ny), radius=28):
                return None
        
        return move_dir

    def _axis_threatened_by_bullet(self, game_state, tank, axis='x', corridor=12, danger_distance=140):
        """
        检测是否有敌方子弹沿指定轴方向直扑当前坦克所在的行/列。
        axis='x' 表示检测同列的纵向射击，axis='y' 检测同行的横向射击。
        """
        enemies = list(game_state.get('allEnemyGroup', [])) if game_state else []
        if not enemies or tank is None or tank.life <= 0:
            return False
        tx, ty = tank.rect.centerx, tank.rect.centery
        for enemy in enemies:
            bullet = getattr(enemy, "bullet", None)
            if bullet is None or not bullet.life:
                continue
            bx, by = bullet.rect.centerx, bullet.rect.centery
            dir_x, dir_y = getattr(bullet, "dir_x", 0), getattr(bullet, "dir_y", 0)
            if axis == 'x':
                # 子弹纵向运动，同列且朝向坦克
                if abs(bx - tx) <= corridor and dir_y != 0:
                    if (dir_y > 0 and by < ty) or (dir_y < 0 and by > ty):
                        if abs(by - ty) <= danger_distance:
                            return True
            else:
                # axis == 'y'：子弹横向运动，同列 y
                if abs(by - ty) <= corridor and dir_x != 0:
                    if (dir_x > 0 and bx < tx) or (dir_x < 0 and bx > tx):
                        if abs(bx - tx) <= danger_distance:
                            return True
        return False

    def _position_threatened_by_bullet(self, game_state, pos, corridor=12, danger_distance=140):
        """判断给定位置是否被敌方子弹直线威胁。"""
        enemies = list(game_state.get('allEnemyGroup', [])) if game_state else []
        if not enemies:
            return False
        px, py = pos
        for enemy in enemies:
            bullet = getattr(enemy, "bullet", None)
            if bullet is None or not bullet.life:
                continue
            bx, by = bullet.rect.centerx, bullet.rect.centery
            dir_x, dir_y = getattr(bullet, "dir_x", 0), getattr(bullet, "dir_y", 0)
            if dir_x != 0 and abs(by - py) <= corridor:
                if (dir_x > 0 and bx < px) or (dir_x < 0 and bx > px):
                    if abs(bx - px) <= danger_distance:
                        return True
            if dir_y != 0 and abs(bx - px) <= corridor:
                if (dir_y > 0 and by < py) or (dir_y < 0 and by > py):
                    if abs(by - py) <= danger_distance:
                        return True
        return False

    def _has_cover_nearby(self, game_state, pos, radius=28):
        """检测指定位置附近是否有铁墙或砖墙作为掩体。"""
        iron_group = game_state.get('ironGroup') if game_state else None
        brick_group = game_state.get('brickGroup') if game_state else None
        px, py = pos
        if iron_group:
            for iron in iron_group:
                if abs(iron.rect.centerx - px) <= radius and abs(iron.rect.centery - py) <= radius:
                    return True
        if brick_group:
            for brick in brick_group:
                if abs(brick.rect.centerx - px) <= radius and abs(brick.rect.centery - py) <= radius:
                    return True
        return False

    # ---------------- 高层选项策略（可学习） ----------------
    def _select_option_learned(self, screen, game_state, tank):
        """
        使用独立策略/价值网络选择高层选项（advance/defend/flank）。
        若未加载选项模型，则返回 None。
        """
        if self.option_agent is None:
            return None
        if tank is None or tank.life <= 0:
            return None
        try:
            visual_state, feature_vector = self.state_extractor.extract_full_state(screen, game_state)
            idx = self.option_agent.select_action(visual_state, feature_vector, training=False)
            return self.option_action_map.get(idx, None)
        except Exception as e:
            print(f"[AI OPTION ERROR] 选项推理失败: {e}")
            return None

    # ---------------- 选项层辅助 ----------------
    def _select_option(self, game_state, tank, base_safe_radius=120, enemy_near_base=160):
        """
        粗分三个选项：
        - defend: 敌人或敌弹威胁基地附近
        - flank: 敌人存在且未威胁基地，尝试侧向接近
        - advance: 默认（不额外干预）
        """
        if tank is None or tank.life <= 0:
            return 'advance'
        home_group = game_state.get('homeGroup') if game_state else None
        enemies = list(game_state.get('allEnemyGroup', [])) if game_state else []
        if not home_group or len(home_group) == 0 or not enemies:
            return 'advance'
        home = list(home_group)[0]
        hx, hy = home.rect.centerx, home.rect.centery
        # 若有敌人或子弹进入基地近邻，优先防守
        for enemy in enemies:
            if not getattr(enemy, "flash", True):
                continue
            ex, ey = enemy.rect.centerx, enemy.rect.centery
            if abs(ex - hx) + abs(ey - hy) <= enemy_near_base:
                return 'defend'
            bullet = getattr(enemy, "bullet", None)
            if bullet and bullet.life:
                bx, by = bullet.rect.centerx, bullet.rect.centery
                if abs(bx - hx) + abs(by - hy) <= enemy_near_base:
                    return 'defend'
        return 'flank'

    def _move_towards_home(self, game_state, tank, corridor=12):
        """朝基地移动（保持同行/同列），用于防守回防。"""
        home_group = game_state.get('homeGroup') if game_state else None
        if tank is None or tank.life <= 0 or not home_group or len(home_group) == 0:
            return None
        home = list(home_group)[0]
        tx, ty = tank.rect.centerx, tank.rect.centery
        hx, hy = home.rect.centerx, home.rect.centery
        dx, dy = hx - tx, hy - ty
        if abs(dx) > abs(dy):
            return 3 if dx > 0 else 2
        else:
            return 1 if dy > 0 else 0

    def _flank_enemy(self, game_state, tank, side_bias=1):
        """
        绕后/侧向接近：对最近敌人侧移一格方向。
        side_bias: 1 右侧优先，-1 左侧优先。
        """
        enemy = self._nearest_enemy(game_state, tank)
        if not enemy or tank is None or tank.life <= 0:
            return None
        tx, ty = tank.rect.centerx, tank.rect.centery
        ex, ey = enemy.rect.centerx, enemy.rect.centery
        dx, dy = ex - tx, ey - ty
        # 若已同列/同行则保持侧向移动
        if abs(dx) <= 12:
            return 3 if side_bias > 0 else 2
        if abs(dy) <= 12:
            return 1 if side_bias > 0 else 0
        # 否则朝侧面靠近：先选主轴，再侧偏一步
        if abs(dx) > abs(dy):
            return 1 if dy > 0 else 0  # 先在次轴靠拢
        else:
            return 3 if dx > 0 else 2

    def _home_in_line(self, game_state, tank, direction, corridor=14):
        """
        判断射击方向上是否存在基地且位于坦克前方同列/同行。
        用于严禁朝基地方向射击（即便后方有敌人）。
        """
        home_group = game_state.get('homeGroup') if game_state else None
        if not home_group or tank is None or tank.life <= 0:
            return False
        home = list(home_group)[0]
        tx, ty = tank.rect.centerx, tank.rect.centery
        hx, hy = home.rect.centerx, home.rect.centery
        dx, dy = direction
        if dx == 0 and dy != 0:
            if abs(hx - tx) <= corridor and ((dy > 0 and hy > ty) or (dy < 0 and hy < ty)):
                return True
        if dy == 0 and dx != 0:
            if abs(hy - ty) <= corridor and ((dx > 0 and hx > tx) or (dx < 0 and hx < tx)):
                return True
        return False

    def _aiming_home(self, game_state, tank, direction, lateral_tol=10):
        """
        更宽松的判定：若射击方向的半平面包含基地，且基地到该方向直线的侧向距离较小，则判定为朝基地射击。
        防止非严格同列/同行时仍对基地开火。
        """
        home_group = game_state.get('homeGroup') if game_state else None
        if not home_group or tank is None or tank.life <= 0:
            return False
        home = list(home_group)[0]
        tx, ty = tank.rect.centerx, tank.rect.centery
        hx, hy = home.rect.centerx, home.rect.centery
        dx, dy = direction
        if dx == 0 and dy == 0:
            return True
        # 向量到基地
        vx, vy = hx - tx, hy - ty
        # 若基地不在射击前方半平面，则不算
        if vx * dx + vy * dy <= 0:
            return False
        # 计算基地到射击方向直线的侧向距离（用叉乘近似，无需开方）
        # distance = |v x d| / |d|
        cross = abs(vx * dy - vy * dx)
        norm_d = abs(dx) + abs(dy)
        if norm_d == 0:
            return True
        # 乘以缩放避免浮点
        lateral = cross / norm_d
        return lateral <= lateral_tol
