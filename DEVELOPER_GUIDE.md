# 🎲 桌游平台开发者指南

欢迎来到桌游平台开发指南！本文档将指导你如何开 发一个新的游戏模块并将其集成到平台中。

## 📑 目录

1. [快速开始](#1-快速开始)
2. [后端开发指南](#2-后端开发指南)
3. [前端开发指南](#3-前端开发指南)
4. [通讯协议详解](#4-通讯协议详解)
5. [完整示例](#5-完整示例)
6. [部署检查清单](#6-部署检查清单)

---

## 1. 快速开始

开发一个新的游戏需要完成以下三个部分：

1. **后端逻辑**：在 `my_modules/games/` 下创建一个新的游戏包
2. **前端页面**：在 `templates/` 下创建游戏的HTML页面
3. **前端脚本**：在 `static/js/` 下创建游戏的JS逻辑

### 目录结构要求

假设你要开发一个名为 `my_game` 的游戏：

```
Integrated-Online-Boardgame-Platform/
├── my_modules/
│   └── games/
│       └── my_game/           # 你的游戏包目录
│           ├── __init__.py    # 必须包含
│           └── game.py        # 游戏核心逻辑
├── templates/
│   └── my_game.html          # 游戏页面模板
└── static/
    └── js/
        └── my_game.js        # 游戏前端逻辑
```

---

## 2. 后端开发指南

### 2.1 创建游戏类

在 `my_modules/games/my_game/game.py` 中，你需要创建一个继承自 `BaseGame` 的类。

**基础模版：**

```python
from my_modules.games.base import BaseGame

class MyGame(BaseGame):
    def __init__(self, room_id):
        super().__init__(room_id)
        # 初始化游戏状态
        self.game_state = {} 
    
    def join(self, account, player_id):
        """玩家加入游戏"""
        # 实现加入逻辑
        pass
        
    def start(self):
        """开始游戏"""
        self.started = True
        return True
    
    def handle_event(self, account, data):
        """核心：处理前端发来的事件"""
        event_name = data.get('event_name')
        
        if event_name == 'my_action':
            # 处理具体动作
            return {
                'ok': True,
                'msg': '操作成功',
                'broadcast': True  # 是否广播给房间内所有人
            }
            
        return {'ok': False, 'msg': '未知事件'}
        
    def get_state(self,account):
        """返回完整游戏状态"""
        return {
            'players': self.players,
            'state': self.game_state
        }
```

### 2.2 注册游戏

在同一个 `game.py` 文件的末尾，必须定义一个 `register_game` 函数：

```python
def register_game():
    return {
        'id': 'my_game',           # 唯一标识符
        'name': '我的超级游戏',      # 显示名称
        'description': '游戏简介',  # 描述
        'min_players': 1,          # 最小玩家数
        'max_players': 4,          # 最大玩家数
        'class': MyGame,           # 游戏类引用
        'url': '/my_game'          # 前端页面路由
    }
```

---

## 3. 前端开发指南

### 3.1 HTML 模板

在 `templates/my_game.html` 中：

```html
<!DOCTYPE html>
<html>
<head>
    <title>我的游戏</title>
</head>
<body>
    <div id="game-container"></div>
    
    <!-- 引入Socket.IO -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <!-- 引入你的游戏脚本 -->
    <script src="{{ url_for('static', filename='js/my_game.js') }}"></script>
</body>
</html>
```

### 3.2 JS 逻辑

在 `static/js/my_game.js` 中：

**重要：前端必须在Socket连接时传递token，并在连接成功后发送`token_reconnect`以获取游戏状态。**

```javascript
// 重要：获取token并在连接时传递
var token = localStorage.getItem('session_token');
const socket = io({
    auth: {
        token: token
    }
});

// Socket连接成功后，发送token_reconnect以获取游戏状态
socket.on('connect', () => {
    console.log('Socket.IO 连接成功！');
    socket.emit('token_reconnect', {token: token});
});

// 监听重连响应，接收游戏状态
socket.on('reconnect_response', (data) => {
    if (data.ok && data.game_state) {
        // 使用返回的游戏状态初始化UI
        updateUI(data.game_state);
    }
});

// 1. 发送事件
function doAction() {
    socket.emit('game_event', {
        token: token,
        event_name: 'my_action',
        event_data: { key: 'value' }
    });
}

// 2. 接收结果（针对发送者）
socket.on('game_event_result', (response) => {
    if (response.ok) {
        console.log('操作成功:', response.msg);
    } else {
        alert(response.msg);
    }
});

// 3. 接收状态更新广播（针对所有人）
socket.on('game_state_updated', (data) => {
    const gameState = data.game_state;
    // 根据新状态更新UI
    updateUI(gameState);
});
```

---

## 4. 通讯协议详解

平台使用 Socket.IO 进行实时通讯。所有的游戏交互都通过 `game_event` 通道进行。

### 4.1 前端发送格式

```javascript
{
    "token": "用户session_token",  // 必填
    "event_name": "事件名称",      // 必填，后端根据此字段分发
    "event_data": {               // 选填，具体业务数据
        "x": 1,
        "y": 2
    }
}
```

### 4.2 后端返回格式

后端 `handle_event` 方法的返回值将直接发送回前端：

```python
{
    'ok': True,             # 操作是否成功
    'msg': '提示信息',       # 用户提示
    'broadcast': True,      # 特殊字段：若为True，平台会自动触发 game_state_updated 广播
    'custom_data': ...      # 其他自定义返回数据
}
```

### 4.3 核心Socket事件列表

| 事件名 | 方向 | 描述 |
|--------|------|------|
| `game_event` | 前端 -> 后端 | 发送游戏操作 |
| `game_event_result` | 后端 -> 前端 | 操作的直接反馈（仅发送者收到） |
| `game_state_updated` | 后端 -> 前端 | 游戏状态更新广播（房间内所有人收到） |
| `reconnect_response` | 后端 -> 前端 | 断线重连后的状态同步 |

---

## 5. 完整示例

这是一个最简单的"猜数字"游戏示例：

### 后端 (game.py)
```python
import random
from my_modules.games.base import BaseGame

class GuessNumberGame(BaseGame):
    def __init__(self, room_id):
        super().__init__(room_id)
        self.target = random.randint(1, 100)
    
    def start(self):
        self.started = True
        return True
        
    def handle_event(self, account, data):
        if data['event_name'] == 'guess':
            guess = int(data['event_data']['number'])
            if guess == self.target:
                return {'ok': True, 'msg': '猜对了！', 'broadcast': True, 'winner': account}
            elif guess < self.target:
                return {'ok': True, 'msg': '太小了', 'broadcast': False}
            else:
                return {'ok': True, 'msg': '太大了', 'broadcast': False}
                
    def get_state(self):
        return {'started': self.started}

def register_game():
    return {
        'id': 'guess_number',
        'name': '猜数字',
        'description': '经典猜数字游戏',
        'min_players': 1,
        'max_players': 10,
        'class': GuessNumberGame,
        'url': '/guess'
    }
```

---

## 6. 部署检查清单

在提交你的游戏之前，请检查：

- [ ] **文件位置**：后端文件是否在 `my_modules/games/你的游戏/` 下？
- [ ] **注册函数**：`game.py` 中是否包含 `register_game()` 函数？
- [ ] **路由配置**：是否在 `app.py` 中添加了对应的页面路由？
  ```python
  @app.route('/你的游戏url')
  def your_game():
      return render_template('你的游戏模板.html')
  ```
- [ ] **静态资源**：JS/CSS 文件是否引用正确？
- [ ] **依赖包**：如果使用了额外的Python包，请在 `requirements.txt` 中添加。

祝开发愉快！🚀
