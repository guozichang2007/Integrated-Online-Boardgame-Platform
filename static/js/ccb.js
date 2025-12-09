// ================================
// main.js
// 登录 / 房间管理 + 游戏主逻辑（与 index.html 配合使用）
// ================================

// 初始化 Socket.IO 客户端，携带token
var token = localStorage.getItem('session_token');
const socket = io({auth: {
        token: token  }});
console.log('main.js loaded, socket.io connected with token');
console.log('Token:', token);
// 平台 & 房间相关全局状态
let currentUser = null;   // 当前用户信息 { account, ID, room, password }
let currentRoom = null;   // 当前所在房间号
let currentGame = null;   // 当前游戏ID
let gameState = null;     // 当前游戏状态

// 游戏相关全局状态
let myOrder = null;       // 玩家在游戏中的编号（暂未使用）
let players = {};         // 当前房间的所有玩家信息
let account = null;       // 当前登录账号（用于在游戏中索引玩家）
let playerID = null;      // 当前玩家ID（显示在游戏中，暂未使用）

// ================================
// DOM 事件绑定（登录 / 房间 / 游戏控制）
// ================================

socket.on('connect', () => {
    console.log('Socket.IO 连接成功！');
    socket.emit('token_reconnect', {token: token});
});

$(document).ready(() => {
    // 跳过回合按钮（游戏操作）
  $('#btnSkip').click(() => {
    // 前端直接封装为游戏内部统一格式：event_name + event_data
    socket.emit('game_event', {
      token: token,
      event_name: 'skip_turn',
      event_data: {}
    });
  });
});

// ================================
// Socket 事件：登录 / 房间 / 平台逻辑
// ================================

// 重连响应
socket.on('reconnect_response', d => {
  if (d.ok && d.game_state) {
    if (d.account){
      account = d.account;
    }
    // 更新游戏状态
    if (d.game_state.players) {
      players = d.game_state.players;
    }
    if (d.game_state.board) {
      renderBoard(d.game_state.board);
    }
    if (d.game_state.turn) {
      renderTurn(d.game_state.turn, d.game_state.players || players);
    }
  }
});



// 开始游戏响应
socket.on('start_game_response', (data) => {
  if (!data.ok) {
    $('#room-message').text(data.msg);
  }
});

// ================================
// 游戏相关事件 & 核心逻辑（棋盘、回合等）
// ================================

// 点击棋盘格子下棋
function onCellClick(e) {
  const y = e.target.dataset.y;
  const x = e.target.dataset.x;

  const pieceType = document.getElementById('selPiece')?.value || 1;
  console.log("click,", x, y, pieceType);
  // 前端直接封装为游戏内部统一格式：event_name + event_data
  socket.emit('game_event', {
    token: token,
    event_name: 'place',
    event_data: {
      ptype: Number(pieceType),
      row: Number(y),
      col: Number(x)
    }
  });
}

// 下棋结果
socket.on('game_event_result', d => {
  const cmdInfo = document.getElementById('cmdInfo');
  if (cmdInfo) {
    cmdInfo.innerText = d.msg || '';
  }
});

// 回合结束
socket.on('turn_ended', d => {
  if (d.turn && d.players) {
    players = d.players;
    renderTurn(d.turn, d.players);
  }
});

// 棋盘更新
socket.on('board_update', d => {
  if (d.players) {
    players = d.players;
    console.log('Updated players:', players);
  }
  if (d.board) {
    renderBoard(d.board);
  }
  if (d.turn && d.players) {
    renderTurn(d.turn, d.players);
  }
});

// 游戏开始广播（整合原 login.js 与 main.js 的处理）
socket.on('game_started', d => {
  console.log('游戏开始:', d);
    
    

  currentRoom = d.room_id || currentRoom;
  currentGame = d.game_id;
  gameState = d.game_state;

  // 切换到游戏界面
  $('#room-panel').hide();
  $('#game').show();
  $('#current-game-name').text('CCB战棋');

  if (d.game_state) {
    if (d.game_state.players) {
      players = d.game_state.players;
    }
    if (d.game_state.board) {
      renderBoard(d.game_state.board);
    }
    if (d.game_state.turn) {
      renderTurn(d.game_state.turn, d.game_state.players || players);
    }
  }
});

// 游戏状态更新（整合原 login.js 与 main.js 的处理）
socket.on('game_state_updated', d => {
  if (d.room_id && currentRoom && d.room_id !== currentRoom) return;

  if (d.game_state) {
    gameState = d.game_state;

    if (d.game_state.players) {
      players = d.game_state.players;
    }
    if (d.game_state.board) {
      renderBoard(d.game_state.board);
    }
    if (d.game_state.turn) {
      renderTurn(d.game_state.turn, d.game_state.players || players);
    }
  }
});

// 渲染棋盘
function renderBoard(board) {
  const tbl = document.getElementById('board');
  if (!tbl) return; // 如果没有找到棋盘元素，直接返回

  tbl.innerHTML = '';

  if (!board || board.length === 0) {
    console.warn('Empty board data received');
    return;
  }

  // 当前玩家的可见范围（若服务器有返回）
  const currentPlayer = players && account ? players[account] : null;
  const visibleRange = currentPlayer ? currentPlayer[7] : null; // 第8个元素是可见范围
  console.log('Visible range for current player:', visibleRange);
  for (let i = 0; i < board.length; i++) {
    const tr = document.createElement('tr');
    for (let j = 0; j < board[i].length; j++) {
      const td = document.createElement('td');
      td.dataset.y = i;
      td.dataset.x = j;

      let cell;
      try {
        cell = Array.isArray(board[i]) && Array.isArray(board[i][j]) ? board[i][j] : [0, 0];
      } catch (e) {
        console.error('Error accessing board cell:', e);
        cell = [0, 0];
      }
      console.log('Rendering cell:', i, j, cell);
      const isVisible = visibleRange && Array.isArray(visibleRange[i]) && visibleRange[i][j] === 1;
      if (!isVisible) {
        // 不可见的格子显示为灰色
        td.innerText = '';
        td.className = 'fog-cell';
        td.style.backgroundColor = 'gray';
      } else {
        const owner = cell[0] || 0;
        const type = cell[1] || 0;

        if (owner ===  -1) {
          td.className = 'not-available-cell';
          console.log('Cell not available:', i, j);
        }
        if (owner !== 0 && owner !== -1) {
          td.className = 'p' + owner; // 根据玩家染色
        }

        switch (type) {
          case 1:
            td.innerText = '步兵';
            break;
          case 2:
            td.innerText = '坦克';
            break;
          case 3:
            td.innerText = '炸机';
            break;
          case 4:
            td.innerText = '战机';
            break;
          case 5:
            td.innerText = '城市';
            td.className = 'pp' + owner;
            break;
          case 6:
            td.innerText = '核井';
            break;
          case 7:
            td.innerText = '指挥';
            break;
          default:
            td.innerText = '';
        }
      }

      td.addEventListener('click', onCellClick);
      tr.appendChild(td);
    }
    tbl.appendChild(tr);
  }
}

// 显示当前回合信息与指挥点
function renderTurn(turn, pls) {
  const info = document.getElementById('turnInfo');
  if (info) {
    info.innerText = `第${turn[1]}轮，轮到 #${turn[0]} 玩家`;
  }
  const cmdInfo = document.getElementById('cmdInfo');
  if (cmdInfo) {
    cmdInfo.innerText = ` 指挥点：${pls && account && pls[account] ? (pls[account][2] || 0) : 0}`;
  }
}
