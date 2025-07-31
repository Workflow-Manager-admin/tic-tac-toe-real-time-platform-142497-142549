-- Schema for Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    profile_data JSONB DEFAULT '{}', -- To store additional profile information (avatar, stats, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schema for Games
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    player_x_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    player_o_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    winner_id INTEGER REFERENCES users(id),
    current_turn VARCHAR(1) CHECK (current_turn IN ('X', 'O')),
    status VARCHAR(32) NOT NULL DEFAULT 'active', -- e.g., active, finished, aborted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schema for Moves
CREATE TABLE moves (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    move_index INTEGER NOT NULL CHECK (move_index BETWEEN 0 AND 8), -- 0-8 for 3x3 board
    symbol VARCHAR(1) NOT NULL CHECK (symbol IN ('X', 'O')),
    move_number INTEGER NOT NULL, -- Sequence of the move (for history)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (game_id, move_number),
    UNIQUE (game_id, move_index)
);

-- Optional: For history of completed & restarted games
CREATE TABLE game_history (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    snapshot JSONB NOT NULL,   -- Stores a snapshot of the board state or moves at restart/finish
    event_type VARCHAR(32) NOT NULL, -- e.g. 'restart', 'finish'
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- (Optional) Indexes for performance
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_moves_game_id_move_number ON moves(game_id, move_number);

-- (If using MySQL, replace JSONB with JSON)
