import sqlite3



def get_db_connection():
    conn = sqlite3.connect('leaderboard.db')
    conn.row_factory = sqlite3.Row # to access columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
                 CREATE TABLE IF NOT EXISTS leaderboard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user UNIQUE TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    trick_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                 
                 )''')
    conn.commit()
    conn.close()

def upload_submission(user: str, file_name: str, trick_name: str, score: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO leaderboard (user, file_name, trick_name, score) VALUES (?, ?, ?, ?)',
                   (user, file_name, trick_name, score))
    
    conn.commit()
    conn.close()

def get_top_scores(limit: int = 10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user, trick_name, score, timestamp FROM leaderboard ORDER BY score DESC LIMIT ?', (limit,))
    results = cursor.fetchall()
    conn.close()
    return results