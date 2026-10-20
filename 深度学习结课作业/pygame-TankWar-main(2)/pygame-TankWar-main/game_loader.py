import pygame
import sys
import os
import wall
import myTank
import enemyTank
import food
import maps
import map_loader
import special_effects

class Game:
    def __init__(self):
        # 通用加载
        # ----------------------------------------------------------------------------
        pygame.init()
        # 用于加载和播放声音的 pygame 模块
        pygame.mixer.init()
        # 加载屏幕
        resolution = 750, 630
        self.screen = pygame.display.set_mode(resolution)
        pygame.display.set_caption("Tank War - 点击窗口获得焦点")
        # 确保窗口可以获得焦点和键盘输入
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.ACTIVEEVENT])
        # 启用键盘重复
        pygame.key.set_repeat(200, 50)  # 200ms延迟，50ms间隔
        # 获取脚本所在目录，确保路径正确
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 加载图片,音乐,音效.
        self.background_image = pygame.image.load(os.path.join(script_dir, "image", "background.png"))
        # 右边提示图片加载
        self.background_image_level_mode = pygame.image.load(os.path.join(script_dir, "image", "background_level_model_tishi.png"))
        self.background_image_endless_mode = pygame.image.load(os.path.join(script_dir, "image", "background_endless_mode_tishi.png"))
        self.background_image_heads_up_mode = pygame.image.load(os.path.join(script_dir, "image", "background_heads_up_mode_tishi.png"))

        self.enemy_icon = pygame.image.load(os.path.join(script_dir, "image", "enemy.png"))
        self.heart_icon = pygame.image.load(os.path.join(script_dir, "image", "heart.png"))

        # 游戏结束图片
        self.game_over_player1_win = pygame.image.load(os.path.join(script_dir, "image", "game_over_player1_win.png"))
        self.game_over_player2_win = pygame.image.load(os.path.join(script_dir, "image", "game_over_player2_win.png"))
        self.game_over_win = pygame.image.load(os.path.join(script_dir, "image", "game_over_win.png"))
        self.game_over_fail = pygame.image.load(os.path.join(script_dir, "image", "game_over_fail.png"))
        # 暂停图片加载
        self.game_pause_image = pygame.image.load(os.path.join(script_dir, "image", "game_pause.png"))

        # 音效加载-------------------------------------------------------
        self.bang_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "bang.wav"))
        self.bang_sound.set_volume(1)
        self.start_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "start.wav"))
        # 队友加载和吃道具音效
        self.add_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "add.wav"))
        # 子弹打出音效（正式）
        self.attack_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "attack.mp3"))
        # 获取道具音效（正式）
        self.get_props_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "get_props.mp3"))
        # 道具出现音效（正式）
        self.prop_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "prop.mp3"))
        # 炸弹爆炸特效（正式）
        self.prop_boom_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "prop_boom.wav"))
        # 打到墙上的音效（正式）
        self.wall_sound = pygame.mixer.Sound(os.path.join(script_dir, "music", "wall.mp3"))
        # 定义精灵组:坦克，我方坦克，敌方坦克，敌方子弹
        # 用于保存和管理多个 Sprite 对象的容器类。pygame.sprite.Group()
        self.allTankGroup = pygame.sprite.Group()
        self.mytankGroup = pygame.sprite.Group()
        self.allEnemyGroup = pygame.sprite.Group()
        self.redEnemyGroup = pygame.sprite.Group()
        self.greenEnemyGroup = pygame.sprite.Group()
        self.otherEnemyGroup = pygame.sprite.Group()
        self.enemyBulletGroup = pygame.sprite.Group()

        # 自定义事件
        # 创建敌方坦克延迟200
        self.DELAYEVENT = pygame.constants.USEREVENT
        pygame.time.set_timer(self.DELAYEVENT, 200)
        # 创建 敌方 子弹延迟1000
        self.ENEMYBULLETNOTCOOLINGEVENT = pygame.constants.USEREVENT + 1
        pygame.time.set_timer(self.ENEMYBULLETNOTCOOLINGEVENT, 1000)
        # 创建 我方 子弹延迟200
        self.MYBULLETNOTCOOLINGEVENT = pygame.constants.USEREVENT + 2
        pygame.time.set_timer(self.MYBULLETNOTCOOLINGEVENT, 200)
        # 敌方坦克 静止8000
        self.NOTMOVEEVENT = pygame.constants.USEREVENT + 3
        pygame.time.set_timer(self.NOTMOVEEVENT, 8000)

        # ...............参数..................................
        self.isEndless = False
        self.delay = 100
        # 敌军剩余数量
        self.remaining_enemy = 20
        # 移动参数
        self.moving = 0
        self.movdir = 0
        self.moving2 = 0
        self.movdir2 = 0
        self.running_T1 = True
        self.running_T2 = True

        self.enemyNumber = 3
        self.enemyCouldMove = True
        self.switch_R1_R2_image = True

        self.overGameLoss = False
        self.overGameWin = False
        # 关于保护罩的参数
        self.invincible_T1 = 200  # 是否无敌
        self.invincible_T2 = 200

        self.clock = pygame.time.Clock()

        # 特效和地图的初始化
        self.special_effect = special_effects.SE()
        self.bgMap = maps.Map()

        # 创建我方坦克
        self.myTank_T1 = myTank.MyTank(1)
        self.allTankGroup.add(self.myTank_T1)
        self.mytankGroup.add(self.myTank_T1)
        self.myTank_T2 = myTank.MyTank(2)
        self.allTankGroup.add(self.myTank_T2)
        self.mytankGroup.add(self.myTank_T2)

        # 创建食物/道具 但不显示
        self.prop = food.Food()
        self.bulletBoomGroup = []
        # 是否打开音效
        self.isSoundEffect = True

        # 基地是否是砖块
        self.iron_time = 0
        
        # AI控制相关
        self.ai_mode = False
        self.ai_agent = None
        self.ai_model_path = None
        self.ai_option_model_path = None

    # 暂停函数----------------------------------------------------------------
    # 功能：点击鼠标进行暂停 并显示图片在桌面
    def game_pause(self):
        self.start_sound.stop()
        while True:
            # 显示图片
            self.screen.blit(self.game_pause_image, (250, 250))
            pygame.display.flip()
            # 如果点击鼠标就暂停结束
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    # 游戏结束函数------------------------------------------------------------
    # 功能：弹出游戏结束界面，并根据结果的不同显示不同结果，并提供退出游戏
    def game_over(self,option):
        while True:
            # 根据游戏结局不同 选择不同图片显示
            if option == 1:
                self.screen.blit(self.game_over_win, (250 , 250))
            elif option == 2:
                self.screen.blit(self.game_over_fail, (250, 250))
            elif option == 3:
                self.screen.blit(self.game_over_player1_win, (250, 250))
            elif option == 4:
                self.screen.blit(self.game_over_player2_win, (250, 250))

            pygame.display.flip()
            key_pressed = pygame.key.get_pressed()
            # 按esc退出游戏
            if key_pressed[pygame.K_ESCAPE]:
                self.start_sound.stop()
                return 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    # 处理事件函数-----------------------------------------------------------
    # 功能：主要就是对冷却事件的处理
    def event_section(self):
        # 注意：这里只处理特定事件，不消耗所有事件
        # pygame.key.get_pressed()在operation_detection_section中使用，不需要事件
        for event in pygame.event.get():
            # 如果鼠标单击
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.game_pause()
            # 如果退出
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 我方子弹冷却事件
            if event.type == self.MYBULLETNOTCOOLINGEVENT:
                self.myTank_T1.bulletNotCooling = True
                # AI模式下，玩家2的子弹冷却也在这里处理
                if self.ai_mode and self.myTank_T2.life > 0:
                    self.myTank_T2.bulletNotCooling = True

            # 敌方子弹冷却事件
            if event.type == self.ENEMYBULLETNOTCOOLINGEVENT:
                for each in self.allEnemyGroup:
                    each.bulletNotCooling = True

            # 敌方坦克静止事件
            if event.type == self.NOTMOVEEVENT:
                self.enemyCouldMove = True

            # 创建敌方坦克延迟
            if event.type == self.DELAYEVENT:
                # 敌方坦克最大数量
                if self.enemyNumber < 4 and self.remaining_enemy-self.enemyNumber >=1:
                    enemy = enemyTank.EnemyTank()
                    if pygame.sprite.spritecollide(enemy, self.allTankGroup, False, None):
                        break
                    self.allEnemyGroup.add(enemy)
                    self.allTankGroup.add(enemy)
                    self.enemyNumber += 1
                    if enemy.isred == True:
                        self.redEnemyGroup.add(enemy)
                    elif enemy.kind == 3:
                        self.greenEnemyGroup.add(enemy)
                    else:
                        self.otherEnemyGroup.add(enemy)

            # 作弊按钮（只处理F3，不影响其他按键）
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.isSoundEffect = not self.isSoundEffect
                    self.start_sound.stop()
                # 不处理其他按键，让operation_detection_section处理
                # if event.key == pygame.K_c and pygame.KMOD_CTRL:
                #     pygame.quit()
                #     sys.exit()
                # if event.key == pygame.K_e:
                #     self.myTank_T1.levelUp()
                # if event.key == pygame.K_q:
                #     self.myTank_T1.levelDown()
                # if event.key == pygame.K_3:
                #     self.myTank_T1.levelUp()
                #     self.myTank_T1.levelUp()
                #     self.myTank_T1.level = 3
                # if event.key == pygame.K_2:
                #     if self.myTank_T1.speed == 3:
                #         self.myTank_T1.speed = 24
                #     else:
                #         self.myTank_T1.speed = 3
                # if event.key == pygame.K_1:
                #     for x, y in [(11, 23), (12, 23), (13, 23), (14, 23), (11, 24), (14, 24), (11, 25), (14, 25)]:
                #         self.bgMap.brick = wall.Brick()
                #         self.bgMap.brick.rect.left, self.bgMap.brick.rect.top = 3 + x * 24, 3 + y * 24
                #         self.bgMap.brickGroup.add(self.bgMap.brick)
                # if event.key == pygame.K_4:
                #     for x, y in [(11, 23), (12, 23), (13, 23), (14, 23), (11, 24), (14, 24), (11, 25), (14, 25)]:
                #         self.bgMap.iron = wall.Iron()
                #         self.bgMap.iron.rect.left, self.bgMap.iron.rect.top = 3 + x * 24, 3 + y * 24
                #         self.bgMap.ironGroup.add(self.bgMap.iron)

    # 处理事件函数（单挑版）---------------------------------------------------------
    # 功能：主要就是对冷却事件的处理
    def event_section_singled_out(self):
        for event in pygame.event.get():
            # 如果鼠标单击
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.game_pause()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # 我方子弹冷却事件
            if event.type == self.MYBULLETNOTCOOLINGEVENT:
                self.myTank_T1.bulletNotCooling = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.isSoundEffect = not self.isSoundEffect
                    self.start_sound.stop()
    # AI控制函数--------------------------------------------------------
    # 功能：使用AI控制玩家2
    def ai_control_section(self):
        """AI控制玩家2"""
        if not self.ai_mode or self.ai_agent is None:
            if self.ai_mode and self.ai_agent is None:
                print("[AI WARNING] AI模式已启用但AI代理未初始化")
            return
        
        # 初始化变量，确保在所有情况下都有定义
        move_dir = None
        should_shoot = False
        shoot_dir = None
        
        if self.myTank_T2.life > 0:
            # 处理移动中的状态（继续移动）
            if self.moving2:
                self.moving2 -= 1
                self.allTankGroup.remove(self.myTank_T2)
                if self.movdir2 == 0:
                    self.myTank_T2.moveUp(self.allTankGroup, self.bgMap.brickGroup,
                                         self.bgMap.ironGroup, self.bgMap.riverGroup)
                    self.running_T2 = True
                elif self.movdir2 == 1:
                    self.myTank_T2.moveDown(self.allTankGroup, self.bgMap.brickGroup,
                                           self.bgMap.ironGroup, self.bgMap.riverGroup)
                    self.running_T2 = True
                elif self.movdir2 == 2:
                    self.myTank_T2.moveLeft(self.allTankGroup, self.bgMap.brickGroup,
                                           self.bgMap.ironGroup, self.bgMap.riverGroup)
                    self.running_T2 = True
                elif self.movdir2 == 3:
                    self.myTank_T2.moveRight(self.allTankGroup, self.bgMap.brickGroup,
                                            self.bgMap.ironGroup, self.bgMap.riverGroup)
                    self.running_T2 = True
                self.allTankGroup.add(self.myTank_T2)
            
            # 如果不在移动中，获取新的AI动作
            if not self.moving2:
                # 获取游戏状态
                game_state = {
                    'myTank_T1': self.myTank_T1,
                    'myTank_T2': self.myTank_T2,
                    'allEnemyGroup': self.allEnemyGroup,
                    'prop': self.prop,
                    'ironGroup': self.bgMap.ironGroup,
                    'brickGroup': self.bgMap.brickGroup,
                    'remaining_enemy': self.remaining_enemy,
                    'enemyNumber': self.enemyNumber,
                    'enemyCouldMove': self.enemyCouldMove,
                    'invincible_T2': self.invincible_T2,
                    'homeGroup': self.bgMap.homeGroup,
                }
                
                # 获取AI动作
                try:
                    result = self.ai_agent.execute_action(
                        self.screen, game_state, self.myTank_T2
                    )
                    # 确保返回值是元组
                    if isinstance(result, tuple) and len(result) == 3:
                        move_dir, should_shoot, shoot_dir = result
                    else:
                        print(f"[AI ERROR] execute_action返回了意外的类型: {type(result)}, 值: {result}")
                        move_dir, should_shoot, shoot_dir = None, False, None
                    # 只在有动作时打印
                    if move_dir is not None:
                        print(f"[AI] 执行移动: 方向={move_dir}, 坦克位置=({self.myTank_T2.rect.left}, {self.myTank_T2.rect.top})")
                    if should_shoot:
                        print(f"[AI] 执行射击: 方向={shoot_dir}")
                except TypeError as e:
                    print(f"[AI ERROR] 解包错误: {e}")
                    print(f"[AI ERROR] execute_action返回值类型: {type(result) if 'result' in locals() else 'unknown'}")
                    import traceback
                    traceback.print_exc()
                    move_dir, should_shoot, shoot_dir = None, False, None
                except Exception as e:
                    print(f"[AI ERROR] AI动作获取失败: {e}")
                    import traceback
                    traceback.print_exc()
                    move_dir, should_shoot, shoot_dir = None, False, None
                
                # 执行移动
                if move_dir is not None:
                    self.allTankGroup.remove(self.myTank_T2)
                    if move_dir == 0:
                        if not self.myTank_T2.moveUp(self.allTankGroup, self.bgMap.brickGroup,
                                                     self.bgMap.ironGroup, self.bgMap.riverGroup):
                            self.moving2 = 7
                            self.movdir2 = 0
                            self.running_T2 = True
                    elif move_dir == 1:
                        if not self.myTank_T2.moveDown(self.allTankGroup, self.bgMap.brickGroup,
                                                      self.bgMap.ironGroup, self.bgMap.riverGroup):
                            self.moving2 = 7
                            self.movdir2 = 1
                            self.running_T2 = True
                    elif move_dir == 2:
                        if not self.myTank_T2.moveLeft(self.allTankGroup, self.bgMap.brickGroup,
                                                       self.bgMap.ironGroup, self.bgMap.riverGroup):
                            self.moving2 = 7
                            self.movdir2 = 2
                            self.running_T2 = True
                    elif move_dir == 3:
                        if not self.myTank_T2.moveRight(self.allTankGroup, self.bgMap.brickGroup,
                                                        self.bgMap.ironGroup, self.bgMap.riverGroup):
                            self.moving2 = 7
                            self.movdir2 = 3
                            self.running_T2 = True
                    self.allTankGroup.add(self.myTank_T2)
            
            # 执行射击（无论是否在移动），移除冷却限制
            if should_shoot and not self.myTank_T2.bullet.life:
                self.myTank_T2.dir_x, self.myTank_T2.dir_y = shoot_dir
                if self.isSoundEffect:
                    self.attack_sound.play()
                self.myTank_T2.shoot()
    
    # 玩家操作检测函数--------------------------------------------------------
    # 功能：对键盘进行检测 并对玩家一和玩家二的操作进行移动
    def operation_detection_section(self):
        # 检查窗口焦点
        window_active = pygame.display.get_active()
        if not window_active:
            if not hasattr(self, '_focus_warning_printed'):
                print("[DEBUG] ⚠ 警告: 游戏窗口没有焦点！请点击游戏窗口")
                self._focus_warning_printed = True
            # 即使没有焦点也继续，因为get_pressed()可能仍然工作
        
        # 使用get_pressed()检测持续按下的键
        key_pressed = pygame.key.get_pressed()
        
        # 调试：检查窗口状态和按键（定期打印，不只是第一次）
        if not hasattr(self, '_key_check_count'):
            self._key_check_count = 0
        self._key_check_count += 1
        if self._key_check_count % 60 == 0:  # 每秒打印一次
            print(f"[DEBUG] 窗口焦点状态: {window_active}, 按键检测 - W: {key_pressed[pygame.K_w]}, S: {key_pressed[pygame.K_s]}, A: {key_pressed[pygame.K_a]}, D: {key_pressed[pygame.K_d]}")
        
        # 调试日志：检查键盘输入（每次按键都打印）
        debug_keys = []
        if key_pressed[pygame.K_w]: debug_keys.append('W')
        if key_pressed[pygame.K_s]: debug_keys.append('S')
        if key_pressed[pygame.K_a]: debug_keys.append('A')
        if key_pressed[pygame.K_d]: debug_keys.append('D')
        if key_pressed[pygame.K_j]: debug_keys.append('J')
        if debug_keys:
            print(f"[DEBUG] ✓✓✓ 检测到按键: {', '.join(debug_keys)}, 玩家1生命: {self.myTank_T1.life}, moving: {self.moving}, 窗口焦点: {window_active}")
        
        # 玩家一的移动、射击操作（在AI模式下也正常工作）
        # 参数 moving movdir alltankGroup self.bgMap.brickGroup, self.bgMap.ironGroup,self.bgMap.riverGroup
        # 确保在AI模式下也能正常检测玩家1的操作
        if self.myTank_T1.life > 0:  # 如果有生命
            if self.moving:
                # 继续移动
                self.moving -= 1
                if self.movdir == 0:
                    self.allTankGroup.remove(self.myTank_T1)
                    if self.myTank_T1.moveUp(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                             self.bgMap.riverGroup):
                        self.moving += 1
                    self.allTankGroup.add(self.myTank_T1)
                    self.running_T1 = True
                elif self.movdir == 1:
                    self.allTankGroup.remove(self.myTank_T1)
                    if self.myTank_T1.moveDown(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                               self.bgMap.riverGroup):
                        self.moving += 1
                    self.allTankGroup.add(self.myTank_T1)
                    self.running_T1 = True
                elif self.movdir == 2:
                    self.allTankGroup.remove(self.myTank_T1)
                    if self.myTank_T1.moveLeft(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                               self.bgMap.riverGroup):
                        self.moving += 1
                    self.allTankGroup.add(self.myTank_T1)
                    self.running_T1 = True
                elif self.movdir == 3:
                    self.allTankGroup.remove(self.myTank_T1)
                    if self.myTank_T1.moveRight(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                                self.bgMap.riverGroup):
                        self.moving += 1
                    self.allTankGroup.add(self.myTank_T1)
                    self.running_T1 = True

            # 检测新的移动按键（允许在移动过程中改变方向）
            # 检查WASD键
            new_move_dir = None
            if key_pressed[pygame.K_w] or key_pressed[pygame.K_UP]:
                new_move_dir = 0
                key_name = "W/↑"
            elif key_pressed[pygame.K_s] or key_pressed[pygame.K_DOWN]:
                new_move_dir = 1
                key_name = "S/↓"
            elif key_pressed[pygame.K_a] or key_pressed[pygame.K_LEFT]:
                new_move_dir = 2
                key_name = "A/←"
            elif key_pressed[pygame.K_d] or key_pressed[pygame.K_RIGHT]:
                new_move_dir = 3
                key_name = "D/→"
            
            # 如果有新的移动输入，且（没有在移动 或 方向改变了）
            if new_move_dir is not None and (not self.moving or self.movdir != new_move_dir):
                print(f"[DEBUG] 玩家1: 按下{key_name}键，开始移动，方向: {new_move_dir}")
                self.moving = 7
                self.movdir = new_move_dir
                self.running_T1 = True
                self.allTankGroup.remove(self.myTank_T1)
                collision = False
                if new_move_dir == 0:
                    collision = self.myTank_T1.moveUp(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                             self.bgMap.riverGroup)
                elif new_move_dir == 1:
                    collision = self.myTank_T1.moveDown(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                               self.bgMap.riverGroup)
                elif new_move_dir == 2:
                    collision = self.myTank_T1.moveLeft(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                               self.bgMap.riverGroup)
                elif new_move_dir == 3:
                    collision = self.myTank_T1.moveRight(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                                self.bgMap.riverGroup)
                if collision:
                    print(f"[DEBUG] 玩家1: {key_name}键移动遇到碰撞")
                    self.moving = 0
                self.allTankGroup.add(self.myTank_T1)
            # 如果按j 则是坦克1发射子弹
            if key_pressed[pygame.K_j]:
                if not self.myTank_T1.bullet.life:
                    print("[DEBUG] 玩家1: 按下J键，发射子弹")
                    if self.isSoundEffect:
                        self.attack_sound.play()
                    self.myTank_T1.shoot()
                elif self.myTank_T1.bullet.life:
                    print("[DEBUG] 玩家1: 子弹已存在，无法发射")

        # 玩家二的移动操作（如果AI模式关闭）
        if not self.ai_mode and self.myTank_T2.life > 0:
            if self.moving2:
                self.moving2 -= 1
                if self.movdir2 == 0:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveUp(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                          self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.running_T2 = True
                if self.movdir2 == 1:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveDown(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                            self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.running_T2 = True
                if self.movdir2 == 2:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveLeft(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                            self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.running_T2 = True
                if self.movdir2 == 3:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveRight(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                             self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.running_T2 = True

            if not self.moving2:
                if key_pressed[pygame.K_UP]:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveUp(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                          self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.moving2 = 7
                    self.movdir2 = 0
                    self.running_T2 = True
                elif key_pressed[pygame.K_DOWN]:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveDown(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                            self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.moving2 = 7
                    self.movdir2 = 1
                    self.running_T2 = True
                elif key_pressed[pygame.K_LEFT]:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveLeft(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                            self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.moving2 = 7
                    self.movdir2 = 2
                    self.running_T2 = True
                elif key_pressed[pygame.K_RIGHT]:
                    self.allTankGroup.remove(self.myTank_T2)
                    self.myTank_T2.moveRight(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup,
                                             self.bgMap.riverGroup)
                    self.allTankGroup.add(self.myTank_T2)
                    self.moving2 = 7
                    self.movdir2 = 3
                    self.running_T2 = True
            # 如果点击0 则是发射子弹
            if key_pressed[pygame.K_KP0]:
                if not self.myTank_T2.bullet.life:
                    if self.isSoundEffect:
                        self.attack_sound.play()
                    self.myTank_T2.shoot()

    # 坦克显示函数---------------------------------------------------------
    # 功能：对我方坦克和敌方坦克进行显示
    def tank_display_section(self):
        # 画我方坦克1
        if self.myTank_T1.life > 0:
            if not (self.delay % 5):
                self.switch_R1_R2_image = not self.switch_R1_R2_image
            if self.switch_R1_R2_image and self.running_T1:
                self.screen.blit(self.myTank_T1.tank_R0, (self.myTank_T1.rect.left, self.myTank_T1.rect.top))
                self.running_T1 = False
            else:
                self.screen.blit(self.myTank_T1.tank_R1, (self.myTank_T1.rect.left, self.myTank_T1.rect.top))

            # 画保护罩 坦克1
            if self.invincible_T1 > 0:
                self.invincible_T1 -= 1
                if self.invincible_T1 % 3 == 0:
                    self.special_effect.SE_protect(self.screen, self.myTank_T1.rect.left, self.myTank_T1.rect.top,
                                                   self.invincible_T1)

        # 画我方坦克2（AI控制）
        if self.myTank_T2.life > 0:
            if self.switch_R1_R2_image and self.running_T2:
                self.screen.blit(self.myTank_T2.tank_R0, (self.myTank_T2.rect.left, self.myTank_T2.rect.top))
                self.running_T2 = False
            else:
                self.screen.blit(self.myTank_T2.tank_R1, (self.myTank_T2.rect.left, self.myTank_T2.rect.top))
            # 画保护罩 坦克2
            if self.invincible_T2 > 0:
                self.invincible_T2 -= 1
                if self.invincible_T2 % 3 == 0:
                    self.special_effect.SE_protect(self.screen, self.myTank_T2.rect.left, self.myTank_T2.rect.top,
                                                   self.invincible_T2)
            # AI模式下，在坦克2上方显示"AI"标识
            if self.ai_mode:
                font = pygame.font.Font(None, 20)
                ai_text = font.render("AI", True, (0, 255, 0))
                self.screen.blit(ai_text, (self.myTank_T2.rect.left, self.myTank_T2.rect.top - 15))

        # 画敌方坦克
        for each in self.allEnemyGroup:
            # 判断5毛钱特效是否播放
            if each.flash:
                # 　判断画左动作还是右动作
                if self.switch_R1_R2_image:
                    self.screen.blit(each.tank_R0, (each.rect.left, each.rect.top))
                    # 如果坦克可以移动
                    if self.enemyCouldMove:
                        self.allTankGroup.remove(each)
                        each.move(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup, self.bgMap.riverGroup)
                        self.allTankGroup.add(each)
                else:
                    self.screen.blit(each.tank_R1, (each.rect.left, each.rect.top))
                    if self.enemyCouldMove:
                        self.allTankGroup.remove(each)
                        each.move(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup, self.bgMap.riverGroup)
                        self.allTankGroup.add(each)
            else:
                # 播放5毛钱特效
                if each.times > 0:
                    each.times -= 1
                    self.special_effect.SE_appearance(self.screen, 3 + each.x * 12 * 24, 3, each.times)
                if each.times == 0:
                    each.flash = True

    # 子弹显示函数-------------------------------------------------------------
    # 功能：对子弹进行显示 并检测子弹与子弹 子弹与坦克 子弹和地图碰撞等的操作
    def bullet_section(self):
        # 绘制我方子弹1
        if self.myTank_T1.bullet.life:
            self.myTank_T1.bullet.move()
            self.screen.blit(self.myTank_T1.bullet.bullet, self.myTank_T1.bullet.rect)
            # 子弹 碰撞 子弹
            for each in self.enemyBulletGroup:
                if each.life:
                    if pygame.sprite.collide_rect(self.myTank_T1.bullet, each):
                        self.myTank_T1.bullet.life = False
                        each.life = False
                        pygame.sprite.spritecollide(self.myTank_T1.bullet, self.enemyBulletGroup, True, None)
            # 子弹 碰撞 敌方坦克
            if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.redEnemyGroup, True, None):
                self.prop.change()
                if self.isSoundEffect:
                    self.prop_sound.play()
                self.enemyNumber -= 1
                if not self.isEndless:
                    self.remaining_enemy -= 1
                self.myTank_T1.bullet.life = False
                mid = special_effects.bulletBoom(self.myTank_T1.bullet.rect.left - 12,
                                                 self.myTank_T1.bullet.rect.top - 12)
                self.bulletBoomGroup.append(mid)
            elif pygame.sprite.spritecollide(self.myTank_T1.bullet, self.greenEnemyGroup, False, None):
                for each in self.greenEnemyGroup:
                    if pygame.sprite.collide_rect(self.myTank_T1.bullet, each):
                        if each.life == 1:
                            pygame.sprite.spritecollide(self.myTank_T1.bullet, self.greenEnemyGroup, True, None)
                            if self.isSoundEffect:
                                self.bang_sound.play()
                            self.enemyNumber -= 1
                            if not self.isEndless:
                                self.remaining_enemy -= 1
                        elif each.life == 2:
                            if self.isSoundEffect:
                                self.wall_sound.play()
                            each.life -= 1
                            each.tank = each.enemy_3_0
                        elif each.life == 3:
                            if self.isSoundEffect:
                                self.wall_sound.play()
                            each.life -= 1
                            each.tank = each.enemy_3_2
                self.myTank_T1.bullet.life = False
                mid = special_effects.bulletBoom(self.myTank_T1.bullet.rect.left - 12,
                                                 self.myTank_T1.bullet.rect.top - 12)
                self.bulletBoomGroup.append(mid)
            elif pygame.sprite.spritecollide(self.myTank_T1.bullet, self.otherEnemyGroup, True, None):
                if self.isSoundEffect:
                    self.bang_sound.play()
                self.enemyNumber -= 1
                if not self.isEndless:
                    self.remaining_enemy -= 1
                self.myTank_T1.bullet.life = False
                mid = special_effects.bulletBoom(self.myTank_T1.bullet.rect.left - 12,
                                                 self.myTank_T1.bullet.rect.top - 12)
                self.bulletBoomGroup.append(mid)
            else:
                # 兜底：若敌人未正确加入分类分组，但仍在allEnemyGroup中
                collided = pygame.sprite.spritecollide(self.myTank_T1.bullet, self.allEnemyGroup, False, None)
                if collided:
                    for enemy in collided:
                        if self.isSoundEffect:
                            self.bang_sound.play()
                        enemy.kill()  # 移出所有分组，避免“幽灵敌人”
                        self.enemyNumber -= 1
                        if not self.isEndless:
                            self.remaining_enemy -= 1
                    self.myTank_T1.bullet.life = False
                    mid = special_effects.bulletBoom(self.myTank_T1.bullet.rect.left - 12,
                                                     self.myTank_T1.bullet.rect.top - 12)
                    self.bulletBoomGroup.append(mid)

            # 子弹 碰撞 brickGroup
            if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.brickGroup, True, None):
                if self.isSoundEffect:
                    self.wall_sound.play()
                self.myTank_T1.bullet.life = False
                self.myTank_T1.bullet.rect.left, self.myTank_T1.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            # 子弹 碰撞 ironGroup
            if self.myTank_T1.bullet.strong:
                if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.ironGroup, True, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T1.bullet.life = False
                    self.myTank_T1.bullet.rect.left, self.myTank_T1.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            else:
                if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.ironGroup, False, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T1.bullet.life = False
                    self.myTank_T1.bullet.rect.left, self.myTank_T1.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            # 子弹 碰撞 家
            if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.homeGroup, True, None):
                self.overGameLoss = True

        # 绘制我方子弹2 （模仿坦克1写）
        if self.myTank_T2.bullet.life:
            self.myTank_T2.bullet.move()
            self.screen.blit(self.myTank_T2.bullet.bullet, self.myTank_T2.bullet.rect)
            # 子弹 碰撞 敌方坦克
            if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.redEnemyGroup, True, None):
                self.prop.change()
                if self.isSoundEffect:
                    self.prop_sound.play()
                self.enemyNumber -= 1
                if not self.isEndless:
                    self.remaining_enemy -= 1
                self.myTank_T2.bullet.life = False
                mid = special_effects.bulletBoom(self.myTank_T2.bullet.rect.left - 12,
                                                 self.myTank_T2.bullet.rect.top - 12)
                self.bulletBoomGroup.append(mid)
            elif pygame.sprite.spritecollide(self.myTank_T2.bullet, self.greenEnemyGroup, False, None):
                for each in self.greenEnemyGroup:
                    if pygame.sprite.collide_rect(self.myTank_T2.bullet, each):
                        if each.life == 1:
                            pygame.sprite.spritecollide(self.myTank_T2.bullet, self.greenEnemyGroup, True, None)
                            if self.isSoundEffect:
                                self.bang_sound.play()
                            self.enemyNumber -= 1
                            if not self.isEndless:
                                self.remaining_enemy -= 1
                        elif each.life == 2:
                            if self.isSoundEffect:
                                self.wall_sound.play()
                            each.life -= 1
                            each.tank = each.enemy_3_0
                        elif each.life == 3:
                            if self.isSoundEffect:
                                self.wall_sound.play()
                            each.life -= 1
                            each.tank = each.enemy_3_2
                self.myTank_T2.bullet.life = False
                mid = special_effects.bulletBoom(self.myTank_T2.bullet.rect.left - 12,
                                                 self.myTank_T2.bullet.rect.top - 12)
                self.bulletBoomGroup.append(mid)
            elif pygame.sprite.spritecollide(self.myTank_T2.bullet, self.otherEnemyGroup, True, None):
                if self.isSoundEffect:
                    self.bang_sound.play()
                self.enemyNumber -= 1
                if not self.isEndless:
                    self.remaining_enemy -= 1
                self.myTank_T2.bullet.life = False
                mid = special_effects.bulletBoom(self.myTank_T2.bullet.rect.left - 12,
                                                 self.myTank_T2.bullet.rect.top - 12)
                self.bulletBoomGroup.append(mid)
            else:
                collided = pygame.sprite.spritecollide(self.myTank_T2.bullet, self.allEnemyGroup, False, None)
                if collided:
                    for enemy in collided:
                        if self.isSoundEffect:
                            self.bang_sound.play()
                        enemy.kill()
                        self.enemyNumber -= 1
                        if not self.isEndless:
                            self.remaining_enemy -= 1
                    self.myTank_T2.bullet.life = False
                    mid = special_effects.bulletBoom(self.myTank_T2.bullet.rect.left - 12,
                                                     self.myTank_T2.bullet.rect.top - 12)
                    self.bulletBoomGroup.append(mid)

            # 子弹 碰撞 brickGroup
            if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.brickGroup, True, None):
                if self.isSoundEffect:
                    self.wall_sound.play()
                self.myTank_T2.bullet.life = False
                self.myTank_T2.bullet.rect.left, self.myTank_T2.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            # 子弹 碰撞 brickGroup
            if self.myTank_T2.bullet.strong:
                if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.ironGroup, True, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T2.bullet.life = False
                    self.myTank_T2.bullet.rect.left, self.myTank_T2.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            else:
                if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.ironGroup, False, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T2.bullet.life = False
                    self.myTank_T2.bullet.rect.left, self.myTank_T2.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
                # 子弹 碰撞 家
            if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.homeGroup, True, None):
                self.overGameLoss = True
        # 绘制敌人子弹
        for each in self.allEnemyGroup:
            # 如果子弹没有生命，则赋予子弹生命
            if not each.bullet.life and self.enemyCouldMove:
                self.enemyBulletGroup.remove(each.bullet)
                each.shoot()
                self.enemyBulletGroup.add(each.bullet)
            # 如果5毛钱特效播放完毕 并且 子弹存活 则绘制敌方子弹
            if each.flash:
                if each.bullet.life:
                    # 如果敌人可以移动
                    if self.enemyCouldMove:
                        each.bullet.move()
                    self.screen.blit(each.bullet.bullet, each.bullet.rect)

                    # 子弹 碰撞 我方坦克
                    # 敌方子弹碰撞到我方坦克1
                    if pygame.sprite.collide_rect(each.bullet, self.myTank_T1):
                        if self.invincible_T1 > 0:
                            if self.isSoundEffect:
                                self.bang_sound.play()
                            each.bullet.life = False
                        else:
                            if self.isSoundEffect:
                                self.bang_sound.play()
                            self.myTank_T1.rect.left, self.myTank_T1.rect.top = 3 + 8 * 24, 3 + 24 * 24
                            if not self.isEndless:
                                self.myTank_T1.life -= 1
                            each.bullet.life = False

                            self.moving = 0  # 重置移动控制参数
                            for i in range(self.myTank_T1.level + 1):
                                self.myTank_T1.levelDown()
                            self.invincible_T1 = 200

                    # 敌方子弹碰撞到我方坦克2
                    if pygame.sprite.collide_rect(each.bullet, self.myTank_T2):
                        if self.invincible_T2 > 0:
                            if self.isSoundEffect:
                                self.bang_sound.play()
                            each.bullet.life = False
                        else:
                            if self.isSoundEffect:
                                self.bang_sound.play()
                            self.myTank_T2.rect.left, self.myTank_T2.rect.top = 3 + 16 * 24, 3 + 24 * 24
                            each.bullet.life = False
                            if not self.isEndless:
                                self.myTank_T2.life -= 1
                            self.moving2 = 0  # 重置移动控制参数
                            for i in range(self.myTank_T2.level + 1):
                                self.myTank_T2.levelDown()
                            self.invincible_T2 = 200

                    # 子弹 碰撞 brickGroup
                    if pygame.sprite.spritecollide(each.bullet, self.bgMap.brickGroup, True, None):
                        each.bullet.life = False
                    # 子弹 碰撞 ironGroup
                    if each.bullet.strong:
                        if pygame.sprite.spritecollide(each.bullet, self.bgMap.ironGroup, True, None):
                            each.bullet.life = False
                    else:
                        if pygame.sprite.spritecollide(each.bullet, self.bgMap.ironGroup, False, None):
                            each.bullet.life = False
                            # 子弹 碰撞 家
                    if pygame.sprite.spritecollide(each.bullet, self.bgMap.homeGroup, True, None):
                        self.overGameLoss = True

    # 子弹显示函数(单挑版）--------------------------------------------------------
    # 功能：单挑模式的子弹显示
    def bullet_plate(self):
        # 绘制我方子弹1
        if self.myTank_T1.bullet.life:
            self.myTank_T1.bullet.move()
            self.screen.blit(self.myTank_T1.bullet.bullet, self.myTank_T1.bullet.rect)
            # 子弹 碰撞 子弹
            if self.myTank_T2.bullet.life:
                if pygame.sprite.collide_rect(self.myTank_T1.bullet, self.myTank_T2.bullet):
                    self.myTank_T1.bullet.life = False
                    self.myTank_T2.bullet.life = False

            # 子弹碰撞到我方坦克2
            if pygame.sprite.collide_rect(self.myTank_T1.bullet, self.myTank_T2):
                if self.invincible_T2 > 0:
                    if self.isSoundEffect:
                        self.bang_sound.play()
                    self.myTank_T1.bullet.life = False
                else:
                    if self.isSoundEffect:
                        self.bang_sound.play()
                    self.myTank_T2.rect.left, self.myTank_T2.rect.top = 3 + 12 * 24, 3 + 0 * 24
                    self.myTank_T1.bullet.life = False
                    self.myTank_T2.life -= 1
                    self.moving2 = 0  # 重置移动控制参数
                    for i in range(self.myTank_T2.level + 1):
                        self.myTank_T2.levelDown()
                    self.invincible_T2 = 200

            # 子弹 碰撞 brickGroup
            if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.brickGroup, True, None):
                if self.isSoundEffect:
                    self.wall_sound.play()
                self.myTank_T1.bullet.life = False
                self.myTank_T1.bullet.rect.left, self.myTank_T1.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            # 子弹 碰撞 ironGroup
            if self.myTank_T1.bullet.strong:
                if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.ironGroup, True, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T1.bullet.life = False
                    self.myTank_T1.bullet.rect.left, self.myTank_T1.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            else:
                if pygame.sprite.spritecollide(self.myTank_T1.bullet, self.bgMap.ironGroup, False, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T1.bullet.life = False
                    self.myTank_T1.bullet.rect.left, self.myTank_T1.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24

        # 绘制我方子弹2 （模仿坦克1写）
        if self.myTank_T2.bullet.life:
            self.myTank_T2.bullet.move()
            self.screen.blit(self.myTank_T2.bullet.bullet, self.myTank_T2.bullet.rect)
            # 子弹碰撞到我方坦克1
            if pygame.sprite.collide_rect(self.myTank_T2.bullet, self.myTank_T1):
                if self.invincible_T1 > 0:
                    if self.isSoundEffect:
                        self.bang_sound.play()
                    self.myTank_T2.bullet.life = False
                else:
                    if self.isSoundEffect:
                        self.bang_sound.play()
                    self.myTank_T1.rect.left, self.myTank_T1.rect.top = 3 + 12 * 24, 3 + 24 * 24
                    self.myTank_T1.life -= 1
                    self.myTank_T2.bullet.life = False

                    self.moving = 0  # 重置移动控制参数
                    for i in range(self.myTank_T1.level + 1):
                        self.myTank_T1.levelDown()
                    self.invincible_T1 = 200

            # 子弹 碰撞 brickGroup
            if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.brickGroup, True, None):
                if self.isSoundEffect:
                    self.wall_sound.play()
                self.myTank_T2.bullet.life = False
                self.myTank_T2.bullet.rect.left, self.myTank_T2.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            # 子弹 碰撞 brickGroup
            if self.myTank_T2.bullet.strong:
                if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.ironGroup, True, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T2.bullet.life = False
                    self.myTank_T2.bullet.rect.left, self.myTank_T2.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24
            else:
                if pygame.sprite.spritecollide(self.myTank_T2.bullet, self.bgMap.ironGroup, False, None):
                    if self.isSoundEffect:
                        self.wall_sound.play()
                    self.myTank_T2.bullet.life = False
                    self.myTank_T2.bullet.rect.left, self.myTank_T2.bullet.rect.right = 3 + 12 * 24, 3 + 24 * 24

    # 道具部分函数------------------------------------------------------------
    # 功能：对道具进行更新显示 并当我方碰到道具时会触发不同效果
    def props_section(self):
        # 最后画食物/道具
        if self.prop.life:
            self.screen.blit(self.prop.image, self.prop.rect)
            # 我方坦克碰撞 食物/道具

            # 如果是坦克1碰到道具
            if pygame.sprite.collide_rect(self.myTank_T1, self.prop):
                if self.isSoundEffect:
                    self.get_props_sound.play()
                if self.prop.kind == 1:  # 敌人全毁
                    if self.isSoundEffect:
                        self.prop_boom_sound.play()
                    for each in self.allEnemyGroup:
                        if pygame.sprite.spritecollide(each, self.allEnemyGroup, True, None):
                            self.enemyNumber -= 1
                            if not self.isEndless:
                                self.remaining_enemy -=1
                    self.prop.life = False
                if self.prop.kind == 2:  # 敌人静止
                    self.enemyCouldMove = False
                    self.prop.life = False
                if self.prop.kind == 3:  # 子弹增强
                    self.myTank_T1.bullet.strong = True
                    self.prop.life = False
                if self.prop.kind == 4:  # 家得到保护
                    for x, y in [(11, 23), (12, 23), (13, 23), (14, 23), (11, 24), (14, 24), (11, 25), (14, 25)]:
                        self.bgMap.iron = wall.Iron()
                        self.bgMap.iron.rect.left, self.bgMap.iron.rect.top = 3 + x * 24, 3 + y * 24
                        self.bgMap.ironGroup.add(self.bgMap.iron)
                    self.prop.life = False
                    self.iron_time = 200
                if self.prop.kind == 5:  # 坦克无敌
                    self.prop.life = False
                    self.invincible_T1 = 200
                if self.prop.kind == 6:  # 坦克升级
                    self.myTank_T1.levelUp()
                    self.prop.life = False
                if self.prop.kind == 7:  # 坦克生命+1
                    if self.myTank_T1.life < 3:
                        self.myTank_T1.life += 1
                    self.prop.life = False

            # 如果是坦克二碰到道具
            elif pygame.sprite.collide_rect(self.myTank_T2, self.prop):
                if self.isSoundEffect:
                    self.get_props_sound.play()
                if self.prop.kind == 1:  # 敌人全毁
                    self.prop_boom_sound.play()
                    for each in self.allEnemyGroup:
                        if pygame.sprite.spritecollide(each, self.allEnemyGroup, True, None):
                            self.enemyNumber -= 1
                            if not self.isEndless:
                                self.remaining_enemy -=1
                    self.prop.life = False
                if self.prop.kind == 2:  # 敌人静止
                    self.enemyCouldMove = False
                    self.prop.life = False
                if self.prop.kind == 3:  # 子弹增强
                    self.myTank_T2.bullet.strong = True
                    self.prop.life = False
                if self.prop.kind == 4:  # 家得到保护
                    for x, y in [(11, 23), (12, 23), (13, 23), (14, 23), (11, 24), (14, 24), (11, 25), (14, 25)]:
                        self.bgMap.iron = wall.Iron()
                        self.bgMap.iron.rect.left, self.bgMap.iron.rect.top = 3 + x * 24, 3 + y * 24
                        self.bgMap.ironGroup.add(self.bgMap.iron)
                    self.prop.life = False
                    self.iron_time = 200
                if self.prop.kind == 5:  # 坦克无敌
                    self.prop.life = False
                    self.invincible_T2 = 200
                if self.prop.kind == 6:  # 坦克升级
                    self.myTank_T2.levelUp()
                    self.prop.life = False
                if self.prop.kind == 7:  # 坦克生命+1
                    if self.myTank_T2.life < 3:
                        self.myTank_T2.life += 1
                    self.prop.life = False

    # 游戏运行函数（普通和无尽模式）----------------------------------------------------
    # 功能：运行此函数就将运行游戏
    # 接口：checkpoint就是选择关卡 1-35分别是对应关卡  99则是自建地图
    #      ai_mode: 是否启用AI模式
    #      ai_model_path: 低层AI模型路径
    #      ai_option_model_path: 高层选项模型路径
    def game_running(self,checkpoint,isEndless, ai_mode=False, ai_model_path=None, ai_option_model_path=None):
        self.isEndless = isEndless
        self.ai_mode = ai_mode
        self.ai_model_path = ai_model_path
        self.ai_option_model_path = ai_option_model_path
        
        # 初始化AI代理
        if self.ai_mode:
            try:
                from ai_agent import TankAIAgent
                print(f"[AI INIT] 正在初始化AI代理，低层模型: {ai_model_path}, 高层选项模型: {ai_option_model_path}")
                self.ai_agent = TankAIAgent(model_path=ai_model_path, option_model_path=ai_option_model_path)
                if ai_model_path and self.ai_agent.agent is not None:
                    print(f"[AI INIT] ✓ 低层模型已加载: {ai_model_path}")
                elif ai_model_path:
                    print(f"[AI WARNING] 低层模型路径提供但模型未加载: {ai_model_path}")
                else:
                    print(f"[AI INIT] ✓ AI模式已启用，低层使用随机策略（无模型）")
                if ai_option_model_path and self.ai_agent.option_agent is not None:
                    print(f"[AI INIT] ✓ 高层选项模型已加载: {ai_option_model_path}")
            except Exception as e:
                print(f"[AI ERROR] AI初始化失败: {e}")
                import traceback
                traceback.print_exc()
                self.ai_mode = False
                self.ai_agent = None
        # 创建地图 但是不用只是当作一个中间变量
        map_num = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]

        # 如果checkpoint是自建关卡
        if checkpoint == 99:
            # 如果返回0则退出 如果返回数组则进行地图创建
            map_loader_me = map_loader.Map_loader()
            mid = map_loader_me.function(True)
            if mid == 0:
                return
            self.bgMap.checkpoint(checkpoint, mid)
        else:
            self.bgMap.checkpoint(checkpoint, map_num)

        # 创建敌方 坦克（在一二三处出现）
        for i in range(1, 4):
            enemy = enemyTank.EnemyTank(i)
            self.allTankGroup.add(enemy)
            self.allEnemyGroup.add(enemy)
            if enemy.isred == True:
                self.redEnemyGroup.add(enemy)
                continue
            if enemy.kind == 3:
                self.greenEnemyGroup.add(enemy)
                continue
            self.otherEnemyGroup.add(enemy)

        # AI模式下，玩家2由AI控制，需要启用
        if ai_mode:
            self.myTank_T2.life = 3  # AI控制的玩家2有生命
            print(f"[DEBUG] AI模式: 玩家2生命设置为 {self.myTank_T2.life}")
        else:
            # 默认是单人
            self.myTank_T2.life = 0
            print(f"[DEBUG] 单人模式: 玩家2生命设置为 {self.myTank_T2.life}")
        
        print(f"[DEBUG] 游戏初始化完成 - 玩家1生命: {self.myTank_T1.life}, 位置: ({self.myTank_T1.rect.left}, {self.myTank_T1.rect.top})")
        print(f"[DEBUG] 控制说明: WASD移动, J射击")
        
        # 清除所有按键状态，避免菜单界面的按键状态影响游戏
        # 先清除事件队列
        pygame.event.clear()
        # 等待一小段时间，确保所有按键状态被清除
        pygame.time.wait(150)
        
        # 强制清除所有按键状态（通过模拟按键释放事件）
        # 清除WASD键
        for key_code in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key_code))
        # 清除方向键
        for key_code in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key_code))
        
        # 处理这些释放事件
        pygame.event.pump()
        # 再次清除事件队列
        pygame.event.clear()
        
        # 清除按键重复设置并重新设置
        pygame.key.set_repeat()  # 清除按键重复设置
        pygame.key.set_repeat(200, 50)  # 重新设置按键重复（200ms延迟，50ms间隔）
        
        # 重置移动状态
        self.moving = 0
        self.movdir = 0
        
        self.start_sound.play()
        # 确保窗口有焦点
        pygame.event.post(pygame.event.Event(pygame.ACTIVEEVENT, gain=1, state=1))
        # 再次清除事件队列，确保干净的状态
        pygame.event.clear()
        
        while True:
            #游戏结束
            if self.remaining_enemy == 0:
                self.overGameWin = True

            if self.overGameLoss:
                mid = self.game_over(2)
                if mid == 0:
                    self.start_sound.stop()
                    return

            if self.overGameWin:
                mid = self.game_over(1)
                if mid == 0:
                    self.start_sound.stop()
                    return
            
            # 确保窗口有焦点（每帧检查）
            window_active = pygame.display.get_active()
            if not window_active:
                # 尝试重新激活窗口
                pygame.event.post(pygame.event.Event(pygame.ACTIVEEVENT, gain=1, state=1))
                if not hasattr(self, '_focus_warning_count'):
                    self._focus_warning_count = 0
                self._focus_warning_count += 1
                if self._focus_warning_count % 60 == 0:  # 每秒警告一次
                    print(f"[DEBUG] ⚠ 警告: 游戏窗口没有焦点！请点击游戏窗口 (警告次数: {self._focus_warning_count})")
            
            # 按键操作
            key_pressed = pygame.key.get_pressed()
            
            # 调试：检查是否有任何按键被按下
            any_key = False
            pressed_keys = []
            for key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_j, pygame.K_ESCAPE]:
                if key_pressed[key]:
                    any_key = True
                    key_name = pygame.key.name(key)
                    pressed_keys.append(key_name)
            
            if not hasattr(self, '_key_check_count'):
                self._key_check_count = 0
            self._key_check_count += 1
            if self._key_check_count % 60 == 0:  # 每秒检查一次
                print(f"[DEBUG] 键盘检测测试 - 窗口焦点: {window_active}, 是否有按键: {any_key}, 按键列表: {pressed_keys}, pygame初始化: {pygame.get_init()}")

            # 按esc退出游戏
            if key_pressed[pygame.K_ESCAPE]:
                print("[DEBUG] 检测到ESC键，退出游戏")
                self.start_sound.stop()
                return

            # 按F1复活玩家1
            if key_pressed[pygame.K_F1] and self.myTank_T1.life == 0:
                self.myTank_T1.life = 3
                self.myTank_T1.rect.left, self.myTank_T1.rect.top = 3 + 8 * 24, 3 + 24 * 24
                if self.isSoundEffect:
                    self.add_sound.play()
            # 按F2复活玩家2
            if key_pressed[pygame.K_F2] and self.myTank_T2.life == 0:
                self.myTank_T2.life = 3
                self.myTank_T2.rect.left, self.myTank_T2.rect.top = 3 + 16 * 24, 3 + 24 * 24
                if self.isSoundEffect:
                    self.add_sound.play()
            # 如果玩家死亡（只在非AI模式下隐藏，AI模式下保持可见）
            if self.myTank_T1.life == 0:
                if not self.ai_mode:
                    self.myTank_T1.rect.left, self.myTank_T1.rect.top = 630, 0
            if self.myTank_T2.life == 0:
                if not self.ai_mode:
                    self.myTank_T2.rect.left, self.myTank_T2.rect.top = 680, 0
            # --------------------------------------------------------------------------
            # 处理事件部分 主要就是各个事件的时间
            # ---------------------------------------------------------------------------
            # 处理所有事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # 处理自定义事件
                if event.type == self.MYBULLETNOTCOOLINGEVENT:
                    self.myTank_T1.bulletNotCooling = True
                    if self.ai_mode and self.myTank_T2.life > 0:
                        self.myTank_T2.bulletNotCooling = True
                if event.type == self.ENEMYBULLETNOTCOOLINGEVENT:
                    for each in self.allEnemyGroup:
                        each.bulletNotCooling = True
                if event.type == self.NOTMOVEEVENT:
                    self.enemyCouldMove = True
                if event.type == self.DELAYEVENT:
                    if self.enemyNumber < 4 and self.remaining_enemy-self.enemyNumber >=1:
                        enemy = enemyTank.EnemyTank()
                        if pygame.sprite.spritecollide(enemy, self.allTankGroup, False, None):
                            break
                        self.allEnemyGroup.add(enemy)
                        self.allTankGroup.add(enemy)
                        self.enemyNumber += 1
                        if enemy.isred == True:
                            self.redEnemyGroup.add(enemy)
                        elif enemy.kind == 3:
                            self.greenEnemyGroup.add(enemy)
                        else:
                            self.otherEnemyGroup.add(enemy)
                if event.type == pygame.KEYDOWN:
                    key_name = pygame.key.name(event.key)
                    key_code = event.key
                    print(f"[DEBUG] KEYDOWN事件: {key_name} (code: {key_code})")
                    
                    # 处理玩家1的移动（事件驱动，作为get_pressed()的备用方案）
                    # 允许在移动过程中改变方向
                    if self.myTank_T1.life > 0:
                        move_dir = None
                        key_name = ""
                        if event.key == pygame.K_w or event.key == pygame.K_UP:
                            key_name = "W/↑"
                            move_dir = 0
                        elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                            key_name = "S/↓"
                            move_dir = 1
                        elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                            key_name = "A/←"
                            move_dir = 2
                        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                            key_name = "D/→"
                            move_dir = 3
                        
                        # 如果有新的移动输入，且（没有在移动 或 方向改变了）
                        if move_dir is not None and (not self.moving or self.movdir != move_dir):
                            print(f"[DEBUG] 事件: {key_name}键按下，开始移动，方向: {move_dir}")
                            self.moving = 7
                            self.movdir = move_dir
                            self.running_T1 = True
                            self.allTankGroup.remove(self.myTank_T1)
                            collision = False
                            if move_dir == 0:
                                collision = self.myTank_T1.moveUp(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup, self.bgMap.riverGroup)
                            elif move_dir == 1:
                                collision = self.myTank_T1.moveDown(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup, self.bgMap.riverGroup)
                            elif move_dir == 2:
                                collision = self.myTank_T1.moveLeft(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup, self.bgMap.riverGroup)
                            elif move_dir == 3:
                                collision = self.myTank_T1.moveRight(self.allTankGroup, self.bgMap.brickGroup, self.bgMap.ironGroup, self.bgMap.riverGroup)
                            if collision:
                                print(f"[DEBUG] 事件: {key_name}键移动遇到碰撞")
                                self.moving = 0
                            self.allTankGroup.add(self.myTank_T1)
                    
                    # 处理特殊按键
                    if event.key == pygame.K_F3:
                        self.isSoundEffect = not self.isSoundEffect
                        self.start_sound.stop()
                    # 射击键
                    elif (event.key == pygame.K_j or event.key == pygame.K_SPACE) and self.myTank_T1.life > 0:
                        if not self.myTank_T1.bullet.life and self.myTank_T1.bulletNotCooling:
                            if self.isSoundEffect:
                                self.attack_sound.play()
                            self.myTank_T1.shoot()
                            self.myTank_T1.bulletNotCooling = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.game_pause()

            # 检查用户的键盘操作
            # ----------------------------------------------------------------------------
            # 移动操作 -------------------------------------------------------------------
            # 调试：检查游戏状态
            if not hasattr(self, '_debug_frame_count'):
                self._debug_frame_count = 0
            self._debug_frame_count += 1
            if self._debug_frame_count % 60 == 0:  # 每秒打印一次
                print(f"[DEBUG] 游戏运行中 - AI模式: {self.ai_mode}, 玩家1生命: {self.myTank_T1.life}, 位置: ({self.myTank_T1.rect.left}, {self.myTank_T1.rect.top}), moving: {self.moving}")
            
            # 在AI模式下，玩家1的操作检测应该正常工作
            self.operation_detection_section()
            # AI控制（如果启用）
            if self.ai_mode:
                self.ai_control_section()
            # --------------------------------------------------------------------------
            # 画图像操作 ----------------------------------------------------------------
            # -------------------------------------------------------------------------
            while self.iron_time > 0:
                self.iron_time -= 1
                if self.iron_time == 1:
                    for x, y in [(11, 23), (12, 23), (13, 23), (14, 23), (11, 24), (14, 24), (11, 25), (14, 25)]:
                        self.bgMap.brick = wall.Brick()
                        self.bgMap.brick.rect.left, self.bgMap.brick.rect.top = 3 + x * 24, 3 + y * 24
                        self.bgMap.brickGroup.add(self.bgMap.brick)

            # 画背景
            self.screen.blit(self.background_image, (0, 0))
            if self.isEndless:
                self.screen.blit(self.background_image_endless_mode, (630, 0))
            else:
                self.screen.blit(self.background_image_level_mode, (630, 0))
            
            # AI模式下显示提示信息
            if self.ai_mode:
                font = pygame.font.Font(None, 24)
                ai_info = [
                    "AI Assist Mode",
                    "Player 1: WASD + J",
                    "Player 2: AI Control"
                ]
                for i, text in enumerate(ai_info):
                    ai_text = font.render(text, True, (0, 255, 0))
                    self.screen.blit(ai_text, (640, 400 + i * 25))
            # 画砖块
            for each in self.bgMap.brickGroup:
                self.screen.blit(each.image, each.rect)
            # 画石头
            for each in self.bgMap.ironGroup:
                self.screen.blit(each.image, each.rect)
            # 画河流
            for each in self.bgMap.riverGroup:
                self.screen.blit(each.image, each.rect)
            # 画冰川
            for each in self.bgMap.iceGroup:
                self.screen.blit(each.image, each.rect)
            # 画home
            for each in self.bgMap.homeGroup:
                self.screen.blit(each.image, each.rect)

            if not self.isEndless:
                # 画敌军图标
                for i in range(0,self.remaining_enemy):
                    if i in range(0,10):
                        x = 630 + 25
                        y = 80 + i*30
                        self.screen.blit(self.enemy_icon,(x,y))
                    else:
                        x = 630 + 65
                        y = 80 + (i-10)*30
                        self.screen.blit(self.enemy_icon, (x, y))

                # 画1P生命
                for i in range(0,self.myTank_T1.life):
                    x = 680 + i*20
                    self.screen.blit(self.heart_icon, (x, 378+5))

                # 画2P生命
                for i in range(0, self.myTank_T2.life):
                    x = 680 + i * 20
                    self.screen.blit(self.heart_icon, (x, 378+55))
            # --------------------------------------------------------------
            # 画坦克---------------------------------------------------------
            # --------------------------------------------------------------
            self.tank_display_section()
            # ................................................................................
            # 子弹区域..........................................................................
            # .................................................................................
            self.bullet_section()
            # 画树 因为树在表层所有在后面画
            for each in self.bgMap.treeGroup:
                self.screen.blit(each.image, each.rect)

            # 画爆炸特效
            for each in self.bulletBoomGroup:
                if each.times > 0:
                    each.times -= 1
                    if each.times % 10 == 0:
                        self.special_effect.SE_boom(self.screen,each.x,each.y,each.times)
                else:
                    self.bulletBoomGroup.remove(each)
            # ----------------------------------------------------------------
            # 画道具-----------------------------------------------------------
            # ----------------------------------------------------------------
            self.props_section()

            # 延迟
            self.delay -= 1
            if not self.delay:
                self.delay = 100
            pygame.display.flip()
            self.clock.tick(60)

    # 游戏运行函数 （单挑模式）----------------------------------------------------------
    # 功能：运行测函数就是运行单挑模式的功能
    # 接口：checkpoint就是选择关卡
    def game_running_singled_out(self,checkpoint):
        # 创建地图
        map_num = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]

        # 如果checkpoint是自建关卡
        if checkpoint == 88:
            map_loader_me = map_loader.Map_loader()
            mid = map_loader_me.function(False)
            if mid == 0:
                return
            self.bgMap.checkpoint(checkpoint, mid)
        else:
            self.bgMap.checkpoint(checkpoint, map_num)

        self.myTank_T1.rect.left , self.myTank_T1.rect.top = 3 + 12 * 24, 3 + 24 * 24
        self.myTank_T2.rect.left , self.myTank_T2.rect.top = 3 + 12 * 24, 3 + 0 * 24
        self.start_sound.play()
        while True:

            if self.myTank_T1.life == 0:
                mid = self.game_over(4)
                if mid == 0:
                    return

            if self.myTank_T2.life == 0:
                mid = self.game_over(3)
                if mid == 0:
                    return
            # 按键操作
            key_pressed = pygame.key.get_pressed()
            # 按esc退出游戏
            if key_pressed[pygame.K_ESCAPE]:
                self.start_sound.stop()
                return

            self.event_section_singled_out()

            # 检查用户的键盘操作
            # ----------------------------------------------------------------------------
            # 移动操作 -------------------------------------------------------------------
            self.operation_detection_section()
            # --------------------------------------------------------------------------
            # 画图像操作 ----------------------------------------------------------------
            # -------------------------------------------------------------------------

            # 画背景
            self.screen.blit(self.background_image, (0, 0))
            self.screen.blit(self.background_image_heads_up_mode, (630, 0))

            # 画砖块
            for each in self.bgMap.brickGroup:
                self.screen.blit(each.image, each.rect)
            # 画石头
            for each in self.bgMap.ironGroup:
                self.screen.blit(each.image, each.rect)
            # 画河流
            for each in self.bgMap.riverGroup:
                self.screen.blit(each.image, each.rect)

            # 画冰川
            for each in self.bgMap.iceGroup:
                self.screen.blit(each.image, each.rect)
            for i in range(0, self.myTank_T1.life):
                x = 680 + i * 20
                self.screen.blit(self.heart_icon, (x, 290 + 5))

            # 画2P生命
            for i in range(0, self.myTank_T2.life):
                x = 680 + i * 20
                self.screen.blit(self.heart_icon, (x, 290 + 55))
            # --------------------------------------------------------------
            # 画坦克---------------------------------------------------------
            # --------------------------------------------------------------
            self.tank_display_section()
            # ................................................................................
            # 子弹区域..........................................................................
            # .................................................................................
            self.bullet_plate()

            # 画树
            for each in self.bgMap.treeGroup:
                self.screen.blit(each.image, each.rect)
            # 画爆炸特效
            for each in self.bulletBoomGroup:
                if each.times > 0:
                    each.times -= 1
                    if each.times % 10 == 0:
                        self.special_effect.SE_boom(self.screen, each.x, each.y, each.times)
                else:
                    self.bulletBoomGroup.remove(each)

            # 延迟
            self.delay -= 1
            if not self.delay:
                self.delay = 100
            pygame.display.flip()

            self.clock.tick(60)
