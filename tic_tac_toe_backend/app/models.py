import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

# PUBLIC_INTERFACE
def get_db_connection():
    """Establish a new database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ.get('DB_PORT', 5432),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

class User:
    """User model handles user database operations."""

    # PUBLIC_INTERFACE
    @staticmethod
    def create_user(username, email, password):
        """Create a new user with hashed password."""
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute(
                        """
                        INSERT INTO users (username, email, password_hash)
                        VALUES (%s, %s, %s)
                        RETURNING id, username, email, created_at
                        """,
                        (username, email, hashed_password)
                    )
                    user = curs.fetchone()
                    return user
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = curs.fetchone()
                return user
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def get_by_username(username):
        """Get user by username."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = curs.fetchone()
                return user
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def verify_password(user, password):
        """Verify a user's password hash."""
        return check_password_hash(user["password_hash"], password) if user else False

    # PUBLIC_INTERFACE
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user's profile data."""
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute(
                        "UPDATE users SET profile_data = %s WHERE id = %s RETURNING id, username, email, profile_data",
                        (profile_data, user_id)
                    )
                    return curs.fetchone()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def get_by_id(user_id):
        """Get user by id."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                return curs.fetchone()
        finally:
            conn.close()

class Game:
    """Game model handles Tic Tac Toe game state."""

    # PUBLIC_INTERFACE
    @staticmethod
    def start_new_game(player_x_id, player_o_id):
        """Start a new game."""
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute(
                        """
                        INSERT INTO games (player_x_id, player_o_id, current_turn)
                        VALUES (%s, %s, %s)
                        RETURNING *
                        """,
                        (player_x_id, player_o_id, 'X')
                    )
                    return curs.fetchone()
        finally:
            conn.close()
    
    # PUBLIC_INTERFACE
    @staticmethod
    def get_game(game_id):
        """Get a game by its ID."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM games WHERE id = %s", (game_id,))
                return curs.fetchone()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def set_winner(game_id, winner_id, status="finished"):
        """Set the winner of the game."""
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute(
                        """UPDATE games SET winner_id = %s, status = %s WHERE id = %s RETURNING *""",
                        (winner_id, status, game_id)
                    )
                    return curs.fetchone()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def update_current_turn(game_id, current_turn):
        """Update the current turn symbol."""
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute(
                        """UPDATE games SET current_turn = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *""",
                        (current_turn, game_id)
                    )
                    return curs.fetchone()
        finally:
            conn.close()
    
    # PUBLIC_INTERFACE
    @staticmethod
    def list_games_for_user(user_id):
        """Return all games for a given user."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute(
                    """
                    SELECT * FROM games 
                    WHERE player_x_id = %s OR player_o_id = %s
                    ORDER BY updated_at DESC
                    """, (user_id, user_id)
                )
                return curs.fetchall()
        finally:
            conn.close()

class Move:
    """Move model handles moves within a game."""

    # PUBLIC_INTERFACE
    @staticmethod
    def add_move(game_id, user_id, move_index, symbol, move_number):
        """Add a move to the game."""
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute(
                        """
                        INSERT INTO moves (game_id, user_id, move_index, symbol, move_number)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING *
                        """, (game_id, user_id, move_index, symbol, move_number)
                    )
                    return curs.fetchone()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def get_moves_for_game(game_id):
        """Get all moves for a given game, ordered by move_number."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute(
                    """SELECT * FROM moves WHERE game_id = %s ORDER BY move_number ASC""",
                    (game_id,)
                )
                return curs.fetchall()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def get_last_move(game_id):
        """Get the last move for a given game."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute(
                    """SELECT * FROM moves WHERE game_id = %s ORDER BY move_number DESC LIMIT 1""",
                    (game_id,)
                )
                return curs.fetchone()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def get_move_count(game_id):
        """Return count of moves in game."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute(
                    "SELECT COUNT(*) AS cnt FROM moves WHERE game_id = %s",
                    (game_id,)
                )
                res = curs.fetchone()
                return res['cnt'] if res else 0
        finally:
            conn.close()

class GameHistory:
    """Game history table for storing completed/restarted games."""

    # PUBLIC_INTERFACE
    @staticmethod
    def record_history(game_id, snapshot, event_type):
        """Record a snapshot and event for a game."""
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as curs:
                    curs.execute("""
                        INSERT INTO game_history (game_id, snapshot, event_type)
                        VALUES (%s, %s, %s) RETURNING *
                    """, (game_id, snapshot, event_type))
                    return curs.fetchone()
        finally:
            conn.close()

    # PUBLIC_INTERFACE
    @staticmethod
    def history_for_game(game_id):
        """List all history records for a game."""
        conn = get_db_connection()
        try:
            with conn.cursor() as curs:
                curs.execute(
                    """SELECT * FROM game_history WHERE game_id = %s ORDER BY event_time ASC""",
                    (game_id,)
                )
                return curs.fetchall()
        finally:
            conn.close()
