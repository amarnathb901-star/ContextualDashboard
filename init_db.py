import sqlite3
import os

# Use the absolute path to ensure the DB is created in the project folder
db_path = '/Users/appit2015140/Documents/Courses/GenAI/ContextualDashboard/research.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()  # Fixed: Use .cursor()

# 1. Create table for your tracked topics
cursor.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_name TEXT UNIQUE,
        is_active INTEGER DEFAULT 1
    )
''')

# 2. Create table for the AI generated signals
cursor.execute('''
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project TEXT,
        report TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# 3. Add a starting topic so the worker isn't empty
cursor.execute("INSERT OR IGNORE INTO topics (topic_name, is_active) VALUES ('Anthropic Claude', 1)")

conn.commit()
conn.close()
print(f"✅ Database initialized at {db_path}")