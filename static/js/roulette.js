// Roulette轮盘赌游戏前端逻辑
const socket = io();
var token = localStorage.getItem('session_token');

// 获取DOM元素
const cardsContainer = document.getElementById('cards-container');
const resetBtn = document.getElementById('resetBtn');
const messageElement = document.getElementById('message');
const statusElement = document.getElementById('status');

// 游戏状态
let gameState = {
    cards: [0, 0, 0, 0, 0, 0],  // 0=未翻开, 1=安全, 2=爆炸
    gameOver: false
};

// 连接状态管理
socket.on('connect', () => {
    console.log('Socket连接成功');
    statusElement.textContent = '连接状态: 已连接';
    statusElement.className = 'status connected';
    messageElement.textContent = '点击卡牌开始游戏！';
});

socket.on('disconnect', () => {
    console.log('Socket连接断开');
    statusElement.textContent = '连接状态: 已断开';
    statusElement.className = 'status disconnected';
    messageElement.textContent = '连接已断开，请刷新页面重新连接...';
});

// 翻牌函数
function flipCard(index) {
    if (gameState.gameOver) {
        messageElement.textContent = '游戏已结束，请点击重置按钮重新开始！';
        return;
    }
    
    if (gameState.cards[index] !== 0) {
        messageElement.textContent = '该卡牌已经翻开！';
        return;
    }
    
    // 发送翻牌事件到后端
    const eventData = {
        token: token,
        event_name: 'flip_card',
        event_data: {
            index: index
        }
    };
    
    console.log('发送翻牌事件:', eventData);
    socket.emit('game_event', eventData);
}

// 重置游戏
function resetGame() {
    const eventData = {
        token: token,
        event_name: 'reset',
        event_data: {}
    };
    
    console.log('发送重置事件:', eventData);
    socket.emit('game_event', eventData);
}

// 监听游戏事件结果
socket.on('game_event_result', (response) => {
    console.log('收到游戏事件结果:', response);
    
    if (response.ok) {
        messageElement.textContent = response.msg;
        
        if (response.cards_state) {
            gameState.cards = response.cards_state;
            gameState.gameOver = response.game_over || false;
            renderCards();
        }
    } else {
        messageElement.textContent = `错误: ${response.msg}`;
    }
});

// 渲染卡牌
function renderCards() {
    cardsContainer.innerHTML = '';
    
    gameState.cards.forEach((cardState, index) => {
        const card = document.createElement('div');
        card.className = 'card';
        
        if (cardState === 0) {
            // 未翻开
            card.classList.add('hidden');
            card.textContent = '?';
            card.onclick = () => flipCard(index);
        } else if (cardState === 1) {
            // 安全
            card.classList.add('safe');
            card.textContent = '✓';
        } else if (cardState === 2) {
            // 爆炸
            card.classList.add('bomb');
            card.textContent = '💥';
        }
        
        cardsContainer.appendChild(card);
    });
}

// 重置按钮事件
resetBtn.addEventListener('click', resetGame);

// 页面加载完成后初始化
window.addEventListener('load', () => {
    renderCards();
});
