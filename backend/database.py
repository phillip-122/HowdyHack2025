import sqlite3

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect('leaderboard.db')
    conn.row_factory = sqlite3.Row # to access columns by name
    return conn

def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            name TEXT PRIMARY KEY,
            total_score REAL NOT NULL DEFAULT 0
        )
    ''')
    
    # Tricks table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tricks (
            user_name TEXT,
            trick_name TEXT,
            highest_score REAL NOT NULL,
            PRIMARY KEY (user_name, trick_name), -- so we can have multiple tricks per user
            FOREIGN KEY (user_name) REFERENCES users(name)
        )
    ''')
    conn.commit()
    conn.close()

def get_user(name: str) -> sqlite3.Row | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
    user = cursor.fetchone()
    conn.close()
    return user

def upload_submission(name: str, 
                      trick_name: str, 
                      score: float
                      ) -> tuple[bool, str]:
    # Check if user is valid
    if not name: # name is empty or None
        return False, "Username must be a non-empty string"   
    if not trick_name or str(trick_name).strip() == "":
        return False, "Trick name must be a non-empty string"
    if not 0 <= score <= 10:
        return False, "Score must be a number between 0 and 10"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create user if they don't exist
        cursor.execute('INSERT OR IGNORE INTO users (name, total_score) VALUES (?, 0)', (name,))
        
        # 2. Check if this trick exists for this user
        cursor.execute('SELECT highest_score FROM user_tricks WHERE user_name = ? AND trick_name = ?', 
                      (name, trick_name))
        existing_trick = cursor.fetchone()
        
        if existing_trick:
            # Trick exists - only update if new score is higher
            if score > existing_trick['highest_score']:
                old_score = existing_trick['highest_score']
                # Update trick score
                cursor.execute('UPDATE user_tricks SET highest_score = ? WHERE user_name = ? AND trick_name = ?',
                              (score, name, trick_name))
                # Update total score (add difference)
                cursor.execute('UPDATE users SET total_score = total_score + ? WHERE name = ?',
                              (score - old_score, name))
                conn.commit()
                return True, f"Updated {trick_name} score to {score}"
            else:
                conn.close()
                return False, f"New score {score} is not higher than existing score {existing_trick['highest_score']}"
        else:
            # New trick for this user
            cursor.execute('INSERT INTO user_tricks (user_name, trick_name, highest_score) VALUES (?, ?, ?)',
                          (name, trick_name, score))
            # Add to total score
            cursor.execute('UPDATE users SET total_score = total_score + ? WHERE name = ?',
                          (score, name))
            conn.commit()
            return True, f"Added new trick {trick_name} with score {score}"
            
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        conn.close()

def get_top_scores(limit: int = 10) -> list[sqlite3.Row]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, total_score FROM users ORDER BY total_score DESC LIMIT ?', (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_user_tricks(name: str) -> list[sqlite3.Row]:
    """Get all tricks and scores for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT trick_name, highest_score FROM user_tricks WHERE user_name = ? ORDER BY highest_score DESC', (name,))
    results = cursor.fetchall()
    conn.close()
    return results