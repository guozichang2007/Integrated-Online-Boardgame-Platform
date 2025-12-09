# 房间管理器

from games.game_registry import game_registry

class Room:
    """
    房间类，管理单个房间的状态和玩家
    """
    def __init__(self, room_id, host_account):
        self.room_id = room_id
        self.host_account = host_account
        self.players = {}  # account -> player_info
        self.selected_game = None
        self.game_info = None
        self.game_instance = None
        self.game_started = False
    
    def add_player(self, account, player_info):
        """
        添加玩家到房间
        
        Args:
            account: 玩家账号
            player_info: 玩家信息字典
        """
        self.players[account] = player_info
    
    def remove_player(self, account):
        """
        从房间移除玩家
        
        Args:
            account: 玩家账号
        """
        if account in self.players:
            del self.players[account]
    
    def select_game(self, game_id):
        """
        选择房间要进行的游戏
        
        Args:
            game_id: 游戏ID
        
        Returns:
            bool: 是否成功选择游戏
        """
        # 只有房主可以选择游戏
        if not self.game_started:
            self.selected_game = game_id
            # 初始化游戏实例
            self.game_instance = game_registry.create_game(game_id, self.room_id)
            self.game_info = game_registry.get_game_info(game_id)

            # 将房间中的玩家添加到游戏中
            print(self.game_instance)
            print(f"roommanager:房间 {self.room_id} 选择游戏: {game_id},info:{self.game_info}")
            for account, info in self.players.items():
                if self.game_instance:
                    self.game_instance.join(account, info['ID'])
                    print(f"玩家 {account} 加入游戏 {game_id}")
            return True
        print(f"选择游戏失败: 房间 {self.room_id} ")
        return False
    
    def start_game(self):
        """
        开始游戏
        
        返回：
        - bool: 是否成功开始游戏
        
        功能：
        1. 验证游戏实例是否存在且游戏未开始
        2. 调用游戏实例的start方法启动游戏
        3. 更新房间状态为游戏已开始
        """
        if self.game_instance and not self.game_started:
            print(f"房间 {self.room_id} 开始游戏: {self.selected_game}")
            result = self.game_instance.start()
            if result:
                self.game_started = True  # 设置游戏已开始标志
                print(f"房间 {self.room_id} 游戏启动成功")
                return {'success': True, 'url': self.game_info['url']}
            else:
                print(f"房间 {self.room_id} 游戏启动失败")
                return {'success': False, 'url': self.game_info['url']}
        elif self.game_started:
            print(f"开始游戏失败: 房间 {self.room_id} 游戏已开始")
        else:
            print(f"开始游戏失败: 房间 {self.room_id} 游戏实例不存在")
        return False
    
    def is_host(self, account):
        """
        检查玩家是否是房主
        
        Args:
            account: 玩家账号
        
        Returns:
            bool: 是否是房主
        """
        return account == self.host_account
    
    def get_info(self):
        """
        获取房间信息
        
        Returns:
            dict: 房间信息
        """
        return {
            'room_id': self.room_id,
            'host_account': self.host_account,
            'players': self.players,
            'selected_game': self.selected_game,
            'game_started': self.game_started
        }

class RoomManager:
    """
    房间管理器，负责创建、管理和维护所有房间
    """
    def __init__(self):
        self.rooms = {}  # room_id -> Room实例
    
    def create_room(self, room_id, host_account, player_info):
        """
        创建新房间
        
        Args:
            room_id: 房间ID
            host_account: 房主账号
            player_info: 房主信息
        
        Returns:
            Room: 房间实例，如果房间已存在返回None
        """
        if room_id not in self.rooms:
            room = Room(room_id, host_account)
            room.add_player(host_account, player_info)
            self.rooms[room_id] = room
            return room
        return None
    
    def join_room(self, room_id, account, player_info):
        """
        加入房间
        
        参数：
        - room_id: 房间ID
        - account: 玩家账号
        - player_info: 玩家信息字典
        
        返回：
        - Room: 房间实例，如果加入成功
        - None: 如果房间不存在或游戏已开始
        
        功能流程：
        1. 检查房间是否存在
        2. 验证游戏是否已开始（游戏开始后不允许加入）
        3. 将玩家添加到房间
        4. 如果游戏已选择，将玩家加入到游戏实例中
        """
        if room_id in self.rooms:
            room = self.rooms[room_id]
            # 如果游戏已开始，不能加入
            if not room.game_started:
                room.add_player(account, player_info)
                # 如果游戏已选择，将玩家加入游戏实例
                if room.game_instance:
                    room.game_instance.join(account, player_info['ID'])
                print(f"玩家 {account} 加入房间 {room_id} 成功")
                return room
            else:
                print(f"加入房间失败: 房间 {room_id} 游戏已开始")
        else:
            print(f"加入房间失败: 房间 {room_id} 不存在")
        return None
    
    def leave_room(self, room_id, account):
        """
        离开房间
        
        Args:
            room_id: 房间ID
            account: 玩家账号
        """
        if room_id in self.rooms:
            room = self.rooms[room_id]
            room.remove_player(account)
            
            # 如果玩家在游戏中，也从游戏中移除
            if room.game_instance:
                room.game_instance.leave(account)
            
            # 如果房间为空，删除房间
            if not room.players:
                del self.rooms[room_id]
            elif account == room.host_account and room.players:
                # 重新选择房主
                room.host_account = next(iter(room.players.keys()))
    
    def get_room(self, room_id):
        """
        获取房间实例
        
        Args:
            room_id: 房间ID
        
        Returns:
            Room: 房间实例，如果不存在返回None
        """
        return self.rooms.get(room_id)
    
    def get_all_rooms(self):
        """
        获取所有房间
        
        Returns:
            list: 所有房间实例列表
        """
        return list(self.rooms)
    
    def select_game(self, room_id, game_id):
        """
        在房间中选择游戏
        
        Args:
            room_id: 房间ID
            game_id: 游戏ID
        
        Returns:
            bool: 是否成功选择游戏
        """
        room = self.get_room(room_id)
        if room:
            return room.select_game(game_id)
        return False
    
    def start_game(self, room_id):
        """
        在房间中开始游戏
        
        Args:
            room_id: 房间ID
        
        Returns:
            bool: 是否成功开始游戏
        """
        room = self.get_room(room_id)
        if room:
            return room.start_game()
        return False
    
    def handle_game_event(self, room_id, account, data):
        """
        处理游戏事件
        
        Args:
            room_id: 房间ID
            account: 玩家账号
            data: 事件数据
        
        Returns:
            dict: 事件处理结果
        """
        print("room_manager:",room_id, account, data)
        room = self.get_room(room_id)
        print(room.game_instance)
        if room and room.game_instance:
            return room.game_instance.handle_event(account, data)
        return {'ok': False, 'msg': '游戏未开始'}
    
    def get_game_state(self, room_id):
        """
        获取游戏状态
        
        Args:
            room_id: 房间ID
        
        Returns:
            dict: 游戏状态
        """
        room = self.get_room(room_id)
        if room and room.game_instance:
            return room.game_instance.get_state()
        return None
