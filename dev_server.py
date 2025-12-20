"""
开发者测试平台 - 完全独立于游戏的测试服务器
与主平台拥有相同的接口，但提供自动化测试功能
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key_for_testing'
socketio = SocketIO(app, cors_allowed_origins="*")

# 数据存储
DEV_USERS_FILE = 'dev_users.json'
dev_users = {}
dev_tokens = {}
dev_rooms = {}
dev_games = {}

# ============================================================
# 游戏注册 - 复用主平台的游戏模块
# ============================================================
from my_modules.games.game_registry import game_registry
game_registry.initialize()

# ============================================================
# 用户管理
# ============================================================
def load_dev_users():
    global dev_users
    if os.path.exists(DEV_USERS_FILE):
        with open(DEV_USERS_FILE, 'r', encoding='utf-8') as f:
            dev_users = json.load(f)
    else:
        # 创建默认测试用户
        dev_users = {
            'dev_user1': {
                'account': 'dev_user1',
                'ID': '测试用户1',
                'password': generate_password_hash('123456'),
                'room': None
            },
            'dev_user2': {
                'account': 'dev_user2', 
                'ID': '测试用户2',
                'password': generate_password_hash('123456'),
                'room': None
            }
        }
        save_dev_users()

def save_dev_users():
    with open(DEV_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dev_users, f, ensure_ascii=False, indent=2)

def create_token(account):
    token = secrets.token_urlsafe(32)
    dev_tokens[token] = account
    return token

def get_account_by_token(token):
    return dev_tokens.get(token)

def update_user_room(account, room_id):
    if account in dev_users:
        dev_users[account]['room'] = room_id
        save_dev_users()

# ============================================================
# HTTP路由
# ============================================================
@app.route('/')
def index():
    """开发者平台主页"""
    return render_template('dev_platform.html', games=game_registry)

@app.route('/api/login', methods=['POST'])
def api_login():
    """登录API"""
    data = request.get_json()
    account = data.get('account')
    password = data.get('password')
    
    if account not in dev_users:
        return jsonify({'ok': False, 'msg': '用户不存在'})
    
    user = dev_users[account]
    if not check_password_hash(user['password'], password):
        return jsonify({'ok': False, 'msg': '密码错误'})
    
    token = create_token(account)
    return jsonify({
        'ok': True, 
        'token': token,
        'account': account,
        'ID': user['ID']
    })

@app.route('/api/auto_login', methods=['POST'])
def api_auto_login():
    """自动登录（开发模式专用）"""
    data = request.get_json()
    account = data.get('account', 'dev_user1')
    
    # 如果用户不存在，自动创建
    if account not in dev_users:
        dev_users[account] = {
            'account': account,
            'ID': f'测试用户_{account}',
            'password': generate_password_hash('123456'),
            'room': None
        }
        save_dev_users()
    
    # 清除用户的房间状态
    dev_users[account]['room'] = None
    save_dev_users()
    
    token = create_token(account)
    return jsonify({
        'ok': True,
        'token': token,
        'account': account,
        'ID': dev_users[account]['ID']
    })

@app.route('/api/games')
def api_games():
    """获取游戏列表"""
    games_list = []
    for game_id, game_info in game_registry.games.items():
        games_list.append({
            'id': game_id,
            'name': game_info['name'],
            'description': game_info['description'],
            'min_players': game_info['min_players'],
            'max_players': game_info['max_players'],
            'url': game_info['url']
        })
    return jsonify({'ok': True, 'games': games_list})

# 游戏页面路由 - 复用原有模板
@app.route('/ccb')
def ccb_game():
    return render_template('ccb.html')

@app.route('/roulette')
def roulette_game():
    return render_template('roulette.html')

@app.route('/stew')
def stew_game():
    return render_template('stew.html')

# ============================================================
# Socket.IO 事件处理 - 与主平台相同的接口
# ============================================================
@socketio.on('connect')
def handle_connect():
    print(f'[DEV] 客户端连接: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'[DEV] 客户端断开: {request.sid}')

@socketio.on('token_connect')
def handle_token_connect(data):
    """通过token连接"""
    token = data.get('token')
    account = get_account_by_token(token)
    
    if account:
        print(f'[DEV] 用户 {account} 通过token连接')
        emit('token_connect_response', {'ok': True, 'account': account})
    else:
        emit('token_connect_response', {'ok': False, 'msg': 'Token无效'})

@socketio.on('token_reconnect')
def handle_token_reconnect(data):
    """重新连接"""
    token = data.get('token')
    account = get_account_by_token(token)
    
    if not account:
        emit('reconnect_response', {'ok': False, 'msg': 'Token无效'})
        return
    
    user = dev_users.get(account)
    room_id = user.get('room') if user else None
    game_state = None
    
    if room_id and room_id in dev_rooms:
        room = dev_rooms[room_id]
        join_room(room_id)
        if room.get('game_instance'):
            game_state = room['game_instance'].get_state(account)
    
    emit('reconnect_response', {
        'ok': True,
        'account': account,
        'ID': user.get('ID', account),
        'room_id': room_id,
        'game_state': game_state
    })

@socketio.on('create_room')
def handle_create_room(data):
    """创建房间"""
    token = data.get('token')
    room_id = data.get('room_id')
    account = get_account_by_token(token)
    
    if not account:
        emit('create_room_response', {'ok': False, 'msg': 'Token无效'})
        return
    
    if not room_id:
        room_id = f'dev_room_{secrets.token_hex(4)}'
    
    if room_id in dev_rooms:
        emit('create_room_response', {'ok': False, 'msg': '房间已存在'})
        return
    
    # 创建房间
    dev_rooms[room_id] = {
        'id': room_id,
        'owner': account,
        'players': [account],
        'game_id': None,
        'game_instance': None,
        'started': False
    }
    
    # 更新用户房间
    update_user_room(account, room_id)
    join_room(room_id)
    
    print(f'[DEV] 用户 {account} 创建房间 {room_id}')
    emit('create_room_response', {'ok': True, 'room_id': room_id})

@socketio.on('join_room')
def handle_join_room(data):
    """加入房间"""
    token = data.get('token')
    room_id = data.get('room_id')
    account = get_account_by_token(token)
    
    if not account:
        emit('join_room_response', {'ok': False, 'msg': 'Token无效'})
        return
    
    if room_id not in dev_rooms:
        emit('join_room_response', {'ok': False, 'msg': '房间不存在'})
        return
    
    room = dev_rooms[room_id]
    if account not in room['players']:
        room['players'].append(account)
    
    update_user_room(account, room_id)
    join_room(room_id)
    
    print(f'[DEV] 用户 {account} 加入房间 {room_id}')
    emit('join_room_response', {'ok': True, 'room_id': room_id})
    
    # 通知房间内所有人
    socketio.emit('room_update', {
        'players': room['players'],
        'game_id': room['game_id']
    }, room=room_id)

@socketio.on('select_game')
def handle_select_game(data):
    """选择游戏"""
    token = data.get('token')
    game_id = data.get('game_id')
    account = get_account_by_token(token)
    
    if not account:
        emit('select_game_response', {'ok': False, 'msg': 'Token无效'})
        return
    
    user = dev_users.get(account)
    room_id = user.get('room') if user else None
    
    if not room_id or room_id not in dev_rooms:
        emit('select_game_response', {'ok': False, 'msg': '不在房间中'})
        return
    
    if game_id not in game_registry.games:
        emit('select_game_response', {'ok': False, 'msg': '游戏不存在'})
        return
    
    room = dev_rooms[room_id]
    room['game_id'] = game_id
    
    print(f'[DEV] 房间 {room_id} 选择游戏 {game_id}')
    emit('select_game_response', {'ok': True, 'game_id': game_id})
    
    # 通知房间
    socketio.emit('room_update', {
        'players': room['players'],
        'game_id': room['game_id']
    }, room=room_id)

@socketio.on('start_game')
def handle_start_game(data):
    """开始游戏"""
    token = data.get('token')
    account = get_account_by_token(token)
    
    if not account:
        emit('start_game_response', {'ok': False, 'msg': 'Token无效'})
        return
    
    user = dev_users.get(account)
    room_id = user.get('room') if user else None
    
    if not room_id or room_id not in dev_rooms:
        emit('start_game_response', {'ok': False, 'msg': '不在房间中'})
        return
    
    room = dev_rooms[room_id]
    game_id = room.get('game_id')
    
    if not game_id:
        emit('start_game_response', {'ok': False, 'msg': '未选择游戏'})
        return
    
    game_info = game_registry.games[game_id]
    game_class = game_info['class']
    
    # 创建游戏实例
    try:
        game_instance = game_class(room_id)
        room['game_instance'] = game_instance
        room['started'] = True
        
        for i in room['players']:
            game_instance.join(i)
            print(f'[DEV] 房间 {room_id} 玩家 {i} 加入游戏 {game_id}')

    
        game_instance.start()
        print(f'[DEV] 房间 {room_id} 开始游戏 {game_id}')
        
        # 通知所有玩家
        for player in room['players']:
            # 获取玩家状态（兼容不同游戏接口）
            player_state = None
            if hasattr(game_instance, 'get_state'):
                player_state = game_instance.get_state(player)
            elif hasattr(game_instance, 'get_state'):
                player_state = game_instance.get_state()
            
            socketio.emit('game_started', {
                'ok': True,
                'game_id': game_id,
                'game_url': game_info['url'],
                'state': player_state
            }, room=room_id)
        
        emit('start_game_response', {'ok': True, 'game_url': game_info['url']})
        
    except Exception as e:
        print(f'[DEV] 创建游戏失败: {e}')
        emit('start_game_response', {'ok': False, 'msg': str(e)})

@socketio.on('game_event')
def handle_game_event(data):
    """处理游戏事件"""
    token = data.get('token')
    account = get_account_by_token(token)
    
    if not account:
        emit('game_event_result', {'ok': False, 'msg': 'Token无效'})
        return
    
    user = dev_users.get(account)
    room_id = user.get('room') if user else None
    
    if not room_id or room_id not in dev_rooms:
        emit('game_event_result', {'ok': False, 'msg': '不在房间中'})
        return
    
    room = dev_rooms[room_id]
    game_instance = room.get('game_instance')
    
    if not game_instance:
        emit('game_event_result', {'ok': False, 'msg': '游戏未开始'})
        return
    
    # 处理游戏事件
    try:
        result = game_instance.handle_event(account,data)
        
        # 广播结果给房间内所有玩家
        for player in room['players']:
            player_state = game_instance.get_state(player)
            socketio.emit('game_state_update', {
                'state': player_state
            }, room=room_id)
        
        emit('game_event_result', result)
        
    except Exception as e:
        print(f'[DEV] 游戏事件处理失败: {e}')
        emit('game_event_result', {'ok': False, 'msg': str(e)})

@socketio.on('leave_room')
def handle_leave_room(data):
    """离开房间"""
    token = data.get('token')
    account = get_account_by_token(token)
    
    if not account:
        emit('leave_room_response', {'ok': False, 'msg': 'Token无效'})
        return
    
    user = dev_users.get(account)
    room_id = user.get('room') if user else None
    
    if room_id and room_id in dev_rooms:
        room = dev_rooms[room_id]
        if account in room['players']:
            room['players'].remove(account)
        leave_room(room_id)
        
        # 如果房间空了，删除房间
        if not room['players']:
            del dev_rooms[room_id]
    
    update_user_room(account, None)
    emit('leave_room_response', {'ok': True})

# ============================================================
# 启动服务器
# ============================================================
if __name__ == '__main__':
    load_dev_users()
    print('=' * 60)
    print('开发者测试平台启动中...')
    print(f'游戏数量: {len(game_registry.games)}')
    print('访问地址: http://127.0.0.1:5001')
    print('=' * 60)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
