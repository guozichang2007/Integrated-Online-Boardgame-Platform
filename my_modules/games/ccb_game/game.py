spawn= [[12,11],[10,5],[10,21],[15,7]]
from my_modules.games.base import BaseGame
#[[0,0],[0,4],[4,0],[4,4]]
import sys
import time
from flask_socketio import emit
sys.setrecursionlimit(3000)

class CCBGame(BaseGame):
    def __init__(self, room_id, rows=23, cols=23, command_point=0):
        # 地图尺寸[(i,j) for i in range (rows) for j in range (cols)]
        self.map=[(18, 0), (17, 0), (16, 1), (15, 1), (18, 1), (19, 2), (19, 3), (18, 3), (18, 2), (17, 1), (15, 2), (16, 2), (16, 3), (17, 3), (17, 4), (16, 4), (15, 4), (14, 4), (13, 4), (14, 5), (15, 5), (16, 5), (17, 6), (16, 6), (17, 7), (16, 7), (15, 6), (14, 6), (13, 5), (12, 6), (11, 5), (11, 4), (10, 5), (8, 5), (9, 4), (12, 7), (13, 7), (14, 7), (15, 7), (17, 8), (17, 9), (16, 9), (17, 10), (18, 10), (18, 11), (19, 11), (19, 12), (16, 8), (15, 8), (14, 8), (13, 8), (12, 8), (11, 7), (11, 8), (11, 9), (14, 9), (15, 9), (16, 10), (15, 11), (16, 11), (16, 12), (17, 13), (18, 14), (19, 14), (19, 15), (18, 15), (18, 16), (19, 17), (19, 18), (18, 19), (19, 19), (17, 20), (18, 20), (17, 21), (18, 21), (17, 22), (18, 22), (13, 9), (13, 10), (15, 10), (10, 8), (9, 8), (9, 10), (8, 10), (7, 10), (7, 11), (8, 11), (6, 11), (6, 12), (7, 12), (6, 9), (7, 8), (6, 8), (7, 9), (6, 10), (5, 9), (5, 10), (5, 11), (4, 11), (5, 12), (4, 12), (3, 12), (4, 13), (5, 13), (3, 13), (3, 14), (2, 14), (2, 15), (3, 15), (4, 15), (5, 15), (6, 15), (7, 14), (7, 15), (8, 14), (8, 15), (8, 16), (7, 16), (5, 16), (4, 16), (3, 16), (2, 16), (6, 16), (2, 17), (2, 18), (2, 19), (3, 19), (3, 18), (3, 17), (4, 17), (5, 17), (5, 18), (5, 19), (5, 20), (5, 21), (4, 21), (3, 22), (4, 22), (5, 22), (11, 10), (11, 11), (12, 12), (11, 13), (10, 13), (11, 14), (10, 15), (10, 16), (11, 15), (11, 16), (9, 17), (8, 17), (15, 13), (14, 13), (13, 14), (13, 15), (15, 12), (14, 12), (13, 12), (14, 11), (13, 11), (12, 11), (12, 10), (13, 13), (12, 13), (12, 14), (12, 15), (13, 16), (14, 16), (15, 17), (15, 18), (13, 17), (13, 18), (12, 17), (10, 17), (11, 17), (6, 17), (7, 17), (6, 18), (7, 18), (8, 18), (9, 18), (10, 18), (11, 18), (12, 18), (6, 19), (7, 19), (8, 19), (9, 19), (10, 19), (11, 19), (12, 19), (13, 19), (6, 20), (6, 21), (6, 22), (7, 22), (7, 21), (7, 20), (8, 20), (8, 21), (8, 22), (9, 22), (9, 21), (10, 21), (10, 22), (11, 22), (11, 21), (11, 20), (12, 20), (12, 21), (12, 22), (14, 19), (15, 20), (14, 20), (13, 20), (13, 21), (14, 21), (15, 21), (16, 21), (16, 22), (13, 22), (14, 22), (15, 22), (10, 9), (20, 1), (21, 1), (21, 0), (21, 2), (22, 3), (22, 4), (22, 2), (22, 1), (22, 0), (2, 2), (2, 3), (2, 4), (1, 2), (1, 3), (9, 5), (20, 12), (21, 12), (12, 9), (13, 6), (14, 10), (17, 2), (20, 15), (21, 15), (21, 16), (21, 13), (22, 11), (22, 12), (21, 10), (9, 20), (14, 14), (12, 16), (14, 15), (15, 14), (16, 13), (11, 12), (10, 20), (17, 14), (16, 14), (17, 15), (18, 18), (15, 15), (20, 18), (20, 19), (19, 20), (19, 21), (19, 22)]
        self.citys=[(9,20),(12,16),(12,13),(12,10),(7,12),(7,9),(14,11),(19,11),(13,7),(9,5),(17,3),(2,3),(20,15)]
        self.bot_code=[-4.594682023167071, 2.7102090237394676, 3.8143841826544205, 1.7437102156677093, 8.51263211671965, 7.9554866873944617, 100.645223055837255, 2.284336794471397, -24.5817870711665555, 0.4022051966992201, 2.5297317609303596, -0.5609423731225323, 0.19772768081500397, 2.6205667307618294, 1.0, 6,10]
        super().__init__(room_id)
        self.start_or_not = False
        self.debug=False
        self.rows = rows
        self.cols = cols
        self.host = None  # 主机 account
        # players: account -> [昵称(ID), 出手顺序(order), 剩余指挥点(command_point),max_command_point]
        self.players = {}
        # 下一个加入玩家的 order
        self.player_number = 0
        # 棋盘：rows x cols，每格 [owner, type]，初始都是 [0,0] [owner, type   ]
        self.board = [
            [[-1, -1] for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
        for (i,j) in self.map:
            if 0<=i<rows and 0<=j<cols:
                self.board[i][j]=[0,0]
        for (i,j) in self.citys:
            if 0<=i<rows and 0<=j<cols:
                self.board[i][j]=[-2,0]
        # 每位新手玩家的初始指挥点
        self.command_point = command_point
        self.turn = [1,1]  # [谁的回合，总回合]
        self.current_player=self.turn[0]
        self.spawn = spawn
        for i in range(len(spawn)):
            self.board[spawn[i][0]][spawn[i][1]] = [i+1,0]

    def start(self):#开始游戏 return：True/False
        """
        开始游戏：
        """
        self.real_player_number=self.player_number
        if self.player_number<4:
            self.join(('yes_i_am_a_bot'+str(self.player_number+1)),('bot'+str(self.player_number+1)))
        if self.player_number<4:
            self.join(('yes_i_am_a_bot'+str(self.player_number+1)),('bot'+str(self.player_number+1)))
        if self.player_number<4:
            self.join(('yes_i_am_a_bot'+str(self.player_number+1)),('bot'+str(self.player_number+1)))
        
        self.players[self.host][2]= self.players[self.host][3]
        self.start_or_not = True
        #print(self.players)
        self.update_board_information()
        return self.start_or_not

    def end_turn(self,account):#结束回合
        if not self.start_or_not:# players: account -> [昵称(ID), 出手顺序(order), 剩余指挥点(command_point),max_command_point,是否有核弹井,是否存活,场上活子]
            return
        if self.players[account][1] != self.turn[0]:
            return None
        for i,j in self.players.items():
            if j[1]==self.turn[0]:
                j[2]=0
        self.turn[0] += 1
        self.turn[1] += 1
        if self.turn[0]>self.player_number:
            self.turn[0]=(self.turn[0]+1) % (self.player_number+1) 
        for sid in self.players:
            if self.players[sid][1]==self.turn[0] and not self.players[sid][5]:
                self.turn[0] += 1
                if self.turn[0]>self.player_number:
                    self.turn[0]=(self.turn[0]+1) % (self.player_number+1) 
                print('跳过淘汰玩家的回合')
        for sid in self.players:
            if self.players[sid][1]==self.turn[0] and not self.players[sid][5]:
                self.turn[0] += 1
                if self.turn[0]>self.player_number:
                    self.turn[0]=(self.turn[0]+1) % (self.player_number+1) 
                print('跳过淘汰玩家的回合')
        for sid in self.players:
            if self.players[sid][1]==self.turn[0] and not self.players[sid][5]:
                self.turn[0] += 1
                if self.turn[0]>self.player_number:
                    self.turn[0]=(self.turn[0]+1) % (self.player_number+1) 
                print('跳过淘汰玩家的回合')
        #死了就下一个，死了就下一个
        if self.turn[0]>self.player_number:
            self.turn[0]=(self.turn[0]+1) % (self.player_number+1) 

        for sid in self.players:
            if self.players[sid][1]==self.turn[0]:
                self.players[sid][2]= self.players[sid][3]
        
        self.update_board_information()
        self.current_player=self.turn[0]
        if self.turn[0]>self.real_player_number:
            self.bot_place_piece()
    
    def join(self, account, ID="Anonymous"):#true：已经加入 None：加入失败 int：加入成功，返回顺序
        """
        玩家加入游戏：
        · account: 客户端唯一标识
        · ID: 可读昵称，默认为 "Anonymous"
        返回该玩家的出手顺序 order（1,2,3,4...），如果已满或已加入则返回 None
        """
        # 最多允许 4 名玩家，且同一个 account 不能重复 join
        if account in self.players:
            return None
        if self.start_or_not or self.player_number > 4:
            return None
        

        if self.host is None:
            self.host = account
        order = self.player_number+1
        self.players[account] = [ID, order, self.command_point,4,False ,True,0, [[1 for _ in range(self.cols)]for _ in range(self.rows)],False]
                                    #Id 序号 现有指挥点 指挥点槽 有无核弹 是否存活 场面棋子数量 可见范围
        self.player_number += 1
        return order
    
    def leave(self, account):
        """
        玩家离开游戏
        
        Args:
            account: 玩家账号
        """
        if account in self.players:
            del self.players[account]
            # 如果房主离开，重新选择房主
            if account == self.host and self.players:
                self.host = next(iter(self.players.keys()))

    def handle_event(self, account, data):
        """
        处理游戏事件
        
        Args:
            event_name: 事件名称
            account: 玩家账号
            data: 事件数据
        
        Returns:
            dict: 处理结果
        """
        if data.get('event_name') == 'place':
            # 处理落子事件
            print('我收到了',data)
            event_data = data.get('event_data')

            ptype = event_data.get('ptype')
            row = event_data.get('row')
            col = event_data.get('col')
            #print(account, ptype, row, col)
            ok, msg = self.place(account, ptype, row, col)
            return {
                'ok': ok,
                'msg': msg,
                'players': self.players,
                'turn': self.turn,
                'board': self.board,
                'broadcast': True
            }
        elif data.get('event_name') == 'skip_turn':
            # 处理跳过回合事件
            self.end_turn(account)
            return {
                'ok': True,
                'players': self.players,
                'turn': self.turn,
                'board': self.board,
                'broadcast': True
            }
        
        return {'ok': False, 'msg': '未知事件'}
    
    def handle_return(self, account):
        return {
                'ok': True,
                'msg': '重新加入游戏成功',
                'players': self.players,
                'turn': self.turn,
                'board': self.board,
                'broadcast': True
            }
    
    def get_state(self):
        """
        获取当前游戏状态，用于重连时刷新前端
        
        Returns:
            dict: 包含游戏完整状态的字典
        """
        return {
            'players': self.players,
            'turn': self.turn,
            'board': self.board
        }

    def bot_place_piece(self):
        
    # 建立所有合法方案
        time.sleep(0.5)
        player = self.current_player
        account='yes_i_am_a_bot'+str(self.current_player)
        avalable = []
        self.btn_nb=self.players[account][4]
        # 创建单位编号映射字典
        unit_mapping = {'A': 4, 'B': 1, 'C': 3, 'D': 2, 'E': 5, 'F': 6, 'H': 7}
        
        for piece_type in ['A', 'B', 'C', 'D', 'E', 'F','H']:
            flag = True
            if piece_type == "A":
                self.army = '战斗机'
                self.value = 3
            if piece_type == "B":
                self.army = '步兵'
                self.value = 1
            if piece_type == "C":
                self.army = '轰炸机'
                self.value = 3
            if piece_type == "D":
                self.army = '坦克'
                self.value = 2
            if piece_type == "E":
                self.army = '油井'
                self.value = 2
            if piece_type == "F":  # 有核弹井时F是核弹，无核弹井时F是核弹井
                if self.btn_nb:
                    self.army = '核弹'
                    self.value = 3
                else:
                    self.army = '核弹发射井'
                    self.value = 6
            if piece_type == "H":
                self.army = '指挥所'
                self.value = 2
            if self.value > self.players[account][2]:
                flag = False
            if flag:
                #print('价格测试通过')
                if True:
                    for i, j in self.map:
                        around = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, 1), (1, 0), (1, -1), (0, 0)]
                        flag = False
                        for dr, dc in around:
                            r, c = i + dr, j + dc
                            if (r, c) in self.map:
                                # 修改1: 检查是否为[0,0]而不是None
                                if self.board[r][c][1] != 0:
                                    # 修改2: 使用列表格式[玩家编号, 单位编号]
                                    if self.board[r][c][0] == player and self.board[r][c][1] != 5 :
                                        flag = True

                        # 开局出生点可放置棋子
                        if self.turn[1] <= 4:
                            if player == 1 and [i, j] == self.spawn[0]:
                                flag = True
                            elif player == 2 and [i, j]== self.spawn[1]:
                                flag = True
                            elif player == 3 and [i, j] == self.spawn[2]:
                                flag = True
                            elif player == 4 and [i, j] == self.spawn[3]:
                                flag = True
                        # 核弹可任意放置
                        if piece_type == 'F' and self.btn_nb:
                            flag = True
                        if flag:
                            # 修改3: 使用新的棋盘格式检查
                            if piece_type == 'A' or piece_type == 'C':
                                if self.board[i][j][1] != 0:
                                    if self.board[i][j][0] != player:
                                        flag = False

                            if piece_type == 'B':
                                cell = self.board[i][j]
                                # 修改4: 步兵检查逻辑调整
                                if cell[1] != 0 and not (cell[1] == unit_mapping['B'] and cell[0] != player) and not (cell[1] == unit_mapping['H'] and cell[0] != player):
                                    flag = False

                            if piece_type == 'D' or piece_type == 'H':
                                cell = self.board[i][j]
                                if cell[1] != 0:
                                    flag = False

                            if piece_type == 'E':
                                if self.board[i][j][1] != 0 or not ((i, j) in self.citys):
                                    flag = False

                            if piece_type == 'F' and not self.btn_nb:
                                cell = self.board[i][j]
                                if cell[1] != 0:
                                    flag = False
                        if flag:
                            strategy = [piece_type, i, j]
                            avalable.append(strategy)
        #print(avalable)
        priority_max = -10000000000000000
        [spawn_x,spawn_y]=self.spawn[self.current_player-1]
        best_strategy=['B',spawn_x,spawn_y]
        for s in avalable:
            piece_type = s[0]
            row = int(s[1])
            col = int(s[2])
            self.cleared = []
            self.cleared_friend = []
            
            # cost变量
            command_place = 0
            leader_yes_no = 1
            A = 0
            B = 0
            C = 0
            D = 0
            E = 0
            F = 0
            G = 0
            H = 0
            H_k = 0
            
            if piece_type == "A":
                cost = 3
                A = 1
            elif piece_type == "B":
                cost = 1
                B = 1
            elif piece_type == "C":
                cost = 3
                C = 1
            elif piece_type == "D":
                cost = 2
                D = 1
            elif piece_type == "E":
                cost = 2
                E = 1
            elif piece_type == "H":
                cost = 2
                H = 1
            elif piece_type == "F":
                if self.btn_nb:
                    cost = 3
                    G = 1
                else:
                    cost = 6
                    F = 1

            if piece_type == 'A':
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                place = 1
                if self.board[row][col][1]!=0:
                    self.cleared_friend.append((row,col))
                for dr, dc in directions:
                    r, c = row + dr, col + dc
                    if (r, c) in self.map:
                        # 修改5: 使用新的棋盘格式
                        if  self.board[r][c][0] != player and self.board[r][c][1] != unit_mapping['D']:
                            self.cleared.append((r, c))
                            if self.board[r][c][1] == unit_mapping['E']:
                                self.cnt_explode(r, c)

            elif piece_type == 'C':
                directions = [(-1, -1), (1, 1), (1, -1), (-1, 1)]
                place = 1
                if self.board[row][col][1]!=0:
                    self.cleared_friend.append((row,col))
                for dr, dc in directions:
                    r, c = row + dr, col + dc
                    if (r, c) in self.map:
                        # 修改6: 使用新的棋盘格式
                        if self.board[r][c][0] != player and self.board[r][c][1] != unit_mapping['C'] and self.board[r][c][1] != unit_mapping['A']:
                            self.cleared.append((r, c))
                            if self.board[r][c][1] == unit_mapping['E']:
                                self.cnt_explode(r, c)

            elif piece_type == 'B':
                if self.board[row][col][1] ==0:
                    place = 1
                elif self.board[row][col][1] == unit_mapping['B'] or self.board[row][col][1] == unit_mapping['H']:
                    place = 0
                    self.cleared.append((row, col))

            elif piece_type == 'D':
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                place = 1
                
                for dr, dc in directions:
                    r, c = row + dr, col + dc
                    count = 0
                    if (r, c) in self.map :
                        if self.board[r][c][0] != player:
                            for ddr, ddc in directions:
                                rn, cn = r + ddr, c + ddc
                                if (rn, cn) in self.map:
                                    if self.board[rn][cn] != [0, 0]:
                                        if self.board[rn][cn][0] == player and self.board[rn][cn][1] == unit_mapping['D']:
                                            count += 1
                    if count >= 3:
                        if self.board[r][c][0] == player:
                            self.cleared_friend.append((r, c))
                        else:
                            self.cleared.append((r, c))
                        if self.board[r][c][1] == unit_mapping['E']:
                            self.cnt_explode(r, c)

            elif piece_type == 'E':
                command_place = 1

            elif piece_type == 'F' and not self.btn_nb:
                place = 1

            elif piece_type == 'F' and self.btn_nb:
                place = -1
                self.cleared_friend.append((self.row_nb_well, self.col_nb_well))
                if True:
                    directions = [(0, 2), (0, -2), (2, 0), (-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, 1), (1, 0), (1, -1), (0, 0)]
                    
                    for dr, dc in directions:
                        r, c = row + dr, col + dc
                        if (r, c) in self.map:
                            # 修改7: 使用新的棋盘格式
                            if self.board[r][c] != [0, 0] and self.board[r][c][1] != unit_mapping['F'] and self.board[r][c][0] != player and ((r, c) not in self.cleared):
                                self.cleared.append((r, c))
                                if self.board[r][c][1] == unit_mapping['E']:
                                    self.cnt_explode(r, c)
                            if self.board[r][c] != [0, 0] and self.board[r][c][1] != unit_mapping['F'] and self.board[r][c][0] == player and ((r, c) not in self.cleared_friend):
                                self.cleared_friend.append((r, c))
                                if self.board[r][c][1] == unit_mapping['E']:
                                    self.cnt_explode(r, c)
                            
                            if self.board[r][c] != [0, 0] and self.board[r][c][1] == unit_mapping['F']:
                                for dr2, dc2 in directions:
                                    rn, cn = self.row_nb_well + dr2, self.col_nb_well + dc2
                                    if (rn, cn) in self.map:
                                        if self.board[rn][cn] != [0, 0] and self.board[rn][cn][1] != unit_mapping['F'] and self.board[rn][cn][0] != player:
                                            if (rn, cn) not in self.cleared:
                                                self.cleared.append((rn, cn))
                                            if self.board[rn][cn][1] == unit_mapping['E']:
                                                self.cnt_explode(rn, cn)
                                        
                                        if self.board[rn][cn] != [0, 0] and self.board[rn][cn][1] != unit_mapping['F'] and self.board[rn][cn][0] == player:
                                            if (rn, cn) not in self.cleared_friend:
                                                self.cleared_friend.append((rn, cn))
                                            if self.board[rn][cn][1] == unit_mapping['E']:
                                                self.cnt_explode(rn, cn)
                                        
                                        if self.board[rn][cn] != [0, 0] and self.board[rn][cn][1] == unit_mapping['F']:
                                            for dr3, dc3 in directions:
                                                rnn, cnn = r + dr3, c + dc3
                                                if (rnn, cnn) in self.map:
                                                    if self.board[rnn][cnn] != [0, 0] and self.board[rnn][cnn][1] != unit_mapping['F'] and self.board[rnn][cnn][0] != player:
                                                        if (rnn, cnn) not in self.cleared:
                                                            self.cleared.append((rnn, cnn))
                                                        if self.board[rnn][cnn][1] == unit_mapping['E']:
                                                            self.cnt_explode(rnn, cnn)
                                                    
                                                    if self.board[rnn][cnn] != [0, 0] and self.board[rnn][cnn][1] != unit_mapping['F'] and self.board[rnn][cnn][0] == player:
                                                        if (rnn, cnn) not in self.cleared_friend:
                                                            self.cleared_friend.append((rnn, cnn))
                                                        if self.board[rnn][cnn][1] == unit_mapping['E']:
                                                            self.cnt_explode(rnn, cnn)

            # 后面的计算和决策逻辑保持不变...
            gain = len(self.cleared)
            lose = len(self.cleared_friend)
            command_place_gain = command_place
            command_place_lose = 0

            for (i, j) in self.cleared:
                if self.board[i][j][1] == unit_mapping['E']:
                    command_place_gain += 1
            for (i, j) in self.cleared_friend:
                if self.board[i][j][1] == unit_mapping['E']:
                    command_place_lose += 1


            touch=0
            around=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,1),(1,0),(1,-1),(0,0)]
            neighbor=[(-1,0),(0,-1),(0,1),(1,0)]
                        
            for dr, dc in around:
                r, c = row + dr, col + dc
                if (r,c) in self.map:
                    if self.board[r][c][1]==0:
                        flage=True
                        for ddr, ddc in around:
                            rn, cn = row + dr, col + dc
                            if (rn,cn) in self.map:
                                if self.board[rn][cn][0]==player and self.board[rn][cn][1]!=5:
                                    flage=False
                        if flage:
                            touch+=1
            # 剩余代码保持不变...
            # ... (touch计算、space_number计算等)

            # 计算不同兵种
            for (x, y) in self.cleared:
                unit_num = self.board[x][y][1]
                if unit_num == unit_mapping['A']:
                    A += 1
                elif unit_num == unit_mapping['B']:
                    B += 1
                elif unit_num == unit_mapping['C']:
                    C += 1
                elif unit_num == unit_mapping['D']:
                    D += 1
                elif unit_num == unit_mapping['E']:
                    E += 1
                elif unit_num == unit_mapping['F']:
                    F += 1
                elif unit_num == unit_mapping['H']:
                    H_k += 1
            
            for (x, y) in self.cleared_friend:
                unit_num = self.board[x][y][1]
                if unit_num == unit_mapping['A']:
                    A -= 1
                elif unit_num == unit_mapping['B']:
                    B -= 1
                elif unit_num == unit_mapping['C']:
                    C -= 1
                elif unit_num == unit_mapping['D']:
                    D -= 1
                elif unit_num == unit_mapping['E']:
                    E -= 1
                elif unit_num == unit_mapping['F']:
                    F -= 1
            danger=0
            for dr,dc in around:
                r,c=row+dr, col+dc
                if (r,c) in self.map:
                    if self.board[r][c][1]!=0:
                        if self.board[r][c][1]!=player:
                            danger+=1
            cross=0
            for dr,dc in neighbor:
                r,c=row+dr, col+dc
                if (r,c) in self.map:
                    if self.board[r][c][1] !=0:
                        if self.board[r][c][1]!=player:
                            cross+=1
            
            danger_yes_no=0
            if danger != 0:
                danger_yes_no =1

            leader_yes_no=0
            if self.players[account][8]:
                leader_yes_no=1
            min_space_number=10000
            max_space_number=0
            for k in self.players :
                if self.players[k][6]< min_space_number and k!= account and self.players[k][5] :
                    min_space_number=self.players[k][6]
                    min_enemy=k
                
                if self.players[k][6]> max_space_number and k!= account and self.players[k][5]:
                    max_space_number=self.players[k][6]
                    max_enemy=k
            kill_number=[0,0,0,0,0]
            kill_real=0
            for (x,y)in self.cleared:
                for k in [1,2,3,4]:
                    if self.board[x][y][0]==(k):
                        kill_number[k]+=1
                    if k<=self.real_player_number and self.board[x][y][0]==(k):
                        kill_real+=1

            '''if min_space_number-kill_number[min_enemy]==0:
                you_per_min=1000000000
            else:
                you_per_min=(self.players[account][6]-lose+1)/(min_space_number-kill_number[min_enemy])'''

            if max_space_number-kill_number[self.players[max_enemy][1]]==0:
                you_per_max=1000000000
            
            else:
                you_per_max=(self.players[account][6]-lose+1)/(max_space_number-kill_number[self.players[max_enemy][1]])-self.players[account][6]/max_space_number

            if self.players[account][6]-lose<=1:
                you_per_max=-100000000000
            [c_cost, c_A, c_B,c_C,c_D,c_E,c_F,c_gain,c_lose,c_place,c_cmd_gain,c_cmd_lose,c_touch,c_y_p_m,c_y_p_max,c_player,c_H]=self.bot_code
                #初始(-1,1.5,1,1.5,2,1,7,1,-1,1,2,-2,0.5)
            #print(H*1000*(1-leader_yes_no)*(9-danger))
            priority=c_cost*cost + c_A*A + c_B*B +c_C*C +c_D*D +c_E*E*(1-danger_yes_no+cross) +c_F*F*(9-touch-danger) +10000000000000*G*(gain-lose)+ c_gain*gain + c_lose*lose +c_place*place +c_cmd_gain*command_place_gain +c_cmd_lose*command_place_lose+c_touch*touch+c_y_p_m*kill_number[self.players[min_enemy][1]]+c_y_p_max*you_per_max+c_player*kill_real+H*100000*(1-leader_yes_no)*(9-2*danger)+H_k*c_H
            
            if priority > priority_max:
                priority_max=priority
                best_strategy=s
                print(best_strategy)
            #print(s,gain,lose,self.cleared,self.cleared_friend)
            # 优先级计算保持不变...
            # ... (priority计算)

        # 执行最佳策略部分也需要修改
        if True:
            print(best_strategy,self.players)
            npiece_type = unit_mapping[best_strategy[0]]
            row = int(best_strategy[1])
            col = int(best_strategy[2])
            cost_map = [0,1,2,3,3,2,6,2]#0,步兵，坦克，轰炸机，战斗机，核弹
        if not self.btn_nb or npiece_type != 6:
            cost = cost_map[npiece_type]
        else:
            cost=3
        

        # 5. 扣除指挥点
        self.players[account][2] -= cost

        # 6. 落子
        
        
        if npiece_type == 1:
            self._resolve_infantry_combat(player, row, col)
        elif npiece_type == 2:
            self.board[row][col] = [player, 2]
            self._tank_surround_clear(account, row, col)
        elif npiece_type == 3:
            print("轰炸机")
            self.board[row][col] = [player, 3]
            self._clear_adjacent_enemy(row, col, diag=True)
        elif npiece_type == 4:
            print("战斗机")
            self.board[row][col] = [player, 4]
            self._clear_adjacent_enemy(row, col, diag=False)
        elif npiece_type == 5:
            self.board[row][col] = [player, 5]
        elif npiece_type == 6 and not self.btn_nb:
            self.board[row][col] = [player, 6]
        elif npiece_type == 6 and self.btn_nb:
            self._launch_nuke(player,row,col)
        elif npiece_type == 7:
            self.board[row][col] = [player, 7]

        self.update_board_information()

        if self.players[account][2] < 1 or not self.players[account][5]:
            self.end_turn(account)
        else:
            self.bot_place_piece()

    # 修改cnt_explode函数
    def cnt_explode(self, row, col):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        player = self.current_player
        unit_mapping = {'A': 3, 'B': 1, 'C': 4, 'D': 2, 'E': 5, 'F': 6, 'H': 7}

        if (row, col) not in self.cleared and self.board[row][col][0] != player:
            self.cleared.append((row, col))
        if (row, col) not in self.cleared_friend and self.board[row][col][0] == player:
            self.cleared_friend.append((row, col))

        for dr, dc in directions:
            r, c = row + dr, col + dc
            if (r, c) in self.map:
                # 修改11: 使用新的棋盘格式
                if self.board[r][c] != [0, 0] and ((r, c) not in self.cleared) and self.board[r][c][0] != player and self.board[r][c][1] != unit_mapping['E']:
                    self.cleared.append((r, c))
                elif self.board[r][c] != [0, 0] and ((r, c) not in self.cleared_friend) and self.board[r][c][0] == player and self.board[r][c][1] != unit_mapping['E']:
                    self.cleared_friend.append((r, c))
                elif self.board[r][c] != [0, 0] and ((r, c) not in self.cleared) and ((r, c) not in self.cleared_friend) and self.board[r][c][1] == unit_mapping['E']:
                    self.cnt_explode(r, c)

    def update_board_information(self):
        
        for sid in self.players:
            self.players[sid][8]=False
            for (i,j) in self.map :
                player=self.players[sid][1]
                if self.board[i][j][0]==player and self.board[i][j][1]==7:
                    self.players[sid][8]=True 
                #检测指挥
        for sid in self.players:
            self.players[sid][4]=False
            well_number=0
            for (i,j) in self.map :
                player=self.players[sid][1]
                if self.board[i][j][0]==player and self.board[i][j][1]==6:
                    self.players[sid][4]=True 
                    if player==self.turn[0]:
                        self.row_nb_well,self.col_nb_well=i,j
                    #检测是否有核弹井
                if self.board[i][j][0]==player and self.board[i][j][1]==5:
                    well_number+=1
                    #检测油井
                self.players[sid][7][i][j]=0
                if self.players[sid][8]:
                    for r,c in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,1),(1,0),(1,-1),(0,0)]:  
                        if (i+r,j+c) in self.map:
                            if self.board[i+r][j+c][0]==player and self.board[i+r][j+c][1]!=0 and self.board[i+r][j+c][1]!= 5:
                                self.players[sid][7][i][j]=1
                
                if self.board[i][j][0]==player:
                    self.players[sid][7][i][j]=1
                
                if not self.players[sid][5] or self.debug:
                    self.players[sid][7][i][j]=1

                    #检测可视

                    
                
            self.players[sid][3]=4+well_number
        self.check_win()
        for (i,j) in self.citys:
            if self.board[i][j]==[0,0]:
                self.board[i][j]=[-2,0]
        self.current_player=self.turn[0]

        #print (self.players)
        emit('board_update',{
            'board': self.board,
            'turn': self.turn,
            'players': self.players
            })
    
    def check_win(self):
        for sid in self.players:
            if self.players[sid][5]:
                count=0
                for (i,j) in self.map :
                    player=self.players[sid][1]
                    if self.board[i][j][0]==player and self.board[i][j][1] != 5 and self.board[i][j] !=0:
                        count+=1
                self.players[sid][6]=count
                if self.turn[1]>self.player_number and count==0:
                    self.players[sid][5]=False
                    



    def place(self, account, piece_type,row, col):#T/F是否成功下子，详细信息
        """
        玩家落子：
        · account: 玩家标识
        · row, col: 落子坐标（0-based）
        · piece_type: 棋子类型，int
             1=步兵, 2=坦克, 3=轰炸机, 4=战斗机, ...
        返回 True/False 表示落子是否成功。
        规则：
        1. 必须是已加入玩家
        2. 坐标合法且该格为空
        3. 玩家剩余指挥点 >= 该棋子消耗
        4. 扣除指挥点并在 board 上写入 [order, piece_type]
        """
        #1=步兵  2=坦克  3=轰炸机  4=战斗机  5=油井  6=核弹/发射井
        if not self.start_or_not:
            return False,"游戏还没开始！"
        # 1. 验证玩家已加入
        if account not in self.players:
            return False,"你还没有加入游戏！"
        player = self.players[account]
        btn_nb = self.players[account][4]
        
    
        
            # 2. 判断第1回合后是否与己方非油井相邻2
        around = [(-1,-1),(-1,0),(-1,1),
                (0,-1), (0,0), (0,1),
                (1,-1),(1,0),(1,1)]
        adjacent_friend = False
        for dr, dc in around:
            r, c = row+dr, col+dc
            if 0 <= r < self.rows and 0 <= c < self.cols:
                owner, t = self.board[r][c]
                # t!=5 表示不是油井
                if owner == player[1] and t != 5 and t != 0:
                    adjacent_friend = True
                    break
        if self.turn[1]<=self.player_number:
            if [row,col] == self.spawn[player[1]-1]:
                adjacent_friend = True


        # 回合>1 且不符合相邻或核弹特殊条件，则不允许下子
        if (not adjacent_friend) :
            # 核弹(6)在有发射井(self.btn_nb=True)时可跨格
            if not (piece_type == 6 and btn_nb):
                return False,"不相邻"
        
        # 3. 目标格检查
        if (row,col) in self.map:
            owner, t = self.board[row][col]
        enable = False

        # 3.1 战斗机(4)和轰炸机(3)：可空格或己方格
        if piece_type in (3, 4):
            enable = (t == 0) or (owner == player[1])

        # 3.2 步兵(1)：可空格或步兵格
        elif piece_type == 1:
            enable = (t == 0) or (t == 1 and owner != player[1]) or (t == 7 and owner != player[1])

        # 3.3 坦克(2)和核弹(6)：必须空格
        elif piece_type == 2:
            enable = (t == 0)

        # 3.4 油井(5)：必须空格且落点为城市
        elif piece_type == 5:
            enable = (t == 0) and (row,col) in self.citys

        elif piece_type == 6 and not btn_nb:
            enable = (t == 0)
        
        elif piece_type == 6 and btn_nb:
            enable = True

        elif piece_type == 7:
            enable = (t == 0)

        if (row,col) not in self.map:
            enable=False

        if not enable:
            # 落点不合法
            return False,"非法落子！"
        # 4. 棋子指挥点消耗
        cost_map = [0,1,2,3,3,2,6,2]#0,步兵，坦克，轰炸机，战斗机，核弹
        if not btn_nb or piece_type != 6:
            cost = cost_map[piece_type]
        else:
            cost=3
        if cost is None:
            # 不支持的棋子类型
            return False,"不支持的棋子类型！"

        # 5. 扣除指挥点
        
        if player[2] < cost:
            return False,"指挥点不足"
        player[2] -= cost

        # 6. 落子
        
        
        if piece_type == 1:
            self._resolve_infantry_combat(player[1], row, col)
        elif piece_type == 2:
            self.board[row][col] = [player[1], 2]
            self._tank_surround_clear(player[1], row, col)
        elif piece_type == 3:
            print("轰炸机")
            self.board[row][col] = [player[1], 3]
            self._clear_adjacent_enemy(row, col, diag=True)
        elif piece_type == 4:
            print("战斗机")
            self.board[row][col] = [player[1], 4]
            self._clear_adjacent_enemy(row, col, diag=False)
        elif piece_type == 5:
            self.board[row][col] = [player[1], 5]
        elif piece_type == 6 and not btn_nb:
            self.board[row][col] = [player[1], 6]
        elif piece_type == 7:
            self.board[row][col] = [player[1], 7]
        elif piece_type == 6 and btn_nb:
            self._launch_nuke(player[1],row,col)

        self.update_board_information()

        if player[2] < 1 or not player[5]:
            self.end_turn(account)
            return True,"end_turn"
        return True,"continue"

    def _clear_adjacent_enemy(self, row, col, diag=False):
        """
        放置战机(4)或轰炸机(3)后，清除上下左右（或斜对角）相邻的所有敌方单位。
        · diag True：斜对角方向 轰炸机 3
        · diag False：上下左右方向 轰炸机 4
        """
        # 四方向 / 四斜角
        if diag:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # 斜对角方向
            for dr, dc in directions:
                r, c = row + dr, col + dc
                # 检查 (r, c) 是否在有效范围内
                if (r,c) in self.map:
                    owner, ptype = self.board[r][c]
                    # 只要是敌人（owner != 0 且 != 当前玩家），并且不是轰炸机或战斗机，清除
                    if owner != 0 and owner != self.turn[0] and ptype != 3 and ptype != 4:
                        if ptype != 5:
                            self.board[r][c] = [0, 0]
                        elif ptype == 5:
                            self.explode(r,c)
            print("斜对角方向")

        else:
            directions = [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                if (r,c) in self.map:
                    owner, ptype = self.board[r][c]
                    # 只要是敌人（owner != 0 且 != self.current_player），就清除
                    if owner != 0 and owner != self.turn[0] and ptype != 2:
                        if ptype != 5:
                            self.board[r][c] = [0, 0]
                        elif ptype == 5:
                            self.explode(r,c)
            print("上下左右方向")

        self.update_board_information()

    def _resolve_infantry_combat(self, player, row, col):
        """
        步兵(1)落子逻辑：
        - 目标格空：占领 → [player,1]
        - 目标已有步兵(1)：同归于尽 → 清空
        """
        owner, ptype = self.board[row][col]
        if ptype == 0:
            # 空格，占领
            self.board[row][col] = [player, 1]
        elif ptype == 1 or ptype == 7:
            # 同归于尽
            self.board[row][col] = [0, 0]
        
        self.update_board_information()

    def _tank_surround_clear(self, player, row, col):
        """
        坦克(2)放置后：
        检查上下左右四个方向上每个格子，
        如果那个格子是敌人（owner != player），
        且它被 >=3 个友军坦克(2)包围，则清除该格的单位。
        """
        directions = [(-1,0),(1,0),(0,-1),(0,1)]


        for dr, dc in directions:
            r, c = row + dr, col + dc
            if (r, c) not in self.board:
                continue


            owner, ptype = self.board[r][c]
            # 只处理敌人
            if owner != 0 and owner != player:
                # 统计它周围（上下左右）属于本 player 且 type==2 的坦克数量
                cnt = 0
                for ddr, ddc in directions:
                    rr, cc = r + ddr, c + ddc
                    if (rr, cc) in self.board:
                        o, t = self.board[rr][cc]
                        if o == player and t == 2:
                            cnt += 1
                if cnt >= 3:
                    # 清除被包围的敌人
                    if ptype != 5:
                        self.board[r][c] = [0, 0]
                    elif ptype == 5:
                        self.explode(r,c)

        self.update_board_information()

    def _launch_nuke(self, player, row, col):
        """
        发射核弹(6)：
        · 扣除 3 点指挥点
        · 清除之前放置的那口发射井
        · 对目标点曼哈顿距离 < 2 范围内的所有格子一律清空
        """
        # 拆除已经放好的发射井
        self.update_board_information()
        self.board[self.row_nb_well][self.col_nb_well] = [0, 0]


        # 包括自身在内的 “半径 1+骑士位” 范围
        directions = [
            (0,2),(0,-2),(2,0),(-2,0),
            (-1,-1),(-1,0),(-1,1),(0,-1),
            (0,1),(1,-1),(1,0),(1,1),(0,0)
        ]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if (r, c) in self.map:
                owner, ptype = self.board[r][c]
                if ptype != 5 and ptype != 6:
                    self.board[r][c] = [0, 0]
                elif ptype == 6:
                    for drr, dcc in directions:
                        rr, cc = self.row_nb_well + drr, self.col_nb_well + dcc
                        if (rr,cc) in self.map:
                            downer, dptype = self.board[rr][cc]
                            if dptype != 5:
                                self.board[rr][cc] = [0, 0]
                            elif dptype == 5:
                                self.explode(rr,cc)
                    self.board[r][c] = [0, 0]
                elif ptype == 5:
                    self.explode(r,c)
        self.update_board_information()
                
    def explode(self, row, col):
        """
        油井(5)被炸时的连锁爆炸：
        · 当前格清空
        · 上下左右如遇油井，递归爆炸
        · 非油井的敌我单位一律清空
        """
        # 先炸掉自己
        self.board[row][col] = [0, 0]


        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if (r, c) not in self.map:
                continue


            owner, ptype = self.board[r][c]
            if ptype == 5:
                # 连锁炸油井
                self.explode(r, c)
            elif owner != 0:
                # 清除非油井的所有单位
                self.board[r][c] = [0, 0]


def test_print(game):
    for row in game.board:
        print(row)

if __name__ == "__main__":
    game = CCBGame()
    account_a = "socket123"
    host_account = None
    game.players={}
    game.player_number=0
    account_a='1'
    host_account = account_a
    game.host= account_a
    while 1:
        if True:
            test_print(game)
            print(game.players,game.turn)
            print("请输入你的指令：1.加入游戏 2.落子 3.开始游戏 4.结束回合")
            order=int(input())
            if order==1:
                #ID=input("请输入昵称：")
                account_a=input("1,请输入你的account：")
                game.join(account_a)
                if host_account is None:
                    host_account = account_a
                
            if order==2:
                account_a=input("2,请输入你的account：")
                piece_type=int(input("请输入棋子类型："))
                row=int(input("请输入行："))
                col=int(input("请输入列："))
                result=game.place(account_a,piece_type,row,col)
                print(result)
            if order==3:
                game.start(host_account)
            if order==4:
                game.end_turn(str(game.turn[0]))
                test_print(game)

def register_game():
    """
    注册CCB游戏
    
    Returns:
        dict: 游戏信息
    """
    return {
        'id': 'ccb_game',
        'name': 'CCB战棋',
        'description': '一款策略战棋游戏',
        'min_players': 1,
        'max_players': 4,
        'class': CCBGame,
        'url': '/ccb'
    }
