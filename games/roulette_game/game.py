from games.base import BaseGame
import random

class RouletteGame(BaseGame):
    """
    Roulette轮盘赌游戏
    6张卡牌，1张爆炸，5张安全
    """
    def __init__(self, room_id):
        super().__init__(room_id)
        self.game_type = 'roulette'
        self.cards = []  # 卡牌数组：0=未翻开, 1=安全, 2=爆炸
        self.game_over = False
        self.shuffle_cards()
    
    def shuffle_cards(self):
        """洗牌：创建6张卡，随机一张是爆炸"""
        self.cards = [1, 1, 1, 1, 1, 2]  # 5张安全(1)，1张爆炸(2)
        random.shuffle(self.cards)
        self.revealed = [False] * 6  # 记录哪些卡已翻开
        self.game_over = False
    
    def join(self, account, player_id):
        if account in self.players:
            return None
        
        if self.host is None:
            self.host = account
        
        order = len(self.players) + 1
        self.players[account] = {
            'ID': player_id,
            'order': order
        }
        return order
    
    def leave(self, account):
        if account in self.players:
            del self.players[account]
            if account == self.host and self.players:
                self.host = next(iter(self.players.keys()))
    
    def start(self):
        if len(self.players) > 0:
            self.started = True
            self.shuffle_cards()
            return True
        return False
    
    def handle_event(self, account, data):
        event_name = data.get('event_name')
        
        if event_name == 'flip_card':
            # 翻牌事件
            card_index = data.get('event_data', {}).get('index', -1)
            
            if card_index < 0 or card_index >= 6:
                return {
                    'ok': False,
                    'msg': '无效的卡牌索引',
                    'broadcast': False
                }
            
            if self.revealed[card_index]:
                return {
                    'ok': False,
                    'msg': '该卡牌已经翻开',
                    'broadcast': False
                }
            
            if self.game_over:
                return {
                    'ok': False,
                    'msg': '游戏已结束',
                    'broadcast': False
                }
            
            # 翻开卡牌
            self.revealed[card_index] = True
            card_type = self.cards[card_index]
            
            if card_type == 2:  # 爆炸
                self.game_over = True
                msg = f'💥 爆炸！'
            else:  # 安全
                msg = f'✓ 安全！'
                # 检查是否全部安全卡都翻开了
                if all(self.revealed[i] or self.cards[i] == 2 for i in range(6)):
                    self.game_over = True
                    msg = f'🎉 恭喜！终于知道炸弹在哪里了！'
            
            return {
                'ok': True,
                'msg': msg,
                'cards_state': self.get_cards_state(),
                'game_over': self.game_over,
                'broadcast': True
            }
        
        elif event_name == 'reset':
            # 重置游戏
            self.shuffle_cards()
            return {
                'ok': True,
                'msg': '游戏已重置',
                'cards_state': self.get_cards_state(),
                'game_over': False,
                'broadcast': True
            }
        
        return {
            'ok': False,
            'msg': '未知事件类型',
            'broadcast': False
        }
    
    def get_cards_state(self):
        """
        获取卡牌状态
        返回数组，每个元素：0=未翻开, 1=安全, 2=爆炸
        """
        state = []
        for i in range(6):
            if self.revealed[i]:
                state.append(self.cards[i])  # 已翻开，显示真实状态
            else:
                state.append(0)  # 未翻开
        return state
    
    def get_state(self):
        return {
            'game_type': self.game_type,
            'room_id': self.room_id,
            'players': self.players,
            'started': self.started,
            'host': self.host,
            'cards_state': self.get_cards_state(),
            'game_over': self.game_over
        }

def register_game():
    return {
        'id': 'roulette',
        'name': 'Roulette',
        'description': '轮盘赌游戏 - 6张卡，1张爆炸，5张安全',
        'min_players': 1,
        'max_players': 1,
        'class': RouletteGame,
        'url': '/roulette'
    }
