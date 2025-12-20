/**
 * 开发者测试平台 - 前端逻辑
 * 完全独立于游戏，提供自动化测试功能
 */

// ============================================================
// 状态管理
// ============================================================
const state = {
    socket: null,
    token: null,
    account: null,
    roomId: null,
    selectedGameId: null,
    selectedGameUrl: null,
    games: []
};

// ============================================================
// DOM元素
// ============================================================
const elements = {
    connStatus: document.getElementById('connStatus'),
    loginStatus: document.getElementById('loginStatus'),
    currentUser: document.getElementById('currentUser'),
    roomStatus: document.getElementById('roomStatus'),
    gameStatus: document.getElementById('gameStatus'),
    username: document.getElementById('username'),
    autoLoginBtn: document.getElementById('autoLoginBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    gamesGrid: document.getElementById('gamesGrid'),
    createRoomBtn: document.getElementById('createRoomBtn'),
    startGameBtn: document.getElementById('startGameBtn'),
    leaveRoomBtn: document.getElementById('leaveRoomBtn'),
    quickStartBtn: document.getElementById('quickStartBtn'),
    logPanel: document.getElementById('logPanel')
};

// ============================================================
// 日志功能
// ============================================================
function log(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;
    elements.logPanel.appendChild(entry);
    elements.logPanel.scrollTop = elements.logPanel.scrollHeight;
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// ============================================================
// 状态更新
// ============================================================
function updateStatus() {
    // 连接状态
    if (state.socket && state.socket.connected) {
        elements.connStatus.textContent = '已连接';
        elements.connStatus.className = 'status-value success';
    } else {
        elements.connStatus.textContent = '未连接';
        elements.connStatus.className = 'status-value error';
    }
    
    // 登录状态
    if (state.token && state.account) {
        elements.loginStatus.textContent = '已登录';
        elements.loginStatus.className = 'status-value success';
        elements.currentUser.textContent = state.account;
    } else {
        elements.loginStatus.textContent = '未登录';
        elements.loginStatus.className = 'status-value error';
        elements.currentUser.textContent = '-';
    }
    
    // 房间状态
    elements.roomStatus.textContent = state.roomId || '-';
    
    // 游戏状态
    elements.gameStatus.textContent = state.selectedGameId || '-';
    
    // 按钮状态
    const isLoggedIn = !!state.token;
    const hasRoom = !!state.roomId;
    const hasGame = !!state.selectedGameId;
    
    elements.createRoomBtn.disabled = !isLoggedIn || hasRoom;
    elements.startGameBtn.disabled = !hasRoom || !hasGame;
    elements.leaveRoomBtn.disabled = !hasRoom;
    elements.quickStartBtn.disabled = !isLoggedIn || !hasGame;
}

// ============================================================
// Socket.IO 连接
// ============================================================
function initSocket() {
    state.socket = io();
    
    state.socket.on('connect', () => {
        log('Socket连接成功', 'success');
        updateStatus();
    });
    
    state.socket.on('disconnect', () => {
        log('Socket连接断开', 'error');
        updateStatus();
    });
    
    state.socket.on('create_room_response', (data) => {
        if (data.ok) {
            state.roomId = data.room_id;
            log(`房间创建成功: ${data.room_id}`, 'success');
        } else {
            log(`房间创建失败: ${data.msg}`, 'error');
        }
        updateStatus();
    });
    
    state.socket.on('select_game_response', (data) => {
        if (data.ok) {
            log(`游戏选择成功: ${data.game_id}`, 'success');
        } else {
            log(`游戏选择失败: ${data.msg}`, 'error');
        }
        updateStatus();
    });
    
    state.socket.on('start_game_response', (data) => {
        if (data.ok) {
            log(`游戏启动成功，正在跳转...`, 'success');
            // 保存token到localStorage供游戏页面使用
            localStorage.setItem('session_token', state.token);
            // 跳转到游戏页面
            setTimeout(() => {
                window.location.href = data.game_url;
            }, 500);
        } else {
            log(`游戏启动失败: ${data.msg}`, 'error');
        }
    });
    
    state.socket.on('leave_room_response', (data) => {
        if (data.ok) {
            state.roomId = null;
            log('已离开房间', 'success');
        }
        updateStatus();
    });
    
    state.socket.on('game_started', (data) => {
        log(`收到游戏开始事件`, 'info');
    });
    
    state.socket.on('room_update', (data) => {
        log(`房间更新: 玩家=${data.players?.join(', ')}, 游戏=${data.game_id || '未选择'}`, 'info');
    });
}

// ============================================================
// API调用
// ============================================================
async function autoLogin() {
    const username = elements.username.value.trim() || 'dev_user1';
    log(`正在自动登录: ${username}...`, 'info');
    
    try {
        const response = await fetch('/api/auto_login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account: username })
        });
        
        const data = await response.json();
        
        if (data.ok) {
            state.token = data.token;
            state.account = data.account;
            localStorage.setItem('session_token', state.token);
            log(`登录成功: ${data.account} (${data.ID})`, 'success');
            
            // 通过socket发送token连接
            state.socket.emit('token_connect', { token: state.token });
        } else {
            log(`登录失败: ${data.msg}`, 'error');
        }
    } catch (e) {
        log(`登录异常: ${e.message}`, 'error');
    }
    
    updateStatus();
}

async function loadGames() {
    try {
        const response = await fetch('/api/games');
        const data = await response.json();
        
        if (data.ok) {
            state.games = data.games;
            renderGames();
            log(`加载了 ${data.games.length} 个游戏`, 'success');
        }
    } catch (e) {
        log(`加载游戏列表失败: ${e.message}`, 'error');
    }
}

// ============================================================
// 渲染游戏列表
// ============================================================
function renderGames() {
    elements.gamesGrid.innerHTML = '';
    
    state.games.forEach(game => {
        const card = document.createElement('div');
        card.className = 'game-card';
        if (state.selectedGameId === game.id) {
            card.classList.add('selected');
        }
        
        card.innerHTML = `
            <h3>${game.name}</h3>
            <p>${game.description}</p>
            <div class="players-info">玩家数: ${game.min_players}-${game.max_players}</div>
        `;
        
        card.onclick = () => selectGame(game);
        elements.gamesGrid.appendChild(card);
    });
}

function selectGame(game) {
    state.selectedGameId = game.id;
    state.selectedGameUrl = game.url;
    log(`选择游戏: ${game.name}`, 'info');
    renderGames();
    updateStatus();
    
    // 如果已在房间中，发送选择游戏事件
    if (state.roomId && state.token) {
        state.socket.emit('select_game', {
            token: state.token,
            game_id: game.id
        });
    }
}

// ============================================================
// 房间操作
// ============================================================
function createRoom() {
    if (!state.token) {
        log('请先登录', 'warn');
        return;
    }
    
    const roomId = 'dev_' + Date.now().toString(36);
    log(`创建房间: ${roomId}...`, 'info');
    
    state.socket.emit('create_room', {
        token: state.token,
        room_id: roomId
    });
}

function startGame() {
    if (!state.roomId || !state.selectedGameId) {
        log('请先创建房间并选择游戏', 'warn');
        return;
    }
    
    log('启动游戏...', 'info');
    state.socket.emit('start_game', { token: state.token });
}

function leaveRoom() {
    if (!state.roomId) return;
    
    log('离开房间...', 'info');
    state.socket.emit('leave_room', { token: state.token });
}

// ============================================================
// 一键启动
// ============================================================
async function quickStart() {
    if (!state.selectedGameId) {
        log('请先选择一个游戏', 'warn');
        return;
    }
    
    log('🚀 开始一键启动流程...', 'info');
    
    // 1. 自动登录
    if (!state.token) {
        await autoLogin();
        await new Promise(r => setTimeout(r, 300));
    }
    
    // 2. 创建房间
    if (!state.roomId) {
        createRoom();
        await new Promise(r => setTimeout(r, 500));
    }
    
    // 3. 选择游戏
    state.socket.emit('select_game', {
        token: state.token,
        game_id: state.selectedGameId
    });
    await new Promise(r => setTimeout(r, 300));
    
    // 4. 启动游戏
    startGame();
}

function logout() {
    state.token = null;
    state.account = null;
    state.roomId = null;
    localStorage.removeItem('session_token');
    log('已登出', 'info');
    updateStatus();
}

// ============================================================
// 事件绑定
// ============================================================
elements.autoLoginBtn.onclick = autoLogin;
elements.logoutBtn.onclick = logout;
elements.createRoomBtn.onclick = createRoom;
elements.startGameBtn.onclick = startGame;
elements.leaveRoomBtn.onclick = leaveRoom;
elements.quickStartBtn.onclick = quickStart;

// ============================================================
// 初始化
// ============================================================
window.addEventListener('load', () => {
    initSocket();
    loadGames();
    updateStatus();
    log('开发者测试平台已就绪', 'success');
});
