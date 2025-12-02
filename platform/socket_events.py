# 平台Socket事件处理模块
# 负责处理所有实时通信事件，包括用户认证、房间管理和游戏流程控制
# 作为前端和后端服务之间的实时通信桥梁

from flask_socketio import emit, join_room, leave_room  # Socket.IO功能，用于发送事件和房间管理
from platform.auth import login_user, update_user_room, verify_token  # 导入认证相关功能
from flask import request
from platform.auth import get_user

# 存储token到Socket会话ID的映射（用于向特定用户发送消息）
account_to_sid = {}  # 键: token, 值: socket session id
# 存储Socket会话ID到token的映射
sid_to_token = {}  # 键: socket session id, 值: token

def init_socket_events(socketio, room_manager):
    """
    初始化Socket事件处理
    
    参数：
    - socketio: SocketIO实例，用于注册事件处理器
    - room_manager: 房间管理器实例，提供房间管理功能
    
    功能：
    - 注册所有Socket.IO事件处理器
    - 将Socket.IO事件与房间管理器功能连接起来
    - 实现实时通信和游戏流程控制
    """
    # Socket连接事件（验证token）
    @socketio.on('connect')
    def handle_connect(auth):
        """
        处理Socket连接事件，验证token
        
        参数：
        - auth: 包含认证信息的字典，包含token字段
        
        功能流程：
        1. 从auth中获取token
        2. 验证token是否有效
        3. 如果有效，建立token与sid的映射
        4. 如果无效，拒绝连接
        """
        token = auth.get('token') if auth else None
        
        if token:
            account = verify_token(token)
            if account:
                sid = request.sid
                account_to_sid[account] = sid
                sid_to_token[sid] = token
                print(f"用户通过token连接成功: account={account}, sid={sid}")
                return True
        
        # Token无效或不存在，但仍允许连接（用于登录）
        print(f"Socket连接: sid={request.sid}, 未提供有效token")
        return True
    
    # 重新连接事件
    @socketio.on('token_reconnect')
    def handle_token_reconnect(data):
        """
        处理Socket重新连接事件，验证token
        
        参数：
        - data: 包含认证信息的字典，包含token字段
        
        功能流程：
        1. 从data中获取token
        2. 验证token是否有效
        3. 如果有效，建立token与sid的映射
        4. 如果无效，发送错误响应
        """
        token = data.get('token')
        
        if token:
            account = verify_token(token)
            if account:
                sid = request.sid
                account_to_sid[account] = sid
                sid_to_token[sid] = token
                print(f"用户通过token重新连接成功: account={account}, sid={sid}")
                room_id=get_user(account).get('room')
                if(room_id):
                    print(f"用户 {account} 重新连接后加入房间: {room_id}")
                room=room_manager.get_room(room_id)
                start_or_not=room.get_info().get('game_started') if room else False
                if(start_or_not):
                    print(f"用户 {account} 重新连接后游戏已开始，重新加入游戏")
                    result =room_manager.handle_reconnect(room_id, account)
                    emit('reconnect_response', {account: account, result: result})
                    return
                return
        
        # Token无效或不存在，发送错误响应
        print(f"Socket重新连接失败: sid={request.sid}, 无效token")
        emit('reconnect_response', {
            'ok': False,
            'msg': '无效的token，重新连接失败'
        })
    # 登录事件
    @socketio.on('login')
    def handle_login(data):
        """
        处理用户登录事件
        
        参数：
        - data: 包含登录信息的字典，必须包含account和password字段
        
        功能流程：
        1. 从请求数据中提取账号和密码
        2. 调用login_user验证用户凭据
        3. 登录成功时：
           - 返回token给前端
           - 建立token与sid的映射
        4. 登录失败时：
           - 返回失败响应，包含错误信息
        
        事件响应：
        - 成功: 'login_response' 事件，包含ok=True、token和用户信息
        - 失败: 'login_response' 事件，包含ok=False和错误消息
        """
        # 从请求数据中提取账号和密码
        account = data.get('account')
        password = data.get('password')
        
        # 调用登录函数验证用户凭据
        result = login_user(account, password)
        
        if result['ok']:
            # 登录成功，保存token与sid的映射
            token = result['token']
            sid = request.sid
            #account_to_sid[account] = sid
            sid_to_token[sid] = token
            
            print(f"用户 {account} 登录成功，token已生成")
            #暂时退出房间
            leave_room(account)
            # 返回登录结果给客户端（包含token）
            emit('login_response', {
                'ok': True,
                'msg': '登录成功',
                'token': token,
                'account': account,
                'room': result['user']['room'],
                'ID': result['user']['ID']
            })
        else:
            # 登录失败，返回错误信息
            print(f"用户 {account} 登录失败: {result.get('msg')}")
            emit('login_response', {
                'ok': False,
                'msg': result['msg']
            })
    
    # 创建房间事件
    @socketio.on('create_room')
    def handle_create_room(data):
        """
        处理创建房间事件
        
        参数：
        - data: 包含房间创建信息的字典，必须包含room_id字段
        
        功能流程：
        1. 验证用户是否已登录
        2. 验证房间ID是否提供
        3. 调用room_manager创建房间
        4. 创建成功时：
           - 将用户加入Socket.IO房间
           - 更新用户房间信息
           - 返回成功响应
           - 广播房间信息给房间内所有用户
        5. 创建失败时：
           - 返回失败响应，包含错误信息
        
        事件响应：
        - 成功: 'create_room_response' 和 'room_info' 事件
        - 失败: 'create_room_response' 事件，包含错误消息
        """
        # 获取当前会话对应的用户账号
        token=data.get('token')
        account = verify_token(token)
        print(f"socket:token = {token}, account = {account}")
        # 验证用户是否已登录
        if not account:
            emit('create_room_response', {
                'ok': False,
                'msg': '请先登录'
            })
            return
        
        # 获取房间ID和用户信息
        room_id = data.get('room_id')
        user_info = get_user(account)
        
        # 验证房间ID是否提供
        if not room_id:
            emit('create_room_response', {
                'ok': False,
                'msg': '房间号不能为空'
            })
            return
        
        print(f"用户 {account} 请求创建房间: {room_id}")
        
        # 创建房间
        room = room_manager.create_room(room_id, account, user_info)
        
        if room:
            # 将用户加入Socket.IO房间
            join_room(room_id)
            # 更新用户房间信息
            update_user_room(account, room_id)
            
            print(f"房间 {room_id} 创建成功，房主: {account}")
            
            # 返回创建成功响应
            emit('create_room_response', {
                'ok': True,
                'msg': '房间创建成功',
                'room_id': room_id
            })
            
            # 发送房间信息给房间内所有用户
            emit('room_info', {
                'room_id': room_id,
                'host': account,
                'players': room.players
            }, room=room_id)
        else:
            # 房间创建失败，返回错误信息
            print(f"房间 {room_id} 创建失败: 房间已存在")
            emit('create_room_response', {
                'ok': False,
                'msg': '房间已存在'
            })
    
    # 加入房间事件
    @socketio.on('join_room')
    def handle_join_room(data):
        """
        处理加入房间事件
        
        参数：
        - data: 包含房间加入信息的字典，必须包含room_id字段
        
        功能流程：
        1. 验证用户是否已登录
        2. 验证房间ID是否提供
        3. 调用room_manager加入房间
        4. 加入成功时：
           - 将用户加入Socket.IO房间
           - 更新用户房间信息
           - 获取玩家在游戏中的顺序（如果已选择游戏）
           - 返回成功响应，包含房间信息和是否为房主
           - 广播房间信息更新给房间内所有用户
        5. 加入失败时：
           - 返回失败响应，包含错误信息
        
        事件响应：
        - 成功: 'join_room_response' 和 'room_info_updated' 事件
        - 失败: 'join_room_response' 事件，包含错误消息
        """
        # 获取当前会话对应的用户账号
        token=data.get('token')
        account = verify_token(token)
        
        # 验证用户是否已登录
        if not account:
            emit('join_room_response', {
                'ok': False,
                'msg': '请先登录'
            })
            return
        
        # 获取房间ID和用户信息
        room_id = data.get('room_id')
        user_info = get_user(account)
        
        # 验证房间ID是否提供
        if not room_id:
            emit('join_room_response', {
                'ok': False,
                'msg': '房间号不能为空'
            })
            return
        
        print(f"用户 {account} 请求加入房间: {room_id}")
        
        # 尝试加入房间
        room = room_manager.join_room(room_id, account, user_info)
        
        if room:
            # 将用户加入Socket.IO房间
            join_room(room_id)
            # 更新用户房间信息
            update_user_room(account, room_id)
            
            # 获取玩家在游戏中的顺序（如果已选择游戏）
            order = None
            if room.game_instance and account in room.game_instance.players:
                order = room.game_instance.players[account][1]  # 假设players结构为{account: [ID, order, ...]}
            
            print(f"用户 {account} 成功加入房间: {room_id}")
            
            # 返回加入成功响应
            emit('join_room_response', {
                'ok': True,
                'msg': '加入房间成功',
                'room_id': room_id,
                'order': order,  # 玩家在游戏中的顺序
                'is_host': room.is_host(account)  # 是否为房主
            })
            
            # 广播房间信息更新给房间内所有用户
            emit('room_info_updated', {
                'room_id': room_id,
                'host': room.host_account,
                'players': room.players,
                'selected_game': room.selected_game
            }, room=room_id)
        else:
            # 加入失败，返回错误信息
            print(f"用户 {account} 加入房间 {room_id} 失败")
            emit('join_room_response', {
                'ok': False,
                'msg': '房间不存在或游戏已开始'
            })
    
    # 离开房间事件
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """
        处理离开房间事件
        
        参数：
        - data: 保留参数（前端不再需要传room_id）
        
        功能流程：
        1. 验证用户是否已登录
        2. 通过request.sid和sid_to_account找到account
        3. 使用get_user(account)获取用户信息，从中获取当前房间ID
        4. 调用room_manager离开房间
        5. 离开Socket.IO房间
        6. 更新用户房间信息为空
        7. 如果房间仍然存在，广播房间信息更新
        8. 返回离开成功响应
        
        事件响应：
        - 成功: 'leave_room_response' 事件
        - 房间仍存在时: 'room_info_updated' 事件广播给剩余用户
        """
        # 获取当前会话对应的用户账号
        token=data.get('token')
        account = verify_token(token)
        
        if not account:
            return
        
        # 通过账号查询用户信息，获取当前所在房间
        user_info = get_user(account)
        room_id = user_info.get('room') if user_info else None
        
        if room_id:
            print(f"用户 {account} 请求离开房间: {room_id}")
            
            # 从房间管理器中离开房间
            room_manager.leave_room(room_id, account)
            # 离开Socket.IO房间
            leave_room(room_id)
            # 更新用户房间信息为空
            update_user_room(account, None)
            
            print(f"用户 {account} 已离开房间: {room_id}")
            
            # 广播房间信息更新给剩余用户
            room = room_manager.get_room(room_id)
            if room:
                emit('room_info_updated', {
                    'room_id': room_id,
                    'host': room.host_account,
                    'players': room.players
                }, room=room_id)
            
            # 返回离开成功响应
            emit('leave_room_response', {
                'ok': True,
                'msg': '已离开房间'
            })
    
    # 选择游戏事件
    @socketio.on('select_game')
    def handle_select_game(data):
        """
        处理选择游戏事件
        
        参数：
        - data: 包含游戏选择信息的字典，必须包含room_id和game_id字段
        
        功能流程：
        1. 验证用户是否已登录
        2. 获取房间ID和游戏ID
        3. 验证房间是否存在
        4. 验证用户是否为房主（只有房主可以选择游戏）
        5. 调用room_manager选择游戏
        6. 选择成功时：
           - 返回成功响应
           - 广播游戏选择更新给房间内所有用户
        7. 选择失败时：
           - 返回失败响应，包含错误信息
        
        事件响应：
        - 成功: 'select_game_response' 和 'game_selected' 事件
        - 失败: 'select_game_response' 事件，包含错误消息
        """
        # 获取当前会话对应的用户账号
        token=data.get('token')
        account = verify_token(token)
        
        # 验证用户是否已登录
        if not account:
            emit('select_game_response', {
                'ok': False,
                'msg': '请先登录'
            })
            return
        
        # 获取房间ID和游戏ID（房间ID由后端通过账号查询得到）
        user_info = get_user(account)
        room_id = user_info.get('room') if user_info else None
        game_id = data.get('game_id')
        
        # 验证房间是否存在
        room = room_manager.get_room(room_id)
        if not room:
            emit('select_game_response', {
                'ok': False,
                'msg': '房间不存在'
            })
            return
        
        # 验证用户是否为房主（只有房主可以选择游戏）
        if not room.is_host(account):
            emit('select_game_response', {
                'ok': False,
                'msg': '只有房主可以选择游戏'
            })
            return
        
        print(f"房主 {account} 在房间 {room_id} 选择游戏: {game_id}")
        
        # 尝试选择游戏
        result = room_manager.select_game(room_id, game_id)
        
        if result:
            print(f"房间 {room_id} 游戏选择成功: {game_id}")
            
            # 返回选择成功响应
            emit('select_game_response', {
                'ok': True,
                'msg': '游戏选择成功'
            })
            
            # 广播游戏选择更新给房间内所有用户
            emit('game_selected', {
                'room_id': room_id,
                'game_id': game_id
            }, room=room_id)
        else:
            print(f"房间 {room_id} 游戏选择失败: {game_id}")
            
            # 选择失败，返回错误信息
            emit('select_game_response', {
                'ok': False,
                'msg': '游戏选择失败'
            })
    
    # 开始游戏事件
    @socketio.on('start_game')
    def handle_start_game(data):
        """
        处理开始游戏事件
        
        参数：
        - data: 包含开始游戏信息的字典，必须包含room_id字段
        
        功能流程：
        1. 验证用户是否已登录
        2. 获取房间ID
        3. 验证房间是否存在
        4. 验证用户是否为房主（只有房主可以开始游戏）
        5. 验证是否已选择游戏
        6. 调用room_manager开始游戏
        7. 开始成功时：
           - 获取初始游戏状态
           - 返回成功响应
           - 广播游戏开始事件，包含游戏状态
        8. 开始失败时：
           - 返回失败响应，包含错误信息
        
        事件响应：
        - 成功: 'start_game_response' 和 'game_started' 事件
        - 失败: 'start_game_response' 事件，包含错误消息
        """
        # 获取当前会话对应的用户账号
        token=data.get('token')
        account = verify_token(token)
        
        print(f"socket:收到用户 {account} 的开始游戏事件: {data}")
        # 验证用户是否已登录
        if not account:
            emit('start_game_response', {
                'ok': False,
                'msg': '请先登录'
            })
            return
        
        # 获取房间ID（通过当前用户信息确定，不再依赖前端传入）
        user_info = get_user(account)
        room_id = user_info.get('room') if user_info else None
        
        # 验证房间是否存在
        room = room_manager.get_room(room_id)
        if not room:
            emit('start_game_response', {
                'ok': False,
                'msg': '房间不存在'
            })
            return
        
        # 验证用户是否为房主（只有房主可以开始游戏）
        if not room.is_host(account):
            emit('start_game_response', {
                'ok': False,
                'msg': '只有房主可以开始游戏'
            })
            return
        
        # 验证是否已选择游戏
        if not room.selected_game:
            emit('start_game_response', {
                'ok': False,
                'msg': '请先选择游戏'
            })
            return
        
        print(f"房主 {account} 请求在房间 {room_id} 开始游戏: {room.selected_game}")
        
        # 尝试开始游戏
        result = room_manager.start_game(room_id)
        
        if result.get('success'):
            # 获取初始游戏状态
            game_state = room_manager.get_game_state(room_id)
            
            print(f"房间 {room_id} 游戏 {room.selected_game} 开始成功")
            
            # 返回开始成功响应
            emit('start_game_response', {
                'ok': True,
                'msg': '游戏开始成功'
            })
            # 广播游戏开始事件，包含游戏状态
            url = result.get('url')
            print(f"socket:游戏开始成功，重定向URL: {url}")
            emit('game_started', {
                'room_id': room_id,
                'game_id': room.selected_game,
                'game_state': game_state,
                'redirect_url': url
            }, room=room_id)
        else:
            print(f"房间 {room_id} 游戏开始失败")
            
            # 开始失败，返回错误信息
            emit('start_game_response', {
                'ok': False,
                'msg': '游戏开始失败'
            })
    
    # 游戏事件转发器
    @socketio.on('game_event')
    def handle_game_event(data):
        """
        转发游戏特定事件
        
        参数：
        - data: 包含游戏事件信息的字典，前端已封装为统一格式：
          {
              "event_name": str,      # 事件名称，如 "place"、"skip_turn" 等
              "event_data": dict      # 事件参数，由具体游戏自己约定
              "account": str          # 发起事件的用户账号
          }
        
        功能流程：
        1. 验证用户是否已登录
        2. 通过 request.sid -> sid_to_account -> get_user(account) 确定房间ID
        3. 直接从 data 读取 event_name 和 event_data
        4. 验证房间是否存在且游戏已开始
        5. 调用 room_manager.handle_game_event(room_id, event_name, account, event_data)
        6. 将处理结果通过 'game_event_result' 返回给发起者
        7. 如果需要广播，获取最新游戏状态并通过 'game_state_updated' 广播给房间内所有用户
        """
        # 获取当前会话对应的用户账号
        token=data.get('token')
        account = verify_token(token)
        
        print(f"socket:收到用户 {account} 的游戏事件: {data}")
        # 验证用户是否已登录
        if not account:
            print(f"socket:用户 {account} 未登录，无法发送游戏事件")   
            emit('game_event_result', {
                'ok': False,
                'msg': '请先登录'
            })
            return
        
        # 通过当前账号获取房间ID
        user_info = get_user(account)
        room_id = user_info.get('room') if user_info else None

        # 从前端传来的数据中直接读取标准事件名称和参数
        event_name = data.get('event_name')

        if not event_name:
            emit('game_event_result', {
                'ok': False,
                'msg': '缺少事件名称 event_name'
            })
            return

        print(f"socket:收到房间 {room_id} 的游戏事件: {event_name}")
        # 验证房间是否存在且游戏已开始
        room = room_manager.get_room(room_id)
        if not room or not room.game_started:
            print(f"socket:房间 {room_id} 游戏未开始，无法处理游戏事件")
            emit('game_event_result', {
                'ok': False,
                'msg': '游戏未开始'
            })
            return
        
        print(f"用户 {account} 在房间 {room_id} 发送游戏事件: {event_name}, data={data}")
        
        # 调用房间管理器处理游戏事件
        result = room_manager.handle_game_event(room_id, account, data)
        # 发送事件响应给发起者（统一事件名为 game_event_result）
        emit('game_event_result', result)
        
        # 如果事件需要广播，获取最新游戏状态并广播给房间内所有用户
        if result.get('broadcast', False):
            game_state = room_manager.get_game_state(room_id)
            emit('game_state_updated', {
                'room_id': room_id,
                'game_state': game_state
            }, room=room_id)
