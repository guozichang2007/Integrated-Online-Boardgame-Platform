# 游戏基类定义

class BaseGame:
    """
    所有游戏的基类，定义了游戏必须实现的接口
    """
    def __init__(self, room_id):
        """
        初始化游戏
        
        Args:
            room_id: 房间ID
        """
        self.room_id = room_id
        self.players = {}  # account -> 玩家信息
        self.started = False
        self.host = None
    
    def join(self, account, player_id):
        """
        玩家加入游戏
        
        Args:
            account: 玩家账号
            player_id: 玩家游戏ID
        
        Returns:
            int: 玩家顺序号，如果失败返回None
        """
        pass
        
    def leave(self, account):
        """
        玩家离开游戏
        
        Args:
            account: 玩家账号
        """
        pass
    
    def start(self):
        """
        开始游戏
        
        Returns:
            bool: 是否成功开始
        """
        pass
    
    def handle_event(self, account, data):
        """
        处理游戏事件
        
        Args:
            account: 发起事件的玩家账号
            data: 事件数据
        
        Returns:
            dict: 处理结果
        """
        pass
    
    def get_state(self,account=0):
        """
        获取游戏状态
        
        Returns:
            dict: 游戏状态数据
        """
        pass

    def handle_return(self, account):
        """
        处理玩家返回游戏
        
        Args:
            account: 玩家账号
        
        Returns:
            dict: 处理结果
        """
        self.get_state(account)
        pass

