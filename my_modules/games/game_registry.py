# 游戏注册表，用于管理和加载游戏

import os
import importlib

class GameRegistry:
    """
    游戏注册表，负责发现、注册和创建游戏实例
    """
    def __init__(self):
        self.games = {}
    
    def initialize(self):
        """
        自动发现并注册所有游戏
        """
        # 获取games目录的绝对路径
        games_dir = os.path.dirname(__file__)
        # 遍历games目录下的所有文件夹
        for game_folder in os.listdir(games_dir):
            game_path = os.path.join(games_dir, game_folder)
            # 检查是否是目录且不是__pycache__
            if os.path.isdir(game_path) and game_folder != '__pycache__':
                try:
                    # 尝试导入游戏模块
                    game_module_name = f'my_modules.games.{game_folder}.game'

                    game_module = importlib.import_module(game_module_name)

                    # 检查游戏模块是否有register_game函数
                    if hasattr(game_module, 'register_game'):
                        # 调用注册函数获取游戏信息
                        game_info = game_module.register_game()
                        self.games[game_info['id']] = game_info
                        print(f'成功注册游戏: {game_info["name"]}')
                        print(self.games)
                except ImportError as e:
                    print(f'导入游戏模块 {game_folder} 失败: {e}')
                except Exception as e:
                    print(f'注册游戏 {game_folder} 时出错: {e}')
    
    def register_game(self, game_info):
        """
        手动注册游戏
        
        Args:
            game_info: 游戏信息字典
        """
        self.games[game_info['id']] = game_info
    
    def get_available_games(self):
        """
        获取所有可用游戏
        
        Returns:
            list: 游戏信息列表
        """
        return list(self.games.values())
    
    def get_game_info(self, game_id):
        """
        获取指定游戏的信息
        
        Args:
            game_id: 游戏ID
        
        Returns:
            dict: 游戏信息，如果不存在返回None
        """
        return self.games.get(game_id)
    
    def create_game(self, game_id, room_id):
        """
        创建游戏实例
        
        Args:
            game_id: 游戏ID
            room_id: 房间ID
        
        Returns:
            BaseGame: 游戏实例，如果游戏不存在返回None
        """
        print(self.games)
        if game_id in self.games:
            game_info = self.games[game_id]
            game_class = game_info['class']
            instance = game_class(room_id)
            instance.url = game_info['url']
            return instance
        print(f'游戏 {game_id} 不存在')
        return None

# 创建全局游戏注册表实例
game_registry = GameRegistry()