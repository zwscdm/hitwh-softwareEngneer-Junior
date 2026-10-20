"""
快速测试AI功能
用于验证AI模块是否可以正常导入和运行
"""

def test_imports():
    """测试所有模块是否可以正常导入"""
    print("测试模块导入...")
    try:
        from ai_state_extractor import StateExtractor
        print("✓ StateExtractor 导入成功")
        
        from ai_model import DQNAgent, DQNNetwork
        print("✓ AI模型 导入成功")
        
        from ai_agent import TankAIAgent
        print("✓ AI代理 导入成功")
        
        from ai_training_env import TrainingEnvironment
        print("✓ 训练环境 导入成功")
        
        print("\n所有模块导入成功！")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_creation():
    """测试模型创建"""
    print("\n测试模型创建...")
    try:
        from ai_model import DQNAgent
        import torch
        
        agent = DQNAgent(
            visual_input_size=(84, 84),
            visual_channels=1,
            feature_vector_dim=85,
            action_dim=9,
            device='cpu'  # 使用CPU测试
        )
        print("✓ DQN模型创建成功")
        
        # 测试前向传播
        import numpy as np
        visual_state = np.random.rand(1, 84, 84, 1).astype(np.float32)
        feature_vector = np.random.rand(120).astype(np.float32)
        
        action = agent.select_action(visual_state, feature_vector, training=True)
        print(f"✓ 模型推理成功，选择动作: {action}")
        
        return True
    except Exception as e:
        print(f"✗ 模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_state_extractor():
    """测试状态提取器"""
    print("\n测试状态提取器...")
    try:
        import pygame
        import numpy as np
        from ai_state_extractor import StateExtractor
        
        pygame.init()
        screen = pygame.Surface((630, 630))
        screen.fill((0, 0, 0))
        
        extractor = StateExtractor()
        
        # 测试视觉状态提取
        visual_state = extractor.extract_visual_state(screen)
        print(f"✓ 视觉状态提取成功，形状: {visual_state.shape}")
        
        # 测试特征向量提取
        game_state = {
            'myTank_T1': None,
            'myTank_T2': None,
            'allEnemyGroup': None,
            'prop': None,
            'remaining_enemy': 10,
            'enemyNumber': 2,
            'enemyCouldMove': True,
            'invincible_T2': 0,
        }
        feature_vector = extractor.extract_feature_vector(game_state)
        print(f"✓ 特征向量提取成功，形状: {feature_vector.shape}")
        
        pygame.quit()
        return True
    except Exception as e:
        print(f"✗ 状态提取器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("AI模块测试")
    print("=" * 50)
    
    results = []
    results.append(("模块导入", test_imports()))
    results.append(("状态提取器", test_state_extractor()))
    results.append(("模型创建", test_model_creation()))
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有测试通过！AI模块已准备就绪。")
        print("\n下一步:")
        print("1. 运行训练: python ai_train.py --checkpoint 1 --episodes 1000")
        print("2. 训练完成后，在游戏主菜单中选择 'AI Assist Level' 或 'AI Assist Endless'")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
