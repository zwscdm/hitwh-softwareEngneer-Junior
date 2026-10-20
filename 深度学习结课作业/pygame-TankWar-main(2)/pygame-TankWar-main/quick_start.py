"""
快速开始指南
演示如何使用AI功能
"""

import os
import sys

def print_usage():
    """打印使用说明"""
    print("=" * 60)
    print("AI for Game - 快速开始指南")
    print("=" * 60)
    print("\n1. 安装依赖:")
    print("   pip install -r requirements.txt")
    print("\n2. 测试AI模块:")
    print("   python test_ai.py")
    print("\n3. 训练AI模型:")
    print("   python ai_train.py --checkpoint 1 --episodes 1000 --save_dir models")
    print("   参数说明:")
    print("   --checkpoint: 关卡编号 (1-35)")
    print("   --endless: 使用无尽模式 (可选)")
    print("   --episodes: 训练轮数 (建议1000+)")
    print("   --save_dir: 模型保存目录 (默认: models)")
    print("\n4. 运行游戏并使用AI:")
    print("   python main.py")
    print("   然后在主菜单中选择:")
    print("   - 'AI Assist Level': AI辅助关卡模式")
    print("   - 'AI Assist Endless': AI辅助无尽模式")
    print("\n5. 游戏控制:")
    print("   玩家1 (键盘): WASD移动, J射击")
    print("   玩家2 (AI): 自动控制")
    print("\n" + "=" * 60)

def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    missing = []
    
    try:
        import pygame
        print("✓ pygame")
    except ImportError:
        missing.append("pygame")
        print("✗ pygame")
    
    try:
        import torch
        print(f"✓ torch ({torch.__version__})")
    except ImportError:
        missing.append("torch")
        print("✗ torch")
    
    try:
        import numpy
        print(f"✓ numpy ({numpy.__version__})")
    except ImportError:
        missing.append("numpy")
        print("✗ numpy")
    
    try:
        import cv2
        print(f"✓ opencv-python")
    except ImportError:
        missing.append("opencv-python")
        print("✗ opencv-python")
    
    if missing:
        print(f"\n缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ 所有依赖已安装")
        return True

def check_models():
    """检查是否有训练好的模型"""
    model_dir = "models"
    if not os.path.exists(model_dir):
        print(f"\n模型目录不存在: {model_dir}")
        print("请先训练模型: python ai_train.py --checkpoint 1 --episodes 1000")
        return False
    
    models = [f for f in os.listdir(model_dir) if f.endswith('.pth')]
    if not models:
        print(f"\n模型目录为空: {model_dir}")
        print("请先训练模型: python ai_train.py --checkpoint 1 --episodes 1000")
        return False
    
    print(f"\n找到 {len(models)} 个模型文件:")
    for model in models[:5]:  # 只显示前5个
        print(f"  - {model}")
    if len(models) > 5:
        print(f"  ... 还有 {len(models) - 5} 个模型")
    
    return True

if __name__ == '__main__':
    print_usage()
    
    print("\n" + "-" * 60)
    print("环境检查")
    print("-" * 60)
    
    deps_ok = check_dependencies()
    models_ok = check_models()
    
    print("\n" + "-" * 60)
    if deps_ok and models_ok:
        print("✓ 环境检查通过，可以开始使用AI功能！")
    elif deps_ok:
        print("⚠️  依赖已安装，但需要先训练模型")
    else:
        print("✗ 请先安装依赖")
