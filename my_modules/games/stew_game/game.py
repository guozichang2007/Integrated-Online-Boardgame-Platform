from my_modules.games.base import BaseGame
import random

class StewGame(BaseGame):
    """
    Stew (炖菜) 游戏
    """
    def __init__(self, room_id):
        self.game_type = 'stew'
        self.deck = []
        self.pot = []
        self.animals = []
        self.scores = {}
        self.current_index = 0
        self.current_player = None
        self.phase = 'waiting' # waiting, playing, resolved
        self.current_card = None # Card drawn by current player
        self.game_over = False
        self.target_score = 5
        self.last_stew_caller = None # To determine who starts next round

        self.host = None
        self.players = []  # account -> 玩家信息
        
        # Card Definitions (ID, Name, Count, Value, Description)
        # 1: Chicken (5 pts)
        # 2: Stone (-3 pts)
        # 3: Carrot (2 pts)
        # 4: Leek (3 pts)
        # 5: Garlic (6 pts if 1, 1 pt if >=2)
        # 6: Potato (Square of count)
        self.card_defs = {
            1: {'name': 'Chicken', 'points': 5, 'count': 1},
            2: {'name': 'Stone', 'points': -3, 'count': 1},
            3: {'name': 'Carrot', 'points': 2, 'count': 2},
            4: {'name': 'Leek', 'points': 3, 'count': 2},
            5: {'name': 'Garlic', 'points': 6, 'count': 2},
            6: {'name': 'Potato', 'points': 0, 'count': 4}, # Points calculated dynamically
        }

    def init_round(self):
        """Initialize a new round"""
        # Create Deck
        print(f'[StewGame] Initializing new round ')
        self.deck = []
        for cid, info in self.card_defs.items():
            for _ in range(info['count']):
                self.deck.append(cid)
        random.shuffle(self.deck)
        
        self.pot = []
        self.current_card = None
        
        # Initialize Animals
        # Status: 0 = Unfed, 1 = Fed
        # fed_card: The card used to feed (hidden until end?) - Rule says "place food card face down... to indicate it has been fed". 
        # Actually we need to know what card is there? No, rules say "Any face down food card can feed any animal".
        # But wait, "If you call Stew with a card in your hand... play that card".
        # The fed card effectively removes the animal from the game for this round.
        self.animals = [
            {'id': 'boar', 'name': 'Boar', 'fed': False},
            {'id': 'fox', 'name': 'Fox', 'fed': False},
            {'id': 'gopher', 'name': 'Gopher', 'fed': False},
            {'id': 'rabbit', 'name': 'Rabbit', 'fed': False},
            {'id': 'raccoon', 'name': 'Raccoon', 'fed': False},
            {'id': 'vagabond', 'name': 'Vagabond', 'fed': False},
        ]
        
        # Determine start player
        if self.last_stew_caller is not None and 0 <= self.last_stew_caller < len(self.players):
            # last_stew_caller stores the index of last caller
            self.current_index = self.last_stew_caller
        else:
            self.current_index = random.randint(0, len(self.players) - 1) if self.players else 0
        
        # Update current_player with the account
        if self.players:
            self.current_player = self.players[self.current_index]['account']
            
        self.phase = 'waiting_for_draw' # State where anyone can call stew or current player can draw

    def join(self, account):
        print(f'[StewGame] Player {account} joining')
        # Check if player already exists in the array
        for player in self.players:
            if player['account'] == account:
                return None
        
        if self.host is None:
            self.host = account
        
        order = len(self.players) + 1
        self.players.append({"account": account, "order": order})
        self.scores[account] = 0
        print(f'[StewGame] players now: {self.players}')
        return order
    
    def leave(self, account):
        # Find and remove player from array
        for i, player in enumerate(self.players):
            if player['account'] == account:
                self.players.pop(i)
                if account == self.host and self.players:
                    self.host = self.players[0]['account']
                break

    def start(self):
        if len(self.players) >= 1: # Allow 1 player for testing, Rule says 2-4 players
            self.started = True
            self.init_round()
            print(f'[StewGame] Game started ')
            return True
        return False

    def handle_event(self, account, data):
        event_name = data.get('event_name')
        
        if event_name == 'draw':
            return self.handle_draw(account)
        elif event_name == 'action':
            return self.handle_action(account, data)
        elif event_name == 'call_stew':
            return self.handle_call_stew(account, data)
        elif event_name == 'reset_game':
            # Reset entire game (scores 0)
            if account != self.host:
                return {'ok': False, 'msg': 'Only host can reset game'}
            # Reset scores for all players (using account as key)
            self.scores = {player['account']: 0 for player in self.players}
            self.init_round()
            self.game_over = False
            return {'ok': True, 'broadcast': True}
        elif event_name == 'get_hand':
             # Allow frontend to fetch private hand state
            if account == self.current_player and self.current_card:
                return {'ok': True, 'my_card': self.current_card}
            return {'ok': True, 'my_card': None}
        
        return {'ok': False, 'msg': 'Unknown event'}

    def handle_return(self, account):
        return {
            'ok': True,
            'msg': 'Rejoined game',
            'game_state': self.get_state(account),
            'broadcast': False # Only for the returning player? Or broadcast that they returned?
            # CCBGame sets broadcast=True. But usually get_state is large.
            # Let's see how frontend uses it. 
            # If socket event emits this to the specific client, fine.
        }

    def handle_draw(self, account):
        # current_player already set in init_round or updated after each action
        if account != self.current_player:
            return {'ok': False, 'msg': 'Not your turn'}
        
        if self.phase != 'waiting_for_draw':
            return {'ok': False, 'msg': 'Cannot draw now'}
        
        if not self.deck:
             # Deck empty, round ends automatically?
             # Rules: "If no player calls Stew, the round ends, player with most points loses 1 point."
             # This likely happens when a player needs to draw but cannot.
             self.end_round_no_stew()
             return {'ok': True, 'msg': 'Deck empty, round ended.', 'broadcast': True}

        self.current_card = self.deck.pop()
        self.phase = 'player_turn' # Now player has card and must act or call stew
        
        return {
            'ok': True, 
            'msg': 'Card drawn', 
            'card': self.current_card, # Send card to player
            'broadcast': True # Broadcast that player drew (but not what card)
        }

    def handle_action(self, account, data):
        if account != self.current_player:
            return {'ok': False, 'msg': 'Not your turn'}
        
        if self.phase != 'player_turn':
            return {'ok': False, 'msg': 'Cannot act now'}
        
        action_type = data.get('action_type') # 'pot' or 'feed'
        animal_index = data.get('animal_index') # if feed
        
        if action_type == 'pot':
            self.pot.append(self.current_card)
            msg = f'{account} put a card in the pot.'
        elif action_type == 'feed':
            if animal_index is None or animal_index < 0 or animal_index >= len(self.animals):
                return {'ok': False, 'msg': 'Invalid animal'}
            if self.animals[animal_index]['fed']:
                return {'ok': False, 'msg': 'Animal already fed'}
            
            self.animals[animal_index]['fed'] = True
            msg = f'{account} fed the {self.animals[animal_index]["name"]}.'
        else:
            return {'ok': False, 'msg': 'Invalid action'}
        
        self.current_card = None
        self.phase = 'waiting_for_draw'
        
        # Move to next player
        self.current_index = (self.current_index + 1) % len(self.players)
        self.current_player = self.players[self.current_index]['account']
        
        # Check if deck is empty immediately after turn? 
        # No, check when next player tries to draw.
        
        return {
            'ok': True,
            'msg': msg,
            'broadcast': True
        }

    def handle_call_stew(self, account, data):
        # Case 1: Called out of turn (waiting_for_draw phase)
        # Case 2: Called on turn (player_turn phase) -> Must play card first
        
        # Find the index of the calling player
        caller_index = None
        for i, player in enumerate(self.players):
            if player['account'] == account:
                caller_index = i
                break
        
        if caller_index is None:
            return {'ok': False, 'msg': 'Player not in game'}
        
        if self.phase == 'waiting_for_draw':
            # Anyone can call
            msg = f'{account} called STEW!'
            self.resolve_stew(caller_index=caller_index)
            return {'ok': True, 'msg': msg, 'broadcast': True}
        
        elif self.phase == 'player_turn':
            # Only current player can call
            if account != self.current_player:
                return {'ok': False, 'msg': 'Cannot call Stew during another player\'s action phase'}
            
            # Must play card
            action_type = data.get('action_type')
            animal_index = data.get('animal_index')
            
            if not action_type:
                return {'ok': False, 'msg': 'Must play your card when calling Stew'}
            
            if action_type == 'pot':
                self.pot.append(self.current_card)
            elif action_type == 'feed':
                if animal_index is None or animal_index < 0 or animal_index >= len(self.animals):
                    return {'ok': False, 'msg': 'Invalid animal'}
                if self.animals[animal_index]['fed']:
                    return {'ok': False, 'msg': 'Animal already fed'}
                self.animals[animal_index]['fed'] = True
            else:
                 return {'ok': False, 'msg': 'Invalid action'}
            
            msg = f'{account} called STEW!'
            self.resolve_stew(caller_index=caller_index)
            return {'ok': True, 'msg': msg, 'broadcast': True}
        
        else:
            return {'ok': False, 'msg': 'Cannot call Stew now'}

    def end_round_no_stew(self):
        """
        If deck runs out and no one called stew.
        Player with most points loses 1 point.
        """
        max_score = -999
        if self.scores.values():
             max_score = max(self.scores.values())
        
        losers = []
        if max_score > 0: # "If no player has any points, no one loses points"
            losers = [account for account, s in self.scores.items() if s == max_score]
            for account in losers:
                self.scores[account] -= 1
        
        # Create score_changes dictionary using account as key
        score_changes = {player['account']: (-1 if player['account'] in losers else 0) for player in self.players}
        
        self.last_result = {
            'success': False,
            'reason': 'No one called Stew',
            'pot_score': 0,
            'pot_cards': [],
            'caller': None,
            'score_changes': score_changes
        }
        
        self.init_round()

    def resolve_stew(self, caller_index):
        # caller_index is the index in self.players array
        self.last_stew_caller = caller_index
        caller_account = self.players[caller_index]['account']
        
        # 1. Reveal Pot
        pot_cards_details = [self.card_defs[cid] for cid in self.pot]
        
        # 2. Animals Eat
        # Copy pot to modify
        current_pot = list(self.pot)
        
        # Helper to remove first occurrence of card type
        def remove_card(target_id):
            if target_id in current_pot:
                current_pot.remove(target_id)
                return True
            return False

        animal_actions = []

        # Boar: Eats 1 Garlic (5)
        if not self.animals[0]['fed']:
            if remove_card(5):
                animal_actions.append("Boar ate a Garlic!")
        
        # Fox: Eats Chicken (1)
        if not self.animals[1]['fed']:
            if remove_card(1):
                animal_actions.append("Fox ate the Chicken!")
        
        # Gopher: Eats 1 Leek (4)
        if not self.animals[2]['fed']:
            if remove_card(4):
                animal_actions.append("Gopher ate a Leek!")

        # Rabbit: Eats 1 Carrot (3)
        if not self.animals[3]['fed']:
            if remove_card(3):
                animal_actions.append("Rabbit ate a Carrot!")
        
        # Raccoon: Eats 1 Potato (6)
        if not self.animals[4]['fed']:
            if remove_card(6):
                animal_actions.append("Raccoon ate a Potato!")
        
        # Vagabond: 
        # -3 pts if Chicken in stew
        # +3 pts if Chicken NOT in stew
        # This is a score modifier, applies after removals
        vagabond_mod = 0
        if not self.animals[5]['fed']:
            if 1 in current_pot:
                vagabond_mod = -3
                animal_actions.append("Vagabond hates the Chicken (-3 pts)!")
            else:
                vagabond_mod = 3
                animal_actions.append("Vagabond is happy there's no Chicken (+3 pts)!")

        # 3. Calculate Score
        score = 0
        counts = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
        for cid in current_pot:
            counts[cid] += 1
            
        # Chicken (1): 5 pts
        score += counts[1] * 5
        # Stone (2): -3 pts
        score += counts[2] * (-3)
        # Carrot (3): 2 pts
        score += counts[3] * 2
        # Leek (4): 3 pts
        score += counts[4] * 3
        # Garlic (5): 1 if >=2, else 6
        if counts[5] >= 2:
            score += counts[5] * 1
        else:
            score += counts[5] * 6
        # Potato (6): count^2
        score += counts[6] * counts[6]
        
        score += vagabond_mod
        
        # 4. Determine Success
        success = score >= 12
        
        # 5. Award Points - score_changes uses account as key for consistency with self.scores
        score_changes = {player['account']: 0 for player in self.players}
        if success:
            score_changes[caller_account] = 2
            result_msg = "STEW SUCCESS!"
        else:
            # Caller gets 0, others get 1
            for player in self.players:
                if player['account'] != caller_account:
                    score_changes[player['account']] = 1
            result_msg = "STEW FAILED!"

        for account, change in score_changes.items():
            self.scores[account] += change
            
        # Check Winner
        winner = None
        for account, s in self.scores.items():
            if s >= self.target_score:
                if winner is None or s > self.scores[winner]:
                    winner = account
        
        if winner:
            self.game_over = True
            
        self.last_result = {
            'success': success,
            'score': score,
            'animal_actions': animal_actions,
            'result_msg': result_msg,
            'pot_cards': self.pot, # Original pot
            'left_pot': current_pot, # Pot after eating
            'score_changes': score_changes,
            'winner': winner
        }
        
        if not self.game_over:
            self.init_round()

    def get_state(self, account=0):
        
        state = {
            'players': self.players,
            'scores': self.scores,
            'animals': self.animals,
            'pot_count': len(self.pot),
            'deck_count': len(self.deck),
            'phase': self.phase,
            'current_player_account': self.current_player,
            'current_index': self.current_index,
            'game_over': self.game_over
        }
        
        if hasattr(self, 'last_result'):
            state['last_result'] = self.last_result
            
        # If it's the requesting player's turn and they have a card, show it
        if account == self.current_player and self.current_card:
            state['my_card'] = self.current_card
            
        return state

def register_game():
    return {
        'id': 'stew_game',
        'name': 'Stew (炖菜)',
        'description': '扮演农民，收集食材炖一锅好菜！小心贪吃的动物们！',
        'min_players': 2,
        'max_players': 4,
        'class': StewGame,
        'url': '/stew'
    }
