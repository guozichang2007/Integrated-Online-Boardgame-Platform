const socket = io();
let gameState = null;
let myAccount = null;
let isCallingStewMode = false;

// Card Definitions for display
const CARD_DEFS = {
    1: { name: '鸡肉', icon: '🐔', points: 5, color: '#ffec8b' },
    2: { name: '石头', icon: '🪨', points: -3, color: '#888' },
    3: { name: '胡萝卜', icon: '🥕', points: 2, color: '#ffa500' },
    4: { name: '韭葱', icon: '🥬', points: 3, color: '#90ee90' },
    5: { name: '大蒜', icon: '🧄', points: 6, color: '#fffacd' },
    6: { name: '土豆', icon: '🥔', points: '?', color: '#d2b48c' }
};

const ANIMAL_DEFS = {
    'boar': { icon: '🐗', desc: '吃1个大蒜' },
    'fox': { icon: '🦊', desc: '吃鸡肉' },
    'gopher': { icon: '🦦', desc: '吃1个韭葱' }, // Gopher emoji approximation
    'rabbit': { icon: '🐰', desc: '吃1个胡萝卜' },
    'raccoon': { icon: '🦝', desc: '吃1个土豆' },
    'vagabond': { icon: '🧙‍♂️', desc: '无鸡肉+3分, 有鸡肉-3分' }
};

$(document).ready(function() {
    // Login check
    var token = localStorage.getItem('session_token');


    
    // Connect (Reconnect to restore state)
    socket.emit('token_reconnect', {
        token: token
    });
    console.log(token)
    // Events
    socket.on('reconnect_response', function(data) {
        console.log('Reconnect Response:', data);
        if (data.ok) {
            if (data.game_state) {
                gameState = data.game_state;
                renderGame();
                checkAndRequestHand();
            }
        } else {
            console.error('Reconnect failed:', data.msg);
        }
    });

    socket.on('game_state_updated', function(data) {
        console.log('Game State Updated:', data);
        if (data.game_state) {
            gameState = data.game_state;
            renderGame();
            checkAndRequestHand();
        }
    });

    socket.on('game_event_result', function(data) {
        console.log('Game Event Result:', data);
        if (data.ok) {
            if (data.my_card !== undefined) {
                gameState.my_card = data.my_card;
                renderGame();
            }
        }
        if (data.msg) showMessage(data.msg);
    });

    socket.on('game_msg', function(data) {
        showMessage(data.msg);
    });

    // Bind Controls
    $('#btn-draw').click(function() {
        socket.emit('game_event', { event_name: 'draw' ,token: token});
    });

    $('#btn-call-stew').click(function() {
        if (gameState.phase === 'player_turn' && gameState.current_player_account === myAccount) {
            // Toggle Call Stew Mode
            isCallingStewMode = !isCallingStewMode;
            updateControls();
            if (isCallingStewMode) {
                showMessage("请选择把手牌打出的位置（锅或动物）以触发炖菜！");
            } else {
                showMessage("取消喊炖菜模式");
            }
        } else {
            // Direct call
            if (confirm("确定要现在喊炖菜吗？")) {
                socket.emit('game_event', { event_name: 'call_stew',token: token });
            }
        }
    });

    $('#pot-area').click(function() {
        handlePlayCard('pot');
    });

    $('#btn-reset').click(function() {
        if (confirm("确定要重置游戏吗？")) {
            socket.emit('game_event', { event_name: 'reset_game' ,token: token});
        }
    });

});

function checkAndRequestHand() {
    if (!gameState) return;
    if (gameState.current_player_account === myAccount) {
        if (!gameState.my_card && gameState.phase === 'player_turn') {
             socket.emit('game_event', { event_name: 'get_hand' ,token: token});
        }
    }
}

function handlePlayCard(actionType, animalIndex = null) {
    if (!gameState) return;
    if (gameState.phase !== 'player_turn') return;
    if (gameState.current_player_account !== myAccount) return;

    const eventName = isCallingStewMode ? 'call_stew' : 'action';
    
    socket.emit('game_event', {
        event_name: eventName,
        action_type: actionType,
        animal_index: animalIndex,
        token: token
    });
    
    isCallingStewMode = false;
    updateControls();
}

function renderGame() {
    if (!gameState) return;

    // Update Status Msg
    // Find current player in the array
    const currentPlayerObj = gameState.players.find(p => p.account === gameState.current_player_account);
    const currentPlayerName = currentPlayerObj?.account || '未知';
    let statusText = '';
    
    if (gameState.game_over) {
        statusText = "游戏结束！";
        // Show winner in modal if not shown
    } else {
        if (gameState.phase === 'waiting_for_draw') {
            statusText = `等待 ${currentPlayerName} 抽牌...`;
        } else if (gameState.phase === 'player_turn') {
            statusText = `${currentPlayerName} 正在出牌...`;
        }
    }
    $('#status-msg').text(statusText);

    // Update Animals
    $('#animals-container').empty();
    gameState.animals.forEach((animal, index) => {
        const def = ANIMAL_DEFS[animal.id];
        const isFed = animal.fed;
        const div = $('<div>').addClass('animal-card');
        if (isFed) div.addClass('fed');
        
        div.html(`
            <div class="animal-icon">${def.icon}</div>
            <div class="animal-name">${def.desc}</div>
            <div class="animal-desc">${animal.name}</div>
        `);
        
        div.click(function() {
            handlePlayCard('feed', index);
        });
        
        $('#animals-container').append(div);
    });

    // Update Pot
    $('#pot-count').text(`锅里: ${gameState.pot_count}`);

    // Update Hand
    $('#my-card-area').empty();
    if (gameState.my_card) {
        const cardInfo = CARD_DEFS[gameState.my_card];
        const cardDiv = $('<div>').addClass('card')
            .css('border-color', cardInfo.color)
            .html(`
                <div class="card-icon">${cardInfo.icon}</div>
                <div class="card-name">${cardInfo.name}</div>
                <div class="card-points">${cardInfo.points} 分</div>
            `);
        $('#my-card-area').append(cardDiv);
    }

    // Update Scoreboard
    $('#scores-list').empty();
    gameState.players.forEach(player => {
        const account = player.account;
        const score = gameState.scores[account] || 0;
        const isActive = (account === gameState.current_player_account);
        const row = $('<div>').addClass('player-score')
            .toggleClass('active', isActive)
            .html(`<span>${account}</span> <span>${score} 分</span>`);
        $('#scores-list').append(row);
    });

    // Show Result Modal if result exists
    if (gameState.last_result) {
        showResultModal(gameState.last_result);
        // Clear result after showing so it doesn't pop up again on refresh? 
        // Ideally backend handles this, or we just show it. 
        // For now, we show it. 
    }

    // Update Host Controls
    // Check if current user is the first player (host)
    if (gameState.players.length > 0 && myAccount === gameState.players[0].account) {
        $('#btn-reset').show();
    }

    updateControls();
}

function updateControls() {
    if (!gameState) return;
    
    const isMyTurn = (gameState.current_player_account === myAccount);
    const hasCard = !!gameState.my_card;
    
    // Draw Button
    $('#btn-draw').prop('disabled', !(isMyTurn && gameState.phase === 'waiting_for_draw'));
    
    // Call Stew Button
    // Enable if:
    // 1. My Turn + Has Card (Player Turn)
    // 2. NOT My Turn + Phase is Waiting For Draw (Out of turn call)
    // 3. My Turn + Waiting For Draw (Before Draw - Rare/Impossible if logic holds, actually rules say "After another player's turn ends", so before I draw I can call stew without card? Rules say "1. Turn... finish taking food card... call stew" OR "2. After another player's turn". 
    // If it is my turn and I haven't drawn, I am technically "after another player's turn". But logic handles this in 'waiting_for_draw' for everyone.
    
    let canCallStew = false;
    
    if (gameState.phase === 'waiting_for_draw') {
        canCallStew = true; // Anyone can call
    } else if (gameState.phase === 'player_turn' && isMyTurn) {
        canCallStew = true; // I can call with card
    }
    
    $('#btn-call-stew').prop('disabled', !canCallStew);
    
    if (isCallingStewMode) {
        $('#btn-call-stew').text("取消喊炖菜");
        $('#btn-call-stew').css('background', '#555');
    } else {
        $('#btn-call-stew').text("📢 喊炖菜!");
        $('#btn-call-stew').css('background', '');
    }
    
    // Pot & Animal highlighting
    if (isMyTurn && gameState.phase === 'player_turn') {
        $('#pot-area').css('cursor', 'pointer').css('opacity', 1);
        $('.animal-card').css('cursor', 'pointer');
        
        if (isCallingStewMode) {
            $('#pot-area').css('box-shadow', '0 0 20px #ff4500');
        } else {
            $('#pot-area').css('box-shadow', '');
        }
    } else {
        $('#pot-area').css('cursor', 'default').css('opacity', 0.8).css('box-shadow', '');
        $('.animal-card').css('cursor', 'default');
    }
}

function showResultModal(result) {
    // Only show if we haven't seen this specific result ID?
    // Hack: We rely on the user closing it.
    // Ideally we check a timestamp or ID.
    
    // Only show if modal is not open
    if ($('#result-modal').css('display') !== 'none') return;
    
    $('#result-title').text(result.result_msg);
    
    let detailsHtml = '';
    detailsHtml += `<div class="${result.success ? 'win-msg' : 'lose-msg'}">得分: ${result.score} (目标 12)</div>`;
    
    if (result.animal_actions.length > 0) {
        detailsHtml += '<h4>动物行动:</h4><ul>';
        result.animal_actions.forEach(act => {
            detailsHtml += `<li>${act}</li>`;
        });
        detailsHtml += '</ul>';
    } else {
        detailsHtml += '<p>动物们都很安静。</p>';
    }
    
    detailsHtml += '<h4>锅里的食材:</h4><div style="display:flex; flex-wrap:wrap; gap:5px; justify-content:center;">';
    result.pot_cards.forEach(cid => {
        const c = CARD_DEFS[cid];
        // Mark eaten cards?
        const isEaten = !result.left_pot.includes(cid); // This logic is flawed if duplicates exist. 
        // But for display it's okay just to show what was in the pot.
        // Actually, let's just show the cards.
        detailsHtml += `<span style="font-size:24px; title="${c.name}">${c.icon}</span>`;
    });
    detailsHtml += '</div>';
    
    $('#result-details').html(detailsHtml);
    
    let scoreHtml = '<h4>分数变化:</h4><ul>';
    Object.keys(result.score_changes).forEach(acc => {
         // Find player in array by account
         const playerObj = gameState.players.find(p => p.account === acc);
         const name = playerObj?.account || acc;
         const change = result.score_changes[acc];
         scoreHtml += `<li>${name}: ${change > 0 ? '+' : ''}${change}</li>`;
    });
    scoreHtml += '</ul>';
    
    if (result.winner) {
        // Find winner player in array
        const winnerObj = gameState.players.find(p => p.account === result.winner);
        const winName = winnerObj?.account || result.winner;
        scoreHtml += `<h2 style="color:#ffd700; margin-top:20px;">🏆 获胜者: ${winName} 🏆</h2>`;
    }
    
    $('#score-changes').html(scoreHtml);
    
    $('#result-modal').fadeIn();
}

function showMessage(msg) {
    const el = $('<div>').text(msg)
        .css({
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(0,0,0,0.8)',
            color: '#fff',
            padding: '20px',
            borderRadius: '10px',
            zIndex: 200,
            fontSize: '20px'
        })
        .appendTo('body');
    
    setTimeout(() => el.fadeOut(() => el.remove()), 2000);
}
