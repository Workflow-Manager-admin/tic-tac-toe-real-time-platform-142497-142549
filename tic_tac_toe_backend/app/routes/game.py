from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.models import Game, User, Move, GameHistory
import jwt
import os

blp = Blueprint("Game", "game", url_prefix="/game", description="Tic Tac Toe Game endpoints")
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')

def decode_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded['sub']
    except Exception:
        return None

def require_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, message="Missing Bearer token.")
    token = auth_header[7:]
    user_id = decode_jwt(token)
    if not user_id:
        abort(401, message="Invalid or expired token.")
    return user_id

def get_board_state(moves):
    board = [""] * 9
    for move in moves:
        idx = move['move_index']
        sym = move['symbol']
        board[idx] = sym
    return board

def check_winner(board):
    wins = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    for a, b, c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None

# PUBLIC_INTERFACE
@blp.route("/start")
class GameStartView(MethodView):
    """Start a new game between two players."""
    def post(self):
        data = request.get_json()
        other_username = data.get("other_username")
        user_id = require_auth()
        user = User.get_by_id(user_id)
        if not user:
            abort(401, message="Invalid user.")
        other = User.get_by_username(other_username) if other_username else None
        if not other:
            abort(404, message="Opponent user not found.")
        # Player X is always the requester, O is opponent
        game = Game.start_new_game(user['id'], other['id'])
        return {"game": game}

# PUBLIC_INTERFACE
@blp.route("/<int:game_id>")
class GameStatusView(MethodView):
    """Get the current state of a game by id."""
    def get(self, game_id):
        user_id = require_auth()
        game = Game.get_game(game_id)
        if not game:
            abort(404, message="Game not found")
        if user_id not in [game['player_x_id'], game['player_o_id']]:
            abort(403, message="You are not a player in this game.")
        moves = Move.get_moves_for_game(game_id)
        board = get_board_state(moves)
        return {
            "game": game,
            "board": board,
            "moves": moves
        }

# PUBLIC_INTERFACE
@blp.route("/my")
class MyGamesView(MethodView):
    """List all games for the authenticated user."""
    def get(self):
        user_id = require_auth()
        games = Game.list_games_for_user(user_id)
        return {"games": games}

# PUBLIC_INTERFACE
@blp.route("/<int:game_id>/move")
class MoveView(MethodView):
    """Submit a move for a game. Requires turn validation and checks for win/draw."""
    def post(self, game_id):
        data = request.get_json()
        move_index = data.get("move_index")
        user_id = require_auth()
        game = Game.get_game(game_id)
        if not game:
            abort(404, message="Game not found.")
        if game['status'] != 'active':
            abort(400, message="Game is not active.")

        # Determine symbol for current player
        symbol = None
        if user_id == game['player_x_id']:
            symbol = 'X'
        elif user_id == game['player_o_id']:
            symbol = 'O'
        if not symbol:
            abort(403, message="You are not a player in this game.")

        if game['current_turn'] != symbol:
            abort(400, message="It's not your turn.")

        moves = Move.get_moves_for_game(game_id)
        board = get_board_state(moves)

        # Validate move_index
        if move_index is None or not (0 <= move_index <= 8) or board[move_index]:
            abort(400, message="Invalid move.")

        move_num = len(moves) + 1
        move = Move.add_move(game_id, user_id, move_index, symbol, move_num)
        board[move_index] = symbol

        winner = check_winner(board)
        draw = all(cell in ['X', 'O'] for cell in board) and not winner

        result = {
            "move": move,
            "winner": None,
            "draw": False,
            "game": None,
        }
        # Update & close game if win/draw
        if winner:
            winner_id = game['player_x_id'] if winner == 'X' else game['player_o_id']
            updated_game = Game.set_winner(game_id, winner_id)
            GameHistory.record_history(game_id, {"moves": moves + [move], "result": "win", "winner": winner}, "finish")
            result['winner'] = winner
            result['game'] = updated_game
        elif draw:
            # Status stays finished but no winner
            updated_game = Game.set_winner(game_id, None, status="draw")
            GameHistory.record_history(game_id, {"moves": moves + [move], "result": "draw"}, "finish")
            result['draw'] = True
            result['game'] = updated_game
        else:
            # Change current turn
            next_turn = "O" if symbol == "X" else "X"
            Game.update_current_turn(game_id, next_turn)
            result['game'] = Game.get_game(game_id)
        return result

# PUBLIC_INTERFACE
@blp.route("/<int:game_id>/restart")
class GameRestartView(MethodView):
    """Restart a completed game. Only allowed after it's finished."""
    def post(self, game_id):
        user_id = require_auth()
        game = Game.get_game(game_id)
        if not game:
            abort(404, message="Game not found.")
        if game["status"] == "active":
            abort(400, message="Cannot restart an active game.")
        # Remove moves, reset winner, set status to active, turn to X
        moves = Move.get_moves_for_game(game_id)
        GameHistory.record_history(game_id, {"moves": moves, "restart_by": user_id}, "restart")
        # Delete moves
        from app.models import get_db_connection
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM moves WHERE game_id = %s", (game_id,))
        finally:
            conn.close()
        Game.set_winner(game_id, None, status="active")
        Game.update_current_turn(game_id, "X")
        return {"message": "Game restarted", "game_id": game_id}

# PUBLIC_INTERFACE
@blp.route("/<int:game_id>/history")
class GameHistoryView(MethodView):
    """Get a game's historical event records."""
    def get(self, game_id):
        user_id = require_auth()
        game = Game.get_game(game_id)
        if not game or user_id not in [game['player_x_id'], game['player_o_id']]:
            abort(404, message="Game not found or access denied.")
        history = GameHistory.history_for_game(game_id)
        return {"history": history}
