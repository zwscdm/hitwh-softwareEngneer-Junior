import numpy as np
import heapq
from collections import deque


class State:
    def __init__(self, state, parent=None, g=0, h=0):
        self.state = state
        self.parent = parent
        self.g = g  # 从起点到当前节点的实际代价
        self.h = h  # 从当前节点到目标节点的启发式估计
        self.f = g + h  # 总评估值 f = g + h
        
    def __lt__(self, other):
        """用于优先队列排序"""
        return self.f < other.f
    
    def __eq__(self, other):
        """用于状态比较"""
        return np.array_equal(self.state, other.state)
    
    def __hash__(self):
        """用于集合操作"""
        return hash(str(self.state))
    
    def getZeroPos(self):
        """获取空格位置"""
        position = np.where(self.state == 0)
        return position[0][0], position[1][0]
    
    def showInfo(self):
        """打印状态"""
        for i in range(len(self.state)):
            for j in range(len(self.state)):
                print(self.state[i, j], end='  ')
            print()
        print('->')
    
    def getManhattanDistance(self, target_state):
        """计算曼哈顿距离启发式函数"""
        distance = 0
        for i in range(len(self.state)):
            for j in range(len(self.state)):
                if self.state[i, j] != 0:  # 空格不计算距离
                    # 找到该数字在目标状态中的位置
                    target_pos = np.where(target_state == self.state[i, j])
                    target_i, target_j = target_pos[0][0], target_pos[1][0]
                    distance += abs(i - target_i) + abs(j - target_j)
        return distance
    
    def getEuclideanDistance(self, target_state):
        """计算欧几里得距离启发式函数"""
        distance = 0
        for i in range(len(self.state)):
            for j in range(len(self.state)):
                if self.state[i, j] != 0:
                    target_pos = np.where(target_state == self.state[i, j])
                    target_i, target_j = target_pos[0][0], target_pos[1][0]
                    distance += np.sqrt((i - target_i)**2 + (j - target_j)**2)
        return distance
    
    def getMisplacedTiles(self, target_state):
        """计算错位数字数量启发式函数"""
        misplaced = 0
        for i in range(len(self.state)):
            for j in range(len(self.state)):
                if self.state[i, j] != target_state[i, j]:
                    misplaced += 1
        return misplaced
    
    def generateChildren(self, target_state, heuristic_func='manhattan'):
        """生成所有可能的子节点"""
        children = []
        x, y = self.getZeroPos()
        
        # 四个方向的移动
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 上、下、左、右
        
        for dx, dy in moves:
            new_x, new_y = x + dx, y + dy
            
            # 检查边界
            if 0 <= new_x < len(self.state) and 0 <= new_y < len(self.state):
                # 创建新状态
                new_state = self.state.copy()
                new_state[x, y] = new_state[new_x, new_y]
                new_state[new_x, new_y] = 0
                
                # 计算启发式函数值
                if heuristic_func == 'manhattan':
                    h = self.getManhattanDistance(target_state)
                elif heuristic_func == 'euclidean':
                    h = self.getEuclideanDistance(target_state)
                elif heuristic_func == 'misplaced':
                    h = self.getMisplacedTiles(target_state)
                else:
                    h = self.getManhattanDistance(target_state)
                
                child = State(new_state, self, self.g + 1, h)
                children.append(child)
        
        return children
    
    def isGoal(self, target_state):
        """检查是否达到目标状态"""
        return np.array_equal(self.state, target_state)
    
    def reconstructPath(self):
        """重构从起点到终点的路径"""
        path = []
        current = self
        while current:
            path.append(current)
            current = current.parent
        path.reverse()
        return path


class AStarSolver:
    def __init__(self, initial_state, target_state, heuristic='manhattan'):
        self.initial_state = initial_state
        self.target_state = target_state
        self.heuristic = heuristic
        
    def solve(self):
        """A*算法求解"""
        # 初始化
        start = State(self.initial_state)
        start.h = start.getManhattanDistance(self.target_state) if self.heuristic == 'manhattan' else \
                 start.getEuclideanDistance(self.target_state) if self.heuristic == 'euclidean' else \
                 start.getMisplacedTiles(self.target_state)
        start.f = start.g + start.h
        
        open_list = [start]  # 优先队列
        closed_set = set()   # 已访问状态集合
        open_set = {str(start.state): start}  # 用于快速查找
        
        step_count = 0
        
        while open_list:
            step_count += 1
            
            # 按f值排序，取出f值最小的节点
            open_list.sort(key=lambda x: x.f)
            current = open_list.pop(0)
            
            # 从open_set中移除
            current_key = str(current.state)
            if current_key in open_set:
                del open_set[current_key]
            
            # 检查是否达到目标
            if current.isGoal(self.target_state):
                print(f"找到解决方案！总步数: {current.g}")
                print(f"搜索步数: {step_count}")
                return current.reconstructPath()
            
            # 将当前节点加入closed_set
            closed_set.add(str(current.state))
            
            # 生成子节点
            children = current.generateChildren(self.target_state, self.heuristic)
            
            for child in children:
                child_key = str(child.state)
                
                # 如果子节点在closed_set中，跳过
                if child_key in closed_set:
                    continue
                
                # 如果子节点在open_set中，检查是否需要更新
                if child_key in open_set:
                    existing_child = open_set[child_key]
                    if child.g < existing_child.g:
                        # 更新现有节点
                        existing_child.g = child.g
                        existing_child.f = existing_child.g + existing_child.h
                        existing_child.parent = child.parent
                else:
                    # 新节点，加入open_list
                    open_list.append(child)
                    open_set[child_key] = child
        
        print("无解！")
        return None


def printSolution(path, target_state):
    """打印解决方案"""
    if path:
        print(f"\n最优路径（共{len(path)-1}步）:")
        print("=" * 50)
        
        for i, state in enumerate(path):
            print(f"步骤 {i}:")
            state.showInfo()
            if i < len(path) - 1:
                print()
        
        print("目标状态:")
        for i in range(len(target_state)):
            for j in range(len(target_state)):
                print(target_state[i, j], end='  ')
            print()
        print(f"\n总步数: {len(path)-1}")
    else:
        print("无解！")


def testHeuristics(initial_state, target_state):
    """测试不同启发式函数"""
    heuristics = ['manhattan', 'euclidean', 'misplaced']
    heuristic_names = ['曼哈顿距离', '欧几里得距离', '错位数字数量']
    
    print("=" * 60)
    print("不同启发式函数对比测试")
    print("=" * 60)
    
    results = []
    
    for heuristic, name in zip(heuristics, heuristic_names):
        print(f"\n使用{name}启发式函数:")
        print("-" * 40)
        
        solver = AStarSolver(initial_state, target_state, heuristic)
        path = solver.solve()
        
        if path:
            results.append({
                'heuristic': name,
                'steps': len(path) - 1,
                'path': path
            })
            print(f"解决方案步数: {len(path) - 1}")
        else:
            results.append({
                'heuristic': name,
                'steps': -1,
                'path': None
            })
            print("无解")
    
    return results


if __name__ == '__main__':
    # 目标状态
    target_state = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 0]])
    
    # 初始状态1
    initial_state1 = np.array([[2, 8, 3], [1, 6, 4], [7, 0, 5]])
    
    # 初始状态2
    initial_state2 = np.array([[5, 1, 3], [2, 4, 6], [7, 0, 8]])
    
    print("A*算法求解8数码问题")
    print("=" * 60)
    
    # 测试初始状态1
    print("\n测试初始状态1:")
    print("初始状态:")
    for i in range(len(initial_state1)):
        for j in range(len(initial_state1)):
            print(initial_state1[i, j], end='  ')
        print()
    
    print("\n目标状态:")
    for i in range(len(target_state)):
        for j in range(len(target_state)):
            print(target_state[i, j], end='  ')
        print()
    
    # 使用曼哈顿距离求解
    print("\n使用曼哈顿距离启发式函数求解:")
    solver1 = AStarSolver(initial_state1, target_state, 'manhattan')
    path1 = solver1.solve()
    printSolution(path1, target_state)
    
    # 测试初始状态2
    print("\n" + "=" * 60)
    print("测试初始状态2:")
    print("初始状态:")
    for i in range(len(initial_state2)):
        for j in range(len(initial_state2)):
            print(initial_state2[i, j], end='  ')
        print()
    
    print("\n目标状态:")
    for i in range(len(target_state)):
        for j in range(len(target_state)):
            print(target_state[i, j], end='  ')
        print()
    
    # 使用曼哈顿距离求解
    print("\n使用曼哈顿距离启发式函数求解:")
    solver2 = AStarSolver(initial_state2, target_state, 'manhattan')
    path2 = solver2.solve()
    printSolution(path2, target_state)
    
    # 测试不同启发式函数
    print("\n" + "=" * 60)
    print("测试不同启发式函数（初始状态1）:")
    results = testHeuristics(initial_state1, target_state)
    
    # 对比分析
    print("\n" + "=" * 60)
    print("启发式函数对比分析:")
    print("=" * 60)
    
    for result in results:
        if result['steps'] != -1:
            print(f"{result['heuristic']}: {result['steps']}步")
        else:
            print(f"{result['heuristic']}: 无解")
